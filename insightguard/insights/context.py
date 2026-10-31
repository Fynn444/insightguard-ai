from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, 'item'):
        return _json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def build_business_context(sql_summary: dict[str, Any], model_report: dict[str, Any]) -> dict[str, Any]:
    """Create a bounded, JSON-safe insight payload from computed dashboard results."""
    business_kpis = {
        'customers_total': sql_summary.get('customers_total', 0),
        'churn_rate': sql_summary.get('churn_rate'),
        'avg_engagement': sql_summary.get('avg_engagement'),
        'total_revenue': sql_summary.get('total_revenue'),
    }
    customer_segments = {
        'highest_churn_segment': sql_summary.get('segment_highlight'),
        'top_segments': sql_summary.get('top_segments', [])[:5],
    }
    model_findings = {
        'selected_model': model_report.get('selected_model'),
        'selection_metric': model_report.get('selection_metric'),
        'validation_selection_scores': model_report.get('validation_selection_scores', {}),
        'model_comparison': model_report.get('model_comparison', {}),
        'held_out_test_metrics': model_report.get('test_metrics', {}),
        'feature_importance_method': model_report.get('feature_importance_method'),
        'feature_importance': model_report.get('feature_importance', [])[:5],
    }

    return _json_safe({
        'business_kpis': business_kpis,
        'customer_segments': customer_segments,
        'revenue_by_segment': sql_summary.get('revenue_by_segment', [])[:10],
        'data_quality_checks': sql_summary.get('data_quality', []),
        'sql_findings': sql_summary.get('observed_findings', []),
        'model_findings': model_findings,
        'data_provenance': {
            'source': 'synthetic telecom demonstration data',
            'sql': 'computed from the project SQLite database',
            'model': 'computed from a held-out test split and validation-set permutation importance',
        },
    })