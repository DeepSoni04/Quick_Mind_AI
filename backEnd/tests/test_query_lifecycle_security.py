import pytest
from httpx import AsyncClient
from app.core.database import db_instance


@pytest.mark.asyncio
async def test_query_generation_requires_database(async_client: AsyncClient, test_user_factory):
    # User with NO database connection configured
    user, _, headers = await test_user_factory(email="nodb@example.com")
    
    res = await async_client.post(
        "/api/queries/generate",
        json={"nl_query": "Show students"},
        headers=headers
    )
    # Must reject with 400 Bad Request, NOT auto-create a demo database!
    assert res.status_code == 400
    detail = res.json()["detail"].lower()
    assert any(phrase in detail for phrase in ["no database", "no target database", "database connection", "database not"])

    # Verify no fake database connection was inserted
    db_count = await db_instance.db.database_connections.count_documents({"created_by": user["_id"]})
    assert db_count == 0


@pytest.mark.asyncio
async def test_query_approval_and_revalidation_resets(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory,
    mock_schema_discovery
):
    user, _, headers = await test_user_factory(role="analyst")
    conn_id, _ = await test_db_connection_factory(user_id=user["_id"])

    # Generate query
    res = await async_client.post(
        "/api/queries/generate",
        json={"nl_query": "Show students", "database_id": conn_id},
        headers=headers
    )
    assert res.status_code == 200
    q_data = res.json()
    q_id = q_data["query_id"]
    assert q_data["statements"][0]["approval_status"] == "pending"

    # Approve statement
    res = await async_client.post(
        f"/api/queries/{q_id}/approve",
        json={"statement_index": 0},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["statements"][0]["approval_status"] == "approved"

    # Edit and revalidate query -> Must reset approval to pending!
    res = await async_client.post(
        f"/api/queries/{q_id}/revalidate",
        json={"edited_sql": "SELECT id, name FROM students WHERE city = 'Delhi';"},
        headers=headers
    )
    assert res.status_code == 200
    reval_data = res.json()
    assert reval_data["statements"][0]["approval_status"] == "pending"

    # Attempt execution of pending query without re-approving -> Must be rejected (403)!
    res = await async_client.post(f"/api/queries/{q_id}/execute", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_ambiguity_clarification_flow(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory,
    mock_schema_discovery,
    monkeypatch
):
    user, _, headers = await test_user_factory(role="analyst")
    conn_id, _ = await test_db_connection_factory(user_id=user["_id"])

    # Mock LLM to return clarification_needed
    from app.services.llm_service import MockLLMProvider
    async def _mock_clarification(self, nl_query, db_type, schema_text):
        return {
            "needs_clarification": True,
            "clarification_question": "Did you mean active students or all enrolled students?",
            "clarification_choices": ["Active students only", "All enrolled students", "Graduated students"],
            "intent": "Clarify student filter status"
        }
    monkeypatch.setattr(MockLLMProvider, "generate_sql", _mock_clarification)

    res = await async_client.post(
        "/api/queries/generate",
        json={"nl_query": "Show students", "database_id": conn_id},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "clarification_needed"
    assert data["clarification_needed"] is True
    assert len(data["clarification_choices"]) == 3


@pytest.mark.asyncio
async def test_independent_approval_of_multiple_statements(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory,
    mock_schema_discovery
):
    user, _, headers = await test_user_factory(role="analyst")
    conn_id, _ = await test_db_connection_factory(user_id=user["_id"])

    # Multi-statement query
    res = await async_client.post(
        "/api/queries/generate",
        json={"nl_query": "Update department and delete inactive students", "database_id": conn_id},
        headers=headers
    )
    assert res.status_code == 200
    q_data = res.json()
    q_id = q_data["query_id"]
    assert len(q_data["statements"]) == 2
    assert q_data["statements"][0]["approval_status"] == "pending"
    assert q_data["statements"][1]["approval_status"] == "pending"

    # Approve statement 0 only
    res = await async_client.post(
        f"/api/queries/{q_id}/approve",
        json={"statement_index": 0},
        headers=headers
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["statements"][0]["approval_status"] == "approved"
    assert res_data["statements"][1]["approval_status"] == "pending"

    # Attempt execution of statement 1 without its approval -> must fail with 403
    res = await async_client.post(
        f"/api/queries/{q_id}/execute",
        json={"statement_indices": [1]},
        headers=headers
    )
    assert res.status_code == 403
    assert "without explicit user approval" in res.json()["detail"]


@pytest.mark.asyncio
async def test_role_revocation_before_execution(
    async_client: AsyncClient,
    test_user_factory,
    test_db_connection_factory,
    mock_schema_discovery
):
    from bson import ObjectId
    user, _, headers = await test_user_factory(role="analyst")
    conn_id, _ = await test_db_connection_factory(user_id=user["_id"])

    # Generate write query as analyst
    res = await async_client.post(
        "/api/queries/generate",
        json={"nl_query": "Change Rahul department to Computer Science", "database_id": conn_id},
        headers=headers
    )
    assert res.status_code == 200
    q_id = res.json()["query_id"]

    # Approve statement as analyst
    res = await async_client.post(
        f"/api/queries/{q_id}/approve",
        json={"statement_index": 0},
        headers=headers
    )
    assert res.status_code == 200

    # Demote user role to viewer in MongoDB right before execution
    await db_instance.db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {"role": "viewer"}}
    )

    # Attempt execution -> pre-execution revalidation must detect viewer role and block write (403)
    res = await async_client.post(
        f"/api/queries/{q_id}/execute",
        headers=headers
    )
    assert res.status_code == 403
    assert "Viewer role" in res.json()["detail"]
