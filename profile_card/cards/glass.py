"""Glass-style profile card. Registers on import."""

from profile_card.cards._shared import (
    CardContext,
    CardStyle,
    common_github_placeholders,
    common_site_placeholders,
    register,
)


def _resolve_placeholders(ctx: CardContext) -> dict[str, str]:
    """Placeholder substitutions for the glass card template."""
    return {
        **common_github_placeholders(ctx.data),
        **common_site_placeholders(ctx.config),
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
        index_template="profile-card.glass.index.template.html",
    ),
)
