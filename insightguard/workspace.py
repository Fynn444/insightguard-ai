from __future__ import annotations

from datetime import datetime
from typing import Any

from insightguard.db.connection import get_connection


def create_workspace(workspace_id: str, business_name: str, objective: str) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO workspaces(workspace_id, business_name, objective, created_at, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            (workspace_id, business_name, objective, datetime.utcnow().isoformat(timespec='seconds')),
        )
        conn.commit()
    return {'workspace_id': workspace_id, 'business_name': business_name, 'objective': objective}


def list_workspaces() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            'SELECT workspace_id, business_name, objective, status, created_at FROM workspaces ORDER BY created_at DESC'
        ).fetchall()
    return [dict(row) for row in rows]
