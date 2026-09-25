"""Imbalanced fraud classifiers with a temporal hold-out (no leakage).

Models
  1) majority_class — always predict legit (shows why accuracy is misleading)
  2) flag_rare_amount — flag tx if Amount >= train quantile at (1 - fraud_rate)
  3) logistic_class_weighted — LogisticRegression(class_weight='balanced')
  4) random_forest_class_weighted — RandomForestClassifier(class_weight='balanced')

Imbalance choice: class_weight='balanced' (inverse frequency weights on train).
Alternative considered: random undersampling of the majority class — rejected here
so the model still sees the full negative distribution; documented in metrics.json.

Split: transactions ordered by Time; last TEST_FRACTION = test. Features are the
PCA components V1–V28 plus Amount. Time is NOT a model feature (ordering only).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import (
    FEATURE_COLS,
    IMBALANCE_STRATEGY,
    RANDOM_STATE,
    TARGET_COL,
    TEST_FRACTION,
    TEST_PREDS_PARQUET,
)


@dataclass
class FraudBundle:
    train: pd.DataFrame
    test: pd.DataFrame
    cutoff_time: float
    feature_cols: list[str]
    fraud_rate_train: float


def temporal_split(df: pd.DataFrame, test_fraction: float = TEST_FRACTION) -> FraudBundle:
    ordered = df.sort_values("Time").reset_index(drop=True)
    cutoff_idx = int(len(ordered) * (1.0 - test_fraction))
    cutoff_idx = max(1, min(cutoff_idx, len(ordered) - 1))
    cutoff_time = float(ordered.loc[cutoff_idx, "Time"])
    train = ordered.iloc[:cutoff_idx].copy()
    test = ordered.iloc[cutoff_idx:].copy()
    n_fraud_train = int(train[TARGET_COL].sum())
    n_fraud_test = int(test[TARGET_COL].sum())
    if n_fraud_train == 0 or n_fraud_test == 0:
        raise ValueError(
            f"Temporal split left a fold with zero frauds "
            f"(train_fraud={n_fraud_train}, test_fraud={n_fraud_test}). "
            "Adjust TEST_FRACTION."
        )
    rate = n_fraud_train / len(train)
    print(
        f"[models] temporal cutoff Time={cutoff_time:.1f}s | "
        f"train={len(train):,} (fraud={n_fraud_train}) | "
        f"test={len(test):,} (fraud={n_fraud_test}) | "
        f"train_fraud_rate={rate:.4%}"
    )
    return FraudBundle(
        train=train,
        test=test,
        cutoff_time=cutoff_time,
        feature_cols=list(FEATURE_COLS),
        fraud_rate_train=rate,
    )


def _metrics_at_threshold(
    y_true: np.ndarray, y_prob: np.ndarray, threshold: float, model: str
) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    # Guard degenerate cases for ROC/PR
    roc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else None
    pr_auc = (
        float(average_precision_score(y_true, y_prob))
        if len(np.unique(y_true)) > 1
        else None
    )
    return {
        "model": model,
        "threshold": float(threshold),
        "roc_auc": roc,
        "pr_auc": pr_auc,
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "support_fraud": int(y_true.sum()),
        "support_legit": int((y_true == 0).sum()),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def _curve_payload(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    fpr, tpr, roc_thr = roc_curve(y_true, y_prob)
    prec, rec, pr_thr = precision_recall_curve(y_true, y_prob)
    # Subsample long curves for JSON size
    def _sub(xs, n=200):
        if len(xs) <= n:
            return [float(x) for x in xs]
        idx = np.linspace(0, len(xs) - 1, n).astype(int)
        return [float(xs[i]) for i in idx]

    return {
        "roc": {"fpr": _sub(fpr), "tpr": _sub(tpr)},
        "pr": {"precision": _sub(prec), "recall": _sub(rec)},
    }


def _majority_probs(n: int) -> np.ndarray:
    return np.zeros(n, dtype=float)


def _flag_rare_amount_probs(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Hard rule → soft score: 1.0 if Amount >= train quantile(1 - fraud_rate) else 0.0."""
    rate = float(train[TARGET_COL].mean())
    q = float(train["Amount"].quantile(1.0 - rate))
    return (test["Amount"].to_numpy(dtype=float) >= q).astype(float)


def evaluate_models(bundle: FraudBundle, default_threshold: float = 0.5) -> tuple[list[dict], pd.DataFrame]:
    X_train = bundle.train[bundle.feature_cols]
    y_train = bundle.train[TARGET_COL].to_numpy()
    X_test = bundle.test[bundle.feature_cols]
    y_test = bundle.test[TARGET_COL].to_numpy()

    # --- Fit ML models ---
    logit = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=RANDOM_STATE,
                    solver="lbfgs",
                ),
            ),
        ]
    )
    logit.fit(X_train, y_train)
    logit_prob = logit.predict_proba(X_test)[:, 1]

    rf = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    rf.fit(X_train, y_train)
    rf_prob = rf.predict_proba(X_test)[:, 1]

    majority_prob = _majority_probs(len(y_test))
    flag_prob = _flag_rare_amount_probs(bundle.train, bundle.test)

    candidates = [
        ("majority_class", majority_prob),
        ("flag_rare_amount", flag_prob),
        ("logistic_class_weighted", logit_prob),
        ("random_forest_class_weighted", rf_prob),
    ]

    rows: list[dict] = []
    pred_cols: dict[str, np.ndarray] = {}
    for name, prob in candidates:
        row = _metrics_at_threshold(y_test, prob, default_threshold, name)
        row["imbalance_strategy"] = (
            IMBALANCE_STRATEGY if "class_weighted" in name else "n/a"
        )
        row["curves"] = _curve_payload(y_test, prob)
        rows.append(row)
        pred_cols[f"prob_{name}"] = prob

    # Persist test frame + probabilities for Streamlit threshold slider
    out = bundle.test[["Time", "Amount", TARGET_COL]].copy()
    for k, v in pred_cols.items():
        out[k] = v
    TEST_PREDS_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(TEST_PREDS_PARQUET, index=False)
    print(f"[models] wrote {TEST_PREDS_PARQUET} ({len(out):,} rows)")

    # Feature importances (RF) for honesty / EDA
    importances = sorted(
        zip(bundle.feature_cols, rf.feature_importances_.tolist()),
        key=lambda t: t[1],
        reverse=True,
    )[:10]

    return rows, pd.DataFrame(importances, columns=["feature", "importance"])
