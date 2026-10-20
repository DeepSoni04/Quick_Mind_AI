"""
Tests for Feature 1: MongoDB and MySQL database type selection.

Covers:
- db_type validation (valid / invalid values)
- MongoDB URI validation
- MySQL param validation
- Connector selection (mocked connectivity)
- Credential encryption / no passwords in responses
- Connection ownership enforcement
- List / get / delete flows
- Backward-compatible credential retrieval
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock
from app.services.database_service import DatabaseService
from app.core.encryption import encrypt_secret, decrypt_secret


# ---------------------------------------------------------------------------
# Unit tests — validation helpers (no DB or network needed)
# ---------------------------------------------------------------------------

class TestMongoDBURIValidation:
    """DatabaseService._validate_mongodb_uri"""

    def test_valid_standard_uri(self):
        ok, err = DatabaseService._validate_mongodb_uri("mongodb://localhost:27017")
        assert ok, err

    def test_valid_uri_with_credentials(self):
        ok, err = DatabaseService._validate_mongodb_uri(
            "mongodb://user:pass@cluster.example.com:27017/mydb"
        )
        assert ok, err

    def test_valid_srv_uri(self):
        ok, err = DatabaseService._validate_mongodb_uri(
            "mongodb+srv://user:pass@cluster.mongodb.net/mydb"
        )
        assert ok, err

    def test_valid_srv_no_credentials(self):
        ok, err = DatabaseService._validate_mongodb_uri(
            "mongodb+srv://cluster.mongodb.net/mydb"
        )
        assert ok, err

    def test_empty_uri_rejected(self):
        ok, err = DatabaseService._validate_mongodb_uri("")
        assert not ok
        assert "required" in err.lower()

    def test_none_uri_rejected(self):
        ok, err = DatabaseService._validate_mongodb_uri(None)
        assert not ok

    def test_invalid_scheme_rejected(self):
        ok, err = DatabaseService._validate_mongodb_uri("mysql://localhost:3306/db")
        assert not ok

    def test_http_uri_rejected(self):
        ok, err = DatabaseService._validate_mongodb_uri("http://example.com")
        assert not ok


class TestMongoDBURISanitization:
    """URI redaction before logging."""

    def test_credentials_redacted(self):
        uri = "mongodb://admin:SuperSecret@cluster.example.com/db"
        safe = DatabaseService._sanitize_mongodb_uri_for_log(uri)
        assert "SuperSecret" not in safe
        assert "admin" not in safe
        assert "cluster.example.com" in safe

    def test_no_credentials_unchanged(self):
        uri = "mongodb://localhost:27017/db"
        safe = DatabaseService._sanitize_mongodb_uri_for_log(uri)
        assert "localhost" in safe


class TestMySQLParamValidation:
    """DatabaseService._validate_mysql_params"""

    def test_valid_params(self):
        ok, err = DatabaseService._validate_mysql_params(
            {"host": "127.0.0.1", "port": 3306, "database_name": "college_db"}
        )
        assert ok, err

    def test_missing_host(self):
        ok, err = DatabaseService._validate_mysql_params(
            {"host": "", "port": 3306, "database_name": "mydb"}
        )
        assert not ok
        assert "host" in err.lower()

    def test_missing_database(self):
        ok, err = DatabaseService._validate_mysql_params(
            {"host": "localhost", "port": 3306, "database_name": ""}
        )
        assert not ok

    def test_port_out_of_range(self):
        ok, err = DatabaseService._validate_mysql_params(
            {"host": "localhost", "port": 99999, "database_name": "db"}
        )
        assert not ok
        assert "65535" in err or "port" in err.lower()

    def test_zero_port(self):
        ok, err = DatabaseService._validate_mysql_params(
            {"host": "localhost", "port": 0, "database_name": "db"}
        )
        assert not ok


class TestDatabaseTypeDispatch:
    """test_target_connection selects correct connector."""

    def test_unknown_type_returns_error(self):
        svc = DatabaseService(db=None)
        # 'oracle' is genuinely unsupported; postgresql is now a valid type
        ok, msg = svc.test_target_connection({"db_type": "oracle"})
        assert not ok
        assert "Unsupported" in msg or "unsupported" in msg.lower()

    def test_mongodb_dispatched(self):
        svc = DatabaseService(db=None)
        with patch.object(
            DatabaseService, "_test_mongodb_connection", return_value=(True, "ok")
        ) as mock_mongo:
            ok, msg = svc.test_target_connection(
                {"db_type": "mongodb", "connection_string": "mongodb://localhost"}
            )
            mock_mongo.assert_called_once()
            assert ok

    def test_mysql_dispatched(self):
        svc = DatabaseService(db=None)
        with patch.object(
            DatabaseService, "_test_mysql_connection", return_value=(True, "ok")
        ) as mock_mysql:
            ok, msg = svc.test_target_connection(
                {
                    "db_type": "mysql",
                    "host": "localhost",
                    "port": 3306,
                    "database_name": "db",
                    "username": "u",
                    "password": "p",
                }
            )
            mock_mysql.assert_called_once()
            assert ok

    def test_postgresql_dispatched(self):
        svc = DatabaseService(db=None)
        with patch.object(
            DatabaseService, "_test_postgresql_connection", return_value=(True, "ok")
        ) as mock_pg:
            ok, msg = svc.test_target_connection(
                {
                    "db_type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "database_name": "pgdb",
                    "username": "postgres",
                    "password": "secret",
                }
            )
            mock_pg.assert_called_once()
            assert ok


class TestCredentialEncryption:
    """Credentials must be encrypted at rest; secrets not returned in responses."""

    def test_encrypt_decrypt_roundtrip(self):
        secret = "S3cr3tP@$$w0rd!"
        enc = encrypt_secret(secret)
        assert enc != secret
        assert decrypt_secret(enc) == secret

    def test_mongodb_uri_not_plain_text_in_doc(self):
        uri = "mongodb://user:hunter2@localhost/db"
        enc = encrypt_secret(uri)
        assert uri not in enc


# ---------------------------------------------------------------------------
# db_type Pydantic schema validation
# ---------------------------------------------------------------------------

class TestDatabaseSchemaValidation:
    """DatabaseConnectionCreate rejects unsupported db_type values."""

    def test_mongodb_accepted(self):
        from app.schemas.database import DatabaseConnectionCreate
        obj = DatabaseConnectionCreate(name="Test", db_type="mongodb")
        assert obj.db_type == "mongodb"

    def test_mysql_accepted(self):
        from app.schemas.database import DatabaseConnectionCreate
        obj = DatabaseConnectionCreate(name="Test", db_type="mysql")
        assert obj.db_type == "mysql"

    def test_postgresql_accepted(self):
        from app.schemas.database import DatabaseConnectionCreate
        # postgresql is now a fully supported type (added in Phase 2)
        obj = DatabaseConnectionCreate(name="Test", db_type="postgresql")
        assert obj.db_type == "postgresql"

    def test_unknown_type_rejected(self):
        from pydantic import ValidationError
        from app.schemas.database import DatabaseConnectionCreate
        with pytest.raises(ValidationError):
            DatabaseConnectionCreate(name="Test", db_type="oracle")

    def test_test_request_invalid_type_rejected(self):
        from pydantic import ValidationError
        from app.schemas.database import DatabaseConnectionTestRequest
        with pytest.raises(ValidationError):
            DatabaseConnectionTestRequest(db_type="redis")


# ---------------------------------------------------------------------------
# Integration tests — connection CRUD with mock connectivity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_connections_returns_only_owner(
    async_client, test_user_factory, test_db_connection_factory
):
    """User A cannot see User B's connections."""
    user_a, _, headers_a = await test_user_factory(email="a@test.com")
    user_b, _, headers_b = await test_user_factory(email="b@test.com")

    conn_id_a, _ = await test_db_connection_factory(user_a["_id"], name="A's DB")
    conn_id_b, _ = await test_db_connection_factory(user_b["_id"], name="B's DB")

    resp = await async_client.get("/api/databases", headers=headers_a)
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert conn_id_a in ids
    assert conn_id_b not in ids


@pytest.mark.asyncio
async def test_get_connection_other_user_404(
    async_client, test_user_factory, test_db_connection_factory
):
    """User B cannot access User A's connection by ID."""
    user_a, _, headers_a = await test_user_factory(email="owner@test.com")
    _, _, headers_b      = await test_user_factory(email="attacker@test.com")

    conn_id, _ = await test_db_connection_factory(user_a["_id"])

    resp = await async_client.get(f"/api/databases/{conn_id}", headers=headers_b)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_connection_other_user_denied(
    async_client, test_user_factory, test_db_connection_factory
):
    """User B cannot delete User A's connection."""
    user_a, _, _ = await test_user_factory(email="victim@test.com")
    _, _, headers_b = await test_user_factory(email="attacker@test.com")

    conn_id, _ = await test_db_connection_factory(user_a["_id"])

    resp = await async_client.delete(f"/api/databases/{conn_id}", headers=headers_b)
    assert resp.status_code in (403, 404)


@pytest.mark.asyncio
async def test_password_not_in_list_response(
    async_client, test_user_factory, test_db_connection_factory
):
    """Passwords / URIs must not appear in list response."""
    user, _, headers = await test_user_factory(email="nopass@test.com")
    await test_db_connection_factory(user["_id"], db_type="mysql")

    resp = await async_client.get("/api/databases", headers=headers)
    assert resp.status_code == 200
    body_text = resp.text
    assert "secret" not in body_text
    assert "hunter2" not in body_text
    assert "password" not in body_text.lower() or '"password"' not in body_text


@pytest.mark.asyncio
async def test_mongodb_connection_doc_has_no_plain_uri(
    async_client, test_user_factory, test_db_connection_factory
):
    """MongoDB connection list should not expose the raw URI."""
    user, _, headers = await test_user_factory(email="mongo@test.com")
    await test_db_connection_factory(user["_id"], db_type="mongodb")

    resp = await async_client.get("/api/databases", headers=headers)
    assert resp.status_code == 200
    body_text = resp.text
    # The plaintext URI should never appear in the response
    assert "mongodb://localhost:27017" not in body_text


@pytest.mark.asyncio
async def test_create_mongodb_connection_mocked(
    async_client, test_user_factory
):
    """Creating a MongoDB connection calls the MongoDB connector, not MySQL."""
    _, _, headers = await test_user_factory(email="mongocreate@test.com")

    with patch.object(
        DatabaseService, "_test_mongodb_connection", return_value=(True, "ok")
    ) as mock_mongo:
        resp = await async_client.post(
            "/api/databases",
            json={
                "name": "My MongoDB",
                "db_type": "mongodb",
                "connection_string": "mongodb://localhost:27017",
                "database_name": "testdb",
            },
            headers=headers,
        )
        mock_mongo.assert_called_once()

    assert resp.status_code == 200
    data = resp.json()
    assert data["db_type"] == "mongodb"
    assert data["name"] == "My MongoDB"
    # No password field in response
    assert "password" not in data
    assert "encrypted" not in str(data)


@pytest.mark.asyncio
async def test_create_mysql_connection_mocked(
    async_client, test_user_factory
):
    """Creating a MySQL connection calls the MySQL connector."""
    _, _, headers = await test_user_factory(email="mysqlcreate@test.com")

    with patch.object(
        DatabaseService, "_test_mysql_connection", return_value=(True, "ok")
    ) as mock_mysql:
        resp = await async_client.post(
            "/api/databases",
            json={
                "name": "My MySQL",
                "db_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database_name": "college_db",
                "username": "root",
                "password": "secret",
            },
            headers=headers,
        )
        mock_mysql.assert_called_once()

    assert resp.status_code == 200
    data = resp.json()
    assert data["db_type"] == "mysql"
    assert "password" not in data
    assert "secret" not in resp.text


@pytest.mark.asyncio
async def test_create_connection_invalid_type_rejected(
    async_client, test_user_factory
):
    """Creating with db_type=oracle (truly unsupported) should be rejected by schema validation."""
    _, _, headers = await test_user_factory(email="badtype@test.com")

    resp = await async_client.post(
        "/api/databases",
        json={
            "name": "Bad DB",
            "db_type": "oracle",
            "host": "localhost",
            "port": 1521,
            "database_name": "db",
        },
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_connection_test_endpoint_mongodb(
    async_client, test_user_factory
):
    """POST /api/databases/test with mongodb type dispatches to MongoDB connector."""
    _, _, headers = await test_user_factory(email="testep@test.com")

    with patch.object(
        DatabaseService, "_test_mongodb_connection", return_value=(True, "Pong!")
    ):
        resp = await async_client.post(
            "/api/databases/test",
            json={
                "db_type": "mongodb",
                "connection_string": "mongodb://localhost:27017",
            },
            headers=headers,
        )

    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_connection_test_endpoint_mysql_failure(
    async_client, test_user_factory
):
    """POST /api/databases/test with mysql returns failure without leaking password."""
    _, _, headers = await test_user_factory(email="mysqlfail@test.com")

    with patch.object(
        DatabaseService,
        "_test_mysql_connection",
        return_value=(False, "Connection refused"),
    ):
        resp = await async_client.post(
            "/api/databases/test",
            json={
                "db_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database_name": "db",
                "username": "root",
                "password": "hunter2",
            },
            headers=headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "hunter2" not in resp.text


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(async_client):
    """All database endpoints require authentication."""
    resp = await async_client.get("/api/databases")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_existing_mysql_connection_credentials_retrieval(
    test_user_factory, test_db_connection_factory
):
    """get_connection_credentials returns decrypted MySQL credentials."""
    from app.core.database import db_instance
    user, _, _ = await test_user_factory(email="creds@test.com")
    conn_id, _ = await test_db_connection_factory(user["_id"], db_type="mysql")

    svc = DatabaseService(db_instance.db)
    creds = await svc.get_connection_credentials(conn_id, user["_id"])

    assert creds["db_type"] == "mysql"
    assert creds["username"] == "root"
    assert creds["password"] == "secret"


@pytest.mark.asyncio
async def test_existing_mongodb_connection_credentials_retrieval(
    test_user_factory, test_db_connection_factory
):
    """get_connection_credentials returns decrypted MongoDB URI."""
    from app.core.database import db_instance
    user, _, _ = await test_user_factory(email="mongocreds@test.com")
    conn_id, _ = await test_db_connection_factory(user["_id"], db_type="mongodb")

    svc = DatabaseService(db_instance.db)
    creds = await svc.get_connection_credentials(conn_id, user["_id"])

    assert creds["db_type"] == "mongodb"
    assert "mongodb://" in creds["connection_string"]


@pytest.mark.asyncio
async def test_create_postgresql_connection_mocked(
    async_client, test_user_factory
):
    """Creating a PostgreSQL connection calls the PostgreSQL connector."""
    _, _, headers = await test_user_factory(email="pgcreate@test.com")

    with patch.object(
        DatabaseService, "_test_postgresql_connection", return_value=(True, "ok")
    ) as mock_pg:
        resp = await async_client.post(
            "/api/databases",
            json={
                "name": "My PostgreSQL",
                "db_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database_name": "app_db",
                "username": "postgres",
                "password": "pgpass",
            },
            headers=headers,
        )
        mock_pg.assert_called_once()

    assert resp.status_code == 200
    data = resp.json()
    assert data["db_type"] == "postgresql"
    assert data["name"] == "My PostgreSQL"
    assert "password" not in data
    assert "pgpass" not in resp.text
