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
import sys
from pathlib import Path

from . import __version__
from .colors import check_draft_contrast, mixing_note
from .engine import convert_draft
from .models import DraftError, InkleDraft
from .parsers import parse_draft
from .report import build_pdf
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


def _run_conversion(draft: InkleDraft, args) -> int:
    deck = convert_draft(draft, mapping=args.mapping)
    attach_turning(deck, gen_4f4b(len(deck.cards)))
    preview = simulate_band(deck)
    contrast = check_draft_contrast(draft)
    mixing = mixing_note(draft)
    n_warnings = len(deck.warnings) + len(preview.warnings) + len(contrast) + len(mixing)

    print(f"{draft.name} -> {len(deck.cards)} cards (Mapping {args.mapping})")
    print("Turning: 4F 4B (twist-neutral pack sequence)")
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
    result = build_pdf(deck, draft, out)
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
    p_convert.add_argument("--finished-cm", type=float, default=150.0,
                           help="finished band length in cm (warp-length math)")
    p_convert.add_argument("--no-pdf", action="store_true",
                           help="print deck summary and ascii preview instead of a PDF")

    p_demo = sub.add_parser("demo", help="run a bundled starter pattern end to end")
    p_demo.add_argument("name", nargs="?", default="first-band",
                        help="bundled pattern name (see --list)")
    p_demo.add_argument("-o", "--out", default=None, help="output PDF path")
    p_demo.add_argument("--mapping", choices=("A", "B"), default="A")
    p_demo.add_argument("--finished-cm", type=float, default=150.0)
    p_demo.add_argument("--no-pdf", action="store_true")
    p_demo.add_argument("--list", action="store_true", help="list bundled patterns")

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

    except (DraftError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
