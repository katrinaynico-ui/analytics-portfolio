# Online Retail — RFM Segmentation, Cohorts & Retention Models

> **Nota (ES):** Portfolio escrito en **inglés** para reclutadores internacionales. Proyecto local de aprendizaje / demostración técnica — no es un engagement de cliente.

Customer analytics on the public **UCI Online Retail** dataset: RFM segments, monthly cohort retention (DuckDB SQL), and two modeling tasks with competing approaches and honest metrics.

**Author context:** portfolio practice project for analytics / analytics-engineering skills (SQL + Python). No claim of prior production ML experience.

---

## Business problem

A UK-based online giftware retailer (dataset period ~2010–2011) needs:

1. **Who are our customers?** — actionable RFM segments (Champions, At Risk, Hibernating, …).
2. **How does retention evolve?** — monthly acquisition cohorts.
3. **Who is likely to buy again?** — short-horizon repurchase prediction after a cutoff date.
4. **How much might they spend next?** — hold-out revenue as a simple CLV *proxy* (not full lifetime CLV).

These are **derived labels from the public transaction log**, not CRM churn flags from a live system.

## Data source & license

| Field | Value |
| --- | --- |
| Dataset | Online Retail (UCI Machine Learning Repository) |
| Author | Daqing Chen (2015) |
| DOI | https://doi.org/10.24432/C5BW33 |
| Download | https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx |
| License | Creative Commons Attribution 4.0 International (CC BY 4.0) |

Citation:

> Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33

**Not used:** synthetic / fabricated sales data (a synthetic fallback exists only inside `scripts/download_data.py` if the UCI download fails — clearly labeled and not for portfolio claims).

## Method (interview-friendly)

1. **Load & clean** — drop cancellations (`InvoiceNo` starting with `C`), missing `CustomerID`, non-positive qty/price; compute `line_revenue`.
2. **RFM** — Recency / Frequency / Monetary with quintile scores and transparent rule-based segment labels (not black-box clustering).
3. **Cohorts** — DuckDB executes `sql/rfm_cohorts.sql` on the cleaned frame (SQL path alongside pandas).
4. **Temporal split for modeling** (avoids leakage):
   - Features from purchases **before** cutoff (`max(date) − 90 days`).
   - Labels from the following **90-day** window: `repurchase` (binary) and `future_monetary` (regression).
5. **Competing models**
   - Classification: rule baseline (Recency≤60 & Frequency≥2) vs Logistic Regression vs Random Forest.
   - Regression: mean baseline vs Ridge vs Random Forest Regressor.
6. **Metrics** written to `reports/metrics.json` from a real local run.

## Results (from last local run)

Numbers below are filled after `bash scripts/run_all.sh`. See `reports/metrics.json` for the source of truth.

<!-- RESULTS_START -->

| KPI | Value |
| --- | --- |
| Clean transactions | 397,884 |
| Customers | 4,338 |
| Date range | 2010-12-01 → 2011-12-09 |
| Total revenue (GBP) | 8,911,408 |
| Avg cohort retention @ month 1 | 20.6% |
| Hold-out repurchase rate | 57.0% (cutoff 2011-09-10, 90d) |

**RFM segment counts:** Champions 962, Loyal 758, At Risk 643, Hibernating 1065, Need Attention 553, New/Promising 319, Big Spenders 38.

### Repurchase classification (test n=843)

| Model | ROC-AUC | F1 | Precision | Recall |
| --- | ---: | ---: | ---: | ---: |
| Rule baseline | 0.716 | 0.594 | 0.782 | 0.478 |
| Logistic Regression | 0.726 | 0.661 | 0.765 | 0.582 |
| Random Forest | 0.736 | 0.684 | 0.761 | 0.622 |

### Future monetary regression — CLV proxy (MAE, lower better)

| Model | MAE (GBP) | RMSE |
| --- | ---: | ---: |
| Mean baseline | 1,188 | 7,235 |
| Ridge | 955 | 6,554 |
| Random Forest | 909 | 6,677 |

<!-- RESULTS_END -->

**Interpretation notes (honest):**

- Repurchase base rate is far from 50/50; accuracy alone is misleading — prefer ROC-AUC / F1 / average precision.
- Future monetary is heavy-tailed; MAE can look large in absolute GBP even when ranking is useful.
- Rule baseline is intentionally simple so ML gains are explainable, not magical.

## Project layout

```
01-online-retail-rfm/
├── README.md
├── requirements.txt
├── Makefile
├── scripts/
│   ├── download_data.py
│   └── run_all.sh
├── sql/
│   └── rfm_cohorts.sql          # DuckDB cohort retention
├── src/
│   ├── config.py
│   ├── data_load.py
│   ├── clean.py
│   ├── rfm.py
│   ├── cohorts.py
│   ├── models.py
│   └── pipeline.py
├── app/
│   └── streamlit_app.py
├── data/
│   ├── raw/                     # Online_Retail.xlsx (gitignored if you add git later)
│   └── processed/               # parquet outputs
└── reports/
    └── metrics.json
```

## How to run (local only)

```bash
cd projects/01-online-retail-rfm
bash scripts/run_all.sh
# or: make run-all
```

Optional dashboard (not required for success criteria):

```bash
source .venv/bin/activate
streamlit run app/streamlit_app.py
```

**Do not** push this repo or deploy the app publicly unless explicitly approved.

## Stack

Python 3 · pandas · scikit-learn · DuckDB (SQL) · Plotly · Streamlit · parquet

Skills demonstrated: SQL analytics, RFM / cohort design, leakage-aware temporal splits, baseline-vs-ML comparison, reproducible scripts.
