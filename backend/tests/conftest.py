import sys
import os
import pytest
from fastapi.testclient import TestClient

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.main import app, seed_database_if_empty
from app.database import Base, engine

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    seed_database_if_empty()
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

