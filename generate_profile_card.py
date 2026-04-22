"""GitHub profile card generator — CLI entry point.

Thin orchestrator: validates assets, fetches shared data once, dispatches to
each active card's resolver. Card logic lives in `profile_card.cards`;
network I/O in `profile_card.fetchers`. See CONTRIBUTING.md for usage.
"""

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path

from profile_card import (
    CARD_STYLES,
    CardContext,
    CardStyle,
    create_svg_grid_with_heatmap,
    create_svg_legend,
    fetch_contributions_from_github,
    fetch_currently_playing_from_steam,
    load_config,
    map_contributions_to_levels,
    read_background_fragment,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

ASSETS_DIR = Path("assets")
DOCS_DIR = Path("docs")
README_PATH = Path("README.md")

_UNREPLACED_PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")
_README_CARD_PATH_RE = re.compile(r"docs/[^/)]+/profile-card\.[^)]+\.svg")
_LANDING_REDIRECT_RE = re.compile(r"url=\./[^/\s]+/")


def _apply_substitutions(svg: str, subs: dict[str, str]) -> str:
    """Replace each key in `subs` with its value. Single pass per key (no re-scan)."""
    for key, value in subs.items():
        svg = svg.replace(key, value)
    return svg


def _resolve_steam_game(active_styles: dict[str, CardStyle], steam_id: str) -> str:
    """Fetch the Steam game name, or return `"nothing"`.

    `"nothing"` is also returned when no active style has `needs_steam=True`
    or when `STEAM_API_KEY` env var is unset (with a warning).
    """
    if not any(s.needs_steam for s in active_styles.values()):
        return "nothing"
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        logger.warning(
            "Steam-requiring style active but STEAM_API_KEY not set — "
            "recently-playing placeholder will fall back to 'nothing'."
        )
        return "nothing"
    return fetch_currently_playing_from_steam(api_key, steam_id) or "nothing"


def _update_active_style_refs(active_style: str, style: CardStyle) -> None:
    """Point README and docs landing redirect at the configured active style.

    Rewrites in-place: README image path (any `docs/<x>/profile-card.<y>.svg`
    occurrences) and `docs/index.html` `<meta refresh>` target.
    """
    filename = style.outputs[0][0]
    new_path = f"docs/{style.subdir}/{filename}"

    if README_PATH.is_file():
        readme = README_PATH.read_text(encoding="utf-8")
        updated, n = _README_CARD_PATH_RE.subn(new_path, readme)
        if n and updated != readme:
            README_PATH.write_text(updated, encoding="utf-8")
            logger.info("README.md: card path → %s (%d occurrence(s))", new_path, n)

    landing = DOCS_DIR / "index.html"
    if landing.is_file():
        html = landing.read_text(encoding="utf-8")
        updated, n = _LANDING_REDIRECT_RE.subn(f"url=./{active_style}/", html)
        if n and updated != html:
            landing.write_text(updated, encoding="utf-8")
            logger.info("docs/index.html: redirect → ./%s/", active_style)


def _validate_template_files(active_styles: dict[str, CardStyle]) -> None:
    """Raise on first missing template/background — run before any network call."""
    for style_name, style in active_styles.items():
        template_path = ASSETS_DIR / style.template
        if not template_path.is_file():
            raise FileNotFoundError(
                f"Style '{style_name}' template missing: {template_path}"
            )
        if style.background:
            bg_path = DOCS_DIR / style.subdir / style.background
            if not bg_path.is_file():
                raise FileNotFoundError(
                    f"Style '{style_name}' background missing: {bg_path}"
                )
        if style.index_template:
            index_path = ASSETS_DIR / style.index_template
            if not index_path.is_file():
                raise FileNotFoundError(
                    f"Style '{style_name}' index template missing: {index_path}"
                )


def main() -> None:
    """Orchestrate the contribution card update pipeline."""
    parser = argparse.ArgumentParser(description="Generate GitHub profile card SVGs.")
    parser.add_argument(
        "--style",
        default="all",
        choices=[*CARD_STYLES, "all"],
        help="Card style to generate (default: all).",
    )
    args = parser.parse_args()
    active_styles = (
        CARD_STYLES if args.style == "all" else {args.style: CARD_STYLES[args.style]}
    )
    logger.info("Generating styles: %s", ", ".join(active_styles))
    start_time = time.perf_counter()

    config = load_config()
    active_style = config["active_style"]
    if active_style not in CARD_STYLES:
        raise ValueError(
            f"config.active_style '{active_style}' not in {sorted(CARD_STYLES)}"
        )
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("Missing GITHUB_TOKEN environment variable.")

    _validate_template_files(active_styles)

    data = fetch_contributions_from_github(config["user"]["name"], token)
    raw_counts = data["contributions"]
    levels = map_contributions_to_levels(raw_counts)

    steam_game = _resolve_steam_game(active_styles, config["steam_id"])

    ctx = CardContext(
        data=data,
        levels=levels,
        raw_counts=raw_counts,
        config=config,
        steam_game=steam_game,
    )

    shared_markers = {
        "<!-- Contribution Grid Legend -->": create_svg_legend(),
        "<!-- Contribution Grid -->": create_svg_grid_with_heatmap(levels, raw_counts),
    }

    files_written = 0
    for style_name, style in active_styles.items():
        style_dir = DOCS_DIR / style.subdir
        style_dir.mkdir(parents=True, exist_ok=True)

        template = (ASSETS_DIR / style.template).read_text(encoding="utf-8")
        bg_fragment = (
            read_background_fragment(style_dir, style.background)
            if style.background
            else ""
        )

        markers = {
            **shared_markers,
            **{marker: fn(ctx) for marker, fn in style.extra_markers.items()},
        }
        placeholders = style.resolver(ctx)

        for output_file, inject_bg in style.outputs:
            try:
                svg = template.replace(
                    "<!-- Background -->", bg_fragment if inject_bg else ""
                )
                svg = _apply_substitutions(svg, markers)
                svg = _apply_substitutions(svg, placeholders)
                leftover = set(_UNREPLACED_PLACEHOLDER_RE.findall(svg))
                if leftover:
                    logger.warning(
                        "Unreplaced placeholders in %s/%s: %s",
                        style_name,
                        output_file,
                        ", ".join(sorted(leftover)),
                    )
                out_path = style_dir / output_file
                out_path.write_text(svg, encoding="utf-8")
                files_written += 1
                logger.info("Written: %s", out_path)
            except Exception as e:
                logger.error(
                    "Failed to process %s → %s: %s", style_name, output_file, e
                )
                raise

        if style.index_template:
            index_src = (ASSETS_DIR / style.index_template).read_text(encoding="utf-8")
            rendered = _apply_substitutions(index_src, placeholders)
            leftover = set(_UNREPLACED_PLACEHOLDER_RE.findall(rendered))
            if leftover:
                logger.warning(
                    "Unreplaced placeholders in %s/index.html: %s",
                    style_name,
                    ", ".join(sorted(leftover)),
                )
            index_path = style_dir / "index.html"
            index_path.write_text(rendered, encoding="utf-8")
            files_written += 1
            logger.info("Written: %s", index_path)

    _update_active_style_refs(active_style, CARD_STYLES[active_style])

    logger.info(
        "Done: %d file(s) in %.2fs", files_written, time.perf_counter() - start_time
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)
