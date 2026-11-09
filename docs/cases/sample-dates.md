# sample-dates — a desk calendar: tearing pages leave the places

Fictional `sample` client (generated assets) · instagram / reel 1080×1920 · 8.0 s · final render measured on 2026-11-09 (Linux, camera-engine blur). Built to run the whole `/cutroom:reel` flow end to end and to exercise the camera helpers (`holds`, `shakes`, `Lattice`), the `Calendar` move with `trackId`, travel-sized blur and event-driven sound in one real piece. A worked example, never to be refilled with a real client's material.

## Brief

Goal: a reel that opens the studio's booking season. Copy: headline "Tus fechas / libres", lines "Marzo", "Abril", "Mayo". CTA "Reservá tu fecha" + a placeholder number. Client copy stays Spanish; everything else in the repo is English.

## Concepts

| # | name | idea | carry | chosen? | why |
|---|---|---|---|---|---|
| 0 | Calendar | A desk calendar loses its pages one by one; each page leaves a place under it, the last stays with the free dates. | the calendar block | yes | not recorded |
| 1 | Belt | The three places travel on a belt that brakes on the last. | the belt | no | not recorded |
| 2 | Bar | A bar crosses the lens and uncovers each place. | the bar | no | not recorded |

## Beat sheet

| t (s) | beat | kind | carries into the next |
|---|---|---|---|
| 0.0–1.4 | calendar settles | move | the calendar block |
| 1.4–2.4 | rest (camera drift stops) | rest | the calendar block |
| 2.4–3.1 | tear March | move | the calendar block |
| 3.1–3.5 | tear April | move | the calendar block |
| 3.5–4.3 | rest (camera drift stops) | rest | the calendar block |
| 4.3–5.0 | tear May | move | the calendar block |
| 5.0–8.0 | CTA hold, one pulse on the number | hold | — |

## Verifier numbers (final render)

| Metric | Value | Reads as |
|---|---|---|
| still fraction | 0.42 | almost half the piece is at rest |
| longest rest | 1.67 s | a real rest |
| beat-length ratio / CV | 11.6 / 0.72 | uneven, nowhere near a metronome |
| carried boundaries | 3 / 3, none replaced | every move boundary has a survivor |
| t80 median / IQR | 0.64 / 0.15 | no curve warning |
| max speed | 442 px/frame, 61 fast frames | all inside `<MotionBlur>` |
| loudness / true peak | −16.2 LUFS / −1.9 dBFS | mastered by `tools/master.py` |
| final hold / end still fraction | 1.67 s / 1.0 | no end-hold warning |
| result | 0 FAIL, 0 WARN, 2 INFO (loop seam, faces skipped) | |

## Decisions

- First draft FAILed `[blur]`: the place labels sit on pages that fall faster than 80 px/frame and were not marked blurred; marking them fixed it (they are inside `<MotionBlur>`).
- First draft WARNed `[rhythm]` (ratio 2.4) and `[reading]` (CTA legible 2.5 s, needs 2.6 s): the last tear and the CTA hold moved one second earlier; the CTA now holds 3.0 s.
- Delivery caption WARN accepted: the alt text is 116 characters (limit 100) because it names the three months.

## Sound

`python3 tools/sound_events.py remotion-base/out/sample-dates/SampleDates-draft.track.json --json remotion-base/src/examples/sample/dates.cues.json` derived 5 cues for 7 beats: a `tap` when the calendar appears, an `air-in` on each of the three tears, a `chime` at the CTA hold. The composition places one `<Audio>` per cue from that file. Limit found: the cue pan is not applied (a per-cue `<Audio>` is mono); a single `score.wav` from `--out` keeps the pan.

## Rejected and why

Not recorded. The brief keeps two alternative concepts without the reason they lost.

## What it taught

- A `Track` inside a flex container loses its place (the tracking wrapper is absolutely positioned): lay tracked blocks out with explicit offsets, as the other pieces do.
- Text that rides a falling page needs `blurred` on its `Track` or the verifier fails the piece (spec Q-05).
