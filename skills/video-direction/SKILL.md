---
name: video-direction
description: Direct a short motion video (story, reel, post, promo) in Remotion so it reads as an original piece and not a template — concept round, beat sheet, continuity between scenes, motion rules, sound, and an automatic verify loop before delivery. Use whenever a short animated video, social story or promo clip is requested.
---

# Video direction

A short motion piece fails in two predictable ways: it looks like a template, or it plays like a slideshow (one card replaced by the next, every card on screen for the same time). This skill exists to avoid both. It sits on top of the Remotion template in `remotion-base/` and the checker in `tools/verify.py`.

Work in this order. Do not skip steps.

## 1 · Brief and material

The input is a free prompt plus whatever material the user sends. Turn it into files before designing:

- **Client folder** — `clients/<slug>/` holds what stays the same: `client.json` (contact, brand colours and fonts, voice), `assets/` (logo, photos, videos, fonts, music) and `references/`. New client: `python3 tools/brief.py client new <slug> --name "…" --logo … --whatsapp …`, then `brief.py client brand <slug> shots/*.jpg` to draft the colours from the logo and screenshots (check them against the client's material — never invent a brand) and `brief.py client ts <slug>` to generate the Remotion `brand.ts`. Put the material the user sends into `assets/`.
- **Brief** — one per video at `clients/<slug>/briefs/<id>.json` (schema: `schemas/brief.schema.json`): goal, format, duration, CTA and contact, every on-screen text exactly as it must appear (`copy`, with " / " marking the accented part), words to avoid, assets, reference, and later the concepts, chosen concept, beat sheet, composition id and status. Create it with `brief.py new <slug> <id> --format reel [--platform instagram|tiktok|youtube_shorts]`, fill it from the prompt, then run `brief.py check` — it validates the brief against the platform and lists what is still missing as questions. Ask only those; if nobody can answer, decide, and record the choice in `decisions`.
- **Music** (optional) — only licensed or client-supplied tracks: put them in `clients/<slug>/assets/music/` and list them in its `LIBRARY.json` (`brief.py music <slug>` shows the library). `brief.py check` refuses music without a licence.
- **Reference clip** (optional) — put it in `references/` and set `reference` in the brief. `python3 tools/verify.py ref.mp4 --analyze` prints its rhythm numbers (still share, cuts, beat lengths, motion curves); renders from the brief are compared against it automatically.

Stages: brief → concepts → building → review → approved → delivered. Move between them only with `python3 tools/pipeline.py advance <brief>` (the `/cutroom:video` command does this): it refuses a stage that lacks what it needs — three concepts, a chosen one, a beat sheet, a composition id, a draft that passed verification, the user's approval, a final render that passed. `pipeline.py status <brief>` says what blocks and what to do next.

## 2 · Three concepts, then pick one

A concept is one sentence about **the picture**, not about the product: the single visual idea the whole video is made of. Write three that differ in that idea — not the same story told with three color schemes. Useful families:
- **One object that transforms** through every beat (an envelope becomes the card, the card becomes the CTA button).
- **One camera move** through scale (start on a detail, pull back to the place, push into the phone number).
- **Cause and effect** — each beat is what triggers the next one.
- **A physical metaphor** — a postcard being written, a key turning, a ticket being torn.
- **A typographic system** — the words themselves are the set.

Families that grew out of photo-led pieces (places, rooms, a day out). For each, what carries across the scene changes:
- **Window** — one framed window holds every place and changes shape (arch → landscape → circle); the next place opens out of a point of the photo before (a door, the steam, a ray of sun). Carries: the window outline and the opening point.
- **Postcards** — cards of each place fall onto a table, squash, stack and nudge each other, then resolve into a grid around the logo. Carries: the pile.
- **Day arc** — a disc of light crosses the frame from morning to night; each place opens with an iris born from the disc. Carries: the disc and its colour.
- **Trail** — photos pinned in a larger world; the camera walks a drawn path from one to the next while the trail draws itself. Carries: the camera and the trail.
- **Living map** — a map of the place with pins; each card opens out of its pin and folds back into it. Carries: the map and the pins.
- **From coffee to evening** — one full day in photos and clips, ending on a frozen frame that turns into a cream postcard. Carries: the time of day (light, colour), then the frozen frame.
- **Entering** — a first-person walk in one continuous camera gesture: door → inside → a detail → a window with light → the view. Carries: the single camera move.
- **Small details** — a 2×2 grid that fills with close-ups and micro-clips, one word per detail, closing on one large still frame. Carries: the grid, then the cell that grows.
- **Logbook** — one day told as a handwritten travel journal; a written hour opens each beat (8:00, 11:00, 19:00) and the ink stroke that ends one entry draws the next scene. Carries: the page and the ink line.
- **Key** — a key turns and each turn unlocks the next place; it ends on the open door with the contact. Carries: the key and its rotation.
- **Written postcard** — the back of a postcard fills with cursive, the stamp is a photo, and flipping the card reveals the place. Carries: the card, written side → picture side.
- **Light clock** — a single view of the place held still while its light moves from morning to night (grade and light passes over one photo, no cuts). Unlike Day arc, nothing travels: only the light changes. Carries: the frame itself.
- **Before / after rest** — split screen: a grey city against the place; the place's half pushes the seam until it owns the frame. Show rest, never promise an effect. Carries: the seam.
- **Match cut** — each place ends on a shape the next one repeats in the same spot of the frame (a round table → the rim of a cup → the setting sun); the shape holds still while the photo around it changes. Carries: the matched shape and its position.
- **Object wipe** — something in the scene crosses the lens (a towel, a branch, a door frame, a hand) and uncovers the next place as it leaves. Carries: the wiping object and its direction.
- **Film strip** — a strip of negatives slides through the frame; one frame is pulled out, develops into colour and grows into the scene; at the end the strip curls into the logo. Carries: the strip.
- **Scrapbook** — an album page being made: photos taped down, a ticket, a pressed leaf, labels in the script face; the camera drifts across a page that keeps growing. Carries: the page.
- **Chain reaction** — every beat is the cause of the next: a pine cone drops, the ripple it makes frames the next photo, the steam from that photo blows the page… Carries: the cause, always visible.
- **Dive through scale** — one continuous zoom from the whole region down to one detail (or back out): Entre Ríos → the river → the complex → the deck → the cup. No pins, no cuts. Carries: the anchor point, which stays put on screen.
- **Calendar** — a desk calendar whose pages tear off one by one; each torn page reveals the day's place; the last page is blank, "your dates", with the contact. Carries: the calendar block.
- **Letters as windows** — the headline set huge, each letter a window onto a photo; the camera flies through the counter of a letter into the next place and the word resolves at the end. Carries: the letterforms.
- **Thread** — one thread in the brand colour runs through every scene, wrapping around things in the photos (a towel, a railing, a branch), and ties a bow around the logo or the gift card. Carries: the thread.
- **Depth** — each photo split into planes (foreground, subject, sky) that move at different speeds; the camera dollies through the foreground into the next photo. Needs layer masks (cut by hand or with a segmentation model). Carries: the camera and the nearest plane.

A family is a starting point, not a template: every piece still gets three concepts written for its brief and its material, and the chosen one is designed from scratch — its own opening frame, timing, shapes and type. Never fill a previous piece with new photos.

For each concept state: the opening frame, what carries from scene to scene, what it rules out, and its look (palette + type). Show the three to the user and let them choose. If nobody can answer (unattended run), pick the strongest, say which and why at the top of the delivery.

## 3 · Beat sheet

Write the chosen concept as a table before writing any code:

| t (s) | beat | what moves | what holds still | what carries into the next beat |
|---|---|---|---|---|

Rules for the table:
- **Uneven durations.** The longest beat should last at least 3–4× the shortest. Equal lengths read as slides no matter how good each one is.
- **At least one real rest** — ≥ 0.8 s where almost nothing moves. Rests make the active parts land. The final CTA hold (≥ 1.5 s, still and readable) counts.
- **One story.** One idea developed, not a catalogue of features.
- **Small elements, big ground.** Generous empty space; one full-bleed hero moment at most.
- **Every boundary has a survivor.** Name the element that lives through each scene change and visibly moves or scales into the next scene (it morphs, the camera pushes into it, the next scene opens out of it). A plain fade between unrelated scenes is a slide change. Hard cuts are allowed only in deliberate quick bursts and for the end card.

## 4 · Build in Remotion

Build inside `remotion-base/`: put the composition in `src/` (e.g. `src/clients/<slug>/<Name>.tsx` or a new folder next to `examples/`) and register it in `src/Root.tsx`. The template gives formats with Instagram safe zones, brand tokens, motion helpers, a camera, reusable moves and tracking.

- **Moves** (`src/moves`): `Morph` (a box becomes another box), `IrisOpen` (the next scene opens out of a point), `MaskReveal`, `SplitText`, `Typewriter`, `pushThrough` (camera keys into a rectangle). They take a progress value — you choose the curve. They are tools for carrying an element across a boundary, not decorations to sprinkle.
- **Bigger moves** (`src/moves/*.tsx`, pure math exported next to each component and unit-tested):
  - `ArchWindow` + `archShape` / `rectShape` / `circleShape`, `mixShape`, `windowFromPoint`, `anchorPoint`, `coverLayout` — a framed window whose outline morphs between shapes; the next scene is born as a small arch on the previous photo's anchor while that photo zooms into the same point (the anchor stays put).
  - `PostcardDrop` + `postcardPose`, `dropPose`, `squash`, `stackRest`, `gridCells` — cards fall with a landing squash and settle, stack with a seeded tilt, later cards nudge earlier ones, then they spring into a grid.
  - `LightArc` + `arcPoint`, `lightColor`, `DAY_LIGHT` — a disc on an arc whose colour moves through the day; pass `iris` to open the next scene out of the disc (uses `IrisOpen`).
  - `PathCamera` / `PathTrail` + `buildPath`, `nearestLength`, `pathFrame` — the camera travels an SVG path (M L H V C Q Z) across a world of placed photos; arc length is computed in TypeScript, so it is deterministic; `nearestLength` gives the stop for each photo.
  - `KeySvg` (front / profile) + `keyTurn`, `keyTurns`, `Keyhole`, `KeyholeIris`, `keyholeShape`, `DoorSwing` — a key with an arched bow goes into the lock and turns a quarter with a small overshoot (the click); the next scene opens out of the keyhole, and `DoorSwing` opens a door leaf in perspective onto what is behind it (the contact).
  - `Handwriting` + `writeSchedule`, `inkAt`, `writingEnd`, `Stamp`, `Postcard`, `flipAngle` — text written letter by letter with a soft ink front (timing weighted by letter width, pauses after words, punctuation and lines; use the brand's `script` font), a perforated photo stamp with a postmark, and a two-sided card that flips from the written back to the photo.
  Studio-only demos of each live in the `moves` folder of Root (`MovesDemo-*`).
- **Video clips.** Prepare each clip first with `python3 tools/material.py clip <video> --start S --dur S --out clients/<slug>/assets/videos/<name>.mp4` (cut, 30 fps, H.264, no audio, HDR → SDR) and play it with `<Video src={asset("videos/<name>.mp4")} muted>` from `@remotion/media` inside a `<Sequence>` (frame-accurate in renders and the fastest option — Remotion marks `<OffthreadVideo>` and `<Html5Video>` as not optimized; use `trimBefore` (frames into the clip) and `playbackRate` props, never CSS or the DOM video element). A clip can sit inside any move — a window, a card, an iris.
- **Track what matters.** Wrap the subject, each text block and the logo in `<Track id kind>`; mark the subject `inFrame`, and anything inside `<MotionBlur>` as `blurred`. Declare the beat sheet with `<Beats>` and put `<TrackRoot>` at the root. The verifier uses this to check continuity, framing, text safe zones and blur. Give every beat its `kind`: `move` (the boundary must carry an element), `rest` / `hold` (expected to be still), `cut` (a deliberate hard cut). Rests, holds and cuts are exempt from the carry count. Pass `trackId` to `IrisOpen` so an opening out of the subject counts as a carry.

- **Everything from the frame number.** `useCurrentFrame()` + `interpolate()` / `spring()`. No CSS transitions or animations, no `Math.random()` (use `random(seed)` from `remotion`). Same frame → same picture, always.
- **Pick the curve by intent, not by habit:**
  - landings and arrivals → `spring` with low damping (a visible settle);
  - snaps and whips → fast ease-out (`EASE.snap`);
  - camera and slow drifts → gentle ease-in-out (`EASE.glide`).
  Using one soft S-curve for everything is what makes motion look generic.
- **A camera that is operated, not static.** Wrap the scene in `<Camera>`: key it slightly ahead of the subject so it follows, let it settle after each landing, add a slow drift during holds (`drift()`), keep it still during the final CTA.
- **Fast moves need motion blur.** Anything that travels more than ~60 px per frame goes inside `<MotionBlur>` (`src/components/MotionBlur.tsx`, already wired in the examples): drafts get few samples, finals 12. It uses the camera engine by default; the HTML-in-canvas engine (a real shutter) is opt-in with `CUTROOM_BLUR_ENGINE=canvas` once `scripts/blur-ab.mjs` shows it works on the machine. CSS blur is not motion blur.
- **Text comes from the brief.** Read headline, lines, CTA and contact with `useCopy()` (wrap the composition in `<CopyProvider brief={brief} defaults={…}>`) and the brand name/taglines from the generated `CLIENT`. Never type on-screen copy into the component.
- **Safe zones.** Keep text and logos inside the margins of `FORMATS.<id>.safe` (read from the verifier's specs, so Studio and the checker agree): Instagram story y = 250–1600; reel y = 250–1520 with 140 px free on the right for the action buttons; TikTok and Shorts cover even more at the bottom (480 px) and on the right. Turn on `showSafeZones` in Studio while composing; it never renders in the final file unless asked.
- **Type sizes** at 1080 wide: headline ≥ 84 px, supporting text ≥ 44 px, phone number / CTA ≥ 72 px.

## 5 · Originality rules

- Never reuse the previous video's look (palette, type pairing, camera grammar, transition style) unless the user asked for continuity. Brand colors stay; the treatment changes.
- No particles, confetti, sparkle bursts or lens flares as decoration. If a beat needs a flourish, let the main object do it (squash on landing, a wobble, a pulse).
- No stock-transition carousel (fade → slide → zoom → fade). Transitions come from the concept.
- Don't default to the "kinetic words → list ticking → logo" story. It is one concept among many, never the default.
- Cause must be visible: if something reacts, show what made it react.

## 6 · Sound

- Few events, not one beep per animation. One soft material family (paper, wood, air) in one room.
- Generate soft effects with `python3 tools/sfx.py` (synthesized, license-free: air-in/out, pop, paper-slide, tap, flip, chime, click, riser, shimmer) or use royalty-free sources and keep their license next to the project.
- Music only if royalty-free or supplied by the client. Use `<Music duckAt={[…effect frames]}>` so it dips under each effect. `tools/sfx.py --music clients/<slug>/assets/music` writes a calm test bed — fine for drafts, not a replacement for real music.
- Final renders are mastered automatically (`tools/master.py`: −16 LUFS, −1.5 dBTP).
- For Instagram stories it is fine to deliver without music and tell the client to add it from Instagram's library.

## 7 · Verify before showing

Render a draft — it syncs client assets, tracks, exports key stills and verifies in one go:

```bash
cd remotion-base
node scripts/render.mjs --brief ../clients/<slug>/briefs/<id>.json           # draft into out/<id>/
node scripts/render.mjs --brief ../clients/<slug>/briefs/<id>.json --final   # final encode + audio mastering
node scripts/render.mjs <CompositionId>                                      # without a brief
```

(`python3 tools/pipeline.py render <brief> [--final]` runs the same and records the verdict the pipeline gates on. An unchanged composition is not re-rendered; `--force` re-renders.)

With `--brief`, the composition receives the brief as its `brief` prop; `useCopy()` reads copy, CTA and contact from it, so the brief stays the single source of on-screen text.

The verifier (`tools/verify.py`, platform modules in `tools/quality/platforms`, numbers in `platforms/specs/*.json`) uses the brief's platform — Instagram, TikTok or YouTube Shorts. For Instagram it checks:
- **technical limits** of the publishing API — container, codec, 4:2:0, frame rate 23–60, bitrate, duration and file size per format, AAC ≤48 kHz, moov at the front, keyframe interval, colour; for images JPEG, ≤8 MB, 320–1440 px wide, 4:5–1.91:1, sRGB;
- **rhythm** (still share, rests, uneven beats, metronome cadence), **hard cuts**, **motion curves** (t80 of every move: all on one curve, or slow/linear starts), the **end hold** for the CTA, **audio** levels;
- with tracking: **continuity** (no scene boundary where everything is replaced), **framing**, **text in the UI-covered areas**, **motion blur** on fast elements, **legibility** (text height);
- **layout**: the areas stories/reels UI covers, the **3:4 profile-grid crop** (reel cover, feed posts), and for reels the **hook** (first second) and the **loop** seam.

TikTok and Shorts get the same core checks plus their own upload limits and UI areas. If the verifier warns that a platform's specs are stale, re-check the official pages listed in its specs file.

**FAIL** lines must be fixed and re-rendered; **WARN** lines need a conscious decision; **INFO** is context. Look at the stills and the sheet yourself before delivering — the checker measures, it doesn't judge taste.

Other uses:
```bash
python3 tools/verify.py client_old_video.mp4                  # any MP4: format auto-detected
python3 tools/verify.py draft.mp4 --ref reference.mp4         # how close the rhythm is to a reference the client likes
python3 tools/verify.py post.jpg                              # feed / story images
python3 tools/verify.py carousel_folder/                      # carousel: count, matching ratios, each slide
python3 tools/verify.py reference.mp4 --analyze               # numbers only
```

## Examples to learn from

`remotion-base/src/examples/sample/SamplePost.tsx` (post 4:5) — a typographic system: the brand words are the set and fly into the card's tagline; its beat sheet is in the header. It belongs to the fictional sample client (`clients/sample/`, synthetic assets) and exists for tests, CI and `doctor.py`: never fill it with a real client's material. Every real piece starts from its own brief and concepts.

`remotion-base/src/examples/moves/MovesDemo.tsx` — `PostcardDrop`, `LightArc`, `PathCamera`, `Key` and `WrittenPostcard` on their own (Studio only, not pieces).

## 8 · Delivery checklist

- [ ] The concept is stateable in one sentence, and the video is only that.
- [ ] Beat lengths are uneven; there is at least one rest; the CTA holds still ≥ 1.5 s.
- [ ] Every scene change has a survivor element.
- [ ] Contact data is correct, large, and inside the safe zone.
- [ ] `render.mjs` / `verify.py` report no FAIL.
- [ ] Final render at the requested size; still frames (PNG) of the key moments for the client if useful.
- [ ] Sources and licenses of photos and audio noted.
