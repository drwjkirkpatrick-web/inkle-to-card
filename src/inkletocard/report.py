"""report.py - the weaver-facing PDF report. Prompt 7 (sections R1-R4).

WHAT THE PDF IS FOR: a weaver at the loom needs card settings they can
follow without a computer - the threading draft (which color goes through
which hole of which card), the deck summary, and an unambiguous starting
position. Research section 8 of RESEARCH.md is the specification; this
module draws sections R1-R4, and Prompt 8 adds R5-R9.

NOTATION (research sections 3, 8, 11):
- Holes are labeled A, B, C, D clockwise on the card's front face.
- Cards are numbered left to right and face to the right.
- Threading direction is S or Z ("/" = Z, "\\" = S in community notation).
- Home position: holes A and D up - stated explicitly on its own page
  because published books disagree about starting positions.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas as pdfcanvas

from .models import HOLE_ORDER, CardDeck, InkleDraft

PAGE_W, PAGE_H = landscape(letter)          # 792 x 612 pt - wide drafts need width
MARGIN = 40

_TITLE = "Inkle-to-Card Weaving Draft"
_UNKNOWN_COLOR_HEX = "#FF00FF"               # loud magenta: impossible to miss


# ---------------------------------------------------------------------------
# pure data builders (testable without drawing anything)
# ---------------------------------------------------------------------------

def title_block_data(deck: CardDeck, draft: InkleDraft) -> dict:
    """Everything the title page prints, as data."""
    return {
        "title": _TITLE,
        "draft_name": deck.draft_name,
        "mapping": deck.mapping,
        "mapping_label": (
            "Mapping A - one end per card, width-preserving"
            if deck.mapping == "A"
            else "Mapping B - four ends per card, quarter width"
        ),
        "cards": len(deck.cards),
        "ends": len(draft.ends),
        "picks": len(deck.picks),
        "warnings": len(deck.warnings),
        "generated": date.today().isoformat(),
        "hole_labels": list(HOLE_ORDER),
    }


def threading_table_data(deck: CardDeck, draft: InkleDraft) -> dict:
    """The threading draft grid as data: one entry per card, hex per hole."""
    cards = []
    for card in deck.cards:
        hexes = {
            hole: draft.palette.get(color, _UNKNOWN_COLOR_HEX)
            for hole, color in card.hole_colors.items()
        }
        cards.append(
            {
                "number": card.number,
                "hexes": hexes,
                "direction": card.threading.value,
            }
        )
    return {"holes": list(HOLE_ORDER), "cards": cards}


def deck_summary_rows(deck: CardDeck) -> list[str]:
    """One human-readable line per card: 'Card 1: A=navy B=navy ... Z'."""
    rows = []
    for card in deck.cards:
        holes = "  ".join(f"{hole}={card.hole_colors[hole]}" for hole in HOLE_ORDER)
        rows.append(
            f"Card {card.number}: {holes}  [{card.threading.value}-threaded]"
        )
    return rows


def start_position_text(deck: CardDeck) -> str:
    """The explicit starting-position instructions (conventions differ, so
    the PDF states its own instead of assuming the weaver knows them)."""
    sp = deck.start_position
    return (
        f"{sp.description}\n"
        "Holes are labeled A, B, C, D clockwise on the card's front face.\n"
        f"Cards are numbered left to right; card 1 sits at the {sp.tablet_one} "
        f"of the pack, printed sides facing {sp.face}.\n"
        "With holes A and D up, A and B face the unwoven warp and C and D face "
        "the woven cloth. If your cards carry colored bands or striped edges, "
        "turn them all the same way so any misaligned card is easy to spot "
        "(research sections 3, 8 and 11)."
    )


# ---------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------

def _hex(palette: dict[str, str], name: str) -> HexColor:
    return HexColor(palette.get(name, _UNKNOWN_COLOR_HEX))


def _heading(c: pdfcanvas.Canvas, text: str, size: int = 16) -> None:
    c.setFont("Helvetica-Bold", size)
    c.drawString(MARGIN, PAGE_H - MARGIN - 12, text)
    c.setFont("Helvetica", 10)


def _paragraph_lines(c: pdfcanvas.Canvas, text: str, x: float, y: float,
                     leading: float = 15) -> float:
    """Draw text line-by-line; returns the y after the last line."""
    for line in text.split("\n"):
        c.drawString(x, y, line)
        y -= leading
    return y


def _draw_title_page(c: pdfcanvas.Canvas, deck: CardDeck, draft: InkleDraft) -> None:
    data = title_block_data(deck, draft)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(MARGIN, PAGE_H - 80, data["title"])
    c.setFont("Helvetica-Bold", 18)
    c.drawString(MARGIN, PAGE_H - 110, data["draft_name"])
    c.setFont("Helvetica", 12)
    lines = [
        f"Generated {data['generated']} by inkle-to-card",
        "",
        f"Mapping: {data['mapping_label']}",
        f"Cards: {data['cards']}   (from {data['ends']} inkle ends)",
        f"Holes per card: 4 (labeled A, B, C, D)",
        f"Turning picks in the chart: {data['picks']}",
        f"Warnings attached: {data['warnings']}",
        "",
        "This deck reproduces the inkle color sequence on the woven face -",
        "see the woven preview page for what the band should look like.",
    ]
    _paragraph_lines(c, "\n".join(lines), MARGIN, PAGE_H - 150)


def _draw_threading_page(c: pdfcanvas.Canvas, deck: CardDeck, draft: InkleDraft) -> None:
    _heading(c, "R2 - Threading draft (one column per card, one row per hole)")
    data = threading_table_data(deck, draft)
    n = len(data["cards"])
    x0 = MARGIN + 30
    cell_w = min(30.0, (PAGE_W - MARGIN - x0) / max(n, 1))
    row_h = 16.0
    top = PAGE_H - MARGIN - 40

    # card numbers header
    c.setFont("Helvetica", 7)
    for i, card in enumerate(data["cards"]):
        c.drawCentredString(x0 + i * cell_w + cell_w / 2, top + 4,
                            str(card["number"])[-3:])
    # hole rows with colored cells
    for r, hole in enumerate(data["holes"]):
        y = top - (r + 1) * row_h
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y + 3, hole)
        for i, card in enumerate(data["cards"]):
            c.setFillColor(HexColor(card["hexes"][hole]))
            c.rect(x0 + i * cell_w, y, cell_w, row_h - 1, stroke=1, fill=1)
    # threading direction row
    y = top - 5 * row_h
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN, y + 3, "S/Z")
    c.setFont("Helvetica", 10)
    for i, card in enumerate(data["cards"]):
        c.drawCentredString(x0 + i * cell_w + cell_w / 2, y + 3, card["direction"])
    # notation footnote
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(MARGIN, y - 24,
                 'Thread every card the direction shown; "/" = Z-threading, "\\" = S-threading '
                 "(community notation). Holes are labeled clockwise on the front face.")


def _draw_deck_summary_page(c: pdfcanvas.Canvas, deck: CardDeck) -> None:
    _heading(c, "R3 - Card deck summary (thread it exactly as listed, left to right)")
    rows = deck_summary_rows(deck)
    half = (len(rows) + 1) // 2
    columns = [rows[:half], rows[half:]]
    col_w = (PAGE_W - 2 * MARGIN) / 2
    for ci, column in enumerate(columns):
        x = MARGIN + ci * col_w
        y = PAGE_H - MARGIN - 40
        c.setFont("Helvetica", 10)
        for row in column:
            c.drawString(x, y, row)
            y -= 14


def _draw_start_position_page(c: pdfcanvas.Canvas, deck: CardDeck) -> None:
    _heading(c, "R4 - Starting position (set this up before the first pick)")
    c.setFont("Helvetica", 11)
    _paragraph_lines(c, start_position_text(deck), MARGIN, PAGE_H - 80)

    # card diagram: front face, viewed from the weaver's right.
    sq = 130
    x, y = MARGIN + 40, PAGE_H - 420
    c.setLineWidth(2)
    c.rect(x, y, sq, sq)
    r = 11
    corners = {
        "A": (x, y + sq), "D": (x + sq, y + sq),
        "B": (x, y), "C": (x + sq, y),
    }
    for label, (cx, cy) in corners.items():
        c.setFillColor(HexColor("#FFFFFF"))
        c.circle(cx, cy, r, stroke=1, fill=1)
        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(cx, cy - 4, label)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(x, y - 18, "front face, viewed from the weaver's right")
    c.drawString(x, y - 30, "holes A and D are UP; A and B face the warp, C and D face the cloth")


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build_pdf(deck: CardDeck, draft: InkleDraft, out_path=None) -> dict:
    """Render sections R1-R4 to a PDF; returns {'path': Path, 'pages': int}."""
    out = Path(out_path) if out_path is not None else Path(f"{deck.draft_name}.pdf")
    c = pdfcanvas.Canvas(str(out), pagesize=(PAGE_W, PAGE_H))
    _draw_title_page(c, deck, draft)
    c.showPage()
    _draw_threading_page(c, deck, draft)
    c.showPage()
    _draw_deck_summary_page(c, deck)
    c.showPage()
    _draw_start_position_page(c, deck)
    c.showPage()
    c.save()
    return {"path": out, "pages": 4}
