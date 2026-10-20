import logging
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.helpers import format_relative_time, utc_now

logger = logging.getLogger("querymind.history_service")


class HistoryService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch user's query execution history in frontend-compatible structure."""
        cursor = self.db.queries.find({"user_id": user_id}).sort("created_at", -1).limit(50)
        history_list = []
        
        async for q in cursor:
            statements = q.get("statements", [])
            op_type = "select"
            if statements:
                op_type = statements[0].get("operation", "select").lower()
            
            val_status = q.get("validation_status", "valid")
            exec_status = q.get("execution_status", "none")
            
            status_str = "success" if exec_status == "success" else "blocked" if val_status == "blocked" else "pending"
            count_str = f"{q.get('row_count', 0)} rows" if op_type == "select" and exec_status == "success" else "Blocked" if status_str == "blocked" else "1 updated"
            
            exec_time = f"{q.get('execution_time_ms', 0)}ms" if exec_status == "success" else "—"

            history_list.append({
                "id": str(q["_id"]),
                "query": q.get("nl_query", ""),
                "type": op_type,
                "status": status_str,
                "time": format_relative_time(q.get("created_at")),
                "count": count_str,
                "collection": "database",
                "user": "You",
                "executionTime": exec_time
            })

        return history_list

    async def get_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """Generate workspace statistics for DashboardPage."""
        history = await self.get_history(user_id)
        
        total = len(history)
        success = len([h for h in history if h["status"] == "success"])
        blocked = len([h for h in history if h["status"] == "blocked"])
        
        rate = round((success / total) * 100) if total > 0 else 0
        
        times = []
        for h in history:
            t = h.get("executionTime", "—")
            if t != "—" and t.endswith("ms"):
                try:
                    times.append(int(t.replace("ms", "")))
                except ValueError:
                    pass
        avg_time = round(sum(times) / len(times)) if times else 34

        return {
            "total": total,
            "successRate": rate,
            "blocked": blocked,
            "avgResponseTime": f"{avg_time}ms",
            "recent": history[:5]
        }

    async def get_security_logs(self) -> List[Dict[str, Any]]:
        """Retrieve system security audit logs for Admin Panel."""
        cursor = self.db.query_logs.find().sort("created_at", -1).limit(20)
        logs = []
        async for l in cursor:
            user = await self.db.users.find_one({"_id": ObjectId(l["user_id"])}) if "user_id" in l else None
            user_name = user["name"] if user else "Unknown"
            
            event_type = l.get("event_type", "security_event")
            severity = "medium"
            if "blocked" in event_type or "failed" in event_type or l.get("status") == "blocked":
                severity = "high"
            elif "injection" in event_type or "prohibited" in event_type:
                severity = "critical"
            elif "success" in event_type or "login" in event_type:
                severity = "low"

            logs.append({
                "id": str(l["_id"]),
                "time": l.get("created_at", utc_now()).strftime("%H:%M"),
                "event": f"Event: {event_type} (Status: {l.get('status', 'info')})",
                "user": user_name,
                "severity": severity
            })
        return logs
