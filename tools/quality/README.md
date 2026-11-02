# quality — checks for short-form video and images

`tools/verify.py` is the command line; this package does the work.

```
quality/
  media.py      what a file is: container, codecs, rates, sizes, colour, moov position, keyframe interval, image profile
  motion.py     picture analysis: rhythm, cuts, speed, motion curves (t80), reference comparison, contact sheets
  integrity.py  black frames, frozen picture, black bars, brightness; scene changes classed motion / dissolve / cut / still
  faces.py      optional "people visible" check with OpenCV's YuNet face detector (model via tools/models.py)
  limits.py     every threshold of the reading-time, integrity, scene and face checks
  audio.py      loudness (LUFS) and true peak
  track.py      checks on the per-frame element boxes from remotion-base/scripts/render.mjs (incl. reading time)
  checks.py     platform-agnostic verdicts on the analysis (rhythm, cuts, curves, ending, audio)
  report.py     FAIL / WARN / INFO collection, printing, JSON
  bins.py       ffmpeg / ffprobe binaries (env FFMPEG / FFPROBE, default from PATH)
  platforms/    one module per platform: layout rules, which checks apply to which format
    common.py   shared: spec loading + staleness, technical video checks, UI-area layout checks, core video flow
    specs/      <platform>.json — every numeric limit, with "reviewed" date and source URLs
    instagram.py  tiktok.py  youtube_shorts.py
```

## Speed

Frames are decoded once and analysed at 270 px wide; Farneback optical flow at that size is most of
the cost. Flow is skipped on pairs where too few pixels changed to measure a speed (the result is 0
either way), runs in parallel threads when cores are free, and the full-resolution frames the checks
need (contact sheet, layout samples) are kept from the same decoding pass. `CUTROOM_ANALYSIS_CACHE=<dir>`
reuses the analysis of an unchanged file (path, size, mtime) — the tests use it.

Integrity measurements come from the same pass: per-frame mean and 99th-percentile grey level and the
scene-change signal from the analysis frames, black bars from a full-resolution frame every 0.5 s.

## Beats

`.track.json` beats are `{ f, name, kind? }` with `kind` in `move | rest | hold | cut`. Without `kind`
the name decides: a word "cut" → cut (boundary not checked for continuity), "rest"/"hold" → excluded
from the carried share, anything else → move.

## Motion curves

Every active stretch gets a **t80**: the share of its duration needed to cover 80 % of its travel.
≈0.3–0.5 front-loaded (snaps, springs) · ≈0.6–0.7 ease-in-out · ≈0.8 linear · >0.85 slow start.
All moves on one value reads as generic motion; a high median reads as sluggish arrivals.

## Reference comparison

`--ref clip.mp4` analyses a clip the client likes and compares still share, cut rate, median beat
length, curve character and the shape of motion energy over time. Divergences are WARNs, not
errors — matching a reference is a choice.

## Platform specs

Each `platforms/specs/<name>.json` holds `reviewed` (YYYY-MM-DD), `sources` (URL + what it covers),
`source_note` (which numbers are official and which are creator guidance), shared `video` limits and
`formats`. verify.py WARNs when `reviewed` is more than 180 days old: re-check the sources, update the
numbers and the date. Format keys used by the checks: `kind`, `rec`, `dur`, `rec_dur`, `max_mb`, `ui`
(top, bottom, left, right — FAIL), `ui_blocks` ({name: [x0, y0, x1, y1]} — FAIL), `ui_caution` /
`ui_caution_blocks` (WARN), `min_text`, `end_hold`, `hook`, `loop`, and optional `min_res`, `min_vbr`,
`containers`. All pixel values are at the recommended size and scale with the video.

## Adding a platform

1. Write `platforms/specs/<name>.json` (above), then create `platforms/<name>.py` exposing:
   - `NAME` — the `--platform` value
   - `SPEC = common.load_spec(NAME)` and `FORMATS = SPEC["formats"]`
   - `resolve(fmt, media)` — map the `--format` value (and aliases like `post`) to a format key
   - `detect(media)` — pick a format from the file when `--format auto`
   - `check(ctx)` — run the checks; `ctx` holds `media`, `format`, `report`, `analysis`
     (videos), `track` (if `--track`), `lufs`, `peak`, `cover_frame`
2. Reuse `common.*` (a plain vertical-video platform is just `common.vertical_video_check`), `checks.*`,
   `track.continuity` and `track.element_checks`; only write what is specific to the platform
   (crops, feed behaviour, image rules).
3. Register it in `platforms/__init__.py` and add cases to `tools/tests/test_verify.py`
   (the integrity, scene, reading-time and face checks have their own `tools/tests/test_quality_*.py`)
   (`python3 -m pytest tools/tests -q` or `python3 tools/tests/test_verify.py`).

## Reading time (with tracking)

Every `kind: text` record carries `t`, the element's text content (written by render.mjs). For each
continuous appearance — frames with opacity ≥ 0.9 and the whole box inside the frame, dips of ≤ 2
frames bridged — the text needs **0.6 s + 0.28 s per word** (words = whitespace tokens with a letter or
digit). Under 70 % of that is a FAIL, under 100 % a WARN. A text that is on screen but never fully
legible is a WARN. Tracks without `t` skip the check with an INFO. Metrics: `text_appearances_checked`,
`reading_time_min_share` (the tightest appearance, 1.0 = exactly enough).

## Integrity (any video)

| check   | rule | measured on cutroom renders |
|---------|------|-----------------------------|
| black   | FAIL: frames with mean grey < 8 and 99th percentile < 24 outside the first / last 0.2 s | 0 black frames |
| frozen  | WARN: identical frames (mean change < 0.1) for ≥ 2 s, except the run that reaches the end (the CTA hold); INFO when the run lies inside a declared `hold`/`rest` beat; WARN when the final hold itself is > 5 s | longest mid-video run 0.4–1.4 s; final holds 0.1–1.8 s |
| borders | FAIL: black bars (rows / columns never brighter than 24) ≥ 8 px on opposite edges in 90 % of the sampled frames; WARN for one edge | 0 px |
| luma    | WARN: mean brightness outside 40–235 | 197–233 |

Metrics: `black_frames`, `frozen_max_s`, `final_hold_s`, `black_bars_px`, `mean_luma`.

## Scene changes (no tracking)

A scene change is a moment where the picture 0.3 s later differs from the picture 0.3 s earlier by a
mean of ≥ 10 grey levels **and** by ≥ 1.6× the local median of that signal (± 1.5 s) — so a steady slow
zoom is not a change — at least 1 s from the previous one and not in the first / last 0.5 s. Each is classed:

- **cut** — one frame changes ≥ 8 grey levels while both neighbours change < 15 % of that;
- **still** — no frame of the transition changes more than 0.35 (a fade too slow to see moving);
- **dissolve** — every transition frame is close to a blend of the frames 0.1 s before and after it
  (median residual < 0.34 of their difference): a cross-fade, even over slowly drifting pictures;
- **motion** — anything else: a push, an iris, a flip, a carried element.

Only without `--track` (with tracking, the beat continuity check rules): WARN when < 80 % of the
changes happen in motion, FAIL under 50 %, INFO with fewer than 2 changes. Calibration
(blend residual in brackets):

| video | changes | verdict |
|-------|---------|---------|
| example story, one object transforming | 2 motion (0.52, 0.67) | pass |
| example reel, camera through scale | 5 motion (0.40–0.56) | pass |
| example typographic post | 1 motion (0.40) | INFO (too few) |
| photo slideshow, dissolves | 5 dissolve (0.03–0.04) | FAIL |
| photo slideshow, hard cuts | 4 cut | FAIL |
| Ken Burns slideshow, dissolves | 5 dissolve (0.27–0.30) | FAIL |
| Ken Burns slideshow, hard cuts | 4 cut | FAIL |
| photos pushed into each other | 5 motion (0.59–0.72) | pass |

Metrics: `scene_changes_found`, `scene_changes_in_motion` (from the analysis, also with `--analyze`),
and without tracking `scene_change_kinds`, `changes_in_motion`.

## Faces

`faces.py` samples one frame per second (kept from the decoding pass), downscales it to ≤ 640 px and
runs `cv2.FaceDetectorYN` (YuNet, score ≥ 0.8). Any face → WARN "people visible — get their permission
before publishing" with timestamps. It never identifies anyone. The model is optional:
`python3 tools/models.py fetch` downloads `face_detection_yunet_2023mar.onnx` (MIT, OpenCV Zoo) into
`tools/models/`, checks its pinned SHA-256 and writes `tools/models/LICENSES.md`; `status` shows what is
installed; `CUTROOM_FACE_MODEL=<path>` uses a file elsewhere. Without it: INFO "face check skipped".
Metric: `frames_with_faces`.
