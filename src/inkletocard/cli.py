"""cli.py - the command line: from inkle draft to card-weaving PDF in one call.

USAGE
    inkletocard convert DRAFT.json [-o OUT.pdf] [--mapping A|B] [--finished-cm N]
    inkletocard convert DRAFT.inkle --no-pdf          # text summary + ascii preview
    inkletocard demo [NAME] [--list]                  # bundled starter patterns

The demo command exists because a weaver's first band should take minutes,
not setup time: pick a starter, get a nine-page PDF with the threading
draft, turning chart, materials, and an explicit starting position.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .colors import check_draft_contrast, mixing_note
from .engine import convert_draft
from .models import DraftError, InkleDraft
from .parsers import parse_draft
from .photo import extract_palette, import_grid, match_colors
from .importers import import_tdd
from .report import (
    build_pdf,
    materials_report,
    turning_chart_data,
    warnings_list,
)
from .simulate import ascii_render, simulate_band
from .turning import attach_turning, gen_4f4b

# src/inkletocard/cli.py -> parents[2] is the repo root, where patterns/ lives.
PATTERNS_DIR = Path(__file__).resolve().parents[2] / "patterns"


def _pattern_paths() -> dict[str, Path]:
    return {p.stem: p for p in sorted(PATTERNS_DIR.glob("*.json"))}


def _load_pattern(name: str) -> InkleDraft:
    paths = _pattern_paths()
    if name not in paths:
        raise DraftError(f"no bundled pattern {name!r}; available: {', '.join(paths)}")
    return parse_draft(paths[name])


def _resolve_finished_cm(args) -> float:
    """Accept --finished-cm or --finished-in (mutually exclusive); default 150 cm."""
    fin_in = getattr(args, "finished_in", None)
    fin_cm = getattr(args, "finished_cm", None)
    if fin_in is not None and fin_cm is not None:
        raise DraftError("give either --finished-cm or --finished-in, not both")
    if fin_in is not None:
        if fin_in <= 0:
            raise DraftError("--finished-in must be a positive length in inches")
        return fin_in * 2.54
    if fin_cm is not None:
        if fin_cm <= 0:
            raise DraftError("--finished-cm must be a positive length in centimeters")
        return fin_cm
    return 150.0


def _run_conversion(draft: InkleDraft, args, deck=None) -> int:
    # NOTE: imported decks arrive pre-built (cards + picks attached); drafts
    # from our own parsers run the conversion engine here.
    if deck is None:
        repeats = getattr(args, "repeats", 1)
        if repeats < 1:
            raise DraftError("--repeats must be at least 1")
        deck = convert_draft(draft, mapping=args.mapping)
        attach_turning(deck, gen_4f4b(len(deck.cards), repeats=repeats))
    preview = simulate_band(deck)
    n_warnings = len(warnings_list(deck, draft, preview=preview))  # deduped, same list as the PDF

    chart = turning_chart_data(deck)
    print(f"{draft.name} -> {len(deck.cards)} cards ({deck.mapping} deck)")
    if chart["shorthand"]:
        print(f"Turning: {chart['shorthand']} (F = forward/away, B = backward/toward)")
    else:
        print("Turning: cards turn individually - read the chart (PDF page R5)")
    print(f"Warnings: {n_warnings} (all listed in the PDF, page R9)")
    if args.no_pdf:
        print()
        for card in deck.cards:
            holes = "  ".join(f"{h}={card.hole_colors[h]}" for h in ("A", "B", "C", "D"))
            print(f"Card {card.number}: {holes}  [{card.threading.value}]")
        print()
        print(ascii_render(preview))
        print()
        print("Deck summary: cards are numbered left to right, printed side facing right;")
        print("start with holes A and D up (the home position) - details in the PDF.")
        return 0

    out = Path(args.out) if args.out else Path(f"{draft.name}.pdf")
    materials = materials_report(deck, draft, finished_cm=_resolve_finished_cm(args))
    result = build_pdf(deck, draft, out, materials=materials)
    print(f"PDF report: {result['path']} ({result['pages']} pages)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="inkletocard",
        description="Convert an inkle belt pattern into card (tablet) weaving "
                    "settings and a PDF report.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_convert = sub.add_parser("convert", help="convert a draft file (.json or .inkle)")
    p_convert.add_argument("draft", help="path to the draft file")
    p_convert.add_argument("-o", "--out", default=None, help="output PDF path")
    p_convert.add_argument("--mapping", choices=("A", "B"), default="A",
                           help="A: one end per card (full width, default); "
                                "B: four ends per card (quarter width)")
    p_convert.add_argument("--finished-cm", type=float, default=None,
                           help="finished band length in cm (warp-length math)")
    p_convert.add_argument("--finished-in", type=float, default=None,
                           help="finished band length in inches (alternative to --finished-cm)")
    p_convert.add_argument("--repeats", type=int, default=1,
                           help="8-pick 4F-4B cycles to chart (default 1)")
    p_convert.add_argument("--no-pdf", action="store_true",
                           help="print deck summary and ascii preview instead of a PDF")

    p_demo = sub.add_parser("demo", help="run a bundled starter pattern end to end")
    p_demo.add_argument("name", nargs="?", default="first-band",
                        help="bundled pattern name (see --list)")
    p_demo.add_argument("-o", "--out", default=None, help="output PDF path")
    p_demo.add_argument("--mapping", choices=("A", "B"), default="A")
    p_demo.add_argument("--finished-cm", type=float, default=None)
    p_demo.add_argument("--finished-in", type=float, default=None)
    p_demo.add_argument("--repeats", type=int, default=1)
    p_demo.add_argument("--no-pdf", action="store_true")
    p_demo.add_argument("--list", action="store_true", help="list bundled patterns")

    p_check = sub.add_parser("check", help="validate a draft and print loom-side facts (no PDF)")
    p_check.add_argument("draft", help="path to the draft file")
    p_check.add_argument("--mapping", choices=("A", "B"), default="A",
                         help="preview the card count under this mapping (default A)")

    p_tdd = sub.add_parser("import-tdd",
                           help="import a Tablet Weaving Draft Designer (.tdd) file")
    p_tdd.add_argument("file", help="path to the .tdd file")
    p_tdd.add_argument("--holes", default="ABCD",
                       help="hole letters of the chart rows, top to bottom (ABCD or DCBA)")
    p_tdd.add_argument("-o", "--out", default=None, help="output PDF path")
    p_tdd.add_argument("--save-draft", default=None,
                       help="save the imported deck's inkle view as JSON here")
    p_tdd.add_argument("--finished-cm", type=float, default=None)
    p_tdd.add_argument("--finished-in", type=float, default=None)
    p_tdd.add_argument("--no-pdf", action="store_true")

    p_palette = sub.add_parser("palette", help="extract a draft-ready palette from a photo")
    p_palette.add_argument("photo", help="photo of yarn, fabric, or a chart")
    p_palette.add_argument("--colors", type=int, default=6,
                           help="number of colors to extract (default 6)")
    p_palette.add_argument("--match", default=None,
                           help="draft file: match photo colors to this draft's palette")
    p_palette.add_argument("-o", "--out", default=None,
                           help="write the palette as JSON here")

    p_grid = sub.add_parser("import-grid",
                            help="import a draft from a photo of a 2-row chart")
    p_grid.add_argument("photo", help="photo of the chart (grid fills the frame)")
    p_grid.add_argument("--cols", type=int, required=True,
                        help="number of pattern columns in the chart")
    p_grid.add_argument("--name", default=None,
                        help="draft name (default: the photo's file name)")
    p_grid.add_argument("--save-draft", default=None,
                        help="also save the imported draft as JSON here")
    p_grid.add_argument("-o", "--out", default=None, help="output PDF path")
    p_grid.add_argument("--mapping", choices=("A", "B"), default="A")
    p_grid.add_argument("--finished-cm", type=float, default=None)
    p_grid.add_argument("--finished-in", type=float, default=None)
    p_grid.add_argument("--repeats", type=int, default=1)
    p_grid.add_argument("--no-pdf", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            if args.list:
                for name, path in _pattern_paths().items():
                    draft = parse_draft(path)
                    print(f"{name}: {len(draft.ends)} ends, "
                          f"{len(draft.palette)} colors - {path}")
                return 0
            draft = _load_pattern(args.name)
            return _run_conversion(draft, args)

        if args.command == "convert":
            draft = parse_draft(args.draft)
            return _run_conversion(draft, args)

        if args.command == "palette":
            swatches = extract_palette(args.photo, n_colors=args.colors)
            print(f"photo palette ({len(swatches)} colors):")
            for s in swatches:
                print(f"  {s['name']:<16} {s['hex']}   {s['share'] * 100:.0f}% of pixels")
            if args.match:
                target = parse_draft(args.match)
                report = match_colors(swatches, target.palette)
                print(f"\nmatched against {target.name!r} "
                      f"(close = within {report['tolerance']:.0f} RGB distance):")
                for m in report["matches"]:
                    tag = "exact" if m["distance"] == 0 else ("close" if m["close"] else "FAR")
                    print(f"  {m['hex']} ({m['share'] * 100:.0f}%) -> {m['match']} "
                          f"[{tag}, d={m['distance']}]")
                if report["missing"]:
                    print(f"  not seen in photo: {', '.join(report['missing'])}")
            print("\npaste into a text draft:")
            print("palette: " + ", ".join(f"{s['name']} {s['hex']}" for s in swatches))
            if args.out:
                Path(args.out).write_text(
                    json.dumps({s["name"]: s["hex"] for s in swatches}, indent=2) + "\n"
                )
                print(f"palette JSON written: {args.out}")
            return 0

        if args.command == "check":
            draft = parse_draft(args.draft)  # raises DraftError if invalid
            n_heddled = sum(1 for e in draft.ends if e.heddled)
            print(f"OK: {draft.name!r} - {len(draft.ends)} ends "
                  f"({n_heddled} heddled / {len(draft.ends) - n_heddled} open), "
                  f"{len(draft.palette)} colors")
            print("colors:")
            for name, count in sorted(draft.color_counts().items()):
                print(f"  {name:<14} {draft.palette[name]}  {count} ends")
            blocks = draft.stripe_blocks()
            shown = ", ".join(f"{color}x{width}" for color, width in blocks[:12])
            if len(blocks) > 12:
                shown += f" ... ({len(blocks)} blocks total)"
            print(f"stripe blocks: {shown}")
            deck = convert_draft(draft, mapping=args.mapping)
            attach_turning(deck, gen_4f4b(len(deck.cards)))
            print(f"mapping {args.mapping}: {len(deck.cards)} cards")
            from .simulate import simulate_band
            warns = warnings_list(deck, draft, preview=simulate_band(deck))
            if warns:
                print(f"warnings ({len(warns)}):")
                for w in warns:
                    print(f"  - {w}")
            else:
                print("no warnings")
            return 0

        if args.command == "import-tdd":
            imported = import_tdd(args.file, hole_rows=args.holes)
            if args.save_draft:
                Path(args.save_draft).write_text(
                    json.dumps(imported.draft.to_dict(), indent=2) + "\n"
                )
                print(f"draft saved: {args.save_draft}")
            return _run_conversion(imported.draft, args, deck=imported.deck)

        if args.command == "import-grid":
            draft = import_grid(args.photo, cols=args.cols, name=args.name)
            if args.save_draft:
                Path(args.save_draft).write_text(
                    json.dumps(draft.to_dict(), indent=2) + "\n"
                )
                print(f"draft saved: {args.save_draft}")
            return _run_conversion(draft, args)

    except (DraftError, ImportError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
