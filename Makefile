.PHONY: run test lint all help

PYTHON ?= $(shell if [ -f .venv-test/bin/python3 ]; then echo .venv-test/bin/python3; elif [ -f .venv/bin/python3 ]; then echo .venv/bin/python3; else echo python3; fi)
PYTEST ?= $(shell if [ -f .venv-test/bin/pytest ]; then echo .venv-test/bin/pytest; elif [ -f .venv/bin/pytest ]; then echo .venv/bin/pytest; else echo pytest; fi)
RUFF ?= $(shell if [ -f .venv-test/bin/ruff ]; then echo .venv-test/bin/ruff; elif [ -f .venv/bin/ruff ]; then echo .venv/bin/ruff; else echo ruff; fi)
STREAMLIT ?= $(shell if [ -f .venv-test/bin/streamlit ]; then echo .venv-test/bin/streamlit; elif [ -f .venv/bin/streamlit ]; then echo .venv/bin/streamlit; else echo streamlit; fi)

run:
	$(STREAMLIT) run app.py

test:
	$(PYTEST) tests/ -q

lint:
	$(RUFF) check .

all: lint test

help:
	@echo "Available targets:"
	@echo "  run   - Run Streamlit application"
	@echo "  test  - Run pytest test suite"
	@echo "  lint  - Run Ruff linter"
	@echo "  all   - Run lint and test"
