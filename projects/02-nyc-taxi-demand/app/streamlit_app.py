"""Interactive Streamlit dashboard for NYC yellow taxi demand.

Run:  streamlit run app/streamlit_app.py
Import check (CI / reproduce): does not require the server to start.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    HOURLY_CITY_PARQUET,
    HOURLY_ZONE_PARQUET,
    METRICS_JSON,
    SAMPLE_MONTHS,
)


@st.cache_data(show_spinner=False)
def load_tables():
    city = pd.read_parquet(HOURLY_CITY_PARQUET) if HOURLY_CITY_PARQUET.exists() else None
    zone = pd.read_parquet(HOURLY_ZONE_PARQUET) if HOURLY_ZONE_PARQUET.exists() else None
    metrics = None
    if METRICS_JSON.exists():
        metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    return city, zone, metrics


def main() -> None:
    st.set_page_config(page_title="NYC Taxi Demand", layout="wide")
    st.title("NYC Yellow Taxi — Demand & Revenue (portfolio)")
    st.caption(
        f"NYC TLC public trip records · sample months {', '.join(SAMPLE_MONTHS)} · "
        "local portfolio project · not a client engagement"
    )

    city, zone, metrics = load_tables()
    if city is None or metrics is None:
        st.warning(
            "Processed data missing. From the project root run: "
            "`bash scripts/run_all.sh`"
        )
        return

    ds = metrics["dataset"]
    eda = metrics["eda"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clean trips", f"{ds['n_clean_trips']:,}")
    c2.metric("Pickup zones", f"{ds['n_pickup_zones']:,}")
    c3.metric("Total revenue (USD)", f"{ds['total_revenue_usd']:,.0f}")
    c4.metric("Mean trips / hour", f"{eda['mean_trips_per_hour']:,.0f}")

    st.sidebar.header("Filters")
    hours = sorted(city["hour_of_day"].unique().tolist())
    pick_hours = st.sidebar.multiselect("Hours of day", hours, default=hours)
    dows = sorted(city["day_of_week"].unique().tolist())
    dow_labels = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    pick_dow = st.sidebar.multiselect(
        "Day of week",
        dows,
        default=dows,
        format_func=lambda d: dow_labels.get(int(d), str(d)),
    )

    city_f = city[
        city["hour_of_day"].isin(pick_hours) & city["day_of_week"].isin(pick_dow)
    ]

    zone_names = []
    if zone is not None and not zone.empty:
        zone_names = (
            zone[["location_id", "zone_name", "borough"]]
            .drop_duplicates()
            .sort_values("zone_name")
        )
        options = [
            f"{r.location_id} — {r.zone_name} ({r.borough})"
            for r in zone_names.itertuples(index=False)
        ]
        pick_zones = st.sidebar.multiselect(
            "Pickup zones (charts)",
            options,
            default=options[:8] if len(options) >= 8 else options,
        )
        picked_ids = {int(o.split(" — ")[0]) for o in pick_zones}
    else:
        pick_zones = []
        picked_ids = set()

    tab_demand, tab_zones, tab_models = st.tabs(
        ["Citywide demand", "By zone", "Model metrics"]
    )

    with tab_demand:
        left, right = st.columns(2)
        ts = city_f.sort_values("pickup_hour")
        fig_ts = px.line(
            ts,
            x="pickup_hour",
            y="trip_count",
            title="Citywide trips per hour (filtered)",
        )
        left.plotly_chart(fig_ts, use_container_width=True)

        by_h = (
            city_f.groupby("hour_of_day", as_index=False)["trip_count"]
            .mean()
            .sort_values("hour_of_day")
        )
        fig_h = px.bar(
            by_h, x="hour_of_day", y="trip_count", title="Mean trips by hour of day"
        )
        right.plotly_chart(fig_h, use_container_width=True)

        by_d = (
            city_f.groupby("day_of_week", as_index=False)["trip_count"]
            .mean()
            .sort_values("day_of_week")
        )
        by_d["dow_label"] = by_d["day_of_week"].map(dow_labels)
        fig_d = px.bar(
            by_d, x="dow_label", y="trip_count", title="Mean trips by day of week"
        )
        st.plotly_chart(fig_d, use_container_width=True)

    with tab_zones:
        if zone is None or zone.empty or not picked_ids:
            st.info("Zone table missing or no zones selected.")
        else:
            zf = zone[
                zone["location_id"].isin(picked_ids)
                & zone["hour_of_day"].isin(pick_hours)
            ].copy()
            # DuckDB dow is Sunday=0; citywide uses pandas Mon=0 — for filter we use
            # zone table's own hour_of_day only here to avoid confusion.
            daily = (
                zf.groupby(["zone_name", "pickup_hour"], as_index=False)["trip_count"]
                .sum()
                .sort_values("pickup_hour")
            )
            fig_z = px.line(
                daily,
                x="pickup_hour",
                y="trip_count",
                color="zone_name",
                title="Trips per hour by selected pickup zone",
            )
            st.plotly_chart(fig_z, use_container_width=True)

            top = (
                zf.groupby(["location_id", "zone_name", "borough"], as_index=False)[
                    "trip_count"
                ]
                .sum()
                .sort_values("trip_count", ascending=False)
                .head(20)
            )
            st.dataframe(top, use_container_width=True)

    with tab_models:
        st.subheader("Hourly citywide trip-count forecast (temporal hold-out)")
        reg = pd.DataFrame(metrics["modeling"]["demand_regression"])
        st.dataframe(reg, use_container_width=True)
        fig_mae = px.bar(
            reg,
            x="model",
            y="mae",
            title="MAE by model (lower better)",
            text="mae",
        )
        st.plotly_chart(fig_mae, use_container_width=True)
        fig_rmse = px.bar(
            reg,
            x="model",
            y="rmse",
            title="RMSE by model (lower better)",
            text="rmse",
        )
        st.plotly_chart(fig_rmse, use_container_width=True)
        st.info(
            f"Cutoff={metrics['modeling']['cutoff']} · "
            f"hold-out={metrics['modeling']['hold_out_days']} days · "
            f"best MAE model={metrics['modeling']['best_model_by_mae']}"
        )
        st.caption(
            "Seasonal naive = hour-of-week mean from train only. "
            "ML models use calendar + lag features (lag_1h / 24h / 168h, roll_mean_24h)."
        )


if __name__ == "__main__":
    main()
