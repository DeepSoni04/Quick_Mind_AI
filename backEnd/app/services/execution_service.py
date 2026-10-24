import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import pymysql
import psycopg2

from app.core.config import settings
from app.core.security import sanitize_sensitive_text
from app.schemas.query import QueryResultResponse, SQLStatementInfo
from app.services.database_service import DatabaseService
from app.services.llm_service import get_llm_provider
from app.services.schema_service import SchemaService
from app.services.sql_validator import SQLValidator
from app.utils.helpers import utc_now

logger = logging.getLogger("querymind.execution_service")

# SQL keywords that signal rows will be modified — trigger impact preview
_DESTRUCTIVE_OPS = frozenset(["DELETE", "UPDATE", "INSERT"])

# Regex to extract WHERE clause from a DELETE/UPDATE statement for COUNT(*) preview
_WHERE_RE = re.compile(r"\bWHERE\b(.+?)(?:LIMIT\b|ORDER\s+BY\b|$)", re.IGNORECASE | re.DOTALL)
# Regex to capture table name from DELETE FROM <table>
_DELETE_TABLE_RE = re.compile(r"DELETE\s+FROM\s+[`\"]?(\w+)[`\"]?", re.IGNORECASE)
# Regex to capture table name from UPDATE <table>
_UPDATE_TABLE_RE = re.compile(r"UPDATE\s+[`\"]?(\w+)[`\"]?", re.IGNORECASE)


class ExecutionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.db_service = DatabaseService(db)
        self.schema_service = SchemaService(db)
        self.validator = SQLValidator()

    # ------------------------------------------------------------------
    # Public: execute_query
    # ------------------------------------------------------------------

    async def execute_query(
        self,
        query_id: str,
        user_id: str,
        statement_indices: Optional[List[int]] = None
    ) -> QueryResultResponse:
        """Execute approved SQL statements against target database after pre-execution revalidation."""
        try:
            obj_q_id = ObjectId(query_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid query_id format.")

        # 1. Verify query ownership
        query = await self.db.queries.find_one({"_id": obj_q_id, "user_id": user_id})
        if not query:
            raise HTTPException(status_code=404, detail="Query not found.")

        statements = query.get("statements", [])
        if not statements:
            raise HTTPException(status_code=400, detail="No SQL statements found in query.")

        # 2. Verify target database connection
        conn_id = query["database_id"]
        try:
            obj_conn_id = ObjectId(conn_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid database connection reference.")

        conn_doc = await self.db.database_connections.find_one({"_id": obj_conn_id, "created_by": user_id})
        if not conn_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target database connection is no longer accessible or has been deleted."
            )

        creds = await self.db_service.get_connection_credentials(conn_id, user_id)
        db_type = creds.get("db_type", "mysql")

        # 3. Check current user role
        user_doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        current_role = user_doc.get("role", "viewer") if user_doc else "viewer"

        # 4. Filter statement indices
        indices_to_run = statement_indices if statement_indices is not None else list(range(len(statements)))
        if not indices_to_run:
            raise HTTPException(status_code=400, detail="No statement indices specified for execution.")

        # 5. Load active permissions for revalidation
        permissions_dict = await self.schema_service.get_permissions_dict(conn_id)

        # 6. Pre-execution revalidation
        for idx in indices_to_run:
            if idx < 0 or idx >= len(statements):
                raise HTTPException(status_code=400, detail=f"Invalid statement index {idx}.")

            stmt = statements[idx]

            if stmt.get("approval_status") != "approved":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Statement #{idx + 1} cannot be executed without explicit user approval."
                )

            # Skip SQL revalidation for MongoDB (uses MQL, not SQL)
            if db_type != "mongodb":
                sql_text = stmt.get("sql", "")
                reval_info = self.validator.validate_statement(
                    raw_sql=sql_text,
                    dialect=db_type,
                    user_role=current_role,
                    allowed_permissions=permissions_dict
                )

                if reval_info.validation_status in ["blocked", "invalid"]:
                    await self.db.queries.update_one(
                        {"_id": obj_q_id},
                        {"$set": {
                            f"statements.{idx}.validation_status": reval_info.validation_status,
                            f"statements.{idx}.validation_message": reval_info.validation_message,
                            f"statements.{idx}.approval_status": "pending",
                            "validation_status": reval_info.validation_status,
                            "updated_at": utc_now()
                        }}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Pre-execution revalidation failed for Statement #{idx + 1}: {reval_info.validation_message}"
                    )

        # 7. Execute approved statements
        columns: List[str] = []
        rows: List[List[Any]] = []
        total_rows = 0
        total_time_ms = 0
        executed_sqls = []
        is_truncated = False

        max_rows = settings.MAX_QUERY_ROWS
        timeout_sec = settings.QUERY_TIMEOUT_SECONDS

        user_settings = await self.db.user_settings.find_one({"user_id": user_id})
        if user_settings:
            max_rows = min(user_settings.get("rowLimit", max_rows), settings.MAX_ALLOWED_QUERY_ROWS)
            timeout_sec = min(user_settings.get("queryTimeout", timeout_sec), settings.MAX_QUERY_TIMEOUT_SECONDS)

        try:
            for idx in indices_to_run:
                stmt = statements[idx]
                sql_to_run = stmt["sql"]
                executed_sqls.append(sql_to_run)

                if db_type in ("mongodb", "mongo"):
                    # Prefer the structured mql object; fall back to the sql string
                    mql_obj = stmt.get("mql") or stmt.get("sql", "")
                    cols, row_data, elapsed_ms, stmt_truncated = await self._execute_mongodb_query(
                        connection_string=creds["connection_string"],
                        database_name=creds["database_name"],
                        mql=mql_obj,
                        max_rows=max_rows,
                        timeout=timeout_sec
                    )
                else:
                    cols, row_data, elapsed_ms, stmt_truncated = self._execute_single_sql(
                        db_type=creds["db_type"],
                        host=creds["host"],
                        port=creds["port"],
                        username=creds["username"],
                        password=creds["password"],
                        database_name=creds["database_name"],
                        sql=sql_to_run,
                        timeout=timeout_sec,
                        max_rows=max_rows
                    )

                total_time_ms += elapsed_ms
                if stmt_truncated:
                    is_truncated = True

                if cols:
                    columns = cols
                if row_data:
                    rows.extend(row_data)
                    total_rows += len(row_data)

        except Exception as e:
            raw_err = str(e)
            safe_err = sanitize_sensitive_text(
                raw_err,
                known_secrets=[creds.get("password", ""), creds.get("username", "")]
            )
            logger.error(f"Execution error for query {query_id}: {safe_err}")

            now = utc_now()
            await self.db.queries.update_one(
                {"_id": obj_q_id},
                {"$set": {
                    "execution_status": "failed",
                    "execution_error": safe_err,
                    "updated_at": now
                }}
            )
            await self.db.query_logs.insert_one({
                "query_id": query_id,
                "user_id": user_id,
                "event_type": "execution_failed",
                "status": "failed",
                "error_message": safe_err,
                "created_at": now
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database execution error: {safe_err}"
            )

        now = utc_now()
        await self.db.queries.update_one(
            {"_id": obj_q_id},
            {"$set": {
                "execution_status": "success",
                "result_columns": columns,
                "result_rows": rows,
                "row_count": total_rows,
                "execution_time_ms": total_time_ms,
                "executed_at": now,
                "updated_at": now
            }}
        )

        await self.db.database_connections.update_one(
            {"_id": ObjectId(conn_id)},
            {"$inc": {"queries_count": 1}, "$set": {"updated_at": now}}
        )

        # Generate summary
        summary = None
        try:
            llm = get_llm_provider()
            summary = await llm.generate_summary(
                nl_query=query["nl_query"],
                sql="; ".join(executed_sqls),
                row_count=total_rows
            )
        except Exception as summary_err:
            logger.warning(f"Summary generation notice: {summary_err}")
            summary = f"{total_rows} records returned."

        await self.db.query_logs.insert_one({
            "query_id": query_id,
            "user_id": user_id,
            "event_type": "execution_success",
            "status": "success",
            "execution_time_ms": total_time_ms,
            "created_at": now
        })

        stmt_objs = [SQLStatementInfo(**s) for s in statements]
        return QueryResultResponse(
            query_id=query_id,
            status="executed",
            nl_query=query["nl_query"],
            statements=stmt_objs,
            columns=columns,
            rows=rows,
            row_count=total_rows,
            execution_time_ms=total_time_ms,
            summary=summary,
            truncated=is_truncated,
            max_allowed_rows=max_rows
        )

    # ------------------------------------------------------------------
    # Public: estimate_impact — called during query generation/approval
    # ------------------------------------------------------------------

    def estimate_impact(
        self,
        db_type: str,
        host: Optional[str],
        port: Optional[int],
        username: str,
        password: str,
        database_name: str,
        sql: str,
        timeout: int = 10,
    ) -> Optional[int]:
        """
        For DELETE/UPDATE statements, run a SELECT COUNT(*) with the same WHERE
        clause to estimate the number of rows that would be affected.
        Returns None if estimation is not applicable or fails.
        """
        op_upper = sql.strip().split()[0].upper() if sql.strip() else ""
        if op_upper not in ("DELETE", "UPDATE"):
            return None

        try:
            if op_upper == "DELETE":
                m = _DELETE_TABLE_RE.search(sql)
                table = m.group(1) if m else None
            else:  # UPDATE
                m = _UPDATE_TABLE_RE.search(sql)
                table = m.group(1) if m else None

            if not table:
                return None

            where_match = _WHERE_RE.search(sql)
            where_clause = f"WHERE {where_match.group(1).strip()}" if where_match else ""

            # Build count query using appropriate quoting
            if db_type.lower() == "mysql":
                count_sql = f"SELECT COUNT(*) FROM `{table}` {where_clause}"
            else:
                count_sql = f'SELECT COUNT(*) FROM "{table}" {where_clause}'

            cols, row_data, _, _ = self._execute_single_sql(
                db_type=db_type,
                host=host,
                port=port,
                username=username,
                password=password,
                database_name=database_name,
                sql=count_sql,
                timeout=timeout,
                max_rows=1,
            )
            if row_data and row_data[0]:
                return int(row_data[0][0])
        except Exception as e:
            logger.debug(f"Impact estimation failed (non-critical): {e}")

        return None

    # ------------------------------------------------------------------
    # Private: SQL execution (MySQL / PostgreSQL)
    # ------------------------------------------------------------------

    def _execute_single_sql(
        self,
        db_type: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database_name: str,
        sql: str,
        timeout: int = 20,
        max_rows: int = 1000
    ) -> Tuple[List[str], List[List[Any]], int, bool]:
        """Execute a single SQL string against target DB with server-side timeout and fetch limits."""
        start = time.time()
        cols = []
        rows = []
        truncated = False
        db_type_low = db_type.lower()

        if db_type_low == "mysql":
            conn = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=database_name,
                connect_timeout=timeout,
                read_timeout=timeout,
                autocommit=True
            )
            try:
                with conn.cursor() as cursor:
                    # Enforce server-side execution timeout in milliseconds for MySQL
                    try:
                        cursor.execute(f"SET SESSION max_execution_time = {timeout * 1000};")
                    except Exception:
                        pass

                    cursor.execute(sql)
                    if cursor.description:
                        cols = [d[0] for d in cursor.description]
                        fetched = cursor.fetchmany(max_rows + 1)
                        if len(fetched) > max_rows:
                            truncated = True
                            rows = [list(r) for r in fetched[:max_rows]]
                        else:
                            rows = [list(r) for r in fetched]
            finally:
                conn.close()

        elif db_type_low in ["postgresql", "postgres"]:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                dbname=database_name,
                connect_timeout=timeout,
                options=f"-c statement_timeout={timeout * 1000}"
            )
            conn.autocommit = True
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    if cursor.description:
                        cols = [d[0] for d in cursor.description]
                        fetched = cursor.fetchmany(max_rows + 1)
                        if len(fetched) > max_rows:
                            truncated = True
                            rows = [list(r) for r in fetched[:max_rows]]
                        else:
                            rows = [list(r) for r in fetched]
            finally:
                conn.close()
        else:
            raise ValueError(f"Unsupported target database dialect '{db_type}'.")

        elapsed_ms = int((time.time() - start) * 1000)
        return cols, rows, elapsed_ms, truncated

    # ------------------------------------------------------------------
    # Private: MongoDB execution
    # ------------------------------------------------------------------

    async def _execute_mongodb_query(
        self,
        connection_string: str,
        database_name: str,
        mql,  # Either a structured dict (from LLM) or a raw string (legacy)
        max_rows: int = 1000,
        timeout: int = 20,
    ) -> Tuple[List[str], List[List[Any]], int, bool]:
        """
        Execute a MongoDB operation.

        Accepts two forms for `mql`:
          1. Structured dict (preferred, produced by the LLM service):
             {
               "collection": "users",
               "operation": "find" | "aggregate" | "count" | "insert_one" |
                             "insert_many" | "update_one" | "update_many" |
                             "delete_one" | "delete_many",
               "filter": {...},
               "projection": {...},
               "update": {...},
               "document": {...},
               "documents": [...],
               "pipeline": [...],
               "options": {...}
             }
          2. Legacy JSON/string form (for backwards-compatibility with saved queries):
             - JSON object  → find with that filter
             - JSON array   → aggregate pipeline (or [collection, pipeline])
             - Bare string  → find({}) on that collection name
        """
        import pymongo
        import json as _json

        start = time.time()
        truncated = False

        try:
            client = pymongo.MongoClient(
                connection_string,
                serverSelectionTimeoutMS=timeout * 1000,
                connectTimeoutMS=timeout * 1000,
                socketTimeoutMS=timeout * 1000,
            )
            mdb = client[database_name]

            # --- Resolve structured vs legacy MQL ---
            if isinstance(mql, dict):
                # New structured form
                collection_name = mql.get("collection") or (
                    mdb.list_collection_names()[0] if mdb.list_collection_names() else "documents"
                )
                operation = mql.get("operation", "find").lower()
                filt = mql.get("filter") or {}
                projection = mql.get("projection") or None
                update = mql.get("update") or {}
                document = mql.get("document") or {}
                documents = mql.get("documents") or []
                pipeline = mql.get("pipeline") or []
                options = mql.get("options") or {}
            else:
                # Legacy string form — parse for backwards compatibility
                mql_stripped = str(mql).strip().strip(";").strip()
                collection_name = None
                pipeline = None
                filt = {}
                projection = None
                update = {}
                document = {}
                documents = []
                options = {}

                if mql_stripped.startswith("["):
                    parsed = _json.loads(mql_stripped)
                    if parsed and isinstance(parsed[0], str):
                        collection_name = parsed[0]
                        pipeline = parsed[1] if len(parsed) > 1 else []
                    else:
                        collection_name = (
                            mdb.list_collection_names()[0]
                            if mdb.list_collection_names() else "results"
                        )
                        pipeline = parsed
                    operation = "aggregate"
                elif mql_stripped.startswith("{"):
                    parsed_obj = _json.loads(mql_stripped)
                    # Check if it's a full structured MQL object
                    if "operation" in parsed_obj and "collection" in parsed_obj:
                        collection_name = parsed_obj.get("collection")
                        operation = parsed_obj.get("operation", "find").lower()
                        filt = parsed_obj.get("filter") or {}
                        projection = parsed_obj.get("projection") or None
                        update = parsed_obj.get("update") or {}
                        document = parsed_obj.get("document") or {}
                        documents = parsed_obj.get("documents") or []
                        pipeline = parsed_obj.get("pipeline") or []
                    else:
                        # Plain find filter object
                        filt = parsed_obj
                        collection_name = (
                            mdb.list_collection_names()[0]
                            if mdb.list_collection_names() else "results"
                        )
                        operation = "find"
                else:
                    collection_name = mql_stripped.strip("`\"'")
                    operation = "find"
                    filt = {}

            col = mdb[collection_name]
            docs: List[Dict] = []
            result_meta: Optional[Dict] = None  # for write operation results

            # --- Dispatch operation ---
            if operation == "find":
                cursor = col.find(filt, projection).limit(max_rows + 1)
                docs = list(cursor)

            elif operation == "count":
                count = col.count_documents(filt)
                client.close()
                elapsed_ms = int((time.time() - start) * 1000)
                return ["count"], [[str(count)]], elapsed_ms, False

            elif operation == "aggregate":
                if not pipeline:
                    pipeline = [{"$match": filt}]
                docs = list(col.aggregate(pipeline))

            elif operation == "insert_one":
                res = col.insert_one(document)
                client.close()
                elapsed_ms = int((time.time() - start) * 1000)
                return ["inserted_id", "acknowledged"], [[str(res.inserted_id), str(res.acknowledged)]], elapsed_ms, False

            elif operation == "insert_many":
                res = col.insert_many(documents)
                client.close()
                elapsed_ms = int((time.time() - start) * 1000)
                ids = ", ".join(str(i) for i in res.inserted_ids)
                return ["inserted_count", "inserted_ids"], [[str(len(res.inserted_ids)), ids]], elapsed_ms, False

            elif operation in ("update_one", "update_many"):
                if not update:
                    raise ValueError(f"update field is required for {operation}.")
                if operation == "update_one":
                    res = col.update_one(filt, update)
                else:
                    res = col.update_many(filt, update)
                client.close()
                elapsed_ms = int((time.time() - start) * 1000)
                return (
                    ["matched_count", "modified_count", "acknowledged"],
                    [[str(res.matched_count), str(res.modified_count), str(res.acknowledged)]],
                    elapsed_ms, False
                )

            elif operation in ("delete_one", "delete_many"):
                if operation == "delete_one":
                    res = col.delete_one(filt)
                else:
                    res = col.delete_many(filt)
                client.close()
                elapsed_ms = int((time.time() - start) * 1000)
                return (
                    ["deleted_count", "acknowledged"],
                    [[str(res.deleted_count), str(res.acknowledged)]],
                    elapsed_ms, False
                )

            else:
                # Unknown operation — fall back to find
                logger.warning(f"Unknown MongoDB operation '{operation}', falling back to find.")
                docs = list(col.find(filt).limit(max_rows + 1))

            client.close()

            if len(docs) > max_rows:
                truncated = True
                docs = docs[:max_rows]

            if not docs:
                elapsed_ms = int((time.time() - start) * 1000)
                return [], [], elapsed_ms, truncated

            # Flatten docs into columnar rows
            all_keys: List[str] = []
            seen: set = set()
            for doc in docs:
                for k in doc.keys():
                    if k not in seen:
                        all_keys.append(k)
                        seen.add(k)

            columns = all_keys
            rows = []
            for doc in docs:
                row = []
                for k in columns:
                    val = doc.get(k)
                    if isinstance(val, (dict, list)):
                        import json as _j
                        val = _j.dumps(val, default=str)
                    elif val is not None:
                        val = str(val)
                    row.append(val)
                rows.append(row)

            elapsed_ms = int((time.time() - start) * 1000)
            return columns, rows, elapsed_ms, truncated

        except Exception as e:
            raise RuntimeError(f"MongoDB query execution error: {e}") from e
