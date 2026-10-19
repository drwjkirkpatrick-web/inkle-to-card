"""engine.py - convert an inkle draft into a card (tablet) deck. Prompt 3.

THE CORE IDEA (research/RESEARCH.md section 7):

Mapping A - width-preserving (default). One inkle end becomes ONE card, with
all four holes threaded that end's color. The deck reproduces the inkle color
sequence across the band at full width: card k shows end k's color, forever,
because all four of its threads are the same color no matter which hole the
turn brings to the top. Cost: about 4x the thread of the inkle original.

Mapping B - material-efficient. Four consecutive ends share one card; the
holes are arranged so that an 8-pick 4F-4B cycle shows the four colors in
draft order: hole D carries the group's first end (the first pick shows D),
then C, B, A - and the second half of the cycle mirrors the first, exactly
the mirror rule from the research. The band comes out one-quarter as wide.

Both mappings thread every card Z (a documented v1 choice: under pack turning
with the balanced 4F-4B sequence, Z threading makes the finished cords
S-twined; the practical effect for a first band is only in the selvedge
twist direction).

Start position is always the explicit convention from the research: holes A
and D up, printed side toward the right, card 1 at the left of the pack.
"""
from __future__ import annotations

from .models import (
    HOLE_ORDER,
    Card,
    CardDeck,
    End,
    InkleDraft,
    StartPosition,
    ThreadingDirection,
)

# Surface order inside one card group: an 8-pick 4F-4B cycle from home shows
# holes D, C, B, A then the mirror - so the group's FIRST end goes in hole D.
_HOLE_TO_GROUP_INDEX = {"D": 0, "C": 1, "B": 2, "A": 3}


def convert_draft(draft: InkleDraft, mapping: str = "A") -> CardDeck:
    """Convert a validated inkle draft into card-weaving settings.

    mapping="A": one end per card (width-preserving, 4x thread).
    mapping="B": four ends per card (quarter width, material-efficient).
    """
    if mapping == "A":
        cards = [
            Card(
                number=i + 1,
                hole_colors={hole: end.color_name for hole in HOLE_ORDER},
                threading=ThreadingDirection.Z,
            )
            for i, end in enumerate(draft.ends)
        ]
        warnings = [
            f"Mapping A (width-preserving): each of the {len(draft.ends)} ends becomes "
            "one card threaded with four threads of the same color - about 4x the "
            "thread of an inkle band of the same width."
        ]
        warnings.extend(_pack_warnings(len(cards), alt_cards=-(-len(draft.ends) // 4)))
        return CardDeck(
            draft_name=draft.name,
            mapping="A",
            cards=cards,
            start_position=StartPosition(),
            warnings=warnings,
        )

    if mapping == "B":
        groups = [draft.ends[i : i + 4] for i in range(0, len(draft.ends), 4)]
        edge_color = draft.ends[0].color_name
        cards: list[Card] = []
        padded = 0
        for g, group in enumerate(groups):
            if len(group) < 4:
                pad = [
                    End(index=group[-1].index + k + 1, color_name=edge_color, heddled=False)
                    for k in range(4 - len(group))
                ]
                group = group + pad
                padded += len(pad)
            hole_colors = {
                hole: group[_HOLE_TO_GROUP_INDEX[hole]].color_name for hole in HOLE_ORDER
            }
            cards.append(
                Card(number=g + 1, hole_colors=hole_colors, threading=ThreadingDirection.Z)
            )
        warnings = [
            f"Mapping B (material-efficient): {len(draft.ends)} ends compressed to "
            f"{len(cards)} cards - the band weaves one-quarter as wide as the inkle original."
        ]
        narrow = [(color, width) for color, width in draft.stripe_blocks() if width < 4]
        if narrow:
            warnings.append(
                f"{len(narrow)} stripe feature(s) narrower than 4 ends (first: "
                f"{narrow[0][0]} x{narrow[0][1]}) will not read at full width under Mapping B."
            )
        if padded:
            warnings.append(
                f"The last card was padded with {padded} extra end(s) of the edge color "
                f"{edge_color!r} so all four of its holes carry a thread."
            )
        warnings.extend(_pack_warnings(len(cards)))
        return CardDeck(
            draft_name=draft.name,
            mapping="B",
            cards=cards,
            start_position=StartPosition(),
            warnings=warnings,
        )

    raise ValueError(f"mapping must be 'A' or 'B', not {mapping!r}")


def _pack_warnings(n_cards: int, alt_cards: int | None = None) -> list[str]:
    """Card-count guidance from research section 11: commercial packs hold 25.

    alt_cards: how many cards the OTHER mapping would need (used by Mapping A
    to suggest the narrower option).
    """
    import math

    warnings: list[str] = []
    if n_cards > 25:
        packs = math.ceil(n_cards / 25)
        text = (
            f"Card-pack math: this band needs {n_cards} cards; commercial packs hold 25 "
            "(Schacht, Lacis, Hendrickson) - that is "
            f"{packs} pack{'s' if packs != 1 else ''}"
        )
        if alt_cards and alt_cards != n_cards and alt_cards <= 25:
            text += f"; Mapping B would weave it on {alt_cards} cards (one pack)"
        warnings.append(text + ".")
        if n_cards > 100:
            warnings.append(
                f"{n_cards} cards is a very long pack - consider wooden tablets, "
                "a narrower draft, or Mapping B."
            )
    return warnings
