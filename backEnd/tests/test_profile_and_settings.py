"""
Tests for Feature 2: Authenticated user profile and settings persistence.

Covers:
- GET /api/auth/me returns real name + email
- PUT /api/auth/me updates name, persists to MongoDB
- Role immutability (cannot be changed via PUT /me)
- Empty name rejected (422)
- GET /api/settings returns defaults then persisted values
- PUT /api/settings persists bounds-checked settings
- Row-limit / query-timeout out-of-range rejected
- Settings scoped per user
"""
import pytest


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_me_returns_real_name(async_client, test_user_factory):
    """GET /api/auth/me returns the authenticated user's actual name."""
    _, _, headers = await test_user_factory(
        email="alice@example.com", name="Alice Wonder"
    )
    resp = await async_client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Alice Wonder"
    assert data["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(async_client):
    resp = await async_client.get("/api/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/auth/me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_name_persists(async_client, test_user_factory):
    """Name change should be persisted and visible on next GET /api/auth/me."""
    _, _, headers = await test_user_factory(
        email="bob@example.com", name="Bob Smith"
    )

    resp = await async_client.put(
        "/api/auth/me", json={"name": "Robert Smith"}, headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Robert Smith"

    # Verify persistence via a second GET
    resp2 = await async_client.get("/api/auth/me", headers=headers)
    assert resp2.json()["name"] == "Robert Smith"


@pytest.mark.asyncio
async def test_update_name_strips_whitespace(async_client, test_user_factory):
    """Leading/trailing whitespace in the name should be stripped."""
    _, _, headers = await test_user_factory(email="trim@example.com", name="Testy")
    resp = await async_client.put(
        "/api/auth/me", json={"name": "   Trimmed Name   "}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Trimmed Name"


@pytest.mark.asyncio
async def test_update_name_empty_rejected(async_client, test_user_factory):
    """Empty name string should be rejected with 422."""
    _, _, headers = await test_user_factory(email="noname@example.com")
    resp = await async_client.put(
        "/api/auth/me", json={"name": ""}, headers=headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_name_whitespace_only_rejected(async_client, test_user_factory):
    """Whitespace-only name should be rejected."""
    _, _, headers = await test_user_factory(email="ws@example.com")
    resp = await async_client.put(
        "/api/auth/me", json={"name": "   "}, headers=headers
    )
    assert resp.status_code in (422, 400)


@pytest.mark.asyncio
async def test_update_email_field_ignored(async_client, test_user_factory):
    """Extra email field in PUT body should NOT change the stored email."""
    _, _, headers = await test_user_factory(
        email="noemail@example.com", name="Noemail Test"
    )
    resp = await async_client.put(
        "/api/auth/me",
        json={"name": "New Name", "email": "hacker@evil.com"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "noemail@example.com"


@pytest.mark.asyncio
async def test_update_role_field_ignored(async_client, test_user_factory):
    """Extra role field in PUT body should NOT elevate user privileges."""
    _, _, headers = await test_user_factory(
        email="role@example.com", name="Normal User", role="viewer"
    )
    resp = await async_client.put(
        "/api/auth/me",
        json={"name": "Normal User", "role": "admin"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "viewer"


@pytest.mark.asyncio
async def test_put_me_unauthenticated(async_client):
    resp = await async_client.put("/api/auth/me", json={"name": "x"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_users_cannot_modify_each_other(async_client, test_user_factory):
    """PUT /api/auth/me is strictly scoped to the caller — no user_id override."""
    _, _, headers_a = await test_user_factory(email="a2@example.com", name="Alice")
    _, _, headers_b = await test_user_factory(email="b2@example.com", name="Bob")

    # B updates their own name
    resp = await async_client.put(
        "/api/auth/me", json={"name": "Hacker"}, headers=headers_b
    )
    assert resp.status_code == 200

    # A's name must be unchanged
    resp_a = await async_client.get("/api/auth/me", headers=headers_a)
    assert resp_a.json()["name"] == "Alice"


# ---------------------------------------------------------------------------
# GET /api/settings
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_settings_default_values(async_client, test_user_factory):
    """First GET returns sensible defaults (row_limit=1000, query_timeout=30)."""
    _, _, headers = await test_user_factory(email="s1@test.com")
    resp = await async_client.get("/api/settings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["row_limit"] == 1000
    assert data["query_timeout"] == 30


@pytest.mark.asyncio
async def test_settings_unauthenticated(async_client):
    resp = await async_client.get("/api/settings")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/settings
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_settings_persist_row_limit(async_client, test_user_factory):
    """Updated row_limit should be readable on a subsequent GET."""
    _, _, headers = await test_user_factory(email="s2@test.com")

    await async_client.put("/api/settings", json={"row_limit": 250}, headers=headers)

    resp = await async_client.get("/api/settings", headers=headers)
    assert resp.json()["row_limit"] == 250


@pytest.mark.asyncio
async def test_settings_persist_query_timeout(async_client, test_user_factory):
    _, _, headers = await test_user_factory(email="s3@test.com")
    await async_client.put(
        "/api/settings", json={"query_timeout": 60}, headers=headers
    )
    resp = await async_client.get("/api/settings", headers=headers)
    assert resp.json()["query_timeout"] == 60


@pytest.mark.asyncio
async def test_settings_persist_toggles(async_client, test_user_factory):
    """Boolean toggles (confirmUpdates, confirmDeletes) should persist."""
    _, _, headers = await test_user_factory(email="s4@test.com")
    await async_client.put(
        "/api/settings",
        json={"confirmUpdates": False, "confirmDeletes": False},
        headers=headers,
    )
    resp = await async_client.get("/api/settings", headers=headers)
    data = resp.json()
    assert data["confirmUpdates"] is False
    assert data["confirmDeletes"] is False


@pytest.mark.asyncio
async def test_row_limit_too_high_rejected(async_client, test_user_factory):
    """row_limit > 5000 should be rejected with 422."""
    _, _, headers = await test_user_factory(email="s5@test.com")
    resp = await async_client.put(
        "/api/settings", json={"row_limit": 99999}, headers=headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_row_limit_too_low_rejected(async_client, test_user_factory):
    """row_limit < 1 should be rejected."""
    _, _, headers = await test_user_factory(email="s6@test.com")
    resp = await async_client.put(
        "/api/settings", json={"row_limit": 0}, headers=headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_query_timeout_too_high_rejected(async_client, test_user_factory):
    """query_timeout > 120 should be rejected."""
    _, _, headers = await test_user_factory(email="s7@test.com")
    resp = await async_client.put(
        "/api/settings", json={"query_timeout": 999}, headers=headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_settings_isolated_per_user(async_client, test_user_factory):
    """Each user has their own settings; one user's change must not affect another."""
    _, _, headers_x = await test_user_factory(email="sx@test.com")
    _, _, headers_y = await test_user_factory(email="sy@test.com")

    # X sets row_limit=50, Y sets row_limit=500
    await async_client.put("/api/settings", json={"row_limit": 50}, headers=headers_x)
    await async_client.put("/api/settings", json={"row_limit": 500}, headers=headers_y)

    resp_x = await async_client.get("/api/settings", headers=headers_x)
    resp_y = await async_client.get("/api/settings", headers=headers_y)

    assert resp_x.json()["row_limit"] == 50
    assert resp_y.json()["row_limit"] == 500


@pytest.mark.asyncio
async def test_put_settings_unauthenticated(async_client):
    resp = await async_client.put("/api/settings", json={"row_limit": 100})
    assert resp.status_code == 401
