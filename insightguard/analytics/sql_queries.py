from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from insightguard.db.connection import get_db_path


def resolve_sql_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[1] / 'sql',
        Path(__file__).resolve().parents[2] / 'sql',
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


SQL_DIR = resolve_sql_dir()
SQL_RESOURCE_NAMES = frozenset(path.stem for path in SQL_DIR.glob('*.sql'))


def get_sql_query(name: str) -> str:
    if not isinstance(name, str) or name not in SQL_RESOURCE_NAMES:
        raise FileNotFoundError(f'No SQL resource named {name!r} is available.')
    path = SQL_DIR / f'{name}.sql'
    return path.read_text(encoding='utf-8')


def execute_sql_query(
    name: str,
    db_path: str | None = None,
    params: tuple | dict[str, Any] | None = None,
    workspace_id: str | None = None,
) -> pd.DataFrame:
    sql = get_sql_query(name)
    connection_path = db_path or get_db_path()
    query_params = params if params is not None else {'workspace_id': workspace_id}
    with sqlite3.connect(connection_path) as conn:
        return pd.read_sql_query(sql, conn, params=query_params)


def get_dashboard_sql_summary(db_path: str | None = None, workspace_id: str | None = None) -> dict[str, Any]:
    connection_path = db_path or get_db_path()
    query_params = {'workspace_id': workspace_id}
    with sqlite3.connect(connection_path) as conn:
        customers_total = conn.execute(
            'SELECT COUNT(*) FROM customers WHERE (:workspace_id IS NULL OR workspace_id = :workspace_id)',
            query_params,
        ).fetchone()[0]
        churn_rate = conn.execute(
            """SELECT AVG(CAST(cl.churn_label AS REAL))
               FROM churn_labels cl JOIN customers c ON c.customer_id = cl.customer_id
               WHERE (:workspace_id IS NULL OR c.workspace_id = :workspace_id)""",
            query_params,
        ).fetchone()[0]
        avg_engagement = conn.execute(
            """SELECT AVG(u.engagement_index)
               FROM usage_records u JOIN customers c ON c.customer_id = u.customer_id
               WHERE (:workspace_id IS NULL OR c.workspace_id = :workspace_id)""",
            query_params,
        ).fetchone()[0]
        total_revenue = conn.execute(
            """SELECT ROUND(COALESCE(SUM(total_revenue), 0), 2) FROM customers
               WHERE (:workspace_id IS NULL OR workspace_id = :workspace_id)""",
            query_params,
        ).fetchone()[0]

    segments = execute_sql_query('customer_segmentation', db_path=connection_path, workspace_id=workspace_id)
    quality = execute_sql_query('data_quality_checks', db_path=connection_path, workspace_id=workspace_id)
    revenue = execute_sql_query('revenue_and_churn', db_path=connection_path, workspace_id=workspace_id)

    summary: dict[str, Any] = {
        'customers_total': int(customers_total),
        'workspace_id': workspace_id,
        'churn_rate': float(churn_rate) if churn_rate is not None else 0.0,
        'avg_engagement': float(avg_engagement) if avg_engagement is not None else 0.0,
        'total_revenue': float(total_revenue) if total_revenue is not None else 0.0,
        'top_segments': [],
        'revenue_by_segment': [],
        'data_quality': quality.to_dict(orient='records'),
    }

    if not segments.empty:
        summary['top_segments'] = segments.sort_values('churn_rate', ascending=False).head(5).to_dict(orient='records')
        top_row = segments.sort_values('churn_rate', ascending=False).iloc[0]
        summary['segment_highlight'] = {
            'region': top_row.get('region'),
            'contract_type': top_row.get('contract_type'),
            'churn_rate': float(top_row.get('churn_rate', 0.0)),
        }

    if not revenue.empty:
        summary['revenue_by_segment'] = revenue.to_dict(orient='records')

    findings: list[str] = []
    if summary['top_segments']:
        top = summary['top_segments'][0]
        findings.append(
            f"Observed finding: {top['region']} {top['contract_type']} customers show the highest churn rate at {top['churn_rate']:.3f}."
        )
    if summary['revenue_by_segment']:
        highest = max(summary['revenue_by_segment'], key=lambda row: float(row.get('total_revenue', 0)))
        findings.append(
            f"Revenue observation: {highest['contract_type']} generates the highest segment revenue at {float(highest['total_revenue']):,.2f}."
        )
    if summary['data_quality']:
        total_issues = sum(int(item.get('issue_count', 0)) for item in summary['data_quality'])
        findings.append(f"Data-quality check: {total_issues} quality issues were flagged in the current dataset snapshot.")

    summary['observed_findings'] = findings
    return summary
