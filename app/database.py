"""
Database configuration and session management.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./certificates.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# this lets us swap the session factory in tests so background threads
# hit the test DB instead of the real one
_session_factory_override = None


def get_session_factory():
    """returns the current session factory — overridable for tests"""
    if _session_factory_override is not None:
        return _session_factory_override
    return SessionLocal


def set_session_factory(factory):
    """swap the session factory (used in test fixtures)"""
    global _session_factory_override
    _session_factory_override = factory


class Base(DeclarativeBase):
    """base class for all our models"""
    pass


def get_db():
    """
    Dependency that hands out DB sessions.
    FastAPI injects this wherever we need it, and the finally
    block makes sure we don't leak connections.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
