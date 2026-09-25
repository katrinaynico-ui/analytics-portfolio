"""Write reports/metrics.json after dbt run + test (row counts, test results)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "data" / "warehouse" / "analytics.duckdb"
METRICS = ROOT / "reports" / "metrics.json"
TARGET = ROOT / "target"


def _table_counts(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    tables = [
        "raw.transactions_clean",
        "staging.stg_transactions",
        "intermediate.int_orders",
        "marts.fct_orders",
        "marts.dim_customers",
        "marts.mart_daily_revenue",
        "marts.mart_rfm",
    ]
    out: dict[str, int] = {}
    for t in tables:
        try:
            out[t] = int(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
        except Exception:
            # DuckDB may use different schema naming depending on dbt config
            short = t.split(".", 1)[-1]
            found = False
            for schema in ("main", "staging", "intermediate", "marts", "raw"):
                try:
                    out[t] = int(
                        con.execute(f'SELECT COUNT(*) FROM "{schema}"."{short}"').fetchone()[0]
                    )
                    found = True
                    break
                except Exception:
                    continue
            if not found:
                # try without schema (dbt-duckdb sometimes flattens)
                try:
                    out[t] = int(con.execute(f"SELECT COUNT(*) FROM {short}").fetchone()[0])
                except Exception:
                    out[t] = -1
    return out


def _discover_model_tables(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Count known mart/staging relations under any schema."""
    wanted = {
        "stg_transactions",
        "int_orders",
        "int_customer_order_stats",
        "fct_orders",
        "dim_customers",
        "mart_daily_revenue",
        "mart_rfm",
        "transactions_clean",
    }
    rows = con.execute(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type IN ('BASE TABLE', 'VIEW')
        """
    ).fetchall()
    counts: dict[str, int] = {}
    for schema, name in rows:
        if name in wanted:
            n = con.execute(f'SELECT COUNT(*) FROM "{schema}"."{name}"').fetchone()[0]
            counts[f"{schema}.{name}"] = int(n)
    return counts


def _parse_run_results() -> dict:
    path = TARGET / "run_results.json"
    if not path.exists():
        return {"tests_total": 0, "tests_passed": 0, "tests_failed": 0, "models_ok": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    results = data.get("results", [])
    tests = [r for r in results if r.get("unique_id", "").startswith("test.")]
    models = [r for r in results if r.get("unique_id", "").startswith("model.")]
    # run_results from `dbt test` only has tests; from `dbt run` only models.
    # We also look at a combined approach: call dbt test with --store-failures and read.
    passed = sum(1 for r in tests if r.get("status") == "pass")
    failed = sum(1 for r in tests if r.get("status") in ("fail", "error"))
    models_ok = sum(1 for r in models if r.get("status") == "success")
    return {
        "tests_total": len(tests),
        "tests_passed": passed,
        "tests_failed": failed,
        "models_ok": models_ok,
        "elapsed_seconds": data.get("elapsed_time"),
    }


def _run_dbt_test_and_collect() -> dict:
    """Run dbt test and parse run_results.json."""
    proc = subprocess.run(
        [sys.executable.replace("python", "dbt") if False else str(ROOT / ".venv" / "bin" / "dbt"),
         "test", "--profiles-dir", str(ROOT), "--project-dir", str(ROOT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    # Prefer parsing run_results even if exit != 0
    summary = _parse_run_results()
    summary["dbt_test_exit_code"] = proc.returncode
    summary["dbt_test_stdout_tail"] = "\n".join(proc.stdout.strip().splitlines()[-30:])
    return summary


def main() -> int:
    # Expect caller already ran dbt test; re-parse last run_results if present,
    # else run dbt test once.
    test_summary = _parse_run_results()
    if test_summary["tests_total"] == 0:
        # Maybe last artifact was from `dbt run` — run tests now
        print("[metrics] no test results in target/; running dbt test…")
        test_summary = _run_dbt_test_and_collect()

    if not WAREHOUSE.exists():
        print(f"[metrics] ERROR: missing warehouse {WAREHOUSE}", file=sys.stderr)
        return 1

    con = duckdb.connect(str(WAREHOUSE), read_only=True)
    counts = _discover_model_tables(con)

    # KPIs from marts
    kpis: dict = {}
    try:
        # find fct_orders / mart_daily_revenue / dim_customers
        fct = next((k for k in counts if k.endswith(".fct_orders")), None)
        dim = next((k for k in counts if k.endswith(".dim_customers")), None)
        daily = next((k for k in counts if k.endswith(".mart_daily_revenue")), None)
        rfm = next((k for k in counts if k.endswith(".mart_rfm")), None)

        if fct:
            sch, name = fct.split(".", 1)
            row = con.execute(
                f'''
                SELECT
                  COUNT(*) AS n_orders,
                  COUNT(DISTINCT customer_id) AS n_customers_with_orders,
                  ROUND(SUM(order_revenue), 2) AS total_revenue,
                  MIN(order_date)::VARCHAR AS date_min,
                  MAX(order_date)::VARCHAR AS date_max
                FROM "{sch}"."{name}"
                '''
            ).fetchone()
            kpis["orders"] = {
                "n_orders": row[0],
                "n_customers_with_orders": row[1],
                "total_revenue": float(row[2]) if row[2] is not None else None,
                "date_min": row[3],
                "date_max": row[4],
            }
        if dim:
            sch, name = dim.split(".", 1)
            kpis["n_customers_dim"] = int(
                con.execute(f'SELECT COUNT(*) FROM "{sch}"."{name}"').fetchone()[0]
            )
        if daily:
            sch, name = daily.split(".", 1)
            row = con.execute(
                f'''
                SELECT COUNT(*), ROUND(SUM(daily_revenue), 2), ROUND(AVG(daily_revenue), 2)
                FROM "{sch}"."{name}"
                '''
            ).fetchone()
            kpis["daily_revenue"] = {
                "n_days": row[0],
                "total_revenue": float(row[1]) if row[1] is not None else None,
                "avg_daily_revenue": float(row[2]) if row[2] is not None else None,
            }
        if rfm:
            sch, name = rfm.split(".", 1)
            segs = con.execute(
                f'''
                SELECT segment, COUNT(*) AS n
                FROM "{sch}"."{name}"
                GROUP BY 1 ORDER BY n DESC
                '''
            ).fetchall()
            kpis["rfm_segment_counts"] = {s: int(n) for s, n in segs}
    finally:
        con.close()

    # Also try to read model list from manifest
    models_built: list[str] = []
    manifest = TARGET / "manifest.json"
    if manifest.exists():
        man = json.loads(manifest.read_text(encoding="utf-8"))
        for uid, node in man.get("nodes", {}).items():
            if uid.startswith("model.") and node.get("resource_type") == "model":
                models_built.append(node.get("name"))
        models_built = sorted(set(models_built))

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "03-dbt-duckdb-analytics",
        "framing": (
            "Portfolio practice: dbt + DuckDB warehouse modeling on UCI Online Retail "
            "seeded from project 01 processed parquet. Not a client engagement."
        ),
        "data_seed": {
            "source": "01-online-retail-rfm/data/processed/transactions_clean.parquet",
            "dataset": "UCI Online Retail",
            "doi": "https://doi.org/10.24432/C5BW33",
            "license": "CC BY 4.0",
            "citation": (
                "Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. "
                "https://doi.org/10.24432/C5BW33"
            ),
        },
        "warehouse_path": str(WAREHOUSE.relative_to(ROOT)),
        "models": models_built,
        "row_counts": counts,
        "kpis": kpis,
        "dbt_tests": {
            "total": test_summary.get("tests_total", 0),
            "passed": test_summary.get("tests_passed", 0),
            "failed": test_summary.get("tests_failed", 0),
            "exit_code": test_summary.get("dbt_test_exit_code"),
        },
        "notes": [
            "Seed reuses cleaned parquet from project 01 (no re-download of UCI Excel).",
            "Models follow staging → intermediate → marts.",
            "Metrics from a real local dbt run; no invented business outcomes.",
        ],
    }

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[metrics] wrote {METRICS}")
    print(json.dumps({"row_counts": counts, "dbt_tests": payload["dbt_tests"]}, indent=2))

    if payload["dbt_tests"]["failed"] and payload["dbt_tests"]["failed"] > 0:
        return 1
    if payload["dbt_tests"]["total"] == 0:
        print("[metrics] WARN: zero tests recorded", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
