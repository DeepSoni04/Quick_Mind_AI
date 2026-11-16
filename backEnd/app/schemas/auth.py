from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserStats(BaseModel):
    queries_run: int = 0
    saved_queries: int = 0
    connected_clusters: int = 0
    success_rate: str = "99.4%"


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str  # admin, analyst, viewer
    avatar: str
    status: str = "active"
    title: Optional[str] = "Lead Data Architect & AI Admin"
    department: Optional[str] = "Data Platform & AI Infrastructure"
    bio: Optional[str] = "QueryMind database engineer exploring automated NL query models."
    phone: Optional[str] = "+91 98765 43210"
    location: Optional[str] = "Ahmedabad, India"
    created_at: Optional[datetime] = None
    joined_date: Optional[str] = "January 2026"
    api_token: Optional[str] = None
    two_factor_enabled: Optional[bool] = False
    stats: Optional[UserStats] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdateRequest(BaseModel):
    """Request body for PUT /api/auth/me."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    title: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    avatar: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)
