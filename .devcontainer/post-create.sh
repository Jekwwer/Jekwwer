#!/usr/bin/env bash

set -euo pipefail

npm install

pipx install poetry
poetry install --with lint,mypy

poetry run pre-commit install --hook-type pre-commit --hook-type commit-msg
