# 🔥 inkle-to-card

**Turn any inkle belt pattern into a complete card (tablet) weaving setup —
threading draft, colors, positions, turning chart, and a crystal-clear
starting position — rendered as a beautiful nine-page PDF you can follow at
the loom.**

You drew your belt as an inkle draft. Your heart says card weaving — those
mesmerizing turned patterns, that pack of cards riding your inkle loom. But
every tool you found speaks *tablet* in and *tablet* out; nobody translates
an inkle pattern into card settings. So this project does exactly that, in
one command, grounded in published weaving conventions and 39 cited
sources (`research/RESEARCH.md`).

## What you get

One command, one PDF, everything the loom asks of you:

- **R1 Title** — name, mapping, card and end counts
- **R2 Threading draft** — one column per card, rows A–D, colored cells, S/Z row
- **R3 Deck summary** — every card's four hole colors, spelled out
- **R4 Starting position** — holes A and D up, printed side right, card 1 left,
  with a diagram — stated explicitly, because books genuinely disagree here
- **R5 Turning chart** — pick by pick, with the twist-neutral 4F-4B shorthand
- **R6 Woven preview** — what the face of your band should look like, predicted
- **R7 Materials** — warp length (1.2 × finished + 50 cm), yarn per color, card count
- **R8 Notation legend** — A–D labels, F/B, S/Z, and the mark-your-cards habit
- **R9 Warnings** — twist buildup, grain mismatch, and low value contrast

## Quickstart

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/inkletocard demo --list          # three starter patterns
.venv/bin/inkletocard demo first-band      # writes first-band.pdf
.venv/bin/inkletocard convert my-draft.json -o belt.pdf
```

No PDF? Add `--no-pdf` and read the full deck summary and an ASCII preview
right in your terminal.

## Write your draft in 30 seconds

JSON (what the bundled patterns use):

```json
{"name": "my belt",
 "palette": {"navy": "#1B2A4A", "cream": "#F5F0E6"},
 "order": "navy navy cream cream navy navy cream cream",
 "heddles": "H U H U H U H U"}
```

...or plain text at the loom table:

```text
name: my belt
palette: navy #1B2A4A, cream #F5F0E6
ends: navy H | cream U | cream H | navy U | navy H | cream U | cream H | navy U
```

Full grammar and every error message: `docs/DRAFT-FORMAT.md`.

## Two ways to map ends onto cards

- **Mapping A (default)** — one end per card, all four holes that end's color.
  Your belt pattern weaves at **full width**, stripe for stripe.
- **Mapping B (`--mapping B`)** — four ends per card, a quarter as wide and
  a quarter the thread, with each card's holes arranged so the 8-pick
  4F-4B cycle shows your four colors in draft order.

## Color help built in

Value contrast — light against dark — is what makes a band pattern read, far
more than hue. Weavers test it with a black-and-white photo of their yarns;
this tool runs that test numerically: your PDF gets a value ladder, and any
stripe boundary that will not read gets a warning with the numbers.

## Photos in, drafts out (v0.2)

Photograph your yarn and get a draft-ready palette, with pixel shares and
human color names:

```bash
.venv/bin/inkletocard palette yarn.jpg --colors 4
```

Ask "which of *my* yarns can weave this pattern?" - match a photo against a
draft's palette and see which palette colors the photo never shows:

```bash
.venv/bin/inkletocard palette stash.jpg --match my-belt.json
```

Import a pattern from a photo of a 2-row chart - a book scan or another
tool's screenshot - and go straight to the PDF (top row = heddled ends,
bottom = open, warp order top/bottom per column, exactly as inkle drafts
are read):

```bash
.venv/bin/inkletocard import-grid chart.png --cols 17 --name harbor \
    --save-draft harbor.json
```

Grid cells are sampled over their central half (grid lines and margins are
ignored), colors cluster into at most 12 named palette entries, and the
imported draft is validated before it converts.

## Examples

Three starter bands, ready to weave: `examples/first-band.pdf`,
`examples/quiet-harbor-17.pdf`, `examples/belt-stripes-40.pdf`.

## Honest limitations

- Baltic pick-up patterns are out of scope for v0.1 — the card-woven analog
  is double-face technique (two light, two dark), a planned v0.2 extension.
- Under Mapping B, stripe features narrower than four ends will not read at
  full width; the PDF says so on the warnings page.
- The surface-sequence model (D, C, B, A, A, B, C, D from home position) is
  validated against published drafts but not yet against a hand-woven band
  of our own — that weave test is the next milestone.

## Research basis

Every convention this tool follows is cited and evidence-quoted in
`research/RESEARCH.md` — 39 sources in a verifiable citation ledger
(`research/citations/ledger.json`), fetched page text in `research/pages/`.
