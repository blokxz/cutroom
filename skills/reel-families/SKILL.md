---
name: reel-families
description: Orchestrate a short Reel through template families in the fewest prompts — summarize repo and brief state first, pick or invent a family, synthesize rhythm-legal beat-sheet variations, then hand the chosen one to the video-direction pipeline. Use for reels, stories or posts where several original variations or a new template family are wanted.
---

# reel-families — router

Contract: `spec.md` (wins). Rules: `guidelines.md`. Run from the repo root; at most 3 user turns (L-02).

## Flow

| # | Step | Load |
|---|---|---|
| 1 | `python3 tools/reel_summary.py` → act on P0, then P1 touching this request | `references/summary-report.md` |
| 2 | Pick families, or `python3 tools/variation.py invent` | `references/family-taxonomy.md` · `references/variation-rules.md` |
| 3 | `variation.py sheet <family> --duration S --seed N` per variant, `check` | `references/template-schema.md` |
| 4 | Write 3 concepts, ask the user once | `guidelines.md` §3 |
| 5 | Hand off: `/cutroom:video` stages build → delivery (`video-direction`) | `references/onetake-benchmark.md` |

Registry data: `references/families.json`. Worked run: `references/examples.md`.
