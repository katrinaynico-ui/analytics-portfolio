"""Load and lightly validate the credit-card fraud CSV."""
from __future__ import annotations

import pandas as pd

from src.config import FEATURE_COLS, RAW_CSV, TARGET_COL


REQUIRED = ["Time", "Amount", TARGET_COL] + FEATURE_COLS


def load_raw() -> pd.DataFrame:
    if not RAW_CSV.exists():
        raise FileNotFoundError(
            f"Missing {RAW_CSV}. Run: python scripts/download_data.py"
        )
    df = pd.read_csv(RAW_CSV)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")
    print(f"[data_load] loaded {len(df):,} rows × {df.shape[1]} cols from {RAW_CSV.name}")
    return df
