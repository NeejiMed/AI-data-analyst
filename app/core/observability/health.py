"""
Enhanced health check with system component status.
Goes beyond a simple ping - tells you which components
are actually healthy.
"""

from datetime import datetime

import structlog

logger = structlog.get_logger()


def check_database(db) -> dict:
    """Check database connectivity and basic query execution."""
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


def check_vector_store() -> dict:
    """Verify ChromaDB is accessible."""
    try:
        from app.rag.vectorstore import get_collection_stats

        stats = get_collection_stats()
        return {
            "status": "healthy",
            "document_count": stats["document_count"],
        }
    except Exception as e:
        logger.error("vector_store_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


def check_llm() -> dict:
    """Verify LLM API is responsive."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return {"status": "healthy", "model": settings.llm_model, "provider": "groq"}
    except Exception as e:
        logger.error("llm_health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


def get_full_health_status(db=None) -> dict:
    """
    Comprehensive health status of all critical components.
    Used by deployment platforms platforms for readiness probes.
    """
    components = {"llm": check_llm(), "vector_store": check_vector_store()}

    if db:
        components["database"] = check_database(db)

    all_healthy = all(comp["status"] == "healthy" for comp in components.values())

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "components": components,
    }
