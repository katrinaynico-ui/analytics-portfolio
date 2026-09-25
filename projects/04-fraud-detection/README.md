# Credit Card Fraud Detection — Imbalanced Classification (stretch)

> **Nota (ES):** Portfolio escrito en **inglés** para reclutadores internacionales. Proyecto local de aprendizaje / stretch técnico — **no** es experiencia productiva en fraude / AML ni un engagement de cliente.

Public **credit-card fraud** classification: DuckDB SQL EDA, class-weighted logistic vs Random Forest (plus simple baselines), honest **F1 / ROC-AUC / PR-AUC**, and a local Streamlit dashboard with threshold slider.

**Author context:** portfolio practice / stretch for imbalanced classification skills (SQL + sklearn). **No claim of prior production fraud-ML experience** or of operating payment-risk systems.

---

## Business problem (framed as learning)

A risk-analytics learner wants to practice **detecting rare fraudulent transactions** when:

1. **~0.17% of rows are fraud** — accuracy alone is meaningless.
2. Features are **PCA-anonymized** (classic ULB set) — limited interpretability.
3. Models must be compared with **precision, recall, F1, ROC-AUC, PR-AUC**.

These metrics come from a **public research CSV**, not from a live card network.

## Data source & license

| Field | Value |
| --- | --- |
| Dataset | Credit Card Fraud Detection (Sep 2013 European cardholders) |
| Origin | Worldline / ULB Machine Learning Group (Dal Pozzolo et al.) |
| Kaggle listing | https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud |
| OpenML | https://www.openml.org/d/1597 |
| Download used here | TensorFlow public GCS mirror (no Kaggle credentials) |
| Fallback mirror | Zenodo CC BY 4.0 — https://doi.org/10.5281/zenodo.7395559 |
| Size | ~151 MB CSV · 284,807 transactions · 492 frauds |
| Features | `Time`, `V1`–`V28` (PCA), `Amount`, `Class` |
| License | Public research release via Kaggle/OpenML; Zenodo mirror **CC BY 4.0** |

Citation:

> Dal Pozzolo, A., Caelen, O., Johnson, R. A., & Bontempi, G. (2015). Calibrating Probability with Undersampling for Unbalanced Classification. IEEE CIDM. Dataset: Credit Card Fraud Detection (Worldline / ULB MLG).

**Honest PCA note:** `V1`–`V28` are principal components of confidential raw features. Only `Time` and `Amount` are in clear form. Feature engineering and business interpretation are therefore limited — stated explicitly for interview honesty.

**Not used:** synthetic fraud generators. Download fails loudly if public mirrors are unreachable. No Kaggle API key required.

## Method (interview-friendly)

1. **Load & clean** — read CSV; drop exact duplicates; validate labels / Amount.
2. **SQL EDA** — DuckDB runs `sql/fraud_eda.sql` (global rates, amount buckets × class, hour-of-day proxy from `Time`).
3. **Temporal hold-out** (avoids leakage):
   - Sort by `Time`; last **20%** of transactions = test.
   - Model features = `V1`–`V28` + `Amount`. **`Time` is ordering-only**, not in `X`.
4. **Class imbalance** — `class_weight='balanced'` on Logistic Regression and Random Forest (inverse frequency). Undersampling the majority class was considered but **not** used, so the model still sees the full negative distribution.
5. **Competing models**
   - Majority class (always legit) — shows why accuracy is a trap.
   - Flag-rare Amount rule — flag if `Amount ≥` train quantile at `(1 − fraud_rate)`.
   - Class-weighted logistic regression (scaled features).
   - Class-weighted Random Forest.
6. **Metrics** at threshold 0.5 → `reports/metrics.json` from a real local run (ROC-AUC, PR-AUC, F1, precision, recall + confusion counts).

## Results (from last local run)

Numbers below are filled after `bash scripts/run_all.sh`. See `reports/metrics.json` for the source of truth.

<!-- RESULTS_START -->

| KPI | Value |
| --- | --- |
| Transactions (after dedupe) | 283,726 |
| Frauds | 473 |
| Fraud rate | 0.1667% |
| Hold-out | last 20% by Time (cutoff=145234s) |
| Train / test | 226,980 / 56,746 (fraud 399 / 74) |
| Best F1 (ML) | **random_forest_class_weighted** (0.8321) |
| Best ROC-AUC (ML) | **logistic_class_weighted** (0.9862) |

### Classification (test hold-out, threshold = 0.5)

| Model | ROC-AUC | PR-AUC | F1 | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| majority_class | 0.5000 | 0.0013 | 0.0000 | 0.0000 | 0.0000 |
| flag_rare_amount | 0.4994 | 0.0013 | 0.0000 | 0.0000 | 0.0000 |
| logistic_class_weighted | 0.9862 | 0.7612 | 0.0801 | 0.0419 | 0.9054 |
| random_forest_class_weighted | 0.9722 | 0.8150 | 0.8321 | 0.9048 | 0.7703 |

<!-- RESULTS_END -->

**Interpretation notes (honest):**

- With ~0.17% positives, a majority classifier gets ~99.8% accuracy and **near-zero F1** — accuracy is not reported as a success metric.
- **PR-AUC** is more informative than ROC-AUC alone under extreme imbalance.
- PCA features limit storytelling (“V14 matters”) vs real payment attributes (MCC, device, geo).
- Two days of 2013 European card traffic is a **classic teaching set**, not a modern production fraud stack.

## Project layout

```
04-fraud-detection/
├── README.md
├── requirements.txt
├── Makefile
├── scripts/
│   ├── download_data.py
│   └── run_all.sh
├── sql/
│   └── fraud_eda.sql           # DuckDB EDA aggregates
├── src/
│   ├── config.py
│   ├── data_load.py
│   ├── clean.py
│   ├── aggregates.py
│   ├── models.py
│   └── pipeline.py
├── app/
│   └── streamlit_app.py        # confusion matrix / ROC / PR / threshold slider
├── data/
│   ├── raw/                    # creditcard.csv
│   └── processed/              # clean + test predictions parquet
└── reports/
    └── metrics.json
```

## How to run (local only)

```bash
cd projects/04-fraud-detection
bash scripts/run_all.sh
# optional UI
.venv/bin/streamlit run app/streamlit_app.py
```

**Do not push / publish to GitHub** from this environment unless explicitly authorized.

## Stack

Python · pandas · scikit-learn · DuckDB · Plotly · Streamlit · Parquet
