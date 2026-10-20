import pytest
from httpx import AsyncClient
from app.core.database import db_instance


@pytest.mark.asyncio
async def test_session_lifecycle_and_closed_session_protection(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory,
    mock_schema_discovery
):
    user, _, headers = await test_user_factory(role="analyst")
    conn_id, _ = await test_db_connection_factory(user_id=user["_id"])

    # 1. Create active session
    res = await async_client.post(
        "/api/sessions",
        json={"name": "Analytics Sprint 1"},
        headers=headers
    )
    assert res.status_code == 200
    sess = res.json()
    sess_id = sess["id"]
    assert sess["status"] == "active"
    assert sess["name"] == "Analytics Sprint 1"

    # 2. Query in active session works
    res = await async_client.post(
        "/api/queries/generate",
        json={"nl_query": "Show students", "database_id": conn_id, "session_id": sess_id},
        headers=headers
    )
    assert res.status_code == 200

    # 3. Rename session
    res = await async_client.put(
        f"/api/sessions/{sess_id}",
        json={"name": "Analytics Sprint 1 - Renamed"},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Analytics Sprint 1 - Renamed"

    # 4. Close session
    from bson import ObjectId
    await db_instance.db.query_sessions.update_one(
        {"_id": ObjectId(sess_id)},
        {"$set": {"status": "closed"}}
    )

    # 5. Query in closed session must be rejected with 400 Bad Request
    res = await async_client.post(
        "/api/queries/generate",
        json={"nl_query": "Show students", "database_id": conn_id, "session_id": sess_id},
        headers=headers
    )
    assert res.status_code == 400
    assert "closed session" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_session_cross_user_isolation(
    async_client: AsyncClient,
    test_user_factory
):
    user_a, _, headers_a = await test_user_factory(email="user_a_sess@example.com")
    user_b, _, headers_b = await test_user_factory(email="user_b_sess@example.com")

    # User A creates session
    res = await async_client.post("/api/sessions", json={"name": "User A Session"}, headers=headers_a)
    sess_id_a = res.json()["id"]

    # User B cannot view User A's session (404)
    res = await async_client.get(f"/api/sessions/{sess_id_a}", headers=headers_b)
    assert res.status_code == 404

    # User B cannot update User A's session (404)
    res = await async_client.put(f"/api/sessions/{sess_id_a}", json={"name": "Hacked"}, headers=headers_b)
    assert res.status_code == 404

    # User B cannot delete User A's session (404)
    res = await async_client.delete(f"/api/sessions/{sess_id_a}", headers=headers_b)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_csv_export_format_and_authorization(
    async_client: AsyncClient,
    test_user_factory
):
    from bson import ObjectId
    from datetime import datetime, timezone
    user, _, headers = await test_user_factory()
    now = datetime.now(timezone.utc)

    # Insert an executed query log with results
    log_doc = {
        "user_id": user["_id"],
        "database_id": "test_db_id",
        "sql": "SELECT id, name, city FROM students LIMIT 2;",
        "status": "success",
        "row_count": 2,
        "execution_time_ms": 12.5,
        "results": [
            {"id": 1, "name": "Aarav Patel", "city": "Ahmedabad"},
            {"id": 2, "name": "Priya Shah", "city": "Surat"}
        ],
        "created_at": now
    }
    insert_res = await db_instance.db.query_logs.insert_one(log_doc)
    log_id = str(insert_res.inserted_id)

    # User can export to CSV
    res = await async_client.get(f"/api/export/{log_id}/csv", headers=headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment; filename=" in res.headers["content-disposition"]
    csv_text = res.text
    assert "id,name,city" in csv_text
    assert "Aarav Patel" in csv_text
    assert "Priya Shah" in csv_text

    # Other user cannot export it (404)
    _, _, other_headers = await test_user_factory(email="other_export@example.com")
    res = await async_client.get(f"/api/export/{log_id}/csv", headers=other_headers)
    assert res.status_code == 404
