# inkle-to-card

Convert an inkle belt pattern into correlated card (tablet) weaving settings - per-card
A-D hole colors, S/Z threading direction, F/B turning sequence, and an explicit deck
start position - and render them as a PDF report.

Status: research Step 1 complete (2026-10-18). Grounded report: research/RESEARCH.md
(citation ledger: research/citations/ledger.json; fetched page evidence: research/pages/).

## Headline findings
- Inkle draft = warp-only 2-row grid (top heddled / bottom unheddled), 1 square = 1 end,
  read left to right. Weft invisible (warp-faced).
- Card settings = hole colors A-D + S/Z threading + F/B turning per pick + deck start
  position. "Home position": holes A and D up; conventions DIFFER between books
  (Groff requires A/D toward the fell) - the program must state its convention.
- Tablets are routinely woven ON an inkle loom: 4 ends per card, the card stack replaces
  the heddles (Mullarkey's laces: 40 ends -> 10 four-hole cards).
- 4F-4B turning from standard position shows surface rows D,C,B,A,A,B,C,D - the
  prediction model for the converter (Keith: turning 4F-4B shows rows D,C,B,A,A,B,C,D).
- Grain mismatch: inkle features narrower than 4 ends cannot map 1:1 (finest card
  feature = per-card 8-pick cycle). Baltic pick-up out of scope v1; double-face
  (2 light / 2 dark threading) is the later path.
- No existing tool converts inkle drafts -> card settings. Prior art: TDD
  (github.com/jamespbarrett/tabletweave), Twisted Threads (shelaghlewins.com,
  twistedthreads.org), GTT (guntram.co.za), Seizenn (raktres.net/seizenn - edits both
  inkle and tablet, no conversion), karetka (CSV tablet pattern -> turning
  instructions), cardweaver (DSL + synthesis), snaut/tabletweaving (JS editor).

## v1 mapping algorithm (derived; validate in Step 2)
1. Parse inkle draft -> ordered ends (color + heddled/open flag).
2. Assign ends to cards. Mapping A (default, width-preserving): 1 inkle end = 1
   card, all four holes that end's color (deck = inkle color sequence, full width).
   Mapping B (optional, --narrow): 4 ends per card, pattern compressed to 1/4 width.
3. S/Z per card by rule (S-threaded turned forward -> Z-twined cord).
4. Turning: 8-pick 4F-4B pack default; per-card overrides advanced.
5. Start: all cards home position (A,D up), printed side right, Tablet 1 left.
6. Emit: draft table (rows A-D + direction row), turning chart, start-position figure,
   materials.

## PDF report spec
P1 title block | P2 threading draft table (column per card, rows A-D + S/Z row) |
P3 card deck summary | P4 starting position (explicit convention + figure) |
P5 turning chart | P6 woven preview | P7 materials (warp = 1.2 x length + 50 cm) |
P8 notation legend | P9 twist-build-up warnings.

## Roadmap
Step 2: algorithm spec + hand-translate a 17-end starter (9H/8U), validate vs
TDD/Seizenn | Step 3: Python architecture (parser -> card model -> reportlab PDF) |
Step 4: build + tests, compile->test->commit->README->push main | Step 5: weave a
sample band, correct the model where the cloth disagrees.
