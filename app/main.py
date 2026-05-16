from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
logger = structlog.get_logger()
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting application",
        name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env
    )
    yield
    logger.info("Shutting down application")

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