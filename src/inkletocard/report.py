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
# R5-R9 builders (Prompt 8)
# ---------------------------------------------------------------------------

def turning_chart_data(deck: CardDeck) -> dict:
    """The pick-by-pick turning chart as data, plus a pack shorthand.

    Shorthand is only produced when every card turns the same way in every
    pick (true pack weaving) - e.g. gen_4f4b yields "4F 4B". With per-card
    overrides there is no safe shorthand and the chart must be read cell by
    cell (uniform=False).
    """
    if not deck.picks:
        raise ValueError("no picks attached - build a turning sequence first")
    n = len(deck.cards)
    rows: list[list[str]] = []
    pack_dirs: list[str] = []
    uniform = True
    for pick in deck.picks:
        if len(pick.turns) not in (0, n):
            raise ValueError(f"a pick carries {len(pick.turns)} turns but the deck has {n} cards")
        if len(pick.turns) == 0:
            raise ValueError("pack-shorthand picks are ambiguous - build explicit picks")
        dirs = [turn.value for turn in pick.turns]
        rows.append(dirs)
        if len(set(dirs)) == 1:
            pack_dirs.append(dirs[0])
        else:
            uniform = False
    shorthand = None
    if uniform:
        runs: list[str] = []
        for d in pack_dirs:
            if runs and runs[-1].endswith(d):
                runs[-1] = str(int(runs[-1][:-1]) + 1) + d  # "4F" style, count first
            else:
                runs.append("1" + d)
        shorthand = " ".join(runs)
    return {"picks": len(rows), "cards": n, "rows": rows, "uniform": uniform,
            "shorthand": shorthand}


def materials_report(deck: CardDeck, draft: InkleDraft, finished_cm: float = 150.0,
                     take_up: float = 0.2, loom_waste_cm: float = 50.0) -> dict:
    """Yarn and card counts for the materials page (research section 3, 6).

    Warp length rule of thumb: 1.2 x finished length + 50 cm allowance for
    take-up and loom waste (Phiala's formula; Mullarkey's laces use explicit
    take-up and loom-waste allowances instead - both are supported here).
    """
    warp_cm = finished_cm * (1.0 + take_up) + loom_waste_cm
    counts = draft.color_counts()
    threads_per_color: dict[str, int] = {}
    for color, ends in counts.items():
        threads_per_color[color] = ends * 4 if deck.mapping == "A" else ends
    per_color_meters = {
        color: round(threads * warp_cm / 100.0, 1)
        for color, threads in threads_per_color.items()
    }
    return {
        "finished_cm": finished_cm,
        "take_up": take_up,
        "loom_waste_cm": loom_waste_cm,
        "warp_length_cm": round(warp_cm, 1),
        "threads_per_color": threads_per_color,
        "per_color_meters": per_color_meters,
        "card_count": len(deck.cards),
        "shuttle_note": "One belt shuttle (a shuttle with one beveled edge packs the weft tightly).",
        "formula": f"warp length = {finished_cm:g} cm x {1.0 + take_up:g} + {loom_waste_cm:g} cm = {warp_cm:.0f} cm",
    }


def legend_text() -> str:
    """The notation legend page (research sections 3, 8, 11)."""
    return (
        "Holes: each card has four holes labeled A, B, C, D clockwise on its front face.\n"
        "Threading: S or Z - which way the warp is strung through the holes; every\n"
        'hole of a card is strung the same direction. Community slash notation:\n'
        '"/" = Z-threading, "\\" = S-threading.\n'
        "Turning: F = forward quarter turn (away from you, like a bicycle wheel\n"
        "from the weaver's seat); B = backward quarter turn (toward you).\n"
        "A pick = one quarter turn of every card + one pass of the weft.\n"
        "Home position: holes A and D up before the first pick.\n"
        "Cards: number them left to right, printed sides facing right; if your\n"
        "cards have colored bands or striped edges, keep them all oriented the\n"
        "same way so a turned-around card is easy to spot.\n"
        "A magenta cell anywhere in this report means an unknown color name -\n"
        "fix the draft's palette before weaving."
    )


def warnings_list(deck: CardDeck, draft: InkleDraft, preview=None, extra=None) -> list[str]:
    """Aggregate every warning the report should print, numbered in the PDF."""
    items = list(deck.warnings)
    if preview is not None:
        items.extend(preview.warnings)
    from .colors import check_draft_contrast, mixing_note
    items.extend(check_draft_contrast(draft))
    items.extend(mixing_note(draft))
    if extra:
        items.extend(extra)
    # de-duplicate while keeping order
    seen: set[str] = set()
    unique = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _draw_turning_chart_page(c: pdfcanvas.Canvas, deck: CardDeck) -> None:
    _heading(c, "R5 - Turning chart (one row per pick, one column per card)")
    data = turning_chart_data(deck)
    c.setFont("Helvetica", 12)
    if data["shorthand"]:
        c.drawString(MARGIN, PAGE_H - 70,
                     f"Turn the whole pack as one: {data['shorthand']}"
                     "   (F = forward/away, B = backward/toward)")
    else:
        c.drawString(MARGIN, PAGE_H - 70,
                     "Cards turn individually - read every cell before each pick.")
    x0 = MARGIN + 34
    cell_w = min(24.0, (PAGE_W - MARGIN - x0) / max(data["cards"], 1))
    top = PAGE_H - 100
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN, top + 4, "pick")
    for i in range(data["cards"]):
        c.setFont("Helvetica", 7)
        c.drawCentredString(x0 + i * cell_w + cell_w / 2, top + 4, str(i + 1)[-3:])
    for r, row in enumerate(data["rows"]):
        y = top - (r + 1) * 14
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN, y, str(r + 1))
        c.setFont("Helvetica", 10)
        for i, turn in enumerate(row):
            c.drawCentredString(x0 + i * cell_w + cell_w / 2, y, turn)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(MARGIN, top - (data["picks"] + 1) * 14 - 10,
                 "Turn the pack, pass the weft, beat - one pick per row. 4F-4B is twist-neutral.")


def _draw_preview_page(c: pdfcanvas.Canvas, deck: CardDeck, draft: InkleDraft, preview) -> None:
    _heading(c, "R6 - Woven preview (what the face of the band should look like)")
    if not preview or not preview.grid:
        c.setFont("Helvetica", 12)
        c.drawString(MARGIN, PAGE_H - 80, "No preview available - attach a turning sequence first.")
        return
    picks = len(preview.grid)
    n = len(preview.card_numbers)
    usable_w = PAGE_W - 2 * MARGIN
    usable_h = PAGE_H - 2 * MARGIN - 60
    cell = max(4.0, min(18.0, usable_w / max(n, 1), usable_h / max(picks, 1)))
    x0 = MARGIN + 30
    y0 = PAGE_H - MARGIN - 50 - picks * cell
    for r, row in enumerate(preview.grid):
        for i, color_name in enumerate(row):
            c.setFillColor(_hex(draft.palette, color_name))
            c.rect(x0 + i * cell, y0 + (picks - 1 - r) * cell, cell - 0.5, cell - 0.5,
                   stroke=0, fill=1)
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(MARGIN, y0 - 16,
                 "pick 1 at the bottom, growing upward as woven; card 1 at the left")
    c.drawString(MARGIN, y0 - 28,
                 "this prediction assumes the home position from page R4 and the attached turning sequence")


def _draw_materials_page(c: pdfcanvas.Canvas, deck: CardDeck, draft: InkleDraft,
                         materials: dict) -> None:
    _heading(c, "R7 - Materials")
    c.setFont("Helvetica", 12)
    lines = [
        materials["formula"],
        f"Warp length to cut: {materials['warp_length_cm']:.0f} cm per thread "
        f"({materials['warp_length_cm'] / 100:.1f} m)",
        f"Cards: {materials['card_count']} four-hole cards",
        "",
        "Warp threads and yarn per color:",
    ]
    for color, meters in sorted(materials["per_color_meters"].items()):
        threads = materials["threads_per_color"][color]
        lines.append(f"  {color}: {threads} threads x {materials['warp_length_cm'] / 100:.1f} m = {meters} m")
    lines += [
        "",
        materials["shuttle_note"],
        "Weft: about the same yardage as one color's warp, in the selvedge color.",
        "Yarn: smooth, strong, relatively inelastic (research section 2) - perle",
        "cotton 3/2 or 5/2, embroidery floss, or firmly twisted wool.",
    ]
    _paragraph_lines(c, "\n".join(lines), MARGIN, PAGE_H - 80, leading=16)


def _draw_legend_page(c: pdfcanvas.Canvas) -> None:
    _heading(c, "R8 - Notation legend")
    c.setFont("Helvetica", 11)
    _paragraph_lines(c, legend_text(), MARGIN, PAGE_H - 80, leading=16)


def _draw_warnings_page(c: pdfcanvas.Canvas, warnings: list[str]) -> None:
    _heading(c, "R9 - Warnings (read before warping)")
    c.setFont("Helvetica", 11)
    if not warnings:
        c.drawString(MARGIN, PAGE_H - 80, "No warnings - weave happy.")
        return
    numbered = [f"{i}. {w}" for i, w in enumerate(warnings, start=1)]
    _paragraph_lines(c, "\n".join(numbered), MARGIN, PAGE_H - 80, leading=15)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build_pdf(deck: CardDeck, draft: InkleDraft, out_path=None, preview=None,
              materials=None, extra_warnings=None) -> dict:
    """Render the full report (R1-R9) to a PDF; returns {'path', 'pages'}.

    NOTE: out_path stays the third argument so existing callers
    (build_pdf(deck, draft, path)) keep working.
    """
    if preview is None:
        from .simulate import simulate_band
        preview = simulate_band(deck)
    if materials is None:
        materials = materials_report(deck, draft)
    warnings = warnings_list(deck, draft, preview=preview, extra=extra_warnings)

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
    _draw_turning_chart_page(c, deck)
    c.showPage()
    _draw_preview_page(c, deck, draft, preview)
    c.showPage()
    _draw_materials_page(c, deck, draft, materials)
    c.showPage()
    _draw_legend_page(c)
    c.showPage()
    _draw_warnings_page(c, warnings)
    c.showPage()
    c.save()
    return {"path": out, "pages": 9}
