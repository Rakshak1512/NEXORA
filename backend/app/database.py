import os
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi import HTTPException, status
from .config import settings

logger = logging.getLogger("cynera.database")

Base = declarative_base()

# Connection string precedence: SUPABASE_DB_URL > DATABASE_URL
raw_db_url = settings.get_active_db_url()

# Status flag
IS_DATABASE_CONFIGURED = bool(raw_db_url)
DATABASE_STATUS = "CONNECTED" if IS_DATABASE_CONFIGURED else "BLOCKED_BY_CONFIGURATION"

if raw_db_url:
    if "postgresql" in raw_db_url or "postgres" in raw_db_url:
        # PostgreSQL Connection Pooling for Supabase / Cloud
        engine = create_engine(
            raw_db_url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        logger.info("[Database] Primary engine configured: Supabase PostgreSQL (pooled).")
    elif "sqlite" in raw_db_url:
        engine = create_engine(raw_db_url, connect_args={"check_same_thread": False})
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        logger.info("[Database] Engine configured: Local SQLite store.")
    else:
        engine = create_engine(raw_db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # No connection string configured
    engine = None
    SessionLocal = None
    logger.warning("[Database] No database URL configured in backend/.env. Database functionality is BLOCKED BY CONFIGURATION.")

def get_db():
    """Dependency for injecting SQLAlchemy database sessions with strict configuration guards and safe error handling."""
    if not SessionLocal:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Primary Supabase PostgreSQL database is not configured. Database-dependent operations are BLOCKED BY CONFIGURATION. Please enter SUPABASE_DB_URL in backend/.env."
        )
    db = SessionLocal()
    try:
        yield db
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Database Error] Session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection or transaction error: {str(e)}"
        )
    finally:
        try:
            db.close()
        except Exception:
            pass

def test_database_connection() -> dict:
    """Executes a real query against the target database to verify live connectivity."""
    if not engine:
        return {
            "connected": False,
            "status": "BLOCKED_BY_CONFIGURATION",
            "message": "SUPABASE_DB_URL and DATABASE_URL are empty. Please configure Supabase in backend/.env."
        }
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "connected": True,
            "status": "CONNECTED",
            "engine": "postgresql" if "postgresql" in raw_db_url else "sqlite",
            "message": "Database connection verified successfully."
        }
    except Exception as e:
        return {
            "connected": False,
            "status": "CONNECTION_FAILED",
            "message": f"Could not establish database connection: {e}"
        }

# Optional Supabase Client Wrapper (if credentials are provided)
supabase_client = None
if settings.SUPABASE_URL and (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY or settings.SUPABASE_KEY):
    try:
        from supabase import create_client
        key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY or settings.SUPABASE_KEY
        supabase_client = create_client(settings.SUPABASE_URL, key)
        logger.info("[Supabase Client] Successfully initialized Supabase API client.")
    except Exception as e:
        logger.warning(f"[Supabase Client] Could not initialize Supabase API client: {e}")
