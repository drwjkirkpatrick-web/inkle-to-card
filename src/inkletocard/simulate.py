"""simulate.py - predict the woven band face, pick by pick. Prompt 5.

THE ROTATION MODEL (research section 3):

From home position (holes A and D up), a FORWARD quarter turn brings the
group's threads to the top face in the order D, C, B, A over four picks; a
BACKWARD quarter turn brings them up as A, B, C, D. The standard 4F-4B
sequence therefore shows

    pick:    1  2  3  4  5  6  7  8
    hole:    D  C  B  A  A  B  C  D

which is exactly the mirror rule from the research (picks 5-8 mirror picks
1-4) - the same fact the PDF report prints as the woven preview.

The simulator tracks each card's net rotation (quarter turns from home,
modulo 4) so it stays correct for ANY turning sequence: all-forward,
all-backward, per-card overrides, multiple repeats.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import CardDeck, Turn

# Which hole the top face shows after each kind of quarter turn, indexed by
# the card's rotation state (see the rotation model above).
_FORWARD_SHOW = ("D", "C", "B", "A")   # r=1->D, 2->C, 3->B, 0->A
_BACKWARD_SHOW = ("A", "B", "C", "D")  # r=3->A, 2->B, 1->C, 0->D


@dataclass
class BandPreview:
    """The predicted face of the woven band."""

    deck_name: str
    mapping: str
    grid: list[list[str]]          # grid[pick][card] = color name on the top face
    card_numbers: list[int]
    warnings: list[str] = field(default_factory=list)


def simulate_band(deck: CardDeck, picks=None) -> BandPreview:
    """Simulate the band face for a deck plus its turning sequence.

    Uses deck.picks when `picks` is omitted. Every pick must carry one
    explicit turn per card (build them with turning.gen_4f4b/build_picks).
    """
    picks = deck.picks if picks is None else picks
    n_cards = len(deck.cards)
    if not picks:
        raise ValueError(
            "no picks to simulate - attach a turning sequence first "
            "(turning.gen_4f4b / turning.build_picks)"
        )
    rotation = [0] * n_cards
    grid: list[list[str]] = []
    for p, pick in enumerate(picks, start=1):
        if len(pick.turns) == 0:
            raise ValueError(
                f"pick {p} uses pack shorthand (empty turns), which is ambiguous - "
                "build explicit picks with gen_4f4b or build_picks"
            )
        if len(pick.turns) != n_cards:
            raise ValueError(
                f"pick {p} carries {len(pick.turns)} turns but the deck has {n_cards} cards"
            )
        row: list[str] = []
        for k, (card, turn) in enumerate(zip(deck.cards, pick.turns)):
            if turn is Turn.F:
                rotation[k] = (rotation[k] + 1) % 4
                hole = _FORWARD_SHOW[(rotation[k] - 1) % 4]
            else:
                rotation[k] = (rotation[k] - 1) % 4
                hole = _BACKWARD_SHOW[(3 - rotation[k]) % 4]
            row.append(card.hole_colors[hole])
        grid.append(row)

    warnings = list(deck.warnings)
    if deck.mapping == "B":
        cycling = [c.number for c in deck.cards if len(set(c.hole_colors.values())) > 1]
        if cycling:
            warnings.append(
                f"{len(cycling)} card(s) (first: card {cycling[0]}) carry more than one "
                "color, so their columns cycle through the 8-pick sequence instead of "
                "showing one constant stripe - stripe features narrower than 4 ends "
                "will not read at full width (research sections 4 and 7)."
            )
    return BandPreview(
        deck_name=deck.draft_name,
        mapping=deck.mapping,
        grid=grid,
        card_numbers=[c.number for c in deck.cards],
        warnings=warnings,
    )


def ascii_render(preview: BandPreview) -> str:
    """Render the preview as text: one line per pick, one symbol per card.

    Symbols are built from color names (n=navy, c=cream...) with a legend
    line so the output stays readable in a terminal or the --no-pdf mode.
    """
    symbols: dict[str, str] = {}
    taken: set[str] = set()
    for row in preview.grid:
        for color in row:
            if color in symbols:
                continue
            base = color.lower()
            symbol = ""
            for ch in base:
                symbol += ch
                if symbol not in taken:
                    break
            while symbol in taken:
                symbol += "x"
            taken.add(symbol)
            symbols[color] = symbol
    lines = ["legend: " + ", ".join(f"{sym}={name}" for name, sym in symbols.items())]
    # card numbers header (last two digits keeps narrow decks aligned)
    lines.append("pick  " + " ".join(f"{str(n)[-2:]:>3}" for n in preview.card_numbers))
    for p, row in enumerate(preview.grid, start=1):
        lines.append(f"{p:>4}  " + " ".join(f"{symbols[c]:>3}" for c in row))
    return "\n".join(lines)


def column_summary(preview: BandPreview) -> list[list[tuple[str, int]]]:
    """Per card, the runs of colors shown across picks: [[(color, count), ...], ...]."""
    summary: list[list[tuple[str, int]]] = []
    for k in range(len(preview.card_numbers)):
        runs: list[tuple[str, int]] = []
        for row in preview.grid:
            color = row[k]
            if runs and runs[-1][0] == color:
                runs[-1] = (color, runs[-1][1] + 1)
            else:
                runs.append((color, 1))
        summary.append(runs)
    return summary
