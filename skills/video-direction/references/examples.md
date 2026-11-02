# Worked example [C-01…C-07 R-01…R-06]

Source: `clients/sample/briefs/sample-post.json` + `remotion-base/src/examples/sample/SamplePost.tsx`. Fictional client, synthetic assets — learn from it, never reuse it (G-09). Copy is Spanish because client copy is the one exception to the English rule.

## Input (C-01)

```
/cutroom:video "Feed post that introduces the studio with its three words; WhatsApp CTA"
```

## Brief after stage `brief` (C-02)

```json
{
  "id": "sample-post", "client": "sample", "platform": "instagram", "format": "feed_video", "duration_s": 8,
  "goal": "Feed post that introduces the studio with its three words.",
  "cta": { "text": "Escribinos por WhatsApp", "contact": "+54 9 11 0000-0000" },
  "copy": { "headline": "Hecho / a mano", "lines": ["Diseño", "Color", "Detalle"], "avoid": [] },
  "assets": { "photos": ["assets/photos/sample-2.jpg"], "videos": [], "music": null },
  "status": "brief"
}
```

## Concepts (R-01 R-02)

| # | name | idea | carry |
|---|---|---|---|
| 0 ✓ | Typographic system | The three studio words are the set and fly into the card. | the words |
| 1 | Collage | Cut-outs stack until they form the card. | the pile |
| 2 | Stamp | A stamp prints the card. | the stamp |

## Beat sheet (R-03…R-06)

| t (s) | beat | moves | holds still | carries |
|---|---|---|---|---|
| 0.0–1.3 | "Diseño" | letters arrive one by one | ground | Diseño |
| 1.3–1.8 | rest | drift | Diseño | Diseño |
| 1.8–2.5 | "Color" | Diseño rises/shrinks, Color in | ground | both words |
| 2.5–3.2 | "Detalle" | Detalle arrives | stack | stack |
| 3.2–4.3 | rest on the stack | drift | stack | words |
| 4.3–5.5 | words → tagline | words fly into card, card wipes up | ground | card |
| 5.5–8.0 | CTA hold | one pulse on the number | everything | — |

Ratio 2.5 s / 0.5 s = 5× (R-03) · rests 0.5 s + 1.1 s + CTA 2.5 s (R-04 R-05) · survivor at every boundary (R-06).

## Output (C-06 C-07)

- `status: delivered`, `composition: SamplePost`.
- `decisions`: "Reading-time WARN on the CTA accepted: the phone number counts as 4 words; the CTA holds still at the end, long enough to read it."
- `deliveries/sample-post/`: final MP4, covers, WhatsApp version, `caption.md`, sheet, `CHECKLIST.md`.
