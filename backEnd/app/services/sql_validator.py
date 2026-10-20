import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import sqlglot
from sqlglot import exp, parse_one

from app.core.config import settings
from app.schemas.query import SQLStatementInfo

logger = logging.getLogger("querymind.sql_validator")

PROHIBITED_TYPES = (
    exp.Drop, exp.Alter, exp.Create, exp.Grant, exp.Revoke,
    exp.Command, exp.Kill
)

PROHIBITED_KEYWORDS = {
    "DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE",
    "EXEC", "EXECUTE", "SHUTDOWN", "KILL"
}


class SQLValidator:
    def __init__(self, max_rows: int = None):
        self.max_rows = max_rows or settings.MAX_QUERY_ROWS

    def split_statements(self, raw_sql: str, dialect: str = "mysql") -> List[str]:
        """Safely split multiple SQL statements using SQLGlot AST parser."""
        if not raw_sql or not raw_sql.strip():
            return []

        glot_dialect = "mysql" if dialect.lower() == "mysql" else "postgres"
        try:
            parsed = sqlglot.parse(raw_sql.strip(), read=glot_dialect)
            statements = []
            for stmt in parsed:
                if stmt:
                    statements.append(stmt.sql(dialect=glot_dialect).strip())
            if not statements:
                statements = [raw_sql.strip()]
            return statements
        except Exception as e:
            logger.debug(f"SQLGlot parse split exception: {e}")
            # Fallback only when statement cannot be parsed into multiple
            parts = [p.strip() for p in raw_sql.split(";") if p.strip()]
            return parts if parts else [raw_sql.strip()]

    def _is_broad_where_clause(self, where_clause: Optional[exp.Where]) -> bool:
        """Check if WHERE clause is missing or is an obvious tautology (e.g. 1=1, TRUE)."""
        if not where_clause:
            return True

        inner = where_clause.this
        # Check literals like WHERE 1, WHERE TRUE
        if isinstance(inner, exp.Literal):
            val = str(inner.this).strip().lower()
            if val in ("1", "true"):
                return True
        elif isinstance(inner, exp.Boolean):
            if inner.this is True:
                return True
        elif isinstance(inner, exp.EQ):
            # Check equality of identical literals e.g. 1 = 1 or 'a' = 'a'
            left = str(inner.left).strip().lower()
            right = str(inner.right).strip().lower()
            if left == right:
                return True

        where_text = where_clause.sql().strip().upper()
        if where_text in ("WHERE 1=1", "WHERE 1 = 1", "WHERE 1", "WHERE TRUE", "WHERE (1=1)", "WHERE (1 = 1)"):
            return True

        return False

    def validate_statement(
        self,
        raw_sql: str,
        dialect: str = "mysql",
        user_role: str = "analyst",
        allowed_permissions: Optional[Dict[str, Any]] = None,
        permissions: Optional[Dict[str, Any]] = None
    ) -> SQLStatementInfo:
        """Complete AST-based security and permission validation of a single SQL statement."""
        if allowed_permissions is None and permissions is not None:
            allowed_permissions = permissions

        glot_dialect = "mysql" if dialect.lower() == "mysql" else "postgres"
        sql_str = raw_sql.strip().rstrip(";")
        
        # Check empty or whitespace
        if not sql_str:
            return SQLStatementInfo(
                statement_index=0,
                sql="",
                operation="UNKNOWN",
                validation_status="invalid",
                validation_message="Empty SQL statement.",
                approval_status="pending",
                warning_broad_impact=False
            )

        # Detect first non-comment keyword
        uncommented = re.sub(r'--[^\n]*', '', sql_str)
        uncommented = re.sub(r'/\*.*?\*/', '', uncommented, flags=re.DOTALL).strip()
        first_word = uncommented.split()[0].upper() if uncommented else ""

        # Step 1: Parse AST
        try:
            ast = parse_one(sql_str, read=glot_dialect)
        except Exception as e:
            return SQLStatementInfo(
                statement_index=0,
                sql=sql_str,
                operation=first_word or "UNKNOWN",
                validation_status="invalid",
                validation_message=f"SQL syntax error: {str(e)}",
                approval_status="pending",
                warning_broad_impact=False
            )

        if ast is None:
            return SQLStatementInfo(
                statement_index=0,
                sql=sql_str,
                operation="UNKNOWN",
                validation_status="invalid",
                validation_message="Unable to parse SQL statement.",
                approval_status="pending",
                warning_broad_impact=False
            )

        # Step 2: Check Prohibited DDL/DCL Operations ALWAYS
        if isinstance(ast, PROHIBITED_TYPES) or first_word in PROHIBITED_KEYWORDS:
            op_name = first_word if first_word in PROHIBITED_KEYWORDS else type(ast).__name__.upper()
            return SQLStatementInfo(
                statement_index=0,
                sql=sql_str,
                operation=op_name,
                validation_status="blocked",
                validation_message=f"Prohibited operation '{op_name}' is blocked by security policy.",
                approval_status="pending",
                warning_broad_impact=False
            )

        # Step 3: Determine Operation Type
        operation = "SELECT"
        if isinstance(ast, exp.Insert):
            operation = "INSERT"
        elif isinstance(ast, exp.Update):
            operation = "UPDATE"
        elif isinstance(ast, exp.Delete):
            operation = "DELETE"
        elif isinstance(ast, exp.Select):
            operation = "SELECT"
        else:
            if first_word in ["INSERT", "UPDATE", "DELETE", "SELECT"]:
                operation = first_word

        # Step 4: Check Role Restrictions (Viewer cannot execute write operations)
        if user_role.lower() == "viewer" and operation != "SELECT":
            return SQLStatementInfo(
                statement_index=0,
                sql=sql_str,
                operation=operation,
                validation_status="blocked",
                validation_message="Viewer role does not have permission to execute UPDATE, INSERT, or DELETE operations.",
                approval_status="pending",
                warning_broad_impact=False
            )

        # Step 5: Extract CTE aliases to avoid false positives on table names
        cte_names: Set[str] = set()
        with_clause = ast.find(exp.With)
        if with_clause:
            for cte in with_clause.expressions:
                if getattr(cte, "alias", None):
                    cte_names.add(str(cte.alias).lower())
                elif getattr(cte, "name", None):
                    cte_names.add(str(cte.name).lower())
                elif hasattr(cte, "this") and getattr(cte.this, "name", None):
                    cte_names.add(str(cte.this.name).lower())

        # Extract Physical Tables
        tables: List[str] = []
        for table in ast.find_all(exp.Table):
            if table.name:
                t_low = table.name.lower()
                if t_low not in cte_names and t_low not in [t.lower() for t in tables]:
                    tables.append(table.name)

        affected_table = tables[0] if tables else None

        # Extract Referenced Columns (from SELECT, WHERE, JOIN, ORDER BY, GROUP BY, SET, VALUES)
        referenced_columns: List[Tuple[Optional[str], str]] = []
        for col in ast.find_all(exp.Column):
            if col.name and col.name != "*":
                col_tbl = col.table.lower() if col.table else None
                referenced_columns.append((col_tbl, col.name.lower()))

        # Step 6: Validate Permissions (Table-level, Column-level, Operation-level)
        if allowed_permissions and "tables" in allowed_permissions:
            tables_config = allowed_permissions.get("tables", {})
            if tables_config:
                for t_name in tables:
                    t_key = t_name.lower()
                    if t_key not in tables_config:
                        # Table not in whitelist — deny access
                        return SQLStatementInfo(
                            statement_index=0,
                            sql=sql_str,
                            operation=operation,
                            validation_status="blocked",
                            validation_message=f"Table '{t_name}' is not allowed. Only permitted tables may be queried.",
                            approval_status="pending",
                            warning_broad_impact=False,
                            affected_table=t_name,
                            tables=tables
                        )

                    t_conf = tables_config[t_key]

                    # 6a. Table explicitly denied
                    if not t_conf.get("allowed", True):
                        return SQLStatementInfo(
                            statement_index=0,
                            sql=sql_str,
                            operation=operation,
                            validation_status="blocked",
                            validation_message=f"Access to table '{t_name}' is denied by permission policy.",
                            approval_status="pending",
                            warning_broad_impact=False,
                            affected_table=affected_table,
                            tables=tables
                        )

                    # 6b. Operation on Table Allowed
                    allowed_ops = [op.upper() for op in t_conf.get("allowed_operations", ["SELECT", "INSERT", "UPDATE", "DELETE"])]
                    if operation not in allowed_ops:
                        return SQLStatementInfo(
                            statement_index=0,
                            sql=sql_str,
                            operation=operation,
                            validation_status="blocked",
                            validation_message=f"Operation '{operation.lower()}' is not permitted on table '{t_name}'.",
                            approval_status="pending",
                            warning_broad_impact=False,
                            affected_table=affected_table,
                            tables=tables
                        )

                    # 6c. Column-level permissions on Table
                    cols_conf = t_conf.get("columns", {})
                    for col_tbl, col_name in referenced_columns:
                        # Match if column belongs to this table or table was omitted in single-table query
                        if col_tbl is None or col_tbl == t_key:
                            if col_name in cols_conf:
                                c_conf = cols_conf[col_name]
                                if not c_conf.get("allowed", True):
                                    return SQLStatementInfo(
                                        statement_index=0,
                                        sql=sql_str,
                                        operation=operation,
                                        validation_status="blocked",
                                        validation_message=f"Access to column '{col_name}' on table '{t_name}' is denied by permission policy.",
                                        approval_status="pending",
                                        warning_broad_impact=False,
                                        affected_table=affected_table,
                                        tables=tables
                                    )
                                c_ops = [op.upper() for op in c_conf.get("allowed_operations", ["SELECT", "INSERT", "UPDATE", "DELETE"])]
                                if operation not in c_ops:
                                    return SQLStatementInfo(
                                        statement_index=0,
                                        sql=sql_str,
                                        operation=operation,
                                        validation_status="blocked",
                                        validation_message=f"Operation '{operation.lower()}' is not permitted on column '{col_name}' on table '{t_name}'.",
                                        approval_status="pending",
                                        warning_broad_impact=False,
                                        affected_table=affected_table,
                                        tables=tables
                                    )

        # Step 7: Broad UPDATE / DELETE check
        warning_broad = False
        validation_status = "valid"
        val_message = "SQL validated successfully."

        if operation in ["UPDATE", "DELETE"]:
            where_clause = ast.find(exp.Where)
            if self._is_broad_where_clause(where_clause):
                warning_broad = True
                validation_status = "warning"
                val_message = f"Warning: Broad {operation} without WHERE clause or with full-table filter will affect all rows."

        # Step 8: Enforce LIMIT on SELECT queries
        final_sql = sql_str
        if operation == "SELECT":
            limit_expression = ast.find(exp.Limit)
            if limit_expression:
                try:
                    lim_val = int(limit_expression.expression.this)
                    if lim_val > self.max_rows:
                        ast.set("limit", exp.Limit(expression=exp.Literal.number(self.max_rows)))
                        final_sql = ast.sql(dialect=glot_dialect)
                except Exception:
                    pass
            else:
                final_sql = f"{sql_str.rstrip(';')} LIMIT {self.max_rows}"

        return SQLStatementInfo(
            statement_index=0,
            sql=final_sql,
            operation=operation,
            validation_status=validation_status,
            validation_message=val_message,
            approval_status="pending",
            warning_broad_impact=warning_broad,
            affected_table=affected_table,
            tables=tables
        )
