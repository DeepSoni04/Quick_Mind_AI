import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.query import QueryGenerateRequest, QueryResultResponse, SQLStatementInfo
from app.services.llm_service import get_llm_provider
from app.services.schema_service import SchemaService
from app.services.sql_validator import SQLValidator
from app.services.database_service import DatabaseService
from app.utils.helpers import utc_now, format_relative_time

logger = logging.getLogger("querymind.query_service")

# Maximum conversation turns to include in session context sent to LLM
_MAX_SESSION_CONTEXT_TURNS = 6


class QueryService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.schema_service = SchemaService(db)
        self.db_service = DatabaseService(db)
        self.validator = SQLValidator()

    async def generate_query(self, user_id: str, user_role: str, req: QueryGenerateRequest) -> QueryResultResponse:
        """Process natural language request: translate via LLM, validate, and record query state."""

        # 1. Resolve and authenticate real target database connection
        db_conn = None
        if req.database_id:
            try:
                obj_conn_id = ObjectId(req.database_id)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid database_id format.")
            db_conn = await self.db.database_connections.find_one({"_id": obj_conn_id, "created_by": user_id})
            if not db_conn:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified target database connection not found.")
        else:
            # Look for an existing saved connection for this user
            db_conn = await self.db.database_connections.find_one({"created_by": user_id})
            if not db_conn:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No target database configured. Please add and select a valid target database connection before generating queries."
                )

        conn_id = str(db_conn["_id"])
        db_type = db_conn.get("db_type", "mysql")

        # 2. Validate session if specified, and load conversation context
        session_id = req.session_id
        session_context: Optional[List[Dict[str, Any]]] = None
        if session_id:
            try:
                obj_sess_id = ObjectId(session_id)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id format.")
            session = await self.db.query_sessions.find_one({"_id": obj_sess_id, "user_id": user_id})
            if not session:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
            if session.get("status") != "active":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot generate query in a closed session.")

            # Load recent conversation turns for context
            session_context = await self._load_session_context(session_id, user_id)

        # 3. Discover dynamic schema from target database
        schema_data = await self.schema_service.discover_schema(conn_id, user_id)
        schema_text = self._build_schema_text(schema_data, db_type)

        # 4. Call configured LLM provider
        llm = get_llm_provider()
        llm_res = await llm.generate_sql(
            nl_query=req.nl_query,
            db_type=db_type,
            schema_text=schema_text,
            session_context=session_context
        )

        # Handle Ambiguity Clarification Flow
        if llm_res.get("needs_clarification"):
            now = utc_now()
            q_doc = {
                "user_id": user_id,
                "database_id": conn_id,
                "session_id": session_id,
                "nl_query": req.nl_query,
                "input_type": req.input_type,
                "language": req.language,
                "intent": llm_res.get("intent", ""),
                "statements": [],
                "validation_status": "clarification_needed",
                "approval_status": "pending",
                "execution_status": "none",
                "created_at": now,
                "updated_at": now
            }
            res = await self.db.queries.insert_one(q_doc)
            return QueryResultResponse(
                query_id=str(res.inserted_id),
                status="clarification_needed",
                nl_query=req.nl_query,
                statements=[],
                clarification_needed=True,
                clarification_question=llm_res.get("clarification_question"),
                clarification_choices=llm_res.get("clarification_choices")
            )

        # 5. Load applicable permissions from MongoDB for connection
        permissions_dict = await self.schema_service.get_permissions_dict(conn_id)

        # 6. Parse & Validate Generated Statements
        raw_statements = llm_res.get("sql_statements", [])
        validated_statements: List[SQLStatementInfo] = []
        overall_status = "valid"

        is_mongodb = db_type.lower() in ("mongodb", "mongo")

        for idx, item in enumerate(raw_statements):
            sql_text = item.get("sql", "")
            op = (item.get("operation") or "SELECT").upper()
            mql_obj = item.get("mql")  # may be None for SQL databases

            if is_mongodb:
                # For MongoDB: use a lightweight MQL validator, skip the SQL AST validator
                stmt_info = self._validate_mongodb_statement(
                    sql_text=sql_text,
                    mql_obj=mql_obj,
                    operation=op,
                    user_role=user_role,
                    allowed_permissions=permissions_dict,
                    statement_index=len(validated_statements)
                )
            else:
                split_sqls = self.validator.split_statements(sql_text, dialect=db_type)
                for split_sql in split_sqls:
                    stmt_info = self.validator.validate_statement(
                        raw_sql=split_sql,
                        dialect=db_type,
                        user_role=user_role,
                        allowed_permissions=permissions_dict
                    )
                    stmt_info.statement_index = len(validated_statements)
                    stmt_info.approval_status = "pending"
                    validated_statements.append(stmt_info)

                    if stmt_info.validation_status in ["blocked", "invalid"]:
                        overall_status = stmt_info.validation_status
                continue  # SQL path appends above, skip the MongoDB append below

            validated_statements.append(stmt_info)
            if stmt_info.validation_status in ["blocked", "invalid"]:
                overall_status = stmt_info.validation_status

        if not validated_statements:
            overall_status = "invalid"

        # 6b. Attempt impact estimation for DELETE/UPDATE on SQL databases only
        if not is_mongodb and db_type in ("mysql", "postgresql", "postgres"):
            try:
                creds = await self.db_service.get_connection_credentials(conn_id, user_id)
                from app.services.execution_service import ExecutionService
                exec_svc = ExecutionService(self.db)
                for stmt_info in validated_statements:
                    if stmt_info.operation in ("DELETE", "UPDATE") and stmt_info.validation_status not in ("blocked", "invalid"):
                        est = exec_svc.estimate_impact(
                            db_type=db_type,
                            host=creds.get("host"),
                            port=creds.get("port"),
                            username=creds.get("username", ""),
                            password=creds.get("password", ""),
                            database_name=creds.get("database_name", ""),
                            sql=stmt_info.sql,
                        )
                        stmt_info.estimated_rows_affected = est
            except Exception as impact_err:
                logger.debug(f"Impact estimation skipped (non-critical): {impact_err}")

        now = utc_now()
        q_doc = {
            "user_id": user_id,
            "database_id": conn_id,
            "db_type": db_type,
            "session_id": session_id,
            "nl_query": req.nl_query,
            "input_type": req.input_type,
            "language": req.language,
            "intent": llm_res.get("intent", ""),
            "statements": [s.model_dump() for s in validated_statements],
            "validation_status": overall_status,
            "approval_status": "pending",
            "execution_status": "none",
            "created_at": now,
            "updated_at": now
        }

        res = await self.db.queries.insert_one(q_doc)
        query_id = str(res.inserted_id)

        # Audit log
        await self.db.query_logs.insert_one({
            "query_id": query_id,
            "user_id": user_id,
            "event_type": "query_generation",
            "status": overall_status,
            "created_at": now
        })

        return QueryResultResponse(
            query_id=query_id,
            status=overall_status,
            nl_query=req.nl_query,
            statements=validated_statements
        )

    def _build_schema_text(self, schema_data, db_type: str) -> str:
        """Build schema description text tailored to the db_type for LLM prompts."""
        is_mongodb = db_type.lower() in ("mongodb", "mongo")
        prefix_word = "Collection" if is_mongodb else "Table"
        field_word = "Fields" if is_mongodb else "Columns"

        text = f"Database: {schema_data.database_name} ({schema_data.db_type.upper()})\n"
        for t in schema_data.tables:
            col_desc = ", ".join([f"{c.name} ({c.type})" for c in t.columns])
            text += f"{prefix_word}: {t.name} ({field_word}: {col_desc})\n"
        return text

    def _validate_mongodb_statement(
        self,
        sql_text: str,
        mql_obj: Optional[Dict],
        operation: str,
        user_role: str,
        allowed_permissions: Dict,
        statement_index: int
    ) -> SQLStatementInfo:
        """Lightweight MongoDB MQL validator — checks role permissions and basic structure."""
        # Role permission check for write operations
        write_ops = {"INSERT", "UPDATE", "DELETE"}
        if operation in write_ops and user_role == "viewer":
            return SQLStatementInfo(
                statement_index=statement_index,
                sql=sql_text,
                operation=operation,
                validation_status="blocked",
                validation_message="Viewers are not permitted to execute write operations.",
                approval_status="pending",
                warning_broad_impact=False,
                mql=mql_obj,
            )

        # Check collection permissions if permissions are configured
        collection_name = None
        if mql_obj:
            collection_name = mql_obj.get("collection")

        if collection_name and allowed_permissions:
            allowed = allowed_permissions.get(collection_name, {})
            if allowed.get("allowed") is False:
                return SQLStatementInfo(
                    statement_index=statement_index,
                    sql=sql_text,
                    operation=operation,
                    validation_status="blocked",
                    validation_message=f"Access to collection '{collection_name}' is not permitted.",
                    approval_status="pending",
                    mql=mql_obj,
                )

        # Broad impact warning for delete_many / update_many with empty filter
        warning_broad = False
        validation_msg = None
        if mql_obj:
            mongo_op = mql_obj.get("operation", "")
            if mongo_op in ("delete_many", "update_many"):
                filter_obj = mql_obj.get("filter", {})
                if not filter_obj:  # empty filter matches all documents
                    warning_broad = True
                    validation_msg = f"⚠ This {mongo_op} has an empty filter — it will affect ALL documents in '{collection_name}'."

        return SQLStatementInfo(
            statement_index=statement_index,
            sql=sql_text,
            operation=operation,
            validation_status="warning" if warning_broad else "valid",
            validation_message=validation_msg,
            approval_status="pending",
            warning_broad_impact=warning_broad,
            affected_table=collection_name,
            mql=mql_obj,
        )

    async def _load_session_context(self, session_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Load bounded conversation history for session context sent to the LLM."""
        try:
            cursor = self.db.queries.find(
                {"session_id": session_id, "user_id": user_id},
                {"nl_query": 1, "intent": 1, "execution_status": 1}
            ).sort("created_at", -1).limit(_MAX_SESSION_CONTEXT_TURNS)
            turns = []
            async for doc in cursor:
                turns.append({
                    "user": doc.get("nl_query", ""),
                    "assistant_intent": doc.get("intent", ""),
                    "executed": doc.get("execution_status") == "executed"
                })
            turns.reverse()  # chronological order
            return turns
        except Exception as e:
            logger.debug(f"Could not load session context: {e}")
            return []

    async def revalidate_edited_sql(self, query_id: str, edited_sql: str, user_id: str, user_role: str) -> QueryResultResponse:
        """Complete re-validation of user-edited SQL/MQL. Resets all previous approvals."""
        try:
            obj_q_id = ObjectId(query_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid query_id format.")

        query = await self.db.queries.find_one({"_id": obj_q_id, "user_id": user_id})
        if not query:
            raise HTTPException(status_code=404, detail="Query not found.")

        conn_id = query["database_id"]
        db_conn = await self.db.database_connections.find_one({"_id": ObjectId(conn_id), "created_by": user_id})
        if not db_conn:
            raise HTTPException(status_code=404, detail="Target database connection not found.")

        dialect = db_conn.get("db_type", "mysql")
        is_mongodb = dialect.lower() in ("mongodb", "mongo")
        permissions_dict = await self.schema_service.get_permissions_dict(conn_id)

        validated_statements: List[SQLStatementInfo] = []
        overall_status = "valid"

        if is_mongodb:
            # For MongoDB: treat the edited text as-is, parse as MQL JSON if possible
            mql_obj = None
            operation = "SELECT"
            try:
                mql_obj = json.loads(edited_sql)
                mongo_op = mql_obj.get("operation", "find")
                op_map = {
                    "find": "SELECT", "aggregate": "SELECT", "count": "SELECT",
                    "insert_one": "INSERT", "insert_many": "INSERT",
                    "update_one": "UPDATE", "update_many": "UPDATE",
                    "delete_one": "DELETE", "delete_many": "DELETE",
                }
                operation = op_map.get(mongo_op, "SELECT")
            except Exception:
                pass  # Not valid JSON, keep as raw text for display

            stmt_info = self._validate_mongodb_statement(
                sql_text=edited_sql,
                mql_obj=mql_obj,
                operation=operation,
                user_role=user_role,
                allowed_permissions=permissions_dict,
                statement_index=0
            )
            validated_statements = [stmt_info]
            if stmt_info.validation_status in ["blocked", "invalid"]:
                overall_status = stmt_info.validation_status
        else:
            # Split and validate statements independently
            split_sqls = self.validator.split_statements(edited_sql, dialect=dialect)
            for idx, sql_str in enumerate(split_sqls):
                stmt_info = self.validator.validate_statement(
                    raw_sql=sql_str,
                    dialect=dialect,
                    user_role=user_role,
                    allowed_permissions=permissions_dict
                )
                stmt_info.statement_index = idx
                stmt_info.approval_status = "pending"  # Always reset approval!
                validated_statements.append(stmt_info)

                if stmt_info.validation_status in ["blocked", "invalid"]:
                    overall_status = stmt_info.validation_status

        if not validated_statements:
            overall_status = "invalid"

        now = utc_now()
        await self.db.queries.update_one(
            {"_id": obj_q_id},
            {"$set": {
                "statements": [s.model_dump() for s in validated_statements],
                "validation_status": overall_status,
                "approval_status": "pending",
                "updated_at": now
            }}
        )

        await self.db.query_logs.insert_one({
            "query_id": query_id,
            "user_id": user_id,
            "event_type": "sql_edited_revalidation",
            "status": overall_status,
            "created_at": now
        })

        return QueryResultResponse(
            query_id=query_id,
            status=overall_status,
            nl_query=query["nl_query"],
            statements=validated_statements
        )

    async def approve_statement(self, query_id: str, statement_index: int, user_id: str) -> QueryResultResponse:
        """Explicitly approve a single SQL/MQL statement for execution."""
        try:
            obj_q_id = ObjectId(query_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid query_id format.")

        query = await self.db.queries.find_one({"_id": obj_q_id, "user_id": user_id})
        if not query:
            raise HTTPException(status_code=404, detail="Query not found.")

        statements = query.get("statements", [])
        if statement_index < 0 or statement_index >= len(statements):
            raise HTTPException(status_code=400, detail="Invalid statement index.")

        stmt = statements[statement_index]
        if stmt.get("validation_status") in ["blocked", "invalid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve {stmt.get('validation_status')} statement: {stmt.get('validation_message')}"
            )

        stmt["approval_status"] = "approved"

        # Check if all statements are approved
        all_approved = all(s.get("approval_status") == "approved" for s in statements)
        overall_approval = "approved" if all_approved else "partially_approved"

        now = utc_now()
        await self.db.queries.update_one(
            {"_id": obj_q_id},
            {"$set": {
                "statements": statements,
                "approval_status": overall_approval,
                "updated_at": now
            }}
        )

        await self.db.query_logs.insert_one({
            "query_id": query_id,
            "user_id": user_id,
            "event_type": "statement_approval",
            "statement_index": statement_index,
            "status": "approved",
            "created_at": now
        })

        stmt_objs = [SQLStatementInfo(**s) for s in statements]
        return QueryResultResponse(
            query_id=query_id,
            status=query.get("validation_status", "valid"),
            nl_query=query["nl_query"],
            statements=stmt_objs
        )

    async def reject_query(self, query_id: str, user_id: str) -> QueryResultResponse:
        """User rejects generated SQL/MQL query."""
        try:
            obj_q_id = ObjectId(query_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid query_id format.")

        query = await self.db.queries.find_one({"_id": obj_q_id, "user_id": user_id})
        if not query:
            raise HTTPException(status_code=404, detail="Query not found.")

        statements = query.get("statements", [])
        for s in statements:
            s["approval_status"] = "rejected"

        now = utc_now()
        await self.db.queries.update_one(
            {"_id": obj_q_id},
            {"$set": {
                "statements": statements,
                "approval_status": "rejected",
                "updated_at": now
            }}
        )

        stmt_objs = [SQLStatementInfo(**s) for s in statements]
        return QueryResultResponse(
            query_id=query_id,
            status="rejected",
            nl_query=query["nl_query"],
            statements=stmt_objs
        )
