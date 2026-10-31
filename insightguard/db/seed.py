from __future__ import annotations

import uuid
from datetime import datetime

import numpy as np
import pandas as pd

from insightguard.data.generator import generate_synthetic_dataset
from insightguard.db.connection import get_connection


def seed_demo_workspace(
    workspace_id: str = 'workspace-demo',
    business_name: str = 'Npontu Demo Telecom',
    objective: str = 'customer_churn_prediction',
    n_customers: int = 5000,
    seed: int = 42,
    db_path: str | None = None,
) -> dict[str, object]:
    df = generate_synthetic_dataset(n_customers=n_customers, seed=seed)
    current_time = datetime.utcnow().isoformat(timespec='seconds')

    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO workspaces(workspace_id, business_name, objective, created_at, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            (workspace_id, business_name, objective, current_time),
        )

        for _, row in df.iterrows():
            customer_id = row['customer_id']
            conn.execute(
                """
                INSERT OR REPLACE INTO customers(
                    customer_id, workspace_id, age, gender, region, tenure_months, contract_type,
                    device_type, internet_plan, monthly_spend, total_revenue, customer_value_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    customer_id,
                    workspace_id,
                    row.get('age'),
                    row.get('gender'),
                    row.get('region'),
                    row.get('tenure_months'),
                    row.get('contract_type'),
                    row.get('device_type'),
                    row.get('internet_plan'),
                    row.get('monthly_spend'),
                    row.get('total_revenue'),
                    row.get('customer_value_score'),
                    current_time,
                ),
            )

            conn.execute(
                """
                INSERT OR REPLACE INTO subscriptions(
                    subscription_id, customer_id, plan_name, start_date, end_date, status, monthly_fee, add_on_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"sub-{customer_id}",
                    customer_id,
                    row.get('internet_plan'),
                    datetime.utcnow().strftime('%Y-%m-%d'),
                    '2030-12-31',
                    'active',
                    float(row.get('monthly_spend', 0) or 0),
                    int(row.get('billing_disputes', 0) or 0),
                ),
            )

            for month_index in range(6):
                usage_id = f"usage-{customer_id}-{month_index}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO usage_records(
                        usage_id, customer_id, month, data_usage_gb, call_minutes, sms_count,
                        internet_quality_score, customer_support_tickets, engagement_index, churn_risk_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        usage_id,
                        customer_id,
                        f"2024-{(month_index % 12) + 1:02d}",
                        float(row.get('data_usage_gb', 0) or 0),
                        int(row.get('call_minutes', 0) or 0),
                        int(row.get('sms_count', 0) or 0),
                        float(max(0.1, min(1.0, row.get('engagement_index', 0.5) or 0.5))),
                        int((row.get('complaints', 0) or 0) % 3),
                        float(row.get('engagement_index', 0.5) or 0.5),
                        float(np.clip((row.get('days_late', 0) or 0) / 20, 0, 1)),
                    ),
                )

                payment_id = f"payment-{customer_id}-{month_index}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO payments(payment_id, customer_id, payment_month, amount, status, payment_method, days_late)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payment_id,
                        customer_id,
                        f"2024-{(month_index % 12) + 1:02d}",
                        float(row.get('payment_amount', 0) or 0),
                        'paid' if (row.get('days_late', 0) or 0) <= 2 else 'late',
                        'card',
                        int(row.get('days_late', 0) or 0),
                    ),
                )

            conn.execute(
                """
                INSERT OR REPLACE INTO churn_labels(customer_id, workspace_id, churn_label, churn_probability, captured_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    customer_id,
                    workspace_id,
                    int(row.get('churn_label', 0) or 0),
                    float(min(0.99, max(0.01, (row.get('engagement_index', 0.5) or 0.5) * 0.5 + (row.get('days_late', 0) or 0) / 100))),
                    current_time,
                ),
            )

        conn.commit()

    return {
        'workspace_id': workspace_id, 'business_name': business_name, 'objective': objective,
        'customers_inserted': int(len(df)), 'synthetic_data': True,
    }
