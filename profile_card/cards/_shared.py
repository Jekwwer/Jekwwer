"""Shared foundation for card modules.

Holds `CardContext`, `CardStyle`, the `CARD_STYLES` registry + `register()`,
the cross-card SVG generators, and small formatting helpers. Card modules
import from here.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from profile_card.config import Config
from profile_card.fetchers import HEATMAP_WEEKS, ContributionData

# ── Heatmap / Legend Constants ─────────────────────────────────────────────────

HEATMAP_DAYS_PER_WEEK = 7
HEATMAP_CELLS = HEATMAP_WEEKS * HEATMAP_DAYS_PER_WEEK  # 364

# Fraction of total grid width reserved for gaps between columns.
GRID_SPACING_RATIO = 0.1

# Gradient IDs referenced by SVG templates, keyed by intensity level (0–5).
# Stroke IDs always follow the pattern f"{color_id}-stroke".
CONTRIBUTION_COLORS = {
    0: "heat-lvl-0",
    1: "heat-lvl-1",
    2: "heat-lvl-2",
    3: "heat-lvl-3",
    4: "heat-lvl-4",
    5: "heat-lvl-5",
}

MONTH_ABBR: list[str] = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

# Day-of-week indices (Monday=0) to render as row labels in the heatmap.
HEATMAP_ROW_LABELS: list[tuple[int, str]] = [(0, "Mon"), (2, "Wed"), (4, "Fri")]

LEGEND_LABELS: dict[int, str] = {
    0: "0: Burnout / Sleep / Love / Death / Vacay — Who knows! ( ͡° ͜ʖ ͡°)",
    1: "1–10",
    2: "11–20",
    3: "21–30",
    4: "31–49",
    5: "50+",
}

# Legend layout constants (px). Derived from calculate_cell_dimensions(794) output
# and empirically measured label widths at 10 px font-size.
LEGEND_TEXT_OFFSET_X = 20  # cell left edge → label x
LEGEND_TEXT_OFFSET_Y = 12  # cell top → text baseline
LEGEND_LONG_ITEM_WIDTH = 321.3  # width of level-0 item (cell + long label + gap)
LEGEND_SHORT_ITEM_WIDTH = 61.2  # width of each subsequent item (cell + short label)


# ── Dataclasses ────────────────────────────────────────────────────────────────


@dataclass
class CardContext:
    """Shared state passed to per-card resolvers and marker generators.

    Attributes:
        data: Contribution stats from GitHub.
        levels: ISO date → intensity level (0–5) mapping.
        raw_counts: ISO date → raw contribution count mapping.
        config: Public runtime config (user identity, links, Steam ID).
        steam_game: Most-played Steam game name, or `"nothing"` if unavailable.
    """

    data: ContributionData
    levels: dict[str, int]
    raw_counts: dict[str, int]
    config: Config
    steam_game: str = "nothing"


@dataclass
class CardStyle:
    """Configuration for a single profile card style.

    Attributes:
        template: SVG template filename relative to `ASSETS_DIR`.
        outputs: `(output_filename, inject_background)` pairs written to
            `DOCS_DIR / subdir`.
        resolver: Callable returning `{placeholder: value}` for this style.
        background: Background SVG filename in the style subdir; empty if unused.
        subdir: Subdirectory under `DOCS_DIR` for outputs and background.
        extra_markers: `{marker_comment: callable}` for style-specific SVG
            injections beyond the shared Grid + Legend markers.
        needs_steam: Whether this style's resolver reads Steam data from the
            context. `main()` skips the Steam API call when no active style
            has this set.
    """

    template: str
    outputs: list[tuple[str, bool]]
    resolver: Callable[[CardContext], dict[str, str]]
    background: str = ""
    subdir: str = ""
    extra_markers: dict[str, Callable[[CardContext], str]] = field(default_factory=dict)
    needs_steam: bool = False


# ── Registry ───────────────────────────────────────────────────────────────────

CARD_STYLES: dict[str, CardStyle] = {}


def register(name: str, style: CardStyle) -> None:
    """Add `style` to `CARD_STYLES` under `name`; raise `ValueError` on duplicate."""
    if name in CARD_STYLES:
        raise ValueError(f"Card style '{name}' is already registered.")
    CARD_STYLES[name] = style


# ── Helpers ────────────────────────────────────────────────────────────────────


def format_date(date_value: str | None) -> str:
    """Convert an ISO date string to `YYYY/MM/DD`, or return `"N/A"` if None."""
    if isinstance(date_value, str):
        return date_value.replace("-", "/")
    return "N/A"


def format_years_active(first_commit: str | None) -> str:
    """Format elapsed time since `first_commit` as `<N> yr[s] [<M> mo]`."""
    if not first_commit:
        return "unknown"
    today = datetime.now(timezone.utc).date()
    delta = today - datetime.fromisoformat(first_commit).date()
    yrs, rem = divmod(delta.days, 365)
    mos = rem // 30
    if yrs and mos:
        return f"{yrs} yr{'s' if yrs != 1 else ''} {mos} mo"
    if yrs:
        return f"{yrs} yr{'s' if yrs != 1 else ''}"
    return f"{mos} mo"


def common_github_placeholders(data: ContributionData) -> dict[str, str]:
    """Atomic GitHub placeholders every card reads from ContributionData."""
    return {
        "{{gh.total}}": f"{data['total_contributions']:,}🌟",
        "{{gh.streak}}": f"{data['current_streak']}🔥",
        "{{gh.longest.count}}": f"{data['longest_streak']}🏆",
        "{{gh.longest.from}}": format_date(data["longest_streak_start"]),
        "{{gh.longest.to}}": format_date(data["longest_streak_end"]),
    }


def common_site_placeholders(config: Config) -> dict[str, str]:
    """Atomic placeholders sourced from `config.json` (user + links + Steam ID)."""
    name = config["user"]["name"]
    result: dict[str, str] = {
        "{{user.name}}": name,
        "{{user.name.upper}}": name.upper(),
        "{{user.name.title}}": name.title(),
        "{{user.display}}": config["user"]["display"],
        "{{st.id}}": config["steam_id"],
    }
    for key, link in config["links"].items():
        result[f"{{{{link.{key}.url}}}}"] = link["url"]
        result[f"{{{{link.{key}.display}}}}"] = link["display"]
    return result


def read_background_fragment(style_dir: Path, bg_file: str) -> str:
    """Return a background SVG's inner content (outer `<svg>` wrapper stripped).

    Secondary `<defs>` and `<style>` blocks remain valid once inlined.
    """
    raw = (style_dir / bg_file).read_text(encoding="utf-8")
    start = raw.index(">") + 1
    end = raw.rindex("<")
    return raw[start:end].strip()


# ── SVG Generators (shared across cards) ──────────────────────────────────────


def calculate_cell_dimensions(
    grid_width: int, weeks: int = HEATMAP_WEEKS
) -> tuple[float, float]:
    """Return `(cell_size, cell_spacing)` fitting `weeks` columns in `grid_width`."""
    gap_total = grid_width * GRID_SPACING_RATIO
    cell_size = (grid_width - gap_total) / weeks
    cell_spacing = gap_total / (weeks - 1)
    return round(cell_size, 2), round(cell_spacing, 2)


def create_svg_grid_with_heatmap(
    levels: dict[str, int],
    raw_counts: dict[str, int],
    grid_width: int = 794,
) -> str:
    """Render the heatmap as `<rect>` elements preceded by the Grid marker comment."""
    cell_size, cell_spacing = calculate_cell_dimensions(grid_width)

    entries = list(levels.items())[-HEATMAP_CELLS:]
    svg_parts = ["<!-- Contribution Grid -->"]

    x, y = 0.0, 0.0
    for index, (date, level) in enumerate(entries):
        color = CONTRIBUTION_COLORS[level]
        count = raw_counts.get(date, 0)
        svg_parts.append(
            f'<rect class="grid-cell" x="{x}" y="{y}" '
            f'width="{cell_size}" height="{cell_size}" '
            f'fill="url(#{color})" stroke="url(#{color}-stroke)" '
            f'rx="2" title="{date}: {count}"/>'
        )
        y += cell_size + cell_spacing
        if (index + 1) % HEATMAP_DAYS_PER_WEEK == 0:
            y = 0.0
            x += cell_size + cell_spacing

    return "\n".join(svg_parts)


def create_svg_legend(grid_width: int = 794) -> str:
    """Render the colour-scale legend; `grid_width` must match the grid's."""
    cell_size, _ = calculate_cell_dimensions(grid_width)

    parts = ["<!-- Contribution Grid Legend -->"]
    for level, label in LEGEND_LABELS.items():
        x = (
            0.0
            if level == 0
            else round(
                LEGEND_LONG_ITEM_WIDTH + (level - 1) * LEGEND_SHORT_ITEM_WIDTH, 1
            )
        )
        color_id = CONTRIBUTION_COLORS[level]
        parts.append(
            f'<rect x="{x}" y="0" width="{cell_size}" height="{cell_size}" '
            f'fill="url(#{color_id})" stroke="url(#{color_id}-stroke)" rx="2" />'
        )
        parts.append(
            f'<text class="legend-label" x="{round(x + LEGEND_TEXT_OFFSET_X, 1)}" '
            f'y="{LEGEND_TEXT_OFFSET_Y}">{label}</text>'
        )
    return "\n".join(parts)


def create_svg_grid_labels(
    levels: dict[str, int],
    grid_width: int = 794,
) -> str:
    """Render day-of-week + month axis labels; `grid_width` must match the grid's.

    Day labels (Mon/Wed/Fri) pick their row from the weekday of the first visible
    date. Month labels sit at the first column of each new month in the window.
    """
    cell_size, cell_spacing = calculate_cell_dimensions(grid_width)
    step = cell_size + cell_spacing

    entries = list(levels.items())[-HEATMAP_CELLS:]
    if not entries:
        return "<!-- Contribution Grid Labels -->"

    parts = ["<!-- Contribution Grid Labels -->"]

    first_weekday = datetime.fromisoformat(entries[0][0]).weekday()  # Mon=0
    for target_weekday, label in HEATMAP_ROW_LABELS:
        row = (target_weekday - first_weekday) % 7
        y = round(row * step + cell_size * 0.5 + 3.5, 1)
        parts.append(
            f'<text class="mono-sm" x="-10" y="{y}" text-anchor="end">{label}</text>'
        )

    month_positions: dict[str, float] = {}
    prev_month: int | None = None
    for col in range(HEATMAP_WEEKS):
        entry_idx = col * HEATMAP_DAYS_PER_WEEK
        if entry_idx >= len(entries):
            break
        month = int(entries[entry_idx][0][5:7])
        if month != prev_month:
            month_positions[MONTH_ABBR[month - 1]] = round(col * step, 1)
            prev_month = month
    for abbr, x in month_positions.items():
        parts.append(f'<text class="mono-sm" x="{x}" y="-4">{abbr}</text>')

    return "\n".join(parts)
