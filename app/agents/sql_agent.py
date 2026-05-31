"""
SQL generation agent - converts natural language to validated SQL.

Architecture:
1. Extract real schema from database
2. Build schema-grounded prompt
3. Call LLM to generate SQL
4. Validate generated SQL (security layer)
5. Execute validated SQL
6. Return structured results

The LLM never executes SQL directly.
The validator never skips.
"""
import re
from dataclasses import dataclass, field

import pandas as pd
import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.agents.query_validator import QueryValidationError, validate_sql
from app.agents.schema_inspector import get_schema_context
from app.llm.client import call_llm

logger = structlog.get_logger()

@dataclass
class SQLResult:
    """Structured result from SQL Agent execution."""
    question: str
    generated_sql: str
    validated_sql: str
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    error: str | None = None
    success: bool = True

    def to_dataframe(self) -> pd.DataFrame:
        """Convert rows to a pandas DataFrame for easier analysis."""
        return pd.DataFrame(self.rows, columns=self.columns)

    def to_llm_context(self) -> str:
        """Serialize query results for LLM interpretation."""
        if not self.success:
            return f"Query failed with error: {self.error}"

        lines = [
            f"SQL Query: {self.validated_sql}",
            f"Rows returned: {self.row_count}",
            "",
            "Results:"
        ]

        # Show first 20 rows in context to avoid token overflow
        display_rows = self.rows[:20]
        if self.columns:
            lines.append(" | ".join(self.columns))
            lines.append("-" * 60)
            for row in display_rows:
                lines.append(" | ".join(str(row.get(col, "")) for col in self.columns))

        if self.row_count > 20:
            lines.append(f"... and {self.row_count - 20} more rows.")

        return "\n".join(lines)

SQL_GENERATION_SYSTEM = """You are a precise SQL analyst. Your job is to write
correct, efficient SQLite SELECT queries based on a user's business question
and the provided database schema.

Rules you must follow without exception:
- Write ONLY a SELECT statement — no INSERT, UPDATE, DELETE, DROP, or ALTER
- Use ONLY the exact table and column names from the schema provided
- Always use meaningful column aliases for calculated fields
- For date filtering use: strftime('%Y', order_date) or date comparisons
- For aggregations always include appropriate GROUP BY clauses
- Write clean, readable SQL with proper indentation
- Return ONLY the SQL query — no explanation, no markdown, no commentary"""

def build_sql_prompt(
        question: str,
        schema_context: str
) -> list[dict]:
    return [
        {"role": "system", "content": SQL_GENERATION_SYSTEM},
        {
            "role": "user",
            "content": f"""Generate a SQLite SELECT query for this question:
            {question}

            Schema:
            {schema_context}

            Return only the SQL query, nothing else.""",
        },
    ]

class SQLAgent:
    """
    SQL generation and execution agent. Converts natural language questions into validated SQL queries, executes them.
    """

    def __init__(self, db: Session):
        self.db = db
        self._schema_context : str | None = None

    def _get_schema(self) -> str:
        """Lazy-load and cache schema context to avoid redundant database calls."""
        if self._schema_context is None:
            self._schema_context = get_schema_context(self.db)
        return self._schema_context

    def generate_sql(self, question: str) -> str:
        """Generate SQL from a natural language question using the LLM."""
        schema = self._get_schema()
        messages = build_sql_prompt(question, schema)

        logger.info("generating_sql", question_preview=question[:80])
        raw_sql = call_llm(messages, temperature=0.1, max_tokens=500)

        # strip any accidental markdown the model added
        raw_sql = re.sub(r"```(?:sql)?\s*", "", raw_sql).strip()
        raw_sql = raw_sql.rstrip("```").strip()

        logger.info("sql_generated", sql_preview=raw_sql[:120])
        return raw_sql

    def execute_query(self, sql: str) -> tuple[list[str], list[dict]]:
        """Execute validated SQL and return columns and rows."""
        result = self.db.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return columns, rows

    def run(self, question: str) -> SQLResult:
        """
        Full pipeline: question -> SQL -> validate -> execute -> result.
        This is the only public method should be used. All others are helpers.
        """
        logger.info("sql_agent_run", question=question)

        # Step 1: Generate SQL
        try:
            raw_sql =self.generate_sql(question)
        except Exception as e:
            logger.error("sql_generation_failed", error=str(e))
            return SQLResult(
                question=question,
                generated_sql="",
                validated_sql="",
                error=f"SQL generation failed: {e}",
                success=False
            )

        # Step 2: Validate SQL (security layer)
        try:
            validated_sql = validate_sql(raw_sql)
        except QueryValidationError as e:
            logger.error("sql_validation_failed", error=str(e))
            return SQLResult(
                question=question,
                generated_sql=raw_sql,
                validated_sql="",
                error=f"Query blocked by safety validator: {e}",
                success=False
            )

        # Step 3: Execute SQL
        try:
            columns, rows = self.execute_query(validated_sql)
            logger.info("sql_execution_success", row_count=len(rows), column_count=len(columns))
            return SQLResult(
                question=question,
                generated_sql=raw_sql,
                validated_sql=validated_sql,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                success=True
            )
        except Exception as e:
            logger.error("sql_execution_failed", error=str(e))
            return SQLResult(
                question=question,
                generated_sql=raw_sql,
                validated_sql=validated_sql,
                error=f"Query execution failed: {e}",
                success=False
            )
