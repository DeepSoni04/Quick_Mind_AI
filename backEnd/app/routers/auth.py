from fastapi import APIRouter, Depends, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.security import decode_access_token
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse, ProfileUpdateRequest
from app.schemas.common import ResponseModel
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


async def get_current_user_dep(
    authorization: str = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> UserResponse:
    """Dependency to extract and verify current authenticated user from JWT header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header."
        )
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )
    user_id = payload["sub"]
    auth_service = AuthService(db)
    return await auth_service.get_current_user(user_id)


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    auth_service = AuthService(db)
    return await auth_service.register(req)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    auth_service = AuthService(db)
    return await auth_service.login(req)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user_dep)):
    """Return the authenticated user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    req: ProfileUpdateRequest,
    current_user: UserResponse = Depends(get_current_user_dep),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update the authenticated user's own profile (name only)."""
    auth_service = AuthService(db)
    return await auth_service.update_profile(current_user.id, req)


@router.post("/logout", response_model=ResponseModel)
async def logout(current_user: UserResponse = Depends(get_current_user_dep)):
    """Logout endpoint — client should discard its JWT token."""
    return ResponseModel(success=True, message="Successfully logged out")
