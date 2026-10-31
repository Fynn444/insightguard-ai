from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from insightguard.data.generator import generate_synthetic_dataset
from insightguard.data.validator import data_quality_summary, clean_dataframe
from insightguard.db.connection import init_db
from insightguard.db.seed import seed_demo_workspace
from insightguard.ml.pipeline import train_churn_model


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / 'data' / 'audit_test.db'


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db(str(DB_PATH))
    seed_demo_workspace(workspace_id='ws_audit', business_name='Audit Demo', objective='customer_churn_prediction', n_customers=5000, seed=42)

    df = generate_synthetic_dataset(n_customers=5000, seed=42)
    print('DATASET_ROWS', len(df))
    print('MISSING_VALUES', int(df.isna().sum().sum()))
    print('DUPLICATES', int(df.duplicated().sum()))
    print('LABEL_COUNTS', json.dumps(df['churn_label'].value_counts().to_dict()))

    cleaned = clean_dataframe(df)
    print('CLEANED_MISSING_AFTER', int(cleaned.isna().sum().sum()))
    print('QUALITY_SUMMARY', json.dumps(data_quality_summary(df)))

    with sqlite3.connect(DB_PATH) as conn:
        print('DB_CUSTOMERS', conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0])
        print('DB_WORKSPACES', conn.execute('SELECT COUNT(*) FROM workspaces').fetchone()[0])
        print('DB_CONTRACTS', json.dumps(conn.execute('SELECT contract_type, COUNT(*) FROM customers GROUP BY contract_type ORDER BY COUNT(*) DESC LIMIT 5').fetchall()))
        print('SQL_SEGMENT', json.dumps(conn.execute('SELECT region, contract_type, ROUND(AVG(CASE WHEN churn_label = 1 THEN 1.0 ELSE 0.0 END), 4) AS churn_rate FROM customers LEFT JOIN churn_labels USING (customer_id) GROUP BY region, contract_type ORDER BY churn_rate DESC LIMIT 5').fetchall()))

    metrics, predictions = train_churn_model(df)
    print('MODEL_METRICS', json.dumps(metrics))
    print('PREDICTIONS', predictions.shape)


if __name__ == '__main__':
    main()
