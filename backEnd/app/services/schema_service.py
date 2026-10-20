import logging
from typing import Any, Dict, List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import pymysql
import psycopg2

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
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            dbname=db_name,
            connect_timeout=10,
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

    async def get_permissions_dict(self, conn_id: str) -> Dict[str, Any]:
        """Fetch all stored permissions as a lookup dict for SQLValidator."""
        cursor = self.db.schema_access.find({"database_id": conn_id})
        tables_dict: Dict[str, Any] = {}
        async for doc in cursor:
            t_name = doc.get("table_name", "").lower()
            if t_name:
                cols: Dict[str, Any] = {}
                for col_name, c_data in doc.get("columns", {}).items():
                    cols[col_name.lower()] = {
                        "allowed": c_data.get("allowed", True),
                        "allowed_operations": [
                            op.upper()
                            for op in c_data.get(
                                "allowed_operations",
                                ["SELECT", "INSERT", "UPDATE", "DELETE"],
                            )
                        ],
                    }
                tables_dict[t_name] = {
                    "allowed": doc.get("allowed", True),
                    "allowed_operations": [
                        op.upper()
                        for op in doc.get(
                            "allowed_operations",
                            ["SELECT", "INSERT", "UPDATE", "DELETE"],
                        )
                    ],
                    "columns": cols,
                }
        return {"tables": tables_dict}


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
