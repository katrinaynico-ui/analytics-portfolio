"""End-to-end local pipeline: load → clean → DuckDB EDA → models → metrics."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.aggregates import run_fraud_eda_sql
from src.clean import clean_transactions, save_clean
from src.config import (
    DATA_PROCESSED,
    DATASET_CITATION,
    DATASET_LICENSE,
    DATASET_NAME,
    DATASET_PAGE,
    FEATURE_COLS,
    IMBALANCE_STRATEGY,
    METRICS_JSON,
    OPENML_PAGE,
    REPORTS,
    TARGET_COL,
    TEST_FRACTION,
    TF_MIRROR,
    ZENODO_DOI,
)
from src.data_load import load_raw
from src.models import evaluate_models, temporal_split


def run() -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    raw = load_raw()
    clean = clean_transactions(raw)
    save_clean(clean)

    eda = run_fraud_eda_sql(clean)
    bundle = temporal_split(clean, test_fraction=TEST_FRACTION)
    model_rows, importances = evaluate_models(bundle)

    # Strip bulky curve arrays from the "leaderboard" copy; keep full in payload.
    leaderboard = []
    for r in model_rows:
        slim = {k: v for k, v in r.items() if k != "curves"}
        leaderboard.append(slim)

    # Best by F1 among probabilistic ML models (exclude trivial baselines for "best")
    ml_only = [r for r in leaderboard if "class_weighted" in r["model"]]
    best_f1 = max(ml_only, key=lambda r: r["f1"])
    best_roc = max(ml_only, key=lambda r: r["roc_auc"] or -1)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "name": DATASET_NAME,
            "source_page_kaggle": DATASET_PAGE,
            "openml": OPENML_PAGE,
            "download_mirror_tensorflow": TF_MIRROR,
            "zenodo_doi": ZENODO_DOI,
            "citation": DATASET_CITATION,
            "license": DATASET_LICENSE,
            "n_transactions": int(len(clean)),
            "n_fraud": int(clean[TARGET_COL].sum()),
            "fraud_rate": float(clean[TARGET_COL].mean()),
            "n_features_used": len(FEATURE_COLS),
            "feature_cols": list(FEATURE_COLS),
            "pca_anonymized": True,
            "pca_note": (
                "V1–V28 are principal components from the original confidential "
                "features; only Time and Amount are provided in clear form. "
                "This limits feature engineering and interpretability — stated honestly."
            ),
            "time_min_s": float(clean["Time"].min()),
            "time_max_s": float(clean["Time"].max()),
        },
        "eda": eda,
        "modeling": {
            "task": "binary_fraud_classification",
            "target": TARGET_COL,
            "split": "temporal_by_Time",
            "test_fraction": TEST_FRACTION,
            "cutoff_time_s": bundle.cutoff_time,
            "n_train": int(len(bundle.train)),
            "n_test": int(len(bundle.test)),
            "n_fraud_train": int(bundle.train[TARGET_COL].sum()),
            "n_fraud_test": int(bundle.test[TARGET_COL].sum()),
            "imbalance_strategy": IMBALANCE_STRATEGY,
            "imbalance_note": (
                "Used sklearn class_weight='balanced' (inverse class frequency) "
                "for logistic regression and random forest. Undersampling the "
                "majority class was considered but not used, to retain the full "
                "negative-class distribution for learning."
            ),
            "default_threshold": 0.5,
            "classification": leaderboard,
            "curves": {r["model"]: r["curves"] for r in model_rows},
            "best_model_by_f1": best_f1["model"],
            "best_f1": best_f1["f1"],
            "best_model_by_roc_auc": best_roc["model"],
            "best_roc_auc": best_roc["roc_auc"],
            "rf_top_importances": [
                {"feature": str(r.feature), "importance": float(r.importance)}
                for r in importances.itertuples(index=False)
            ],
        },
        "notes": [
            "Portfolio learning / stretch project — not a claim of production fraud-ML experience.",
            "Metrics from a real local run on the public creditcard.csv mirror (no Kaggle auth).",
            "Temporal hold-out by Time; model features = V1–V28 + Amount (Time excluded from X).",
            "Report ROC-AUC, PR-AUC, F1, precision, recall; accuracy alone is misleading at ~0.17% fraud.",
            "No invented business outcomes; figures are reproducible via scripts/run_all.sh.",
        ],
    }

    METRICS_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[pipeline] wrote {METRICS_JSON}")
    _print_summary(payload)
    return payload


def _print_summary(payload: dict) -> None:
    print("\n=== Fraud classification (test hold-out, threshold=0.5) ===")
    for row in payload["modeling"]["classification"]:
        roc = row.get("roc_auc")
        pr = row.get("pr_auc")
        roc_s = f"{roc:.4f}" if roc is not None else "n/a"
        pr_s = f"{pr:.4f}" if pr is not None else "n/a"
        print(
            f"  {row['model']:32s}  ROC-AUC={roc_s}  PR-AUC={pr_s}  "
            f"F1={row['f1']:.4f}  P={row['precision']:.4f}  R={row['recall']:.4f}"
        )
    print(
        f"Best by F1: {payload['modeling']['best_model_by_f1']} "
        f"({payload['modeling']['best_f1']:.4f})"
    )
    print(
        f"Best by ROC-AUC: {payload['modeling']['best_model_by_roc_auc']} "
        f"({payload['modeling']['best_roc_auc']:.4f})"
    )


if __name__ == "__main__":
    run()
