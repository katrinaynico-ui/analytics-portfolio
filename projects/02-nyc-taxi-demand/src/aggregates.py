"""EDA aggregates via DuckDB SQL (analytics-engineer friendly path)."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from src.config import (
    DATA_PROCESSED,
    HOURLY_CITY_PARQUET,
    HOURLY_ZONE_PARQUET,
    SQL_DIR,
)


def run_hourly_zone_sql(
    trips: pd.DataFrame,
    zones: pd.DataFrame,
    sql_path: Path | None = None,
) -> pd.DataFrame:
    """Execute sql/hourly_demand.sql against in-memory DuckDB views."""
    sql_path = sql_path or (SQL_DIR / "hourly_demand.sql")
    sql = sql_path.read_text(encoding="utf-8")
    con = duckdb.connect()
    con.register("trips", trips)
    con.register("zones", zones)
    result = con.execute(sql).df()
    con.close()
    # Normalize pickup_hour timezone-naive
    result["pickup_hour"] = pd.to_datetime(result["pickup_hour"])
    print(
        f"[aggregates] zone-hour rows={len(result):,} | "
        f"hours={result['pickup_hour'].nunique():,} | "
        f"zones={result['location_id'].nunique():,}"
    )
    return result


def citywide_from_zone_hourly(zone_hourly: pd.DataFrame) -> pd.DataFrame:
    """Roll zone-hour to citywide hourly demand (modeling target)."""
    city = (
        zone_hourly.groupby("pickup_hour", as_index=False)
        .agg(
            trip_count=("trip_count", "sum"),
            revenue=("revenue", "sum"),
        )
        .sort_values("pickup_hour")
        .reset_index(drop=True)
    )
    city["hour_of_day"] = city["pickup_hour"].dt.hour
    city["day_of_week"] = city["pickup_hour"].dt.dayofweek  # Mon=0 (pandas)
    city["is_weekend"] = city["day_of_week"].isin([5, 6]).astype(int)
    print(
        f"[aggregates] citywide hours={len(city):,} | "
        f"trips/hour mean={city['trip_count'].mean():.1f}"
    )
    return city


def save_aggregates(zone_hourly: pd.DataFrame, city_hourly: pd.DataFrame) -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    zone_hourly.to_parquet(HOURLY_ZONE_PARQUET, index=False)
    city_hourly.to_parquet(HOURLY_CITY_PARQUET, index=False)
    print(f"[aggregates] wrote {HOURLY_ZONE_PARQUET.name}, {HOURLY_CITY_PARQUET.name}")
