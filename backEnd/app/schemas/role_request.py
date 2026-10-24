from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RoleRequestCreate(BaseModel):
    """User submits a request to be elevated to a higher role."""
    requested_role: str = Field(..., description="Target role: analyst or admin")
    reason: Optional[str] = Field(None, max_length=500)


class RoleRequestResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: str
    requested_role: str
    status: str  # pending, approved, rejected
    reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str
