"""Network fetchers for GitHub contributions and Steam activity.

Owns all external I/O plus the pure processing helpers that operate on fetch
output (`calculate_streaks`, `map_contributions_to_levels`).

Non-obvious invariants:
    - `_SESSION` is shared by every outbound call and retries on 429 + 5xx.
    - GraphQL responses are strictly validated: `errors` or missing `user`
      raises `RuntimeError` (no silent empty cards).
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
STEAM_RECENT_GAMES_URL = (
    "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"
)

CONTRIBUTIONS_START_DATE = datetime(2018, 7, 25, tzinfo=timezone.utc)

# GitHub GraphQL API caps `contributionsCollection` queries to one year.
FETCH_CHUNK_SIZE = timedelta(days=365)

# Also the slice size used when filtering fetched contributions for the heatmap.
HEATMAP_WEEKS = 52

REQUEST_TIMEOUT_SECONDS = 10

# Applied to both GitHub and Steam.
HTTP_RETRY_TOTAL = 3
HTTP_RETRY_BACKOFF = 1.0  # 1s, 2s, 4s between retries
HTTP_RETRY_STATUSES: tuple[int, ...] = (429, 500, 502, 503, 504)

# `repositories.totalCount` is fetched on every chunk but only used from the first.
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


# ── Types ──────────────────────────────────────────────────────────────────────


class ContributionData(TypedDict):
    """Contribution stats returned by `fetch_contributions_from_github`."""

    contributions: dict[str, int]
    total_contributions: int
    current_streak: int
    longest_streak: int
    longest_streak_start: str | None
    longest_streak_end: str | None
    first_commit: str | None
    public_repos: int


class StreakData(TypedDict):
    """Streak stats returned by `calculate_streaks`."""

    current_streak: int
    longest_streak: int
    longest_streak_start: str | None
    longest_streak_end: str | None


# ── HTTP Session ───────────────────────────────────────────────────────────────


def _make_session() -> requests.Session:
    """Build a `requests.Session` that retries 429 + 5xx with exponential backoff.

    POST is retried alongside GET — safe here because the GraphQL query is read-only.
    """
    session = requests.Session()
    retry = Retry(
        total=HTTP_RETRY_TOTAL,
        backoff_factor=HTTP_RETRY_BACKOFF,
        status_forcelist=HTTP_RETRY_STATUSES,
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_SESSION = _make_session()


# ── GitHub ─────────────────────────────────────────────────────────────────────


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
    """Paginate contributions since start date in `FETCH_CHUNK_SIZE` steps.

    Returns `(date → count, public_repos)`. Raises `RuntimeError` on GraphQL
    errors or unexpected payloads so callers don't silently get empty data.
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

        response = _SESSION.post(
            GITHUB_GRAPHQL_URL,
            json={"query": _GRAPHQL_QUERY, "variables": variables},
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()

        if payload.get("errors"):
            raise RuntimeError(f"GraphQL errors: {payload['errors']}")

        user = payload.get("data", {}).get("user")
        if not user:
            raise RuntimeError(f"Unexpected API response: {payload}")

        if public_repos == 0:
            public_repos = user["repositories"]["totalCount"]
        weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
        all_contributions.update(_parse_contribution_days(weeks))

        start = chunk_end

    return all_contributions, public_repos


def fetch_contributions_from_github(username: str, token: str) -> ContributionData:
    """Fetch all contributions, compute streaks + first-commit, slice 52 weeks."""
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
    """Compute current/longest streaks over chronologically sorted dates.

    Today is excluded when it has zero contributions — the day may not be complete.
    """
    today = datetime.now(timezone.utc).date()
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
    """Bucket raw counts into heatmap intensity levels 0–5."""

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


# ── Steam ──────────────────────────────────────────────────────────────────────


def fetch_currently_playing_from_steam(api_key: str, steam_id: str) -> str | None:
    """Return the most-played game in the last two weeks, or None if unavailable.

    Requires the Steam profile's game details to be set to Public.
    """
    try:
        response = _SESSION.get(
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
    except (
        requests.exceptions.RequestException,
        ValueError,
        KeyError,
        IndexError,
    ) as e:
        logger.warning("Steam API request failed: %s", e)
    return None
