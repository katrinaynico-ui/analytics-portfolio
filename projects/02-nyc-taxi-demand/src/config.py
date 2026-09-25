"""Paths and analysis constants for NYC TLC yellow taxi demand forecasting."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS = PROJECT_ROOT / "reports"
SQL_DIR = PROJECT_ROOT / "sql"

# Months included in this local portfolio run (keep download under ~200MB).
# Jan ~50MB + Feb ~50MB ≈ 100MB of yellow trip parquet + tiny zone lookup.
SAMPLE_MONTHS = ("2024-01", "2024-02")

TLC_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
TLC_PAGE = "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page"

ZONE_LOOKUP_CSV = DATA_RAW / "taxi_zone_lookup.csv"
CLEAN_PARQUET = DATA_PROCESSED / "trips_clean.parquet"
HOURLY_CITY_PARQUET = DATA_PROCESSED / "hourly_citywide.parquet"
HOURLY_ZONE_PARQUET = DATA_PROCESSED / "hourly_by_zone.parquet"
FEATURES_PARQUET = DATA_PROCESSED / "hourly_features.parquet"
METRICS_JSON = REPORTS / "metrics.json"

DATASET_NAME = "NYC TLC Yellow Taxi Trip Records"
DATASET_CITATION = (
    "NYC Taxi & Limousine Commission. TLC Trip Record Data. "
    f"{TLC_PAGE}"
)
# NYC Open Data / TLC public release — free for public use; attribute TLC.
DATASET_LICENSE = (
    "NYC Open Data / TLC public trip records (see TLC Trip Record Data page Terms)"
)

# Temporal hold-out: last N days of the sample used only as test labels.
# Features for hour t use only information available before t (lags / calendar).
HOLD_OUT_DAYS = 7
RANDOM_STATE = 42

# Columns kept after clean (subset of TLC yellow schema).
KEEP_COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "PULocationID",
    "DOLocationID",
    "RatecodeID",
    "payment_type",
    "fare_amount",
    "tip_amount",
    "tolls_amount",
    "total_amount",
]
