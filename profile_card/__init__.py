"""Top-level re-exports for the CLI entry point. See `__all__` for the surface."""

from profile_card.cards import (
    CARD_STYLES,
    CardContext,
    CardStyle,
    create_svg_grid_with_heatmap,
    create_svg_legend,
    read_background_fragment,
)
from profile_card.fetchers import (
    fetch_contributions_from_github,
    fetch_currently_playing_from_steam,
    map_contributions_to_levels,
)

__all__ = [
    "CARD_STYLES",
    "CardContext",
    "CardStyle",
    "create_svg_grid_with_heatmap",
    "create_svg_legend",
    "fetch_contributions_from_github",
    "fetch_currently_playing_from_steam",
    "map_contributions_to_levels",
    "read_background_fragment",
]
