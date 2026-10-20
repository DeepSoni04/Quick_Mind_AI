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


class QueryService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.schema_service = SchemaService(db)
        self.db_service = DatabaseService(db)
        self.validator = SQLValidator()

    async def generate_query(self, user_id: str, user_role: str, req: QueryGenerateRequest) -> QueryResultResponse:
        """Process natural language request: translate via LLM, validate AST & permissions, and record query state."""
        
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

        # 2. Validate session if specified
        session_id = req.session_id
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

        # 3. Discover dynamic schema from target database (fails clearly if unreachable)
        schema_data = await self.schema_service.discover_schema(conn_id, user_id)
        schema_text = f"Database: {schema_data.database_name} ({schema_data.db_type.upper()})\n"
        for t in schema_data.tables:
            col_desc = ", ".join([f"{c.name} ({c.type})" for c in t.columns])
            schema_text += f"Table: {t.name} (Columns: {col_desc})\n"

        # 4. Call configured LLM provider
        llm = get_llm_provider()
        llm_res = await llm.generate_sql(
            nl_query=req.nl_query,
            db_type=db_type,
            schema_text=schema_text
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

        for idx, item in enumerate(raw_statements):
            sql_text = item.get("sql", "")
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

        if not validated_statements:
            overall_status = "invalid"

        # 6b. Attempt impact estimation for DELETE/UPDATE on SQL databases
        if db_type in ("mysql", "postgresql", "postgres"):
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

    async def revalidate_edited_sql(self, query_id: str, edited_sql: str, user_id: str, user_role: str) -> QueryResultResponse:
        """Complete re-validation of user-edited SQL. Resets all previous approvals."""
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
        permissions_dict = await self.schema_service.get_permissions_dict(conn_id)

        # Split and validate statements independently
        split_sqls = self.validator.split_statements(edited_sql, dialect=dialect)
        validated_statements: List[SQLStatementInfo] = []
        overall_status = "valid"

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
        """Explicitly approve a single SQL statement for execution."""
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
        """User rejects generated SQL query."""
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
