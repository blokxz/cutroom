# cutroom vs onetake — module by module

Reviewed 2026-10-26 (studied directly 2026-11-02, see the end) against cutroom 0.4 (branch `v0.4-render-setup`) and the onetake skill as published
(SKILL.md, references, script docstrings). This is a comparison of criteria and capabilities, not of code:
cutroom studies onetake for ideas and writes its own implementation; it never copies or runs its code (see `.claude/CLAUDE.md`, rule 4).

Where cutroom is weaker, the gap becomes work in one of the improvement phases below. Re-run this review
when a phase closes.

**Different targets.** onetake makes launch films for software products (real UI as material, 16:9 first,
4K60). cutroom makes social pieces for small businesses (their photos and clips, 9:16 first, a brand and a
contact, publish-ready packages). Some onetake strengths are out of cutroom's scope and are marked so.

Legend: **ahead** · **even** · **behind** · *out of scope*

| # | Module | onetake | cutroom 0.4 | Verdict |
|---|---|---|---|---|
| 1 | Creative direction | 3 concepts by central idea, beat sheet with rhythm + carry, hard rules learned from rejected cuts | Same discipline in `video-direction`; 13 photo-led concept families; brief as the single source of copy | **even** |
| 2 | Process and gates | Protocol in prose, "no skipping" | `pipeline.py`: 7 stages, gates that refuse a stale or failing render, user approval at review | **ahead** |
| 3 | Client, brand and copy | Looks: 6 measured presets, look from screenshots, fonts subset and inlined | `client.json` + generated `brand.ts`, `brand.py` from logo/screenshots, voice and words to avoid, claims check | **ahead** for brands; **behind** without one (no presets) |
| 4 | Material | Real pages recorded with Playwright, UI rebuilt from screenshots | Photo/video folder analysed read-only, numbered contact sheet, clip prep (HDR → SDR) | **ahead** for photo-led work; UI footage *out of scope* |
| 5 | Reference analysis | Energy map, stillness, cuts, bursts, t80, smear, contact sheets | `verify.py --ref` / `--analyze`: stillness, cuts, beat length, t80, energy shape | **even** (no smear reading) |
| 6 | Move library | 39 moves (entrances, carries, contact sims, camera, fluid set), gallery with a sheet + speed graph per move, library tests | 12 moves + motion helpers, Studio demos, unit tests; no sheets, no sims, no fluid set | **behind** |
| 7 | Camera | Keyed but operated: key ahead of the subject, whips to the landing, hand float off in holds, shake on landings, lattice for depth, screen boxes for framing | `Camera` with keys + drift that fades for holds, `PathCamera`, framing check from `track.json`; no chase helper, no shake, no depth | **behind** |
| 8 | Voice, subtitles, languages | Local TTS (Kokoro), word times (faster-whisper), line plan, timed subtitle chunks, second language on the same comp with a time warp, pixel check of the source | Nothing | **behind** (largest gap) |
| 9 | Sound | Synthetic palette in one room + scored mixes timed from the comp's events, ducking, −16 LUFS | `sfx.py` palette in one room, `Music` with ducking, `master.py` −16 LUFS; effects placed by hand | **behind** (no event-driven score) |
| 10 | Render | Shutter blur sized by on-screen travel, holds skipped, parallel browsers, 1080p30 drafts / 4K60 final | Remotion render, cache, `MotionBlur` (camera engine + real-shutter engine opt-in), `--preview`, `--master-4k`; 30 fps only | **even** (60 fps pending) |
| 11 | Verifier | Rhythm legs, burst, audio peak, continuity (carry score), curves, framing | All of those plus per-platform specs (Instagram, TikTok, Shorts) with dates and sources, safe zones, reading time, text size, integrity (black, frozen, bars), faces, claims, loudness | **ahead** |
| 12 | Delivery | An mp4 | Final video, covers (9:16, grid 3:4 and 1:1), WhatsApp version, caption, publishing checklist | **ahead** |
| 13 | Install and diagnosis | Requirements listed | `setup.py`, `doctor.py`, `.env`, CI on Linux and Windows | **ahead** (pending a real Windows run) |
| 14 | Proof: cases and demos | 10 films, each with a README (beat sheet, numbers, what was rejected and why), gallery, hero GIFs | 4 example pieces, Studio move demos, no case write-ups | **behind** |

## Where cutroom must improve → phases

### Phase 1 — render quality and ease of use (0.4) · code done

Modules 10 and 13. `MotionBlur` with two engines, `--master-4k`, `setup.py`, `doctor.py`, Windows CI.

Left to close it:
- [ ] `setup.py` + `doctor.py` on a real Windows PC and on Linux (the netbook) · 1 h
- [ ] Choose the blur engine with `scripts/blur-ab.mjs` · 0.5 h
- [ ] 60 fps profile: format option, render, verifier limits at 60 fps · 2–3 h

### Phase 2 — moves, camera and sound · started (priority)

Modules 6, 7 and 9. onetake's move library is a source of *ideas* (what kinds of moves a piece needs);
every move is designed and written from scratch for cutroom's families and photo-led material.
- [x] Key and Written postcard (0.4)
- [ ] Moves the families are missing, by kind: entrances that land (squash, settle), carries (a container
      that becomes the next scene, a cast that gathers into the logo lockup), contact (a light shake on
      impact), each wired into at least one family · 1 day
- [x] Logbook, Light clock, Before / after rest — covered by existing moves (`Handwriting` + `MaskReveal`, `LightArc`, `MaskReveal`), registered as `ready` families; a dedicated move is added only if a shipped piece shows the gap (decision 2026-11-09)
- [ ] Moves for the ten families added on 2026-10-26 (match cut, object wipe, film strip, scrapbook,
      chain reaction, dive through scale, calendar, letters as windows, thread, depth). Ideas drawn from
      travel-reel transition trends (object masking, match cuts, whip pans) and onetake's concept types
      (chain reaction, a dive through scale); designed for photo-led pieces · 3–4 days
- [x] Camera: follow helper (`leadKeys`), whip to a landing (`whipKeys`, `EASE.whip`), hand float that stops in holds (`holds`),
      shake on landings (`shakes`), a far grid so moves read on an empty ground (`Lattice`) · done 2026-11-09. Depth layers still open.
- [ ] Event-driven sound: effects placed from the beats in `track.json` instead of by hand, one material
      family per piece, music ducked under the hits · 4 h
- [ ] Move sheets: a still strip + speed graph per move, generated from the Studio demos · 3 h

≈ 6–7 days with the ten new families (≈ 3 without them).

### Phase 3 — voice and subtitles · on hold

Module 8. Parked by decision (2026-10-26): the client's reels carry their text on screen and narrated
reels are not common yet. Scope kept for later: local TTS or the user's recording, word timing with
faster-whisper, a `Captions` component inside the safe zones, ducking under the voice, a subtitle check in
the verifier, a second language from the same composition. ≈ 2 days.

### Phase 4 — demos and cases · not started

Module 14.
- [ ] One case per example piece: `docs/cases/<piece>.md` with beat sheet, verifier numbers, what was rejected and why · 3 h
- [ ] A showcase reel of cutroom made with cutroom · 4 h
- [ ] README with GIFs of the pieces and the move sheets · 1 h

≈ 1 day.

**Total left without phase 3: about 8–9 days of work** (4–5 without the ten new families), plus review rounds.

## Study of onetake — 2026-11-02

First direct reading of the published skill (SKILL.md, six references, `lib/motion.js` outline, `looks.json`, ten case READMEs, the verifier's legs). Everything below is our own summary of what it does and the design we would build for photo-led social pieces; none of its code is copied or run. Its licence (PolyForm Noncommercial 1.0.0) would not allow reuse anyway.

### What it is

- A film is **one HTML file** that is a pure function of time (`__seek(t)`), built on a **39-move library** in five groups: enter (7), carry (8), contact (6 + 4 live sims), camera (≈10), fluid (5: light field, ripples, silk, belt, SwiftUI-style springs).
- Rendered frame by frame with **real shutter blur**: several seeks across the open shutter averaged in linear light, sample count sized by the farthest on-screen travel the comp declares (camera included); still stretches skip it; several browsers in parallel; 1080p30 drafts, 4K60 final.
- An **oracle** for acceptance: cadence, rest, burst, audio, then (with the comp) carry score, curves and framing.
- Targets product launches (10–30 s, demos to 60 s): real UI recorded or rebuilt, narration, subtitles, second language by time-warping the audio onto one composition.

### Counts, side by side

| Thing | onetake | cutroom |
|---|---|---|
| Moves | 39 | 12 + motion helpers |
| Named concept types | ≈7 (element transforms, camera through scale, before/after split, chain reaction, physical metaphor, continuous surface, typographic system) | 30 families |
| Case films with write-ups | 10 | 1 sample, no write-up |
| Look presets | 6, measured from accepted films | brand from logo/screens (`brand.py`) |
| Sound materials | 6 synthesized, one room | 9 synthesized effects (`sfx.py`), one family per piece |

Families and move counts are not the same unit: a family is a creative idea built from several moves. Every concept type onetake names exists in cutroom (transforming object, scale camera / dive, before–after rest, chain reaction, physical metaphor, typographic system). Two of its case films use ideas we lacked: a **continuous belt of places** and a **field of light that floods and drains in rings onto the next scene**; both are now registered as families (`continuous_surface`, `light_flood`, status `needs-move`).

### Where cutroom is already at or past it

- Rhythm: beat-length variation must be CV ≥ 0.3 (theirs 0.25); hard cuts, motion curves (t80), end hold, reading time and per-platform limits are checked; theirs has no platform specs, safe zones, claims check, covers or caption package.
- Gates: `pipeline.py` refuses stale or failing renders; theirs is a protocol in prose.
- Same lessons arrived at independently: no particle decoration, never cut on a metronome, a survivor at every boundary, small elements on a big ground, one sound room, deterministic frames.

### Ideas worth building ourselves (own design)

| # | Idea | Why it matters | Maps to |
|---|---|---|---|
| 1 | **Operated camera helpers**: key the subject ~0.1 s ahead, key the landing before a snap, a slow hand float that is zero in holds, a decaying seeded shake on landings | their one-dot film was rejected with a still camera and accepted with a chasing one | phase 2 camera; Q-04 |
| 2 | **A far grid on empty ground** so camera moves read against something | moves on an empty ground do not read | phase 2 camera |
| 3 | **Depth from one camera**: layers at different depths moved by one view matrix, blur by distance from the focus plane | gives `Depth` family a path that needs fewer masks | phase 2; family `depth` |
| 4 | **Blur samples sized by declared travel** (done: `<MotionBlur travel>`; the composition declares the travel, `track.json` is not read back) (camera travel adds to each element's) from `track.json`, not a fixed count | fewer renders wasted on holds, no bands on whips | `MotionBlur` |
| 5 | **Events from the composition**: sounds placed from its own event list, none within 40 ms of another, panned by screen x, a room shared by all | one room, fewer sounds than beats | Q-06; phase 2 sound |
| 6 | **True-peak margin for AAC**: their finals needed a −3.5 to −4 dBTP ceiling before the AAC re-encode stayed under −3 dBFS; we master at −1.5 dBTP, so measure the encoded file (the verifier already reads it) before trusting the master | avoids a late audio FAIL | `master.py` |
| 7 | **Case write-ups** per piece: concept, beat sheet, measured numbers, what was rejected and why (with the client's own words) | their strongest teaching asset; we have none | phase 4; Q-08 |
| 8 | **Meaning built into the picture**: a film that was "beautiful but says nothing" only worked once the idea was in the artwork; labels added to explain made it worse | new creative rule R-16 in `video-direction` | R-16 |
| 9 | **Do not show whole pages as thumbnails**: show a component live, or full-frame with the cause visible | applies to our photo-led pieces as: full-frame photo or a detail, never a tiny postage stamp of a place | `video-direction` §4 |
| 10 | **Fluid set**: a light field as the ground, rings that drain onto the next scene, a belt that slows with its own clock, domain-warped noise "silk" fills | each is a new family seed; only `light_flood` and `continuous_surface` registered so far | phase 2 moves |

### Not for cutroom (for now)

- Recording or rebuilding UI, narration, word timing, subtitles, second language by time warp: parked with phase 3.
- 4K60 as the default final: our platforms top out at 1080p; `--master-4k` stays optional.

### Verdict changes

None of the 14 rows flips. Row 11 (Verifier) stays **ahead**; row 6 (Move library) stays **behind** and now names fluid, contact and camera helpers as the missing kinds; row 14 (Proof) stays **behind** with the case template described above.
