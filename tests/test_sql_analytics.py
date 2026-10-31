import pandas as pd

from insightguard.analytics.sql_queries import execute_sql_query, get_dashboard_sql_summary
from insightguard.db.connection import init_db
from insightguard.db.seed import seed_demo_workspace


def test_execute_sql_query_returns_expected_structure(tmp_path):
    db_path = tmp_path / 'sql_audit.db'
    init_db(str(db_path))
    seed_demo_workspace(
        workspace_id='ws_sql',
        business_name='SQL Audit',
        objective='customer_churn_prediction',
        n_customers=2000,
        seed=7,
        db_path=str(db_path),
    )

    df = execute_sql_query('customer_segmentation', db_path=str(db_path))

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert {'contract_type', 'region', 'churn_rate', 'avg_engagement'}.issubset(df.columns)


def test_dashboard_summary_exposes_real_business_kpis(tmp_path):
    db_path = tmp_path / 'dashboard_audit.db'
    init_db(str(db_path))
    seed_demo_workspace(
        workspace_id='ws_dash',
        business_name='Dashboard Audit',
        objective='customer_churn_prediction',
        n_customers=2000,
        seed=11,
        db_path=str(db_path),
    )

    summary = get_dashboard_sql_summary(db_path=str(db_path))

    assert summary['customers_total'] > 0
    assert 'churn_rate' in summary
    assert 'top_segments' in summary
    assert 'data_quality' in summary
    assert isinstance(summary['top_segments'], list)


def test_dashboard_analytics_are_scoped_to_selected_workspace(tmp_path):
    db_path = tmp_path / 'workspace_scope.db'
    init_db(str(db_path))
    seed_demo_workspace(
        workspace_id='ws_scope_a',
        business_name='Scope A',
        objective='customer_churn_prediction',
        n_customers=60,
        seed=3,
        db_path=str(db_path),
    )
    seed_demo_workspace(
        workspace_id='ws_scope_b',
        business_name='Scope B',
        objective='customer_churn_prediction',
        n_customers=35,
        seed=4,
        db_path=str(db_path),
    )

    summary_a = get_dashboard_sql_summary(db_path=str(db_path), workspace_id='ws_scope_a')
    summary_b = get_dashboard_sql_summary(db_path=str(db_path), workspace_id='ws_scope_b')
    segments_a = execute_sql_query('customer_segmentation', db_path=str(db_path), workspace_id='ws_scope_a')

    assert summary_a['customers_total'] == 60
    assert summary_b['customers_total'] == 35
    assert summary_a['total_revenue'] != summary_b['total_revenue']
    assert not segments_a.empty
    assert summary_a['workspace_id'] == 'ws_scope_a'


def test_unknown_sql_resource_name_is_rejected():
    import pytest

    with pytest.raises(FileNotFoundError):
        execute_sql_query('../README', db_path='unused.db')
