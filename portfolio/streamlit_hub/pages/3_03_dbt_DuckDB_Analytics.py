import sys
from pathlib import Path

HUB = Path(__file__).resolve().parents[1]
if str(HUB) not in sys.path:
    sys.path.insert(0, str(HUB))

from hub_lib.project_page import render_project_page

render_project_page("03")
