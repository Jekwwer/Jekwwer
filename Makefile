# Makefile: Simplifies common development tasks.

.PHONY: help format format-fix lint lint-fix type spell

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help             Show this help message."
	@echo ""
	@echo "  format           Verify formatting in Python files (Ruff) and Prettier-supported files."
	@echo "  format-fix       Auto-format Python files (Ruff) and Prettier-supported files."
	@echo "  lint             Run Ruff to lint Python files."
	@echo "  lint-fix         Run Ruff to auto-fix Python lint issues."
	@echo "  type             Run Mypy for static type checking."
	@echo "  spell            Run cspell to spell-check all files."

format:
	poetry run ruff format . --check
	npm run format

format-fix:
	poetry run ruff format .
	npm run format-fix

lint:
	poetry run ruff check .

lint-fix:
	poetry run ruff check --fix .

type:
	poetry run mypy --install-types --non-interactive .

spell:
	npm run spell
