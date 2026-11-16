import pytest
from app.services.sql_validator import SQLValidator


def test_validator_cte_handling():
    """Ensure Common Table Expressions (CTEs) are treated as internal CTEs, not checked against DB tables."""
    validator = SQLValidator(max_rows=100)
    sql = """
    WITH regional_sales AS (
        SELECT city, SUM(amount) AS total_sales
        FROM orders
        GROUP BY city
    )
    SELECT city, total_sales FROM regional_sales WHERE total_sales > 1000;
    """
    # Permission allows 'orders' table
    permissions = {
        "tables": {
            "orders": {
                "allowed": True,
                "allowed_operations": ["SELECT"],
                "columns": {
                    "city": {"allowed": True, "allowed_operations": ["SELECT"]},
                    "amount": {"allowed": True, "allowed_operations": ["SELECT"]}
                }
            }
        }
    }
    res = validator.validate_statement(sql, dialect="mysql", user_role="analyst", permissions=permissions)
    assert res.validation_status == "valid"
    assert "orders" in [t.lower() for t in res.tables]
    # 'regional_sales' CTE should not trigger table permission violations
    assert "Table 'regional_sales' is not allowed" not in res.validation_message


def test_validator_table_permission_violation():
    validator = SQLValidator()
    sql = "SELECT id, ssn FROM employee_salaries;"
    permissions = {
        "tables": {
            "students": {"allowed": True, "allowed_operations": ["SELECT"]}
        }
    }
    res = validator.validate_statement(sql, dialect="mysql", user_role="analyst", permissions=permissions)
    assert res.validation_status == "blocked"
    assert "not allowed" in res.validation_message.lower()


def test_validator_column_permission_violation():
    validator = SQLValidator()
    sql = "SELECT id, password_hash FROM users;"
    permissions = {
        "tables": {
            "users": {
                "allowed": True,
                "allowed_operations": ["SELECT"],
                "columns": {
                    "id": {"allowed": True, "allowed_operations": ["SELECT"]},
                    "password_hash": {"allowed": False, "allowed_operations": []}
                }
            }
        }
    }
    res = validator.validate_statement(sql, dialect="mysql", user_role="analyst", permissions=permissions)
    assert res.validation_status == "blocked"
    assert "password_hash" in res.validation_message.lower()


def test_validator_operation_permission_violation():
    validator = SQLValidator()
    # User tries DELETE on students, but permissions only allow SELECT
    sql = "DELETE FROM students WHERE id = 5;"
    permissions = {
        "tables": {
            "students": {
                "allowed": True,
                "allowed_operations": ["SELECT"]
            }
        }
    }
    res = validator.validate_statement(sql, dialect="mysql", user_role="analyst", permissions=permissions)
    assert res.validation_status == "blocked"
    assert "operation 'delete' is not permitted" in res.validation_message.lower()


def test_validator_broad_impact_where_clauses():
    validator = SQLValidator()

    # WHERE 1=1
    res1 = validator.validate_statement("UPDATE students SET status='Active' WHERE 1=1;", dialect="mysql", user_role="analyst")
    assert res1.validation_status == "warning"
    assert res1.warning_broad_impact is True

    # WHERE TRUE
    res2 = validator.validate_statement("DELETE FROM students WHERE TRUE;", dialect="postgres", user_role="analyst")
    assert res2.validation_status == "warning"
    assert res2.warning_broad_impact is True

    # Targeted WHERE clause should NOT trigger broad impact warning
    res3 = validator.validate_statement("UPDATE students SET status='Active' WHERE id = 42;", dialect="mysql", user_role="analyst")
    assert res3.validation_status == "valid"
    assert res3.warning_broad_impact is False


def test_validator_prohibited_statements():
    validator = SQLValidator()
    prohibited = [
        "DROP TABLE users;",
        "ALTER TABLE users DROP COLUMN email;",
        "TRUNCATE TABLE logs;",
        "GRANT ALL PRIVILEGES ON *.* TO 'hacker'@'%';",
        "REVOKE SELECT ON users FROM 'viewer';",
        "CREATE TABLE backdoor (id INT);"
    ]
    for stmt in prohibited:
        res = validator.validate_statement(stmt, dialect="mysql", user_role="analyst")
        assert res.validation_status == "blocked"
        assert "prohibited operation" in res.validation_message.lower()


def test_validator_dialect_limit_injection():
    # MySQL default row limit
    v_mysql = SQLValidator(max_rows=500)
    res_m = v_mysql.validate_statement("SELECT * FROM students;", dialect="mysql", user_role="analyst")
    assert "LIMIT 500" in res_m.sql

    # PostgreSQL default row limit
    v_pg = SQLValidator(max_rows=250)
    res_p = v_pg.validate_statement("SELECT * FROM students;", dialect="postgres", user_role="analyst")
    assert "LIMIT 250" in res_p.sql

    # Query with smaller limit is preserved
    res_small = v_mysql.validate_statement("SELECT * FROM students LIMIT 10;", dialect="mysql", user_role="analyst")
    assert "LIMIT 10" in res_small.sql
    assert "LIMIT 500" not in res_small.sql
