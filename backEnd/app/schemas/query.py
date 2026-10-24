from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SQLStatementInfo(BaseModel):
    statement_index: int = 0
    sql: str
    operation: str  # SELECT, INSERT, UPDATE, DELETE
    validation_status: str  # valid, invalid, warning, blocked
    validation_message: Optional[str] = None
    approval_status: str = "pending"  # pending, approved, rejected
    warning_broad_impact: bool = False
    affected_table: Optional[str] = None
    tables: List[str] = Field(default_factory=list)
    # Structured MongoDB MQL object (set when db_type is mongodb)
    mql: Optional[Dict[str, Any]] = None
    # Impact preview: estimated rows affected by DELETE/UPDATE before execution
    estimated_rows_affected: Optional[int] = None


class QueryGenerateRequest(BaseModel):
    nl_query: str = Field(..., min_length=1)
    database_id: Optional[str] = None
    session_id: Optional[str] = None
    input_type: str = "text"  # text or voice
    language: str = "English"  # English or Hinglish


class QueryRevalidateRequest(BaseModel):
    edited_sql: str = Field(..., min_length=1)


class StatementApproveRequest(BaseModel):
    statement_index: int = 0


class QueryExecuteRequest(BaseModel):
    statement_indices: Optional[List[int]] = None


class QueryResultResponse(BaseModel):
    query_id: str
    status: str
    nl_query: str
    statements: List[SQLStatementInfo]
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0
    summary: Optional[str] = None
    truncated: bool = False
    max_allowed_rows: int = 1000
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    clarification_choices: Optional[List[str]] = None
