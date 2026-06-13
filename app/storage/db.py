from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from app.core.exceptions import ConflictError, StorageError


@dataclass(frozen=True)
class SpeakerRecord:
    id: int
    name: str
    slug: str
    embedding_path: str
    created_at: str


class SpeakerRepository:
    """SQLite repository for speaker metadata.

    This keeps SQL away from model/business logic and follows the Repository
    pattern, making storage replaceable later if needed.
    """

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            raise StorageError(f"Database operation failed: {exc}") from exc
        finally:
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass

    def init_schema(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS speakers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE,
                    slug TEXT NOT NULL UNIQUE,
                    embedding_path TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    UNIQUE(name COLLATE NOCASE)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_speakers_slug ON speakers(slug)")

    def add(self, *, name: str, slug: str, embedding_path: str) -> SpeakerRecord:
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO speakers (name, slug, embedding_path, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, slug, embedding_path, created_at),
                )
                row_id = int(cursor.lastrowid)
        except StorageError as exc:
            if "UNIQUE" in str(exc):
                raise ConflictError(f"Speaker '{name}' already exists.") from exc
            raise
        return SpeakerRecord(row_id, name, slug, embedding_path, created_at)

    def get_by_name_or_slug(self, value: str) -> SpeakerRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, slug, embedding_path, created_at
                FROM speakers
                WHERE name = ? COLLATE NOCASE OR slug = ?
                """,
                (value, value),
            ).fetchone()
        return self._to_record(row)

    def exists(self, name: str, slug: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM speakers WHERE name = ? COLLATE NOCASE OR slug = ? LIMIT 1",
                (name, slug),
            ).fetchone()
        return row is not None

    def list_all(self) -> list[SpeakerRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, slug, embedding_path, created_at
                FROM speakers
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [self._to_record(row) for row in rows if row is not None]

    def delete(self, name_or_slug: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM speakers WHERE name = ? COLLATE NOCASE OR slug = ?",
                (name_or_slug, name_or_slug),
            )
            return cursor.rowcount > 0

    @staticmethod
    def _to_record(row: sqlite3.Row | None) -> SpeakerRecord | None:
        if row is None:
            return None
        return SpeakerRecord(
            id=int(row["id"]),
            name=str(row["name"]),
            slug=str(row["slug"]),
            embedding_path=str(row["embedding_path"]),
            created_at=str(row["created_at"]),
        )
