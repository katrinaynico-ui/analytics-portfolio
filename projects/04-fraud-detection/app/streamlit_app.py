"""Interactive Streamlit dashboard for imbalanced fraud classification.

Run:  streamlit run app/streamlit_app.py
Import check (CI / reproduce): does not require the server to start.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import METRICS_JSON, TEST_PREDS_PARQUET  # noqa: E402

MODEL_OPTIONS = [
    ("logistic_class_weighted", "prob_logistic_class_weighted"),
    ("random_forest_class_weighted", "prob_random_forest_class_weighted"),
    ("flag_rare_amount", "prob_flag_rare_amount"),
    ("majority_class", "prob_majority_class"),
]


@st.cache_data(show_spinner=False)
def load_tables():
    preds = pd.read_parquet(TEST_PREDS_PARQUET) if TEST_PREDS_PARQUET.exists() else None
    metrics = None
    if METRICS_JSON.exists():
        metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    return preds, metrics


def _score_at_threshold(y_true: np.ndarray, y_prob: np.ndarray, thr: float) -> dict:
    y_pred = (y_prob >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else None,
        "pr_auc": float(average_precision_score(y_true, y_prob))
        if len(np.unique(y_true)) > 1
        else None,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def main() -> None:
    st.set_page_config(page_title="Fraud Detection (portfolio)", layout="wide")
    st.title("Credit Card Fraud — Imbalanced Classification (portfolio stretch)")
    st.caption(
        "Public ULB/Worldline creditcard.csv · PCA-anonymized features · "
        "local learning project · not production fraud-ML experience"
    )

    preds, metrics = load_tables()
    if preds is None or metrics is None:
        st.warning(
            "Processed data missing. From the project root run: "
            "`bash scripts/run_all.sh`"
        )
        return

    ds = metrics["dataset"]
    mod = metrics["modeling"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions", f"{ds['n_transactions']:,}")
    c2.metric("Frauds", f"{ds['n_fraud']:,}")
    c3.metric("Fraud rate", f"{ds['fraud_rate']:.4%}")
    c4.metric("Best F1 (ML)", f"{mod['best_f1']:.3f}")

    st.sidebar.header("Model & threshold")
    model_labels = [m[0] for m in MODEL_OPTIONS]
    pick = st.sidebar.selectbox("Model", model_labels, index=0)
    prob_col = dict(MODEL_OPTIONS)[pick]
    thr = st.sidebar.slider("Decision threshold", 0.01, 0.99, 0.50, 0.01)

    y_true = preds["Class"].to_numpy()
    y_prob = preds[prob_col].to_numpy()
    scores = _score_at_threshold(y_true, y_prob, thr)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("ROC-AUC", f"{scores['roc_auc']:.4f}" if scores["roc_auc"] else "n/a")
    m2.metric("PR-AUC", f"{scores['pr_auc']:.4f}" if scores["pr_auc"] else "n/a")
    m3.metric("F1", f"{scores['f1']:.4f}")
    m4.metric("Precision", f"{scores['precision']:.4f}")
    m5.metric("Recall", f"{scores['recall']:.4f}")

    # Confusion matrix
    cm = np.array([[scores["tn"], scores["fp"]], [scores["fn"], scores["tp"]]])
    fig_cm = px.imshow(
        cm,
        text_auto=True,
        color_continuous_scale="Blues",
        labels=dict(x="Predicted", y="Actual", color="Count"),
        x=["Legit (0)", "Fraud (1)"],
        y=["Legit (0)", "Fraud (1)"],
        title=f"Confusion matrix — {pick} @ threshold={thr:.2f}",
    )
    st.plotly_chart(fig_cm, use_container_width=True)

    # ROC + PR from stored curves in metrics.json
    curves = metrics["modeling"]["curves"].get(pick, {})
    col_a, col_b = st.columns(2)
    with col_a:
        roc = curves.get("roc", {})
        fig_roc = go.Figure()
        if roc:
            fig_roc.add_trace(
                go.Scatter(x=roc["fpr"], y=roc["tpr"], mode="lines", name=pick)
            )
        fig_roc.add_trace(
            go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="chance", line=dict(dash="dash"))
        )
        fig_roc.update_layout(
            title="ROC curve (from pipeline)",
            xaxis_title="FPR",
            yaxis_title="TPR",
            height=400,
        )
        st.plotly_chart(fig_roc, use_container_width=True)
    with col_b:
        pr = curves.get("pr", {})
        fig_pr = go.Figure()
        if pr:
            fig_pr.add_trace(
                go.Scatter(
                    x=pr["recall"], y=pr["precision"], mode="lines", name=pick
                )
            )
        fig_pr.update_layout(
            title="Precision–Recall curve (from pipeline)",
            xaxis_title="Recall",
            yaxis_title="Precision",
            height=400,
        )
        st.plotly_chart(fig_pr, use_container_width=True)

    st.subheader("Leaderboard @ threshold 0.5 (from metrics.json)")
    board = pd.DataFrame(mod["classification"])[
        ["model", "roc_auc", "pr_auc", "f1", "precision", "recall", "tp", "fp", "fn", "tn"]
    ]
    st.dataframe(board, use_container_width=True)

    with st.expander("Honest notes"):
        for note in metrics.get("notes", []):
            st.write(f"- {note}")
        st.write(f"- PCA note: {ds.get('pca_note', '')}")
        st.write(f"- Imbalance: {mod.get('imbalance_note', '')}")


if __name__ == "__main__":
    main()
