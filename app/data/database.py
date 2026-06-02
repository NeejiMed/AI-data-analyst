import structlog
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class Base(DeclarativeBase):
    pass


def get_engine():
    """
    create SQLAlchemy engine with appropriate settings. Sqlite gets special config for thread safety.
    PostgresSQL works with default settings.
    """
    if settings.database_url.startswith("sqlite"):
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.debug,
        )

        # enable WAL mode for better concurrency in SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    else:
        engine = create_engine(
            settings.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=settings.debug,
        )

    return engine


engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that provides a database session and ensures it's closed after the request.
    """
    db = SessionLocal()
    try:
        yield db

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
