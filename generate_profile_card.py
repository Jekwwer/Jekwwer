"""GitHub contribution heatmap generator.

Fetches contribution data from the GitHub GraphQL API, calculates streaks,
and writes updated SVG profile cards to the docs/ directory.

Architecture:
    Each card style in CARD_STYLES owns its placeholder resolver and any
    card-specific SVG marker generators.  main() fetches shared data once,
    conditionally fetches per-card prerequisites (e.g. Steam), and dispatches
    to each style's resolver.  Adding a new style = one CARD_STYLES entry
    plus one resolver function.

Required environment variables:
    GH_USERNAME  — GitHub username.
    GITHUB_TOKEN — Personal access token with read:user scope.

Optional environment variables:
    STEAM_API_KEY — Steam Web API key (used by styles with needs_steam=True).
    STEAM_ID      — 64-bit Steam user ID.
"""

import argparse
import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypedDict

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
STEAM_RECENT_GAMES_URL = (
    "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"
)

# Earliest date from which contributions are fetched.
CONTRIBUTIONS_START_DATE = datetime(2018, 7, 25, tzinfo=timezone.utc)

# GitHub GraphQL API limits a single contributionsCollection query to one year.
FETCH_CHUNK_SIZE = timedelta(days=365)

HEATMAP_WEEKS = 52
HEATMAP_DAYS_PER_WEEK = 7
HEATMAP_CELLS = HEATMAP_WEEKS * HEATMAP_DAYS_PER_WEEK  # 364

REQUEST_TIMEOUT_SECONDS = 10

# Fraction of total grid width reserved for gaps between columns.
GRID_SPACING_RATIO = 0.1

ASSETS_DIR = Path("assets")  # source files: template SVGs
DOCS_DIR = Path("docs")  # deployment output: generated SVGs + backgrounds

# GraphQL query fetches contribution counts per day for a given date range.
# repositories.totalCount is fetched on every call but only used from the first.
_GRAPHQL_QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC) {
      totalCount
    }
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

# Gradient IDs referenced by SVG templates, keyed by intensity level (0–5).
# Stroke IDs always follow the pattern f"{color_id}-stroke".
CONTRIBUTION_COLORS = {
    0: "heat-lvl-0",
    1: "heat-lvl-1",
    2: "heat-lvl-2",
    3: "heat-lvl-3",
    4: "heat-lvl-4",
    5: "heat-lvl-5",
}

MONTH_ABBR: list[str] = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

# Day-of-week indices (Monday=0) to render as row labels in the heatmap.
HEATMAP_ROW_LABELS: list[tuple[int, str]] = [(0, "Mon"), (2, "Wed"), (4, "Fri")]

# Legend labels per intensity level.
LEGEND_LABELS: dict[int, str] = {
    0: "0: Burnout / Sleep / Love / Death / Vacay — Who knows! ( ͡° ͜ʖ ͡°)",
    1: "1–10",
    2: "11–20",
    3: "21–30",
    4: "31–49",
    5: "50+",
}

# Legend layout constants (px). Derived from calculate_cell_dimensions(794) output
# and empirically measured label widths at 10 px font-size.
LEGEND_TEXT_OFFSET_X = 20  # cell left edge → label x
LEGEND_TEXT_OFFSET_Y = 12  # cell top → text baseline
LEGEND_LONG_ITEM_WIDTH = 321.3  # width of level-0 item (cell + long label + gap)
LEGEND_SHORT_ITEM_WIDTH = 61.2  # width of each subsequent item (cell + short label)

# ── Types ──────────────────────────────────────────────────────────────────────


class ContributionData(TypedDict):
    """Contribution stats returned by fetch_contributions_from_github."""

    contributions: dict[str, int]
    total_contributions: int
    current_streak: int
    longest_streak: int
    longest_streak_start: str | None
    longest_streak_end: str | None
    first_commit: str | None
    public_repos: int


class StreakData(TypedDict):
    """Streak stats returned by calculate_streaks."""

    current_streak: int
    longest_streak: int
    longest_streak_start: str | None
    longest_streak_end: str | None


@dataclass
class CardContext:
    """Shared state passed to per-card resolvers and marker generators.

    Attributes:
        data: Contribution stats from GitHub.
        levels: ISO date → intensity level (0–5) mapping.
        raw_counts: ISO date → raw contribution count mapping.
        steam_game: Most-played Steam game name, or "nothing" if unavailable.
        steam_id: Steam 64-bit user ID, or "" if unavailable.
    """

    data: ContributionData
    levels: dict[str, int]
    raw_counts: dict[str, int]
    steam_game: str = "nothing"
    steam_id: str = ""


@dataclass
class CardStyle:
    """Configuration for a single profile card style.

    Attributes:
        template: SVG template filename relative to ASSETS_DIR.
        outputs: (output_filename, inject_background) pairs written to the style subdir.
        resolver: Callable returning a {placeholder: value} dict for this style.
        background: Background SVG filename in the style subdir; empty string if unused.
        subdir: Subdirectory under DOCS_DIR for outputs and background.
        extra_markers: {marker_comment: callable} for style-specific SVG injection
            beyond the shared Grid + Legend markers (e.g. heatmap axis labels).
        needs_steam: Whether this style's resolver reads Steam data from CardContext.
            Used by main() to skip the Steam API call when no active style needs it.
    """

    template: str
    outputs: list[tuple[str, bool]]
    resolver: Callable[[CardContext], dict[str, str]]
    background: str = ""
    subdir: str = ""
    extra_markers: dict[str, Callable[[CardContext], str]] = field(default_factory=dict)
    needs_steam: bool = False


# ── Helpers ────────────────────────────────────────────────────────────────────


def format_date(date_value: str | None) -> str:
    """Convert an ISO date string to YYYY/MM/DD, or return 'N/A' if None."""
    if isinstance(date_value, str):
        return date_value.replace("-", "/")
    return "N/A"


def _format_years_active(first_commit: str | None) -> str:
    """Format elapsed time since first_commit as '<N> yr[s] [<M> mo]'."""
    if not first_commit:
        return "unknown"
    today = datetime.now(timezone.utc).date()
    delta = today - datetime.fromisoformat(first_commit).date()
    yrs, rem = divmod(delta.days, 365)
    mos = rem // 30
    if yrs and mos:
        return f"{yrs} yr{'s' if yrs != 1 else ''} {mos} mo"
    if yrs:
        return f"{yrs} yr{'s' if yrs != 1 else ''}"
    return f"{mos} mo"


def _read_background_fragment(style_dir: Path, bg_file: str) -> str:
    """Return a background SVG's inner content with the outer <svg> wrapper stripped."""
    raw = (style_dir / bg_file).read_text(encoding="utf-8")
    start = raw.index(">") + 1
    end = raw.rindex("<")
    return raw[start:end].strip()


def _parse_contribution_days(weeks: list[Any]) -> dict[str, int]:
    """Extract a date → count mapping from a GraphQL weeks payload."""
    contributions: dict[str, int] = {}
    for week in weeks:
        for day in week.get("contributionDays", []):
            date_str = day.get("date")
            count = day.get("contributionCount", 0)
            if date_str and isinstance(count, int):
                contributions[date_str] = count
    return contributions


def _fetch_all_contributions(username: str, token: str) -> tuple[dict[str, int], int]:
    """Fetch all contributions since CONTRIBUTIONS_START_DATE, one year at a time.

    Returns:
        Tuple of (date → count mapping, public repository count).
    """
    all_contributions: dict[str, int] = {}
    public_repos = 0
    headers = {"Authorization": f"Bearer {token}"}

    start = CONTRIBUTIONS_START_DATE
    end = datetime.now(timezone.utc)

    logger.info("Fetching contributions for '%s' since %s", username, start.date())

    while start < end:
        chunk_end = min(start + FETCH_CHUNK_SIZE, end)
        variables = {
            "username": username,
            "from": start.isoformat(),
            "to": chunk_end.isoformat(),
        }
        logger.debug("Chunk: %s → %s", start.date(), chunk_end.date())

        try:
            response = requests.post(
                GITHUB_GRAPHQL_URL,
                json={"query": _GRAPHQL_QUERY, "variables": variables},
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()

            if "data" in payload and payload["data"].get("user"):
                user = payload["data"]["user"]
                if public_repos == 0:
                    public_repos = user["repositories"]["totalCount"]
                weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
                all_contributions.update(_parse_contribution_days(weeks))
            else:
                logger.error("Unexpected API response: %s", payload)
        except requests.exceptions.RequestException as e:
            logger.error(
                "Request failed (%s → %s): %s", start.date(), chunk_end.date(), e
            )

        start = chunk_end

    return all_contributions, public_repos


def fetch_currently_playing_from_steam(api_key: str, steam_id: str) -> str | None:
    """Fetch the most-played game in the last two weeks from Steam.

    Requires the Steam profile's game details to be set to Public.

    Returns:
        Name of the most-played recent game, or None if unavailable.
    """
    try:
        response = requests.get(
            STEAM_RECENT_GAMES_URL,
            params={
                "key": api_key,
                "steamid": steam_id,
                "count": "5",
                "format": "json",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        games = response.json().get("response", {}).get("games", [])
        if games:
            return str(games[0]["name"])
    except requests.exceptions.RequestException as e:
        logger.warning("Steam API request failed: %s", e)
    return None


# ── Core Functions ─────────────────────────────────────────────────────────────


def fetch_contributions_from_github(username: str, token: str) -> ContributionData:
    """Fetch contribution data and calculate streaks for a GitHub user."""
    all_contributions, public_repos = _fetch_all_contributions(username, token)

    cutoff = (
        datetime.now(timezone.utc).date() - timedelta(weeks=HEATMAP_WEEKS)
    ).isoformat()
    recent_contributions = {
        date: count for date, count in all_contributions.items() if date >= cutoff
    }

    streaks = calculate_streaks(all_contributions)
    total = sum(all_contributions.values())
    first_commit = min((d for d, c in all_contributions.items() if c > 0), default=None)

    logger.info(
        "Total: %d | Current streak: %d | Longest streak: %d",
        total,
        streaks["current_streak"],
        streaks["longest_streak"],
    )

    return {
        "contributions": recent_contributions,
        "total_contributions": total,
        "current_streak": streaks["current_streak"],
        "longest_streak": streaks["longest_streak"],
        "longest_streak_start": streaks["longest_streak_start"],
        "longest_streak_end": streaks["longest_streak_end"],
        "first_commit": first_commit,
        "public_repos": public_repos,
    }


def calculate_streaks(contributions: dict[str, int]) -> StreakData:
    """Calculate the current and longest contribution streaks."""
    today = datetime.now(timezone.utc).date()
    # Exclude today when it has no contributions — the day may not be complete yet.
    active = {
        d: c
        for d, c in contributions.items()
        if not (datetime.fromisoformat(d).date() == today and c == 0)
    }
    sorted_dates = sorted(active.keys(), key=lambda d: datetime.fromisoformat(d))

    current_streak = 0
    longest_streak = 0
    longest_streak_start = None
    longest_streak_end = None
    streak_start = None

    for date_str in sorted_dates:
        date = datetime.fromisoformat(date_str).date()

        if active[date_str] > 0:
            if current_streak == 0:
                streak_start = date

            current_streak += 1

            if current_streak > longest_streak:
                longest_streak = current_streak
                longest_streak_start = streak_start
                longest_streak_end = date
        else:
            current_streak = 0
            streak_start = None

    logger.info(
        "Streaks — current: %d days | longest: %d days (%s → %s)",
        current_streak,
        longest_streak,
        longest_streak_start.isoformat() if longest_streak_start else "N/A",
        longest_streak_end.isoformat() if longest_streak_end else "N/A",
    )

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "longest_streak_start": (
            longest_streak_start.isoformat() if longest_streak_start else None
        ),
        "longest_streak_end": (
            longest_streak_end.isoformat() if longest_streak_end else None
        ),
    }


def map_contributions_to_levels(contributions: dict[str, int]) -> dict[str, int]:
    """Map raw contribution counts to heatmap intensity levels (0–5)."""

    def _count_to_level(count: int) -> int:
        if count == 0:
            return 0
        if count <= 10:
            return 1
        if count <= 20:
            return 2
        if count <= 30:
            return 3
        if count <= 49:
            return 4
        return 5

    return {date: _count_to_level(count) for date, count in contributions.items()}


def calculate_cell_dimensions(
    grid_width: int, weeks: int = HEATMAP_WEEKS
) -> tuple[float, float]:
    """Calculate cell size and inter-cell spacing for the heatmap grid."""
    gap_total = grid_width * GRID_SPACING_RATIO
    cell_size = (grid_width - gap_total) / weeks
    cell_spacing = gap_total / (weeks - 1)
    return round(cell_size, 2), round(cell_spacing, 2)


def create_svg_grid_with_heatmap(
    levels: dict[str, int],
    raw_counts: dict[str, int],
    grid_width: int = 794,
) -> str:
    """Render the contribution heatmap as a sequence of SVG <rect> elements."""
    cell_size, cell_spacing = calculate_cell_dimensions(grid_width)

    entries = list(levels.items())[-HEATMAP_CELLS:]

    svg_parts = ["<!-- Contribution Grid -->"]

    x, y = 0.0, 0.0
    for index, (date, level) in enumerate(entries):
        color = CONTRIBUTION_COLORS[level]
        count = raw_counts.get(date, 0)
        svg_parts.append(
            f'<rect class="grid-cell" x="{x}" y="{y}" '
            f'width="{cell_size}" height="{cell_size}" '
            f'fill="url(#{color})" stroke="url(#{color}-stroke)" '
            f'rx="2" title="{date}: {count}"/>'
        )
        y += cell_size + cell_spacing
        if (index + 1) % HEATMAP_DAYS_PER_WEEK == 0:
            y = 0.0
            x += cell_size + cell_spacing

    logger.info("SVG grid generated: %d cells", len(entries))
    return "\n".join(svg_parts)


def create_svg_legend(grid_width: int = 794) -> str:
    """Render the heatmap colour-scale legend."""
    cell_size, _ = calculate_cell_dimensions(grid_width)

    parts = ["<!-- Contribution Grid Legend -->"]
    for level, label in LEGEND_LABELS.items():
        x = (
            0.0
            if level == 0
            else round(
                LEGEND_LONG_ITEM_WIDTH + (level - 1) * LEGEND_SHORT_ITEM_WIDTH, 1
            )
        )
        color_id = CONTRIBUTION_COLORS[level]
        parts.append(
            f'<rect x="{x}" y="0" width="{cell_size}" height="{cell_size}" '
            f'fill="url(#{color_id})" stroke="url(#{color_id}-stroke)" rx="2" />'
        )
        parts.append(
            f'<text class="legend-label" x="{round(x + LEGEND_TEXT_OFFSET_X, 1)}" '
            f'y="{LEGEND_TEXT_OFFSET_Y}">{label}</text>'
        )
    logger.info("SVG legend generated")
    return "\n".join(parts)


def create_svg_grid_labels(
    levels: dict[str, int],
    grid_width: int = 794,
) -> str:
    """Render day-of-week and month labels for the heatmap grid."""
    cell_size, cell_spacing = calculate_cell_dimensions(grid_width)
    step = cell_size + cell_spacing

    entries = list(levels.items())[-HEATMAP_CELLS:]
    if not entries:
        return "<!-- Contribution Grid Labels -->"

    parts = ["<!-- Contribution Grid Labels -->"]

    first_weekday = datetime.fromisoformat(entries[0][0]).weekday()  # Mon=0
    for target_weekday, label in HEATMAP_ROW_LABELS:
        row = (target_weekday - first_weekday) % 7
        y = round(row * step + cell_size * 0.5 + 3.5, 1)
        parts.append(
            f'<text class="mono-sm" x="-10" y="{y}" text-anchor="end">{label}</text>'
        )

    month_positions: dict[str, float] = {}
    prev_month: int | None = None
    for col in range(HEATMAP_WEEKS):
        entry_idx = col * HEATMAP_DAYS_PER_WEEK
        if entry_idx >= len(entries):
            break
        month = int(entries[entry_idx][0][5:7])
        if month != prev_month:
            month_positions[MONTH_ABBR[month - 1]] = round(col * step, 1)
            prev_month = month
    for abbr, x in month_positions.items():
        parts.append(f'<text class="mono-sm" x="{x}" y="-4">{abbr}</text>')

    logger.info("SVG grid labels generated")
    return "\n".join(parts)


# ── Per-Card Placeholder Resolvers ─────────────────────────────────────────────
#
# One resolver per card style.  Each returns {placeholder-token: replacement}
# for its template.  Add a new resolver + CARD_STYLES entry to support a new card.


def _resolve_glass_placeholders(ctx: CardContext) -> dict[str, str]:
    """Placeholders for the glass style card."""
    data = ctx.data
    longest_start = format_date(data["longest_streak_start"])
    longest_end = format_date(data["longest_streak_end"])
    return {
        "total-contributions-ph": f"{data['total_contributions']:,}🌟",
        "current-streak-ph": f"{data['current_streak']}🔥",
        "longest-streak-ph": (
            f"{longest_start} .. {longest_end} : {data['longest_streak']}🏆"
        ),
    }


def _resolve_man_placeholders(ctx: CardContext) -> dict[str, str]:
    """Placeholders for the man-page style card."""
    data = ctx.data
    longest_start = format_date(data["longest_streak_start"])
    longest_end = format_date(data["longest_streak_end"])
    first = data["first_commit"]
    return {
        "total-contributions-ph": f"{data['total_contributions']:,}🌟",
        "current-streak-ph": f"{data['current_streak']}🔥",
        "longest-streak-count-ph": (
            f"{data['longest_streak']}🏆 {longest_start} .. {longest_end}"
        ),
        "first-commit-ph": first or "unknown",
        "years-active-ph": _format_years_active(first),
        "repos-ph": str(data["public_repos"]),
        "currently-playing-ph": ctx.steam_game,
        "steam-id-ph": ctx.steam_id,
    }


# ── Card Style Registry ────────────────────────────────────────────────────────
#
# Adding a new style: add one entry here + one resolver above.

CARD_STYLES: dict[str, CardStyle] = {
    "glass": CardStyle(
        template="profile-card.glass.template.svg",
        outputs=[
            ("profile-card.glass.svg", True),
            ("profile-card.glass-no-background.svg", False),
        ],
        background="background.glass.svg",
        subdir="glass",
        resolver=_resolve_glass_placeholders,
    ),
    "man": CardStyle(
        template="profile-card.man-page.template.svg",
        outputs=[
            ("profile-card.man-page.svg", True),
            ("profile-card.man-page-no-background.svg", False),
        ],
        background="background.man-page.svg",
        subdir="man",
        resolver=_resolve_man_placeholders,
        extra_markers={
            "<!-- Contribution Grid Labels -->": (
                lambda ctx: create_svg_grid_labels(ctx.levels)
            ),
        },
        needs_steam=True,
    ),
}


# ── Entry Point ────────────────────────────────────────────────────────────────


def _apply_substitutions(svg: str, subs: dict[str, str]) -> str:
    """Replace every key in subs with its value. Single pass per key."""
    for key, value in subs.items():
        svg = svg.replace(key, value)
    return svg


def _resolve_steam(active_styles: dict[str, CardStyle]) -> tuple[str, str]:
    """Fetch Steam game + id if any active style needs it. Defaults otherwise."""
    if not any(s.needs_steam for s in active_styles.values()):
        return "nothing", ""
    api_key = os.getenv("STEAM_API_KEY")
    steam_id = os.getenv("STEAM_ID")
    if not (api_key and steam_id):
        return "nothing", ""
    game = fetch_currently_playing_from_steam(api_key, steam_id)
    return game or "nothing", steam_id


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

    username = os.getenv("GH_USERNAME")
    token = os.getenv("GITHUB_TOKEN")
    if not username:
        raise ValueError("Missing GH_USERNAME environment variable.")
    if not token:
        raise ValueError("Missing GITHUB_TOKEN environment variable.")

    data = fetch_contributions_from_github(username, token)
    raw_counts = data["contributions"]
    levels = map_contributions_to_levels(raw_counts)

    steam_game, steam_id = _resolve_steam(active_styles)

    ctx = CardContext(
        data=data,
        levels=levels,
        raw_counts=raw_counts,
        steam_game=steam_game,
        steam_id=steam_id,
    )

    # Shared markers used by every card.
    shared_markers = {
        "<!-- Contribution Grid Legend -->": create_svg_legend(),
        "<!-- Contribution Grid -->": create_svg_grid_with_heatmap(levels, raw_counts),
    }

    for style_name, style in active_styles.items():
        style_dir = DOCS_DIR / style.subdir if style.subdir else DOCS_DIR
        style_dir.mkdir(parents=True, exist_ok=True)

        bg_fragment = (
            _read_background_fragment(style_dir, style.background)
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
                svg = (ASSETS_DIR / style.template).read_text(encoding="utf-8")
                svg = svg.replace(
                    "<!-- Background -->", bg_fragment if inject_bg else ""
                )
                svg = _apply_substitutions(svg, markers)
                svg = _apply_substitutions(svg, placeholders)
                out_path = style_dir / output_file
                out_path.write_text(svg, encoding="utf-8")
                logger.info("Written: %s", out_path)
            except Exception as e:
                logger.error(
                    "Failed to process %s → %s: %s", style_name, output_file, e
                )
                raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)
