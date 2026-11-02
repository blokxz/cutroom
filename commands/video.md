---
description: Make a short motion video (story, reel, post) from a free prompt and the user's material — brief, concepts, beat sheet, Remotion build, render and quality check, one gated stage at a time
argument-hint: "<what the video is for>" or <path to an existing brief.json>
allowed-tools: Bash(python3 tools/*) Bash(python tools/*) Bash(py tools/*) Bash(npx tsc *) Bash(mkdir *) Bash(cp *) Read Write Edit Glob Grep
---

You are directing a short motion video with the cutroom kit. Request: $ARGUMENTS

Work from the root of the cutroom repo (the folder with `tools/pipeline.py`, `remotion-base/` and `clients/`). If the current folder is not that repo, stop and tell the user to open Claude Code in their clone of cutroom. The commands below use `python3`; on machines where Python 3 is called `python` or `py` (common on Windows), use that name instead.

Load the `video-direction` skill first and follow it — it holds the creative rules. This command adds the order and the gates:

1. **Find or create the brief.**
   - If the request is a path to a brief, use it.
   - Otherwise identify the client (`clients/<slug>/`; new client → `python3 tools/brief.py client new …`, then `client brand` and `client ts`; record the folders holding the client's originals as absolute paths in `source_folders` of `clients/<slug>/client.local.json` (git-ignored) — every tool refuses to write there) and create the brief with `python3 tools/brief.py new <slug> <id> --format <format> [--platform instagram|tiktok|youtube_shorts]`.
   - Fill it from the request: goal, copy exactly as it must appear, CTA, contact, words to avoid, assets, reference.

2. **Loop until delivered.** At every step run:

   ```bash
   python3 tools/pipeline.py status <brief>
   ```

   Do what its `next:` line says, then:

   ```bash
   python3 tools/pipeline.py advance <brief>
   ```

   - A refused advance lists what is missing: fix that, don't edit `status` by hand.
   - **brief** — ask the user only the questions `status` lists. If nobody can answer, decide, and write the choice into `decisions`.
   - **material** — `python3 tools/material.py analyze <slug> <folder> [--videos]`, open `clients/<slug>/material/<batch>/contact_sheet.png`, choose photos by number (ask the user when the choice matters) and run `python3 tools/material.py select <brief> 3,7,2 [--videos 1]`. Then write three concepts.
   - **concepts** — show the three concepts and wait for the user's choice.
   - **building** — build the composition, then:

     ```bash
     python3 tools/pipeline.py render <brief>
     ```

     Fix every FAIL and re-render. WARN lines need a decision written into `decisions`. While iterating, `render <brief> --preview` gives a half-size quick look (it never counts for a gate).
   - **review** — show the draft MP4 and the stills (`remotion-base/out/<id>/`). Only after the user says it's approved:

     ```bash
     python3 tools/pipeline.py advance <brief> --approved
     ```

     Never approve on their behalf.
   - **approved** — run:

     ```bash
     python3 tools/pipeline.py render <brief> --final
     ```

     Then write `deliveries/<id>/caption.md` in the client's voice (`voice_guide` in client.json: short, medium and booking versions, hashtags, alt text — no health promises) and build the package:

     ```bash
     python3 tools/deliver.py <brief>
     ```

3. **Deliver** `deliveries/<id>/` (video, covers, WhatsApp version, caption, sheet, checklist) with one line of context. Go through `CHECKLIST.md` with the user and include `decisions`.

Rules:
- The brief is the single source of on-screen text. Compositions read copy, CTA and contact through `useCopy()` from `src/lib/brief.ts`, never as strings written in the component.
- Never claim a render passed without the verifier output showing no FAIL.
