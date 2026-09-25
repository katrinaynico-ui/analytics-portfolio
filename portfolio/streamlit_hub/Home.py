"""Career DS OS — unified local portfolio hub (Home)."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

HUB = Path(__file__).resolve().parent
if str(HUB) not in sys.path:
    sys.path.insert(0, str(HUB))

from hub_lib import PROFILE, PROJECTS, format_number, load_metrics  # noqa: E402


def home_kpis(pid: str, m: dict) -> list[tuple[str, str]]:
    if pid == "01":
        rf = next(x for x in m["modeling"]["classification"] if x["model"] == "random_forest")
        reg = next(
            x for x in m["modeling"]["regression"] if x["model"] == "random_forest_regressor"
        )
        return [
            ("Clean rows", format_number(m["dataset"]["n_clean_rows"])),
            ("RF ROC-AUC", f"{rf['roc_auc']:.3f}"),
            ("RF MAE (£)", format_number(reg["mae"], 0)),
        ]
    if pid == "02":
        return [
            ("Clean trips", format_number(m["dataset"]["n_clean_trips"])),
            ("Best MAE", format_number(m["modeling"]["best_mae"], 0)),
            ("vs naive MAE", format_number(m["modeling"]["demand_regression"][0]["mae"], 0)),
        ]
    if pid == "03":
        return [
            ("Models", str(len(m["models"]))),
            ("dbt tests", f"{m['dbt_tests']['passed']}/{m['dbt_tests']['total']}"),
            ("Orders", format_number(m["kpis"]["orders"]["n_orders"])),
        ]
    if pid == "04":
        return [
            ("Transactions", format_number(m["dataset"]["n_transactions"])),
            ("Best F1", f"{m['modeling']['best_f1']:.3f}"),
            ("Best ROC-AUC", f"{m['modeling']['best_roc_auc']:.3f}"),
        ]
    return []


st.set_page_config(
    page_title="Career DS OS — Portfolio Hub",
    page_icon="📊",
    layout="wide",
)

st.title("Career DS OS — Portfolio Hub")
st.caption("Local only · not published · metrics from reproducible runs")

st.subheader(PROFILE["name"])
st.write(PROFILE["geo"])
st.write(f"Contact: `{PROFILE['email']}`")

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Verified skills (profile lock)")
    for s in PROFILE["verified_skills"]:
        st.markdown(f"- {s}")
    st.markdown("### Experience on CV")
    st.markdown(f"- {PROFILE['experience']}")
with col2:
    st.markdown("### Not claimed as prior job skills")
    for s in PROFILE["not_confirmed"]:
        st.markdown(f"- {s}")
    st.markdown("### Integrity")
    for s in PROFILE["integrity"]:
        st.markdown(f"- {s}")

st.divider()
st.subheader("Projects (local DONE)")

for p in PROJECTS:
    m = load_metrics(p["slug"], p["metrics_rel"])
    with st.container(border=True):
        st.markdown(f"**{p['id']} · {p['title']}**")
        st.caption(p["stack"])
        st.write(p["short"])
        if m is None:
            st.warning(f"Missing metrics: `projects/{p['slug']}/{p['metrics_rel']}`")
        else:
            kpis = home_kpis(p["id"], m)
            cols = st.columns(max(len(kpis), 1))
            for c, (label, value) in zip(cols, kpis):
                c.metric(label, value)
        st.markdown(
            f"Open the matching page in the sidebar · "
            f"README: `projects/{p['slug']}/README.md`"
        )
