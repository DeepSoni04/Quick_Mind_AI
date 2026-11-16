import csv
import io
from typing import Any, Dict, List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.routers.auth import get_current_user_dep
from app.schemas.auth import UserResponse
from app.schemas.common import ResponseModel
from app.services.history_service import HistoryService
from app.utils.helpers import utc_now

router = APIRouter(prefix="/api", tags=["History & Dashboard"])


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_history(
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = HistoryService(db)
    return await service.get_history(current_user.id)


@router.get("/history/{log_id}", response_model=Dict[str, Any])
async def get_history_item(
    log_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get a single query log entry owned by the current user."""
    try:
        obj_id = ObjectId(log_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid history ID.")

    doc = await db.query_logs.find_one({"_id": obj_id, "user_id": current_user.id})
    if not doc:
        raise HTTPException(status_code=404, detail="History entry not found.")

    return {
        "id": str(doc["_id"]),
        "sql": doc.get("sql", ""),
        "status": doc.get("status", ""),
        "row_count": doc.get("row_count", 0),
        "execution_time_ms": doc.get("execution_time_ms", 0),
        "results": doc.get("results", []),
        "created_at": doc.get("created_at", utc_now()).isoformat() if doc.get("created_at") else None,
    }


@router.delete("/history/clear", response_model=ResponseModel)
async def clear_history(
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Clear all query history for the current user."""
    await db.query_logs.delete_many({"user_id": current_user.id})
    await db.queries.delete_many({"user_id": current_user.id})
    return ResponseModel(success=True, message="History cleared.")


@router.delete("/history/{log_id}", response_model=ResponseModel)
async def delete_history_item(
    log_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a single history entry owned by the current user."""
    try:
        obj_id = ObjectId(log_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid history ID.")

    res = await db.query_logs.delete_one({"_id": obj_id, "user_id": current_user.id})
    if res.deleted_count == 0:
        # Also try in queries collection
        try:
            res2 = await db.queries.delete_one({"_id": obj_id, "user_id": current_user.id})
            if res2.deleted_count == 0:
                raise HTTPException(status_code=404, detail="History entry not found.")
        except Exception:
            raise HTTPException(status_code=404, detail="History entry not found.")
    return ResponseModel(success=True, message="History entry deleted.")


@router.get("/dashboard/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = HistoryService(db)
    return await service.get_dashboard_stats(current_user.id)


@router.get("/export/{log_id}/csv")
async def export_query_csv(
    log_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Export a query result as a CSV file. Only the query owner can export."""
    try:
        obj_id = ObjectId(log_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid log ID.")

    doc = await db.query_logs.find_one({"_id": obj_id, "user_id": current_user.id})
    if not doc:
        raise HTTPException(status_code=404, detail="Query log entry not found or access denied.")

    results = doc.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail="No results to export.")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)
    output.seek(0)

    filename = f"query_{log_id}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
