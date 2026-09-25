"""Clean TLC yellow trips for demand / revenue analytics."""
from __future__ import annotations

import pandas as pd

from src.config import CLEAN_PARQUET, DATA_PROCESSED, SAMPLE_MONTHS


def clean_trips(df: pd.DataFrame) -> pd.DataFrame:
    """Drop invalid timestamps, non-positive fares/passengers, out-of-range months.

    Scope stays inside SAMPLE_MONTHS so stray vendor timestamps do not leak
    into the hourly series used for forecasting.
    """
    out = df.copy()
    before = len(out)

    out["tpep_pickup_datetime"] = pd.to_datetime(
        out["tpep_pickup_datetime"], errors="coerce"
    )
    out["tpep_dropoff_datetime"] = pd.to_datetime(
        out["tpep_dropoff_datetime"], errors="coerce"
    )
    out = out.dropna(subset=["tpep_pickup_datetime", "tpep_dropoff_datetime"])

    # Keep only pickups inside the documented sample months
    month_starts = [pd.Timestamp(f"{ym}-01") for ym in SAMPLE_MONTHS]
    month_ends = [ms + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1) for ms in month_starts]
    mask = False
    for start, end in zip(month_starts, month_ends):
        mask = mask | (
            (out["tpep_pickup_datetime"] >= start) & (out["tpep_pickup_datetime"] < end)
        )
    out = out.loc[mask]

    out["passenger_count"] = pd.to_numeric(out["passenger_count"], errors="coerce")
    out["trip_distance"] = pd.to_numeric(out["trip_distance"], errors="coerce")
    out["fare_amount"] = pd.to_numeric(out["fare_amount"], errors="coerce")
    out["total_amount"] = pd.to_numeric(out["total_amount"], errors="coerce")
    out["PULocationID"] = pd.to_numeric(out["PULocationID"], errors="coerce")
    out["DOLocationID"] = pd.to_numeric(out["DOLocationID"], errors="coerce")

    out = out.dropna(subset=["PULocationID", "fare_amount", "total_amount"])
    out = out[
        (out["fare_amount"] > 0)
        & (out["total_amount"] > 0)
        & (out["trip_distance"] >= 0)
        & (out["tpep_dropoff_datetime"] >= out["tpep_pickup_datetime"])
        & (out["PULocationID"] > 0)
    ]
    # Passenger nulls exist in some months — allow null, drop zero/negative when present
    pc = out["passenger_count"]
    out = out[pc.isna() | (pc > 0)]

    out["PULocationID"] = out["PULocationID"].astype(int)
    out["DOLocationID"] = out["DOLocationID"].fillna(0).astype(int)
    out["pickup_hour"] = out["tpep_pickup_datetime"].dt.floor("h")
    out["hour_of_day"] = out["tpep_pickup_datetime"].dt.hour
    out["day_of_week"] = out["tpep_pickup_datetime"].dt.dayofweek  # Mon=0
    out["date"] = out["tpep_pickup_datetime"].dt.date

    out = out.sort_values("tpep_pickup_datetime").reset_index(drop=True)
    print(
        f"[clean] rows {before:,} → {len(out):,} | "
        f"zones {out['PULocationID'].nunique():,} | "
        f"pickup {out['tpep_pickup_datetime'].min()} → {out['tpep_pickup_datetime'].max()}"
    )
    return out


def save_clean(df: pd.DataFrame, path=None) -> None:
    path = path or CLEAN_PARQUET
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"[clean] wrote {path}")
