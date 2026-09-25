.PHONY: setup seed dbt-run dbt-test run-all app check

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

seed:
	.venv/bin/python scripts/seed_warehouse.py

dbt-run:
	.venv/bin/dbt run --profiles-dir .

dbt-test:
	.venv/bin/dbt test --profiles-dir .

run-all:
	bash scripts/run_all.sh

app:
	.venv/bin/streamlit run app/streamlit_app.py

check:
	test -f reports/metrics.json
	.venv/bin/python -c "import importlib.util; from pathlib import Path; p=Path('app/streamlit_app.py'); s=importlib.util.spec_from_file_location('streamlit_app', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('ok')"
