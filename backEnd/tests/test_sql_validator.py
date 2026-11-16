import pytest
from app.services.sql_validator import SQLValidator


def test_sql_validator_select_valid():
    validator = SQLValidator(max_rows=100)
    sql = "SELECT id, name, city FROM students WHERE city = 'Ahmedabad';"
    res = validator.validate_statement(sql, dialect="mysql", user_role="analyst")
    
    assert res.validation_status == "valid"
    assert res.operation == "SELECT"
    assert "LIMIT 100" in res.sql
    assert res.warning_broad_impact is False


def test_sql_validator_prohibited_ddl_drop():
    validator = SQLValidator()
    sql = "DROP TABLE students;"
    res = validator.validate_statement(sql, dialect="mysql", user_role="analyst")
    
    assert res.validation_status == "blocked"
    assert "Prohibited operation" in res.validation_message


def test_sql_validator_viewer_role_blocks_update():
    validator = SQLValidator()
    sql = "UPDATE students SET status = 'Active' WHERE id = 1;"
    res = validator.validate_statement(sql, dialect="mysql", user_role="viewer")
    
    assert res.validation_status == "blocked"
    assert "Viewer role" in res.validation_message


def test_sql_validator_broad_delete_warning():
    validator = SQLValidator()
    sql = "DELETE FROM students;"
    res = validator.validate_statement(sql, dialect="mysql", user_role="analyst")
    
    assert res.validation_status == "warning"
    assert res.warning_broad_impact is True
    assert "without WHERE clause" in res.validation_message


def test_sql_validator_multiple_statement_splitting():
    validator = SQLValidator()
    raw_sql = "UPDATE customers SET name='John' WHERE id=1; DELETE FROM customers WHERE status='inactive';"
    statements = validator.split_statements(raw_sql, dialect="mysql")
    
    assert len(statements) == 2
    assert "UPDATE" in statements[0]
    assert "DELETE" in statements[1]
