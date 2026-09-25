#!/usr/bin/env python3
"""Download public NYC TLC yellow trip parquet + zone lookup into data/raw/.

Source: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
CDN:    https://d37ci6vzurychx.cloudfront.net/trip-data/

Sample months are listed in src.config.SAMPLE_MONTHS (Jan–Feb 2024 ≈ 100MB).
No synthetic fallback — portfolio metrics require real TLC files.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    DATA_RAW,
    SAMPLE_MONTHS,
    TLC_BASE_URL,
    ZONE_LOOKUP_CSV,
    ZONE_LOOKUP_URL,
)


def _fetch(url: str, dest: Path, min_bytes: int = 1_000) -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= min_bytes:
        print(f"[download] Already present: {dest.name} ({dest.stat().st_size:,} bytes)")
        return dest
    print(f"[download] Fetching {url}")
    urllib.request.urlretrieve(url, dest)
    size = dest.stat().st_size
    print(f"[download] Saved {dest.name} ({size:,} bytes)")
    if size < min_bytes:
        dest.unlink(missing_ok=True)
        raise SystemExit(f"Downloaded file looks too small: {dest}")
    return dest


def download() -> list[Path]:
    paths: list[Path] = []
    for ym in SAMPLE_MONTHS:
        fname = f"yellow_tripdata_{ym}.parquet"
        url = f"{TLC_BASE_URL}/{fname}"
        paths.append(_fetch(url, DATA_RAW / fname, min_bytes=1_000_000))
    paths.append(_fetch(ZONE_LOOKUP_URL, ZONE_LOOKUP_CSV, min_bytes=1_000))
    total = sum(p.stat().st_size for p in paths)
    print(f"[download] Total raw bytes: {total:,} (~{total / 1e6:.1f} MB)")
    if total > 220_000_000:
        print("[download] WARNING: download exceeds ~200MB budget; consider fewer months.")
    return paths


if __name__ == "__main__":
    download()
