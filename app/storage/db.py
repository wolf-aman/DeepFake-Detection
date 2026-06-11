import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
import app.config as config


def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS speakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            embedding_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def insert_speaker(name: str, embedding_path: str) -> int:
    """
    Insert a new speaker into the database.
    
    Args:
        name: Unique speaker name
        embedding_path: Path to the stored embedding file
        
    Returns:
        The ID of the inserted speaker
        
    Raises:
        sqlite3.IntegrityError: If speaker name already exists
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO speakers (name, embedding_path, created_at) VALUES (?, ?, ?)",
        (name, embedding_path, datetime.now())
    )
    
    speaker_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return speaker_id


def get_speaker(name: str) -> Optional[Dict]:
    """
    Retrieve a speaker by name.
    
    Args:
        name: Speaker name to search for
        
    Returns:
        Dictionary with speaker data or None if not found
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM speakers WHERE name = ?", (name,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None


def list_speakers() -> List[Dict]:
    """
    List all enrolled speakers.
    
    Returns:
        List of dictionaries containing speaker data
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM speakers ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]


def delete_speaker(name: str) -> bool:
    """
    Delete a speaker from the database.
    
    Args:
        name: Speaker name to delete
        
    Returns:
        True if speaker was deleted, False if not found
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM speakers WHERE name = ?", (name,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted


init_db()
