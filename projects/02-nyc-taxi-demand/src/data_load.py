"""Load raw NYC TLC yellow trip parquet files + zone lookup."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import DATA_RAW, KEEP_COLUMNS, SAMPLE_MONTHS, ZONE_LOOKUP_CSV


def raw_trip_paths() -> list[Path]:
    paths = []
    for ym in SAMPLE_MONTHS:
        p = DATA_RAW / f"yellow_tripdata_{ym}.parquet"
        if not p.exists():
            raise FileNotFoundError(
                f"Missing {p}. Run: python scripts/download_data.py"
            )
        paths.append(p)
    return paths


def load_raw_trips() -> pd.DataFrame:
    """Concatenate sample months; keep a stable TLC column subset."""
    frames = []
    for path in raw_trip_paths():
        df = pd.read_parquet(path)
        missing = [c for c in KEEP_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"{path.name} missing columns: {missing}")
        frames.append(df[KEEP_COLUMNS].copy())
        print(f"[load] {path.name}: {len(df):,} rows")
    out = pd.concat(frames, ignore_index=True)
    print(f"[load] combined trips: {len(out):,}")
    return out


def load_zones() -> pd.DataFrame:
    if not ZONE_LOOKUP_CSV.exists():
        raise FileNotFoundError(
            f"Missing {ZONE_LOOKUP_CSV}. Run: python scripts/download_data.py"
        )
    zones = pd.read_csv(ZONE_LOOKUP_CSV)
    # Normalize common TLC lookup headers
    zones.columns = [str(c).strip() for c in zones.columns]
    rename = {
        "LocationID": "LocationID",
        "Borough": "Borough",
        "Zone": "Zone",
        "service_zone": "service_zone",
    }
    zones = zones.rename(columns={c: rename.get(c, c) for c in zones.columns})
    return zones
