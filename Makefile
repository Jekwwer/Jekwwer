.PHONY: help install format format-fix lint lint-fix type spell check clean pre-commit

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help         Show this help message."
	@echo ""
	@echo "  install      Install Python and Node dependencies."
	@echo "  clean        Remove tool caches."
	@echo ""
	@echo "  format       Verify formatting (Ruff + Prettier)."
	@echo "  format-fix   Auto-fix formatting (Ruff + Prettier)."
	@echo "  lint         Lint Python files (Ruff)."
	@echo "  lint-fix     Auto-fix Python lint issues (Ruff)."
	@echo "  type         Static type check Python files (Mypy)."
	@echo "  spell        Spell-check all files (cspell)."
	@echo "  check        Run all checks (format, lint, type, spell)."
	@echo ""
	@echo "  pre-commit   Run all pre-commit hooks against all files."

install:
	poetry install
	npm install

format:
	poetry run ruff format . --check
	npx prettier --check --config .prettierrc .

format-fix:
	poetry run ruff format .
	npx prettier --write --config .prettierrc .

lint:
	poetry run ruff check .

lint-fix:
	poetry run ruff check --fix .

type:
	poetry run mypy --install-types --non-interactive .

spell:
	npx cspell . --cache

check: format lint type spell

clean:
	rm -rf .ruff_cache .mypy_cache .cspellcache

pre-commit:
	poetry run pre-commit run --all-files
