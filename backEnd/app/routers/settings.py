from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings as app_settings
from app.core.database import get_database
from app.routers.auth import get_current_user_dep
from app.schemas.auth import UserResponse
from app.utils.helpers import utc_now

router = APIRouter(prefix="/api/settings", tags=["Settings"])

# Defaults
DEFAULT_ROW_LIMIT = 1000
DEFAULT_QUERY_TIMEOUT = 30
MAX_ROW_LIMIT = 5000
MIN_ROW_LIMIT = 1
MAX_TIMEOUT = 120
MIN_TIMEOUT = 1


class SettingsUpdate(BaseModel):
    theme: str | None = None
    default_language: str | None = None
    row_limit: int | None = Field(None, ge=MIN_ROW_LIMIT, le=MAX_ROW_LIMIT)
    query_timeout: int | None = Field(None, ge=MIN_TIMEOUT, le=MAX_TIMEOUT)
    auto_execute: bool | None = None
    notifications_enabled: bool | None = None
    # Legacy camelCase aliases
    rowLimit: int | None = Field(None, ge=MIN_ROW_LIMIT, le=MAX_ROW_LIMIT)
    queryTimeout: int | None = Field(None, ge=MIN_TIMEOUT, le=MAX_TIMEOUT)
    confirmUpdates: bool | None = None
    confirmDeletes: bool | None = None


def _format_settings(doc: dict) -> Dict[str, Any]:
    """Return settings dict with snake_case keys expected by frontend and tests."""
    return {
        "row_limit": doc.get("row_limit", DEFAULT_ROW_LIMIT),
        "query_timeout": doc.get("query_timeout", DEFAULT_QUERY_TIMEOUT),
        "theme": doc.get("theme", "light"),
        "default_language": doc.get("default_language", "English"),
        "auto_execute": doc.get("auto_execute", True),
        "notifications_enabled": doc.get("notifications_enabled", True),
        "confirmUpdates": doc.get("confirmUpdates", True),
        "confirmDeletes": doc.get("confirmDeletes", True),
    }


@router.get("", response_model=Dict[str, Any])
async def get_settings(
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Retrieve user-specific settings persisted in MongoDB."""
    user_settings = await db.user_settings.find_one({"user_id": current_user.id})
    if not user_settings:
        default_settings = {
            "user_id": current_user.id,
            "row_limit": DEFAULT_ROW_LIMIT,
            "query_timeout": DEFAULT_QUERY_TIMEOUT,
            "theme": "light",
            "default_language": "English",
            "auto_execute": True,
            "notifications_enabled": True,
            "confirmUpdates": True,
            "confirmDeletes": True,
            "created_at": utc_now(),
            "updated_at": utc_now()
        }
        await db.user_settings.insert_one(default_settings)
        return _format_settings(default_settings)

    return _format_settings(user_settings)


@router.put("", response_model=Dict[str, Any])
async def update_settings(
    data: SettingsUpdate,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update and persist user settings in MongoDB with strict bounds validation (422 on violation)."""
    to_update: Dict[str, Any] = {}

    # Handle both snake_case and camelCase inputs
    row_limit = data.row_limit if data.row_limit is not None else data.rowLimit
    query_timeout = data.query_timeout if data.query_timeout is not None else data.queryTimeout

    if row_limit is not None:
        to_update["row_limit"] = row_limit
    if query_timeout is not None:
        to_update["query_timeout"] = query_timeout
    if data.theme is not None:
        to_update["theme"] = data.theme
    if data.default_language is not None:
        to_update["default_language"] = data.default_language
    if data.auto_execute is not None:
        to_update["auto_execute"] = data.auto_execute
    if data.notifications_enabled is not None:
        to_update["notifications_enabled"] = data.notifications_enabled
    if data.confirmUpdates is not None:
        to_update["confirmUpdates"] = data.confirmUpdates
    if data.confirmDeletes is not None:
        to_update["confirmDeletes"] = data.confirmDeletes

    to_update["updated_at"] = utc_now()

    await db.user_settings.update_one(
        {"user_id": current_user.id},
        {"$set": to_update, "$setOnInsert": {"created_at": utc_now()}},
        upsert=True
    )

    updated_doc = await db.user_settings.find_one({"user_id": current_user.id})
    return _format_settings(updated_doc)
