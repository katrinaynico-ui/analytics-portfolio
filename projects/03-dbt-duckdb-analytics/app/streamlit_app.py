"""Thin Streamlit dashboard reading dbt marts from the local DuckDB warehouse.

Run:  streamlit run app/streamlit_app.py
Import check (CI / reproduce): does not require the server to start.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "data" / "warehouse" / "analytics.duckdb"
METRICS_JSON = ROOT / "reports" / "metrics.json"


def _find_relation(con: duckdb.DuckDBPyConnection, name: str) -> str | None:
    rows = con.execute(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE lower(table_name) = lower(?)
        """,
        [name],
    ).fetchall()
    if not rows:
        return None
    schema, table = rows[0]
    return f'"{schema}"."{table}"'


@st.cache_data(show_spinner=False)
def load_tables():
    metrics = None
    if METRICS_JSON.exists():
        metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    if not WAREHOUSE.exists():
        return None, None, None, metrics

    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    try:
        daily_rel = _find_relation(con, "mart_daily_revenue")
        rfm_rel = _find_relation(con, "mart_rfm")
        fct_rel = _find_relation(con, "fct_orders")
        daily = con.execute(f"SELECT * FROM {daily_rel} ORDER BY 1").df() if daily_rel else None
        rfm = con.execute(f"SELECT * FROM {rfm_rel}").df() if rfm_rel else None
        fct = con.execute(f"SELECT * FROM {fct_rel}").df() if fct_rel else None
    finally:
        con.close()
    return daily, rfm, fct, metrics


def main() -> None:
    st.set_page_config(page_title="Retail dbt Marts", layout="wide")
    st.title("Online Retail — dbt + DuckDB marts (portfolio)")
    st.caption(
        "UCI Online Retail seed via project 01 parquet · dbt staging→marts · "
        "local portfolio project · not a client engagement"
    )

    daily, rfm, fct, metrics = load_tables()
    if daily is None or metrics is None:
        st.warning(
            "Warehouse / metrics missing. From the project root run: "
            "`bash scripts/run_all.sh`"
        )
        return

    kpis = metrics.get("kpis", {})
    orders = kpis.get("orders", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orders (fct)", f"{orders.get('n_orders', 0):,}")
    c2.metric("Customers (dim)", f"{kpis.get('n_customers_dim', 0):,}")
    c3.metric("Total revenue (GBP)", f"{orders.get('total_revenue', 0):,.0f}")
    c4.metric(
        "dbt tests passed",
        f"{metrics.get('dbt_tests', {}).get('passed', 0)}/"
        f"{metrics.get('dbt_tests', {}).get('total', 0)}",
    )

    tab_rev, tab_rfm, tab_meta = st.tabs(["Daily revenue", "RFM segments", "Pipeline meta"])

    with tab_rev:
        if daily is None or daily.empty:
            st.info("mart_daily_revenue missing")
        else:
            fig = px.line(
                daily,
                x="revenue_date",
                y="daily_revenue",
                title="Daily revenue (GBP)",
            )
            st.plotly_chart(fig, use_container_width=True)
            left, right = st.columns(2)
            fig_o = px.bar(
                daily.tail(60),
                x="revenue_date",
                y="n_orders",
                title="Orders / day (last 60 days in series)",
            )
            left.plotly_chart(fig_o, use_container_width=True)
            fig_c = px.bar(
                daily.tail(60),
                x="revenue_date",
                y="n_customers",
                title="Active customers / day (last 60)",
            )
            right.plotly_chart(fig_c, use_container_width=True)
            st.dataframe(daily.tail(30), use_container_width=True)

    with tab_rfm:
        if rfm is None or rfm.empty:
            st.info("mart_rfm missing")
        else:
            seg = (
                rfm.groupby("segment", as_index=False)
                .agg(n_customers=("customer_id", "count"), monetary=("monetary", "sum"))
                .sort_values("n_customers", ascending=False)
            )
            fig = px.bar(
                seg, x="segment", y="n_customers", title="Customers by RFM segment"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(seg, use_container_width=True)
            st.caption(
                "Segments are rule-based from dbt SQL (ntile RFM scores), "
                "recomputed in this project — not copied as ground truth from ML."
            )

    with tab_meta:
        st.subheader("Models built")
        st.write(metrics.get("models", []))
        st.subheader("Row counts")
        st.json(metrics.get("row_counts", {}))
        st.subheader("dbt tests")
        st.json(metrics.get("dbt_tests", {}))
        st.caption(metrics.get("framing", ""))


if __name__ == "__main__":
    main()
