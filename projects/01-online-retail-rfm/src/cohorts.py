"""Monthly cohort retention via DuckDB SQL (showcases SQL alongside pandas)."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from src.config import COHORT_PARQUET, DATA_PROCESSED, SQL_DIR


def run_cohort_sql(transactions: pd.DataFrame, sql_path: Path | None = None) -> pd.DataFrame:
    """Execute sql/rfm_cohorts.sql against an in-memory DuckDB view of transactions."""
    sql_path = sql_path or (SQL_DIR / "rfm_cohorts.sql")
    sql = sql_path.read_text(encoding="utf-8")
    con = duckdb.connect()
    con.register("transactions", transactions)
    result = con.execute(sql).df()
    con.close()
    print(f"[cohorts] rows={len(result):,} cohorts={result['cohort_month'].nunique()}")
    return result


def save_cohorts(df: pd.DataFrame, path=None) -> None:
    path = path or COHORT_PARQUET
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"[cohorts] wrote {path}")
