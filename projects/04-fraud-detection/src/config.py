"""Paths and analysis constants for credit-card fraud classification (portfolio)."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS = PROJECT_ROOT / "reports"
SQL_DIR = PROJECT_ROOT / "sql"

# Public mirrors of the classic ULB / Worldline credit-card fraud CSV (no Kaggle auth).
# Primary: TensorFlow public dataset bucket (same md5 as widely cited creditcard.csv).
# Fallback: Zenodo CC BY 4.0 deposit mirroring the Kaggle file.
DOWNLOAD_URLS = (
    "https://storage.googleapis.com/download.tensorflow.org/data/creditcard.csv",
    "https://zenodo.org/records/7395559/files/creditcard.csv?download=1",
)
RAW_CSV = DATA_RAW / "creditcard.csv"
# Expect ~150MB; reject tiny / HTML error pages.
MIN_RAW_BYTES = 50_000_000

CLEAN_PARQUET = DATA_PROCESSED / "transactions_clean.parquet"
TEST_PREDS_PARQUET = DATA_PROCESSED / "test_predictions.parquet"
METRICS_JSON = REPORTS / "metrics.json"

DATASET_NAME = "Credit Card Fraud Detection (ULB / Worldline, Sep 2013)"
DATASET_PAGE = "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud"
OPENML_PAGE = "https://www.openml.org/d/1597"
ZENODO_DOI = "https://doi.org/10.5281/zenodo.7395559"
TF_MIRROR = DOWNLOAD_URLS[0]
DATASET_CITATION = (
    "Dal Pozzolo, A., Caelen, O., Johnson, R. A., & Bontempi, G. (2015). "
    "Calibrating Probability with Undersampling for Unbalanced Classification. "
    "IEEE Symposium on Computational Intelligence and Data Mining. "
    "Dataset: Credit Card Fraud Detection (Worldline / ULB MLG). "
    f"Kaggle: {DATASET_PAGE} · OpenML: {OPENML_PAGE} · "
    f"public CSV mirror (TensorFlow): {TF_MIRROR} · Zenodo: {ZENODO_DOI}"
)
DATASET_LICENSE = (
    "Public research release (ULB / Worldline via Kaggle & OpenML); "
    "Zenodo mirror CC BY 4.0 (10.5281/zenodo.7395559). "
    "Features V1–V28 are PCA-anonymized; only Time and Amount are raw."
)

# Temporal hold-out: last TEST_FRACTION of transactions by Time (seconds from t0).
# Avoids random leakage of near-simultaneous transactions across splits.
TEST_FRACTION = 0.20
RANDOM_STATE = 42

# Modeling: class_weight='balanced' on train (documented alternative: undersample).
# We keep all majority-class rows so the model sees the full negative distribution.
IMBALANCE_STRATEGY = "class_weight_balanced"
FEATURE_COLS = [f"V{i}" for i in range(1, 29)] + ["Amount"]
# Time is used only for ordering the temporal split, not as a model feature.
TARGET_COL = "Class"
