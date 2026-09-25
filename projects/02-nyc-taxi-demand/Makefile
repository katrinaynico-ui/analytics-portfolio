.PHONY: setup download pipeline run-all app check

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

download:
	.venv/bin/python scripts/download_data.py

pipeline:
	.venv/bin/python -m src.pipeline

run-all:
	bash scripts/run_all.sh

app:
	.venv/bin/streamlit run app/streamlit_app.py

check:
	.venv/bin/python -c "import importlib.util; from pathlib import Path; p=Path('app/streamlit_app.py'); s=importlib.util.spec_from_file_location('streamlit_app', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('ok')"
	test -f reports/metrics.json
