#!/usr/bin/env bash
# Seed DuckDB warehouse ← project 01 parquet → dbt run → dbt test → metrics.json
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# Ensure local profiles.yml exists (gitignored; example is committed)
if [[ ! -f profiles.yml ]]; then
  cp profiles.yml.example profiles.yml
  echo "[run_all] created profiles.yml from example"
fi

python scripts/seed_warehouse.py

echo "[run_all] dbt deps (if any)…"
dbt deps --profiles-dir . --project-dir . 2>/dev/null || true

echo "[run_all] dbt debug…"
dbt debug --profiles-dir . --project-dir .

echo "[run_all] dbt run…"
dbt run --profiles-dir . --project-dir .

echo "[run_all] dbt test…"
dbt test --profiles-dir . --project-dir .

python scripts/write_metrics.py

# Import check for Streamlit app (does not start the server)
python -c "
import importlib.util
from pathlib import Path
p = Path('app/streamlit_app.py')
spec = importlib.util.spec_from_file_location('streamlit_app', p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('[check] streamlit_app imported OK; main=', callable(getattr(mod, 'main', None)))
"

test -f reports/metrics.json
echo "[run_all] SUCCESS — reports/metrics.json ready"
echo "[run_all] Optional UI: streamlit run app/streamlit_app.py"
