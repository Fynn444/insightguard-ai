from __future__ import annotations

import uuid
from typing import Any

import numpy as np
import pandas as pd


def _customer_contracts():
    return ['monthly', 'annual', 'prepaid', 'enterprise']


def generate_synthetic_dataset(n_customers: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data: dict[str, list[Any]] = {
        'customer_id': [],
        'workspace_id': [],
        'age': [],
        'gender': [],
        'region': [],
        'tenure_months': [],
        'contract_type': [],
        'device_type': [],
        'internet_plan': [],
        'monthly_spend': [],
        'total_revenue': [],
        'customer_value_score': [],
        'churn_label': [],
        'data_usage_gb': [],
        'call_minutes': [],
        'sms_count': [],
        'engagement_index': [],
        'payment_amount': [],
        'days_late': [],
        'complaints': [],
        'inactive_days': [],
        'billing_disputes': [],
    }

    for _ in range(n_customers):
        customer_id = str(uuid.uuid4())
        contract_type = rng.choice(_customer_contracts(), p=[0.45, 0.25, 0.2, 0.1])
        region = rng.choice(['North', 'South', 'East', 'West', 'Central'])
        tenure = int(np.clip(rng.normal(30, 18), 1, 84))
        age = int(np.clip(rng.normal(38, 12), 18, 75))
        gender = rng.choice(['Male', 'Female', 'Other'])
        device_type = rng.choice(['Smartphone', 'Tablet', 'Feature Phone'])
        internet_plan = rng.choice(['Basic', 'Standard', 'Premium', 'Unlimited'])
        monthly_spend = float(np.clip(rng.normal(42, 18), 10, 150))
        revenue = float(monthly_spend * max(6, tenure / 6))
        value_score = float(np.clip(rng.normal(0.6, 0.2), 0.05, 0.99))

        churn_probability = 0.12
        churn_probability += 0.14 if contract_type == 'prepaid' else 0
        churn_probability += 0.10 if contract_type == 'monthly' else 0
        churn_probability += 0.05 if region in {'North', 'South'} else 0
        churn_probability += max(0, (36 - tenure) / 180)
        churn_probability += max(0, (0.7 - value_score) / 2)
        churn_probability = np.clip(churn_probability, 0.03, 0.82)
        churn_label = int(rng.random() < churn_probability)

        data_usage = float(np.clip(rng.normal(18, 12), 0, 120))
        if churn_label:
            data_usage *= 0.72
        call_minutes = int(np.clip(rng.normal(160, 80), 20, 700))
        sms_count = int(np.clip(rng.normal(120, 60), 10, 500))
        engagement = float(np.clip(rng.normal(0.68, 0.2), 0.05, 0.99))
        if churn_label:
            engagement *= 0.7

        payment_amount = float(np.clip(monthly_spend * rng.uniform(0.7, 1.4), 5, 200))
        days_late = int(rng.choice([0, 1, 2, 5, 10, 20], p=[0.55, 0.2, 0.12, 0.08, 0.04, 0.01]))
        complaints = int(rng.choice([0, 1, 2, 3, 5], p=[0.72, 0.18, 0.06, 0.03, 0.01]))
        inactive_days = int(np.clip(rng.normal(7, 8), 0, 60))
        billing_disputes = int(rng.choice([0, 1, 2], p=[0.82, 0.12, 0.06]))

        if rng.random() < 0.03:
            age = np.nan
        if rng.random() < 0.04:
            monthly_spend = np.nan
        if rng.random() < 0.03:
            contract_type = 'unknown'
        if rng.random() < 0.02:
            internet_plan = 'Premium*'
        if rng.random() < 0.01:
            payment_amount = 99999

        data['customer_id'].append(customer_id)
        data['workspace_id'].append('workspace-demo')
        data['age'].append(age)
        data['gender'].append(gender)
        data['region'].append(region)
        data['tenure_months'].append(tenure)
        data['contract_type'].append(contract_type)
        data['device_type'].append(device_type)
        data['internet_plan'].append(internet_plan)
        data['monthly_spend'].append(monthly_spend)
        data['total_revenue'].append(revenue)
        data['customer_value_score'].append(value_score)
        data['churn_label'].append(churn_label)
        data['data_usage_gb'].append(data_usage)
        data['call_minutes'].append(call_minutes)
        data['sms_count'].append(sms_count)
        data['engagement_index'].append(engagement)
        data['payment_amount'].append(payment_amount)
        data['days_late'].append(days_late)
        data['complaints'].append(complaints)
        data['inactive_days'].append(inactive_days)
        data['billing_disputes'].append(billing_disputes)

    df = pd.DataFrame(data)
    df['synthetic_flag'] = 'synthetic'
    return df
