from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env', override=False)


def get_settings() -> dict:
    project_root = Path(__file__).resolve().parents[1]
    db_path = Path(os.getenv('DB_PATH', str(project_root / 'data' / 'insightguard.db')))
    if not db_path.is_absolute():
        db_path = project_root / db_path
    return {
        'APP_NAME': os.getenv('APP_NAME', 'InsightGuard AI'),
        'APP_ENV': os.getenv('APP_ENV', 'development'),
        'DB_PATH': str(db_path),
        'DATA_DIR': os.getenv('DATA_DIR', str(project_root / 'data')),
        'SNWOLLEY_API_KEY': os.getenv('SNWOLLEY_API_KEY', ''),
        'SNWOLLEY_USE_MOCK': os.getenv('SNWOLLEY_USE_MOCK', 'true').lower() == 'true',
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    }
