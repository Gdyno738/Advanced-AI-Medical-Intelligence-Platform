"""
One-time DB migration: add the warning column to the predictions table.
Safe to run even if the column already exists.
"""
import sys
sys.path.insert(0, 'd:/medical-ai-platform')

from app.core.config import DATABASE_URL
from sqlalchemy import create_engine, text

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

with engine.connect() as conn:
    result = conn.execute(text("PRAGMA table_info(predictions)"))
    cols = [row[1] for row in result]
    print("Existing columns:", cols)

    if "warning" not in cols:
        conn.execute(text("ALTER TABLE predictions ADD COLUMN warning TEXT"))
        conn.commit()
        print("[OK] Added 'warning' column to predictions table.")
    else:
        print("[OK] 'warning' column already present — nothing to do.")
