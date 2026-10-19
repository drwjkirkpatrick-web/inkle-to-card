# PROMPTS.md - inkle-to-card build plan (10 prompts, v0.1 core)

Conventions for every prompt:
- Test runner: `.venv/bin/python -m pytest -q` (project venv; never the system python).
- Compile check before commit: `.venv/bin/python -m py_compile src/inkletocard/<module>.py`.
- One agent per file: each prompt's listed files are owned exclusively by its executor; the
  parent owns all shared files (`__init__.py`, `pyproject.toml`, README.md, Project_state.md).
- Every module gets a teaching-notes docstring (NOTE:/WHY: comments for a non-coder reader).
- Finish each prompt: compile -> tests green -> `git add <files>` -> commit `Pn: <desc>` -> push.
- Research basis and citation ids: research/RESEARCH.md. Key constants: HOLE_ORDER = A,B,C,D;
  SURFACE_CYCLE = D,C,B,A,A,B,C,D (4F-4B from home position, holes A and D up).

Dependency table:

    P1 models -> P2 parsers -> P3 engine -> P4 turning -> P5 simulate -> P8 pdf2
                          \-> P6 colors -> P7 pdf1 -> P8 pdf2 -> P9 cli -> P10 docs

---

## Prompt 1 - Scaffold + domain model
**Files (parent-owned):** `src/inkletocard/__init__.py`, `src/inkletocard/models.py`,
`tests/test_models.py`
**Spec:** enums `ThreadingDirection` (S, Z) and `Turn` (F, B); constants `HOLE_ORDER =
("A","B","C","D")` and `SURFACE_CYCLE = ("D","C","B","A","A","B","C","D")`. Dataclasses:
`End(index, color_name, heddled: bool)`, `InkleDraft(name, palette: dict[str,str],
ends: list[End])` with `validate()` (hex format, heddled/open alternation, >= 8 ends),
`Card(number, hole_colors: dict[str,str], threading: ThreadingDirection)`,
`StartPosition(top_holes=("A","D"), face="right", tablet_one="left", description)`,
`Pick(turns: list[Turn])` (one entry per card; empty = pack turn shorthand),
`CardDeck(draft_name, mapping, cards, start_position, picks, warnings)`.
`to_dict()/from_dict()` on each dataclass, filtering to `__dataclass_fields__` (computed
properties must not break round-trips).
**Tests:** round-trip equality for every dataclass; alternation validator rejects U,U;
hex validator rejects "navy"; SURFACE_CYCLE length 8 and first element "D"; a Card
reports all four holes.
**Acceptance:** `pytest -q` green; `import inkletocard` works.
**Commit:** `P1: scaffold + domain model`

## Prompt 2 - Inkle draft parsers
**Files:** `src/inkletocard/parsers.py`, `tests/test_parsers.py`
**Spec:** `parse_inkle_json(text_or_path)` accepting two shapes: (a) `"ends": [{"color":
..., "heddled": ...}]`, (b) `"order": "navy cream cream"` + `"heddles": "H U U"`.
`parse_inkle_text(text)` for a plain format with `name:`, `palette: name #hex, ...`,
`ends: <color> <H|U> | <color> <H|U> | ...`. All errors raise `DraftError` with the
offending line/context: unknown color name (list palette keys), bad hex, non-alternating
heddles, empty ends. Both parsers call `draft.validate()` before returning.
**Tests:** both JSON shapes; text format; each error case asserts the message content.
**Acceptance:** fixture strings parse to InkleDraft; errors are actionable.
**Commit:** `P2: inkle draft parsers (JSON + text)`

## Prompt 3 - Conversion engine (ends -> cards)
**Files:** `src/inkletocard/engine.py`, `tests/test_engine.py`
**Spec:** `convert_draft(draft, mapping="A") -> CardDeck`.
Mapping A (default, width-preserving): card i carries end i's color in all four holes;
deck order = draft order left to right. Mapping B (narrow): four consecutive ends per
card with holes arranged so the surface cycle shows the draft order - hole D = first end
of the group, C = second, B = third, A = fourth (so picks 0-3 show ends 1-4, picks 4-7
mirror them, per the 4F-4B mirror rule). Width not a multiple of 4 under B: pad the last
card with the draft's edge color and add a warning. Threading direction: all cards Z
(v1 documented choice). Warnings: Mapping B lists lost sub-4-end features; Mapping A
notes 4x thread consumption.
**Tests:** 17-end draft -> A yields 17 cards, all holes = end color, order preserved;
B yields 5 cards (last padded) + warning; 40-end draft -> B yields 10 cards, card 1 hole
D = end 1 color and hole A = end 4 color; A never pads.
**Acceptance:** both mappings produce valid decks; Mullarkey 40-end/10-card case passes.
**Commit:** `P3: conversion engine, mappings A and B`

## Prompt 4 - Threading direction + turning sequences
**Files:** `src/inkletocard/turning.py`, `tests/test_turning.py`
**Spec:** `gen_4f4b(n_cards, repeats=1) -> list[Pick]` (pack shorthand: 4 forward, 4
backward); `build_picks(rows) -> list[Pick]` for per-card overrides; `net_quarter_turns(deck)
-> dict[int, int]` per card (+1 per F, -1 per B); `twist_warnings(deck)` flags |net| > 4
(twist buildup). Home position note in docstrings: all cards start holes A and D up.
**Tests:** 4F-4B net 0 per card; 8F net +8 with warning; generated 8 picks alternate
F,B correctly; per-card override changes only that card's row.
**Acceptance:** twist accounting correct; warnings fire on unbalanced sequences.
**Commit:** `P4: turning sequences + twist accounting`

## Prompt 5 - Band face simulator
**Files:** `src/inkletocard/simulate.py`, `tests/test_simulate.py`
**Spec:** `simulate_band(deck, picks) -> BandPreview` where `grid[pick][card]` = color
name on the top face at that pick: hole = SURFACE_CYCLE[pick % 8], color =
card.hole_colors[hole] (from home position). `ascii_render(preview) -> str` for text
mode; `column_summary(preview)` = per-card color runs; aggregate deck warnings +
grain-mismatch detection under Mapping B (single-end features) into preview warnings.
**Tests:** solid card (all holes one color) -> column constant across 8 picks;
4-color Mapping-B card cycles exactly D,C,B,A,A,B,C,D; preview width == len(cards).
**Acceptance:** simulator output matches the research surface-sequence rule.
**Commit:** `P5: band face simulator`

## Prompt 6 - Color utilities (value contrast)
**Files:** `src/inkletocard/colors.py`, `tests/test_colors.py`
**Spec:** `relative_luminance(hex) -> float` (WCAG formula), `contrast_ratio(a, b) ->
float`, `value_ladder(palette) -> list` sorted dark-to-light, `check_draft_contrast(draft,
threshold=1.8) -> list[Warning]` for adjacent stripe-block boundaries with low value
contrast (the digital black-and-white-photo test), `CSS_NAMES` small builtin table +
`suggest_name(hex) -> str`. Include the mixing caveat helper `mixing_note(draft)` for
sub-2-end features.
**Tests:** white vs black ratio ~21; same-color pair warns; ladder sorted; known luminance
of #FFFFFF == 1.0; suggest_name basic hits.
**Acceptance:** low-contrast drafts get warnings with human-readable text.
**Commit:** `P6: color utilities + value contrast checks`

## Prompt 7 - PDF report, part 1 (P1-P4 of the report spec)
**Files:** `src/inkletocard/report.py`, `tests/test_report.py`
**Spec:** reportlab canvas; `build_pdf(deck, draft, preview, out_path)`. Sections:
R1 title block (name, date, mapping, card/end counts); R2 threading draft table - one
column per card L->R, rows A-D with colored cells, fifth row S/Z; R3 deck summary per
card; R4 starting position page - explicit convention text (holes A and D up, printed
side toward the right, Tablet 1 at the left) plus a drawn card diagram (square + four
labeled corner circles A-D). Guard with `pytest.importorskip("reportlab")`.
**Tests:** smoke: build from a fixture deck -> bytes start with %PDF, >= 2 pages
(count via page-callback or pypdf if available); section builder functions return
structured data (testable without drawing).
**Acceptance:** a real PDF renders for a fixture deck.
**Commit:** `P7: PDF report part 1 (draft table, deck, start position)`

## Prompt 8 - PDF report, part 2 (P5-P9 of the report spec)
**Files:** extend `src/inkletocard/report.py`, extend `tests/test_report.py`
**Spec:** R5 turning chart (rows = picks; pack shorthand "4F 4B" when uniform); R6 woven
preview grid (colored rectangles per pick/card); R7 materials - yarn per color = ends of
that color x warp length, warp length = 1.2 x finished + 50 cm (overridable take-up and
loom-waste), card count, shuttle note; R8 legend (A-D labels, F/B, S/Z with "/" = Z,
"\" = S, mark-your-cards advice); R9 warnings page (twist, mapping, grain, low contrast).
**Tests:** full build -> >= 4 pages; turning chart builder correct for 4F-4B and
overrides; materials math (40 ends 80" -> expected totals).
**Acceptance:** complete PDF for the demo deck with all nine sections.
**Commit:** `P8: PDF report part 2 (turning, preview, materials, legend, warnings)`

## Prompt 9 - CLI + bundled starter patterns
**Files:** `src/inkletocard/cli.py`, `patterns/first-band.json`,
`patterns/quiet-harbor-17.json`, `patterns/belt-stripes-40.json`, `tests/test_cli.py`
**Spec:** `main(argv)` with commands: `convert DRAFT [-o OUT.pdf] [--mapping A|B]
[--no-pdf]` (no-pdf prints deck summary + ascii preview), `demo [NAME] [--list]`.
Bundled patterns: first-band (8 ends, 2 colors), quiet-harbor-17 (17 ends, 4 colors,
9H/8U), belt-stripes-40 (40 ends, 2 colors). End-to-end: parse -> convert -> turning ->
simulate -> contrast check -> report.
**Tests:** `main(["demo","first-band","-o",tmp])` exits 0 and writes a PDF;
`--no-pdf` prints hole colors; `--list` shows 3 names; convert of each bundled pattern
round-trips.
**Acceptance:** one command from draft file to PDF.
**Commit:** `P9: CLI + bundled starter patterns`

## Prompt 10 - Docs, examples, release polish
**Files:** rewrite `README.md` (Phosphorus voice: lead with what makes the project
special, warm + community tone, feature-first), `docs/DRAFT-FORMAT.md` (both input
formats with copy-paste examples), regenerate `examples/*.pdf` from the 3 bundled
patterns, update `Project_state.md`, tag `v0.1.0`.
**Spec:** README quickstart commands must actually run as written; limitations section
honest (Mapping B grain loss, pick-up out of scope, conventions declared); link
research/RESEARCH.md as the evidence base.
**Tests:** full suite green; README command smoke (demo runs).
**Acceptance:** v0.1.0 tagged and pushed; a weaver can go from idea to card deck in one
command.
**Commit:** `P10: docs, examples, v0.1.0`


---

## Prompt 11 (v0.2, executed 2026-10-18) - Photo import: palettes, matching, pattern grids

**Files:** `src/inkletocard/photo.py`, `tests/test_photo.py`, CLI commands
`palette` and `import-grid`, docs updates.

**Spec (as built):**
- `extract_palette(photo, n_colors=6)`: adaptive-quantize the photo, report each
  dominant color as hex + nearest common name (deduped) + pixel share.
- `match_colors(swatches, palette)`: snap each photo color to the nearest draft
  palette color (close = within 90 RGB distance, tunable); list palette colors
  the photo never shows.
- `import_grid(photo, cols)`: read a 2-row draft chart photo - central-half cell
  sampling, 25% auto border peel, cluster to <=12 named colors, warp order
  top/bottom per column (research section 2), validate before returning.
- CLI: `inkletocard palette PHOTO [--colors N] [--match DRAFT] [-o JSON]` and
  `inkletocard import-grid PHOTO --cols N [--name] [--save-draft] [-o PDF]`,
  reusing the full conversion pipeline. `--finished-cm` now actually reaches the
  materials page. Pillow added as a dependency.

**Acceptance:** photo tests green (Pillow-gated), CLI end-to-end tests green,
imported drafts round-trip through the JSON format.
