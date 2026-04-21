"""GitHub contribution heatmap generator.

Fetches contribution data from the GitHub GraphQL API, calculates streaks,
and writes updated SVG profile cards to the assets/ directory.

Pipeline:
    1. _fetch_all_contributions      — paginate GitHub GraphQL year by year.
    2. calculate_streaks             — compute current/longest streak with dates.
    3. map_contributions_to_levels   — map raw counts to 6 heatmap intensity levels.
    4. create_svg_grid_with_heatmap  — render a 52×7 SVG <rect> grid.
    5. create_svg_legend             — render the colour-scale legend.
    6. replace_placeholders_in_svg   — inject stats into SVG text-node placeholders.
    7. main                          — orchestrate and write output files.

Required environment variables:
    GH_USERNAME  — GitHub username.
    GITHUB_TOKEN — Personal access token with read:user scope.
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass
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


@dataclass
class CardStyle:
    """Configuration for a single profile card style.

    Attributes:
        template: SVG template filename relative to ASSETS_DIR.
        outputs: (output_filename, inject_background) pairs written to DOCS_DIR.
        background: Background SVG filename in DOCS_DIR; empty string if unused.
    """

    template: str
    outputs: list[tuple[str, bool]]
    background: str = ""


# Registry of supported card styles.
# Add a new CardStyle entry here to support an additional style — no other
# code changes required.
CARD_STYLES: dict[str, CardStyle] = {
    "glass": CardStyle(
        template="profile-card.glass.template.svg",
        outputs=[
            ("profile-card.glass.svg", True),
            ("profile-card.glass-no-background.svg", False),
        ],
        background="background.glass.svg",
    ),
}

# GraphQL query fetches contribution counts per day for a given date range.
_GRAPHQL_QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
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
    """Contribution stats returned by fetch_contributions_from_github.

    Attributes:
        contributions (dict[str, int]): Daily counts for the last 52 weeks.
        total_contributions (int): All-time total contribution count.
        current_streak (int): Current consecutive-day streak length.
        longest_streak (int): Longest consecutive-day streak ever.
        longest_streak_start (str | None): ISO date the longest streak began.
        longest_streak_end (str | None): ISO date the longest streak ended.
    """

    contributions: dict[str, int]
    total_contributions: int
    current_streak: int
    longest_streak: int
    longest_streak_start: str | None
    longest_streak_end: str | None


class StreakData(TypedDict):
    """Streak stats returned by calculate_streaks.

    Attributes:
        current_streak (int): Current consecutive-day streak length.
        longest_streak (int): Longest consecutive-day streak ever.
        longest_streak_start (str | None): ISO date the longest streak began.
        longest_streak_end (str | None): ISO date the longest streak ended.
    """

    current_streak: int
    longest_streak: int
    longest_streak_start: str | None
    longest_streak_end: str | None


# ── Helpers ────────────────────────────────────────────────────────────────────


def format_date(date_value: str | None) -> str:
    """Convert an ISO date string to YYYY/MM/DD, or return 'N/A' if None."""
    if isinstance(date_value, str):
        return date_value.replace("-", "/")
    return "N/A"


def _read_background_fragment(bg_file: str) -> str:
    """Return a background SVG's inner content with the outer <svg> wrapper stripped.

    Stripping the wrapper makes the fragment embeddable inside the card SVG.
    Secondary <defs> and <style> blocks are valid SVG and render correctly.
    """
    raw = (DOCS_DIR / bg_file).read_text(encoding="utf-8")
    # Drop the opening <svg ...> tag and the closing </svg>.
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


def _fetch_all_contributions(username: str, token: str) -> dict[str, int]:
    """Fetch all contributions since CONTRIBUTIONS_START_DATE, one year at a time.

    GitHub's GraphQL API limits contributionsCollection queries to a one-year
    window, so this function paginates in FETCH_CHUNK_SIZE steps.

    Args:
        username: GitHub username.
        token: GitHub personal access token.

    Returns:
        Dict mapping ISO date strings to daily contribution counts.
    """
    all_contributions: dict[str, int] = {}
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
                weeks = payload["data"]["user"]["contributionsCollection"][
                    "contributionCalendar"
                ]["weeks"]
                all_contributions.update(_parse_contribution_days(weeks))
            else:
                logger.error("Unexpected API response: %s", payload)
        except requests.exceptions.RequestException as e:
            logger.error(
                "Request failed (%s → %s): %s", start.date(), chunk_end.date(), e
            )

        start = chunk_end

    return all_contributions


# ── Core Functions ─────────────────────────────────────────────────────────────


def fetch_contributions_from_github(username: str, token: str) -> ContributionData:
    """Fetch contribution data and calculate streaks for a GitHub user.

    Retrieves all-time contributions via _fetch_all_contributions, then filters
    to the last HEATMAP_WEEKS weeks for the heatmap display.

    Args:
        username: GitHub username.
        token: GitHub personal access token with read:user scope.

    Returns:
        ContributionData with heatmap contributions and all-time streak stats.
    """
    all_contributions = _fetch_all_contributions(username, token)

    cutoff = (
        datetime.now(timezone.utc).date() - timedelta(weeks=HEATMAP_WEEKS)
    ).isoformat()
    recent_contributions = {
        date: count for date, count in all_contributions.items() if date >= cutoff
    }

    streaks = calculate_streaks(all_contributions)
    total = sum(all_contributions.values())

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
    }


def calculate_streaks(contributions: dict[str, int]) -> StreakData:
    """Calculate the current and longest contribution streaks.

    A streak is a consecutive sequence of days with at least one contribution.
    Dates are processed in chronological order.

    Args:
        contributions: Dict mapping ISO date strings to daily contribution counts.

    Returns:
        StreakData with current/longest streak lengths and the longest streak's dates.
    """
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
    """Map raw contribution counts to heatmap intensity levels (0–5).

    Level thresholds:
        0  — no contributions
        1  — 1–10
        2  — 11–20
        3  — 21–30
        4  — 31–49
        5  — 50+

    Args:
        contributions: Dict mapping ISO date strings to daily contribution counts.

    Returns:
        Dict mapping the same dates to intensity levels.
    """

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
    """Calculate the cell size and inter-cell spacing for the heatmap grid.

    GRID_SPACING_RATIO of the total grid width is reserved for column gaps;
    the remainder is divided equally across all week columns.

    Args:
        grid_width: Total grid width in pixels.
        weeks: Number of week columns.

    Returns:
        Tuple of (cell_size, cell_spacing), both rounded to 2 decimal places.
    """
    gap_total = grid_width * GRID_SPACING_RATIO
    cell_size = (grid_width - gap_total) / weeks
    cell_spacing = gap_total / (weeks - 1)
    return round(cell_size, 2), round(cell_spacing, 2)


def create_svg_grid_with_heatmap(
    levels: dict[str, int],
    raw_counts: dict[str, int],
    grid_width: int = 794,
) -> str:
    """Render the contribution heatmap as an SVG <g> element.

    Produces HEATMAP_CELLS <rect> elements arranged in a 52-column × 7-row grid,
    with CSS class and fill references matching the SVG template's style definitions.

    Args:
        levels: Dict mapping ISO date strings to intensity levels (0–5).
        raw_counts: Dict mapping ISO date strings to raw contribution counts,
            used to populate cell tooltip titles.
        grid_width: Total grid width in pixels.

    Returns:
        SVG markup string, including the opening <!-- Contribution Grid --> marker.
    """
    cell_size, cell_spacing = calculate_cell_dimensions(grid_width)

    # Take the most recent HEATMAP_CELLS entries so the grid is always full.
    entries = list(levels.items())[-HEATMAP_CELLS:]

    svg_parts = [
        "<!-- Contribution Grid -->",
        '<g transform="translate(50, 520)">',
    ]

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

    svg_parts.append("</g>")
    logger.info("SVG grid generated: %d cells", len(entries))
    return "\n".join(svg_parts)


def create_svg_legend(grid_width: int = 794) -> str:
    """Render the heatmap colour-scale legend as an SVG <g> element.

    Generates one labelled cell per intensity level. Level-0 uses a long
    descriptive label; levels 1–5 use compact range labels. Positions are
    computed from LEGEND_LONG_ITEM_WIDTH / LEGEND_SHORT_ITEM_WIDTH constants
    so gaps remain consistent with the grid's cell size.

    Args:
        grid_width: Total grid width in pixels (must match
            create_svg_grid_with_heatmap).

    Returns:
        SVG markup string, including the opening
        <!-- Contribution Grid Legend --> marker.
    """
    cell_size, _ = calculate_cell_dimensions(grid_width)

    parts = [
        "<!-- Contribution Grid Legend -->",
        '<g transform="translate(50, 636)">',
    ]
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
    parts.append("</g>")
    logger.info("SVG legend generated")
    return "\n".join(parts)


def replace_placeholders_in_svg(svg_content: str, stats: ContributionData) -> str:
    """Replace stat placeholders in an SVG template with real values.

    Placeholder tokens in the SVG are substituted in a single pass:
        total-contributions-ph  → formatted total with thousands separator
        current-streak-ph       → current streak in days
        longest-streak-ph       → date range and length of longest streak

    Args:
        svg_content: Raw SVG string containing placeholder tokens.
        stats: Contribution stats to inject.

    Returns:
        SVG string with all placeholders replaced.
    """
    longest_start = format_date(stats["longest_streak_start"])
    longest_end = format_date(stats["longest_streak_end"])

    replacements = {
        "total-contributions-ph": f"{stats['total_contributions']:,}🌟",
        "current-streak-ph": f"{stats['current_streak']}🔥",
        "longest-streak-ph": (
            f"{longest_start} ➝ {longest_end} : {stats['longest_streak']}🏆"
        ),
    }

    result = svg_content
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


# ── Entry Point ────────────────────────────────────────────────────────────────


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
    styles = (
        CARD_STYLES if args.style == "all" else {args.style: CARD_STYLES[args.style]}
    )

    username = os.getenv("GH_USERNAME")
    token = os.getenv("GITHUB_TOKEN")

    if not username:
        logger.error("GH_USERNAME environment variable is required but not set.")
        raise ValueError("Missing GH_USERNAME environment variable.")
    if not token:
        logger.error("GITHUB_TOKEN environment variable is required but not set.")
        raise ValueError("Missing GITHUB_TOKEN environment variable.")

    data = fetch_contributions_from_github(username, token)
    raw = data["contributions"]
    levels = map_contributions_to_levels(raw)
    grid = create_svg_grid_with_heatmap(levels, raw)
    legend = create_svg_legend()

    for style_name, style in styles.items():
        bg_fragment = (
            _read_background_fragment(style.background) if style.background else ""
        )
        for output_file, inject_bg in style.outputs:
            try:
                svg = (ASSETS_DIR / style.template).read_text(encoding="utf-8")
                bg = bg_fragment if inject_bg else ""
                svg = svg.replace("<!-- Background -->", bg)
                svg = svg.replace("<!-- Contribution Grid Legend -->", legend)
                svg = svg.replace("<!-- Contribution Grid -->", grid)
                svg = replace_placeholders_in_svg(svg, data)
                (DOCS_DIR / output_file).write_text(svg, encoding="utf-8")
                logger.info("Written: %s", DOCS_DIR / output_file)
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
