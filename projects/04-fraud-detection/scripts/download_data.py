#!/usr/bin/env python3
"""Download the public credit-card fraud CSV (no Kaggle credentials).

Primary mirror: TensorFlow public GCS bucket
  https://storage.googleapis.com/download.tensorflow.org/data/creditcard.csv
Fallback: Zenodo CC BY 4.0 deposit (10.5281/zenodo.7395559)

Original research release: Worldline / ULB MLG — also on Kaggle & OpenML.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import DATA_RAW, DOWNLOAD_URLS, MIN_RAW_BYTES, RAW_CSV  # noqa: E402


def _fetch(url: str, dest: Path) -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= MIN_RAW_BYTES:
        print(f"[download] Already present: {dest.name} ({dest.stat().st_size:,} bytes)")
        return dest
    print(f"[download] Fetching {url}")
    try:
        urllib.request.urlretrieve(url, dest)
    except urllib.error.URLError as exc:
        raise SystemExit(f"Download failed for {url}: {exc}") from exc
    size = dest.stat().st_size
    print(f"[download] Saved {dest.name} ({size:,} bytes)")
    if size < MIN_RAW_BYTES:
        dest.unlink(missing_ok=True)
        raise SystemExit(
            f"Downloaded file looks too small ({size} bytes); expected >={MIN_RAW_BYTES}. "
            "Check mirror availability."
        )
    return dest


def download() -> Path:
    last_err: Exception | None = None
    for url in DOWNLOAD_URLS:
        try:
            return _fetch(url, RAW_CSV)
        except SystemExit as exc:
            last_err = exc
            print(f"[download] Mirror failed: {exc}")
            RAW_CSV.unlink(missing_ok=True)
            continue
    raise SystemExit(f"All download mirrors failed. Last error: {last_err}")


if __name__ == "__main__":
    path = download()
    print(f"[download] Ready: {path}")
