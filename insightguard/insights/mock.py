from __future__ import annotations

from typing import Any

from insightguard.insights.service import InsightRequest


class MockInsightsProvider:
    name = 'development_mock'
    simulated = True

    def generate(self, request: InsightRequest) -> dict[str, Any]:
        context = request.context
        kpis = context.get('business_kpis', {})
        segments = context.get('customer_segments', {})
        model = context.get('model_findings', {})

        customers = kpis.get('customers_total')
        churn_rate = kpis.get('churn_rate')
        selected_model = model.get('selected_model')
        test_metrics = model.get('held_out_test_metrics', {})
        test_f1 = test_metrics.get('f1')

        summary_parts = []
        if customers is not None and churn_rate is not None:
            summary_parts.append(
                f"The supplied synthetic SQL snapshot contains {int(customers):,} customers "
                f"with an observed churn rate of {float(churn_rate):.1%}."
            )
        if selected_model and test_f1 is not None:
            summary_parts.append(
                f"The selected {str(selected_model).replace('_', ' ')} model recorded held-out F1 "
                f"of {float(test_f1):.3f}."
            )
        if not summary_parts:
            summary_parts.append('The supplied business context does not contain enough SQL or model results for a specific summary.')
        summary_parts.append('This is a deterministic development mock, not a Snwolley-generated response.')

        evidence = [str(item) for item in context.get('sql_findings', [])[:3]]
        recommendations: list[str] = []
        highest_segment = segments.get('highest_churn_segment')
        if isinstance(highest_segment, dict):
            region = highest_segment.get('region')
            contract = highest_segment.get('contract_type')
            segment_rate = highest_segment.get('churn_rate')
            if region is not None and contract is not None and segment_rate is not None:
                evidence.append(
                    f"SQL segment observation: {region} / {contract}, churn rate {float(segment_rate):.1%}."
                )
                recommendations.append(
                    f"Review the {region} {contract} cohort for retention opportunities; its observed churn rate is "
                    f"{float(segment_rate):.1%}. This segment pattern is descriptive and does not establish cause."
                )

        feature_importance = model.get('feature_importance', [])
        if feature_importance:
            strongest = feature_importance[0]
            feature_name = strongest.get('feature')
            importance = strongest.get('importance_mean')
            if feature_name is not None and importance is not None:
                evidence.append(
                    f"Validation permutation importance ranks {feature_name} highest "
                    f"(mean F1 decrease {float(importance):.4f})."
                )
                recommendations.append(
                    f"Review how {feature_name.replace('_', ' ')} relates to retention workflows; model importance "
                    "is predictive evidence only, not a causal finding."
                )

        if not recommendations:
            recommendations.append('Review the supplied SQL and model findings with business owners before taking action.')

        return {
            'executive_summary': ' '.join(summary_parts),
            'recommendations': recommendations,
            'confidence': 'Not assessed',
            'provider': self.name,
            'simulated': self.simulated,
            'evidence': evidence,
        }