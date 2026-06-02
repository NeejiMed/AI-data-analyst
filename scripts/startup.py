"""
Production startup script for the application.
This runs database initialization and knowledge base ingestion before starting the server.
Idempotent, so it can be safely run multiple times without causing issues.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import structlog

from app.core.logging import configure_logging

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
    from app.data.database import (  # Import Base to ensure all models are registered
        Base,
        get_engine,
    )

    Base.metadata.create_all(bind=get_engine())  # Create tables if they don't exist
    logger.info("database_initialized")

    # Step 2: Seed data if database is empty
    from sqlalchemy import func  # Import func to perform aggregate functions like count
    from sqlalchemy.orm import (
        sessionmaker,  # Import sessionmaker to create a session for database operations
    )

    from app.data.database import (
        get_engine,  # Import get_engine to create a database session
    )
    from app.data.models.business import (
        Order,  # Import Order model to check if the database is empty
    )

    session = sessionmaker(bind=get_engine())  # Create a session factory
    db = session()  # Create a database session
    order_count = db.query(
        func.count(Order.id)
    ).scalar()  # Count the number of orders in the database
    db.close()  # Close the database session

    if order_count == 0:
        logger.info("database_empty_seeding_data")
        from scripts.seed_data import (
            main as seed_main,  # Import the main function from the seed_data script
        )

        seed_main()  # Run the data seeding function
    else:
        logger.info("database_not_empty_skipping_seeding", order_count=order_count)

    # Step 3: Initialize RAG knowledge base
    logger.info("initializing_rag_knowledge_base")
    from app.rag.retrieval import (
        ingest_knowledge_base,  # Import the function to ingest the knowledge base
    )

    count = (
        ingest_knowledge_base()
    )  # Ingest the knowledge base and get the count of ingested items
    logger.info("rag_initialized", chunks=count)

    logger.info("production_startup_complete")


if __name__ == "__main__":
    run_startup()
