"""Public runtime config loader.

Reads `config.json` at the repo root — holds committed, non-secret values
(username, public links, Steam ID). Secrets (`GITHUB_TOKEN`, `STEAM_API_KEY`)
stay in env vars.
"""

import json
from pathlib import Path
from typing import TypedDict

CONFIG_PATH = Path("config.json")


class Link(TypedDict):
    """Single link entry: canonical URL + display string shown on the card."""

    url: str
    display: str


class User(TypedDict):
    """User identity block."""

    name: str
    display: str


class Config(TypedDict):
    """Top-level shape of `config.json`."""

    user: User
    links: dict[str, Link]
    steam_id: str


def load_config() -> Config:
    """Load and parse `config.json` from the current working directory."""
    raw: Config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return raw
