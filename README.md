# cutroom

Short motion videos (Instagram stories, reels and posts; TikTok; YouTube Shorts) made with Remotion that read as original pieces, not templates or slideshows. cutroom is a Claude Code plugin plus the kit it drives:

- a **creative process**: brief → three concepts → beat sheet → build → verify → deliver;
- a **Remotion template** with the building blocks: moves, an operated camera, motion blur, tracking, safe zones;
- a **verifier** that measures the result per platform before anyone calls it done.

```
/cutroom:video "Instagram story for Hotel Sol: summer promo, write to our WhatsApp"
```

## Install

```bash
git clone https://github.com/blokxz/cutroom && cd cutroom
cd remotion-base && npm ci && cd ..
pip install -r tools/requirements.txt          # add --break-system-packages on system Pythons that need it
cp .env.example .env                           # optional: browser, Python, concurrency, ffmpeg paths
```

Or in one step, on Windows, macOS or Linux: `python tools/setup.py` (checks Node, Python and ffmpeg and tells you how to install what's missing, installs the dependencies, creates `.env`), then `python tools/doctor.py` (versions, paths and a real test frame — paste its output when asking for help).

Then open Claude Code in the clone and install the plugin from its own marketplace:

```
/plugin marketplace add blokxz/cutroom
/plugin install cutroom@blokxz
```

The project's `.claude/settings.json` already lists the marketplace and enables the plugin, so Claude Code offers it when you open the folder. The plugin is meant to be used **inside the clone**: clients, briefs and renders live there.

**Requirements:** Node 20.19+ or 22.13+, Python 3.10+, `ffmpeg`/`ffprobe` on the PATH (or set `FFMPEG` / `FFPROBE`). Remotion downloads its own headless browser on the first render; set `REMOTION_BROWSER` to use an existing one.

## How a video is made

`/cutroom:reel` (skill `reel-families`: template families, seeded variations, invented concepts, summary-first, ≤ 3 user turns; diagram in [`docs/reel-families-architecture.svg`](docs/reel-families-architecture.svg)) hands its choice to the same pipeline. `/cutroom:video` loads the `video-direction` skill (spec-driven: `spec.md` → `SKILL.md` router, `guidelines.md`, `references/`; diagram in [`docs/skill-architecture.svg`](docs/skill-architecture.svg)) and walks one brief through seven stages with `tools/pipeline.py`. A stage can't be skipped: `advance` refuses until its gate passes.

| stage | what happens | gate to leave it |
|---|---|---|
| brief | prompt → `clients/<slug>/briefs/<id>.json`; only the missing questions are asked; on-screen copy checked for risky claims | `brief.py check` has no ERROR |
| material | photos and videos analysed (contact sheet), chosen by number, copied or prepared as clips; three concepts written | material analysed and selected (or a typography-only piece), 3 concepts |
| concepts | the user picks one concept | a chosen concept and a beat sheet |
| building | composition in `remotion-base/src`, rendered and verified | a draft render with no FAIL |
| review | the user watches the draft and stills | the user's explicit approval (`--approved`) |
| approved | final encode + mastering, caption in the client's voice, delivery package | a current final render with no FAIL and a package without severe claims |
| delivered | `deliveries/<id>/`: video, covers 9:16 / 3:4 / 1:1, WhatsApp 720p, caption, sheet, checklist | — |

```bash
python3 tools/pipeline.py status  clients/sample/briefs/sample-post.json
python3 tools/pipeline.py advance clients/<slug>/briefs/<id>.json [--approved]
python3 tools/pipeline.py render  clients/<slug>/briefs/<id>.json [--final|--preview] [--force]
```

## Input: client + brief

```bash
python3 tools/brief.py client new hotel-sol --name "Hotel Sol" --logo logo.png --whatsapp "+54 9 11 …"
python3 tools/brief.py client brand hotel-sol shots/*.jpg     # colours from logo + screenshots → client.json
python3 tools/brief.py client ts hotel-sol                     # client.json → remotion-base/src/clients/hotel-sol/brand.ts
python3 tools/brief.py new hotel-sol summer-promo --format reel [--platform instagram|tiktok|youtube_shorts]
python3 tools/brief.py check clients/hotel-sol/briefs/summer-promo.json   # errors + what to ask
python3 tools/brief.py music hotel-sol                          # the client's licensed music library
```

## Material: from a folder of photos and videos to assets

```bash
python3 tools/material.py analyze hotel-sol "/path/to/client photos" [--videos]   # analysis.json + numbered contact_sheet.png
python3 tools/material.py select clients/hotel-sol/briefs/summer-promo.json 3,7,2 [--videos 1:4.0-7.5]
python3 tools/material.py clip IMG_0042.MOV --start 4 --dur 3 --out clip.mp4 [--crop-top 0.16] [--mode card]
```

- **analyze** reads only. Per photo it scores sharpness (relative to the set), exposure, horizon tilt, upscale needed, duplicates and a focus point; per video it finds the best 2–4 s windows and tells filmed footage from exported slideshows.
- **select** copies the chosen photos (rotated, ≤ 2400 px, sRGB, no GPS metadata) into `assets/photos/`, prepares clips into `assets/videos/` and records the choice in the brief.
- **clip** outputs 30 fps H.264 BT.709 without audio; iPhone HDR is tone-mapped to SDR, and wide videos can become a card over their own blurred background.
- **Originals are read-only by code**: folders listed in `source_folders` (absolute paths, in the git-ignored `clients/<slug>/client.local.json`) and in `CUTROOM_READONLY` can't be written by any cutroom tool.

## Delivery package

```bash
python3 tools/deliver.py clients/hotel-sol/briefs/summer-promo.json [--cover-time 2.1]
```

Builds `deliveries/<id>/` from the final render:

- the video and three covers (9:16, the 3:4 profile-grid crop and 1:1);
- a 720p version for WhatsApp;
- the caption (`caption.md`, written in the client's `voice_guide`), checked for claims and completeness;
- `sheet.json` with SHA-256 of every asset used, the on-screen texts, the versions and the verdict;
- `CHECKLIST.md` for the last human review.

`tools/quality/claims.py` flags health promises (severe), guarantees and superlatives, and prices or offers without dates, in Spanish and English.

- `client.json` (schema `schemas/client.schema.json`) holds what stays the same: contact, brand colours and fonts, name, taglines, voice.
- The brief (`schemas/brief.schema.json`) holds one video: goal, format, every on-screen text exactly as it must appear, CTA, assets, reference, concepts, beats, status, decisions.
- The brief is the **single source of on-screen text**: compositions read it through `useCopy()` / `contactFrom()` in `src/lib/brief.ts`. Brand name and taglines come from `client.json` via the generated `CLIENT` export.
- Fonts and music live only in `clients/<slug>/assets/`. They are synced into `remotion-base/public/clients/<slug>/` on every render. Music needs a licence: a file next to it, or an entry in `assets/music/LIBRARY.json` (schema `schemas/music-library.schema.json`).

## Rendering

```bash
cd remotion-base
npm run dev                                                                     # Studio
node scripts/render.mjs --brief ../clients/sample/briefs/sample-post.json          # draft + tracking + stills + verify
node scripts/render.mjs --brief ../clients/sample/briefs/sample-post.json --final  # crf 14 (drafts use crf 20); both mastered to −16 LUFS
```

- **One browser** is used for the whole run: composition, video and stills.
- **Parallel frames:** set `--concurrency` or `CUTROOM_CONCURRENCY`.
- **Cache:** an unchanged composition, brief and asset set is not re-rendered; only the verifier runs again. Use `--force` to re-render anyway.
- **Output colour:** limited-range BT.709 4:2:0 with a keyframe every 2 s.
- **Motion blur:** `<MotionBlur>` uses few samples in drafts and 12 in finals. The camera engine is the default; the HTML-in-canvas engine (a real shutter, Chromium 149+) is opt-in with `CUTROOM_BLUR_ENGINE=canvas` — compare first with `node scripts/blur-ab.mjs <CompositionId> <frame>...`.
- **4K master:** `--master-4k` renders a 2160×3840 final (`<id>-4k.mp4`) for clients who ask for one; it is above the platforms' 1920 px upload limit, so it is not verified against them — publish the 1080 final.

## Template (`remotion-base/src`)

| path | what |
|---|---|
| `lib/formats.ts` | story / reel / post sizes and UI margins |
| `lib/motion.ts` | `EASE` (snap, glide, out, in), `tween`, `land`, `settle`, `drift`, camera keys |
| `lib/brief.ts` | `Brief` type, `useCopy`, `CopyProvider`, `copyFrom`, `contactFrom`, `splitAccent` |
| `lib/brand.ts` | brand token shape + `loadFonts` (fonts from the client folder) |
| `moves/` | `Morph`, `IrisOpen`, `MaskReveal`, `SplitText`, `Typewriter`, `pushThrough`, `progress` |
| `components/Camera.tsx` | keyed, operated camera with drift that goes still for the CTA |
| `components/Track.tsx` | `TrackRoot`, `Track`, `Beats` (each beat has `kind`: move, rest, hold, cut) |
| `components/Music.tsx` | background music that ducks under the effects |
| `components/Accent.tsx`, `SafeZones.tsx`, `Paper.tsx` | accented copy, composing overlay, paper ground |
| `examples/sample/` | `SamplePost` — the fictional sample client's example, used by tests, CI and `doctor.py` |

## The verifier

`tools/verify.py <file|folder> [--platform instagram|tiktok|youtube_shorts] [--format auto|…] [--track f.track.json] [--ref ref.mp4]`

| layer | what it checks |
|---|---|
| core (any video) | rhythm (still share, rests, uneven beats), regular cuts, motion curves (t80), the CTA end hold, loudness and peaks; black frames, frozen picture, black bars, luminance; `--ref` compares all of that with a reference clip |
| without tracking | each scene change classified as motion, dissolve, hard cut or still (a slideshow fails) |
| with tracking | continuity across scene boundaries, framing, text under UI areas, motion blur on fast elements, legibility, **reading time** (0.6 s + 0.28 s per word, fully legible) |
| faces (optional) | warns when people appear, so their permission is asked; needs the local YuNet model (`python3 tools/models.py fetch`, hash-verified) |
| Instagram | publishing-API limits; UI areas of stories and reels; the 3:4 grid crop; reel hook and loop; images; carousels |
| TikTok, YouTube Shorts | upload limits, durations and the UI areas of each app |

Every platform number lives in `tools/quality/platforms/specs/<platform>.json`, with source URLs and a `reviewed` date. The verifier warns when that date is more than 180 days old. To add a platform, see `tools/quality/README.md`.

## Tests and CI

```bash
python3 -m pytest tools/tests -q                    # 48 cases: verifier + pipeline gates (~2 min)
cd remotion-base && npx tsc --noEmit && npm test    # types + 39 unit tests
python3 tools/check_plugin.py                       # plugin packaging + skill spec trace (tools/check_skill.py)
python3 tools/reel_summary.py                       # operational summary + prioritized actions
claude plugin validate --strict .                   # full plugin check (local)
```

`.github/workflows/ci.yml` runs on every push: the verifier tests, types and unit tests, the plugin check, and a real render of every example verified from its brief. The renders are uploaded as a CI artifact.

## Licences

- cutroom: MIT (see `LICENSE`).
- Remotion: free for individuals and teams of up to 3 people; larger companies need a company licence (remotion.dev/license).
- Sample client fonts (`clients/sample/assets/fonts`): DM Serif Display, Inter, Caveat — SIL Open Font License.
- Sounds and the test music bed: generated by `tools/sfx.py`, no third-party material.
- The sample client (`clients/sample/`) is fictional: its photos and logo are generated, not photographs of a real place or brand.
- All code and texts are original; none is derived from other video tools' source.
