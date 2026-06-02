"""
AI Data Analyst - FastAPI Application
Production-grade API with observability, health checks, and analytics.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.observability.health import get_full_health_status
from app.core.observability.metrics import get_metrics_summary
from app.core.observability.middleware import RequestLoggingMiddleware
from app.data.database import get_db

configure_logging()
logger = structlog.get_logger()
settings = get_settings()


class QueryRequest(BaseModel):
    question: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "starting_application",
        name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )
    yield
    logger.info("shutting_down_application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered data analyst platform",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# Middleware — order matters, first added = outermost
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check.
    Returns status of all system components.
    Used by deployment platforms for liveness/readiness probes.
    """
    return get_full_health_status(db)


@app.get("/metrics", tags=["system"])
async def metrics():
    """
    Application metrics endpoint.
    Returns LLM usage, workflow stats, and performance data.
    """
    return get_metrics_summary()


@app.get("/", tags=["system"])
async def root():
    return {"message": f"{settings.app_name} is running"}


@app.post("/query", tags=["analytics"])
async def query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Main analytics endpoint.
    Accepts a business question, returns complete AI analysis.
    """
    from app.agents.workflow import AnalyticsWorkflow
    from app.core.observability.metrics import record_workflow_run

    workflow = AnalyticsWorkflow(db)
    response = workflow.run(request.question)

    record_workflow_run(
        intent=response.intent.value,
        processing_time_ms=response.processing_time_ms,
        success=response.success,
        error=response.error,
    )

    return response.to_dict()
