"""Minimal cleaning — dataset is already numeric / PCA-anonymized."""
from __future__ import annotations

import pandas as pd

from src.config import CLEAN_PARQUET, FEATURE_COLS, TARGET_COL


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out[TARGET_COL] = out[TARGET_COL].astype(int)
    # Drop exact duplicate rows if any (keeps first).
    before = len(out)
    out = out.drop_duplicates().reset_index(drop=True)
    dropped = before - len(out)
    # Basic integrity
    if out[TARGET_COL].isna().any():
        raise ValueError("Null labels found")
    if out["Amount"].isna().any() or (out["Amount"] < 0).any():
        raise ValueError("Invalid Amount values")
    n_fraud = int(out[TARGET_COL].sum())
    rate = n_fraud / len(out)
    print(
        f"[clean] rows={len(out):,} (dropped_dupes={dropped}) | "
        f"fraud={n_fraud} ({rate:.4%}) | features={len(FEATURE_COLS)}"
    )
    return out


def save_clean(df: pd.DataFrame) -> None:
    CLEAN_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEAN_PARQUET, index=False)
    print(f"[clean] wrote {CLEAN_PARQUET}")
