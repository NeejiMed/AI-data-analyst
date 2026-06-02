"""
Schema Inspector Agent - extracts database schema at runtiime.

why this is needed for security:
if we hardcode the schema in a prompt, it drifts from reality as the databse
envolves. By extracting the schema at runtime, the LLM always has the current,
accurate schema. It cannot hallucinate tables or columns that don't exist, which reduces the risk of generating invalid SQL queries.
"""

import structlog
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

logger = structlog.get_logger()


def get_schema_context(db: Session) -> str:
    """
    Extract full database schema as a formatted string for LLM injection.
    Returns table names, column names, types and relationships.
    """
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()

    schema_lines = [
        "DATABASE SCHEMA:",
        "==" * 30,
        "The following tables and columns exist in the database.",
        "Only reference these exact table and column names in your SQL queries.",
        "",
    ]

    for table in tables:
        columns = inspector.get_columns(table)
        foreign_keys = inspector.get_foreign_keys(table)

        schema_lines.append(f"Table: {table}")
        schema_lines.append(" Columns:")
        for col in columns:
            nullable = "nullable" if col["nullable"] else "required"
            schema_lines.append(f"  - {col['name']} ({col['type']}, {nullable})")

        if foreign_keys:
            schema_lines.append(" Relationships:")
            for fk in foreign_keys:
                schema_lines.append(
                    f"  - {fk['constrained_columns']} -> "
                    f"{fk['referred_table']}({fk['referred_columns']})"
                )

        schema_lines.append("")  # Blank line between tables

    # add sample value for key categorical columns
    # This helps the LLM generate correct WHERE clause values
    schema_lines.append("SAMPLE VALUES FOR CATEGORICAL COLUMNS:")
    schema_lines.append("==" * 30)

    categorical_queries = {
        "orders.status": "SELECT DISTINCT status FROM orders",
        "orders.region": "SELECT DISTINCT region FROM orders",
        "orders.sales_channel": "SELECT DISTINCT sales_channel FROM orders",
        "customers.segment": "SELECT DISTINCT segment FROM customers",
        "products.category": "SELECT DISTINCT category FROM products",
    }

    for label, query in categorical_queries.items():
        try:
            result = db.execute(text(query))
            values = [str(row[0]) for row in result if row[0]]
            schema_lines.append(f"  {label}: {', '.join(values)}")
        except Exception as e:
            logger.warning(f"Failed to fetch sample values for {label}: {e}")

    logger.info("schema_extracted", table_count=len(tables))
    return "\n".join(schema_lines)


def get_table_row_counts(db: Session) -> dict[str, int]:
    """Returns row counts per table, this is useful for query planning."""
    inspector = inspect(db.bind)
    counts = {}
    for table in inspector.get_table_names():
        try:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            counts[table] = result.scalar()
        except Exception as e:
            logger.warning(f"Failed to fetch row count for {table}: {e}")
            counts[table] = -1  # -1 indicates unknown count due to error
    return counts
