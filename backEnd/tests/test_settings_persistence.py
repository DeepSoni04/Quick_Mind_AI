import pytest
from httpx import AsyncClient
from app.core.database import db_instance


@pytest.mark.asyncio
async def test_settings_persistence_and_bounds_validation(
    async_client: AsyncClient,
    test_user_factory
):
    user, _, headers = await test_user_factory(email="settings_user@example.com")

    # 1. Default settings initially
    res = await async_client.get("/api/settings", headers=headers)
    assert res.status_code == 200
    defaults = res.json()
    assert defaults["row_limit"] == 1000
    assert defaults["query_timeout"] == 30

    # 2. Update settings with valid custom values
    update_payload = {
        "theme": "dark",
        "default_language": "Gujarati",
        "row_limit": 500,
        "query_timeout": 60,
        "auto_execute": False,
        "notifications_enabled": True
    }
    res = await async_client.put("/api/settings", json=update_payload, headers=headers)
    assert res.status_code == 200
    saved = res.json()
    assert saved["row_limit"] == 500
    assert saved["query_timeout"] == 60
    assert saved["theme"] == "dark"

    # 3. Verify settings were persisted directly in MongoDB collection
    doc = await db_instance.db.user_settings.find_one({"user_id": user["_id"]})
    assert doc is not None
    assert doc["row_limit"] == 500
    assert doc["query_timeout"] == 60
    assert doc["default_language"] == "Gujarati"

    # 4. Fetch settings again to verify persistent retrieval
    res = await async_client.get("/api/settings", headers=headers)
    assert res.status_code == 200
    assert res.json()["row_limit"] == 500

    # 5. Bounds validation: Row limit exceeding upper bound (> 5000) -> 422 Unprocessable Entity
    res = await async_client.put("/api/settings", json={"row_limit": 10000}, headers=headers)
    assert res.status_code == 422

    # Bounds validation: Row limit below lower bound (< 1) -> 422
    res = await async_client.put("/api/settings", json={"row_limit": 0}, headers=headers)
    assert res.status_code == 422

    # Bounds validation: Query timeout exceeding upper bound (> 120) -> 422
    res = await async_client.put("/api/settings", json={"query_timeout": 300}, headers=headers)
    assert res.status_code == 422

    # Bounds validation: Query timeout below lower bound (< 1) -> 422
    res = await async_client.put("/api/settings", json={"query_timeout": 0}, headers=headers)
    assert res.status_code == 422
