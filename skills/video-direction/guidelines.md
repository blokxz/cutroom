# video-direction — guidelines

Execution procedure derived from `spec.md`. IDs in brackets point to spec rules. Run from the cutroom repo root; `python3` may be `python` / `py` on Windows.

## 0 · Every stage [G-01 G-10 G-11]

- Loop: `python3 tools/pipeline.py status <brief>` → do `next:` → `python3 tools/pipeline.py advance <brief>`; refused ⇒ fix the listed gaps [G-01].
- Own implementation only; may study `onetake` for ideas, never copy or run its code [G-10].
- Files, code, comments, commit text in English (client copy excepted); never commit `remotion-base/out/`, `deliveries/`, `tools/models/` [G-11].

## 1 · Brief [C-01 C-02 C-03 G-05 G-06 G-07]

1. Input is a brief path ⇒ use it; skip to step 5.
2. Resolve client `clients/<slug>/`. New client:
   - `python3 tools/brief.py client new <slug> --name "…" --logo … --whatsapp …`
   - `python3 tools/brief.py client brand <slug> shots/*.jpg` — draft colours; verify against client material [G-05].
   - `python3 tools/brief.py client ts <slug>` — regenerate `brand.ts` (also after every `client.json` edit).
   - Write originals' absolute paths to `source_folders` in `clients/<slug>/client.local.json` [G-06].
   - Copy received material into `clients/<slug>/assets/`.
3. `python3 tools/brief.py new <slug> <id> --format <format> [--platform instagram|tiktok|youtube_shorts]`.
4. Fill from the prompt: goal, `copy` verbatim (`" / "` marks the accented part), CTA + contact, `avoid`, assets, reference.
5. `python3 tools/brief.py check <brief>` — ask the user only the listed questions. No answer possible ⇒ decide, append to `decisions` [§7 severity].
6. Optional music: file in `assets/music/` + entry with licence in `LIBRARY.json`; `brief.py music <slug>` lists it. `check` refuses unlicensed tracks [G-07].
7. Optional reference clip: put in `references/`, set `reference`; `python3 tools/verify.py ref.mp4 --analyze` prints its rhythm.

Edge cases:
- Prompt contains claims (health, results) ⇒ do not put them on screen; `deliver.py` flags severe claims [G-05].
- Copy conflicts with `avoid` ⇒ `check` errors; rewrite only with user consent, else record in `decisions`.

## 2 · Material and concepts [R-01 R-02 R-13]

1. `python3 tools/material.py analyze <slug> <folder> [--videos]` — reads originals read-only.
2. Open `clients/<slug>/material/<batch>/contact_sheet.png`; choose by number (ask when it matters).
3. `python3 tools/material.py select <brief> 3,7,2 [--videos 1]`. Typography-only piece ⇒ no selection needed.
4. Write 3 concepts into `brief.concepts` (`name`, `idea`, `carry`). Families: `references/concept-families.md` — a starting point, never a template [G-09].
5. Reject a set where concepts differ only by palette or type [R-01].

## 3 · Choice and beat sheet [R-03…R-07]

1. Show the 3 concepts; wait for choice. Unattended ⇒ pick strongest, record why, state it at delivery top.
2. Set `chosen_concept`.
3. Write the beat table before any code (`references/beat-sheet.md`); store in `brief.beats`.
4. Self-check the table: ratio [R-03], rest [R-04], CTA hold [R-05], survivor per boundary [R-06], one story [R-07].

## 4 · Build [C-05 G-04 G-08 R-08…R-12 R-15]

1. Create `remotion-base/src/clients/<slug>/<Name>.tsx`; register in `src/Root.tsx`; set `brief.composition`.
2. Wrap in `<CopyProvider brief={brief} defaults={…}>`; all text via `useCopy()`, brand via `CLIENT` [G-04].
3. Pick moves and helpers from `references/remotion-kit.md`; moves carry an element across a boundary, never decorate.
4. Clips: `python3 tools/material.py clip <video> --start S --dur S --out clients/<slug>/assets/videos/<name>.mp4`, play with `<Video>` from `@remotion/media`.
5. Instrument: `<TrackRoot>`, `<Beats>` with `kind`, `<Track id kind>` on subject (`inFrame`), texts, logo; `blurred` inside `<MotionBlur>`; `trackId` on `IrisOpen` [R-15].
6. Layout: `showSafeZones` in Studio; sizes and zones in `references/platform-layout.md` [R-11 R-12].
7. Type-check: `cd remotion-base && npx tsc --noEmit`.

## 5 · Originality [R-13 G-09]

- Brand colours stay; treatment (palette use, type pairing, camera grammar, transition style) changes per piece unless continuity was asked.
- Flourish needed ⇒ the main object does it (squash, wobble, pulse).

## 6 · Sound [R-14 G-07]

- `python3 tools/sfx.py` — synthesized, licence-free: air-in/out, pop, paper-slide, tap, flip, chime, click, riser, shimmer.
- `<Music duckAt={[…effect frames]}>`. `tools/sfx.py --music clients/<slug>/assets/music` = draft test bed only.
- Final mastering automatic (`tools/master.py`).
- Instagram story may ship without music; tell the client to add it from Instagram's library.

## 7 · Render, verify, review [C-06 G-02 G-03 §7]

1. `python3 tools/pipeline.py render <brief>` (draft; `--preview` = half size, never gates; `--force` re-renders unchanged).
2. Per line: FAIL ⇒ fix + re-render; WARN ⇒ decision in `decisions`; INFO ⇒ read. Detail: `references/verifier.md`.
3. Inspect stills + sheet in `remotion-base/out/<id>/` yourself — the checker measures, it does not judge taste.
4. Show draft MP4 + stills. Only after explicit user approval: `python3 tools/pipeline.py advance <brief> --approved` [G-02].

## 8 · Final and delivery [C-07 G-03]

1. `python3 tools/pipeline.py render <brief> --final` (encode + mastering); 0 FAIL required.
2. Write `deliveries/<id>/caption.md` in `voice_guide` voice: short, medium, booking versions, hashtags, alt text; no health promises.
3. `python3 tools/deliver.py <brief>`; then `advance`.
4. Deliver `deliveries/<id>/` with one line of context; walk `CHECKLIST.md` with the user; include `decisions`.

Checklist:
- [ ] Concept stateable in one sentence; video is only that [R-02].
- [ ] Uneven beats, ≥ 1 rest, CTA still ≥ 1.5 s [R-03 R-04 R-05].
- [ ] Survivor at every scene change [R-06].
- [ ] Contact correct, large, inside safe zone [R-11 R-12].
- [ ] 0 FAIL in final verify [G-03].
- [ ] Sources and licences of photos and audio noted [G-07].
