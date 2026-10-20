import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_audit_policies(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory,
    mock_schema_discovery
):
    # 1. Register Viewer user and add a DB connection
    viewer_doc, viewer_token, viewer_headers = await test_user_factory(
        email="viewer@example.com",
        name="Viewer User",
        role="viewer"
    )
    viewer_conn_id, _ = await test_db_connection_factory(user_id=viewer_doc["_id"])

    # 2. Viewer attempts DELETE operation -> MUST be blocked by AST validator!
    gen_payload = {
        "nl_query": "Delete all inactive student records.",
        "database_id": viewer_conn_id
    }
    res = await async_client.post("/api/queries/generate", json=gen_payload, headers=viewer_headers)
    assert res.status_code == 200
    q_data = res.json()
    assert q_data["status"] == "blocked"
    assert "Viewer role does not have permission" in q_data["statements"][0]["validation_message"]

    # 3. Create Analyst user explicitly (no auto-promotion loophole)
    analyst_doc, analyst_token, analyst_headers = await test_user_factory(
        email="analyst_test@example.com",
        name="Analyst User",
        role="analyst"
    )
    analyst_conn_id, _ = await test_db_connection_factory(user_id=analyst_doc["_id"])

    # Analyst attempts Malicious DDL Injection Attempt (DROP TABLE) -> MUST be blocked with Prohibited operation!
    res = await async_client.post(
        "/api/queries/generate",
        json={"nl_query": "Show all students", "database_id": analyst_conn_id},
        headers=analyst_headers
    )
    assert res.status_code == 200
    q_id = res.json()["query_id"]

    edit_payload = {"edited_sql": "DROP TABLE students;"}
    res = await async_client.post(f"/api/queries/{q_id}/revalidate", json=edit_payload, headers=analyst_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "blocked"
    assert "Prohibited operation" in res.json()["statements"][0]["validation_message"]

