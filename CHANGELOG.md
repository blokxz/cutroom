# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · [semver](https://semver.org/) versioning.

## [0.4.0] — Unreleased

Phase 1 of the plan to surpass onetake: render quality and ease of use.

### Added

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

- `tools/sound_events.py`: sound cues placed from a render's `.track.json` (at most one per beat, 0.04 s apart, text never sounds, pan from screen x) with an optional stereo `score.wav` mixed from the `sfx.py` palette. Contract C-07 in the `reel-families` spec.

- `docs/cases/`: a case template and the first case, `sample-post.md`, with real verifier numbers (what was rejected is marked "not recorded", never reconstructed).

### Removed

- The worked-example client and its four pieces: every client asset, brief and example built for it. The kit now ships only a fictional `sample` client (generated photos and logo, SIL OFL fonts, generated music) and one example, `SamplePost`, used by the tests, CI and `doctor.py`. Real clients are created from scratch through `/cutroom:video`.

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
