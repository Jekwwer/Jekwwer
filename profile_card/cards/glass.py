"""Glass-style profile card. Registers on import."""

from profile_card.cards._shared import CardContext, CardStyle, format_date, register


def _resolve_placeholders(ctx: CardContext) -> dict[str, str]:
    """Placeholder substitutions for the glass card template."""
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


register(
    "glass",
    CardStyle(
        template="profile-card.glass.template.svg",
        outputs=[
            ("profile-card.glass.svg", True),
            ("profile-card.glass-no-background.svg", False),
        ],
        background="background.glass.svg",
        subdir="glass",
        resolver=_resolve_placeholders,
    ),
)
