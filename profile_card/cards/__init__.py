"""Card registry.

Each card module is imported here for its side effect: at import time the
module calls `register(...)` which populates `CARD_STYLES`. See
CONTRIBUTING.md for adding a new style.
"""

from profile_card.cards import (
    glass,  # noqa: F401 - side-effect import populates CARD_STYLES
    man,  # noqa: F401 - side-effect import populates CARD_STYLES
)
from profile_card.cards._shared import (
    CARD_STYLES,
    CardContext,
    CardStyle,
    create_svg_grid_with_heatmap,
    create_svg_legend,
    read_background_fragment,
)

__all__ = [
    "CARD_STYLES",
    "CardContext",
    "CardStyle",
    "create_svg_grid_with_heatmap",
    "create_svg_legend",
    "read_background_fragment",
]
