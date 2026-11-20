import sys
import os
import pytest
os.environ.setdefault("OTP_HASH_SECRET", "test-only-otp-hmac-secret-32-bytes-minimum")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("COLLECTOR_CREDENTIAL", "test-only-collector-credential")
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import app.database as db_module
from app.main import app, seed_database_if_empty
from app.database import Base, get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    test_db_file = os.path.join(backend_root, "test_cynera_runner.db")
    # Always start from a clean disposable test database; stale files can preserve old demo roles/data.
    if os.path.exists(test_db_file):
        os.remove(test_db_file)
    test_db_url = f"sqlite:///{test_db_file}"
    test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})

    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    import app.main as main_module
    main_module.engine = test_engine
    main_module.SessionLocal = TestSessionLocal
    orig_engine = db_module.engine
    orig_session = db_module.SessionLocal
    orig_configured = db_module.IS_DATABASE_CONFIGURED

    db_module.engine = test_engine
    db_module.SessionLocal = TestSessionLocal
    db_module.IS_DATABASE_CONFIGURED = True

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed initial test data
    seed_database_if_empty()

    yield

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    db_module.engine = orig_engine
    db_module.SessionLocal = orig_session
    db_module.IS_DATABASE_CONFIGURED = orig_configured

    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


