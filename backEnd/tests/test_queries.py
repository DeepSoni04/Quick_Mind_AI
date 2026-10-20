import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_query_generation_and_approval_workflow(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory,
    mock_schema_discovery
):
    # 1. Register analyst user
    user_doc, token, headers = await test_user_factory(
        email="analyst@example.com",
        name="Query Analyst",
        role="analyst"
    )

    # 2. Add DB Connection via DB connection factory (real DB connection registered)
    conn_id, _ = await test_db_connection_factory(user_id=user_doc["_id"])

    # 3. Test Query Generation
    gen_payload = {
        "nl_query": "Show all students from Ahmedabad",
        "input_type": "text",
        "language": "English",
        "database_id": conn_id
    }
    res = await async_client.post("/api/queries/generate", json=gen_payload, headers=headers)
    assert res.status_code == 200
    q_data = res.json()
    assert "query_id" in q_data
    assert len(q_data["statements"]) >= 1
    assert q_data["statements"][0]["approval_status"] == "pending"

    query_id = q_data["query_id"]

    # 4. Attempt Execution without Approval -> MUST BE REJECTED (403)!
    res = await async_client.post(f"/api/queries/{query_id}/execute", headers=headers)
    assert res.status_code == 403

    # 5. Approve Statement
    res = await async_client.post(f"/api/queries/{query_id}/approve", json={"statement_index": 0}, headers=headers)
    assert res.status_code == 200
    assert res.json()["statements"][0]["approval_status"] == "approved"

    # 6. Test Edited SQL Re-validation
    edit_payload = {"edited_sql": "SELECT * FROM students WHERE city = 'Surat';"}
    res = await async_client.post(f"/api/queries/{query_id}/revalidate", json=edit_payload, headers=headers)
    assert res.status_code == 200
    # Prior approval MUST be reset to pending!
    assert res.json()["statements"][0]["approval_status"] == "pending"

