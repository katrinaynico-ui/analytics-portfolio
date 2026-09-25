"""Competing hourly demand forecasts with a strict temporal hold-out.

Target: citywide trip_count per hour.

Approaches
  1) Seasonal naive — hour-of-week mean from the TRAIN window only
     (same Mon 09:00 → average of all Mon 09:00 in train).
  2) Ridge regression — calendar + backward-looking lag features.
  3) Random Forest regressor — same feature set.

Leakage control
  - Hold-out = last HOLD_OUT_DAYS of the sample (time-ordered).
  - Lag / rolling features at hour t use only values at t-k (past).
  - Seasonal baseline parameters fit on train only; applied to test.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.config import FEATURES_PARQUET, HOLD_OUT_DAYS, RANDOM_STATE

FEATURE_COLS = [
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "lag_1h",
    "lag_24h",
    "lag_168h",
    "roll_mean_24h",
]


@dataclass
class DemandBundle:
    frame: pd.DataFrame
    train: pd.DataFrame
    test: pd.DataFrame
    cutoff: pd.Timestamp
    feature_cols: list[str]


def build_hourly_features(city: pd.DataFrame) -> pd.DataFrame:
    """Add backward-looking lags on a complete hourly index (fill missing hours with 0)."""
    s = city.set_index("pickup_hour").sort_index()
    full_idx = pd.date_range(s.index.min(), s.index.max(), freq="h")
    s = s.reindex(full_idx)
    s["trip_count"] = s["trip_count"].fillna(0)
    s["revenue"] = s["revenue"].fillna(0)
    s["hour_of_day"] = s.index.hour
    s["day_of_week"] = s.index.dayofweek
    s["is_weekend"] = s["day_of_week"].isin([5, 6]).astype(int)

    s["lag_1h"] = s["trip_count"].shift(1)
    s["lag_24h"] = s["trip_count"].shift(24)
    s["lag_168h"] = s["trip_count"].shift(168)
    # Shifted rolling mean so the window ends at t-1 (no same-hour leakage)
    s["roll_mean_24h"] = s["trip_count"].shift(1).rolling(24, min_periods=12).mean()

    out = s.reset_index().rename(columns={"index": "pickup_hour"})
    # Drop early rows without enough lag history (need 168h)
    out = out.dropna(subset=FEATURE_COLS).reset_index(drop=True)
    print(f"[models] feature rows after lag warmup: {len(out):,}")
    return out


def temporal_split(features: pd.DataFrame, hold_out_days: int = HOLD_OUT_DAYS) -> DemandBundle:
    tmax = features["pickup_hour"].max()
    cutoff = tmax - pd.Timedelta(days=hold_out_days) + pd.Timedelta(hours=1)
    # test = [cutoff, tmax]
    train = features[features["pickup_hour"] < cutoff].copy()
    test = features[features["pickup_hour"] >= cutoff].copy()
    if train.empty or test.empty:
        raise ValueError(
            f"Bad split: train={len(train)} test={len(test)} cutoff={cutoff}"
        )
    print(
        f"[models] cutoff={cutoff} | train_hours={len(train):,} | "
        f"test_hours={len(test):,} | hold_out_days={hold_out_days}"
    )
    return DemandBundle(
        frame=features,
        train=train,
        test=test,
        cutoff=cutoff,
        feature_cols=FEATURE_COLS,
    )


def _seasonal_naive_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Hour-of-week mean demand from train (hour_of_day × day_of_week)."""
    key = ["hour_of_day", "day_of_week"]
    means = train.groupby(key)["trip_count"].mean()
    global_mean = float(train["trip_count"].mean())
    keyed = list(zip(test["hour_of_day"], test["day_of_week"]))
    preds = np.array([means.get(k, global_mean) for k in keyed], dtype=float)
    return preds


def evaluate_demand(bundle: DemandBundle) -> list[dict]:
    X_train = bundle.train[bundle.feature_cols]
    y_train = bundle.train["trip_count"].to_numpy(dtype=float)
    X_test = bundle.test[bundle.feature_cols]
    y_test = bundle.test["trip_count"].to_numpy(dtype=float)

    results: list[dict] = []

    # 1) Seasonal naive
    naive_pred = _seasonal_naive_predict(bundle.train, bundle.test)
    results.append(_reg_metrics("seasonal_naive_hourofweek", y_test, naive_pred))

    # 2) Ridge
    ridge = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("reg", Ridge(alpha=1.0, random_state=RANDOM_STATE)),
        ]
    )
    ridge.fit(X_train, y_train)
    results.append(_reg_metrics("ridge_regression", y_test, ridge.predict(X_test)))

    # 3) Random Forest
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=5,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    results.append(
        _reg_metrics("random_forest_regressor", y_test, rf.predict(X_test))
    )

    return results


def save_features(features: pd.DataFrame) -> None:
    FEATURES_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(FEATURES_PARQUET, index=False)
    print(f"[models] wrote {FEATURES_PARQUET}")


def _reg_metrics(name: str, y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    # MAPE guarded against zeros (hours with 0 trips are rare citywide but possible)
    nonzero = y_true > 0
    mape = (
        float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])))
        if nonzero.any()
        else None
    )
    return {
        "model": name,
        "task": "hourly_citywide_trip_count",
        "n_test": int(len(y_true)),
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "y_mean": float(y_true.mean()),
        "y_median": float(np.median(y_true)),
        "y_std": float(y_true.std()),
    }
