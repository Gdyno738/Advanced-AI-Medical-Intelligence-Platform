"""
Database engine and session management.

Provides the SQLAlchemy engine, session factory, and schema migration
for the Advanced AI Medical Intelligence Platform.
"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import DATABASE_URL
from app.db.models import Base

# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Columns the predictions table MUST have (added over time)
_REQUIRED_COLUMNS = {"probabilities", "model_id"}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create or migrate database tables on startup.

    If the predictions table exists but is missing required columns,
    the table is dropped and recreated. This is safe because prediction
    history is non-critical cached data.
    """
    inspector = inspect(engine)

    if "predictions" in inspector.get_table_names():
        existing_cols = {col["name"] for col in inspector.get_columns("predictions")}
        missing = _REQUIRED_COLUMNS - existing_cols

        if missing:
            print(f"[DB] Schema outdated — missing columns: {missing}. Recreating table.")
            with engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS predictions"))
            # Fall through to create_all below

    Base.metadata.create_all(bind=engine)
    print("[DB] Schema ready.")


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session (FastAPI dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
