from __future__ import annotations

from typing import Any

import pandas as pd


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned = cleaned.replace({" ": pd.NA, "": pd.NA, "N/A": pd.NA, "nan": pd.NA})
    for column in cleaned.columns:
        if cleaned[column].dtype.kind in 'if':
            cleaned[column] = pd.to_numeric(cleaned[column], errors='coerce')
        elif cleaned[column].dtype == 'object':
            cleaned[column] = cleaned[column].astype(str).str.strip()
            cleaned[column] = cleaned[column].replace({'nan': pd.NA, 'None': pd.NA})
    return cleaned


def data_quality_summary(df: pd.DataFrame) -> dict[str, Any]:
    qualitative = {
        'rows': int(len(df)),
        'columns': int(len(df.columns)),
        'missing_values': int(df.isna().sum().sum()),
        'duplicate_rows': int(df.duplicated().sum()),
    }
    return qualitative
