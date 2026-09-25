#!/usr/bin/env bash
# Smoke check for the portfolio Streamlit hub — no long-lived server.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  echo "FAIL: no python available" >&2
  exit 1
fi

echo "== hub smoke check =="
echo "ROOT=$ROOT"
echo "PY=$PY ($("$PY" -c 'import sys; print(sys.version.split()[0])'))"

"$PY" - <<'PY'
import ast
import importlib
import sys
from pathlib import Path

ROOT = Path(".").resolve()
sys.path.insert(0, str(ROOT))

# 1) Syntax-check all Python entrypoints
paths = [ROOT / "Home.py", *sorted((ROOT / "pages").glob("*.py"))]
paths += sorted((ROOT / "hub_lib").glob("*.py"))
for p in paths:
    ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    print(f"OK syntax {p.relative_to(ROOT)}")

# 2) Import library (no Streamlit server)
from hub_lib import PROJECTS, PROFILE, load_metrics, projects_root

assert PROFILE["name"].startswith("Nicolás"), "profile name lock"
assert len(PROJECTS) == 4, "expected 4 projects"

missing = []
for p in PROJECTS:
    m = load_metrics(p["slug"], p["metrics_rel"])
    path = projects_root() / p["slug"] / p["metrics_rel"]
    if m is None:
        missing.append(str(path))
        print(f"MISSING metrics {path}")
    else:
        print(f"OK metrics {p['slug']} keys={list(m.keys())[:6]}...")

# 3) Import project_page helpers
from hub_lib.project_page import get_project, RENDERERS

for pid in ("01", "02", "03", "04"):
    get_project(pid)
    assert pid in RENDERERS

# 4) Compile Home + pages as modules without executing Streamlit UI long-run
#    (ast already done; also ensure streamlit import works if installed)
try:
    import streamlit  # noqa: F401
    print(f"OK streamlit import ({streamlit.__version__})")
except ImportError as e:
    print(f"WARN: streamlit not installed in this interpreter: {e}")

if missing:
    print("SMOKE FAIL: missing metrics files:")
    for x in missing:
        print(" -", x)
    sys.exit(1)

print("SMOKE OK")
PY

echo "== done =="
