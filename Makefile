
LOG_DIR := logs
POETRY_RUN = poetry run

.PHONY: run test lint format typecheck scan clean
		lean_logs clean_log_debug clean_log_info clean_log_error

# Static analyzers

run:
	@$(POETRY_RUN) uvicorn src.hanuman.main:app --reload

lint:
	@$(POETRY_RUN) ruff check src tests

lint-fix:
	@$(POETRY_RUN) ruff check --fix --unsafe-fixes src tests && black src tests

format:
	@$(POETRY_RUN) black src tests

mypy:
	@$(POETRY_RUN) mypy src tests

semgrep:
	@$(POETRY_RUN) semgrep -c .semgrep.yml src/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Test

test:
	@$(POETRY_RUN) pytest -v tests/

test-cov:
	@$(POETRY_RUN) pytest --cov=src/hanuman --cov-report=term-missing --cov-report=xml

coverage-html:
	@$(POETRY_RUN) pytest --cov=src/hanuman --cov-report=html --cov-report=term-missing
	@xdg-open htmlcov/index.html

clean-coverage:
	rm -rf .coverage htmlcov coverage.xml

# Logs cleaner and display

clean_logs:
	@echo rm -f $(LOG_DIR)/hanuman_*.json $(LOG_DIR)/hanuman_*.json

clean_log_debug:
	@echo rm -f $(LOG_DIR)/hanuman_debug.json

clean_log_info:
	@echo rm -f $(LOG_DIR)/hanuman_info.json

clean_log_error:
	@echo rm -f $(LOG_DIR)/hanuman_error.json

log-debug:
	@tail -f $(LOG_DIR)/hanuman_debug.json

log-info:
	@tail -f $(LOG_DIR)/hanuman_info.json

log-error:
	@tail -f $(LOG_DIR)/hanuman_error.json
