"""Interactive Streamlit dashboard for Online Retail RFM analytics.

Run:  streamlit run app/streamlit_app.py
Import check (CI / reproduce):  python -c "import app.streamlit_app"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    CLEAN_PARQUET,
    COHORT_PARQUET,
    METRICS_JSON,
    RFM_PARQUET,
)


@st.cache_data(show_spinner=False)
def load_tables():
    rfm = pd.read_parquet(RFM_PARQUET) if RFM_PARQUET.exists() else None
    cohorts = pd.read_parquet(COHORT_PARQUET) if COHORT_PARQUET.exists() else None
    clean = pd.read_parquet(CLEAN_PARQUET) if CLEAN_PARQUET.exists() else None
    metrics = None
    if METRICS_JSON.exists():
        metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    return rfm, cohorts, clean, metrics


def main() -> None:
    st.set_page_config(page_title="Online Retail RFM", layout="wide")
    st.title("Online Retail — RFM, Cohorts & Retention Models")
    st.caption(
        "UCI Online Retail (Chen, 2015) · local portfolio project · "
        "not a client engagement"
    )

    rfm, cohorts, clean, metrics = load_tables()
    if rfm is None or metrics is None:
        st.warning(
            "Processed data missing. From the project root run: "
            "`bash scripts/run_all.sh`"
        )
        return

    ds = metrics["dataset"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers", f"{ds['n_customers']:,}")
    c2.metric("Clean rows", f"{ds['n_clean_rows']:,}")
    c3.metric("Revenue (GBP)", f"{ds['total_revenue']:,.0f}")
    c4.metric(
        "Date span",
        f"{ds['date_min'][:10]} → {ds['date_max'][:10]}",
    )

    st.sidebar.header("Filters")
    segments = sorted(rfm["segment"].unique())
    pick_seg = st.sidebar.multiselect("RFM segments", segments, default=segments)
    r_max = st.sidebar.slider("Max Recency (days)", 0, int(rfm["Recency"].max()), int(rfm["Recency"].max()))
    filtered = rfm[rfm["segment"].isin(pick_seg) & (rfm["Recency"] <= r_max)]

    tab_rfm, tab_cohort, tab_models = st.tabs(["RFM segments", "Cohort retention", "Model metrics"])

    with tab_rfm:
        left, right = st.columns(2)
        seg_counts = filtered["segment"].value_counts().reset_index()
        seg_counts.columns = ["segment", "customers"]
        fig_seg = px.bar(seg_counts, x="segment", y="customers", title="Customers by segment")
        left.plotly_chart(fig_seg, use_container_width=True)

        fig_sc = px.scatter(
            filtered.sample(min(2000, len(filtered)), random_state=42),
            x="Frequency",
            y="Monetary",
            color="segment",
            size="Recency",
            hover_data=["CustomerID", "RFM_score"],
            title="Frequency vs Monetary (sample)",
            log_y=True,
        )
        right.plotly_chart(fig_sc, use_container_width=True)
        st.dataframe(
            filtered.sort_values("Monetary", ascending=False).head(50),
            use_container_width=True,
        )

    with tab_cohort:
        if cohorts is None or cohorts.empty:
            st.info("Cohort table missing.")
        else:
            heat = cohorts.pivot_table(
                index="cohort_month",
                columns="month_offset",
                values="retention_rate",
                aggfunc="mean",
            )
            # Limit columns for readability
            cols = [c for c in heat.columns if c <= 12]
            heat = heat[cols]
            fig_h = px.imshow(
                heat,
                aspect="auto",
                color_continuous_scale="Blues",
                title="Monthly cohort retention rate",
                labels=dict(color="retention"),
            )
            st.plotly_chart(fig_h, use_container_width=True)
            st.caption(
                f"Avg month-1 retention: "
                f"{metrics['cohorts'].get('avg_retention_month_1')}"
            )

    with tab_models:
        st.subheader("Repurchase classification (hold-out window)")
        clf = pd.DataFrame(metrics["modeling"]["classification"])
        st.dataframe(clf, use_container_width=True)
        fig_auc = px.bar(
            clf,
            x="model",
            y="roc_auc",
            title="ROC-AUC by model",
            text="roc_auc",
        )
        st.plotly_chart(fig_auc, use_container_width=True)

        st.subheader("Future monetary regression (CLV proxy)")
        reg = pd.DataFrame(metrics["modeling"]["regression"])
        st.dataframe(reg, use_container_width=True)
        fig_mae = px.bar(reg, x="model", y="mae", title="MAE by model (lower better)", text="mae")
        st.plotly_chart(fig_mae, use_container_width=True)

        st.info(
            f"Cutoff={metrics['modeling']['cutoff'][:10]} · "
            f"hold-out={metrics['modeling']['hold_out_days']} days · "
            f"repurchase rate={metrics['modeling']['repurchase_rate']:.3f}"
        )

    if clean is not None:
        st.sidebar.caption(f"Loaded {len(clean):,} clean transactions")


# Allow `python -c "import importlib; importlib.import_module(...)"` without Streamlit server
if __name__ == "__main__":
    main()
