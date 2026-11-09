# reel-families — guidelines

Procedure derived from `spec.md`; IDs in brackets. `video-direction` owns brief, build, render, verify and delivery steps — do not repeat them here.

## 1 · Summary first [L-01 C-05]

1. `python3 tools/reel_summary.py` (`--json` to parse).
2. Execute actions in order P0 → P1. Do only P1 items that touch this request's family or platform; list the rest in the delivery note.
3. After acting, re-run; the touched actions must be gone. Otherwise record why in `decisions` [L-04].
4. Stale platform specs (P0): re-check the official pages named in the specs JSON before building.

## 2 · Choose families [F-01 F-02 F-03 F-04 C-01 C-02]

1. Read `references/family-taxonomy.md`; filter `families.json` by the brief's material (photos, clips, none) and platform.
2. Variants N (default 3 [L-03]): pick families so the set spans ≥ 2 carry kinds and ≥ 2 boundaries [F-04].
3. Prefer `ready` families. A `needs-move` pick is allowed as a proposal only; building it requires its move first [F-02].
4. Want something new ⇒ `python3 tools/variation.py invent --seed N --n 3` [C-04 F-03]. Rules and mutation operators: `references/variation-rules.md`.
5. Unattended run ⇒ choose the strongest, record why [L-02].

## 3 · Synthesize variations [C-03 G-03 G-08 Q-01 Q-02 L-03 L-04]

1. Per variant: `python3 tools/variation.py sheet <family> --duration <brief.duration_s> --seed <n>`; seeds 1…N.
2. `python3 tools/variation.py check <beats.json> --duration S` must print `beat sheet OK` [G-03].
3. Replace the placeholder beat names with the piece's real beats; keep `t` boundaries (stretch only within the ratio rule).
4. Write each concept: one sentence about the picture, `carry`, what it rules out, look (palette + type). Brief `concepts` allows 3.
5. Show all variants in one message; ask one question: which? [L-03 L-02]
6. Append family ids and seeds to `decisions` [L-04].

## 4 · Invent or modify a family [F-03 F-05 G-04]

1. Start from `invent` output; replace its `idea` TODO with a sentence naming the opening frame and what carries.
2. Modify = change one axis of an existing family (carry, boundary, move) and say which; never fill an old piece with new photos [G-04].
3. If no `ready` move realises the boundary, add the move in `remotion-base/src/moves` (pure math exported + unit test) before building [F-02].
4. After one shipped piece with 0 FAIL, add the family to `families.json` and run `python3 -m pytest tools/tests/test_variation.py -q` [F-05].

## 5 · Hand off [G-01 G-05 G-06 C-06]

1. Write `chosen_concept` + `beats` into the brief; run the `video-direction` flow (`python3 tools/pipeline.py status|advance|render <brief>`).
2. Sound: after the draft render run `python3 tools/sound_events.py remotion-base/out/<id>/<Composition>-draft.track.json --json cues.json --out score.wav` [C-07]; use `score.wav` as one `<Audio>` (or place `<Audio>` by frame from the cues), re-render, re-verify.
3. Quality targets Q-03…Q-06 are met in the build: curves by intent, operated camera, `<MotionBlur>`, one sound room (see `video-direction` references). Open gaps (Q-07, Q-08) are reported, not hidden.
4. State results only from verifier output [G-05]. Never say "onetake level"; say which targets passed and which are open.
5. Delivery note: summary delta (actions closed / still open), families + seeds, decisions. Write `docs/cases/<id>.md` from `docs/cases/TEMPLATE.md` with the final verifier numbers [Q-08].

## 6 · Environment [G-02 G-07]

- Linux/POSIX paths, `python3`, no `bin/`; machine paths only in `.env`.
- Repo text in English; client copy is the only exception.
- Commits authored by the repo owner, no co-author or generated-by lines.
- Benchmark source is `docs/benchmark.md`; refresh it by studying `onetake` for ideas (capabilities, numbers, what it rejects), then design our own better version. Never copy or run its code.
