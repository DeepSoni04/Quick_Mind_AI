from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    name: Optional[str] = "Database Session"
    database_id: Optional[str] = None
    # Legacy alias
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    user_id: str
    database_id: Optional[str] = None
    name: str = "Database Session"
    status: str = "active"
    created_at: str
    updated_at: str
    query_count: int = 0
