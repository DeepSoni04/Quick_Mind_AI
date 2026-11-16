from typing import Any, Dict, Optional
from pydantic import BaseModel


class ResponseModel(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class HealthResponse(BaseModel):
    status: str = "ok"
