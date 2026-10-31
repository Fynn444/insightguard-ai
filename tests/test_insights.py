import logging

import pytest

from insightguard.insights.context import build_business_context
from insightguard.insights.mock import MockInsightsProvider
from insightguard.insights.service import (
    InsightProvider,
    InsightProviderError,
    InsightRequest,
    InsightResponse,
    InsightService,
    ResponseValidationError,
)
from insightguard.snwolley.interface import SnwolleyClient, SnwolleyIntegrationUnavailable


@pytest.fixture
def business_context():
    return {
        'business_kpis': {
            'customers_total': 142,
            'churn_rate': 0.21,
            'avg_engagement': 0.61,
            'total_revenue': 82400.0,
        },
        'customer_segments': {
            'highest_churn_segment': {
                'region': 'North',
                'contract_type': 'monthly',
                'churn_rate': 0.34,
            },
            'top_segments': [],
        },
        'sql_findings': ['SQL found 142 customers in the current snapshot.'],
        'model_findings': {
            'selected_model': 'logistic_regression',
            'held_out_test_metrics': {'f1': 0.48},
            'feature_importance': [
                {'feature': 'tenure_months', 'importance_mean': 0.02},
            ],
        },
    }


def test_mock_provider_satisfies_interface_and_uses_actual_context(business_context):
    provider = MockInsightsProvider()
    assert isinstance(provider, InsightProvider)

    response = InsightService(provider).generate('Executive summary', business_context)

    assert response.provider == 'development_mock'
    assert response.simulated is True
    assert '142 customers' in response.executive_summary
    assert '21.0%' in response.executive_summary
    assert any('North monthly' in item and '34.0%' in item for item in response.recommendations)
    assert any('tenure_months' in item for item in response.evidence)
    assert 'not a Snwolley-generated response' in response.executive_summary


def test_context_builder_preserves_actual_sql_and_model_findings():
    context = build_business_context(
        {
            'customers_total': 9,
            'churn_rate': 0.2,
            'top_segments': [{'region': 'West', 'contract_type': 'prepaid', 'churn_rate': 0.5}],
            'segment_highlight': {'region': 'West', 'contract_type': 'prepaid', 'churn_rate': 0.5},
            'data_quality': [{'issue_type': 'missing_age', 'issue_count': 2}],
            'observed_findings': ['Observed from SQL'],
        },
        {
            'selected_model': 'random_forest',
            'selection_metric': 'validation_f1',
            'validation_selection_scores': {'random_forest': 0.6},
            'test_metrics': {'f1': 0.55},
            'feature_importance': [{'feature': 'tenure_months', 'importance_mean': 0.1}],
        },
    )

    assert context['business_kpis']['customers_total'] == 9
    assert context['customer_segments']['highest_churn_segment']['region'] == 'West'
    assert context['data_quality_checks'][0]['issue_count'] == 2
    assert context['model_findings']['held_out_test_metrics']['f1'] == 0.55
    assert context['model_findings']['feature_importance'][0]['feature'] == 'tenure_months'


@pytest.mark.parametrize(
    'payload',
    [
        {},
        {'executive_summary': '', 'recommendations': [], 'confidence': 'Not assessed', 'provider': 'mock', 'simulated': True},
        {'executive_summary': 'Summary', 'recommendations': 'not-a-list', 'confidence': 'Not assessed', 'provider': 'mock', 'simulated': True},
        {'executive_summary': 'Summary', 'recommendations': [], 'confidence': 'Certain', 'provider': 'mock', 'simulated': True},
        {'executive_summary': 'Summary', 'recommendations': [], 'confidence': [], 'provider': 'mock', 'simulated': True},
    ],
)
def test_invalid_responses_are_rejected(payload):
    with pytest.raises(ResponseValidationError):
        InsightResponse.from_mapping(payload)


def test_service_rejects_provider_provenance_mismatch():
    class InvalidProvider:
        name = 'expected'
        simulated = True

        def generate(self, request: InsightRequest):
            return {
                'executive_summary': 'Response',
                'recommendations': [],
                'confidence': 'Not assessed',
                'provider': 'unexpected',
                'simulated': True,
                'evidence': [],
            }

    with pytest.raises(ResponseValidationError, match='provider does not match'):
        InsightService(InvalidProvider()).generate('summary', {})


def test_provider_failure_is_logged_and_wrapped(caplog):
    class FailedProvider:
        name = 'failing_provider'
        simulated = True

        def generate(self, request: InsightRequest):
            raise RuntimeError('provider detail')

    with caplog.at_level(logging.ERROR, logger='insightguard.insights.service'):
        with pytest.raises(InsightProviderError, match='failing_provider'):
            InsightService(FailedProvider()).generate('summary', {})

    assert 'Insight provider failing_provider failed with RuntimeError.' in caplog.text
    assert 'provider detail' not in caplog.text


def test_snwolley_disabled_without_credentials_fails_safely():
    with pytest.raises(SnwolleyIntegrationUnavailable, match='credentials are missing'):
        SnwolleyClient(use_mock=False, api_key='')


def test_credentials_do_not_enable_undocumented_network_integration():
    with pytest.raises(SnwolleyIntegrationUnavailable, match='documentation is unavailable'):
        SnwolleyClient(use_mock=False, api_key='test-credential')