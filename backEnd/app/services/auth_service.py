import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, UserResponse, TokenResponse, ProfileUpdateRequest
from app.utils.helpers import make_avatar, utc_now

logger = logging.getLogger("querymind.auth")


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def register(self, req: RegisterRequest) -> TokenResponse:
        """Register a new user. Role defaults to 'viewer' unless email matches ADMIN_EMAIL."""
        existing = await self.db.users.find_one({"email": req.email.lower()})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with that email already exists."
            )

        # Determine initial role
        role = "viewer"
        if req.email.lower() == settings.ADMIN_EMAIL.lower():
            role = "admin"

        now = utc_now()
        user_doc = {
            "name": req.name.strip(),
            "email": req.email.lower().strip(),
            "password_hash": hash_password(req.password),
            "role": role,
            "status": "active",
            "created_at": now,
            "updated_at": now
        }

        res = await self.db.users.insert_one(user_doc)
        user_id = str(res.inserted_id)

        user_resp = UserResponse(
            id=user_id,
            name=user_doc["name"],
            email=user_doc["email"],
            role=role,
            avatar=make_avatar(user_doc["name"]),
            status="active"
        )

        token = create_access_token({"sub": user_id, "role": role})
        return TokenResponse(access_token=token, user=user_resp)

    async def login(self, req: LoginRequest) -> TokenResponse:
        """Authenticate user by email and password."""
        user = await self.db.users.find_one({"email": req.email.lower()})

        # Bootstrap Admin if admin email tries to log in for the first time
        if not user and req.email.lower() == settings.ADMIN_EMAIL.lower() and req.password == settings.ADMIN_PASSWORD:
            now = utc_now()
            admin_doc = {
                "name": "System Administrator",
                "email": settings.ADMIN_EMAIL.lower(),
                "password_hash": hash_password(settings.ADMIN_PASSWORD),
                "role": "admin",
                "status": "active",
                "created_at": now,
                "updated_at": now
            }
            res = await self.db.users.insert_one(admin_doc)
            user = admin_doc
            user["_id"] = res.inserted_id

        # Guard: user must exist before accessing attributes
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your email and password."
            )

        pwd_hash = user.get("password_hash") or user.get("hashed_password") or ""
        if not verify_password(req.password, pwd_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your email and password."
            )

        # Sync Admin role if configured
        role = user.get("role", "viewer")
        if user["email"].lower() == settings.ADMIN_EMAIL.lower() and role != "admin":
            role = "admin"
            await self.db.users.update_one({"_id": user["_id"]}, {"$set": {"role": "admin"}})

        user_id = str(user["_id"])
        user_resp = UserResponse(
            id=user_id,
            name=user["name"],
            email=user["email"],
            role=role,
            avatar=make_avatar(user["name"]),
            status=user.get("status", "active")
        )

        token = create_access_token({"sub": user_id, "role": role})
        return TokenResponse(access_token=token, user=user_resp)

    async def get_current_user(self, user_id: str) -> UserResponse:
        """Retrieve current user profile."""
        try:
            obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid auth token.")

        user = await self.db.users.find_one({"_id": obj_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found.")

        return UserResponse(
            id=str(user["_id"]),
            name=user["name"],
            email=user["email"],
            role=user.get("role", "viewer"),
            avatar=make_avatar(user["name"]),
            status=user.get("status", "active")
        )

    async def update_profile(self, user_id: str, req: ProfileUpdateRequest) -> UserResponse:
        """Update the current user's own profile (name only). Role and email are immutable."""
        try:
            obj_id = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user ID.")

        user = await self.db.users.find_one({"_id": obj_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        new_name = req.name.strip()
        if not new_name:
            raise HTTPException(status_code=422, detail="Name must not be empty.")

        now = utc_now()
        await self.db.users.update_one(
            {"_id": obj_id},
            {"$set": {"name": new_name, "updated_at": now}}
        )

        return UserResponse(
            id=str(user["_id"]),
            name=new_name,
            email=user["email"],
            role=user.get("role", "viewer"),
            avatar=make_avatar(new_name),
            status=user.get("status", "active")
        )
