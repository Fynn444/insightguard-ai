from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from insightguard.data.generator import generate_synthetic_dataset


def main() -> None:
    data_dir = Path(__file__).resolve().parents[1] / 'data'
    data_dir.mkdir(exist_ok=True)
    df = generate_synthetic_dataset(n_customers=5000, seed=42)
    output = data_dir / 'synthetic_customer_data.csv'
    df.to_csv(output, index=False)
    print(f'Generated {len(df)} synthetic customers and saved to {output}')


if __name__ == '__main__':
    main()
