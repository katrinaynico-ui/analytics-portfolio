# Nicolás Beneito Colomina — Analytics Portfolio (Public portfolio)

> **ES:** Portafolio público. Demos Streamlit: ejecuta en local (ver cada proyecto).

Zurich timezone · Switzerland work OK · Remote English  
Contact: nicolas.beneito.work@gmail.com

## Objective

Demonstrate **verifiable** analytics / analytics-engineering skills with public datasets, reproducible pipelines, honest metrics, and interactive apps. Portfolio practice projects — not client engagements and not claims of prior production ML experience.

## Verified background (separate from these projects)

- SQL — advanced, 5+ years (user-declared)
- dbt + cloud warehouse (BigQuery / Snowflake)
- English — very good
- Experience: Typeform — Data Analyst / Analytics (~3–4 years; calendar dates TBD)

## Projects

| # | Project | Status | Stack | Live demo |
|---|---|---|---|---|
| 01 | [Online Retail RFM](projects/01-online-retail-rfm/) | **DONE (local)** | DuckDB SQL + pandas + sklearn + Streamlit | Local only |
| 02 | [NYC Taxi demand](projects/02-nyc-taxi-demand/) | **DONE (local)** | DuckDB SQL + forecasting + Streamlit | Local only |
| 03 | [dbt + DuckDB AE demo](projects/03-dbt-duckdb-analytics/) | **DONE (local)** | dbt + tests + marts | Local only |
| 04 | [Fraud detection (stretch)](projects/04-fraud-detection/) | **DONE (local)** | Imbalanced classification + Streamlit | Local only |

### Snapshot metrics (local runs — from each `reports/metrics.json`)

- **01 Retail:** 397,884 rows · RF repurchase ROC-AUC **0.736** · future monetary MAE **£909**
- **02 Taxi:** 5,826,753 trips · RF hourly demand MAE **371** (vs seasonal naive **461**)
- **03 dbt:** 7 models · **26/26** tests pass · marts on Retail seed (18,532 orders · 4,338 customers)
- **04 Fraud:** 283,726 txns · fraud rate **0.167%** · RF F1 **0.832** · RF PR-AUC **0.815** · logistic ROC-AUC **0.986**

## Unified hub (local)

```bash
cd portfolio/streamlit_hub
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_check.sh          # smoke (no long server)
streamlit run Home.py              # multipage hub
```

Hub lives at [`streamlit_hub/`](streamlit_hub/) — Home + one page per project + FAQ. Loads real `metrics.json` files; does not invent numbers.

## How to run (local)

Each project has `scripts/run_all.sh` and `app/streamlit_app.py`. See project READMEs.

## Stack

Python, pandas, DuckDB SQL, scikit-learn, Streamlit, dbt-duckdb, Git.

## Integrity rules

- No invented experience, titles, or certifications
- Public datasets with citation + license
- Metrics from reproducible runs only
- Do **not** publish to GitHub or deploy Streamlit Cloud without explicit confirmation
