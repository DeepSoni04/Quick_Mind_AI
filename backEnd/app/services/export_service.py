import csv
import io
from typing import Any, List, Dict
from fastapi import HTTPException
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class ExportService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def export_query_result_csv(self, query_id: str, user_id: str) -> str:
        """Export executed query results to CSV string."""
        try:
            q_obj_id = ObjectId(query_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid query_id format.")

        query = await self.db.queries.find_one({"_id": q_obj_id, "user_id": user_id})
        if not query:
            raise HTTPException(status_code=404, detail="Query not found.")

        if query.get("execution_status") != "success":
            raise HTTPException(status_code=400, detail="Cannot export CSV for unexecuted or failed query.")

        # Re-fetch data or fetch from query doc
        columns = query.get("result_columns", [])
        rows = query.get("result_rows", [])

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        if columns:
            writer.writerow(columns)
        for r in rows:
            writer.writerow(r)

        return output.getvalue()
