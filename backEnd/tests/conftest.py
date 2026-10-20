import os
os.environ["LLM_PROVIDER"] = "mock"
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.core.config import settings
settings.LLM_PROVIDER = "mock"
from app.main import app
from app.core.database import db_instance, connect_to_mongo
from app.core.security import hash_password, create_access_token
from app.core.encryption import encrypt_secret


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Setup test database and clean collections between tests."""
    await connect_to_mongo()
    if db_instance.db is not None:
        await db_instance.db.users.delete_many({})
        await db_instance.db.database_connections.delete_many({})
        await db_instance.db.queries.delete_many({})
        await db_instance.db.query_sessions.delete_many({})
        await db_instance.db.query_logs.delete_many({})
        await db_instance.db.schema_access.delete_many({})
        await db_instance.db.user_settings.delete_many({})
    yield


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user_factory():
    """Factory fixture to create users with specific roles and return (user_doc, token, headers)."""
    async def _create_user(email="user@example.com", name="Test User", role="viewer", password="password123"):
        now = datetime.now(timezone.utc)
        user_doc = {
            "name": name,
            "email": email.lower(),
            "password_hash": hash_password(password),
            "role": role,
            "status": "Active",
            "queries_run": 0,
            "success_rate": 100.0,
            "created_at": now,
            "updated_at": now
        }
        res = await db_instance.db.users.insert_one(user_doc)
        user_id = str(res.inserted_id)
        token = create_access_token(data={"sub": user_id, "email": email.lower(), "role": role})
        headers = {"Authorization": f"Bearer {token}"}
        user_doc["_id"] = user_id
        return user_doc, token, headers

    return _create_user


@pytest_asyncio.fixture
async def test_db_connection_factory():
    """Factory fixture to insert a mock target database connection document directly."""
    async def _create_db_conn(user_id: str, name="Test College DB", db_type="mysql"):
        from app.core.encryption import encrypt_secret
        now = datetime.now(timezone.utc)
        if db_type == "mongodb":
            doc = {
                "created_by": user_id,
                "name": name,
                "db_type": "mongodb",
                "host": None,
                "port": None,
                "database_name": "college_db",
                "encrypted_uri": encrypt_secret("mongodb://localhost:27017/college_db"),
                "status": "Connected",
                "queries_count": 0,
                "created_at": now,
                "updated_at": now,
            }
        else:
            doc = {
                "created_by": user_id,
                "name": name,
                "db_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database_name": "college_db",
                "credentials_ref": f"cred_{user_id}",
                "encrypted_username": encrypt_secret("root"),
                "encrypted_password": encrypt_secret("secret"),
                "status": "Connected",
                "queries_count": 0,
                "created_at": now,
                "updated_at": now,
            }
        res = await db_instance.db.database_connections.insert_one(doc)
        return str(res.inserted_id), doc

    return _create_db_conn


@pytest.fixture
def mock_schema_discovery(monkeypatch):
    """Fixture to mock target DB live schema discovery for offline tests."""
    from app.services.schema_service import SchemaService
    from app.schemas.database import DatabaseSchemaResponse, TableSchema, ColumnSchema

    async def _mock_discover(self, conn_id: str, user_id: str):
        return DatabaseSchemaResponse(
            database_id=conn_id,
            database_name="college_db",
            db_type="mysql",
            tables=[
                TableSchema(
                    name="students",
                    columns=[
                        ColumnSchema(name="id", type="INT", nullable=False, primary_key=True),
                        ColumnSchema(name="name", type="VARCHAR(100)", nullable=False),
                        ColumnSchema(name="city", type="VARCHAR(100)", nullable=True),
                        ColumnSchema(name="status", type="VARCHAR(50)", nullable=True),
                    ]
                )
            ]
        )

    monkeypatch.setattr(SchemaService, "discover_schema", _mock_discover)


