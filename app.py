from __future__ import annotations

import os
import re

import pandas as pd
import streamlit as st

from insightguard.analytics.sql_queries import execute_sql_query, get_dashboard_sql_summary
from insightguard.config import get_settings
from insightguard.data.generator import generate_synthetic_dataset
from insightguard.db.connection import init_db
from insightguard.db.seed import seed_demo_workspace
from insightguard.insights.context import build_business_context
from insightguard.ml.pipeline import predict_new_customers, train_churn_model
from insightguard.reporting.report_generator import generate_report_bytes
from insightguard.snwolley.interface import SnwolleyClient, SnwolleyIntegrationUnavailable
from insightguard.workspace import create_workspace, list_workspaces


st.set_page_config(page_title='InsightGuard AI', layout='wide')
settings = get_settings()

if not os.path.exists(settings['DB_PATH']):
    init_db(settings['DB_PATH'])
    seed_demo_workspace()


st.title('InsightGuard AI')

with st.sidebar:
    st.header('Workspace')
    business_name = st.text_input('Business name', value='Npontu Demo Telecom')
    objective = st.selectbox('Business objective', ['customer_churn_prediction', 'sales_forecasting'])
    workspace_id = st.text_input('Workspace ID', value='workspace-demo')
    if st.button('Create workspace'):
        create_workspace(workspace_id, business_name, objective)
        seed_demo_workspace(workspace_id=workspace_id, business_name=business_name, objective=objective)
        st.success(f'Workspace {workspace_id} created and seeded')

    workspaces = list_workspaces()
    if workspaces:
        selected = st.selectbox('Select workspace', [w['workspace_id'] for w in workspaces])
    else:
        selected = workspace_id
    st.caption('Synthetic data only. AI output is marked as simulated when the real toolkit is unavailable.')

st.subheader('Overview')
col1, col2, col3 = st.columns(3)
col1.metric('Workspaces', len(list_workspaces()))
col2.metric('Objective', objective)
col3.metric('Data source', 'Synthetic telecom dataset')

summary = get_dashboard_sql_summary(settings['DB_PATH'], workspace_id=selected)

st.subheader('Business KPI overview')
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
metric_col1.metric('Customers', summary['customers_total'])
metric_col2.metric('Churn rate', f"{summary['churn_rate'] * 100:.2f}%")
metric_col3.metric('Avg engagement', f"{summary['avg_engagement']:.3f}")
metric_col4.metric('Revenue', f"${summary['total_revenue']:,.2f}")

if summary.get('observed_findings'):
    st.subheader('Observed SQL findings')
    for finding in summary['observed_findings']:
        st.markdown(f'- {finding}')

st.subheader('Customer segments')
segments = execute_sql_query('customer_segmentation', db_path=settings['DB_PATH'], workspace_id=selected)
if not segments.empty:
    st.dataframe(segments.head(20), use_container_width=True)
    st.bar_chart(segments[['region', 'churn_rate']].groupby('region').mean().reset_index().rename(columns={'churn_rate': 'avg_churn_rate'}), x='region', y='avg_churn_rate')

st.subheader('Revenue comparison')
revenue = execute_sql_query('revenue_and_churn', db_path=settings['DB_PATH'], workspace_id=selected)
if not revenue.empty:
    st.dataframe(revenue, use_container_width=True)

st.subheader('Data quality')
quality = execute_sql_query('data_quality_checks', db_path=settings['DB_PATH'], workspace_id=selected)
if not quality.empty:
    st.dataframe(quality, use_container_width=True)

@st.cache_data(show_spinner=False)
def get_demo_dataset() -> pd.DataFrame:
    return generate_synthetic_dataset(n_customers=2500, seed=42)


st.subheader('Dataset preview')
df = get_demo_dataset()
st.dataframe(df.head(10), use_container_width=True)

@st.cache_data(show_spinner='Training and evaluating churn models...')
def get_model_results(dataset: pd.DataFrame):
    return train_churn_model(dataset)


model_report, historical_predictions = get_model_results(df)
st.subheader('Historical model comparison')
st.caption(
    'Validation F1 selects the model. The metrics below are measured on the same held-out test split, '
    'which is not used for model selection.'
)
comparison_rows = []
for model_name, comparison in model_report['model_comparison'].items():
    test_metrics = comparison['test_metrics']
    comparison_rows.append({
        'Model': model_name.replace('_', ' ').title(),
        'Validation F1': comparison['validation_f1'],
        'Test accuracy': test_metrics['accuracy'],
        'Test precision': test_metrics['precision'],
        'Test recall': test_metrics['recall'],
        'Test F1': test_metrics['f1'],
        'Test ROC-AUC': test_metrics['roc_auc'],
    })
st.dataframe(pd.DataFrame(comparison_rows).set_index('Model'), use_container_width=True)
st.caption(
    f"Selected on validation F1: {model_report['selected_model'].replace('_', ' ').title()} "
    f"({model_report['selection_metric']} = {model_report['validation_selection_scores'][model_report['selected_model']]:.3f})."
)

st.subheader('Selected model: held-out test results')
metric_values = model_report['test_metrics']
test_metric_cols = st.columns(5)
for column, label, key in zip(
    test_metric_cols,
    ['Accuracy', 'Precision', 'Recall', 'F1', 'ROC-AUC'],
    ['accuracy', 'precision', 'recall', 'f1', 'roc_auc'],
):
    column.metric(label, f"{metric_values[key]:.3f}" if metric_values[key] is not None else 'N/A')
st.caption(f"Held-out test records: {model_report['split_sizes']['test']}")
st.dataframe(
    pd.DataFrame(
        metric_values['confusion_matrix'],
        index=['Actual no churn', 'Actual churn'],
        columns=['Predicted no churn', 'Predicted churn'],
    ),
    use_container_width=True,
)

st.subheader('Model interpretation')
st.caption(
    'Permutation importance is measured on the validation split using F1. It describes predictive sensitivity, '
    'not causation.'
)
st.dataframe(pd.DataFrame(model_report['feature_importance']), use_container_width=True)

st.subheader('New-customer prediction')
st.caption('These are new-record predictions, separate from the historical held-out evaluation above.')
with st.form('new_customer_prediction'):
    input_col1, input_col2, input_col3 = st.columns(3)
    with input_col1:
        prediction_age = st.number_input('Age', min_value=18, max_value=100, value=38)
        prediction_gender = st.selectbox('Gender', ['Female', 'Male', 'Other'])
        prediction_region = st.selectbox('Region', ['North', 'South', 'East', 'West', 'Central'])
        prediction_tenure = st.number_input('Tenure (months)', min_value=0, max_value=120, value=24)
    with input_col2:
        prediction_contract = st.selectbox('Contract type', ['monthly', 'annual', 'prepaid', 'enterprise'])
        prediction_device = st.selectbox('Device type', ['Smartphone', 'Tablet', 'Feature Phone'])
        prediction_plan = st.selectbox('Internet plan', ['Basic', 'Standard', 'Premium', 'Unlimited'])
    with input_col3:
        prediction_spend = st.number_input('Monthly spend', min_value=0.0, max_value=1000.0, value=42.0)
        prediction_revenue = st.number_input('Total revenue to date', min_value=0.0, max_value=1000000.0, value=1000.0)
        prediction_value = st.number_input('Customer value score', min_value=0.0, max_value=1.0, value=0.6)
    submitted = st.form_submit_button('Predict churn risk')

if submitted:
    new_record = {
        'age': prediction_age,
        'gender': prediction_gender,
        'region': prediction_region,
        'tenure_months': prediction_tenure,
        'contract_type': prediction_contract,
        'device_type': prediction_device,
        'internet_plan': prediction_plan,
        'monthly_spend': prediction_spend,
        'total_revenue': prediction_revenue,
        'customer_value_score': prediction_value,
    }
    try:
        new_prediction = predict_new_customers(new_record, model_path=model_report['artifact_path'])
    except FileNotFoundError as error:
        st.error(str(error))
    else:
        prediction = new_prediction.iloc[0]
        prediction_cols = st.columns(3)
        prediction_cols[0].metric('Churn probability', f"{prediction['probability_churn']:.1%}")
        prediction_cols[1].metric('Predicted class', 'Churn' if prediction['predicted_label'] else 'No churn')
        prediction_cols[2].metric('Risk category', prediction['risk_category'])

st.subheader('Historical held-out risk distribution')
st.bar_chart(historical_predictions['risk_category'].value_counts())

st.subheader('AI-augmented business insights')
insight_context = build_business_context(summary, model_report)
insight = None
try:
    agent = SnwolleyClient(
        use_mock=settings['SNWOLLEY_USE_MOCK'],
        api_key=settings['SNWOLLEY_API_KEY'],
    )
    insight = agent.generate_insight('Executive summary', insight_context)
except SnwolleyIntegrationUnavailable as error:
    st.warning(str(error))
    st.caption('No AI-generated response is available until the official Snwolley toolkit contract is provided.')
else:
    if insight['simulated']:
        st.warning('DEVELOPMENT MOCK OUTPUT: this response is simulated and is not from Snwolley.')
    st.markdown(insight['executive_summary'])
    st.caption(f"Provider: {insight['provider']} | Confidence: {insight['confidence']}")
    if insight['evidence']:
        st.markdown('**Evidence from supplied analytics**')
        for item in insight['evidence']:
            st.markdown(f'- {item}')
    st.markdown('**Suggested review actions**')
    for recommendation in insight['recommendations']:
        st.markdown(f'- {recommendation}')

report_insights = []
if insight is not None:
    report_insights.extend([insight['executive_summary'], *insight['evidence'], *insight['recommendations']])
else:
    report_insights.append('AI insight unavailable because official Snwolley setup has not been supplied.')

report_summary = '\n'.join([
    f'Workspace: {selected}',
    f"Customers: {summary['customers_total']:,}",
    f"Observed churn rate: {summary['churn_rate']:.4f}",
    f"Average engagement: {summary['avg_engagement']:.4f}",
    f"Total revenue: {summary['total_revenue']:.2f}",
    f"Selected model: {model_report['selected_model']}",
    f"Held-out test F1: {model_report['test_metrics']['f1']:.4f}",
    f"AI provider: {insight['provider'] if insight is not None else 'unavailable'}",
    f"AI simulated: {insight['simulated'] if insight is not None else 'not available'}",
])
safe_workspace_name = re.sub(r'[^A-Za-z0-9_-]+', '_', selected).strip('_')[:64] or 'workspace'
st.download_button(
    'Download business report (PDF)',
    data=generate_report_bytes('InsightGuard Business Summary', report_summary, report_insights),
    file_name=f'insightguard-{safe_workspace_name}-report.pdf',
    mime='application/pdf',
)
