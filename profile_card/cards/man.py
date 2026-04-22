"""Man-page-style profile card. Registers on import.

Opts into the Steam prerequisite fetch via `needs_steam=True` and adds an
`extra_markers` entry for heatmap axis labels (unused by the glass card).
"""

from profile_card.cards._shared import (
    CardContext,
    CardStyle,
    common_github_placeholders,
    common_site_placeholders,
    create_svg_grid_labels,
    format_years_active,
    register,
)


def _grid_labels(ctx: CardContext) -> str:
    """Generate heatmap axis labels marker content for the man card."""
    return create_svg_grid_labels(ctx.levels)


def _resolve_placeholders(ctx: CardContext) -> dict[str, str]:
    """Placeholder substitutions for the man-page card template."""
    data = ctx.data
    return {
        **common_github_placeholders(data),
        **common_site_placeholders(ctx.config),
        "{{gh.first}}": data["first_commit"] or "unknown",
        "{{gh.years}}": format_years_active(data["first_commit"]),
        "{{gh.repos}}": str(data["public_repos"]),
        "{{st.game}}": ctx.steam_game,
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
        index_template="profile-card.man-page.index.template.html",
    ),
)
