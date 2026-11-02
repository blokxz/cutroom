# cutroom vs onetake — module by module

Reviewed 2026-10-26 against cutroom 0.4 (branch `v0.4-render-setup`) and the onetake skill as published
(SKILL.md, references, script docstrings). This is a comparison of criteria and capabilities, not of code:
cutroom never uses onetake or copies its code (see `.claude/CLAUDE.md`, rule 4).

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
- [ ] Logbook, Light clock, Before / after rest · 4–6 h
- [ ] Moves for the ten families added on 2026-10-26 (match cut, object wipe, film strip, scrapbook,
      chain reaction, dive through scale, calendar, letters as windows, thread, depth). Ideas drawn from
      travel-reel transition trends (object masking, match cuts, whip pans) and onetake's concept types
      (chain reaction, a dive through scale); designed for photo-led pieces · 3–4 days
- [ ] Camera: follow helper (key ahead of the subject), whip to a landing, hand float that stops in holds,
      shake on landings, a depth layer so moves read on an empty ground · 4 h
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
