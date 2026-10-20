import pytest
from httpx import AsyncClient
from app.core.database import db_instance


@pytest.mark.asyncio
async def test_frontend_auth_and_health_endpoints(async_client: AsyncClient, test_user_factory):
    # Health endpoint
    res = await async_client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    # Register
    reg_payload = {"name": "UI Tester", "email": "uitest@example.com", "password": "password123"}
    res = await async_client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 200
    reg_data = res.json()
    assert "access_token" in reg_data
    assert "user" in reg_data
    assert reg_data["user"]["name"] == "UI Tester"
    token = reg_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Me
    res = await async_client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "uitest@example.com"

    # Login
    res = await async_client.post("/api/auth/login", json={"email": "uitest@example.com", "password": "password123"})
    assert res.status_code == 200
    assert "access_token" in res.json()

    # Logout
    res = await async_client.post("/api/auth/logout", headers=headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Successfully logged out"


@pytest.mark.asyncio
async def test_frontend_database_endpoints(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory,
    monkeypatch
):
    user, token, headers = await test_user_factory(role="analyst")

    # Mock connection test for API creation test
    from app.services.database_service import DatabaseService
    monkeypatch.setattr(DatabaseService, "test_target_connection", lambda self, params: (True, "Connection OK"))
    monkeypatch.setattr(DatabaseService, "_test_mysql_connection", staticmethod(lambda params: (True, "Connection OK")))
    monkeypatch.setattr(DatabaseService, "_test_mongodb_connection", staticmethod(lambda params: (True, "Connection OK")))

    # POST /api/databases (accepts camelCase connectionString or discrete fields)
    db_payload = {
        "name": "Frontend Test MySQL",
        "db_type": "mysql",
        "host": "localhost",
        "port": 3306,
        "database_name": "college_db",
        "username": "root",
        "password": "secret_password"
    }
    res = await async_client.post("/api/databases", json=db_payload, headers=headers)
    assert res.status_code == 200
    db_data = res.json()
    conn_id = db_data["id"]
    assert db_data["name"] == "Frontend Test MySQL"

    # GET /api/databases
    res = await async_client.get("/api/databases", headers=headers)
    assert res.status_code == 200
    dbs = res.json()
    assert len(dbs) == 1
    assert dbs[0]["id"] == conn_id

    # GET /api/databases/{id}
    res = await async_client.get(f"/api/databases/{conn_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == conn_id

    # POST /api/databases/{id}/test
    res = await async_client.post(f"/api/databases/{conn_id}/test", headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # DELETE /api/databases/{id}
    res = await async_client.delete(f"/api/databases/{conn_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Database connection removed"


@pytest.mark.asyncio
async def test_frontend_query_and_session_and_history_endpoints(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory,
    mock_schema_discovery
):
    user, token, headers = await test_user_factory(role="analyst")
    conn_id, _ = await test_db_connection_factory(user_id=user["_id"])

    # 1. Sessions: POST, GET, PUT, DELETE
    res = await async_client.post("/api/sessions", json={"name": "Sprint UI"}, headers=headers)
    assert res.status_code == 200
    sess_id = res.json()["id"]

    res = await async_client.get("/api/sessions", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    res = await async_client.get(f"/api/sessions/{sess_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == sess_id

    res = await async_client.put(f"/api/sessions/{sess_id}", json={"name": "Sprint UI - Updated"}, headers=headers)
    assert res.status_code == 200

    # 2. Queries: POST /generate, POST /approve, POST /revalidate
    gen_payload = {
        "nl_query": "List all active students",
        "input_type": "text",
        "language": "English",
        "database_id": conn_id,
        "session_id": sess_id
    }
    res = await async_client.post("/api/queries/generate", json=gen_payload, headers=headers)
    assert res.status_code == 200
    q_data = res.json()
    q_id = q_data["query_id"]

    # Approve
    res = await async_client.post(f"/api/queries/{q_id}/approve", json={"statement_index": 0}, headers=headers)
    assert res.status_code == 200

    # Revalidate
    res = await async_client.post(
        f"/api/queries/{q_id}/revalidate",
        json={"edited_sql": "SELECT id, name FROM students;"},
        headers=headers
    )
    assert res.status_code == 200

    # 3. History: GET /api/history, GET /api/history/{id}, DELETE /api/history/{id}, DELETE /api/history/clear
    from datetime import datetime, timezone
    log_doc = {
        "user_id": user["_id"],
        "database_id": conn_id,
        "sql": "SELECT id, name FROM students LIMIT 10;",
        "status": "success",
        "row_count": 5,
        "execution_time_ms": 15.0,
        "results": [{"id": 1, "name": "Student A"}],
        "created_at": datetime.now(timezone.utc)
    }
    insert_res = await db_instance.db.query_logs.insert_one(log_doc)
    log_id = str(insert_res.inserted_id)

    res = await async_client.get("/api/history", headers=headers)
    assert res.status_code == 200
    history_items = res.json()
    assert len(history_items) >= 1

    res = await async_client.get(f"/api/history/{log_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == log_id

    res = await async_client.delete(f"/api/history/{log_id}", headers=headers)
    assert res.status_code == 200

    res = await async_client.delete("/api/history/clear", headers=headers)
    assert res.status_code == 200

    # Cleanup session
    res = await async_client.delete(f"/api/sessions/{sess_id}", headers=headers)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_frontend_admin_stats_and_settings(
    async_client: AsyncClient,
    test_user_factory
):
    admin_doc, admin_token, admin_headers = await test_user_factory(role="admin", email="admin_stat@example.com")

    # Admin stats
    res = await async_client.get("/api/admin/stats", headers=admin_headers)
    assert res.status_code == 200
    stats = res.json()
    assert "total_users" in stats
    assert "total_queries" in stats
    assert "total_databases" in stats

    # Settings
    res = await async_client.get("/api/settings", headers=admin_headers)
    assert res.status_code == 200
    settings = res.json()
    assert "row_limit" in settings
    assert "query_timeout" in settings
