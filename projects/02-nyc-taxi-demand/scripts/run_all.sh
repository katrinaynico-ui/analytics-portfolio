#!/usr/bin/env bash
# Reproduce the full local pipeline (download → clean → SQL EDA → models → metrics).
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

python scripts/download_data.py
python -m src.pipeline

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
