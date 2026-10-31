from __future__ import annotations

import sqlite3


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workspaces (
    workspace_id TEXT PRIMARY KEY,
    business_name TEXT NOT NULL,
    objective TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    region TEXT,
    tenure_months INTEGER,
    contract_type TEXT,
    device_type TEXT,
    internet_plan TEXT,
    monthly_spend REAL,
    total_revenue REAL,
    customer_value_score REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    plan_name TEXT,
    start_date TEXT,
    end_date TEXT,
    status TEXT,
    monthly_fee REAL,
    add_on_count INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS usage_records (
    usage_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    month TEXT NOT NULL,
    data_usage_gb REAL,
    call_minutes INTEGER,
    sms_count INTEGER,
    internet_quality_score REAL,
    customer_support_tickets INTEGER,
    engagement_index REAL,
    churn_risk_score REAL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    payment_month TEXT NOT NULL,
    amount REAL,
    status TEXT,
    payment_method TEXT,
    days_late INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS churn_labels (
    customer_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    churn_label INTEGER NOT NULL,
    churn_probability REAL,
    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id)
);

CREATE INDEX IF NOT EXISTS idx_customers_workspace ON customers(workspace_id);
CREATE INDEX IF NOT EXISTS idx_usage_customer_month ON usage_records(customer_id, month);
CREATE INDEX IF NOT EXISTS idx_payments_customer_month ON payments(customer_id, payment_month);
CREATE INDEX IF NOT EXISTS idx_churn_workspace ON churn_labels(workspace_id);
"""


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()
