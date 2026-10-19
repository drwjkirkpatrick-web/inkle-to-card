# Weave test: validating the model against real cloth

The surface-sequence model (`SURFACE_CYCLE = D, C, B, A, A, B, C, D` from
home position, holes A and D up) is validated against published drafts and
sources, but not yet against hand-woven cloth. This page is the protocol
for the first weave test. It also covers the two import assumptions flagged
in research section 13 (TDD hole-row order, home-slash = forward).

## What to weave

1. **Primary:** `examples/quiet-harbor-17.pdf` - Mapping A, 17 cards,
   4 colors, the standard 4F-4B pack sequence.
2. **Optional, tests the import rules:** any TDD `.tdd` band imported with
   `inkletocard import-tdd` - ideally one whose woven result you already know.

## Setup checks (before the first pick)

- Cards labeled A, B, C, D clockwise on the front face, printed side facing
  right, card 1 at the left of the pack, holes A and D up (PDF page R4).
- Warp length cut per page R7: 1.2 x finished length + 50 cm per thread.
- Weft in the selvedge color; belt shuttle.

## What to record (weave at least 2 full 8-pick repeats)

| # | Expected (from the PDF) | Observed | Notes |
|---|---|---|---|
| 1 | Column order left-to-right = draft ends 1..17 | | |
| 2 | One constant color per column (all 4 holes same color) | | |
| 3 | Stripe boundaries match the R6 preview's columns | | |
| 4 | Picks 5-8 mirror picks 1-4 (invisible for solid cards - any visible change is a finding) | | |
| 5 | No twist building up at the far end (4F-4B is balanced) | | |
| 6 | Band width roughly 17 x thread diameter | | |

## Reading the result

- **Column colors in the wrong order** -> the surface-cycle start is off.
  Record which color showed at pick 1; the fix lands in the simulator
  constants plus a test.
- **First pick shows a color that is not hole D's** -> home-position or
  hole-labeling assumption is wrong. For `.tdd` imports, retry with
  `--holes DCBA`; if that fixes it, DCBA becomes the documented default.
- **Twist accumulates anyway** -> turning-sequence mismatch; note the pick
  count where the cards became hard to turn.
- **Everything matches** -> the model is cloth-validated: update
  Project_state.md and the README limitations section, tag the release
  `weave-validated`, and the two import assumptions graduate from
  "derived" to "confirmed".

## How to report

Open a GitHub issue (or just tell Hermes) with the table filled in and a
phone photo of the band beside PDF page R6. Deviations become constant
fixes plus regression tests; the goal is preview == cloth.
