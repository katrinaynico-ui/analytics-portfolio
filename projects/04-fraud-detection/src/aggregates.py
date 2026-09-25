"""DuckDB SQL path for EDA aggregates (optional but welcome)."""
from __future__ import annotations

import re

import duckdb
import pandas as pd

from src.config import SQL_DIR


def _extract_selects(sql_text: str) -> list[str]:
    """Strip line comments and return SELECT statements (split on ';')."""
    no_line_comments = re.sub(r"(?m)^\s*--.*?$", "", sql_text)
    parts = [p.strip() for p in no_line_comments.split(";")]
    return [p for p in parts if p.upper().startswith("SELECT")]


def run_fraud_eda_sql(df: pd.DataFrame) -> dict:
    """Execute sql/fraud_eda.sql against an in-memory DuckDB view `tx`."""
    sql_path = SQL_DIR / "fraud_eda.sql"
    sql_text = sql_path.read_text(encoding="utf-8")
    selects = _extract_selects(sql_text)
    if len(selects) < 3:
        raise RuntimeError(f"Expected 3 SELECT statements in {sql_path}, got {len(selects)}")

    con = duckdb.connect(database=":memory:")
    con.register("tx", df)

    summary = con.execute(selects[0]).df().iloc[0].to_dict()
    amount_buckets = con.execute(selects[1]).df()
    by_hour = con.execute(selects[2]).df()
    con.close()

    bucket_list = [
        {
            "amount_bucket": str(r.amount_bucket),
            "is_fraud": int(r.is_fraud),
            "n": int(r.n),
        }
        for r in amount_buckets.itertuples(index=False)
    ]
    hour_list = [
        {
            "hour_of_day": int(r.hour_of_day),
            "n": int(r.n),
            "n_fraud": int(r.n_fraud),
            "fraud_pct": float(r.fraud_pct),
        }
        for r in by_hour.itertuples(index=False)
    ]
    print(
        f"[aggregates] DuckDB EDA: n={int(summary['n_transactions']):,} "
        f"fraud={int(summary['n_fraud'])} ({float(summary['fraud_pct']):.4f}%)"
    )
    return {
        "summary": {
            k: (float(v) if isinstance(v, (int, float)) else v) for k, v in summary.items()
        },
        "amount_buckets": bucket_list,
        "fraud_by_hour_of_day": hour_list,
    }
