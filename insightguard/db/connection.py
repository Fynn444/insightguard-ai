from __future__ import annotations

import sqlite3
from pathlib import Path

from insightguard.config import get_settings


def get_db_path() -> str:
    return get_settings()['DB_PATH']


def ensure_parent_dir(db_path: str | None = None) -> str:
    target = Path(db_path or get_db_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    return str(target)


def get_connection(db_path: str | None = None):
    path = ensure_parent_dir(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> str:
    from insightguard.db.schema import create_schema

    path = ensure_parent_dir(db_path)
    with get_connection(path) as conn:
        create_schema(conn)
    return path
