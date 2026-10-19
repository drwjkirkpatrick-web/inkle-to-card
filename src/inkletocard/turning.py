"""turning.py - turning sequences and twist accounting. Prompt 4.

WEAVING BACKGROUND (research sec 3):

- A PICK is one quarter turn of every card followed by one pass of the weft.
- FORWARD (F): the card turns the way a bicycle wheel does from the weaver's
  point of view. BACKWARD (B): the reverse.
- The default sequence for threading-based drafts is 4F-4B: four forward
  picks, four backward picks. It is TWIST-NEUTRAL - each card's threads end
  the 8-pick cycle with zero net rotation, so twist never builds up in the
  warp. It is also why threaded-in drafts mirror: picks 5-8 show the mirror
  image of picks 1-4.
- Turning always one way (FFFF...) accumulates twist: after |net| grows past
  about a full turn (4 quarter-turns) the warp starts to kink and the cards
  get hard to turn. Weavers push the twist out, untie and comb, or use
  swivels/weights - the PDF warnings page tells them when.
"""
from __future__ import annotations

from .models import CardDeck, DraftError, Pick, Turn

# Net quarter-turns beyond this count trigger a twist warning.
TWIST_WARN_THRESHOLD = 4


def gen_4f4b(n_cards: int, repeats: int = 1) -> list[Pick]:
    """Generate the standard 4-forward / 4-backward pack sequence.

    Every pick carries an explicit turn for every card, so the deck's JSON
    stays unambiguous even if a weaver later overrides individual cards.
    """
    if n_cards < 1:
        raise ValueError(f"n_cards must be >= 1, not {n_cards}")
    if repeats < 1:
        raise ValueError(f"repeats must be >= 1, not {repeats}")
    picks: list[Pick] = []
    for _ in range(repeats):
        picks.extend(Pick(turns=[Turn.F] * n_cards) for _ in range(4))
        picks.extend(Pick(turns=[Turn.B] * n_cards) for _ in range(4))
    return picks


def build_picks(rows: list) -> list[Pick]:
    """Build per-card picks from rows like ["F F B B", "B B F F"].

    Every row must name a turn for EVERY card; lengths must match. Accepts
    "F"/"B" (any case) or Turn values.
    """
    if not rows:
        raise ValueError("no pick rows given")
    picks: list[Pick] = []
    expected: int | None = None
    for r, row in enumerate(rows, start=1):
        tokens = row.split() if isinstance(row, str) else list(row)
        if expected is None:
            expected = len(tokens)
        elif len(tokens) != expected:
            raise ValueError(
                f"pick row {r} has {len(tokens)} turns but row 1 has {expected}; "
                "every row needs one turn per card"
            )
        turns = []
        for i, tok in enumerate(tokens):
            if isinstance(tok, Turn):
                turns.append(tok)
                continue
            key = str(tok).strip().upper()
            if key not in ("F", "B"):
                raise ValueError(
                    f"pick row {r}, card {i + 1}: turn {tok!r} must be F (forward) or B (backward)"
                )
            turns.append(Turn(key))
        picks.append(Pick(turns=turns))
    return picks


def net_quarter_turns(deck: CardDeck) -> dict[int, int]:
    """Net rotation per card number: +1 per forward pick, -1 per backward."""
    n_cards = len(deck.cards)
    net = {card.number: 0 for card in deck.cards}
    for pick in deck.picks:
        if len(pick.turns) not in (0, n_cards):
            raise ValueError(
                f"a pick carries {len(pick.turns)} turns but the deck has {n_cards} cards"
            )
        for card, turn in zip(deck.cards, pick.turns):
            net[card.number] += 1 if turn is Turn.F else -1
    return net


def twist_warnings(deck: CardDeck) -> list[str]:
    """Warn when any card accumulates more than a full turn of net twist."""
    warnings: list[str] = []
    for number, net in sorted(net_quarter_turns(deck).items()):
        if abs(net) > TWIST_WARN_THRESHOLD:
            direction = "forward" if net > 0 else "backward"
            warnings.append(
                f"Card {number} accumulates {net} quarter-turns of {direction} twist "
                f"over the woven sequence (more than the {TWIST_WARN_THRESHOLD}-quarter "
                "warning threshold). Expect kinking warp: push the twist toward the far "
                "end of the warp, untie and comb it out, or weight/swivel that card's "
                "bundle - research section 3 lists the standard fixes."
            )
    return warnings


def attach_turning(deck: CardDeck, picks: list[Pick]) -> CardDeck:
    """Convenience: return the deck with picks attached and twist warnings merged."""
    if not picks:
        raise DraftError("no picks to attach")
    deck.picks = picks
    deck.warnings = list(deck.warnings) + twist_warnings(deck)
    return deck
