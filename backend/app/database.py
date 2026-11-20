import json
import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

def resolve_db_url(raw_url: str) -> str:
    """Ensures local SQLite URLs always resolve to persistent backend/cynera.db."""
    if "sqlite" in raw_url:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cynera_db = os.path.join(backend_dir, "cynera.db").replace(os.sep, "/")
        return f"sqlite:///{cynera_db}"
    return raw_url

db_url = resolve_db_url(settings.DATABASE_URL)
connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

engine = create_engine(db_url, connect_args=connect_args)

# Enforce foreign key constraints in SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in db_url:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Supabase Client Wrapper (if credentials are provided)
supabase_client = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        print("[Supabase] Successfully connected to live Supabase backend.")
    except Exception as e:
        print(f"[Supabase] Could not connect to Supabase: {e}. Using SQLAlchemy engine.")
