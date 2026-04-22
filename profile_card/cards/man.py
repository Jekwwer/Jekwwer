"""Man-page-style profile card. Registers on import.

Opts into the Steam prerequisite fetch via `needs_steam=True` and adds an
`extra_markers` entry for heatmap axis labels (unused by the glass card).
"""

from profile_card.cards._shared import (
    CardContext,
    CardStyle,
    create_svg_grid_labels,
    format_date,
    format_years_active,
    register,
)


def _grid_labels(ctx: CardContext) -> str:
    """Generate heatmap axis labels marker content for the man card."""
    return create_svg_grid_labels(ctx.levels)


def _resolve_placeholders(ctx: CardContext) -> dict[str, str]:
    """Placeholder substitutions for the man-page card template."""
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
        "years-active-ph": format_years_active(first),
        "repos-ph": str(data["public_repos"]),
        "currently-playing-ph": ctx.steam_game,
        "steam-id-ph": ctx.steam_id,
    }


register(
    "man",
    CardStyle(
        template="profile-card.man-page.template.svg",
        outputs=[
            ("profile-card.man-page.svg", True),
            ("profile-card.man-page-no-background.svg", False),
        ],
        background="background.man-page.svg",
        subdir="man",
        resolver=_resolve_placeholders,
        extra_markers={"<!-- Contribution Grid Labels -->": _grid_labels},
        needs_steam=True,
    ),
)
