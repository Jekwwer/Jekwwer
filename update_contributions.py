"""A script to fetch GitHub data, calculate streaks, and generate a heatmap grid."""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, TypedDict

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ContributionData(TypedDict):
    """Type definition for contribution data.

    Attributes:
        contributions (dict[str, int]): Contribution counts by date.
        total_contributions (int): Total contributions.
        current_streak (int): Current streak.
        longest_streak (int): Longest streak.
        longest_streak_start (str | None): Start date of the longest streak.
        longest_streak_end (str | None): End date of the longest streak.
    """

    contributions: dict[str, int]
    total_contributions: int
    current_streak: int
    longest_streak: int
    longest_streak_start: str | None
    longest_streak_end: str | None


# Define contribution levels and corresponding colors for the heatmap (defined in CSS)
contribution_colors = {
    0: "no_contribution",  # No contributions
    1: "contribution_1_10",  # 1-10 contributions
    2: "contribution_11_20",  # 11-20 contributions
    3: "contribution_21_30",  # 21-30 contributions
    4: "contribution_31_49",  # 31-49 contributions
    5: "contribution_50",  # 50+ contributions
}


def fetch_contributions_from_github(username: str, token: str) -> ContributionData:
    """Fetch contribution data for a GitHub user using the GitHub GraphQL API.

    Args:
        username (str): GitHub username.
        token (str): GitHub personal access token.

    Returns:
        ContributionData: A dictionary with contribution stats.
    """
    all_contributions: dict[str, int] = {}
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}"}
    query = """
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

    # Start date for contributions (adjust to your earliest contribution date)
    start_date = datetime(2018, 7, 25, tzinfo=timezone.utc)
    end_date = datetime.now(timezone.utc)
    one_year = timedelta(days=365)

    logger.info("Fetching contributions for user '%s'", username)

    # Fetch contributions year by year
    while start_date < end_date:
        chunk_end_date = min(start_date + one_year, end_date)
        variables = {
            "username": username,
            "from": start_date.isoformat(),
            "to": chunk_end_date.isoformat(),
        }

        logger.debug(
            "Fetching contributions from %s to %s",
            start_date.isoformat(),
            chunk_end_date.isoformat(),
        )

        try:
            response = requests.post(
                url,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            if "data" in data and data["data"].get("user"):
                calendar = data["data"]["user"]["contributionsCollection"][
                    "contributionCalendar"
                ]
                weeks = calendar.get("weeks", [])

                for week in weeks:
                    for day in week.get("contributionDays", []):
                        date_str = day.get("date")
                        contribution_count = day.get("contributionCount", 0)
                        if date_str and isinstance(contribution_count, int):
                            all_contributions[date_str] = contribution_count
            else:
                logger.error("Error in API response: %s", data)
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch data: %s", e)

        # Move to the next year
        start_date = chunk_end_date

    # Filter contributions for the last 52 weeks
    last_52_weeks_start = (
        datetime.now(timezone.utc).date() - timedelta(weeks=52)
    ).isoformat()
    contributions_last_year = {
        date: count
        for date, count in all_contributions.items()
        if date >= last_52_weeks_start
    }

    streaks = calculate_streaks(all_contributions)

    logger.info("Fetched total contributions: %d", sum(all_contributions.values()))
    logger.info(
        "Current streak: %d, Longest streak: %d",
        streaks["current_streak"],
        streaks["longest_streak"],
    )

    return {
        "contributions": contributions_last_year,  # Last 52 weeks for the heatmap
        "total_contributions": sum(all_contributions.values()),
        "current_streak": streaks["current_streak"],
        "longest_streak": streaks["longest_streak"],
        "longest_streak_start": streaks.get("longest_streak_start"),
        "longest_streak_end": streaks.get("longest_streak_end"),
    }


def calculate_streaks(contributions: dict[str, int]) -> dict[str, Any]:
    """Calculate the current and longest streaks with dates, from contribution data.

    Args:
        contributions (dict[str, int]): Contribution counts by date.

    Returns:
        dict[str, Any]: Current streak, longest streak, and their respective dates.
    """
    logger.info("Calculating streaks...")
    sorted_dates = sorted(contributions.keys(), key=lambda x: datetime.fromisoformat(x))
    current_streak = 0
    longest_streak = 0
    longest_streak_start = None
    longest_streak_end = None
    streak_start = None

    for _, date_str in enumerate(sorted_dates):
        date = datetime.fromisoformat(date_str).date()
        if contributions[date_str] > 0:  # Active streak
            if current_streak == 0:
                streak_start = date  # Start a new streak
                logger.debug("New streak started on %s", streak_start)

            current_streak += 1
            logger.debug("Current streak incremented to %d on %s", current_streak, date)

            # Update longest streak
            if current_streak > longest_streak:
                longest_streak = current_streak
                longest_streak_start = streak_start
                longest_streak_end = date
                logger.info(
                    "Longest streak updated: %d days from %s to %s",
                    longest_streak,
                    longest_streak_start,
                    longest_streak_end,
                )
        else:  # No contributions; reset current streak
            if current_streak > 0:
                logger.debug("Streak ended on %s", date)
            current_streak = 0
            streak_start = None

    logger.info("Streak calculation complete.")
    logger.info(
        "Current streak: %d days, Longest streak: %d days (from %s to %s)",
        current_streak,
        longest_streak,
        longest_streak_start.isoformat() if longest_streak_start else "N/A",
        longest_streak_end.isoformat() if longest_streak_end else "N/A",
    )

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "longest_streak_start": longest_streak_start.isoformat()
        if longest_streak_start
        else None,
        "longest_streak_end": longest_streak_end.isoformat()
        if longest_streak_end
        else None,
    }


def map_contributions_to_levels(contributions: dict[str, int]) -> dict[str, int]:
    """Map raw contribution counts to predefined levels.

    Args:
        contributions (dict[str, int]): Raw contribution counts by date.

    Returns:
        dict[str, int]: Mapped contribution levels by date.
    """
    logger.info("Mapping contribution counts to levels...")
    mapped = {}
    for date, count in contributions.items():
        if count == 0:
            level = 0
        elif count <= 10:
            level = 1
        elif count <= 20:
            level = 2
        elif count <= 30:
            level = 3
        elif count <= 49:
            level = 4
        else:
            level = 5
        mapped[date] = level
        logger.debug("Date: %s, Count: %d, Level: %d", date, count, level)

    logger.info(
        "Completed mapping contributions to levels. Total dates mapped: %d", len(mapped)
    )
    return mapped


def calculate_cell_dimensions(
    grid_width: int, weeks: int = 52, days: int = 7
) -> tuple[float, float]:
    """Calculate dimensions for heatmap cells.

    Args:
        grid_width (int): Width of the grid in pixels.
        weeks (int): Number of weeks (columns).
        days (int): Number of days (rows).

    Returns:
        tuple[float, float]: Cell size and spacing.
    """
    logger.info("Calculating cell dimensions for the heatmap grid...")
    total_spacing = grid_width * 0.1  # Total spacing allocated for gaps
    effective_width = grid_width - total_spacing  # Remaining width for cells
    cell_size = effective_width / weeks
    cell_spacing = grid_width * 0.1 / (weeks - 1)

    logger.debug(
        "Grid width: %d, Total spacing: %f, Effective width: %f",
        grid_width,
        total_spacing,
        effective_width,
    )
    logger.debug("Calculated cell size: %f, Cell spacing: %f", cell_size, cell_spacing)

    logger.info("Cell dimensions calculated successfully.")
    return round(cell_size, 2), round(cell_spacing, 2)


def create_svg_grid_with_heatmap(
    contributions: dict[str, int], grid_width: int = 794
) -> str:
    """Generate SVG heatmap grid from contribution levels.

    Args:
        contributions (dict[str, int]): Contribution levels by date.
        grid_width (int): Width of the grid in pixels.

    Returns:
        str: SVG markup for the heatmap grid.
    """
    logger.info("Generating SVG heatmap grid...")
    svg_parts = []
    svg_parts.append("<!-- Contribution Grid -->")
    svg_parts.append('<g transform="translate(50, 520)">')

    # Trim contributions to 364 entries (last 52 weeks + 1 day)
    trimmed_contributions = list(contributions.items())[1:]
    logger.debug(
        "Trimmed contributions to %d entries for the grid.", len(trimmed_contributions)
    )

    cell_size, cell_spacing = calculate_cell_dimensions(grid_width)
    logger.debug("Calculated cell size: %f, cell spacing: %f", cell_size, cell_spacing)

    x, y = 0.0, 0.0

    for index, (date, level) in enumerate(trimmed_contributions):
        color = contribution_colors.get(level, "#363a4f")
        svg_parts.append(
            f'<rect class="grid-cell" x="{x}" y="{y}" width="{cell_size}" '
            f'height="{cell_size}" fill="url(#{color})" stroke="url(#{color}_stroke)" '
            f'rx="2" title="{date}: {level} contributions"/>'
        )
        logger.debug("Added grid cell: Date=%s, Level=%d, Color=%s", date, level, color)

        y += cell_size + cell_spacing

        if (index + 1) % 7 == 0:  # Start a new column after 7 days
            y = 0
            x += cell_size + cell_spacing

    svg_parts.append("</g>")
    logger.info(
        "SVG grid generation complete with %d cells.", len(trimmed_contributions)
    )
    return "\n".join(svg_parts)


def replace_placeholders_in_svg(svg_content: str, stats: dict[str, Any]) -> str:
    """Replace placeholders in the SVG file with the fetched statistics.

    Args:
        svg_content (str): SVG content with placeholders.
        stats (dict[str, Any]): Fetched statistics.

    Returns:
        str: SVG content with placeholders replaced by statistics.
    """
    logger.info("Replacing placeholders in SVG content...")

    # Format dates as YYYY/MM/DD instead of YYYY-MM-DD
    def format_date(date_value: Optional[str]) -> str:
        """Convert YYYY-MM-DD to YYYY/MM/DD or return 'N/A' if None."""
        if isinstance(date_value, str):
            return date_value.replace("-", "/")
        return "N/A"  # Handle None and other invalid cases

    longest_streak_start = format_date(stats.get("longest_streak_start"))
    longest_streak_end = format_date(stats.get("longest_streak_end"))

    # Format longest streak with date range
    longest_streak_text = (
        f"{longest_streak_start} ➝ {longest_streak_end} : {stats['longest_streak']}🏆"
    )
    logger.debug("Formatted longest streak text: %s", longest_streak_text)

    # Format numbers with thousand separators
    total_contributions = f"{stats['total_contributions']:,}🌟"
    current_streak = f"{stats['current_streak']}🔥"

    logger.debug("Formatted total contributions: %s", total_contributions)
    logger.debug("Formatted current streak: %s", current_streak)

    # Replace placeholders in the SVG content
    updated_svg = svg_content.replace("total-contributions-ph", total_contributions)
    updated_svg = updated_svg.replace("current-streak-ph", current_streak)
    updated_svg = updated_svg.replace("longest-streak-ph", longest_streak_text)

    logger.info("SVG placeholders replaced successfully.")
    return updated_svg


def main() -> None:
    """Main function to fetch contributions and update SVG files."""
    logger.info("Starting the main process...")

    # Fetch environment variables
    username = os.getenv("USERNAME", "default_username")
    token = os.getenv("GITHUB_TOKEN")

    # Ensure the token is provided
    if not token:
        logger.error("GITHUB_TOKEN environment variable is required but not set.")
        raise ValueError("Missing GITHUB_TOKEN environment variable.")

    logger.debug("Environment variables - USERNAME: %s, GITHUB_TOKEN: ******", username)

    # Fetch contributions and stats
    logger.info("Fetching contributions for user: %s", username)
    data = fetch_contributions_from_github(username, token)

    raw_contributions = data["contributions"]
    stats: dict[str, Any] = {
        "total_contributions": data["total_contributions"],
        "current_streak": data["current_streak"],
        "longest_streak": data["longest_streak"],
        "longest_streak_start": data.get("longest_streak_start"),
        "longest_streak_end": data.get("longest_streak_end"),
    }

    logger.info("Fetched contribution stats: %s", stats)

    # Map contributions to levels and generate the grid
    logger.info("Mapping contributions to levels...")
    contributions = map_contributions_to_levels(raw_contributions)

    logger.info("Generating SVG contribution grid...")
    contribution_grid = create_svg_grid_with_heatmap(contributions)

    # Read, update, and save SVG files
    file_pairs = [
        ("profile-card.svg", "profile-card-latest.svg"),
        ("profile-card-no-bg.svg", "profile-card-no-bg-latest.svg"),
    ]
    for file_name, updated_file_name in file_pairs:
        logger.info("Processing file: %s", file_name)

        try:
            with open(f"assets/{file_name}", encoding="utf-8") as svg_file:
                original_svg = svg_file.read()
            logger.debug("Read file: assets/%s", file_name)

            # Insert the contribution grid and replace placeholders
            updated_svg = original_svg.replace(
                "<!-- Contribution Grid -->", contribution_grid
            )
            updated_svg = replace_placeholders_in_svg(updated_svg, stats)

            # Save the updated SVG
            with open(
                f"assets/{updated_file_name}", "w", encoding="utf-8"
            ) as updated_svg_file:
                updated_svg_file.write(updated_svg)
            logger.info("Updated file saved: assets/%s", updated_file_name)
        except Exception as e:
            logger.error("Error processing file %s: %s", file_name, e)

    logger.info("Main process completed successfully.")


if __name__ == "__main__":
    logger.info("Script execution started.")
    try:
        main()
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
    logger.info("Script execution finished.")
