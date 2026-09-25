"""Render a single project page from catalog entry + metrics.json."""

from __future__ import annotations


import streamlit as st

from hub_lib.constants import PROJECTS
from hub_lib.metrics import format_number, load_metrics, metrics_path, projects_root


def get_project(pid: str) -> dict:
    for p in PROJECTS:
        if p["id"] == pid:
            return p
    raise KeyError(pid)


def render_run_instructions(p: dict) -> None:
    root = projects_root() / p["slug"]
    st.markdown("### How to run locally")
    st.code(
        f"cd {root}\n"
        f"# optional: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt\n"
        f"{p['run']}\n"
        f"{p['app']}",
        language="bash",
    )
    st.markdown(f"**Project README:** `{root / 'README.md'}`")
    st.markdown(f"**Metrics source:** `{root / p['metrics_rel']}`")


def render_interview(p: dict) -> None:
    st.markdown("### Explain this in an interview (honest bullets)")
    for b in p["interview_bullets"]:
        st.markdown(f"- {b}")


def render_raw_metrics(m: dict | None, path) -> None:
    with st.expander("Raw metrics.json"):
        if m is None:
            st.error(f"File missing: {path}")
        else:
            st.json(m)


def render_01(m: dict) -> None:
    ds, rfm, mod = m["dataset"], m["rfm"], m["modeling"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clean rows", format_number(ds["n_clean_rows"]))
    c2.metric("Customers", format_number(ds["n_customers"]))
    c3.metric("Total revenue (£)", format_number(ds["total_revenue"], 0))
    c4.metric("Hold-out repurchase rate", f"{mod['repurchase_rate']:.1%}")

    st.markdown("#### RFM segment counts")
    st.dataframe(
        [{"segment": k, "n": v} for k, v in rfm["segment_counts"].items()],
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("#### Repurchase classification")
    st.dataframe(mod["classification"], hide_index=True, use_container_width=True)
    st.markdown("#### Future monetary regression (MAE lower is better)")
    st.dataframe(mod["regression"], hide_index=True, use_container_width=True)


def render_02(m: dict) -> None:
    ds, eda, mod = m["dataset"], m["eda"], m["modeling"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clean trips", format_number(ds["n_clean_trips"]))
    c2.metric("Pickup zones", format_number(ds["n_pickup_zones"]))
    c3.metric("Mean trips/hour", format_number(eda["mean_trips_per_hour"], 0))
    c4.metric("Best MAE (RF)", format_number(mod["best_mae"], 1))

    st.markdown("#### Top pickup zones")
    st.dataframe(eda["top_pickup_zones"], hide_index=True, use_container_width=True)
    st.markdown("#### Demand regression (hold-out)")
    st.dataframe(mod["demand_regression"], hide_index=True, use_container_width=True)


def render_03(m: dict) -> None:
    kpis, tests = m["kpis"], m["dbt_tests"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Models", str(len(m["models"])))
    c2.metric("dbt tests", f"{tests['passed']}/{tests['total']}")
    c3.metric("Orders", format_number(kpis["orders"]["n_orders"]))
    c4.metric("Customers", format_number(kpis["n_customers_dim"]))

    st.markdown("#### Row counts")
    st.dataframe(
        [{"relation": k, "rows": v} for k, v in m["row_counts"].items()],
        hide_index=True,
        use_container_width=True,
    )
    st.markdown("#### RFM segments (dbt SQL)")
    st.dataframe(
        [{"segment": k, "n": v} for k, v in kpis["rfm_segment_counts"].items()],
        hide_index=True,
        use_container_width=True,
    )
    st.info(
        "DuckDB is a local stand-in for cloud warehouse patterns. "
        "RFM here may differ slightly from project 01 pandas RFM."
    )


def render_04(m: dict) -> None:
    ds, mod = m["dataset"], m["modeling"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions", format_number(ds["n_transactions"]))
    c2.metric("Fraud rate", f"{ds['fraud_rate'] * 100:.4f}%")
    c3.metric("Best F1", f"{mod['best_f1']:.3f}")
    c4.metric("Best ROC-AUC", f"{mod['best_roc_auc']:.3f}")

    st.caption(
        "Accuracy alone is misleading at ~0.17% fraud — prefer F1 / PR-AUC / recall."
    )
    # Drop huge curve payloads for the table view
    rows = []
    for row in mod["classification"]:
        rows.append({k: v for k, v in row.items() if k not in ("curves",)})
    st.markdown("#### Classification (threshold 0.5)")
    st.dataframe(rows, hide_index=True, use_container_width=True)
    if mod.get("rf_top_importances"):
        st.markdown("#### RF top importances (PCA features)")
        st.dataframe(mod["rf_top_importances"], hide_index=True, use_container_width=True)


RENDERERS = {
    "01": render_01,
    "02": render_02,
    "03": render_03,
    "04": render_04,
}


def render_project_page(pid: str) -> None:
    p = get_project(pid)
    st.set_page_config(page_title=f"{p['id']} · {p['title']}", page_icon="📁", layout="wide")
    st.title(f"{p['id']} · {p['title']}")
    st.caption(p["stack"])
    st.write(p["short"])

    path = metrics_path(p["slug"], p["metrics_rel"])
    m = load_metrics(p["slug"], p["metrics_rel"])
    if m is None:
        st.error(f"Missing metrics file: `{path}` — run the project pipeline first.")
    else:
        st.success(f"Loaded `{path.name}` · generated_at_utc={m.get('generated_at_utc', 'n/a')}")
        RENDERERS[pid](m)
        if m.get("notes"):
            st.markdown("#### Notes from metrics.json")
            for n in m["notes"]:
                st.markdown(f"- {n}")

    render_run_instructions(p)
    render_interview(p)
    render_raw_metrics(m, path)
