import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import pymysql
try:
    import psycopg2
except ImportError:
    psycopg2 = None

from app.core.security import sanitize_sensitive_text
from app.schemas.database import ColumnSchema, DatabaseSchemaResponse, TableSchema
from app.schemas.schema import SchemaPermissionsResponse, TablePermissionConfig, ColumnPermissionConfig
from app.services.database_service import DatabaseService

logger = logging.getLogger("querymind.schema_service")

# Maximum documents to sample per collection when discovering MongoDB schema.
_MONGO_SAMPLE_SIZE = 20


class SchemaService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.db_service = DatabaseService(db)

    async def discover_schema(self, conn_id: str, user_id: str) -> DatabaseSchemaResponse:
        """Discover schema from the target database (MySQL or MongoDB)."""
        creds = await self.db_service.get_connection_credentials(conn_id, user_id)
        db_type = creds["db_type"]

        tables: List[TableSchema] = []

        try:
            if db_type == "mysql":
                tables = self._discover_mysql_schema(
                    host=creds["host"],
                    port=creds["port"],
                    user=creds["username"],
                    password=creds["password"],
                    db_name=creds["database_name"],
                )
            elif db_type in ("postgresql", "postgres"):
                tables = self._discover_postgresql_schema(
                    host=creds["host"],
                    port=creds["port"],
                    user=creds["username"],
                    password=creds["password"],
                    db_name=creds["database_name"],
                )
            elif db_type == "mongodb":
                tables = await self._discover_mongodb_schema(
                    uri=creds["connection_string"],
                    db_name=creds["database_name"],
                )
            else:
                raise ValueError(
                    f"Unsupported database type '{db_type}'."
                )
        except HTTPException:
            raise
        except Exception as e:
            safe_err = sanitize_sensitive_text(
                str(e),
                known_secrets=[
                    creds.get("password", ""),
                    creds.get("username", ""),
                    creds.get("connection_string", ""),
                ],
            )
            logger.error(f"Schema discovery failed for conn {conn_id}: {safe_err}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Schema discovery failed: {safe_err}",
            )

        # Update collections_count in the connection document
        try:
            await self.db.database_connections.update_one(
                {"_id": ObjectId(creds["id"])},
                {"$set": {"collections_count": len(tables)}},
            )
        except Exception:
            pass

        return DatabaseSchemaResponse(
            database_id=conn_id,
            database_name=creds["database_name"],
            db_type=db_type,
            tables=tables,
        )

    # ------------------------------------------------------------------
    # MySQL
    # ------------------------------------------------------------------

    def _discover_mysql_schema(
        self, host: str, port: int, user: str, password: str, db_name: str
    ) -> List[TableSchema]:
        """Query MySQL INFORMATION_SCHEMA for tables and columns."""
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE';",
                    (db_name,),
                )
                table_rows = cursor.fetchall()
                tables: List[TableSchema] = []

                for t in table_rows:
                    t_name = t["TABLE_NAME"]
                    cursor.execute(
                        """
                        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION;
                        """,
                        (db_name, t_name),
                    )
                    col_rows = cursor.fetchall()
                    cols = [
                        ColumnSchema(
                            name=c["COLUMN_NAME"],
                            type=c["DATA_TYPE"],
                            nullable=(c["IS_NULLABLE"] == "YES"),
                            primary_key=(c["COLUMN_KEY"] == "PRI"),
                            foreign_key=None,
                        )
                        for c in col_rows
                    ]
                    tables.append(TableSchema(name=t_name, columns=cols))
                return tables
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # PostgreSQL
    # ------------------------------------------------------------------

    def _discover_postgresql_schema(
        self, host: str, port: int, user: str, password: str, db_name: str
    ) -> List[TableSchema]:
        """Query PostgreSQL information_schema for tables and columns."""
        ssl_mode = "require" if (".neon.tech" in host or "supabase" in host or "aws" in host) else "prefer"
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            dbname=db_name,
            connect_timeout=10,
            sslmode=ssl_mode,
        )
        try:
            with conn.cursor() as cursor:
                # List all user tables (exclude pg_catalog and information_schema)
                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                    """
                )
                table_rows = cursor.fetchall()
                tables: List[TableSchema] = []

                for (t_name,) in table_rows:
                    cursor.execute(
                        """
                        SELECT
                            c.column_name,
                            c.data_type,
                            c.is_nullable,
                            CASE WHEN pk.column_name IS NOT NULL THEN TRUE ELSE FALSE END AS is_pk
                        FROM information_schema.columns c
                        LEFT JOIN (
                            SELECT kcu.column_name
                            FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage kcu
                              ON tc.constraint_name = kcu.constraint_name
                              AND tc.table_schema = kcu.table_schema
                            WHERE tc.constraint_type = 'PRIMARY KEY'
                              AND tc.table_name = %s
                              AND tc.table_schema = 'public'
                        ) pk ON c.column_name = pk.column_name
                        WHERE c.table_name = %s AND c.table_schema = 'public'
                        ORDER BY c.ordinal_position;
                        """,
                        (t_name, t_name),
                    )
                    col_rows = cursor.fetchall()
                    cols = [
                        ColumnSchema(
                            name=col_name,
                            type=data_type,
                            nullable=(is_nullable == "YES"),
                            primary_key=bool(is_pk),
                            foreign_key=None,
                        )
                        for col_name, data_type, is_nullable, is_pk in col_rows
                    ]
                    tables.append(TableSchema(name=t_name, columns=cols))
                return tables
        finally:
            conn.close()

    # ------------------------------------------------------------------

    async def _discover_mongodb_schema(
        self, uri: str, db_name: str
    ) -> List[TableSchema]:
        """
        Discover MongoDB collections and infer field names/types by sampling
        up to _MONGO_SAMPLE_SIZE documents per collection.

        Only basic BSON types are inferred; no full collection scans are performed.
        """
        import pymongo

        if not db_name:
            raise ValueError(
                "A database name is required to discover a MongoDB schema. "
                "Specify the database name when adding the connection."
            )

        try:
            client = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=8000,
            )
            target_db = client[db_name]

            collection_names: List[str] = target_db.list_collection_names()
            tables: List[TableSchema] = []

            for col_name in sorted(collection_names):
                try:
                    sample_docs = list(
                        target_db[col_name].find({}, limit=_MONGO_SAMPLE_SIZE)
                    )
                    field_types: Dict[str, str] = {}

                    for doc in sample_docs:
                        for field, value in doc.items():
                            if field not in field_types:
                                field_types[field] = _bson_type_name(value)

                    cols = [
                        ColumnSchema(
                            name=fname,
                            type=ftype,
                            nullable=True,
                            primary_key=(fname == "_id"),
                            foreign_key=None,
                        )
                        for fname, ftype in sorted(
                            field_types.items(), key=lambda x: (x[0] != "_id", x[0])
                        )
                    ]
                    tables.append(TableSchema(name=col_name, columns=cols))
                except Exception as col_err:
                    logger.warning(
                        f"Could not sample collection '{col_name}': {col_err}"
                    )
                    # Include collection with no columns rather than skip it entirely
                    tables.append(TableSchema(name=col_name, columns=[]))

            client.close()
            return tables

        except Exception as e:
            # Re-raise so the caller can sanitize and wrap it
            raise RuntimeError(f"MongoDB schema discovery error: {e}") from e

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    async def get_permissions(self, conn_id: str, user_id: str) -> SchemaPermissionsResponse:
        """Retrieve stored schema permissions or generate defaults."""
        schema_info = await self.discover_schema(conn_id, user_id)

        table_configs: List[TablePermissionConfig] = []
        for t in schema_info.tables:
            stored = await self.db.schema_access.find_one(
                {"database_id": conn_id, "table_name": t.name}
            )
            allowed_ops = (
                stored.get("allowed_operations", ["SELECT", "INSERT", "UPDATE", "DELETE"])
                if stored
                else ["SELECT", "INSERT", "UPDATE", "DELETE"]
            )
            is_allowed = stored.get("allowed", True) if stored else True

            col_configs = []
            for c in t.columns:
                col_stored = (
                    stored.get("columns", {}).get(c.name)
                    if stored and "columns" in stored
                    else None
                )
                c_allowed = col_stored.get("allowed", True) if col_stored else True
                c_ops = (
                    col_stored.get("allowed_operations", ["SELECT", "INSERT", "UPDATE", "DELETE"])
                    if col_stored
                    else ["SELECT", "INSERT", "UPDATE", "DELETE"]
                )
                col_configs.append(
                    ColumnPermissionConfig(
                        column_name=c.name,
                        allowed=c_allowed,
                        allowed_operations=c_ops,
                    )
                )

            table_configs.append(
                TablePermissionConfig(
                    table_name=t.name,
                    allowed=is_allowed,
                    allowed_operations=allowed_ops,
                    columns=col_configs,
                )
            )

        return SchemaPermissionsResponse(database_id=conn_id, tables=table_configs)

    async def update_permissions(
        self, conn_id: str, tables: List[TablePermissionConfig], user_id: str
    ):
        """Save updated table/column permissions to MongoDB."""
        for t in tables:
            cols_dict = {}
            if t.columns:
                for c in t.columns:
                    cols_dict[c.column_name] = {
                        "allowed": c.allowed,
                        "allowed_operations": c.allowed_operations,
                    }

            doc = {
                "database_id": conn_id,
                "table_name": t.table_name,
                "allowed": t.allowed,
                "allowed_operations": t.allowed_operations,
                "columns": cols_dict,
            }

            await self.db.schema_access.update_one(
                {"database_id": conn_id, "table_name": t.table_name},
                {"$set": doc},
                upsert=True,
            )

    async def _get_matching_conn_ids(self, conn_id: str) -> List[str]:
        """Find all database_connection IDs pointing to the same physical host and database."""
        matching_conn_ids = [conn_id]
        try:
            from bson import ObjectId
            target_conn = await self.db.database_connections.find_one({"_id": ObjectId(conn_id)})
            if target_conn:
                host = target_conn.get("host")
                db_name = target_conn.get("database_name")
                conn_str = target_conn.get("connection_string")
                query_filters = []
                if host and db_name:
                    query_filters.append({"host": host, "database_name": db_name})
                if conn_str:
                    query_filters.append({"connection_string": conn_str})
                if query_filters:
                    async for oc in self.db.database_connections.find({"$or": query_filters}):
                        matching_conn_ids.append(str(oc["_id"]))
        except Exception as e:
            logger.warning(f"Error resolving matching connection IDs for {conn_id}: {e}")
        return list(set(matching_conn_ids))

    async def get_permissions_dict(
        self,
        conn_id: str,
        discovered_tables: Optional[List[TableSchema]] = None
    ) -> Dict[str, Any]:
        """Fetch all stored permissions as a lookup dict for SQLValidator, merging across same-target databases."""
        matching_conn_ids = await self._get_matching_conn_ids(conn_id)
        cursor = self.db.schema_access.find({"database_id": {"$in": matching_conn_ids}})
        tables_dict: Dict[str, Any] = {}
        async for doc in cursor:
            t_name = doc.get("table_name", "").lower()
            if t_name:
                cols: Dict[str, Any] = tables_dict.get(t_name, {}).get("columns", {})
                for col_name, c_data in doc.get("columns", {}).items():
                    col_key = col_name.lower()
                    existing_col = cols.get(col_key, {})
                    is_allowed = existing_col.get("allowed", True) and c_data.get("allowed", True)
                    cols[col_key] = {
                        "allowed": is_allowed,
                        "target_role": c_data.get("target_role", existing_col.get("target_role", "all")),
                        "allowed_operations": [
                            op.upper()
                            for op in c_data.get(
                                "allowed_operations",
                                existing_col.get("allowed_operations", ["SELECT", "INSERT", "UPDATE", "DELETE"]),
                            )
                        ],
                    }
                existing_table = tables_dict.get(t_name, {})
                table_allowed = existing_table.get("allowed", True) and doc.get("allowed", True)
                tables_dict[t_name] = {
                    "allowed": table_allowed,
                    "allowed_operations": [
                        op.upper()
                        for op in doc.get(
                            "allowed_operations",
                            existing_table.get("allowed_operations", ["SELECT", "INSERT", "UPDATE", "DELETE"]),
                        )
                    ],
                    "columns": cols,
                }

        # If discovered_tables are provided, ensure all legitimate physical tables from the DB are permitted
        if discovered_tables:
            for t in discovered_tables:
                t_name = getattr(t, "name", None) or getattr(t, "table_name", None)
                if not t_name:
                    continue
                t_key = t_name.lower()
                if t_key not in tables_dict:
                    cols_dict = {}
                    for col in getattr(t, "columns", []):
                        c_name = getattr(col, "name", None) or getattr(col, "column_name", None) or str(col)
                        cols_dict[c_name.lower()] = {
                            "allowed": True,
                            "target_role": "all",
                            "allowed_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"]
                        }
                    tables_dict[t_key] = {
                        "allowed": True,
                        "allowed_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                        "columns": cols_dict
                    }

        return {"tables": tables_dict}

    async def apply_natural_language_rule(
        self, conn_id: str, user_id: str, rule_text: str
    ) -> Dict[str, Any]:
        """Parse natural language security rule via LLM and enforce it in schema_access across all matching DB connections."""
        from app.services.llm_service import get_llm_provider

        # 1. Discover target schema
        schema_info = await self.discover_schema(conn_id, user_id)

        # Build schema representation
        schema_lines = []
        for t in schema_info.tables:
            col_names = [f"{c.name}:{c.type}" for c in t.columns]
            schema_lines.append(f"Table: {t.name} ({', '.join(col_names)})")
        schema_text = "\n".join(schema_lines)

        # 2. Parse rule with LLM
        llm = get_llm_provider()
        parsed = await llm.parse_security_rule(rule_text=rule_text, schema_text=schema_text)

        table_name = parsed.get("table_name")
        column_name = parsed.get("column_name")
        action = parsed.get("action", "restrict_column")
        allowed = parsed.get("allowed", False)
        restricted_ops = parsed.get("restricted_operations", ["DELETE"])

        # Determine target_role accurately from rule_text
        rule_lower = rule_text.lower()
        if "viewer" in rule_lower and "admin" not in rule_lower and "all" not in rule_lower:
            target_role = "viewer"
        elif "analyst" in rule_lower and "admin" not in rule_lower and "all" not in rule_lower:
            target_role = "analyst"
        elif "admin" in rule_lower and "viewer" not in rule_lower and "all" not in rule_lower:
            target_role = "admin"
        else:
            # Default to 'all' so restrictions apply universally unless scoped to a specific role
            target_role = "all"

        # Normalize table name against discovered schema tables to handle plurals (e.g. faculties -> faculty)
        if schema_info and schema_info.tables:
            matched_table = None
            t_candidates = [table_name] if table_name else []
            for tbl in schema_info.tables:
                tbl_low = tbl.name.lower()
                for cand in t_candidates + rule_lower.split():
                    cand_clean = cand.strip(" ,.;:'\"`").lower()
                    if not cand_clean:
                        continue
                    if cand_clean == tbl_low:
                        matched_table = tbl.name
                        break
                    if cand_clean.rstrip("s") == tbl_low.rstrip("s") or cand_clean.replace("ies", "y") == tbl_low:
                        matched_table = tbl.name
                        break
                if matched_table:
                    break
            if matched_table:
                table_name = matched_table

            # Normalize column name against discovered table columns
            if table_name:
                for tbl in schema_info.tables:
                    if tbl.name.lower() == table_name.lower():
                        for c in tbl.columns:
                            c_low = c.name.lower()
                            if column_name and column_name.lower() == c_low:
                                column_name = c.name
                                break
                            if c_low in rule_lower:
                                column_name = c.name
                                break

        now = datetime.now(timezone.utc)
        rule_doc = {
            "database_id": conn_id,
            "created_by": user_id,
            "rule_text": rule_text.strip(),
            "table_name": table_name,
            "column_name": column_name,
            "action": action,
            "target_role": target_role,
            "allowed": allowed,
            "restricted_operations": restricted_ops,
            "summary": parsed.get("summary", rule_text),
            "created_at": now
        }

        # 3. Apply into schema_access collection across all matching connection IDs (same physical DB)
        matching_conn_ids = await self._get_matching_conn_ids(conn_id)
        for cid in matching_conn_ids:
            if table_name:
                if column_name:
                    col_key = column_name.lower()
                    await self.db.schema_access.update_one(
                        {"database_id": cid, "table_name": table_name},
                        {
                            "$set": {
                                f"columns.{col_key}.allowed": allowed,
                                f"columns.{col_key}.allowed_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"] if allowed else [],
                                f"columns.{col_key}.target_role": target_role,
                                f"columns.{col_key}.rule_text": rule_text,
                                "updated_at": now
                            },
                            "$setOnInsert": {
                                "database_id": cid,
                                "table_name": table_name,
                                "allowed": True,
                                "allowed_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                                "created_at": now
                            }
                        },
                        upsert=True
                    )
                elif action == "restrict_operation":
                    all_ops = ["SELECT", "INSERT", "UPDATE", "DELETE"]
                    remaining_ops = [op for op in all_ops if op.upper() not in [ro.upper() for ro in restricted_ops]]
                    await self.db.schema_access.update_one(
                        {"database_id": cid, "table_name": table_name},
                        {
                            "$set": {
                                "allowed_operations": remaining_ops,
                                "rule_text": rule_text,
                                "updated_at": now
                            },
                            "$setOnInsert": {
                                "database_id": cid,
                                "table_name": table_name,
                                "allowed": True,
                                "columns": {},
                                "created_at": now
                            }
                        },
                        upsert=True
                    )
                else:
                    await self.db.schema_access.update_one(
                        {"database_id": cid, "table_name": table_name},
                        {
                            "$set": {
                                "allowed": allowed,
                                "rule_text": rule_text,
                                "updated_at": now
                            },
                            "$setOnInsert": {
                                "database_id": cid,
                                "table_name": table_name,
                                "allowed_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                                "columns": {},
                                "created_at": now
                            }
                        },
                        upsert=True
                    )

        # 4. Save into natural_language_security_rules collection
        res = await self.db.natural_language_security_rules.insert_one(rule_doc)
        rule_doc["id"] = str(res.inserted_id)
        if "_id" in rule_doc:
            del rule_doc["_id"]
        if "created_at" in rule_doc and hasattr(rule_doc["created_at"], "isoformat"):
            rule_doc["created_at"] = rule_doc["created_at"].isoformat()
        return rule_doc

    async def get_natural_language_rules(self, conn_id: str) -> List[Dict[str, Any]]:
        rules = []
        matching_conn_ids = await self._get_matching_conn_ids(conn_id)
        cursor = self.db.natural_language_security_rules.find({"database_id": {"$in": matching_conn_ids}}).sort("created_at", -1)
        async for r in cursor:
            r["id"] = str(r["_id"])
            del r["_id"]
            if "created_at" in r and hasattr(r["created_at"], "isoformat"):
                r["created_at"] = r["created_at"].isoformat()
            rules.append(r)
        return rules

    async def delete_natural_language_rule(self, conn_id: str, rule_id: str) -> bool:
        obj_id = ObjectId(rule_id)
        matching_conn_ids = await self._get_matching_conn_ids(conn_id)
        rule = await self.db.natural_language_security_rules.find_one({"_id": obj_id, "database_id": {"$in": matching_conn_ids}})
        if not rule:
            return False

        table_name = rule.get("table_name")
        column_name = rule.get("column_name")
        action = rule.get("action")

        for cid in matching_conn_ids:
            if table_name:
                if column_name:
                    col_key = column_name.lower()
                    await self.db.schema_access.update_one(
                        {"database_id": cid, "table_name": table_name},
                        {"$set": {f"columns.{col_key}.allowed": True, f"columns.{col_key}.allowed_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"]}}
                    )
                elif action == "restrict_operation":
                    await self.db.schema_access.update_one(
                        {"database_id": cid, "table_name": table_name},
                        {"$set": {"allowed_operations": ["SELECT", "INSERT", "UPDATE", "DELETE"]}}
                    )
                else:
                    await self.db.schema_access.update_one(
                        {"database_id": cid, "table_name": table_name},
                        {"$set": {"allowed": True}}
                    )

        await self.db.natural_language_security_rules.delete_one({"_id": obj_id})
        return True


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _bson_type_name(value: Any) -> str:
    """Map a Python/BSON value to a human-readable type string."""
    from bson import ObjectId as BsonObjectId, Decimal128
    import datetime as _dt

    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "double"
    if isinstance(value, str):
        return "string"
    if isinstance(value, _dt.datetime):
        return "date"
    if isinstance(value, BsonObjectId):
        return "ObjectId"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, bytes):
        return "binary"
    if value is None:
        return "null"
    try:
        if isinstance(value, Decimal128):
            return "decimal"
    except Exception:
        pass
    return type(value).__name__
