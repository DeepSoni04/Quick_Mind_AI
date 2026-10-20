from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str  # admin, analyst, viewer
    avatar: str
    status: str = "active"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdateRequest(BaseModel):
    """Request body for PUT /api/auth/me — only name is editable.
    Email changes are deliberately not supported to preserve JWT-based auth integrity.
    """
    name: str = Field(..., min_length=1, max_length=200)
