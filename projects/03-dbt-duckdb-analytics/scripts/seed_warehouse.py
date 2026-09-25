"""Load project-01 cleaned parquet into a local DuckDB "warehouse" seed.

This avoids re-downloading the UCI Online Retail Excel. The parquet files are
outputs of ``01-online-retail-rfm`` (cleaned transactions + optional RFM table).

Portfolio framing: treat those parquet files as a **landing-zone seed** that a
downstream analytics-engineer dbt project would model into staging → marts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "data" / "warehouse" / "analytics.duckdb"

# Sibling project 01 processed outputs (prefer reuse over re-download)
PROJ_01_PROCESSED = (
    ROOT.parent / "01-online-retail-rfm" / "data" / "processed"
)
TXN_PARQUET = PROJ_01_PROCESSED / "transactions_clean.parquet"
RFM_PARQUET = PROJ_01_PROCESSED / "rfm_segments.parquet"


def main() -> int:
    if not TXN_PARQUET.exists():
        print(
            f"[seed] ERROR: missing {TXN_PARQUET}\n"
            "  Run project 01 first: cd ../01-online-retail-rfm && bash scripts/run_all.sh",
            file=sys.stderr,
        )
        return 1

    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    if WAREHOUSE.exists():
        WAREHOUSE.unlink()
    wal = Path(str(WAREHOUSE) + ".wal")
    if wal.exists():
        wal.unlink()

    con = duckdb.connect(str(WAREHOUSE))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    con.execute(
        f"""
        CREATE OR REPLACE TABLE raw.transactions_clean AS
        SELECT * FROM read_parquet('{TXN_PARQUET.as_posix()}')
        """
    )
    n_txn = con.execute("SELECT COUNT(*) FROM raw.transactions_clean").fetchone()[0]
    print(f"[seed] raw.transactions_clean ← {TXN_PARQUET.name} ({n_txn:,} rows)")

    if RFM_PARQUET.exists():
        con.execute(
            f"""
            CREATE OR REPLACE TABLE raw.rfm_segments AS
            SELECT * FROM read_parquet('{RFM_PARQUET.as_posix()}')
            """
        )
        n_rfm = con.execute("SELECT COUNT(*) FROM raw.rfm_segments").fetchone()[0]
        print(f"[seed] raw.rfm_segments ← {RFM_PARQUET.name} ({n_rfm:,} rows)")
    else:
        print(f"[seed] WARN: {RFM_PARQUET.name} missing — mart_rfm will compute from transactions")

    con.execute(
        """
        CREATE OR REPLACE TABLE raw._seed_meta AS
        SELECT
            'UCI Online Retail (via 01-online-retail-rfm processed parquet)' AS source_label,
            ? AS txn_parquet_path,
            ? AS seeded_at_utc
        """,
        [str(TXN_PARQUET), __import__("datetime").datetime.utcnow().isoformat() + "Z"],
    )
    con.close()
    print(f"[seed] warehouse ready: {WAREHOUSE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
