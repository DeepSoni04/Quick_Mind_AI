from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import re


SUPPORTED_DB_TYPES = {"mongodb", "mysql", "postgresql"}


def _validate_db_type(v: Optional[str]) -> str:
    if v is None:
        return "mysql"
    normalized = v.lower().strip()
    if normalized not in SUPPORTED_DB_TYPES:
        raise ValueError(f"Unsupported database type '{v}'. Must be one of: {', '.join(sorted(SUPPORTED_DB_TYPES))}.")
    return normalized


class DatabaseConnectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    db_type: str = Field(default="mysql")
    # MySQL / PostgreSQL fields
    host: Optional[str] = None
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    database_name: Optional[str] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    # MongoDB fields
    connection_string: Optional[str] = None
    connectionString: Optional[str] = None

    @field_validator("db_type", mode="before")
    @classmethod
    def validate_db_type(cls, v):
        return _validate_db_type(v)


class DatabaseConnectionTestRequest(BaseModel):
    db_type: str = Field(default="mysql")
    # MySQL / PostgreSQL fields
    host: Optional[str] = None
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    database_name: Optional[str] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    # MongoDB fields
    connection_string: Optional[str] = None
    connectionString: Optional[str] = None

    @field_validator("db_type", mode="before")
    @classmethod
    def validate_db_type(cls, v):
        return _validate_db_type(v)


class DatabaseConnectionResponse(BaseModel):
    id: str
    name: str
    db_type: str
    type: Optional[str] = None
    # SQL fields (None for MongoDB connections)
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    database: Optional[str] = None
    status: str = "Connected"
    collections_count: int = 0
    collectionsCount: Optional[int] = 0
    queries_count: int = 0
    queriesCount: Optional[int] = 0
    last_synced: str = "Just now"
    lastSynced: Optional[str] = "Just now"
    created_at: str
    updated_at: str


class ColumnSchema(BaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None


class TableSchema(BaseModel):
    name: str
    columns: List[ColumnSchema]
    row_count_est: Optional[int] = None


class DatabaseSchemaResponse(BaseModel):
    database_id: str
    database_name: str
    db_type: str
    tables: List[TableSchema]
