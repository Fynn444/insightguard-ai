import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from insightguard.data.generator import generate_synthetic_dataset
from insightguard.ml.pipeline import (
    FEATURE_COLUMNS,
    load_churn_model,
    predict_new_customers,
    prepare_features,
    train_churn_model,
)


@pytest.fixture(scope='module')
def trained_model(tmp_path_factory):
    model_path = tmp_path_factory.mktemp('model') / 'churn_model.joblib'
    dataset = generate_synthetic_dataset(n_customers=300, seed=19)
    report, held_out = train_churn_model(dataset, seed=23, model_path=model_path)
    return dataset, report, held_out, model_path


def test_training_compares_models_and_reports_held_out_metrics(trained_model):
    _, report, held_out, _ = trained_model

    assert set(report['model_comparison']) == {'logistic_regression', 'random_forest'}
    assert report['selected_model'] in report['model_comparison']
    assert report['selection_metric'] == 'validation_f1'
    assert report['split_sizes']['train'] + report['split_sizes']['validation'] + report['split_sizes']['test'] == len(trained_model[0])
    for comparison in report['model_comparison'].values():
        metrics = comparison['test_metrics']
        assert {'accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'confusion_matrix'} <= set(metrics)
        assert len(metrics['confusion_matrix']) == 2
        assert all(len(row) == 2 for row in metrics['confusion_matrix'])
    assert len(held_out) == report['split_sizes']['test']
    assert {'actual_label', 'predicted_label', 'probability_churn', 'risk_category'} <= set(held_out)


def test_prediction_features_exclude_identifiers_and_leakage(trained_model):
    dataset, report, _, _ = trained_model
    features = prepare_features(dataset)
    excluded = set(dataset.columns) - set(FEATURE_COLUMNS)

    assert tuple(features.columns) == FEATURE_COLUMNS
    assert {'customer_id', 'workspace_id', 'synthetic_flag', 'churn_label', 'engagement_index', 'data_usage_gb'} <= excluded
    assert not set(report['feature_columns']).intersection(excluded)
    assert 'churn_probability' not in report['feature_columns']


def test_training_is_reproducible(trained_model, tmp_path):
    dataset, expected_report, _, _ = trained_model
    repeated_report, _ = train_churn_model(
        dataset,
        seed=23,
        model_path=tmp_path / 'repeated_model.joblib',
    )

    assert repeated_report['selected_model'] == expected_report['selected_model']
    assert repeated_report['validation_selection_scores'] == expected_report['validation_selection_scores']
    assert repeated_report['model_comparison'] == expected_report['model_comparison']


def test_model_saves_reloads_and_predicts_without_target(trained_model):
    _, report, _, model_path = trained_model
    loaded = load_churn_model(model_path)
    unseen = pd.DataFrame([{
        'age': 44,
        'gender': ' FEMALE ',
        'region': 'North',
        'tenure_months': 8,
        'contract_type': 'Monthly',
        'device_type': 'Smartphone',
        'internet_plan': 'Premium*',
        'monthly_spend': 79.0,
        'total_revenue': 500.0,
        'customer_value_score': 0.32,
    }])

    assert isinstance(loaded, dict)
    assert isinstance(loaded['pipeline'], Pipeline)
    prediction = predict_new_customers(unseen, model_path=model_path)

    assert prediction.loc[0, 'probability_churn'] == pytest.approx(
        predict_new_customers(unseen, model_bundle=loaded).loc[0, 'probability_churn']
    )
    assert 0 <= prediction.loc[0, 'probability_churn'] <= 1
    assert prediction.loc[0, 'predicted_label'] in (0, 1)
    assert prediction.loc[0, 'risk_category'] in {'Low', 'Medium', 'High'}
    assert 'churn_label' not in prediction.columns
    assert report['artifact_path'] == str(model_path)


def test_inference_handles_missing_and_invalid_values(trained_model):
    _, _, _, model_path = trained_model
    prediction = predict_new_customers(
        {'age': 'not-a-number', 'gender': 31, 'region': ' north ', 'contract_type': 'monthly'},
        model_path=model_path,
    )

    assert len(prediction) == 1
    assert prediction['probability_churn'].between(0, 1).all()


def test_invalid_inference_input_is_rejected(trained_model):
    _, _, _, model_path = trained_model

    with pytest.raises(ValueError, match='supported customer feature'):
        predict_new_customers({'customer_id': 'not-a-feature'}, model_path=model_path)
    with pytest.raises(ValueError, match='At least one customer record'):
        predict_new_customers(pd.DataFrame(), model_path=model_path)


def test_missing_or_incompatible_artifact_is_reported_gracefully(tmp_path):
    missing_path = tmp_path / 'missing.joblib'
    incompatible_path = tmp_path / 'incompatible.joblib'
    incompatible_path.write_text('not a joblib model', encoding='utf-8')
    assert load_churn_model(missing_path) is None
    assert load_churn_model(incompatible_path) is None
    with pytest.raises(FileNotFoundError, match='No compatible churn model'):
        predict_new_customers({'age': 30}, model_path=missing_path)


def test_model_comparison_requires_target():
    with pytest.raises(ValueError, match='churn_label'):
        train_churn_model(pd.DataFrame({'age': [25, 30]}))
