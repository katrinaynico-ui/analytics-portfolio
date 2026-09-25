"""End-to-end local pipeline: load → clean → RFM → cohorts → models → metrics."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.clean import clean_transactions, save_clean
from src.cohorts import run_cohort_sql, save_cohorts
from src.config import (
    CUSTOMER_FEATURES_PARQUET,
    DATA_PROCESSED,
    DATASET_CITATION,
    DATASET_DOI,
    DATASET_LICENSE,
    HOLD_OUT_DAYS,
    METRICS_JSON,
    REPORTS,
)
from src.data_load import load_raw
from src.models import build_temporal_features, evaluate_classification, evaluate_regression
from src.rfm import compute_rfm, save_rfm


def run() -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    raw = load_raw()
    clean = clean_transactions(raw)
    save_clean(clean)

    rfm = compute_rfm(clean)
    save_rfm(rfm)

    cohorts = run_cohort_sql(clean)
    save_cohorts(cohorts)

    bundle = build_temporal_features(clean)
    bundle.feature_matrix.to_parquet(CUSTOMER_FEATURES_PARQUET)
    print(f"[pipeline] wrote {CUSTOMER_FEATURES_PARQUET}")

    class_metrics = evaluate_classification(bundle)
    reg_metrics = evaluate_regression(bundle)

    # Cohort snapshot: month-0 and month-1 average retention (real numbers only)
    m0 = cohorts.loc[cohorts["month_offset"] == 0, "retention_rate"]
    m1 = cohorts.loc[cohorts["month_offset"] == 1, "retention_rate"]
    m3 = cohorts.loc[cohorts["month_offset"] == 3, "retention_rate"]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "name": "UCI Online Retail",
            "doi": DATASET_DOI,
            "citation": DATASET_CITATION,
            "license": DATASET_LICENSE,
            "n_clean_rows": int(len(clean)),
            "n_customers": int(clean["CustomerID"].nunique()),
            "date_min": str(clean["InvoiceDate"].min()),
            "date_max": str(clean["InvoiceDate"].max()),
            "total_revenue": float(clean["line_revenue"].sum()),
        },
        "rfm": {
            "n_customers": int(len(rfm)),
            "segment_counts": rfm["segment"].value_counts().to_dict(),
            "monetary_median": float(rfm["Monetary"].median()),
            "frequency_median": float(rfm["Frequency"].median()),
            "recency_median_days": float(rfm["Recency"].median()),
        },
        "cohorts": {
            "n_cohort_months": int(cohorts["cohort_month"].nunique()),
            "avg_retention_month_0": float(m0.mean()) if len(m0) else None,
            "avg_retention_month_1": float(m1.mean()) if len(m1) else None,
            "avg_retention_month_3": float(m3.mean()) if len(m3) else None,
        },
        "modeling": {
            "hold_out_days": HOLD_OUT_DAYS,
            "cutoff": str(bundle.cutoff),
            "holdout_end": str(bundle.holdout_end),
            "n_customers_modeled": int(len(bundle.feature_matrix)),
            "repurchase_rate": float(bundle.y_class.mean()),
            "classification": class_metrics,
            "regression": reg_metrics,
        },
        "notes": [
            "Metrics from a real local run on the UCI Online Retail file.",
            "Temporal split: features before cutoff; labels in the following hold-out window.",
            "No invented business outcomes; figures are reproducible via scripts/run_all.sh.",
        ],
    }

    METRICS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[pipeline] wrote {METRICS_JSON}")
    _print_summary(payload)
    return payload


def _print_summary(payload: dict) -> None:
    print("\n=== Classification (repurchase) ===")
    for row in payload["modeling"]["classification"]:
        print(
            f"  {row['model']:24s}  ROC-AUC={row.get('roc_auc')}  "
            f"F1={row['f1']:.3f}  P={row['precision']:.3f}  R={row['recall']:.3f}"
        )
    print("=== Regression (future monetary MAE) ===")
    for row in payload["modeling"]["regression"]:
        print(f"  {row['model']:24s}  MAE={row['mae']:.2f}  RMSE={row['rmse']:.2f}")


if __name__ == "__main__":
    run()
