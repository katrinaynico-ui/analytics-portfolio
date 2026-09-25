"""Competing approaches for repurchase (retention) and holdout CLV proxy.

Temporal split (no leakage):
  - Feature window: all purchases BEFORE cutoff
  - Label window: [cutoff, cutoff + HOLD_OUT_DAYS)
  - repurchase = 1 if customer has ≥1 invoice in label window
  - future_monetary = sum revenue in label window (CLV proxy for short horizon)

Approaches
  Classification:
    1) Rule baseline — Recency/Frequency thresholds
    2) Logistic Regression
    3) Random Forest Classifier
  Regression (future monetary):
    1) Mean baseline
    2) Ridge regression
    3) Random Forest Regressor
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import HOLD_OUT_DAYS, RANDOM_STATE


FEATURE_COLS = [
    "Recency",
    "Frequency",
    "Monetary",
    "avg_basket",
    "n_products",
    "tenure_days",
]


@dataclass
class ModelBundle:
    feature_matrix: pd.DataFrame
    y_class: pd.Series
    y_reg: pd.Series
    cutoff: pd.Timestamp
    holdout_end: pd.Timestamp


def build_temporal_features(transactions: pd.DataFrame) -> ModelBundle:
    """Build customer features before cutoff; labels from the following HOLD_OUT_DAYS."""
    tmax = transactions["InvoiceDate"].max()
    cutoff = tmax - pd.Timedelta(days=HOLD_OUT_DAYS)
    holdout_end = tmax + pd.Timedelta(days=1)

    hist = transactions[transactions["InvoiceDate"] < cutoff].copy()
    future = transactions[
        (transactions["InvoiceDate"] >= cutoff) & (transactions["InvoiceDate"] < holdout_end)
    ].copy()

    if hist.empty:
        raise ValueError("History window empty — check HOLD_OUT_DAYS vs dataset span.")

    as_of = cutoff
    feats = hist.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda s: (as_of - s.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("line_revenue", "sum"),
        n_products=("StockCode", "nunique"),
        first_purchase=("InvoiceDate", "min"),
        n_lines=("InvoiceNo", "count"),
    )
    feats["avg_basket"] = feats["Monetary"] / feats["Frequency"].clip(lower=1)
    feats["tenure_days"] = (as_of - feats["first_purchase"]).dt.days
    feats = feats.drop(columns=["first_purchase", "n_lines"])

    future_rev = future.groupby("CustomerID")["line_revenue"].sum().rename("future_monetary")
    future_flag = future.groupby("CustomerID")["InvoiceNo"].nunique().gt(0).astype(int).rename("repurchase")

    # Only customers observed in history (cold-start excluded — honest scope)
    X = feats.join(future_flag, how="left").join(future_rev, how="left")
    X["repurchase"] = X["repurchase"].fillna(0).astype(int)
    X["future_monetary"] = X["future_monetary"].fillna(0.0)

    print(
        f"[models] cutoff={cutoff.date()} holdout_end={holdout_end.date()} | "
        f"customers={len(X):,} | repurchase_rate={X['repurchase'].mean():.3f}"
    )
    return ModelBundle(
        feature_matrix=X,
        y_class=X["repurchase"],
        y_reg=X["future_monetary"],
        cutoff=cutoff,
        holdout_end=holdout_end,
    )


def _rule_predict(X: pd.DataFrame) -> np.ndarray:
    """Transparent baseline: recent + repeat buyers more likely to return."""
    return ((X["Recency"] <= 60) & (X["Frequency"] >= 2)).astype(int).to_numpy()


def _rule_scores(X: pd.DataFrame) -> np.ndarray:
    """Pseudo-probability for ROC: combine inverted recency + log frequency."""
    rec = 1.0 / (1.0 + X["Recency"].to_numpy(dtype=float))
    freq = np.log1p(X["Frequency"].to_numpy(dtype=float))
    raw = 0.6 * rec + 0.4 * (freq / (freq.max() + 1e-9))
    return raw


def evaluate_classification(bundle: ModelBundle) -> list[dict]:
    X = bundle.feature_matrix[FEATURE_COLS]
    y = bundle.y_class
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
    )

    results = []

    # 1) Rules
    pred = _rule_predict(X_test)
    scores = _rule_scores(X_test)
    results.append(_class_metrics("rule_baseline", y_test, pred, scores))

    # 2) Logistic Regression
    logit = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    logit.fit(X_train, y_train)
    pred = logit.predict(X_test)
    scores = logit.predict_proba(X_test)[:, 1]
    results.append(_class_metrics("logistic_regression", y_test, pred, scores))

    # 3) Random Forest
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=10,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    pred = rf.predict(X_test)
    scores = rf.predict_proba(X_test)[:, 1]
    results.append(_class_metrics("random_forest", y_test, pred, scores))

    return results


def evaluate_regression(bundle: ModelBundle) -> list[dict]:
    X = bundle.feature_matrix[FEATURE_COLS]
    y = bundle.y_reg
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE
    )

    results = []

    # 1) Mean baseline
    mean_pred = np.full_like(y_test, fill_value=float(y_train.mean()), dtype=float)
    results.append(_reg_metrics("mean_baseline", y_test, mean_pred))

    # 2) Ridge
    ridge = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("reg", Ridge(alpha=1.0, random_state=RANDOM_STATE)),
        ]
    )
    ridge.fit(X_train, y_train)
    results.append(_reg_metrics("ridge_regression", y_test, ridge.predict(X_test)))

    # 3) RF regressor
    rfr = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=10,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rfr.fit(X_train, y_train)
    results.append(_reg_metrics("random_forest_regressor", y_test, rfr.predict(X_test)))

    return results


def _class_metrics(name: str, y_true, y_pred, y_score) -> dict:
    y_true = np.asarray(y_true)
    out = {
        "model": name,
        "task": "repurchase_classification",
        "n_test": int(len(y_true)),
        "positive_rate_test": float(y_true.mean()),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    # ROC-AUC / AP need both classes present
    if len(np.unique(y_true)) > 1:
        out["roc_auc"] = float(roc_auc_score(y_true, y_score))
        out["average_precision"] = float(average_precision_score(y_true, y_score))
    else:
        out["roc_auc"] = None
        out["average_precision"] = None
    return out


def _reg_metrics(name: str, y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    return {
        "model": name,
        "task": "future_monetary_regression",
        "n_test": int(len(y_true)),
        "mae": mae,
        "rmse": rmse,
        "y_mean": float(y_true.mean()),
        "y_median": float(np.median(y_true)),
    }
