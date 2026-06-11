import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
import app.config as config


def init_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS speakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            embedding_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def _connect():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def insert_speaker(name: str, embedding_path: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO speakers (name, embedding_path, created_at) VALUES (?, ?, ?)",
            (name, embedding_path, datetime.now().isoformat()),
        )


def get_speaker(name: str) -> Optional[Dict]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM speakers WHERE name = ?", (name,)).fetchone()
    return dict(row) if row else None


def list_speakers() -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM speakers ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def delete_speaker(name: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM speakers WHERE name = ?", (name,))
    return cursor.rowcount > 0