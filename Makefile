.PHONY: run test lint format typecheck scan clean

run:
	poetry run uvicorn src.hanuman.main:app --reload

test:
	poetry run pytest -v tests/

lint:
	poetry run ruff check src tests

lint-fix:
	poetry run ruff check --fix src tests

format:
	poetry run black src tests

typecheck:
	poetry run mypy src tests

semgrep:
	poetry run semgrep -c .semgrep.yml src/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

test-cov:
	poetry run pytest --cov=src/hanuman --cov-report=term-missing
