# video-direction — spec

Single source of truth. `SKILL.md`, `guidelines.md` and `references/` derive from this file; on conflict, this file wins and the others are fixed. Every rule has an ID; derived files cite IDs, `tools/check_skill.py` enforces the links (CI).

## 1 · Intent

Direct one short motion piece (story, reel, feed post, Short, TikTok) in Remotion so it reads as an original piece — not a template, not a slideshow — and ships only after the automatic verifier passes.

## 2 · Scope

| In | Out |
|---|---|
| Social video/image ≤ platform `dur` max; 9:16, 4:5 | Long-form, 16:9 launch films, UI screen recordings |
| Client brand from `client.json`; copy from brief | Inventing brand, contact or claims |
| Licensed / client / synthesized audio | Unlicensed music, voice-over, subtitles (not built) |
| cutroom tools: `tools/*.py`, `remotion-base/` | Copying or running `onetake` code (studying it for ideas is allowed) |

## 3 · Contracts

| ID | Contract |
|---|---|
| C-01 | **Input**: free prompt (`$ARGUMENTS`) + optional material, or a path to an existing brief. |
| C-02 | **Brief** `clients/<slug>/briefs/<id>.json`, schema `schemas/brief.schema.json`. Required: `id client platform format goal cta`. Sole source of on-screen text. |
| C-03 | **Client** `clients/<slug>/client.json` (schema `schemas/client.schema.json`): contact, brand colours/fonts, voice. Sole source of contact and brand. Edit ⇒ regenerate `brand.ts`. |
| C-04 | **State**: `brief.status` ∈ `brief → material → concepts → building → review → approved → delivered`. Changed only by `tools/pipeline.py advance`. |
| C-05 | **Composition**: Remotion component under `remotion-base/src/`, registered in `src/Root.tsx`, id stored in `brief.composition`. |
| C-06 | **Verdict**: `tools/verify.py` lines `FAIL` / `WARN` / `INFO`, recorded in `brief.render` by `pipeline.py render`. |
| C-07 | **Output**: `deliveries/<id>/` from `tools/deliver.py` — final video, covers, WhatsApp version, `caption.md`, contact sheet, `CHECKLIST.md`. Git-ignored. |

## 4 · Stage gates (owned by `tools/pipeline.py`)

| From → to | Gate |
|---|---|
| brief → material | `brief.py check` no ERROR |
| material → concepts | material analysed + selected (or typography-only); 3 concepts |
| concepts → building | `chosen_concept` + `beats` |
| building → review | `composition` + current draft render, no FAIL |
| review → approved | user said approved (`--approved`) |
| approved → delivered | current mastered `--final` render, no FAIL; package without severe claims |

## 5 · Guardrails (hard; never break)

| ID | Rule |
|---|---|
| G-01 | No skipped stage; never edit `status` by hand; a refused advance ⇒ fix what it lists. |
| G-02 | Never approve on the user's behalf. |
| G-03 | Never claim a render passed without verifier output showing 0 FAIL. |
| G-04 | Never type on-screen copy, CTA or contact into a component; read via `useCopy()` / generated `CLIENT`. |
| G-05 | Never invent brand colours, contact data or health/result claims. |
| G-06 | Client originals are read-only (`source_folders` in `client.local.json`); tools call `media.guard.ensure_writable()`. |
| G-07 | Only licensed media: music listed in `LIBRARY.json` with licence; fonts with licence. |
| G-08 | Deterministic frames: everything from `useCurrentFrame()`; no CSS transitions/animations, no `Math.random()`. |
| G-09 | Never fill a previous piece (or `SamplePost`) with new material; every piece starts from its own brief. |
| G-10 | Never copy or reuse `onetake` code or run its scripts to make output; studying it for ideas is allowed, recorded in `docs/benchmark.md`. |
| G-11 | Repo text in English; renders, deliveries, models never committed. |

## 6 · Creative rules (checked by verifier or checklist)

| ID | Rule | Threshold |
|---|---|---|
| R-01 | Three concepts, differing in the visual idea, not palette. | exactly 3 |
| R-02 | Concept = one sentence about the picture; states opening frame, carry, what it rules out, look. | 1 sentence |
| R-03 | Uneven beats. | longest ≥ 3× shortest |
| R-04 | At least one real rest. | ≥ 0.8 s near-still |
| R-05 | CTA end hold, still and readable. | ≥ 1.5 s |
| R-06 | Every scene boundary has a survivor that moves/scales into the next scene; plain fade between unrelated scenes = slide change. | hard cuts only in bursts or end card |
| R-07 | One story; small elements, big ground; ≤ 1 full-bleed hero moment. | — |
| R-08 | Curve by intent: landings `spring` low damping; snaps `EASE.snap`; camera `EASE.glide`. Not one curve for all. | t80 spread |
| R-09 | Operated camera: keyed ahead of subject, settle after landings, `drift()` in holds, still on CTA. | — |
| R-10 | Motion blur for travel > ~60 px/frame via `<MotionBlur>`; CSS blur ≠ motion blur. | final 12 samples |
| R-11 | Text and logos inside `FORMATS.<id>.safe`. | per platform spec |
| R-12 | Type at 1080 wide: headline ≥ 84 px, support ≥ 44 px, CTA/phone ≥ 72 px. | px |
| R-13 | Originality: no reuse of previous look; no decorative particles/confetti/flares; no stock transition carousel; "kinetic words → list → logo" is never the default; visible cause. | — |
| R-14 | Sound: few events, one material family, one room; music ducks under effects; master −16 LUFS, −1.5 dBTP. | LUFS |
| R-15 | Tracking: `<TrackRoot>`, `<Beats>` with `kind` ∈ `move rest hold cut`, `<Track>` on subject, texts, logo. | — |

## 7 · Severity contract

| Level | Action |
|---|---|
| FAIL | Fix, re-render. Blocks gates. |
| WARN | Conscious decision written to `brief.decisions`. |
| INFO | Context only. |
| Unanswerable question (unattended run) | Decide, record in `decisions`, state it at the top of the delivery. |

## 8 · Change control

- Change behaviour here first, then derived files, then `CHANGELOG.md`.
- New rule ⇒ new ID (never reuse a retired ID) + a citation in `guidelines.md` or `references/`.
- Numeric platform limits live in `tools/quality/platforms/specs/*.json`, not here.
