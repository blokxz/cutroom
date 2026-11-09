# sample-post — a typographic system: the three words are the set

Fictional `sample` client (generated assets) · instagram / feed_video 1080×1350 · 8.0 s · metrics measured on a draft render on 2026-11-09 (Linux, camera-engine blur). The piece exists for tests, CI and `doctor.py`; it is a worked example, never to be refilled with a real client's material.

## Brief

Goal: a feed post that introduces the studio with its three words. Copy: headline "Hecho / a mano", lines "Diseño", "Color", "Detalle". CTA: "Escribinos por WhatsApp" + a placeholder number. Client copy stays Spanish; everything else in the repo is English.

## Concepts

| # | name | idea | carry | chosen? | why |
|---|---|---|---|---|---|
| 0 | Typographic system | The three studio words are the set and fly into the card. | the words | yes | not recorded |
| 1 | Collage | Cut-outs stack until they form the card. | the pile | no | not recorded |
| 2 | Stamp | A stamp prints the card. | the stamp | no | not recorded |

## Beat sheet

| t (s) | beat | kind | carries into the next |
|---|---|---|---|
| 0.0–1.3 | "Diseño" arrives letter by letter | move | Diseño |
| 1.3–1.8 | rest | rest | Diseño |
| 1.8–2.5 | "Color" | move | both words |
| 2.5–3.2 | "Detalle" | move | the stack |
| 3.2–4.3 | rest on the stack | rest | the words |
| 4.3–5.5 | words fly into the tagline, card wipes up | move | the card |
| 5.5–8.0 | CTA hold, one pulse on the number | hold | — |

## Verifier numbers (draft, 2026-11-09)

| Metric | Value | Reads as |
|---|---|---|
| still share | 0.54 | over half the piece is at rest |
| longest rest | 1.37 s | a real rest |
| beat-length ratio / CV | 14.3 / 0.58 | uneven, nowhere near a metronome |
| carried boundaries | 3 / 3, none replaced | every move boundary has a survivor |
| t80 median / IQR | 0.71 / 0.09 | no curve warning |
| max speed | 288 px/frame, 5 fast frames | inside `<MotionBlur>` |
| loudness / true peak | −16.8 LUFS / −2.6 dBFS | no audio warning (the draft is mastered like a final) |
| final hold / end still fraction | 1.37 s / 0.93 | no end-hold warning raised for this format (feed_video: WARN level) |
| result | 0 FAIL, 1 WARN, 1 INFO | |

## Decisions

- WARN `reading`: "ESCRIBINOS POR WHATSAPP +54 9 11 0000…" is legible for 2.30 s and needs about 2.6 s. Accepted in the brief: the phone number counts as 4 words and the CTA holds still at the end.
- INFO `faces`: skipped (the detector model is not fetched here).

## Event-driven sound check (2026-11-09)

`python3 tools/sound_events.py remotion-base/out/sample-post/SamplePost-draft.track.json` derives 4 cues for 7 beats: `air-in` at f55 and f75, `tap` when the card appears at f147, `chime` at the CTA hold at f165. The piece still places its own `<Audio>` by hand (it also clicks on each word); the tool is for new pieces.

## Rejected and why

Not recorded. The brief keeps two alternative concepts without the reason they lost.

## What it taught

- A piece can pass every rhythm check with all boundaries carried and still need a decision on a WARN: reading time on the CTA is a conscious trade-off, written into `decisions`.
- Rests and holds are exempt from the carry count; that is why 3 of 3 boundaries is the right denominator here (spec R-04, R-05, R-06).
