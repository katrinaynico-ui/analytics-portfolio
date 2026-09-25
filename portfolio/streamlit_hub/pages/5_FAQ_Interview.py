"""Static FAQ / interview framing — RAG-less, honest."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

HUB = Path(__file__).resolve().parents[1]
if str(HUB) not in sys.path:
    sys.path.insert(0, str(HUB))

from hub_lib import PROFILE, PROJECTS

st.set_page_config(page_title="FAQ / Interview", page_icon="💬", layout="wide")
st.title("FAQ & interview framing")
st.caption("Static bullets — no RAG. Prefer honesty over polish.")

st.markdown("### Who are you targeting?")
st.markdown(
    f"- **{PROFILE['name']}** — {PROFILE['geo']}\n"
    "- Fit bias: **Analytics Engineer / Data Analyst** (SQL + dbt + warehouse) over ML/DS titles "
    "until Python/ML are confirmed as prior job skills.\n"
    f"- CV experience: {PROFILE['experience']}."
)

st.markdown("### What are these four projects?")
st.markdown(
    "Local portfolio practice on **public datasets**. They demonstrate reproducible SQL/Python/dbt "
    "pipelines and honest metrics. They are **not** client engagements and **not** claims of prior "
    "production ML, fraud ops, or NYC taxi operations experience."
)

st.markdown("### How should I talk about metrics?")
st.markdown(
    "- Quote numbers only from each project's `reports/metrics.json` (or this hub's loaded copy).\n"
    "- Say the hold-out / split method (temporal) when asked about leakage.\n"
    "- For fraud: lead with imbalance (~0.17%), F1 / PR-AUC / recall — not accuracy.\n"
    "- For dbt: emphasize tests, layers, and that DuckDB stands in for BQ/Snowflake patterns."
)

st.markdown("### Per-project interview bullets")
for p in PROJECTS:
    with st.expander(f"{p['id']} · {p['title']}"):
        for b in p["interview_bullets"]:
            st.markdown(f"- {b}")

st.markdown("### What not to say")
for s in PROFILE["not_confirmed"]:
    st.markdown(f"- Do not invent: {s}")
for s in PROFILE["integrity"]:
    st.markdown(f"- {s}")
