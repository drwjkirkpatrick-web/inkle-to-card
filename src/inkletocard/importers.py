"""importers.py - import tablet-weaving drafts from other tools (v0.3).

TODAY: the Tablet Weaving Draft Designer (TDD) `.tdd` plain-text format -
grounded in TDD's own example file, its old-JSON converter, and its app
source (research/RESEARCH.md section 13).

THE FORMAT:

    # comments start with '#'
    <turning chart: one row per pick, one char per card - '/' or '\\'>
    <4 hole rows: one char per card - a palette digit, or ' ' for a dropped hole>
    <S/Z row: one char per card>
    <palette: "N - #rrggbb" lines>

DERIVED TURN RULE (weave-test candidate): TDD's converter gives each card an
initial slash from its threading (Z-threaded -> '\\', S-threaded -> '/') and
flips it at every turn reversal. Under the standard twining rules, a card
turned FORWARD produces exactly that initial character, so the importer reads
the home slash as FORWARD and the other slash as BACKWARD.

HOLE-ROW ORDER: TDD labels holes A-D as a display toggle, so which file row
is hole A is an assumption - default ABCD top-to-bottom, override with
--holes DCBA. The import prints its assumptions in the deck warnings, which
the PDF repeats on page R9.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .colors import suggest_name  # noqa: F401  (re-exported for convenience)
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
from .photo import _unique_names

# A card's "home" character in the TDD turning chart, by threading direction.
_HOME_SLASH = {"Z": "\\", "S": "/"}
_PALETTE_LINE = re.compile(r"^([0-9a-fA-F])\s*-\s*(#[0-9a-fA-F]{6})\s*$")


@dataclass
class ImportedPattern:
    """An imported deck plus the reverse-engineered inkle view of it."""

    deck: CardDeck
    draft: InkleDraft


def deck_to_draft(deck: CardDeck, palette: dict[str, str], name: str | None = None) -> InkleDraft:
    """Reverse-engineer the inkle view of a deck: one end per hole, in the
    surface order D, C, B, A per card, so per-color end counts equal the
    deck's per-color thread counts (exactly what the materials page needs)."""
    ends: list[End] = []
    for card in deck.cards:
        for hole in SURFACE_CYCLE[:4]:  # D, C, B, A - the order the face shows
            ends.append(
                End(index=len(ends), color_name=card.hole_colors[hole],
                    heddled=(len(ends) % 2 == 0))
            )
    draft = InkleDraft(name=name or deck.draft_name, palette=palette, ends=ends)
    problems = draft.validate()
    if problems:
        raise DraftError(
            "imported deck does not yield a valid draft:\n- " + "\n- ".join(problems)
        )
    return draft


def _tdd_blocks(text: str) -> list[list[str]]:
    """Split a .tdd file into (turning, threading, palette) line blocks."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith("#"):
            continue
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    if len(blocks) != 3:
        raise DraftError(
            f"a .tdd file has 3 blocks (turning chart, threading chart, palette) - "
            f"found {len(blocks)}"
        )
    return blocks


def import_tdd(path, hole_rows: str = "ABCD") -> ImportedPattern:
    """Import a TDD (Tablet Weaving Draft Designer) .tdd draft."""
    order = hole_rows.strip().upper()
    if len(order) != 4 or set(order) != set("ABCD"):
        raise ValueError("hole_rows must be a 4-letter order like ABCD or DCBA")

    turning_rows, threading_rows, palette_lines = _tdd_blocks(Path(path).read_text())

    if len(threading_rows) < 5:
        raise DraftError(
            f"threading block needs 4 hole rows plus an S/Z row - "
            f"found {len(threading_rows)} lines"
        )
    sz_raw = threading_rows[-1].strip().upper()
    hole_lines = threading_rows[:-1]
    if len(hole_lines) != 4:
        raise DraftError(f"expected 4 hole rows, found {len(hole_lines)}")
    if not sz_raw or any(ch not in "SZ" for ch in sz_raw):
        raise DraftError(
            f"the S/Z row must name S or Z for every card - got {threading_rows[-1]!r}"
        )
    n = len(sz_raw)
    for line in hole_lines + turning_rows:
        if len(line) != n:
            raise DraftError(
                f"a chart row has {len(line)} characters but the S/Z row has {n}; "
                "every row needs exactly one character per card"
            )
    for line in turning_rows:
        if any(ch not in "/\\" for ch in line.strip()):
            raise DraftError(
                f"turning chart rows may only contain '/' and '\\' - got {line!r}"
            )

    hex_by_digit: dict[str, str] = {}
    for line in palette_lines:
        match = _PALETTE_LINE.match(line.strip())
        if not match:
            raise DraftError(
                f"cannot read palette line {line.strip()!r} - expected 'N - #rrggbb'"
            )
        hex_by_digit[match.group(1)] = match.group(2)
    if not hex_by_digit:
        raise DraftError("the palette block is empty")
    names = _unique_names(list(hex_by_digit.values()))
    name_by_digit = {digit: names[hexv] for digit, hexv in hex_by_digit.items()}
    palette = {name_by_digit[digit]: hex_by_digit[digit] for digit in hex_by_digit}

    directions = [ThreadingDirection(ch) for ch in sz_raw]
    row_to_hole = {r: order[r] for r in range(4)}
    cards: list[Card] = []
    for c in range(n):
        hole_colors: dict[str, str] = {}
        for r, line in enumerate(hole_lines):
            ch = line[c]
            if ch == " ":
                continue  # dropped hole - filled below, with a warning
            if ch not in hex_by_digit:
                raise DraftError(
                    f"threading row {r + 1}, card {c + 1}: color {ch!r} is not in "
                    f"the palette ({', '.join(sorted(hex_by_digit))})"
                )
            hole_colors[row_to_hole[r]] = name_by_digit[ch]
        if not hole_colors:
            raise DraftError(f"card {c + 1} has no threads in any hole")
        cards.append(Card(number=c + 1, hole_colors=hole_colors, threading=directions[c]))

    warnings = [
        f"Imported from a TDD file. Assumptions printed for the weave test "
        f"(research section 13): hole rows read top-to-bottom as {order} "
        "(flip with --holes DCBA if the first pick shows the wrong colors), "
        "and a card's home slash (Z '\\', S '/') read as a forward turn."
    ]
    filled: list[str] = []
    for card in cards:
        missing = [h for h in HOLE_ORDER if h not in card.hole_colors]
        if missing:
            fill = next(iter(card.hole_colors.values()))
            for h in missing:
                card.hole_colors[h] = fill
            filled.append(f"card {card.number} (holes {'/'.join(missing)} filled with {fill!r})")
    if filled:
        warnings.append(
            "Dropped-hole technique detected: " + "; ".join(filled) +
            ". The preview assumes every hole is threaded, so the real band will differ."
        )

    picks = []
    for row in turning_rows:
        turns = [
            Turn.F if row[c] == _HOME_SLASH[card.threading.value] else Turn.B
            for c, card in enumerate(cards)
        ]
        picks.append(Pick(turns=turns))

    deck = CardDeck(
        draft_name=Path(path).stem,
        mapping="TDD",
        cards=cards,
        start_position=StartPosition(),
        picks=picks,
        warnings=warnings,
    )
    draft = deck_to_draft(deck, palette, name=deck.draft_name)
    return ImportedPattern(deck=deck, draft=draft)
