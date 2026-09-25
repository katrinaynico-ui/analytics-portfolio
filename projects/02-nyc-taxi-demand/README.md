# NYC Yellow Taxi — Hourly Demand Forecasting

> **Nota (ES):** Portfolio escrito en **inglés** para reclutadores internacionales. Proyecto local de aprendizaje / demostración técnica — no es un engagement de cliente.

Public **NYC TLC** yellow taxi trip records: EDA (DuckDB SQL), citywide hourly demand forecasting with a seasonal baseline vs Ridge / Random Forest, and a local Streamlit dashboard.

**Author context:** portfolio practice project for analytics / forecasting skills (SQL + Python). No claim of prior production ML experience or of operating NYC taxi systems.

---

## Business problem

A mobility / ops analyst wants a **short-horizon view of yellow-taxi demand**:

1. **When is demand high?** — hour-of-day and day-of-week profiles.
2. **Where do trips start?** — top pickup zones (TLC LocationID).
3. **Can we forecast citywide hourly trips?** — last-week-style hold-out with honest MAE / RMSE.

These metrics are **derived from public TLC trip files**, not from a live dispatch or surge-pricing system.

## Data source & license

| Field | Value |
| --- | --- |
| Dataset | NYC TLC Yellow Taxi Trip Records (Parquet) |
| Publisher | NYC Taxi & Limousine Commission |
| Page | https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page |
| CDN pattern | `https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_YYYY-MM.parquet` |
| Zone lookup | `https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv` |
| Sample months (this repo) | **2024-01**, **2024-02** (~50MB each ≈ **100MB** total) |
| License | NYC Open Data / TLC public trip records (see TLC page terms; attribute TLC) |

Citation:

> NYC Taxi & Limousine Commission. TLC Trip Record Data. https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

**Not used:** synthetic trip generators. Download script fails loudly if TLC CDN is unreachable.

## Method (interview-friendly)

1. **Load & clean** — concat sample months; drop invalid timestamps, non-positive fares, bad location IDs; keep pickups inside the documented months.
2. **SQL aggregates** — DuckDB executes `sql/hourly_demand.sql` (zone × hour trip counts + revenue) joined to taxi zone lookup.
3. **Citywide hourly series** — sum zones → trips/hour; reindex to a complete hourly grid.
4. **Temporal hold-out** (avoids leakage):
   - Last **7 days** of the sample = test window.
   - Features at hour *t* use only past information: calendar + `lag_1h`, `lag_24h`, `lag_168h`, `roll_mean_24h` (shifted).
5. **Competing models**
   - Seasonal naive: hour-of-week mean fit on **train only**.
   - Ridge regression (scaled features).
   - Random Forest regressor.
6. **Metrics** written to `reports/metrics.json` from a real local run (MAE / RMSE / MAPE).

## Results (from last local run)

Numbers below are filled after `bash scripts/run_all.sh`. See `reports/metrics.json` for the source of truth.

<!-- RESULTS_START -->

| KPI | Value |
| --- | --- |
| Clean trips | 5,826,753 |
| Pickup zones | 261 |
| Sample months | 2024-01 → 2024-02 |
| Total revenue (USD) | 159,691,766 |
| Mean trips / hour | 4,046 |
| Peak hour (mean) | 18:00 (~7,122 trips) |
| Hold-out | last 7 days (cutoff 2024-02-23, n_test=168 hours) |

**Top pickup zones (by trips):** Midtown Center, Upper East Side South/North, JFK Airport, Midtown East.

### Citywide hourly trip-count forecast (test hold-out)

| Model | MAE | RMSE | MAPE |
| --- | ---: | ---: | ---: |
| Seasonal naive (hour-of-week) | 461 | 859 | 10.3% |
| Ridge | 491 | 733 | 21.6% |
| Random Forest | **371** | **699** | 11.9% |

Test mean demand ≈ 4,427 trips/hour — RF MAE ≈ 8.4% of mean.

<!-- RESULTS_END -->

**Interpretation notes (honest):**

- Citywide hourly counts are smoother than zone-level series; MAE in the hundreds of trips can still be a small relative error when mean demand is thousands/hour.
- Seasonal naive is intentionally strong for taxi data (weekly seasonality) — ML gains should be explained, not assumed.
- Two months is a **sample** for portfolio practice, not a full multi-year production model.

## Project layout

```
02-nyc-taxi-demand/
├── README.md
├── requirements.txt
├── Makefile
├── scripts/
│   ├── download_data.py
│   └── run_all.sh
├── sql/
│   └── hourly_demand.sql       # DuckDB zone×hour aggregates
├── src/
│   ├── config.py
│   ├── data_load.py
│   ├── clean.py
│   ├── aggregates.py
│   ├── models.py
│   └── pipeline.py
├── app/
│   └── streamlit_app.py
├── data/
│   ├── raw/                    # TLC parquet + zone lookup
│   └── processed/              # clean + hourly parquet
└── reports/
    └── metrics.json
```

## How to run (local only)

```bash
cd projects/02-nyc-taxi-demand
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

Skills demonstrated: public data hygiene, SQL analytics, leakage-aware temporal splits, baseline-vs-ML forecasting, reproducible scripts.
