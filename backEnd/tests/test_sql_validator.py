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


def test_sql_validator_system_metadata_tables_permitted():
    validator = SQLValidator(max_rows=100)
    permissions = {
        "tables": {
            "students": {"allowed": True, "columns": {"id": True, "name": True}}
        }
    }
    sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
    res = validator.validate_statement(sql, dialect="postgres", user_role="analyst", permissions=permissions)

    assert res.validation_status == "valid"
    assert res.operation == "SELECT"


def test_sql_validator_system_metadata_tables_prohibit_modification():
    validator = SQLValidator(max_rows=100)
    permissions = {
        "tables": {
            "students": {"allowed": True, "columns": {"id": True, "name": True}}
        }
    }
    sql = "DELETE FROM information_schema.tables WHERE table_name = 'students';"
    res = validator.validate_statement(sql, dialect="postgres", user_role="admin", permissions=permissions)

    assert res.validation_status == "blocked"
    assert "Modifying system metadata table" in res.validation_message


@pytest.mark.asyncio
async def test_mock_llm_insert_faculty_not_hijacked_as_select():
    from app.services.llm_service import MockLLMProvider
    provider = MockLLMProvider()
    query = "add faculty id=6, Prof.Janak Sharma,janak@mail.com who is in 3rd department and he is a professor with 24000 salary"
    res = await provider.generate_sql(query, "postgres", "")

    assert res["status"] == "success"
    assert len(res["sql_statements"]) == 1
    stmt = res["sql_statements"][0]
    assert stmt["operation"] == "INSERT"
    assert "INSERT INTO" in stmt["sql"]
    assert "Prof.Janak Sharma" in stmt["sql"]
    assert "janak@mail.com" in stmt["sql"]
    assert "24000" in stmt["sql"]

    validator = SQLValidator()
    val_res = validator.validate_statement(stmt["sql"], dialect="postgres", user_role="analyst")
    assert val_res.validation_status == "valid"
    assert val_res.operation == "INSERT"


def test_sql_validator_singular_plural_query_plural_db_singular():
    """Verify that a query for 'students' against a database having 'student' validates and rewrites AST."""
    validator = SQLValidator(max_rows=100)
    permissions = {
        "tables": {
            "student": {"allowed": True, "columns": {"id": {"allowed": True}, "name": {"allowed": True}}}
        }
    }
    sql = 'SELECT * FROM "students" LIMIT 5;'
    res = validator.validate_statement(sql, dialect="postgres", user_role="analyst", permissions=permissions)

    assert res.validation_status == "valid"
    assert res.operation == "SELECT"
    assert res.affected_table == "student"
    assert '"student"' in res.sql
    assert "students" not in res.sql


def test_sql_validator_singular_plural_query_singular_db_plural():
    """Verify that a query for 'department' against a database having 'departments' validates and rewrites AST."""
    validator = SQLValidator(max_rows=100)
    permissions = {
        "tables": {
            "departments": {"allowed": True, "columns": {"id": {"allowed": True}, "name": {"allowed": True}}}
        }
    }
    sql = 'SELECT * FROM "department" LIMIT 10;'
    res = validator.validate_statement(sql, dialect="postgres", user_role="analyst", permissions=permissions)

    assert res.validation_status == "valid"
    assert res.operation == "SELECT"
    assert res.affected_table == "departments"
    assert '"departments"' in res.sql


def test_sql_validator_singular_plural_faculty_faculties():
    """Verify that a query for 'faculties' against a database having 'faculty' validates and rewrites AST."""
    validator = SQLValidator(max_rows=100)
    permissions = {
        "tables": {
            "faculty": {"allowed": True, "columns": {"id": {"allowed": True}, "name": {"allowed": True}}}
        }
    }
    sql = 'SELECT * FROM "faculties";'
    res = validator.validate_statement(sql, dialect="postgres", user_role="analyst", permissions=permissions)

    assert res.validation_status == "valid"
    assert res.operation == "SELECT"
    assert res.affected_table == "faculty"
    assert '"faculty"' in res.sql


@pytest.mark.asyncio
async def test_mock_llm_top_n_students_with_singular_plural_resolution():
    """Verify MockLLMProvider extracts Top N limit and resolves singular/plural table names."""
    from app.services.llm_service import MockLLMProvider
    provider = MockLLMProvider()

    # 1. Schema has plural 'students'
    schema_plural = "Table: students\nColumns: student_id, name, email, cgpa"
    res1 = await provider.generate_sql("show top 5 students", "postgres", schema_plural)
    assert res1["status"] == "success"
    stmt1 = res1["sql_statements"][0]
    assert "LIMIT 5" in stmt1["sql"]
    assert '"students"' in stmt1["sql"]
    assert 'ORDER BY "cgpa" DESC' in stmt1["sql"]

    # 2. Schema has singular 'student'
    schema_singular = "Table: student\nColumns: student_id, name, email, cgpa"
    res2 = await provider.generate_sql("show top 5 students", "postgres", schema_singular)
    assert res2["status"] == "success"
    stmt2 = res2["sql_statements"][0]
    assert "LIMIT 5" in stmt2["sql"]
    assert '"student"' in stmt2["sql"]
    assert 'ORDER BY "cgpa" DESC' in stmt2["sql"]




