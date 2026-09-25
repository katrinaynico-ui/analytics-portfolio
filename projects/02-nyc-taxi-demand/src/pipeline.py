"""End-to-end local pipeline: load → clean → SQL aggregates → models → metrics."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.aggregates import citywide_from_zone_hourly, run_hourly_zone_sql, save_aggregates
from src.clean import clean_trips, save_clean
from src.config import (
    DATA_PROCESSED,
    DATASET_CITATION,
    DATASET_LICENSE,
    DATASET_NAME,
    HOLD_OUT_DAYS,
    METRICS_JSON,
    REPORTS,
    SAMPLE_MONTHS,
    TLC_PAGE,
)
from src.data_load import load_raw_trips, load_zones
from src.models import build_hourly_features, evaluate_demand, save_features, temporal_split


def run() -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    raw = load_raw_trips()
    zones = load_zones()
    clean = clean_trips(raw)
    save_clean(clean)

    zone_hourly = run_hourly_zone_sql(clean, zones)
    city_hourly = citywide_from_zone_hourly(zone_hourly)
    save_aggregates(zone_hourly, city_hourly)

    features = build_hourly_features(city_hourly)
    save_features(features)
    bundle = temporal_split(features, hold_out_days=HOLD_OUT_DAYS)
    demand_metrics = evaluate_demand(bundle)

    # Simple EDA snapshots (honest, from processed tables)
    by_hour = (
        city_hourly.groupby("hour_of_day")["trip_count"].mean().round(1).to_dict()
    )
    by_dow = (
        city_hourly.groupby("day_of_week")["trip_count"].mean().round(1).to_dict()
    )
    top_zones = (
        zone_hourly.groupby(["location_id", "zone_name", "borough"], as_index=False)[
            "trip_count"
        ]
        .sum()
        .sort_values("trip_count", ascending=False)
        .head(10)
    )
    top_zones_list = [
        {
            "location_id": int(r.location_id),
            "zone_name": r.zone_name,
            "borough": r.borough,
            "trip_count": int(r.trip_count),
        }
        for r in top_zones.itertuples(index=False)
    ]

    best = min(demand_metrics, key=lambda r: r["mae"])
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "name": DATASET_NAME,
            "source_page": TLC_PAGE,
            "citation": DATASET_CITATION,
            "license": DATASET_LICENSE,
            "sample_months": list(SAMPLE_MONTHS),
            "n_clean_trips": int(len(clean)),
            "n_pickup_zones": int(clean["PULocationID"].nunique()),
            "date_min": str(clean["tpep_pickup_datetime"].min()),
            "date_max": str(clean["tpep_pickup_datetime"].max()),
            "total_revenue_usd": float(clean["total_amount"].sum()),
            "mean_fare_usd": float(clean["fare_amount"].mean()),
        },
        "eda": {
            "n_citywide_hours": int(len(city_hourly)),
            "n_zone_hour_rows": int(len(zone_hourly)),
            "mean_trips_per_hour": float(city_hourly["trip_count"].mean()),
            "median_trips_per_hour": float(city_hourly["trip_count"].median()),
            "mean_revenue_per_hour_usd": float(city_hourly["revenue"].mean()),
            "trips_by_hour_of_day_mean": {str(k): v for k, v in by_hour.items()},
            "trips_by_day_of_week_mean": {str(k): v for k, v in by_dow.items()},
            "top_pickup_zones": top_zones_list,
        },
        "modeling": {
            "target": "citywide_hourly_trip_count",
            "hold_out_days": HOLD_OUT_DAYS,
            "cutoff": str(bundle.cutoff),
            "n_train_hours": int(len(bundle.train)),
            "n_test_hours": int(len(bundle.test)),
            "feature_cols": bundle.feature_cols,
            "demand_regression": demand_metrics,
            "best_model_by_mae": best["model"],
            "best_mae": best["mae"],
        },
        "notes": [
            "Metrics from a real local run on NYC TLC yellow trip parquet (sample months only).",
            "Temporal hold-out: last HOLD_OUT_DAYS; lag features use only past hours.",
            "Seasonal naive uses hour-of-week means fit on the train window only.",
            "No invented business outcomes; figures are reproducible via scripts/run_all.sh.",
        ],
    }

    METRICS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[pipeline] wrote {METRICS_JSON}")
    _print_summary(payload)
    return payload


def _print_summary(payload: dict) -> None:
    print("\n=== Hourly demand regression (test hold-out) ===")
    for row in payload["modeling"]["demand_regression"]:
        mape = row.get("mape")
        mape_s = f"{mape:.3f}" if mape is not None else "n/a"
        print(
            f"  {row['model']:32s}  MAE={row['mae']:.1f}  "
            f"RMSE={row['rmse']:.1f}  MAPE={mape_s}"
        )
    print(f"Best by MAE: {payload['modeling']['best_model_by_mae']}")


if __name__ == "__main__":
    run()
