# Online Retail — dbt + DuckDB Analytics Warehouse

> **Nota (ES):** Portfolio escrito en **inglés** para reclutadores internacionales. Proyecto local de aprendizaje / demostración de **Analytics Engineering** (dbt + SQL + modelado tipo warehouse) — no es un engagement de cliente.

Warehouse-style modeling with **dbt-duckdb** on the public **UCI Online Retail** dataset: staging → intermediate → marts (`fct_orders`, `dim_customers`, `mart_daily_revenue`, `mart_rfm`), with schema tests.

**Author context:** portfolio practice project showcasing verified Analytics Engineer skills (SQL, dbt, dimensional modeling). No claim of prior production warehouse ownership or client delivery.

---

## Business problem

An analytics team wants a **reproducible retail mart layer**:

1. **Orders & revenue** — invoice-grain facts and daily revenue KPIs.
2. **Customer dimension** — lifetime frequency / monetary / tenure.
3. **RFM segments** — transparent rule-based labels computed in dbt SQL (not a black-box model).

This is **dbt practice on a public seed**, not a live ERP or production BigQuery/Snowflake deployment.

## Data source & warehouse seed

| Field | Value |
| --- | --- |
| Dataset | Online Retail (UCI Machine Learning Repository) |
| Author | Daqing Chen (2015) |
| DOI | https://doi.org/10.24432/C5BW33 |
| License | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| **Seed used here** | Cleaned parquet from sibling project **`01-online-retail-rfm`** (`data/processed/transactions_clean.parquet`) |

Citation:

> Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33

**Why reuse project 01 parquet?** Avoids re-downloading the UCI Excel and treats those cleaned files as a **landing-zone / portfolio warehouse seed**. `scripts/seed_warehouse.py` loads them into `data/warehouse/analytics.duckdb` (`raw.*`). Run project 01 first if the parquet files are missing.

**Not used:** fabricated sales facts; synthetic warehouses.

## Method (interview-friendly)

1. **Seed** — DuckDB `raw.transactions_clean` ← project 01 parquet.
2. **Staging** — `stg_transactions` renames/casts columns.
3. **Intermediate** — `int_orders` (invoice grain), `int_customer_order_stats`.
4. **Marts** — `fct_orders`, `dim_customers`, `mart_daily_revenue`, `mart_rfm` (ntile RFM + rule segments).
5. **Tests** — `unique` / `not_null` / `relationships` / `accepted_values` on marts (and staging keys).
6. **Metrics** — `reports/metrics.json` from a real local `dbt run` + `dbt test`.

## Results (from last local run)

Numbers below are filled after `bash scripts/run_all.sh`. See `reports/metrics.json` for the source of truth.

<!-- RESULTS_START -->

| KPI | Value |
| --- | --- |
| Seed transactions | 397,884 |
| Orders (`fct_orders`) | 18,532 |
| Customers (`dim_customers`) | 4,338 |
| Date range | 2010-12-01 → 2011-12-09 |
| Total revenue (GBP) | 8,911,408 |
| Days in `mart_daily_revenue` | 305 |
| Avg daily revenue (GBP) | ~29,218 |
| dbt tests | **26 / 26 passed** |

**RFM segment counts (dbt SQL):** Need Attention 1079, Hibernating 989, Champions 904, At Risk 526, Loyal 423, New/Promising 412, Big Spenders 5.

<!-- RESULTS_END -->

**Interpretation notes (honest):**

- RFM segments here are **recomputed in dbt** for modeling practice; they may differ slightly from project 01’s pandas RFM (different tie-breaking / as-of date handling).
- DuckDB is a **local stand-in** for a cloud warehouse (BigQuery / Snowflake / Redshift). Patterns transfer; this repo does not claim cloud production experience by itself.
- Tests assert grain and referential integrity — not business correctness of every GBP.

## Project layout

```
03-dbt-duckdb-analytics/
├── README.md
├── requirements.txt
├── Makefile
├── dbt_project.yml
├── profiles.yml.example      # copy → profiles.yml (gitignored)
├── models/
│   ├── staging/              # stg_transactions + sources
│   ├── intermediate/         # int_orders, int_customer_order_stats
│   └── marts/                # fct_orders, dim_customers, mart_*
├── macros/
│   └── generate_schema_name.sql
├── scripts/
│   ├── seed_warehouse.py
│   ├── write_metrics.py
│   └── run_all.sh
├── app/
│   └── streamlit_app.py      # reads marts from DuckDB
├── data/warehouse/           # analytics.duckdb (local, gitignored)
└── reports/
    └── metrics.json
```

## How to run (local only)

Prerequisite: project 01 processed parquet present:

```bash
ls ../01-online-retail-rfm/data/processed/transactions_clean.parquet
# if missing: cd ../01-online-retail-rfm && bash scripts/run_all.sh
```

Then:

```bash
cd projects/03-dbt-duckdb-analytics
bash scripts/run_all.sh
# or: make run-all
```

What `run_all.sh` does: create venv → install deps → seed DuckDB → `dbt run` → `dbt test` → write `reports/metrics.json`.

Manual dbt (after seed + `cp profiles.yml.example profiles.yml`):

```bash
source .venv/bin/activate
dbt run --profiles-dir .
dbt test --profiles-dir .
```

Optional dashboard:

```bash
source .venv/bin/activate
streamlit run app/streamlit_app.py
```

**Do not** push this repo or deploy the app publicly unless explicitly approved.

## Stack

Python 3 · **dbt-core** · **dbt-duckdb** · DuckDB · pandas · Plotly · Streamlit

Skills demonstrated: dbt project structure, staging/intermediate/marts layering, schema tests, local warehouse reproducibility, honest portfolio framing.
