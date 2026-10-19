# Project State: inkle-to-card

> **Last updated:** 2026-10-18
> **Current phase:** polish (v0.1.0 shipped)
> **Overall health:** green

---

## 1. Goal (1-2 sentences)
Convert an inkle belt pattern into correlated card (tablet) weaving settings - per-card
A-D hole colors, S/Z threading, F/B turning sequence, explicit start position - and
render them as a PDF report.

## 2. Current Status
### Done
- [x] Research Step 1: domain foundations (research/RESEARCH.md, 27 cited sources, evidence-verified)
- [x] Research Step 2 additions: tablet styles (sec 11) + color selection guidance (sec 12)
- [x] Build plan: 10 prompts (PROMPTS.md)
- [x] Mapping design decision: Mapping A (1 end = 1 card, width-preserving) default; Mapping B (4 ends/card) optional
- [x] Prompt 1: scaffold + domain model (models.py) - 18 tests green
- [x] Prompt 2: inkle draft parsers (parsers.py) - JSON (2 shapes) + text format - 46 tests green total
- [x] Prompt 3: conversion engine (engine.py) - mappings A and B
- [x] Prompt 4: turning sequences + twist accounting (turning.py)
- [x] Prompt 5: band face simulator (simulate.py)
- [x] Prompt 6: color utilities (colors.py) - value contrast, ladder, suggestions
- [x] Prompt 7: PDF report part 1 (report.py) - R1 title, R2 threading table, R3 deck summary, R4 start position
- [x] Prompt 8: PDF report part 2 - R5 turning chart, R6 woven preview, R7 materials, R8 legend, R9 warnings
- [x] Prompt 9: CLI (convert/demo) + 3 bundled starter patterns
- [x] Prompt 10: README (Phosphorus voice), docs/DRAFT-FORMAT.md, examples/*.pdf, CLI warning-count fix, v0.1.0 tag - 130 tests green

### In Progress
- [ ] v0.2 candidates (not scheduled): double-face pick-up translation, Seizenn/TDD pattern import, calibration from a hand-woven band

### Not Started
- Step 5 validation: weave a sample band from examples/quiet-harbor-17.pdf and correct the model where the cloth disagrees

## 3. Architecture & Key Decisions
| Decision | Rationale | Date |
|---|---|---|
| Mapping A default (1 inkle end = 1 card, all 4 holes that color) | Preserves the belt pattern at full width; research RESEARCH.md sec 7 | 2026-10-18 |
| Mapping B optional (4 ends/card) | Material-efficient; matches Mullarkey-style drafts; pattern compressed 1/4 | 2026-10-18 |
| SURFACE_CYCLE = D,C,B,A,A,B,C,D from home position | Keith: 4F-4B from standard position shows rows D,C,B,A,A,B,C,D | 2026-10-18 |
| Start position convention: A/D up, printed side right, Tablet 1 left | keithweaves + Capriest + Little Looms; stated explicitly in PDF because conventions differ | 2026-10-18 |
| src/ layout + project venv (.venv) + reportlab | Hermes host has no pip/pytest in runtime python | 2026-10-18 |

## 4. Blockers & Risks
- **Risk:** reportlab pip install on ARM64 Jetson - verify in venv setup; fallback: pure-stdlib PDF writer (P7 contingency).
- **Risk:** value-contrast warning threshold uncalibrated - pick 1.8:1 default, revisit in P6 tests.

## 5. Next Step (only ONE)
> **Next:** Weave a sample band from examples/quiet-harbor-17.pdf (Step 5 validation) - then decide v0.2 scope.

## 6. Environment & Tooling Notes
- Python 3.14.7; project venv at .venv (`.venv/bin/python -m pytest -q`)
- pytest + reportlab installed into .venv only (never the Hermes runtime python)
- gh CLI authed as drwjkirkpatrick-web; default branch main
- Citation ledger: research/citations/ledger.json (39 sources; do not reset)

## 7. Recent Session Log
- 2026-10-18: Research Step 1 (domain foundations) grounded + verified; saved RESEARCH.md, README.md.
- 2026-10-18: Research Step 2 (tablet styles, color selection) added as sections 11-12; mapping corrected to A-default; PROMPTS.md build plan; scaffold.
- 2026-10-18: Prompt 1 executed: models.py + 18 tests green; repo published.
- 2026-10-18: Prompt 2 executed: parsers.py (JSON ends/order shapes + text format, format sniffing) + 28 tests.
- 2026-10-18: Prompts 3-9 executed one-commit-per-prompt: engine, turning, simulate, colors, report R1-R9, CLI + patterns (130 tests).
- 2026-10-18: Prompt 10 executed: docs + examples + v0.1.0 tag. All 10 prompts complete.

## 8. References
- Research: research/RESEARCH.md (grounded, citation-verified)
- Build plan: PROMPTS.md
