"""models.py - the core domain vocabulary of inkle-to-card.

WHY this module exists: parsing, conversion, turning, simulation, and the PDF
report all speak the language defined here. Defining the vocabulary once, with
the weaving terms pinned to the research, keeps every later stage a plain
data-movement problem.

Domain background (grounded in research/RESEARCH.md, sections 2-3):

- An INKLE DRAFT is warp-only: an ordered list of ENDS (warp threads), each with
  a color, alternating between HEDDLED ends (threaded on string heddles) and
  UNHEDDLED ends. 17 ends (9 H / 8 U) is a typical starter width.
- A CARD (tablet) has four holes labeled A, B, C, D clockwise on its front
  face, is threaded S or Z (all four holes the same direction or it will not
  turn), and is turned F (forward, away) or B (backward, toward) one quarter
  turn per pick.
- START POSITION ("home position"): all cards rotated so holes A and D are up,
  printed side toward the right, Tablet 1 at the left of the pack. Conventions
  differ between books, so the converter states its convention explicitly.
- SURFACE CYCLE: from home position, an 8-pick 4F-4B repeat shows the hole
  threads in the order D, C, B, A, A, B, C, D (the second half mirrors the
  first). This constant is the heart of the band-face simulator.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Hole labels, clockwise on the front face of the card (research sec 3).
HOLE_ORDER: tuple[str, ...] = ("A", "B", "C", "D")

# Which hole's thread shows on the top face at each pick of the default
# 4F-4B cycle, counted from home position (research sec 3).
SURFACE_CYCLE: tuple[str, ...] = ("D", "C", "B", "A", "A", "B", "C", "D")

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class DraftError(ValueError):
    """Raised when a draft cannot be parsed or fails validation.

    NOTE: validation itself returns a problem list (so callers can show every
    problem at once); parsers raise DraftError when that list is not empty.
    """


class ThreadingDirection(str, Enum):
    """Direction the warp is strung through the holes.

    WHY S and Z: looking at the card pack from above, the threads lie on a
    slight diagonal, like the middle stroke of the letter S or Z. All four
    holes of a card must be strung the same way or the card will not turn.
    Linda Hendrickson's books call these L (left) and R (right) respectively.
    """

    S = "S"
    Z = "Z"


class Turn(str, Enum):
    """A quarter turn of a card.

    F (forward): turns the way a bicycle wheel does from the weaver's view.
    B (backward): the reverse movement.
    """

    F = "F"
    B = "B"


# ---------------------------------------------------------------------------
# serialization helpers
# ---------------------------------------------------------------------------

def _ser(value: Any) -> Any:
    """Convert a dataclass field value into plain JSON-safe data."""
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return to_dict(value)
    if isinstance(value, dict):
        return {k: _ser(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_ser(v) for v in value]
    return value


def _deser(value: Any, ann: Any) -> Any:
    """Rebuild one field value from plain data, guided by its annotation.

    NOTE: with `from __future__ import annotations` every annotation arrives
    here as a STRING (e.g. "list[Turn]"), so we dispatch on string patterns
    rather than isinstance checks.
    """
    ann = str(ann).strip()
    if ann.startswith("list["):
        inner = ann[5:-1]
        if inner == "Turn":
            return [Turn(v) for v in value]
        if inner == "End":
            return [from_dict(End, v) for v in value]
        if inner == "Card":
            return [from_dict(Card, v) for v in value]
        if inner == "Pick":
            return [from_dict(Pick, v) for v in value]
        return list(value)
    if ann.startswith("dict["):
        return dict(value)
    if ann.startswith("tuple["):
        return tuple(value)
    if ann == "ThreadingDirection":
        return ThreadingDirection(value)
    if ann == "Turn":
        return Turn(value)
    if ann == "StartPosition":
        return from_dict(StartPosition, value)
    if ann == "bool":
        return bool(value)
    if ann == "int":
        return int(value)
    return value


def to_dict(obj: Any) -> dict:
    """Serialize any models dataclass to a plain dict.

    NOTE: only real dataclass fields are emitted, so computed properties can
    never sneak into a round-trip (a past project broke from_dict that way).
    """
    return {name: _ser(getattr(obj, name)) for name in obj.__dataclass_fields__}


def from_dict(cls: type, data: dict) -> Any:
    """Rebuild a models dataclass from a plain dict.

    Unknown keys are IGNORED on purpose: forward compatibility with dicts that
    carry extra (computed) fields (computed properties must never break the
    round-trip).
    """
    kwargs = {}
    for name, fld in cls.__dataclass_fields__.items():
        if name in data:
            kwargs[name] = _deser(data[name], fld.type)
    return cls(**kwargs)


# ---------------------------------------------------------------------------
# inkle side
# ---------------------------------------------------------------------------

@dataclass
class End:
    """One warp thread of the inkle draft, in left-to-right warp order."""

    index: int                 # position in the draft, 0-based, left to right
    color_name: str            # key into the draft palette
    heddled: bool              # True: top row / string heddle; False: open row

    def to_dict(self) -> dict:
        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "End":
        return from_dict(cls, data)


@dataclass
class InkleDraft:
    """A warp-only inkle pattern: palette + ordered ends."""

    name: str
    palette: dict[str, str]      # color name -> "#rrggbb"
    ends: list[End]

    def validate(self) -> list[str]:
        """Return every problem found (empty list means the draft is valid).

        WHY a list: loom-side mistakes are easier to fix when the weaver sees
        ALL problems at once instead of one exception per run.
        """
        problems: list[str] = []
        if not self.name.strip():
            problems.append("draft has no name")
        for cname, hexv in self.palette.items():
            if not isinstance(hexv, str) or not _HEX_RE.match(hexv):
                problems.append(f"palette color {cname!r} has invalid hex {hexv!r} (want #rrggbb)")
        if len(self.ends) < 8:
            problems.append(f"only {len(self.ends)} ends; a band needs at least 8 (two cards)")
        for i, end in enumerate(self.ends):
            if end.color_name not in self.palette:
                problems.append(
                    f"end {i + 1} uses unknown color {end.color_name!r}; "
                    f"palette has: {', '.join(sorted(self.palette))}"
                )
        for i in range(1, len(self.ends)):
            if self.ends[i].heddled == self.ends[i - 1].heddled:
                problems.append(
                    f"ends {i} and {i + 1} are both "
                    f"{'heddled' if self.ends[i].heddled else 'unheddled'}; "
                    "heddled and open ends must alternate"
                )
        return problems

    # computed helpers (never serialized) -----------------------------------

    def color_counts(self) -> dict[str, int]:
        """Total ends per color - feeds the PDF materials calculation."""
        counts: dict[str, int] = {}
        for end in self.ends:
            counts[end.color_name] = counts.get(end.color_name, 0) + 1
        return counts

    def stripe_blocks(self) -> list[tuple[str, int]]:
        """Runs of consecutive same-color ends: [(color, width), ...].

        WHY: stripe blocks are what the grain analysis talks about - blocks
        of 4+ ends map cleanly under Mapping B, and single-end features are
        what the low-contrast and mixing warnings target.
        """
        blocks: list[tuple[str, int]] = []
        for end in self.ends:
            if blocks and blocks[-1][0] == end.color_name:
                blocks[-1] = (end.color_name, blocks[-1][1] + 1)
            else:
                blocks.append((end.color_name, 1))
        return blocks

    def to_dict(self) -> dict:
        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InkleDraft":
        return from_dict(cls, data)


# ---------------------------------------------------------------------------
# card side
# ---------------------------------------------------------------------------

@dataclass
class Card:
    """One card (tablet) with a thread color through each hole."""

    number: int                       # 1-based, left to right in the pack
    hole_colors: dict[str, str]       # hole letter A-D -> color name
    threading: ThreadingDirection = ThreadingDirection.Z

    def holes_complete(self) -> bool:
        return set(self.hole_colors) == set(HOLE_ORDER)

    def to_dict(self) -> dict:
        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return from_dict(cls, data)


@dataclass
class StartPosition:
    """The deck's explicit starting orientation.

    WHY a whole dataclass: published books DISAGREE about starting position
    (some put A and D up, some A and D toward the fell), so the PDF report
    prints this convention verbatim instead of assuming the weaver knows it.
    """

    top_holes: tuple[str, ...] = ("A", "D")
    face: str = "right"        # printed side of the cards faces right
    tablet_one: str = "left"   # card 1 sits at the left of the pack
    description: str = (
        "Home position: rotate every card so holes A and D are at the top, "
        "printed sides facing right, with card 1 at the left of the pack."
    )

    def to_dict(self) -> dict:
        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StartPosition":
        return from_dict(cls, data)


@dataclass
class Pick:
    """One pick: a quarter turn of each card, then a weft pass.

    An EMPTY turns list is pack shorthand: every card turns the same way
    (the common "4 forward, 4 back" style).
    """

    turns: list[Turn] = field(default_factory=list)

    def to_dict(self) -> dict:
        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Pick":
        return from_dict(cls, data)


@dataclass
class CardDeck:
    """The complete card-weaving settings the program produces."""

    draft_name: str
    mapping: str                       # "A" (1 end = 1 card) or "B" (4 ends = 1 card)
    cards: list[Card]
    start_position: StartPosition = field(default_factory=StartPosition)
    picks: list[Pick] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CardDeck":
        return from_dict(cls, data)
