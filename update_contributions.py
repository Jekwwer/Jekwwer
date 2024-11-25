"""A script to fetch GitHub data, calculate streaks, and generate a heatmap grid."""

import os
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import requests


class ContributionData(TypedDict):
    """Type definition for contribution data.

    Attributes:
        contributions (dict[str, int]): Contribution counts by date.
        total_contributions (int): Total contributions.
        current_streak (int): Current streak.
        longest_streak (int): Longest streak.
    """
    contributions: dict[str, int]
    total_contributions: int
    current_streak: int
    longest_streak: int


# Define contribution levels and corresponding colors
contribution_colors = {
    0: '#363a4f',   # No contributions
    1: '#ee99a0',   # 1-5 contributions
    2: '#f5a97f',   # 6-10 contributions
    3: '#eed49f',   # 11-15 contributions
    4: '#a6da95',   # 16+ contributions
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
    url = 'https://api.github.com/graphql'
    headers = {'Authorization': f"Bearer {token}"}
    query = '''
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
    '''

    # Start date for contributions (adjust to your earliest contribution date)
    start_date = datetime(2018, 7, 25, tzinfo=timezone.utc)
    end_date = datetime.now(timezone.utc)
    one_year = timedelta(days=365)

    # Fetch contributions year by year
    while start_date < end_date:
        chunk_end_date = min(start_date + one_year, end_date)
        variables = {
            'username': username,
            'from': start_date.isoformat(),
            'to': chunk_end_date.isoformat()
        }

        response = requests.post(
            url,
            json={'query': query, 'variables': variables},
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'].get('user'):
                calendar = data['data']['user'][
                    'contributionsCollection']['contributionCalendar']
                weeks = calendar.get('weeks', [])

                for week in weeks:
                    for day in week.get('contributionDays', []):
                        date_str = day.get('date')
                        contribution_count = day.get('contributionCount', 0)
                        if date_str and isinstance(contribution_count, int):
                            all_contributions[date_str] = contribution_count
            else:
                print('Error in API response:', data)
        else:
            print(f"Failed to fetch data: {response.status_code}, {response.text}")

        # Move to the next year
        start_date = chunk_end_date

    # Filter contributions for the last 52 weeks
    last_52_weeks_start = (
        datetime.now(timezone.utc).date() - timedelta(weeks=52)).isoformat()
    contributions_last_year = {
        date: count for date,
        count in all_contributions.items() if date >= last_52_weeks_start}

    streaks = calculate_streaks(all_contributions)

    return {
        'contributions': contributions_last_year,  # Last 52 weeks for the heatmap
        'total_contributions': sum(all_contributions.values()),
        'current_streak': streaks['current_streak'],
        'longest_streak': streaks['longest_streak'],
    }


def calculate_streaks(contributions: dict[str, int]) -> dict[str, int]:
    """Calculate the current and longest streaks from contribution data.

    Args:
        contributions (dict[str, int]): Contribution counts by date.

    Returns:
        dict[str, int]: Current and longest streaks.
    """
    sorted_dates = sorted(contributions.keys(), key=lambda x: datetime.fromisoformat(x))
    current_streak = 0
    longest_streak = 0
    streak = 0
    # Updated to use timezone-aware UTC datetime
    today = datetime.now(timezone.utc).date()

    for i, date_str in enumerate(sorted_dates):
        date = datetime.fromisoformat(date_str).date()
        if contributions[date_str] > 0:
            # Start or continue a streak
            if i == 0 or (
                date - datetime.fromisoformat(sorted_dates[i - 1]).date()
            ) == timedelta(days=1):
                streak += 1
            else:
                # Reset streak if not consecutive
                streak = 1
            longest_streak = max(longest_streak, streak)

            # Check if this is part of the current streak
            if date == today or (i > 0 and datetime.fromisoformat(
                    sorted_dates[i - 1]).date() == today - timedelta(days=1)):
                current_streak = streak
        else:
            streak = 0

    return {'current_streak': current_streak, 'longest_streak': longest_streak}


def map_contributions_to_levels(contributions: dict[str, int]) -> dict[str, int]:
    """Map raw contribution counts to predefined levels.

    Args:
        contributions (dict[str, int]): Raw contribution counts by date.

    Returns:
        dict[str, int]: Mapped contribution levels by date.
    """
    mapped = {}
    for date, count in contributions.items():
        if count == 0:
            level = 0
        elif count <= 5:
            level = 1
        elif count <= 10:
            level = 2
        elif count <= 15:
            level = 3
        else:
            level = 4
        mapped[date] = level
    return mapped


def calculate_cell_dimensions(grid_width: int, weeks: int = 52,
                              days: int = 7) -> tuple[float, float]:
    """Calculate dimensions for heatmap cells.

    Args:
        grid_width (int): Width of the grid in pixels.
        weeks (int): Number of weeks (columns).
        days (int): Number of days (rows).

    Returns:
        tuple[float, float]: Cell size and spacing.
    """
    total_spacing = grid_width * 0.1  # Total spacing allocated for gaps
    effective_width = grid_width - total_spacing  # Remaining width for cells
    cell_size = effective_width / weeks
    cell_spacing = grid_width * 0.1 / (weeks - 1)
    return round(cell_size, 2), round(cell_spacing, 2)


def create_svg_grid_with_heatmap(contributions: dict[str, int],
                                 grid_width: int = 794) -> str:
    """Generate SVG heatmap grid from contribution levels.

    Args:
        contributions (dict[str, int]): Contribution levels by date.
        grid_width (int): Width of the grid in pixels.

    Returns:
        str: SVG markup for the heatmap grid.
    """
    svg_parts = []
    svg_parts.append('<!-- Contribution Grid -->')
    svg_parts.append('<g transform="translate(50, 520)">')

    # Trim contributions to 364 entries
    trimmed_contributions = list(contributions.items())[1:]

    cell_size, cell_spacing = calculate_cell_dimensions(grid_width)
    x, y = 0.0, 0.0

    for index, (date, level) in enumerate(trimmed_contributions):
        color = contribution_colors.get(level, '#363a4f')
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" '
            f'rx="2" fill="{color}" title="{date}: {level} contributions"/>'
        )
        y += cell_size + cell_spacing

        if (index + 1) % 7 == 0:  # Start a new column after 7 days
            y = 0
            x += cell_size + cell_spacing

    svg_parts.append('</g>')
    return '\n'.join(svg_parts)


def replace_placeholders_in_svg(svg_content: str, stats: dict[str, int]) -> str:
    """Replace placeholders in the SVG file with the fetched statistics.

    Args:
        svg_content (str): SVG content with placeholders.
        stats (dict[str, int]): Fetched statistics.

    Returns:
        str: SVG content with placeholders replaced by statistics.
    """
    updated_svg = svg_content
    updated_svg = updated_svg.replace(
        'total-contributions-ph', str(stats['total_contributions'])
    )
    updated_svg = updated_svg.replace(
        'current-streak-ph', str(stats['current_streak'])
    )
    updated_svg = updated_svg.replace(
        'longest-streak-ph', str(stats['longest_streak'])
    )
    return updated_svg


def main() -> None:
    """Main function to fetch contributions and update SVG files."""
    username = 'jekwwer'
    token = os.getenv('GITHUB_TOKEN', 'default_token')

    # Fetch contributions and stats
    data = fetch_contributions_from_github(username, token)
    raw_contributions = data['contributions']
    stats: dict[str, int] = {
        'total_contributions': data['total_contributions'],
        'current_streak': data['current_streak'],
        'longest_streak': data['longest_streak'],
    }

    contributions = map_contributions_to_levels(raw_contributions)
    contribution_grid = create_svg_grid_with_heatmap(contributions)

    # Read and update the SVG files
    for file_name, updated_file_name in [
        ('profile-card.svg', 'profile-card-latest.svg'),
        ('profile-card-no-bg.svg', 'profile-card-no-bg-latest.svg')
    ]:
        with open(f'assets/{file_name}', 'r', encoding='utf-8') as svg_file:
            original_svg = svg_file.read()

        # Insert the contribution grid and replace placeholders
        updated_svg = original_svg.replace(
            '<!-- Contribution Grid -->', contribution_grid
        )
        updated_svg = replace_placeholders_in_svg(updated_svg, stats)

        # Save the updated SVG
        with open(
            f'assets/{updated_file_name}', 'w', encoding='utf-8'
        ) as updated_svg_file:
            updated_svg_file.write(updated_svg)


if __name__ == '__main__':
    main()
