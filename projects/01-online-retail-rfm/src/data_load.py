"""Load raw Online Retail transactions from Excel."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import RAW_XLSX


EXPECTED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


def load_raw(path: Path | None = None) -> pd.DataFrame:
    """Read the UCI Online Retail xlsx into a DataFrame with standard column names."""
    path = path or RAW_XLSX
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run: python scripts/download_data.py"
        )
    df = pd.read_excel(path, engine="openpyxl")
    # Normalize spacing / case differences across mirrors
    df.columns = [str(c).strip().replace(" ", "") for c in df.columns]
    rename = {
        "InvoiceNo": "InvoiceNo",
        "StockCode": "StockCode",
        "Description": "Description",
        "Quantity": "Quantity",
        "InvoiceDate": "InvoiceDate",
        "UnitPrice": "UnitPrice",
        "CustomerID": "CustomerID",
        "CustomerId": "CustomerID",
        "Country": "Country",
    }
    df = df.rename(columns={c: rename.get(c, c) for c in df.columns})
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Unexpected schema; missing columns: {missing}. Got: {list(df.columns)}")
    return df[EXPECTED_COLUMNS].copy()
