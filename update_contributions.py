"""GitHub contribution heatmap generator.

Fetches contribution data from the GitHub GraphQL API, calculates streaks,
and writes updated SVG profile cards to the assets/ directory.

Pipeline:
    1. _fetch_all_contributions      — paginate GitHub GraphQL year by year.
    2. calculate_streaks             — compute current/longest streak with dates.
    3. map_contributions_to_levels   — map raw counts to 6 heatmap intensity levels.
    4. create_svg_grid_with_heatmap  — render a 52×7 SVG <rect> grid.
    5. replace_placeholders_in_svg   — inject stats into SVG text-node placeholders.
    6. main                          — orchestrate and write output files.

Required environment variables:
    USERNAME     — GitHub username.
    GITHUB_TOKEN — Personal access token with read:user scope.
"""

import logging
import os
import sys
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

ASSETS_DIR = Path("assets")
SVG_FILE_PAIRS: list[tuple[str, str]] = [
    ("profile-card.svg", "profile-card-latest.svg"),
    ("profile-card-no-bg.svg", "profile-card-no-bg-latest.svg"),
]

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

# CSS class names referenced by the SVG templates, keyed by intensity level (0–5).
CONTRIBUTION_COLORS = {
    0: "no_contribution",
    1: "contribution_1_10",
    2: "contribution_11_20",
    3: "contribution_21_30",
    4: "contribution_31_49",
    5: "contribution_50",
}

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
    sorted_dates = sorted(contributions.keys(), key=lambda d: datetime.fromisoformat(d))

    current_streak = 0
    longest_streak = 0
    longest_streak_start = None
    longest_streak_end = None
    streak_start = None

    for date_str in sorted_dates:
        date = datetime.fromisoformat(date_str).date()

        if contributions[date_str] > 0:
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
    contributions: dict[str, int], grid_width: int = 794
) -> str:
    """Render the contribution heatmap as an SVG <g> element.

    Produces HEATMAP_CELLS <rect> elements arranged in a 52-column × 7-row grid,
    with CSS class and fill references matching the SVG template's style definitions.

    Args:
        contributions: Dict mapping ISO date strings to intensity levels (0–5).
        grid_width: Total grid width in pixels.

    Returns:
        SVG markup string, including the opening <!-- Contribution Grid --> marker.
    """
    cell_size, cell_spacing = calculate_cell_dimensions(grid_width)

    # Take the most recent HEATMAP_CELLS entries so the grid is always full.
    entries = list(contributions.items())[-HEATMAP_CELLS:]

    svg_parts = [
        "<!-- Contribution Grid -->",
        '<g transform="translate(50, 520)">',
    ]

    x, y = 0.0, 0.0
    for index, (date, level) in enumerate(entries):
        color = CONTRIBUTION_COLORS.get(level, "#363a4f")
        svg_parts.append(
            f'<rect class="grid-cell" x="{x}" y="{y}" '
            f'width="{cell_size}" height="{cell_size}" '
            f'fill="url(#{color})" stroke="url(#{color}_stroke)" '
            f'rx="2" title="{date}: {level} contributions"/>'
        )
        y += cell_size + cell_spacing
        if (index + 1) % HEATMAP_DAYS_PER_WEEK == 0:
            y = 0.0
            x += cell_size + cell_spacing

    svg_parts.append("</g>")
    logger.info("SVG grid generated: %d cells", len(entries))
    return "\n".join(svg_parts)


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
    username = os.getenv("USERNAME")
    token = os.getenv("GITHUB_TOKEN")

    if not username:
        logger.error("USERNAME environment variable is required but not set.")
        raise ValueError("Missing USERNAME environment variable.")
    if not token:
        logger.error("GITHUB_TOKEN environment variable is required but not set.")
        raise ValueError("Missing GITHUB_TOKEN environment variable.")

    data = fetch_contributions_from_github(username, token)
    contributions = map_contributions_to_levels(data["contributions"])
    grid = create_svg_grid_with_heatmap(contributions)

    for template_file, output_file in SVG_FILE_PAIRS:
        try:
            svg = (ASSETS_DIR / template_file).read_text(encoding="utf-8")
            svg = svg.replace("<!-- Contribution Grid -->", grid)
            svg = replace_placeholders_in_svg(svg, data)
            (ASSETS_DIR / output_file).write_text(svg, encoding="utf-8")
            logger.info("Written: %s", ASSETS_DIR / output_file)
        except Exception as e:
            logger.error("Failed to process %s: %s", template_file, e)
            raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)
