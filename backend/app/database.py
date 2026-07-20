"""
Database configuration.

Uses SQLite by default (zero setup, file-based) but the connection string
is read from an environment variable so swapping to PostgreSQL is a
one-line change:

    export DATABASE_URL="postgresql://user:password@host:5432/expenses"

Hosted Postgres providers (Neon, Render, Heroku) often hand out a
"postgres://" URL instead of "postgresql://" — SQLAlchemy 2.x only
accepts the latter, so it's normalized below.
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./expenses.db")

# --- TEMPORARY DIAGNOSTIC (remove once DATABASE_URL is confirmed working) ---
_raw = os.environ.get("DATABASE_URL")
if _raw:
    _scheme = _raw.split("://")[0] if "://" in _raw else "unknown"
    _host = _raw.split("@")[-1].split("/")[0] if "@" in _raw else "unknown"
    print(f"[DIAGNOSTIC] DATABASE_URL env var FOUND. scheme={_scheme!r} host={_host!r}", file=sys.stderr)
else:
    print("[DIAGNOSTIC] DATABASE_URL env var NOT FOUND — falling back to SQLite.", file=sys.stderr)
# --- END DIAGNOSTIC ---

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()