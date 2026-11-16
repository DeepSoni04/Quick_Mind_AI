from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.routers.auth import get_current_user_dep
from app.schemas.auth import UserResponse
from app.schemas.common import ResponseModel
from app.schemas.session import SessionCreateRequest, SessionResponse
from app.services.session_service import SessionService

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = SessionService(db)
    return await service.list_sessions(current_user.id)


@router.post("", response_model=SessionResponse)
async def create_session(
    req: SessionCreateRequest,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = SessionService(db)
    return await service.create_session(current_user.id, req)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = SessionService(db)
    return await service.get_session(session_id, current_user.id)


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    data: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    name = data.get("name") or data.get("title") or "Database Session"
    service = SessionService(db)
    return await service.update_session(session_id, current_user.id, name)


@router.delete("/{session_id}", response_model=ResponseModel)
async def delete_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = SessionService(db)
    await service.delete_session(session_id, current_user.id)
    return ResponseModel(success=True, message="Session deleted.")


@router.post("/{session_id}/close", response_model=ResponseModel)
async def close_session(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = SessionService(db)
    await service.close_session(session_id, current_user.id)
    return ResponseModel(success=True, message="Session closed.")
