from typing import Any, Dict, List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.security import hash_password, generate_temp_password
from app.routers.auth import get_current_user_dep
from app.schemas.auth import UserResponse
from app.schemas.common import ResponseModel
from app.services.history_service import HistoryService
from app.utils.helpers import make_avatar, utc_now

router = APIRouter(prefix="/api/admin", tags=["Admin Panel"])


def check_admin(user: UserResponse):
    """Ensure authenticated user holds the Admin role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required."
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_admin_stats(
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Return high-level stats for the admin dashboard."""
    check_admin(current_user)
    total_users = await db.users.count_documents({})
    total_queries = await db.queries.count_documents({})
    total_databases = await db.database_connections.count_documents({})
    total_sessions = await db.query_sessions.count_documents({})
    return {
        "total_users": total_users,
        "total_queries": total_queries,
        "total_databases": total_databases,
        "total_sessions": total_sessions,
    }


@router.get("/users", response_model=List[Dict[str, Any]])
async def list_all_users(
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """List all registered users with query statistics."""
    check_admin(current_user)
    cursor = db.users.find()
    users = []
    async for u in cursor:
        q_count = await db.queries.count_documents({"user_id": str(u["_id"])})
        users.append({
            "id": str(u["_id"]),
            "name": u.get("name", "User"),
            "email": u.get("email", ""),
            "role": u.get("role", "viewer"),
            "status": u.get("status", "active"),
            "queries": q_count,
            "lastActive": "Recently"
        })
    return users


@router.put("/users/{user_id}/role", response_model=Dict[str, Any])
async def update_user_role(
    user_id: str,
    data: Dict[str, str],
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update assigned role of a user. Returns updated user document."""
    check_admin(current_user)
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    new_role = data.get("role")
    if new_role not in ["admin", "analyst", "viewer"]:
        raise HTTPException(status_code=400, detail="Invalid role specified. Must be admin, analyst, or viewer.")

    res = await db.users.update_one(
        {"_id": obj_id},
        {"$set": {"role": new_role, "updated_at": utc_now()}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")

    updated = await db.users.find_one({"_id": obj_id})
    return {
        "id": str(updated["_id"]),
        "name": updated.get("name", "User"),
        "email": updated.get("email", ""),
        "role": updated.get("role", "viewer"),
        "status": updated.get("status", "active"),
    }


@router.post("/users/{user_id}/reset-password", response_model=Dict[str, Any])
async def admin_reset_password(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate a secure, random temporary password for a user without hardcoded defaults."""
    check_admin(current_user)
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    temp_password = generate_temp_password(14)
    new_hash = hash_password(temp_password)

    await db.users.update_one(
        {"_id": obj_id},
        {"$set": {"password_hash": new_hash, "updated_at": utc_now()}}
    )

    # Log audit event without recording the password in plain text
    await db.query_logs.insert_one({
        "event_type": "admin_password_reset",
        "target_user_id": user_id,
        "admin_user_id": current_user.id,
        "status": "success",
        "created_at": utc_now()
    })

    return {
        "success": True,
        "message": "Password reset successfully.",
        "temporary_password": temp_password
    }


@router.delete("/users/{user_id}", response_model=ResponseModel)
async def delete_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a user and cascade clean their connections and sessions."""
    check_admin(current_user)
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Admin cannot delete their own account.")

    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    res = await db.users.delete_one({"_id": obj_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found.")

    # Cascade delete user data
    await db.database_connections.delete_many({"created_by": user_id})
    await db.query_sessions.delete_many({"user_id": user_id})
    await db.user_settings.delete_many({"user_id": user_id})

    return ResponseModel(success=True, message="User deleted successfully.")


@router.get("/security-logs", response_model=List[Dict[str, Any]])
async def get_security_logs(
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Retrieve security audit logs."""
    check_admin(current_user)
    history_service = HistoryService(db)
    return await history_service.get_security_logs()
