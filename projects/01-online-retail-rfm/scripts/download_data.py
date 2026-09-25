#!/usr/bin/env python3
"""Download UCI Online Retail (public) into data/raw/.

Prefer the real UCI file. A synthetic sample is written ONLY if download fails,
and it is clearly labeled — do not treat it as production evidence.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import DATA_RAW, DATASET_URL, RAW_XLSX  # noqa: E402


def download() -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    if RAW_XLSX.exists() and RAW_XLSX.stat().st_size > 1_000_000:
        print(f"[download] Already present: {RAW_XLSX} ({RAW_XLSX.stat().st_size:,} bytes)")
        return RAW_XLSX

    print(f"[download] Fetching {DATASET_URL}")
    try:
        urllib.request.urlretrieve(DATASET_URL, RAW_XLSX)
    except Exception as exc:  # noqa: BLE001 — last-resort fallback below
        print(f"[download] FAILED: {exc}")
        print("[download] Writing SYNTHETIC SAMPLE only as last resort (not real UCI data).")
        _write_synthetic_sample(RAW_XLSX.with_name("Online_Retail_SYNTHETIC.csv"))
        raise SystemExit(
            "Real dataset download failed. Synthetic CSV written for debugging; "
            "re-run when network to archive.ics.uci.edu is available."
        ) from exc

    size = RAW_XLSX.stat().st_size
    print(f"[download] Saved {RAW_XLSX} ({size:,} bytes)")
    if size < 1_000_000:
        raise SystemExit("Downloaded file looks too small; aborting.")
    return RAW_XLSX


def _write_synthetic_sample(path: Path) -> None:
    """Tiny fake transactions — labeled synthetic; never for portfolio claims."""
    import csv
    from datetime import datetime, timedelta

    path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2011, 1, 1)
    rows = [
        ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
    ]
    for i in range(200):
        rows.append(
            [
                f"5{10000 + i}",
                f"SKU{i % 20}",
                "SYNTHETIC SAMPLE PRODUCT — NOT REAL DATA",
                (i % 5) + 1,
                (start + timedelta(days=i % 120)).strftime("%Y-%m-%d %H:%M:%S"),
                round(1.5 + (i % 10) * 0.5, 2),
                10000 + (i % 40),
                "United Kingdom",
            ]
        )
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print(f"[download] Synthetic sample at {path}")


if __name__ == "__main__":
    download()
