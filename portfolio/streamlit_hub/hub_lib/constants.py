"""Profile lock + project catalog (honest, no invented XP)."""

from __future__ import annotations

from pathlib import Path

# Relative to career-ds-os/projects/
PROJECTS: list[dict] = [
    {
        "id": "01",
        "slug": "01-online-retail-rfm",
        "title": "Online Retail — RFM, Cohorts & Retention",
        "stack": "DuckDB SQL · pandas · sklearn · Streamlit",
        "short": "RFM segments, cohort retention, repurchase + future-monetary models on UCI Online Retail.",
        "metrics_rel": "reports/metrics.json",
        "run": "bash scripts/run_all.sh",
        "app": "streamlit run app/streamlit_app.py",
        "interview_bullets": [
            "Public UCI Online Retail (CC BY 4.0) — cleaned ~398k invoice lines, ~4.3k customers.",
            "RFM with transparent rule segments (not black-box clustering) + DuckDB cohort SQL.",
            "Temporal split: features before cutoff; 90-day hold-out labels (repurchase + future spend).",
            "Competing models: rule / logistic / RF for repurchase; mean / ridge / RF for monetary MAE.",
            "Portfolio practice — not a client engagement; no claim of prior production ML XP.",
        ],
    },
    {
        "id": "02",
        "slug": "02-nyc-taxi-demand",
        "title": "NYC Yellow Taxi — Hourly Demand Forecasting",
        "stack": "DuckDB SQL · forecasting · Streamlit",
        "short": "TLC yellow trips EDA + citywide hourly demand vs seasonal naive / Ridge / RF.",
        "metrics_rel": "reports/metrics.json",
        "run": "bash scripts/run_all.sh",
        "app": "streamlit run app/streamlit_app.py",
        "interview_bullets": [
            "Public NYC TLC yellow parquet (sample months 2024-01/02) — ~5.8M clean trips.",
            "DuckDB zone×hour aggregates joined to taxi zone lookup; citywide hourly series.",
            "Temporal hold-out last 7 days; lag/rolling features use only past hours (no leakage).",
            "Seasonal naive (hour-of-week, train-only) vs Ridge vs Random Forest — report MAE/RMSE/MAPE.",
            "Portfolio practice — not operating NYC taxi systems.",
        ],
    },
    {
        "id": "03",
        "slug": "03-dbt-duckdb-analytics",
        "title": "dbt + DuckDB — Retail Analytics Warehouse",
        "stack": "dbt-duckdb · staging → intermediate → marts · tests",
        "short": "Dimensional modeling on UCI Retail seed from project 01; schema tests on marts.",
        "metrics_rel": "reports/metrics.json",
        "run": "bash scripts/run_all.sh",
        "app": "streamlit run app/streamlit_app.py",
        "interview_bullets": [
            "Seed reuses cleaned parquet from project 01 (landing-zone style) into DuckDB.",
            "Layers: staging → intermediate → marts (fct_orders, dim_customers, daily revenue, RFM).",
            "dbt tests (unique / not_null / relationships / accepted_values) — last run 26/26 pass.",
            "DuckDB is a local stand-in for cloud WH patterns (BQ/Snowflake); this repo alone ≠ cloud prod XP.",
            "RFM in dbt may differ slightly from project 01 pandas RFM (tie-break / as-of) — called out honestly.",
        ],
    },
    {
        "id": "04",
        "slug": "04-fraud-detection",
        "title": "Credit Card Fraud — Imbalanced Classification (stretch)",
        "stack": "DuckDB SQL · sklearn class_weight · Streamlit",
        "short": "ULB/Worldline public card fraud set; F1 / ROC-AUC / PR-AUC under severe imbalance.",
        "metrics_rel": "reports/metrics.json",
        "run": "bash scripts/run_all.sh",
        "app": "streamlit run app/streamlit_app.py",
        "interview_bullets": [
            "Public research CSV (~0.17% fraud). Accuracy alone is a trap — emphasize PR-AUC / F1 / recall.",
            "V1–V28 are PCA-anonymized; only Time + Amount are clear — limited interpretability, stated up front.",
            "Temporal split by Time; class_weight='balanced' on logistic + RF (no majority undersampling).",
            "Baselines: majority class + rare-Amount rule show why naive approaches fail.",
            "Stretch / learning project — NOT a claim of production fraud-ML or AML experience.",
        ],
    },
]

PROFILE = {
    "name": "Nicolás Beneito Colomina",
    "email": "nicolas.beneito.work@gmail.com",
    "geo": "Zurich timezone · Switzerland work OK · Remote English",
    "verified_skills": [
        "SQL — advanced, 5+ years (user-declared)",
        "dbt + cloud warehouse (BigQuery / Snowflake)",
        "English — very good",
    ],
    "experience": "Typeform — Data Analyst / Analytics (~3–4 years; calendar dates TBD)",
    "not_confirmed": [
        "Python / pandas as prior job skill",
        "Sheets / BI tool years",
        "Git / ML production experience",
        "GitHub / LinkedIn on CV (none yet)",
    ],
    "integrity": [
        "No invented experience, titles, or certifications",
        "Public datasets with citation + license",
        "Metrics from reproducible local runs only (reports/metrics.json)",
        "These projects build verifiable assets — they do not claim past production ML/DS XP",
        "Do not publish / deploy without explicit user confirmation",
    ],
}


def project_dir(career_root: Path, slug: str) -> Path:
    return career_root / "projects" / slug
