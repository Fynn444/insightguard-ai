from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class UseCaseDefinition:
    name: str
    description: str
    objective: str
    dataset_requirements: dict[str, Any]
    target_definition: str
    metrics: list[str]


USE_CASES: dict[str, UseCaseDefinition] = {
    'customer_churn_prediction': UseCaseDefinition(
        name='customer_churn_prediction',
        description='Predict churn risk for telecom customers based on customer and usage behaviour.',
        objective='Reduce customer attrition and prioritise retention interventions.',
        dataset_requirements={'tables': ['customers', 'subscriptions', 'usage_records', 'payments', 'churn_labels']},
        target_definition='churn_label = 1 indicates a customer leaving within the business horizon.',
        metrics=['precision', 'recall', 'f1', 'roc_auc'],
    )
}


def get_use_case(name: str) -> UseCaseDefinition:
    if name not in USE_CASES:
        raise KeyError(f'Use case {name!r} is not registered.')
    return USE_CASES[name]
