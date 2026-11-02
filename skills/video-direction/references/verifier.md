# Verifier [C-06 G-03 R-03…R-06 R-08 R-10 R-11 R-14]

`tools/verify.py` (CLI) → `tools/quality/` (checks) → `platforms/<name>.py` + `specs/<name>.json`. Platform from `brief.platform`.

## Commands

| Command | Does |
|---|---|
| `python3 tools/pipeline.py render <brief> [--final] [--preview] [--force]` | render + verify + record verdict (gates read it) |
| `cd remotion-base && node scripts/render.mjs --brief ../clients/<slug>/briefs/<id>.json [--final]` | same render without recording; syncs assets, tracks, stills |
| `node scripts/render.mjs <CompositionId>` | render without a brief |
| `python3 tools/verify.py <file.mp4>` | any MP4, format auto-detected |
| `python3 tools/verify.py draft.mp4 --ref ref.mp4` | rhythm distance to a reference (divergence = WARN) |
| `python3 tools/verify.py post.jpg` / `<carousel_dir>/` | images / carousel (count, ratios, each slide) |
| `python3 tools/verify.py ref.mp4 --analyze` | numbers only |

## Checks

| Group | Measures | Rule |
|---|---|---|
| Technical | container, codec, 4:2:0, fps 23–60, bitrate, duration, size, AAC ≤ 48 kHz, moov front, keyframe interval, colour | spec JSON |
| Rhythm | still share, rests, uneven beats, metronome cadence | R-03 R-04 |
| Cuts | hard cuts outside bursts | R-06 |
| Curves | t80 per move (0.3–0.5 front-loaded · 0.6–0.7 ease-in-out · ≈ 0.8 linear · > 0.85 slow start); all equal = generic | R-08 |
| End hold | CTA still at the end | R-05 |
| Audio | loudness, true peak | R-14 |
| Tracking | continuity per boundary, framing, text in UI areas, blur on fast elements, legibility | R-06 R-10 R-11 |
| Layout | UI-covered areas, 3:4 grid crop, reel hook (1st second), loop seam | R-11 |
| Integrity | black frames, frozen picture, bars, brightness, faces (optional) | — |

## Severity → action

FAIL fix + re-render · WARN decision in `decisions` · INFO context. Stale-specs WARN ⇒ re-check official pages in the specs file.
