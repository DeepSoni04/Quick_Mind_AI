import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_registration_and_login(async_client: AsyncClient):
    # Health check
    res = await async_client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    # Registration
    reg_payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "password123"
    }
    res = await async_client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testuser@example.com"
    assert data["user"]["role"] == "viewer"  # Default role for new users!

    # Login
    login_payload = {
        "email": "testuser@example.com",
        "password": "password123"
    }
    res = await async_client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200
    data = res.json()
    token = data["access_token"]

    # Get Me
    res = await async_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "testuser@example.com"
