"""inkletocard - convert an inkle belt pattern into card (tablet) weaving settings.

The package reads an inkle draft (a warp-only color sequence with heddled /
unheddled ends), converts it into a card deck (per-card hole colors A-D, S/Z
threading, F/B turning sequence, explicit start position), simulates the woven
band face, and renders a PDF report a weaver can follow at the loom.

Evidence base: research/RESEARCH.md (grounded citations).
"""
__version__ = "0.2.0"

from .models import (
    HOLE_ORDER,
    SURFACE_CYCLE,
    Card,
    CardDeck,
    DraftError,
    End,
    InkleDraft,
    Pick,
    StartPosition,
    ThreadingDirection,
    Turn,
)
from .parsers import parse_draft, parse_inkle_json, parse_inkle_text
from .photo import extract_palette, import_grid, match_colors

__all__ = [
    "HOLE_ORDER", "SURFACE_CYCLE", "Card", "CardDeck", "DraftError", "End",
    "InkleDraft", "Pick", "StartPosition", "ThreadingDirection", "Turn",
    "parse_draft", "parse_inkle_json", "parse_inkle_text",
    "extract_palette", "import_grid", "match_colors",
    "__version__",
]
