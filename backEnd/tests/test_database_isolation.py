import pytest
from httpx import AsyncClient
from app.core.database import db_instance
from app.services.database_service import DatabaseService


@pytest.mark.asyncio
async def test_database_connection_user_isolation(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory
):
    # User A
    user_a, token_a, headers_a = await test_user_factory(email="user_a@example.com")
    conn_id_a, _ = await test_db_connection_factory(user_id=user_a["_id"], name="User A DB")

    # User B
    user_b, token_b, headers_b = await test_user_factory(email="user_b@example.com")
    conn_id_b, _ = await test_db_connection_factory(user_id=user_b["_id"], name="User B DB")

    # User A listing connections: should only see User A's connection
    res = await async_client.get("/api/databases", headers=headers_a)
    assert res.status_code == 200
    db_list_a = res.json()
    assert len(db_list_a) == 1
    assert db_list_a[0]["id"] == conn_id_a

    # User B listing connections: should only see User B's connection
    res = await async_client.get("/api/databases", headers=headers_b)
    assert res.status_code == 200
    db_list_b = res.json()
    assert len(db_list_b) == 1
    assert db_list_b[0]["id"] == conn_id_b

    # User A cannot retrieve User B's connection (404)
    res = await async_client.get(f"/api/databases/{conn_id_b}", headers=headers_a)
    assert res.status_code == 404

    # User A cannot delete User B's connection (404)
    res = await async_client.delete(f"/api/databases/{conn_id_b}", headers=headers_a)
    assert res.status_code == 404

    # User B can delete User B's connection (200)
    res = await async_client.delete(f"/api/databases/{conn_id_b}", headers=headers_b)
    assert res.status_code == 200

    # User B connection is gone
    check_b = await db_instance.db.database_connections.find_one({"_id": conn_id_b})
    assert check_b is None


@pytest.mark.asyncio
async def test_schema_discovery_failure_without_fake_fallback(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory
):
    # Create user and connection pointing to non-existent DB host
    user, _, headers = await test_user_factory(email="schema_test@example.com")
    conn_id, _ = await test_db_connection_factory(user_id=user["_id"], name="Unreachable DB")

    # Schema discovery must fail clearly with 400 Bad Request, NOT return fake demo tables!
    res = await async_client.get(f"/api/databases/{conn_id}/schema", headers=headers)
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert any(phrase in detail.lower() for phrase in ["schema discovery failed", "could not", "connection", "failed"])


def test_connection_param_validation():
    """Test that MongoDB URI and MySQL discrete params are validated properly."""
    # MongoDB URI
    ok, err = DatabaseService._validate_mongodb_uri(
        "mongodb+srv://user:pass@cluster.mongodb.net/analytics_db"
    )
    assert ok, err

    # MySQL discrete parameters
    ok, err = DatabaseService._validate_mysql_params({
        "host": "192.168.1.100",
        "port": 3307,
        "database_name": "shop_db",
    })
    assert ok, err

    # Invalid MongoDB URI
    ok, err = DatabaseService._validate_mongodb_uri("postgresql://host:5432/db")
    assert not ok

    # Missing MySQL host
    ok, err = DatabaseService._validate_mysql_params({
        "host": "",
        "port": 3306,
        "database_name": "db",
    })
    assert not ok

