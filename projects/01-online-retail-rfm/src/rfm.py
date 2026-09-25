"""Classic RFM scoring and segment labels (explainable in interviews)."""
from __future__ import annotations

import pandas as pd

from src.config import DATA_PROCESSED, RFM_PARQUET


def compute_rfm(transactions: pd.DataFrame, as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """Recency (days since last purchase), Frequency (# invoices), Monetary (sum revenue)."""
    as_of = as_of or transactions["InvoiceDate"].max() + pd.Timedelta(days=1)
    g = transactions.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda s: (as_of - s.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("line_revenue", "sum"),
        first_purchase=("InvoiceDate", "min"),
        last_purchase=("InvoiceDate", "max"),
        n_items=("Quantity", "sum"),
        n_products=("StockCode", "nunique"),
    )
    g = g.reset_index()
    # Quintile scores: 5 = best. Recency inverted (lower days = better).
    g["R_score"] = pd.qcut(g["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    g["F_score"] = _score_ascending(g["Frequency"])
    g["M_score"] = _score_ascending(g["Monetary"])
    g["RFM_score"] = g["R_score"] + g["F_score"] + g["M_score"]
    g["segment"] = g.apply(_segment_label, axis=1)
    return g


def _score_ascending(s: pd.Series) -> pd.Series:
    """Quintile score 1..5 with duplicates handled (rank method)."""
    try:
        return pd.qcut(s.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    except ValueError:
        # Too few unique values — fall back to rank percentiles
        return pd.cut(
            s.rank(pct=True),
            bins=[-0.01, 0.2, 0.4, 0.6, 0.8, 1.01],
            labels=[1, 2, 3, 4, 5],
        ).astype(int)


def _segment_label(row: pd.Series) -> str:
    """Simple rule-based segments (transparent; not a black-box clustering claim)."""
    r, f, m = row["R_score"], row["F_score"], row["M_score"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and m >= 3:
        return "Loyal"
    if r >= 4 and f <= 2:
        return "New / Promising"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2:
        return "Hibernating"
    if m >= 4:
        return "Big Spenders"
    return "Need Attention"


def save_rfm(df: pd.DataFrame, path=None) -> None:
    path = path or RFM_PARQUET
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"[rfm] wrote {path} | segments:\n{df['segment'].value_counts().to_string()}")
