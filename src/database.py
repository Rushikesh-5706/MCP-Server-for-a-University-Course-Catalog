"""SQLAlchemy engine, session factory, and declarative Base.

DATABASE_URL is read from the environment with a fallback to a local SQLite file.
Call init_db() once at startup to create tables that don't yet exist.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/catalog.db")

# connect_args is only valid for SQLite; it keeps cross-thread sessions working
# in the single-threaded dev server without separate thread pools.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all tables defined under Base if they don't already exist."""
    # Import models so their metadata is registered before create_all runs.
    from src import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session():
    """Yield a database session and close it when the caller is done."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
