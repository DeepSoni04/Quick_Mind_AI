import pytest
from httpx import AsyncClient
from app.core.database import db_instance


@pytest.mark.asyncio
async def test_auth_registration_duplicate_email(async_client: AsyncClient, test_user_factory):
    await test_user_factory(email="existing@example.com")
    
    res = await async_client.post(
        "/api/auth/register",
        json={"name": "Duplicate", "email": "existing@example.com", "password": "password123"}
    )
    assert res.status_code == 400
    assert any(phrase in res.json()["detail"].lower() for phrase in ["already", "registered", "exists"])


@pytest.mark.asyncio
async def test_auth_login_invalid_credentials(async_client: AsyncClient, test_user_factory):
    await test_user_factory(email="valid@example.com", password="correct_password")

    # Invalid password
    res = await async_client.post(
        "/api/auth/login",
        json={"email": "valid@example.com", "password": "wrong_password"}
    )
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()

    # Non-existent user
    res = await async_client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid_token(async_client: AsyncClient):
    res = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.payload"}
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_rbac_and_temporary_password_reset(
    async_client: AsyncClient,
    test_user_factory
):
    # Create Admin
    admin_doc, admin_token, admin_headers = await test_user_factory(
        email="admin@example.com",
        name="Admin",
        role="admin"
    )
    # Create regular user
    user_doc, user_token, user_headers = await test_user_factory(
        email="regular@example.com",
        name="Regular",
        role="viewer"
    )

    # 1. Regular viewer cannot access admin endpoints (403)
    res = await async_client.get("/api/admin/users", headers=user_headers)
    assert res.status_code == 403

    # 2. Admin can list users
    res = await async_client.get("/api/admin/users", headers=admin_headers)
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 2

    # 3. Admin updates user role to analyst
    user_id = user_doc["_id"]
    res = await async_client.put(
        f"/api/admin/users/{user_id}/role",
        json={"role": "analyst"},
        headers=admin_headers
    )
    assert res.status_code == 200
    assert res.json()["role"] == "analyst"

    # 4. Admin resets password -> MUST NOT be "reset123"! Must be secure random temporary password.
    res = await async_client.post(
        f"/api/admin/users/{user_id}/reset-password",
        headers=admin_headers
    )
    assert res.status_code == 200
    data = res.json()
    temp_pass = data.get("temporary_password")
    assert temp_pass is not None
    assert temp_pass != "reset123"
    assert len(temp_pass) >= 12
    # Verify the user can login with the new temporary password
    res = await async_client.post(
        "/api/auth/login",
        json={"email": "regular@example.com", "password": temp_pass}
    )
    assert res.status_code == 200

    # 5. Admin deletes user with cascade
    res = await async_client.delete(f"/api/admin/users/{user_id}", headers=admin_headers)
    assert res.status_code == 200

    # Verify user is gone
    check_user = await db_instance.db.users.find_one({"_id": user_doc["_id"]})
    assert check_user is None
