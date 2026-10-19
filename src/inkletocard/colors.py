"""colors.py - value contrast: the digital black-and-white-photo test. Prompt 6.

WHY THIS MODULE EXISTS (research section 12): the single biggest factor in
whether a band pattern reads is VALUE contrast - how light one color is
against the next - not hue. Weavers test it by photographing their yarns in
black and white; this module does the same test numerically, because warm
and bright colors look lighter to the eye than they measure.

Three tools for the PDF and CLI:

- relative_luminance / contrast_ratio: the standard WCAG math, so the
  numbers agree with web color checkers a weaver may already know.
- value_ladder: the palette sorted dark-to-light, printed in the report so
  the weaver sees the value order at a glance.
- check_draft_contrast: warns at every stripe-block boundary whose two
  colors are too close in value for the boundary to read.

Plus suggest_name() for "what IS this hex?" moments, and mixing_note() for
single-end features: small dots of two colors blend in the eye (research
section 12), so one-end stripes weave as heather, not crisp pinstripes.
"""
from __future__ import annotations

import re

from .models import InkleDraft

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# A small table of common color names (CSS-inspired) for suggestions.
CSS_NAMES: dict[str, str] = {
    "black": "#000000", "white": "#FFFFFF", "silver": "#C0C0C0",
    "gray": "#808080", "maroon": "#800000", "red": "#FF0000",
    "crimson": "#DC143C", "firebrick": "#B22222", "tomato": "#FF6347",
    "coral": "#FF7F50", "salmon": "#FA8072", "orange": "#FFA500",
    "gold": "#FFD700", "yellow": "#FFFF00", "khaki": "#F0E68C",
    "olive": "#808000", "lime": "#00FF00", "green": "#008000",
    "teal": "#008080", "navy": "#000080", "midnightblue": "#191970",
    "royalblue": "#4169E1", "skyblue": "#87CEEB", "blue": "#0000FF",
    "indigo": "#4B0082", "purple": "#800080", "plum": "#DDA0DD",
    "pink": "#FFC0CB", "brown": "#A52A2A", "tan": "#D2B48C",
    "beige": "#F5F5DC", "ivory": "#FFFFF0", "cream": "#F5F0E6",
}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    if not isinstance(hex_color, str) or not _HEX_RE.match(hex_color):
        raise ValueError(f"color must look like '#rrggbb', not {hex_color!r}")
    return (
        int(hex_color[1:3], 16),
        int(hex_color[3:5], 16),
        int(hex_color[5:7], 16),
    )


def relative_luminance(hex_color: str) -> float:
    """Perceived lightness on a 0.0 (black) to 1.0 (white) scale (WCAG math)."""
    r, g, b = _hex_to_rgb(hex_color)

    def linear(channel: int) -> float:
        c = channel / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Light/dark contrast between two colors: 1.0 = identical, 21.0 = black vs white."""
    la, lb = relative_luminance(hex_a), relative_luminance(hex_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def value_ladder(palette: dict[str, str]) -> list[tuple[str, str, float]]:
    """The palette sorted dark-to-light: [(color name, hex, luminance), ...]."""
    entries = [
        (name, hexv, relative_luminance(hexv)) for name, hexv in palette.items()
    ]
    return sorted(entries, key=lambda entry: entry[2])


def check_draft_contrast(draft: InkleDraft, threshold: float = 1.8) -> list[str]:
    """Warn at stripe boundaries whose colors are too close in value to read."""
    warnings: list[str] = []
    blocks = draft.stripe_blocks()
    start = 1  # 1-based end number where the current block starts
    for (color_a, width_a), (color_b, _width_b) in zip(blocks, blocks[1:]):
        ratio = contrast_ratio(draft.palette[color_a], draft.palette[color_b])
        if ratio < threshold:
            warnings.append(
                f"Ends {start + width_a - 1}-{start + width_a}: {color_a} meets {color_b} "
                f"with value contrast {ratio:.1f}:1, below the {threshold:.1f}:1 guideline - "
                "that boundary may not read on the woven band. Prefer a lighter or darker "
                "neighbor (the black-and-white-photo test, research section 12)."
            )
        start += width_a
    return warnings


def suggest_name(hex_color: str) -> str:
    """Nearest common color name by straight RGB distance (a convenience)."""
    r, g, b = _hex_to_rgb(hex_color)
    best_name, best_dist = "", None
    for name, candidate in CSS_NAMES.items():
        cr, cg, cb = _hex_to_rgb(candidate)
        dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if best_dist is None or dist < best_dist:
            best_name, best_dist = name, dist
    return best_name


def mixing_note(draft: InkleDraft) -> list[str]:
    """Caveat for single-end features: small dots blend in the eye."""
    notes: list[str] = []
    start = 1
    for color, width in draft.stripe_blocks():
        if width == 1:
            notes.append(
                f"End {start} is a single {color} thread. Small dots of two colors "
                "blend in the eye (bright green with magenta weaves brown in plain "
                "weave - research section 12), so expect a heathered mix rather "
                "than a crisp one-end stripe."
            )
        start += width
    return notes
