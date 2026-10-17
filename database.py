import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://homematch:homematch_dev@db:5432/homematch",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Yield a database session and always close it after the request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
