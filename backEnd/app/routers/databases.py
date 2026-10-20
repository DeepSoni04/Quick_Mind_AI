from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.routers.auth import get_current_user_dep
from app.schemas.auth import UserResponse
from app.schemas.common import ResponseModel
from app.schemas.database import (
    DatabaseConnectionCreate,
    DatabaseConnectionResponse,
    DatabaseConnectionTestRequest,
    DatabaseSchemaResponse,
)
from app.schemas.schema import SchemaPermissionsResponse, SchemaPermissionsUpdateRequest
from app.services.database_service import DatabaseService
from app.services.schema_service import SchemaService

router = APIRouter(prefix="/api/databases", tags=["Databases"])


@router.get("", response_model=List[DatabaseConnectionResponse])
async def list_databases(
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = DatabaseService(db)
    return await service.list_connections(current_user.id)


@router.post("", response_model=DatabaseConnectionResponse)
async def create_database_connection(
    req: DatabaseConnectionCreate,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = DatabaseService(db)
    return await service.create_connection(current_user.id, req)


@router.get("/{conn_id}", response_model=DatabaseConnectionResponse)
async def get_database_connection(
    conn_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Retrieve a single database connection owned by the current user."""
    service = DatabaseService(db)
    return await service.get_connection(conn_id, current_user.id)


@router.post("/test", response_model=ResponseModel)
async def test_database_connection(
    req: DatabaseConnectionTestRequest,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = DatabaseService(db)
    ok, msg = service.test_target_connection(req.model_dump())
    if not ok:
        return ResponseModel(success=False, message=msg)
    return ResponseModel(success=True, message=msg)


@router.post("/{conn_id}/test", response_model=ResponseModel)
async def test_existing_database_connection(
    conn_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = DatabaseService(db)
    creds = await service.get_connection_credentials(conn_id, current_user.id)
    ok, msg = service.test_target_connection(creds)
    return ResponseModel(success=ok, message=msg)


@router.delete("/{conn_id}", response_model=ResponseModel)
async def delete_database_connection(
    conn_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = DatabaseService(db)
    await service.delete_connection(conn_id, current_user.id)
    return ResponseModel(success=True, message="Database connection removed")


@router.get("/{conn_id}/schema", response_model=DatabaseSchemaResponse)
async def get_database_schema(
    conn_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    schema_service = SchemaService(db)
    return await schema_service.discover_schema(conn_id, current_user.id)


@router.get("/{conn_id}/permissions", response_model=SchemaPermissionsResponse)
async def get_database_permissions(
    conn_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    schema_service = SchemaService(db)
    return await schema_service.get_permissions(conn_id, current_user.id)


@router.post("/{conn_id}/permissions", response_model=ResponseModel)
async def update_database_permissions(
    conn_id: str,
    req: SchemaPermissionsUpdateRequest,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    if current_user.role not in ["analyst", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Analysts and Admins can configure database permissions."
        )
    schema_service = SchemaService(db)
    await schema_service.update_permissions(conn_id, req.tables, current_user.id)
    return ResponseModel(success=True, message="Permissions updated successfully.")
