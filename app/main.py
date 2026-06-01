from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.workflow import AnalyticsWorkflow
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.data.database import get_db

configure_logging()
logger = structlog.get_logger()
settings = get_settings()


class QueryRequest(BaseModel):
    question: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting application",
        name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env
    )
    yield
    logger.info("Shutting_down_application")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI powered data analyst platform",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health", tags=["system"])
async def health_check():
    """liveness probe for deployment platforms"""
    return {"status": "healthy",
            "version": settings.app_version,
            "env": settings.app_env}

@app.get("/", tags=["system"])
async def root():
    """basic endpoint to verify the app is running"""
    return {"message": f"Welcome to {settings.app_name}!"}


@app.post("/query", tags=["analytics"])
async def query(request: QueryRequest, db: Session = Depends(get_db)):
    """Main analytics endpoint for answering business questions."""
    workflow = AnalyticsWorkflow(db)
    response = workflow.run(request.question)
    return response.to_dict()
