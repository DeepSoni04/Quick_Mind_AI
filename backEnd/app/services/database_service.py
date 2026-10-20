import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import pymysql
import psycopg2

from app.core.encryption import encrypt_secret, decrypt_secret
from app.core.security import sanitize_sensitive_text
from app.schemas.database import (
    DatabaseConnectionCreate,
    DatabaseConnectionResponse,
    DatabaseConnectionTestRequest,
    SUPPORTED_DB_TYPES,
)
from app.utils.helpers import utc_now, format_relative_time

logger = logging.getLogger("querymind.database_service")

# Minimal MongoDB URI pattern — validates scheme and non-empty host/authority portion.
# Does NOT require credentials because local dev MongoDB often has no auth.
_MONGODB_URI_RE = re.compile(
    r"^mongodb(\+srv)?://"        # scheme
    r"[^\s@/?#]"                   # at least one char for host or userinfo
    r"[^@]*"                       # rest of userinfo or host
    r"(@[^\s/?#]*)?"               # optional @host
    r"(/[^\s?#]*)?"                # optional /database
    r"(\?[^\s#]*)?$",              # optional query string
    re.IGNORECASE,
)


class DatabaseService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ------------------------------------------------------------------
    # MongoDB-specific helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_mongodb_uri(uri: str) -> Tuple[bool, str]:
        """Syntactically validate a MongoDB URI without connecting."""
        if not uri or not uri.strip():
            return False, "MongoDB connection URI is required."
        uri = uri.strip()
        if not _MONGODB_URI_RE.match(uri):
            return False, (
                "Invalid MongoDB URI. Expected format: "
                "mongodb://[user:pass@]host[:port][/database] "
                "or mongodb+srv://..."
            )
        return True, ""

    @staticmethod
    def _extract_mongodb_database(uri: str, explicit_db: Optional[str]) -> str:
        """Extract the database name from a MongoDB URI, or return the explicit override."""
        if explicit_db and explicit_db.strip():
            return explicit_db.strip()
        # Parse path segment: mongodb://host/dbname?...
        try:
            no_scheme = re.sub(r"^mongodb(\+srv)?://", "", uri, flags=re.IGNORECASE)
            if "/" in no_scheme:
                db_part = no_scheme.split("/", 1)[1]
                db_part = db_part.split("?")[0].strip()
                if db_part:
                    return db_part
        except Exception:
            pass
        return ""

    @staticmethod
    def _sanitize_mongodb_uri_for_log(uri: str) -> str:
        """Remove credentials from MongoDB URI before logging."""
        return re.sub(r"://([^:@]+):([^@]+)@", "://<user>:<redacted>@", uri)

    # ------------------------------------------------------------------
    # MySQL-specific helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_mysql_params(params: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate required MySQL connection fields."""
        host = params.get("host") or ""
        if not host.strip():
            return False, "MySQL host is required."
        port = params.get("port")
        if port is None:
            return False, "MySQL port is required."
        try:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                return False, "Port must be between 1 and 65535."
        except (TypeError, ValueError):
            return False, "Port must be a valid integer."
        db_name = params.get("database_name") or params.get("database") or ""
        if not db_name.strip():
            return False, "Database name is required for MySQL."
        return True, ""

    # ------------------------------------------------------------------
    # Connection testing
    # ------------------------------------------------------------------

    def test_target_connection(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Test connectivity for MongoDB, MySQL, or PostgreSQL depending on db_type."""
        db_type = (params.get("db_type") or "mysql").lower().strip()

        if db_type == "mongodb":
            return self._test_mongodb_connection(params)
        elif db_type == "mysql":
            return self._test_mysql_connection(params)
        elif db_type in ("postgresql", "postgres"):
            return self._test_postgresql_connection(params)
        else:
            return False, f"Unsupported database type '{db_type}'. Must be one of: {', '.join(sorted(SUPPORTED_DB_TYPES))}."

    @staticmethod
    def _test_mongodb_connection(params: Dict[str, Any]) -> Tuple[bool, str]:
        """Test MongoDB connectivity using pymongo (sync, brief timeout)."""
        uri = params.get("connection_string") or params.get("connectionString") or ""

        ok, err = DatabaseService._validate_mongodb_uri(uri)
        if not ok:
            return False, err

        safe_uri = DatabaseService._sanitize_mongodb_uri_for_log(uri)
        try:
            import pymongo
            client = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
            )
            # ismaster is a lightweight ping that works without auth on standalone instances
            client.admin.command("ping")
            client.close()
            logger.info(f"MongoDB connection test successful: {safe_uri}")
            return True, "Connection successful — MongoDB database reachable."
        except Exception as e:
            safe_err = sanitize_sensitive_text(str(e), known_secrets=[uri])
            logger.warning(f"MongoDB connection test failed for {safe_uri}: {safe_err}")
            return False, f"Could not connect to MongoDB: {safe_err}"

    @staticmethod
    def _test_mysql_connection(params: Dict[str, Any]) -> Tuple[bool, str]:
        """Test MySQL connectivity using pymysql."""
        host = (params.get("host") or "").strip()
        port = params.get("port") or 3306
        database_name = (
            params.get("database_name") or params.get("database") or ""
        ).strip()
        username = (params.get("username") or "").strip()
        password = params.get("password") or ""

        valid, err = DatabaseService._validate_mysql_params({
            "host": host, "port": port, "database_name": database_name
        })
        if not valid:
            return False, err

        try:
            conn = pymysql.connect(
                host=host,
                port=int(port),
                user=username,
                password=password,
                database=database_name,
                connect_timeout=5,
            )
            conn.close()
            logger.info(f"MySQL connection test successful: {host}:{port}/{database_name}")
            return True, "Connection successful — MySQL database reachable."
        except Exception as e:
            safe_err = sanitize_sensitive_text(str(e), known_secrets=[password, username])
            logger.warning(f"MySQL connection test failed for {host}:{port}/{database_name}: {safe_err}")
            return False, f"Could not connect to MySQL: {safe_err}"

    @staticmethod
    def _test_postgresql_connection(params: Dict[str, Any]) -> Tuple[bool, str]:
        """Test PostgreSQL connectivity using psycopg2."""
        host = (params.get("host") or "").strip()
        port = params.get("port") or 5432
        database_name = (
            params.get("database_name") or params.get("database") or ""
        ).strip()
        username = (params.get("username") or "").strip()
        password = params.get("password") or ""

        if not host:
            return False, "PostgreSQL host is required."
        if not database_name:
            return False, "Database name is required for PostgreSQL."

        try:
            conn = psycopg2.connect(
                host=host,
                port=int(port),
                user=username,
                password=password,
                dbname=database_name,
                connect_timeout=5,
            )
            conn.close()
            logger.info(f"PostgreSQL connection test successful: {host}:{port}/{database_name}")
            return True, "Connection successful — PostgreSQL database reachable."
        except Exception as e:
            safe_err = sanitize_sensitive_text(str(e), known_secrets=[password, username])
            logger.warning(f"PostgreSQL connection test failed for {host}:{port}/{database_name}: {safe_err}")
            return False, f"Could not connect to PostgreSQL: {safe_err}"

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_connection(
        self, user_id: str, req: DatabaseConnectionCreate
    ) -> DatabaseConnectionResponse:
        """Create and store an encrypted database connection."""
        db_type = req.db_type  # already validated by Pydantic

        now = utc_now()

        if db_type == "mongodb":
            uri = (req.connection_string or req.connectionString or "").strip()
            ok, err = self._validate_mongodb_uri(uri)
            if not ok:
                raise HTTPException(status_code=400, detail=err)

            database_name = self._extract_mongodb_database(
                uri, req.database_name or req.database
            )

            # Test connectivity
            ok, msg = self._test_mongodb_connection({"connection_string": uri})
            if not ok:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Connection test failed: {msg}",
                )

            doc = {
                "created_by": user_id,
                "name": req.name.strip(),
                "db_type": "mongodb",
                "host": None,
                "port": None,
                "database_name": database_name,
                "encrypted_uri": encrypt_secret(uri),
                "status": "Connected",
                "queries_count": 0,
                "created_at": now,
                "updated_at": now,
            }

        else:  # mysql or postgresql
            host = (req.host or "").strip()
            # Default port differs by db type
            default_port = 5432 if db_type in ("postgresql", "postgres") else 3306
            port = req.port or default_port
            database_name = (req.database_name or req.database or "").strip()
            username = (req.username or "").strip()
            password = req.password or ""

            valid, err = self._validate_mysql_params({
                "host": host, "port": port, "database_name": database_name
            })
            if not valid:
                raise HTTPException(status_code=400, detail=err)

            if db_type in ("postgresql", "postgres"):
                ok, msg = self._test_postgresql_connection({
                    "host": host,
                    "port": port,
                    "database_name": database_name,
                    "username": username,
                    "password": password,
                })
                canonical_type = "postgresql"
            else:
                ok, msg = self._test_mysql_connection({
                    "host": host,
                    "port": port,
                    "database_name": database_name,
                    "username": username,
                    "password": password,
                })
                canonical_type = "mysql"

            if not ok:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Connection test failed: {msg}",
                )

            doc = {
                "created_by": user_id,
                "name": req.name.strip(),
                "db_type": canonical_type,
                "host": host,
                "port": int(port),
                "database_name": database_name,
                "encrypted_username": encrypt_secret(username),
                "encrypted_password": encrypt_secret(password),
                "status": "Connected",
                "queries_count": 0,
                "created_at": now,
                "updated_at": now,
            }

        res = await self.db.database_connections.insert_one(doc)
        conn_id = str(res.inserted_id)

        return self._doc_to_response(conn_id, doc)

    async def list_connections(self, user_id: str) -> List[DatabaseConnectionResponse]:
        """List active database connections for user (no credentials in response)."""
        cursor = self.db.database_connections.find({"created_by": user_id})
        connections = []
        async for doc in cursor:
            connections.append(self._doc_to_response(str(doc["_id"]), doc))
        return connections

    async def get_connection(self, conn_id: str, user_id: str) -> DatabaseConnectionResponse:
        """Get a single connection (no credentials) owned by user."""
        doc = await self._get_doc(conn_id, user_id)
        return self._doc_to_response(str(doc["_id"]), doc)

    async def get_connection_credentials(
        self, conn_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Internal helper: retrieve and decrypt target database credentials."""
        doc = await self._get_doc(conn_id, user_id)
        db_type = doc.get("db_type", "mysql")

        creds: Dict[str, Any] = {
            "id": str(doc["_id"]),
            "name": doc["name"],
            "db_type": db_type,
            "host": doc.get("host"),
            "port": doc.get("port"),
            "database_name": doc.get("database_name", ""),
        }

        if db_type == "mongodb":
            creds["connection_string"] = decrypt_secret(doc.get("encrypted_uri", ""))
            creds["username"] = ""
            creds["password"] = ""
        else:
            creds["username"] = decrypt_secret(doc.get("encrypted_username", ""))
            creds["password"] = decrypt_secret(doc.get("encrypted_password", ""))
            creds["connection_string"] = ""

        return creds

    async def delete_connection(self, conn_id: str, user_id: str):
        """Disconnect and delete a connection."""
        try:
            obj_id = ObjectId(conn_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid connection ID.")

        res = await self.db.database_connections.delete_one(
            {"_id": obj_id, "created_by": user_id}
        )
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Database connection not found.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_doc(self, conn_id: str, user_id: str) -> Dict[str, Any]:
        try:
            obj_id = ObjectId(conn_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid connection ID.")

        doc = await self.db.database_connections.find_one(
            {"_id": obj_id, "created_by": user_id}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Database connection not found.")
        return doc

    @staticmethod
    def _doc_to_response(conn_id: str, doc: Dict[str, Any]) -> DatabaseConnectionResponse:
        db_type = doc.get("db_type", "mysql")
        return DatabaseConnectionResponse(
            id=conn_id,
            name=doc["name"],
            db_type=db_type,
            type=db_type,
            host=doc.get("host"),
            port=doc.get("port"),
            database_name=doc.get("database_name", ""),
            database=doc.get("database_name", ""),
            status=doc.get("status", "Connected"),
            collections_count=doc.get("collections_count", 0),
            collectionsCount=doc.get("collections_count", 0),
            queries_count=doc.get("queries_count", 0),
            queriesCount=doc.get("queries_count", 0),
            last_synced=format_relative_time(doc.get("updated_at")),
            lastSynced=format_relative_time(doc.get("updated_at")),
            created_at=(doc.get("created_at") or utc_now()).isoformat(),
            updated_at=(doc.get("updated_at") or utc_now()).isoformat(),
        )
