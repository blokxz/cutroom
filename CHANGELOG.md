# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · [semver](https://semver.org/) versioning.

## [0.4.0] — Unreleased

Phase 1 of the plan to surpass onetake: render quality and ease of use.

### Added

- `covers/carousel-end.html`: a closing slide for photo carousels (light ground, the logo large, one closing line, the handle), pure HTML + SVG, rendered with `scripts/html-still.mjs`.
- Squash and stretch from velocity in `lib/motion.ts` (`stretchFromVelocity`, `velocityOf`, `contactSquash`, `stretchTransform`, `stretchAxes`): area kept, soft cap, squash along the contact normal. `entrancePose` now stretches rise, drop and slide along their travel (`stretch: 0` turns it off). New move `Bouncer` (`bounceAt`, `bounceContacts`, `bounceShape`): closed-form bounces that stretch in flight, squash on each contact and roll to rest.
- The move library is complete: `examples/moves/LibraryDemos.tsx` adds demos for Squash, Morph, pushThrough, IrisOpen, MaskReveal, SplitText, Typewriter, ArchWindow, Caption, Camera, Steam and Stream, so all 27 moves have a Studio demo, a final-quality clip and a sheet in `docs/moves/` (index in `docs/moves/README.md`).
- `<MotionBlur>`: one wrapper for every example. Drafts get few blur samples and finals 12. The camera engine is the default; the HTML-in-canvas engine (real shutter) is opt-in with `CUTROOM_BLUR_ENGINE`. `scripts/blur-ab.mjs` compares both engines on chosen frames.
- `render.mjs --master-4k`: a 2160×3840 final master.
- `tools/setup.py`: one-command setup for Windows, macOS and Linux. It checks requirements with install hints, runs `npm ci` and `pip install`, and creates `.env`.
- `tools/doctor.py`: versions, paths, configuration and a real one-frame render.
- CI job on `windows-latest`: setup, tests, types and a test frame rendered with Remotion's own browser.
- `video-direction`: fifteen new photo-led concept families — Logbook, Key, Written postcard, Light clock, Before / after rest, Match cut, Object wipe, Film strip, Scrapbook, Chain reaction, Dive through scale, Calendar, Letters as windows, Thread and Depth.
- Move `Key`: a key that goes into the lock and turns with a click (`keyTurn`, `keyTurns`), the next scene opening out of the keyhole (`KeyholeIris`), and a door that swings open (`DoorSwing`). Demo: `MovesDemo-Key`.
- Move `WrittenPostcard`: handwriting that writes itself (`Handwriting`, `writeSchedule`), a perforated photo stamp with a postmark (`Stamp`) and a two-sided card that flips (`Postcard`, `flipAngle`). Demo: `MovesDemo-WrittenPostcard`.

- `video-direction` is now spec-driven: `spec.md` (single source of truth: contracts C-NN, guardrails G-NN, creative rules R-NN, stage gates, severity), a 17-line `SKILL.md` router that loads per stage, `guidelines.md` (procedures, edge cases, checklist) and `references/` (brief contract, concept families, beat sheet, Remotion kit, platform layout, verifier, worked example). Diagram: `docs/skill-architecture.svg`.
- `tools/check_skill.py` (run by `check_plugin.py` in CI) and `tools/tests/test_skill_spec.py`: every spec ID must be cited directly downstream, every citation must exist, every reference must be routed, the router stays within budget; seeded mutation tests prove the check catches a dropped rule.

- Skill `reel-families` + command `/cutroom:reel`: spec-driven orchestration of template families. `references/families.json` registers 28 families (carry kind, boundary, moves, status); `tools/variation.py` synthesizes seeded, rhythm-legal beat sheets (longest ≥ 3× shortest, rest ≥ 0.8 s, CTA hold ≥ 1.5 s, a survivor per beat) and invents novel (carry kind × boundary) concepts from buildable moves; `tools/reel_summary.py` gathers briefs, verdicts, stale platform specs, families without a move and benchmark gaps into one report with P0/P1/P2 actions. Fuzz tests cover every family × duration × seed. Diagram: `docs/reel-families-architecture.svg`.

- `docs/benchmark.md`: first direct study of onetake (what it is, counts side by side, where cutroom is ahead, ten ideas to build our own way, what is out of scope). New families `light_flood` and `continuous_surface` (30 in total, both `needs-move`) and creative rule R-16 (every concept states the claim its picture makes).

- Operated-camera helpers in `lib/motion.ts` (`leadKeys`, `whipKeys`, `shake`, `holdFactor`, `latticePoints`, `EASE.whip`); `<Camera>` gains optional `holds` and `shakes`, and `<Lattice>` draws a far grid. `<MotionBlur travel>` sizes the blur samples by the declared travel (`samplesFor`). All optional: existing pieces render unchanged.

- Moves `LightFlood` (light floods the frame and drains in rings onto the next scene), `Belt` (ramp, cruise and an exact brake on an item), `ObjectWipe` (an object crosses the lens and uncovers the next place) and `Calendar` (pages tear off a hinge). Pure math exported and unit-tested, Studio demos `MovesDemo-LightFlood|Belt|ObjectWipe|Calendar`. Families `light_flood`, `continuous_surface`, `object_wipe` and `calendar` are now `ready` (26 of 30).

- Moves `FilmStrip` (a strip rolls, then one frame grows to fill the screen), `Dominoes` (cards tip, each starting on contact), `CauseEffect` (a cause touches a target; squash, recoil and an effect start on the hit frame) and `DepthStage` (one camera through layers: parallax and depth-of-field blur; layers are supplied, not segmented). Pure math unit-tested, demos `MovesDemo-FilmStrip|Dominoes|CauseEffect|Depth`. Every registered family is now `ready`.

- Moves `Entrances` (`entrancePose`: rise, drop with squash, slide, pop, swing; all settle exactly at rest), `Gather` (a cast flies into one target, one after another; new family `gather`, 31 in total) and `Silk` (flowing translucent ribbons as a background that loops exactly). Demos `MovesDemo-Gather` and `MovesDemo-Silk`.

- `CarouselSlide` composition (4:5 still, shared layout and a segmented progress bar) for photo carousels, rendered one still per slide and checked with `verify.py <folder>`.

- `remotion-base/covers/carousel-cover.html`: a carousel cover in plain HTML and SVG (logo, a full-width photo under a wavy edge, title, progress bar; parameters in the query string) and `scripts/html-still.mjs`, which screenshots any HTML page with the same headless Chrome as `render.mjs`.

- Two reels for the Bungalows Concordia client (`clients/bungalows-concordia`, 12 s each, photos and logo kept out of git, palette measured from the logo): `TermasArroyo` (trail) and `TermasCinta` (film_strip), each from brief to a mastered render with 0 FAIL. A third, built on a sun disc (light_clock), was discarded by the client.

- Move `Stream` (`StreamRibbon`): a meandering stream seen from above with pools and riffles, grass and wet-stone banks, a deep channel, irregular flow glints and pebbles, drawn as one continuous course, windowed around the camera so its cut edges stay off-screen (a stream that is still being revealed gets a tapered tip); pure math (`streamCenter`, `streamWidthAt`, `ribbonSides`, `headTaper`) unit-tested. The closing card falls back to the name in type while `assets/logo.png` is missing. `FilmStrip` gains `blurred` and `growEase`, and its sprocket holes are now large enough to read as film.

- `remotion-base/covers/photo-post.html`: a static 4:5 feed post in plain HTML (full-bleed photo, scrim, brand mark or name in type, tagline), parameters in the query string; checked with `verify.py --format feed_image`.

- Reel `Escapada` for Bungalows Concordia (15 s), after the client's own reference reel: two-line captions that come in out of a blur with a moss box on one word, a slow camera per photo, and scene changes through rising steam (new move `Steam`: seeded puffs, a veil that swells around each change, a tracked lead puff). Checked against the reference with `verify.py --ref`.

- Picture quality: finals capture PNG frames; a whole-frame shutter (`--shutter N`, default 4) re-renders only the moving stretches at fractions of a frame (`withTimeOffset`) and `tools/shutter.py` averages them in linear light; `--fps60` writes a 60 fps copy from the same piece.
- `tools/looks.py`: five named looks (palette + two OFL faces from `@fontsource`, contrast-checked) applied to a client in one step.
- `<Caption>`: the two-line caption system (small sans, serif italic out of a blur, one boxed word) that leaves before every change.
- Reference reading: `verify.py --analyze` prints an energy map and bursts of cuts; `--frames` writes a sheet of one frame every 0.5 s.
- Verifier `burnt` WARN: a large area burning to white through a haze (steam, fog, glare); crisp white design shapes do not count.
- `move_sheet.py` measures speed from the pixels when given a video, so every move gets a sheet.
- `/cutroom:film`: the whole protocol in one command. `video-direction` rules R-17 (look), R-18 (captions), R-19 (reference), R-20 (picture quality).

- `tools/compare.py`: compares two renders of the same piece — a labelled side-by-side video, a sheet of the same instants with a 2x crop of the caption band, and numbers per video (detail, flat and blown areas, banding, sharpness, compression blocks, SSIM fidelity to the client's photos, rhythm against a reference), the winner of each, and an optional seeded blind A/B pair. Tests make renders worse on purpose and check that each number moves the right way.

- `tools/move_sheet.py`: a speed graph (px/frame per tracked element, beats and the 80 px/frame blur limit marked) under a contact sheet; first sheets in `docs/moves/`.

- `tools/sound_events.py`: sound cues placed from a render's `.track.json` (at most one per beat, 0.04 s apart, text never sounds, pan from screen x) with an optional stereo `score.wav` mixed from the `sfx.py` palette. Contract C-07 in the `reel-families` spec.

- `docs/cases/`: a case template and the first case, `sample-post.md`, with real verifier numbers (what was rejected is marked "not recorded", never reconstructed).

- Second example piece `SampleDates` (reel, family `calendar`): a desk calendar whose pages tear away and leave a place each. It goes from brief to delivered through `pipeline.py` on the sample client (0 FAIL, 0 WARN; the beat sheet is hand-written and checked with `variation.py check`) and uses `Camera` `holds` and `shakes`, `Lattice`, `Calendar` with `trackId`, travel-sized blur and a cue-driven stereo score (`clients/sample/assets/score/sample-dates.wav`). Case: `docs/cases/sample-dates.md`.

### Removed

- The worked-example client and its four pieces: every client asset, brief and example built for it. The kit now ships only a fictional `sample` client (generated photos and logo, SIL OFL fonts, generated music) and one example, `SamplePost`, used by the tests, CI and `doctor.py`. Real clients are created from scratch through `/cutroom:video`.

### Fixed

- The blur check no longer measures a jump from a frame whose box had no size yet (the first frame can be logged before layout).
- `tools/master.py` cuts the audio at the picture's length, so a score with a tail no longer makes the file longer than the render.
- `tools/master.py` measures the true peak of the encoded AAC file and encodes again with a lower ceiling when AAC overshoots (the first-pass measurement could not see that).
- Clips and the HLG test source keep their colour transfer on ffmpeg builds that no longer carry `-color_trc` into the stream (x264 now writes the VUI itself).
- Windows: `material`, `variation`, `reel_summary`, `sound_events`, `check_skill` and `models` print UTF-8 on legacy code pages; the read-only guard no longer lowercases paths when its check is case-sensitive; tests tolerate a repo on another drive.

### Changed

- The skill recommends `<Video>` from `@remotion/media` for clips, following Remotion's performance guide.

## [0.3.0]

Ideas ported from the earlier HyperFrames reels project, rewritten for cutroom.

### Added

- **Material stage** (`brief → material → concepts`):
  - `tools/material.py analyze` scores photos (sharpness, exposure, horizon, upscale, duplicates, focus point) and videos (best 2–4 s windows, slideshow vs filmed) and draws a numbered contact sheet.
  - `select` copies the chosen photos and prepares clips into the client's assets and records them in the brief.
  - `clip` prepares a video window (30 fps, BT.709, HDR to SDR, card mode).
- **Read-only originals by code:** `tools/media/guard.py` refuses writes inside a client's `source_folders` or `CUTROOM_READONLY`, including through symlinks and `..`.
- **Claims check** (`tools/quality/claims.py`, Spanish and English):
  - health promises are an ERROR in `brief.py check`;
  - guarantees and undated offers are a WARN;
  - the client's `voice_guide.avoid` words are enforced.
- **Delivery package** (`tools/deliver.py`):
  - final video, covers 9:16 / 3:4 / 1:1 and a 720p WhatsApp version;
  - a caption in the client's voice, checked for claims and completeness;
  - `sheet.json` with SHA-256 of every asset, and `CHECKLIST.md`.
  - The pipeline only reaches `delivered` with a package that has no severe claim.
- **Verifier:**
  - reading time for tracked text (track records now carry the text);
  - black frames, frozen picture, black bars and luminance;
  - scene-change continuity without tracking (motion / dissolve / hard cut);
  - optional face warning with a hash-verified local model (`tools/models.py`).
- **Concept families** in the skill (window, postcards, day arc, trail, living map, and more) and new moves: `ArchWindow`, `PostcardDrop`, `LightArc`, `PathCamera`.
- **Examples:** a new example window reel, plus demos of the new moves.
- `render.mjs --preview` (and `pipeline.py render --preview`): half-size quick look that never counts for a gate.
- `client.json`: a detailed `voice_guide`; machine-specific `source_folders` go in the git-ignored `client.local.json`.

## [0.2.0]

The agent-team skeleton (0.1.0) is replaced by a working kit: a Remotion template, a creative-direction skill, a gated pipeline and a per-platform quality verifier.

### Added

- `/cutroom:video` command: drives one brief through brief → concepts → building → review → approved → delivered with `tools/pipeline.py`. Each gate is enforced: a draft or final render must pass verification, and the user must approve.
- `skills/video-direction`: concept round, beat sheet rules, motion and originality rules, sound, verify loop, delivery checklist.
- `remotion-base/`: Remotion 4 template.
  - Moves: `Morph`, `IrisOpen`, `MaskReveal`, `SplitText`, `Typewriter`, `pushThrough`.
  - An operated camera, motion blur, `Track` / `Beats` tracking (beats carry an explicit `kind`) and safe zones.
  - Three brief-driven examples (a story, a reel and a feed post).
- Structured input: `clients/<slug>/client.json` and `briefs/<id>.json`, with JSON schemas.
  - `tools/brief.py` creates clients and briefs, drafts the brand from a logo, generates `brand.ts` (with `CLIENT` and `CONTACT`), lists what is missing as questions and shows the music library.
- `tools/verify.py` with a core plus platform modules.
  - Core: rhythm, cuts, motion curves, end hold, loudness, continuity, framing, UI areas, blur, legibility, and comparison with a reference clip.
  - Platforms: Instagram (reel, story, feed video, images, reel cover, carousel), TikTok and YouTube Shorts.
  - Every platform number lives in a dated specs JSON with sources; a WARN appears after 180 days.
- `remotion-base/scripts/render.mjs`:
  - one browser per run, parallel frames, and a render cache;
  - tracking, key stills and verification;
  - loudness mastering on every render, so drafts are judged like finals;
  - records the verdict the pipeline gates on.
- `.env.example` and `scripts/config.mjs`: browser, Python, concurrency and ffmpeg paths from env, `.env` or auto-detection.
- Per-client music library (`assets/music/LIBRARY.json`, licence required).
- `tools/sfx.py` (synthesised effects) and `tools/master.py` (−16 LUFS / −1.5 dBTP).
- Tests:
  - 48 verifier and pipeline-gate cases (pytest);
  - 39 TypeScript unit tests (vitest);
  - `tools/check_plugin.py`.
- CI runs those tests and a real render of every example on each push.

### Removed

- The 0.1.0 agent-team plan: the `skills.json` catalog and the empty `agents/` and `skills/` scaffolding. `PLAN.md` is now the 0.2.0 roadmap; the old notes stay in `docs/`.

## [0.1.0]

### Added

- Claude Code plugin skeleton: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
- `skills.json`, `PLAN.md`, `docs/roadmap.svg`, `docs/add-ons.md`, `docs/v1-salvage.md`.

### Removed

- The previous TypeScript CLI (`aiteam`). It remains available in [blokxz/ai-team-tree](https://github.com/blokxz/ai-team-tree).
