"""Clean Online Retail transactions for RFM / modeling."""
from __future__ import annotations

import pandas as pd

from src.config import CLEAN_PARQUET, DATA_PROCESSED


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Drop cancellations/returns, missing customers, non-positive qty/price.

    InvoiceNo starting with 'C' denotes cancellations in this dataset.
    CustomerID missing ≈ guest checkout; excluded because RFM is customer-level.
    """
    out = df.copy()
    out["InvoiceNo"] = out["InvoiceNo"].astype(str)
    out["InvoiceDate"] = pd.to_datetime(out["InvoiceDate"], errors="coerce")
    out["CustomerID"] = pd.to_numeric(out["CustomerID"], errors="coerce")

    before = len(out)
    out = out[~out["InvoiceNo"].str.startswith("C", na=False)]
    out = out.dropna(subset=["CustomerID", "InvoiceDate"])
    out = out[(out["Quantity"] > 0) & (out["UnitPrice"] > 0)]
    out["CustomerID"] = out["CustomerID"].astype(int)
    # StockCode / Description can be mixed int/str in the Excel file — force string for parquet
    out["StockCode"] = out["StockCode"].astype(str)
    out["Description"] = out["Description"].astype(str)
    out["InvoiceNo"] = out["InvoiceNo"].astype(str)
    out["Country"] = out["Country"].astype(str)
    out["line_revenue"] = out["Quantity"] * out["UnitPrice"]
    out = out.sort_values("InvoiceDate").reset_index(drop=True)

    print(
        f"[clean] rows {before:,} → {len(out):,} | "
        f"customers {out['CustomerID'].nunique():,} | "
        f"date range {out['InvoiceDate'].min().date()} → {out['InvoiceDate'].max().date()}"
    )
    return out


def save_clean(df: pd.DataFrame, path=None) -> None:
    path = path or CLEAN_PARQUET
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"[clean] wrote {path}")
