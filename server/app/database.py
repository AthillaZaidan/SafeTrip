import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "transitshield.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Use DATABASE_URL from env if available (OpenDeploy sets this), otherwise local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Replace postgres:// with postgresql:// if necessary (some managed DBs provide postgres://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite requires check_same_thread=False, PostgreSQL doesn't
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

ENGINE = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
