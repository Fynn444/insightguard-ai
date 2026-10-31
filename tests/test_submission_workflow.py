from insightguard.analytics.sql_queries import get_dashboard_sql_summary
from insightguard.data.generator import generate_synthetic_dataset
from insightguard.db.connection import init_db
from insightguard.db.seed import seed_demo_workspace
from insightguard.insights.context import build_business_context
from insightguard.insights.mock import MockInsightsProvider
from insightguard.insights.service import InsightService
from insightguard.ml.pipeline import predict_new_customers, train_churn_model


def test_synthetic_to_sql_ml_inference_and_business_insight_workflow(tmp_path):
    db_path = tmp_path / 'submission_workflow.db'
    model_path = tmp_path / 'models' / 'workflow.joblib'
    init_db(str(db_path))
    seeded = seed_demo_workspace(
        workspace_id='workflow_workspace',
        business_name='Workflow Demo',
        objective='customer_churn_prediction',
        n_customers=150,
        seed=31,
        db_path=str(db_path),
    )
    dataset = generate_synthetic_dataset(n_customers=150, seed=31)
    sql_summary = get_dashboard_sql_summary(str(db_path), workspace_id='workflow_workspace')
    model_report, _ = train_churn_model(dataset, seed=31, model_path=model_path)
    new_record = dataset.drop(columns=['churn_label']).iloc[[0]]
    prediction = predict_new_customers(new_record, model_path=model_path)
    context = build_business_context(sql_summary, model_report)
    insight = InsightService(MockInsightsProvider()).generate('Submission workflow summary', context)

    assert seeded['customers_inserted'] == 150
    assert sql_summary['customers_total'] == 150
    assert model_report['artifact_path'] == str(model_path)
    assert 0 <= prediction.loc[0, 'probability_churn'] <= 1
    assert prediction.loc[0, 'risk_category'] in {'Low', 'Medium', 'High'}
    assert insight.simulated is True
    assert insight.provider == 'development_mock'
    assert '150 customers' in insight.executive_summary
