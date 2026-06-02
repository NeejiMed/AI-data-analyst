"""Unit tests for the SQL query validator."""
import pytest

from app.agents.query_validator import QueryValidationError, validate_sql


class TestSQLValidator:

    def test_valid_select_passes(self):
        sql = "SELECT * FROM orders"
        result = validate_sql(sql)
        assert result.upper().startswith("SELECT")

    def test_drop_blocked(self):
        with pytest.raises(QueryValidationError, match="Only SELECT"):
            validate_sql("DROP TABLE orders")

    def test_delete_blocked(self):
        with pytest.raises(QueryValidationError):
            validate_sql("DELETE FROM orders WHERE id = 1")

    def test_update_blocked(self):
        with pytest.raises(QueryValidationError):
            validate_sql("UPDATE orders SET status = 'refunded'")

    def test_insert_blocked(self):
        with pytest.raises(QueryValidationError):
            validate_sql("INSERT INTO orders VALUES (1, 2, 3)")

    def test_system_table_blocked(self):
        with pytest.raises(QueryValidationError, match="system tables"):
            validate_sql("SELECT * FROM sqlite_master")

    def test_union_injection_blocked(self):
        with pytest.raises(QueryValidationError, match="UNION"):
            validate_sql(
                "SELECT * FROM orders UNION SELECT * FROM customers"
            )

    def test_stacked_query_blocked(self):
        with pytest.raises(QueryValidationError):
            validate_sql("SELECT * FROM orders; DROP TABLE orders")

    def test_limit_added_when_missing(self):
        sql = "SELECT * FROM orders"
        result = validate_sql(sql)
        assert "LIMIT" in result.upper()

    def test_existing_limit_preserved(self):
        sql = "SELECT * FROM orders LIMIT 5"
        result = validate_sql(sql)
        assert "LIMIT 5" in result

    def test_markdown_fence_stripped(self):
        sql = "```sql\nSELECT * FROM orders\n```"
        result = validate_sql(sql)
        assert "```" not in result

    def test_trailing_semicolon_stripped(self):
        sql = "SELECT * FROM orders;"
        result = validate_sql(sql)
        assert not result.rstrip().endswith(";")
