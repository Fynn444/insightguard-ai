from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler


FEATURE_COLUMNS = (
    'age',
    'gender',
    'region',
    'tenure_months',
    'contract_type',
    'device_type',
    'internet_plan',
    'monthly_spend',
    'total_revenue',
    'customer_value_score',
)
CATEGORICAL_FEATURES = ('gender', 'region', 'contract_type', 'device_type', 'internet_plan')
NUMERICAL_FEATURES = tuple(column for column in FEATURE_COLUMNS if column not in CATEGORICAL_FEATURES)
MODEL_ARTIFACT_PATH = Path(__file__).resolve().parents[2] / 'data' / 'models' / 'churn_model.joblib'
ARTIFACT_FORMAT_VERSION = 1


def normalize_features(values: pd.DataFrame) -> pd.DataFrame:
    """Select prediction-time fields and normalize them identically at fit and inference."""
    if not isinstance(values, pd.DataFrame):
        raise TypeError('Customer records must be provided as a pandas DataFrame.')

    normalized = values.reindex(columns=FEATURE_COLUMNS).copy()
    for column in NUMERICAL_FEATURES:
        normalized[column] = pd.to_numeric(normalized[column], errors='coerce')
    for column in CATEGORICAL_FEATURES:
        normalized[column] = normalized[column].map(_normalize_category)
    return normalized


def _normalize_category(value: Any) -> str | float:
    if not isinstance(value, str) or not value.strip():
        return np.nan
    normalized = re.sub(r'[^a-z0-9 ]+', '', value.casefold()).strip()
    return np.nan if normalized in {'', 'unknown', 'none', 'null', 'n a'} else normalized


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return only customer fields known to be available before churn is observed."""
    return normalize_features(df)


def _build_pipeline(model: Any) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())]), list(NUMERICAL_FEATURES)),
            ('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('onehot', OneHotEncoder(handle_unknown='ignore'))]), list(CATEGORICAL_FEATURES)),
        ],
        remainder='drop',
    )
    return Pipeline([
        ('normalize', FunctionTransformer(normalize_features)),
        ('preprocessor', preprocessor),
        ('model', model),
    ])


def _calculate_metrics(y_true: pd.Series, predicted: np.ndarray, probabilities: np.ndarray) -> dict[str, Any]:
    return {
        'accuracy': float(accuracy_score(y_true, predicted)),
        'precision': float(precision_score(y_true, predicted, zero_division=0)),
        'recall': float(recall_score(y_true, predicted, zero_division=0)),
        'f1': float(f1_score(y_true, predicted, zero_division=0)),
        'roc_auc': float(roc_auc_score(y_true, probabilities)) if y_true.nunique() == 2 else None,
        'confusion_matrix': confusion_matrix(y_true, predicted, labels=[0, 1]).tolist(),
    }


def _feature_interpretation(pipeline: Pipeline, X: pd.DataFrame, y: pd.Series, seed: int) -> list[dict[str, Any]]:
    result = permutation_importance(
        pipeline,
        X,
        y,
        scoring='f1',
        n_repeats=3,
        random_state=seed,
        n_jobs=1,
    )
    ranked = sorted(
        zip(FEATURE_COLUMNS, result.importances_mean, result.importances_std),
        key=lambda item: item[1],
        reverse=True,
    )
    return [
        {'feature': feature, 'importance_mean': float(mean), 'importance_std': float(std)}
        for feature, mean, std in ranked
    ]


def save_churn_model(model_bundle: dict[str, Any], model_path: str | Path | None = None) -> str:
    path = Path(model_path) if model_path is not None else MODEL_ARTIFACT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model_bundle, path)
    return str(path)


def load_churn_model(model_path: str | Path | None = None) -> dict[str, Any] | None:
    path = Path(model_path) if model_path is not None else MODEL_ARTIFACT_PATH
    try:
        bundle = joblib.load(path)
    except Exception:
        return None
    if not isinstance(bundle, dict) or bundle.get('format_version') != ARTIFACT_FORMAT_VERSION:
        return None
    if not isinstance(bundle.get('pipeline'), Pipeline) or tuple(bundle.get('feature_columns', ())) != FEATURE_COLUMNS:
        return None
    return bundle


def predict_new_customers(
    records: pd.DataFrame | dict[str, Any] | list[dict[str, Any]],
    model_path: str | Path | None = None,
    model_bundle: dict[str, Any] | None = None,
) -> pd.DataFrame:
    if isinstance(records, dict):
        input_frame = pd.DataFrame([records])
    elif isinstance(records, list):
        input_frame = pd.DataFrame(records)
    elif isinstance(records, pd.DataFrame):
        input_frame = records.copy()
    else:
        raise TypeError('Records must be a DataFrame, a customer-record dictionary, or a list of dictionaries.')
    if input_frame.empty:
        raise ValueError('At least one customer record is required.')
    if not set(input_frame.columns).intersection(FEATURE_COLUMNS):
        raise ValueError('Input must include at least one supported customer feature.')

    bundle = model_bundle if model_bundle is not None else load_churn_model(model_path)
    if bundle is None:
        raise FileNotFoundError('No compatible churn model is available. Train and save a model before making predictions.')
    features = normalize_features(input_frame)
    probabilities = bundle['pipeline'].predict_proba(features)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    result = input_frame.reset_index(drop=True).copy()
    result['probability_churn'] = probabilities
    result['predicted_label'] = predictions
    result['risk_category'] = pd.cut(
        probabilities,
        bins=[-np.inf, 0.30, 0.65, np.inf],
        labels=['Low', 'Medium', 'High'],
        right=False,
    ).astype(str)
    return result


def train_churn_model(
    df: pd.DataFrame,
    test_size: float = 0.2,
    validation_size: float = 0.2,
    seed: int = 42,
    model_path: str | Path | None = None,
) -> tuple[dict[str, Any], pd.DataFrame]:
    if 'churn_label' not in df.columns:
        raise ValueError('DataFrame must include churn_label for model training.')
    if not 0 < test_size < 1 or not 0 < validation_size < 1 or test_size + validation_size >= 1:
        raise ValueError('test_size and validation_size must be positive and sum to less than 1.')

    y = pd.to_numeric(df['churn_label'], errors='coerce')
    valid_target = y.isin([0, 1])
    X = df.loc[valid_target].copy()
    y = y.loc[valid_target].astype(int)
    if y.nunique() != 2 or y.value_counts().min() < 3:
        raise ValueError('Training requires at least three examples from each churn class.')
    if not set(FEATURE_COLUMNS).intersection(X.columns):
        raise ValueError('Training data has no supported prediction-time features.')

    X_development, X_test, y_development, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )
    relative_validation_size = validation_size / (1 - test_size)
    X_train, X_validation, y_train, y_validation = train_test_split(
        X_development,
        y_development,
        test_size=relative_validation_size,
        random_state=seed,
        stratify=y_development,
    )

    candidates = {
        'logistic_regression': LogisticRegression(max_iter=1000, class_weight='balanced', random_state=seed),
        'random_forest': RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_leaf=3,
            class_weight='balanced',
            random_state=seed,
            n_jobs=1,
        ),
    }
    validation_scores: dict[str, float] = {}
    pipelines: dict[str, Pipeline] = {}
    test_predictions: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    comparison: dict[str, Any] = {}

    for model_name, estimator in candidates.items():
        pipeline = _build_pipeline(estimator)
        pipeline.fit(X_train, y_train)
        validation_prediction = pipeline.predict(X_validation)
        validation_scores[model_name] = float(f1_score(y_validation, validation_prediction, zero_division=0))
        test_prediction = pipeline.predict(X_test)
        test_probability = pipeline.predict_proba(X_test)[:, 1]
        comparison[model_name] = {
            'validation_f1': validation_scores[model_name],
            'test_metrics': _calculate_metrics(y_test, test_prediction, test_probability),
        }
        pipelines[model_name] = pipeline
        test_predictions[model_name] = (test_prediction, test_probability)

    selected_model = max(candidates, key=lambda name: validation_scores[name])
    selected_pipeline = pipelines[selected_model]
    selected_prediction, selected_probability = test_predictions[selected_model]
    selected_test_metrics = comparison[selected_model]['test_metrics']
    bundle = {
        'format_version': ARTIFACT_FORMAT_VERSION,
        'pipeline': selected_pipeline,
        'model_name': selected_model,
        'feature_columns': FEATURE_COLUMNS,
        'selection_metric': 'validation_f1',
        'selection_score': validation_scores[selected_model],
        'test_metrics': selected_test_metrics,
    }
    artifact_path = save_churn_model(bundle, model_path)
    interpretation = _feature_interpretation(selected_pipeline, X_validation, y_validation, seed)
    report: dict[str, Any] = {
        'selected_model': selected_model,
        'selection_metric': 'validation_f1',
        'validation_selection_scores': validation_scores,
        'test_metrics': selected_test_metrics,
        'model_comparison': comparison,
        'feature_importance_method': 'permutation importance on the validation split, scored by F1; descriptive, not causal',
        'feature_importance': interpretation,
        'feature_columns': list(FEATURE_COLUMNS),
        'excluded_columns': sorted(set(df.columns) - set(FEATURE_COLUMNS) - {'churn_label'}),
        'artifact_path': artifact_path,
        'split_sizes': {
            'train': int(len(X_train)),
            'validation': int(len(X_validation)),
            'test': int(len(X_test)),
        },
    }

    test_output = X_test.copy()
    if 'customer_id' in test_output.columns:
        test_output['customer_id'] = test_output['customer_id']
    test_output['actual_label'] = y_test.to_numpy()
    test_output['predicted_label'] = selected_prediction
    test_output['probability_churn'] = selected_probability
    test_output['risk_category'] = pd.cut(
        selected_probability,
        bins=[-np.inf, 0.30, 0.65, np.inf],
        labels=['Low', 'Medium', 'High'],
        right=False,
    ).astype(str)
    return report, test_output.reset_index(drop=True)
