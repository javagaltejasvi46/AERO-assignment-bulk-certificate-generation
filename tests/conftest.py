"""
Test fixtures — shared setup for all tests.

The important thing here is that we use a separate SQLite database
for tests so we never touch the real database. Each test gets a clean slate.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db, set_session_factory
from app.main import app

# separate DB for tests so we don't pollute real data
TEST_DB_URL = "sqlite:///./test_certificates.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """
    Creates fresh tables before each test and tears them down after.
    Also swaps the session factory so background threads use the test DB.
    """
    Base.metadata.create_all(bind=test_engine)
    set_session_factory(TestSessionLocal)
    yield
    set_session_factory(None)
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """test client with the DB dependency overridden"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """raw DB session for tests that need to inspect the database directly"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
