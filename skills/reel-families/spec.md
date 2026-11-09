# reel-families — spec

Single source of truth. `SKILL.md`, `guidelines.md`, `references/` derive from it; on conflict this file wins. Every rule has an ID; `tools/check_skill.py` enforces the trace in CI. Sits on top of `video-direction` (creative rules R-NN, stage gates, guardrails) and `tools/pipeline.py`; it does not duplicate them.

## 1 · Intent

Turn one request into a legal, original Reel in the fewest prompts: summarize the current state, pick or invent a template family, synthesize a rhythm-legal beat sheet per variation, hand the chosen one to the `video-direction` pipeline. Benchmarked against `onetake`-level production standards using cutroom's own criteria (`docs/benchmark.md`), which may be refreshed by studying onetake; its code is never copied or run.

## 2 · Scope

| In | Out |
|---|---|
| Family registry, variation synthesis, concept invention, operational summary, improvement actions | Voice, subtitles, second language (parked, benchmark phase 3) |
| Reels / stories / posts for instagram, tiktok, youtube_shorts | Long-form, 16:9, UI screen recordings |
| Deterministic structure (`tools/variation.py`); creative sentence by the model | Copying or running `onetake` code (studying it for ideas is allowed) |

## 3 · Contracts

| ID | Contract |
|---|---|
| C-01 | **Input**: free prompt + optional material, or a brief path, + optional `--variants N` (default 3). |
| C-02 | **Registry** `references/families.json`: per family `id carry_kind boundary carry moves needs beats status`. `status` is `ready` iff `moves` non-empty and `needs` empty. |
| C-03 | **Beat sheet** (`variation.py sheet`): JSON list shaped like brief `beats` (`t beat moves holds carries`) plus `kind` ∈ `move rest hold`. Deterministic per `(family, duration, seed)`. |
| C-04 | **Invented concept** (`variation.py invent`): `{name, carry_kind, boundary, carry, moves, parents, idea}`; `idea` is a TODO the model must replace with one sentence. |
| C-05 | **Summary** (`reel_summary.py [--json]`): counts + prioritized actions `{priority, what, do}`. Read-only. |
| C-07 | **Sound cues** (`sound_events.py <track.json>`): `{f, t, effect, volume, pan, why}` derived from the render's beats and element records — ≤ 1 cue per beat, ≥ 0.04 s apart, text never sounds, pan from screen x (±0.6); optional stereo `score.wav`. |
| C-06 | **Output**: brief with 3 concepts, chosen concept, legal `beats`, `composition`, then the `video-direction` delivery (`deliveries/<id>/`). |

## 4 · Family model

| ID | Rule |
|---|---|
| F-01 | A family is a pair `(carry_kind, boundary)` + the moves that realise it. `carry_kind` ∈ object camera shape light text surface; `boundary` ∈ morph iris window mask wipe flip fall camera contact match none. |
| F-02 | A `needs-move` family may be proposed but not built until its move exists with a unit test; then flip `status` to `ready`. |
| F-03 | A variation is **novel** iff its `(carry_kind, boundary)` pair is absent from the registry. Novel + buildable from `ready` moves = invention. |
| F-04 | The 3 concepts of one brief span ≥ 2 carry kinds and ≥ 2 boundaries; no two share a family. |
| F-05 | An invented or modified family is written back to `families.json` only after one real piece shipped with it (0 FAIL). |

## 5 · Onetake-level quality targets (criteria from `docs/benchmark.md`)

| ID | Target | Measured by | State |
|---|---|---|---|
| Q-01 | Uneven rhythm, longest ≥ 3× shortest, ≥ 1 rest ≥ 0.8 s, CTA hold ≥ 1.5 s | `variation.py check`, verifier rhythm | enforced |
| Q-02 | Every boundary has a visible survivor | `variation.py check` (`carries`), verifier continuity | enforced |
| Q-03 | Motion curves differ by intent (t80 spread), no single easing | verifier curves | enforced |
| Q-04 | Operated camera: key ahead of the subject (~0.1 s), whip keyed at the landing, hand float that stops in holds, decaying shake on landings, a far grid on empty ground | review + `<Camera>` | helpers done (`leadKeys`, `whipKeys`, `shake`, `holdFactor`, `Lattice`); use is manual |
| Q-05 | Motion blur on fast travel, final ≥ 12 samples | verifier blur, `<MotionBlur>` | enforced |
| Q-06 | One sound room; events placed from beats (no two within 40 ms), panned by screen x, music ducked, −16 LUFS, true peak safe after AAC | verifier audio | tool done (`sound_events.py`); wiring into the piece is manual; the −16 LUFS master stays in `master.py` |
| Q-07 | Move variety: every family `ready` | `reel_summary.py` | gap (see summary) |
| Q-08 | Proof: a case write-up per shipped piece (beat sheet, numbers, what was rejected and why) | `docs/cases/<piece>.md` (template: `docs/cases/TEMPLATE.md`) | sample done; one per new piece |

Parity is never claimed; open gaps surface as actions in the summary (L-01).

## 6 · Loop and budget

| ID | Rule |
|---|---|
| L-01 | **Summary first**: run `reel_summary.py` before any other action; execute P0 then P1 actions that touch this request; re-run and confirm the list shrank. |
| L-02 | **Prompt budget**: ≤ 3 user turns — request, concept choice, draft approval. Everything else is decided, recorded in `decisions`. |
| L-03 | Variants are generated in one batch (`--variants N` seeds) and shown together; never one at a time. |
| L-04 | Every WARN/decision/seed used is appended to `brief.decisions` so a run can be replayed. |

## 7 · Guardrails

| ID | Rule |
|---|---|
| G-01 | Stage progression only through `tools/pipeline.py`; never edit `status`; never approve for the user. |
| G-02 | Never copy or run `onetake` code; studying it for ideas is allowed, findings go to `docs/benchmark.md`, which stays the benchmark source. |
| G-03 | A beat sheet must pass `variation.py check` before any code is written. |
| G-04 | Never fill a previous piece with new material; every piece gets freshly written concepts. |
| G-05 | Never claim a render passed without verifier output showing 0 FAIL; never claim onetake parity. |
| G-06 | On-screen text only through the brief (`useCopy()`); contact/brand only through `client.json`. |
| G-07 | English in the repo; Linux/POSIX paths; renders, deliveries, models never committed; no AI attribution in commits. |
| G-08 | Seeds, not randomness: no `Math.random()`; same inputs ⇒ same frames. |

## 8 · Change control

- Spec first, then derived files, then `CHANGELOG.md`; new rule ⇒ new ID, never reuse a retired one.
- Registry edits keep C-02 consistent (`tools/tests/test_variation.py` enforces it, incl. that every listed move exists in `remotion-base/src/moves`).
