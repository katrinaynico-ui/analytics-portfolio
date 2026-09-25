"""Paths and analysis constants for the Online Retail RFM project."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS = PROJECT_ROOT / "reports"
SQL_DIR = PROJECT_ROOT / "sql"

RAW_XLSX = DATA_RAW / "Online_Retail.xlsx"
CLEAN_PARQUET = DATA_PROCESSED / "transactions_clean.parquet"
CUSTOMER_FEATURES_PARQUET = DATA_PROCESSED / "customer_features.parquet"
RFM_PARQUET = DATA_PROCESSED / "rfm_segments.parquet"
COHORT_PARQUET = DATA_PROCESSED / "cohort_retention.parquet"
METRICS_JSON = REPORTS / "metrics.json"

# UCI Online Retail — Chen, Daqing (2015). CC BY 4.0.
DATASET_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/"
    "Online%20Retail.xlsx"
)
DATASET_DOI = "https://doi.org/10.24432/C5BW33"
DATASET_CITATION = (
    "Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. "
    "https://doi.org/10.24432/C5BW33"
)
DATASET_LICENSE = "Creative Commons Attribution 4.0 International (CC BY 4.0)"

# Temporal split: use early period for features, late period for labels.
# Avoids target leakage from using full-period Monetary as both feature and label.
HOLD_OUT_DAYS = 90
RANDOM_STATE = 42
