.PHONY: install fmt lint test run clean

install:
\tpython -m pip install --upgrade pip
\tpip install -r requirements.txt
\tpre-commit install || true

fmt:
\tisort .
\tblack .

lint:
\tflake8 .

test:
\tpytest -q

run:
\tpython app.py "Please add 5 and 7"

clean:
\tfind . -name "__pycache__" -type d -exec rm -rf {} +
\trm -rf .pytest_cache .mypy_cache

