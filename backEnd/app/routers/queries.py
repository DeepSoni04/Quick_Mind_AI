from fastapi import APIRouter, Depends, Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.routers.auth import get_current_user_dep
from app.schemas.auth import UserResponse
from app.schemas.query import (
    QueryExecuteRequest,
    QueryGenerateRequest,
    QueryRevalidateRequest,
    QueryResultResponse,
    StatementApproveRequest,
)
from app.services.execution_service import ExecutionService
from app.services.export_service import ExportService
from app.services.query_service import QueryService

router = APIRouter(prefix="/api/queries", tags=["Queries"])


@router.post("", response_model=QueryResultResponse)
@router.post("/generate", response_model=QueryResultResponse)
async def generate_query(
    req: QueryGenerateRequest,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = QueryService(db)
    return await service.generate_query(current_user.id, current_user.role, req)


@router.post("/{query_id}/validate", response_model=QueryResultResponse)
@router.post("/{query_id}/revalidate", response_model=QueryResultResponse)
async def revalidate_query(
    query_id: str,
    req: QueryRevalidateRequest,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = QueryService(db)
    return await service.revalidate_edited_sql(query_id, req.edited_sql, current_user.id, current_user.role)


@router.post("/{query_id}/approve", response_model=QueryResultResponse)
async def approve_query(
    query_id: str,
    req: StatementApproveRequest = StatementApproveRequest(statement_index=0),
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = QueryService(db)
    return await service.approve_statement(query_id, req.statement_index, current_user.id)


@router.post("/{query_id}/reject", response_model=QueryResultResponse)
async def reject_query(
    query_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    service = QueryService(db)
    return await service.reject_query(query_id, current_user.id)


@router.post("/{query_id}/execute", response_model=QueryResultResponse)
async def execute_query(
    query_id: str,
    req: QueryExecuteRequest = QueryExecuteRequest(),
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    exec_service = ExecutionService(db)
    return await exec_service.execute_query(query_id, current_user.id, req.statement_indices)


@router.get("/{query_id}/export")
@router.get("/{query_id}/export-csv")
async def export_csv(
    query_id: str,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    export_service = ExportService(db)
    csv_content = await export_service.export_query_result_csv(query_id, current_user.id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="querymind-result-{query_id}.csv"'}
    )
