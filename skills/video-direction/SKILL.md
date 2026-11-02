---
name: video-direction
description: Direct a short motion video (story, reel, post, promo) in Remotion so it reads as an original piece and not a template — concept round, beat sheet, continuity between scenes, motion rules, sound, and an automatic verify loop before delivery. Use whenever a short animated video, social story or promo clip is requested.
---

# video-direction — router

Contract: `spec.md` (wins on conflict). Procedure: `guidelines.md`. Load a reference only at the stage that needs it.

## Always

- Obey guardrails G-01…G-11 in `spec.md` §5.
- Drive state only through `python3 tools/pipeline.py status|advance|render <brief>` (C-04).
- Each turn: run `status`, do its `next:` line, `advance`.

## Route by `brief.status`

| Stage | Do | Load |
|---|---|---|
| brief | create/fill brief, ask only `check` questions | `guidelines.md` §1 · `references/brief-contract.md` |
| material | analyse + select photos/clips, write 3 concepts | `guidelines.md` §2 · `references/concept-families.md` |
| concepts | show concepts, wait for choice, write beats | `guidelines.md` §3 · `references/beat-sheet.md` |
| building | compose, render, fix FAIL | `guidelines.md` §4–6 · `references/remotion-kit.md` · `references/platform-layout.md` |
| review | show draft + stills, wait for approval | `guidelines.md` §7 · `references/verifier.md` |
| approved | final render, caption, package | `guidelines.md` §8 |
| delivered | walk `CHECKLIST.md` with user | `guidelines.md` §8 |

Worked input → output: `references/examples.md`.
