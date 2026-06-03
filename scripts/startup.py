"""
Production startup script for the application.
This runs database initialization and knowledge base ingestion before starting the server.
Idempotent, so it can be safely run multiple times without causing issues.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog  # noqa: E402

from app.core.logging import configure_logging  # noqa: E402

configure_logging()
logger = structlog.get_logger()


def run_startup():
    logger.info("production_startup_begin")

    # Skip heavy initialization in test/CI environment
    if os.environ.get("APP_ENV") == "test":
        logger.info("test_environment_skipping_seed_and_rag")
        from app.data.database import Base, get_engine
        from app.data.models import business  # noqa: F401

        Base.metadata.create_all(bind=get_engine())
        logger.info("production_startup_complete")
        return

    # Step 1: Initialize the database tables
    logger.info("initializing_database")
    from app.data.database import Base, get_engine
    from app.data.models import business  # noqa: F401 — registers all models

    Base.metadata.create_all(bind=get_engine())
    logger.info("database_initialized")

    # Step 2: Seed data if database is empty
    from sqlalchemy import func

    from app.data.database import session_local
    from app.data.models.business import Order

    db = session_local()
    try:
        order_count = db.query(func.count(Order.id)).scalar()
    finally:
        db.close()

    if order_count == 0:
        logger.info("database_empty_seeding_data")
        from scripts.seed_data import main as seed_main

        seed_main()
    else:
        logger.info(
            "database_not_empty_skipping_seeding",
            order_count=order_count,
        )

    # Step 3: Initialize RAG knowledge base
    logger.info("initializing_rag_knowledge_base")
    from app.rag.retrieval import ingest_knowledge_base

    count = ingest_knowledge_base()
    logger.info("rag_initialized", chunks=count)

    logger.info("production_startup_complete")


if __name__ == "__main__":
    run_startup()
