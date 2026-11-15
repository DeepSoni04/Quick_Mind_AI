from typing import List, Optional
from pydantic import BaseModel, Field


class ColumnPermissionConfig(BaseModel):
    column_name: str
    allowed: bool = True
    allowed_operations: List[str] = Field(default_factory=lambda: ["SELECT", "INSERT", "UPDATE", "DELETE"])


class TablePermissionConfig(BaseModel):
    table_name: str
    allowed: bool = True
    allowed_operations: List[str] = Field(default_factory=lambda: ["SELECT", "INSERT", "UPDATE", "DELETE"])
    columns: Optional[List[ColumnPermissionConfig]] = None


class SchemaPermissionsUpdateRequest(BaseModel):
    database_id: str
    tables: List[TablePermissionConfig]


class SchemaPermissionsResponse(BaseModel):
    database_id: str
    tables: List[TablePermissionConfig]


class NaturalLanguageRuleRequest(BaseModel):
    rule_text: str


class NaturalLanguageRuleResponse(BaseModel):
    id: str
    database_id: str
    rule_text: str
    table_name: Optional[str] = None
    column_name: Optional[str] = None
    action: str = "restrict_column"
    target_role: str = "viewer"
    allowed: bool = False
    restricted_operations: List[str] = Field(default_factory=lambda: ["SELECT", "INSERT", "UPDATE", "DELETE"])
    summary: str
    created_at: Optional[Any] = None
