import logging
from typing import Any, Dict, List, Optional
from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.session import SessionCreateRequest, SessionResponse
from app.utils.helpers import utc_now

logger = logging.getLogger("querymind.session_service")


class SessionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create_session(self, user_id: str, req: SessionCreateRequest) -> SessionResponse:
        """Create a new conversational session."""
        # Support both 'name' and legacy 'title' field
        name = req.name or req.title or "Database Session"

        if req.database_id:
            try:
                db_id_obj = ObjectId(req.database_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid database_id format.")
            conn = await self.db.database_connections.find_one({"_id": db_id_obj, "created_by": user_id})
            if not conn:
                raise HTTPException(status_code=404, detail="Database connection not found.")

        now = utc_now()
        doc = {
            "user_id": user_id,
            "database_id": req.database_id,
            "name": name,
            "status": "active",
            "created_at": now,
            "updated_at": now
        }
        res = await self.db.query_sessions.insert_one(doc)
        return SessionResponse(
            id=str(res.inserted_id),
            user_id=user_id,
            database_id=req.database_id,
            name=name,
            status="active",
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            query_count=0
        )

    def _doc_to_response(self, s: Dict[str, Any], user_id: str, count: int = 0) -> SessionResponse:
        return SessionResponse(
            id=str(s["_id"]),
            user_id=user_id,
            database_id=s.get("database_id"),
            name=s.get("name") or s.get("title") or "Database Session",
            status=s.get("status", "active"),
            created_at=s.get("created_at", utc_now()).isoformat(),
            updated_at=s.get("updated_at", utc_now()).isoformat(),
            query_count=count
        )

    async def list_sessions(self, user_id: str) -> List[SessionResponse]:
        """List active sessions for user."""
        cursor = self.db.query_sessions.find({"user_id": user_id}).sort("created_at", -1)
        sessions = []
        async for s in cursor:
            s_id = str(s["_id"])
            count = await self.db.queries.count_documents({"session_id": s_id})
            sessions.append(self._doc_to_response(s, user_id, count))
        return sessions

    async def get_session(self, session_id: str, user_id: str) -> SessionResponse:
        """Get a single session owned by user."""
        try:
            obj_id = ObjectId(session_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid session ID.")

        s = await self.db.query_sessions.find_one({"_id": obj_id, "user_id": user_id})
        if not s:
            raise HTTPException(status_code=404, detail="Session not found.")

        count = await self.db.queries.count_documents({"session_id": session_id})
        return self._doc_to_response(s, user_id, count)

    async def update_session(self, session_id: str, user_id: str, name: str) -> SessionResponse:
        """Rename a session."""
        try:
            obj_id = ObjectId(session_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid session ID.")

        res = await self.db.query_sessions.update_one(
            {"_id": obj_id, "user_id": user_id},
            {"$set": {"name": name, "updated_at": utc_now()}}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found.")

        return await self.get_session(session_id, user_id)

    async def delete_session(self, session_id: str, user_id: str):
        """Delete a session owned by user."""
        try:
            obj_id = ObjectId(session_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid session ID.")

        res = await self.db.query_sessions.delete_one({"_id": obj_id, "user_id": user_id})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Session not found.")

    async def close_session(self, session_id: str, user_id: str):
        """Close conversational session."""
        try:
            obj_id = ObjectId(session_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid session ID.")

        res = await self.db.query_sessions.update_one(
            {"_id": obj_id, "user_id": user_id},
            {"$set": {"status": "closed", "updated_at": utc_now()}}
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Session not found.")
