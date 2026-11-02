# Brief contract [C-02 C-03 C-04 G-05 G-06 G-07]

Schema: `schemas/brief.schema.json`. Required: `id client platform format goal cta`.

| Field | Type | Filled at | Notes |
|---|---|---|---|
| `id` | string | brief | file name `<id>.json` |
| `client` | string | brief | slug of `clients/<slug>/` |
| `platform` | enum | brief | `instagram` · `tiktok` · `youtube_shorts` |
| `format` | string | brief | key in the platform specs (`reel`, `story`, `feed_video`, `video`, `ad`, `short`) |
| `duration_s` | number | brief | within spec `dur` |
| `goal`, `audience` | string | brief | |
| `cta` | object | brief | `text`, `contact` |
| `copy` | object | brief | `headline`, `lines[]`, `avoid[]`; `" / "` marks the accented part; verbatim on screen |
| `assets` | object | brief/material | `photos[]`, `videos[]`, `music` (licensed or null) |
| `reference` | string\|null | brief | clip in `references/` |
| `material` | object | material | written by `material.py select` |
| `concepts` | array | material | 3 × `{name, idea, carry}` |
| `chosen_concept` | int\|null | concepts | index |
| `beats` | array | concepts | `[{t, beat}]` |
| `composition` | string\|null | building | Remotion id |
| `status` | enum | pipeline only | never by hand (G-01) |
| `render` | object | pipeline only | verdicts + hashes |
| `delivery` | object | approved | package info |
| `decisions` | array | any | every WARN accepted, every choice made for the user |
| `notes` | string | any | |

## Client folder

```
clients/<slug>/
  client.json         contact, brand colours/fonts, voice_guide   (schema: schemas/client.schema.json)
  client.local.json   source_folders (absolute, read-only originals) — git-ignored
  assets/             logo, photos, videos, fonts, music/ + LIBRARY.json (schemas/music-library.schema.json)
  briefs/<id>.json
  references/
  material/<batch>/   contact_sheet.png from material.py analyze
```

`sync-clients.mjs` copies fonts/music to `remotion-base/public/clients/<slug>/` (git-ignored). Edit `client.json` ⇒ `brief.py client ts <slug>`.
