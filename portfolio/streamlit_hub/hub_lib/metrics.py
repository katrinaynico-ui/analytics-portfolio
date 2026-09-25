"""Load project metrics.json without inventing numbers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def hub_root() -> Path:
    return Path(__file__).resolve().parents[1]


def career_root() -> Path:
    # .../career-ds-os/portfolio/streamlit_hub → career-ds-os
    return hub_root().parents[1]


def projects_root() -> Path:
    return career_root() / "projects"


def format_number(n: float | int | None, digits: int = 0) -> str:
    if n is None:
        return "—"
    if isinstance(n, float) and not n.is_integer() and digits == 0:
        digits = 2
    if digits == 0:
        return f"{int(round(n)):,}"
    return f"{n:,.{digits}f}"


def load_metrics(project_slug: str, metrics_rel: str = "reports/metrics.json") -> dict[str, Any] | None:
    path = projects_root() / project_slug / metrics_rel
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def metrics_path(project_slug: str, metrics_rel: str = "reports/metrics.json") -> Path:
    return projects_root() / project_slug / metrics_rel
