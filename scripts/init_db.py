from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from insightguard.db.connection import init_db


def main() -> None:
    db_file = init_db()
    print(f'Database initialised at {db_file}')


if __name__ == '__main__':
    main()
