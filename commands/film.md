---
description: Make a short motion film from one request, end to end — read the reference, three concepts, a beat sheet, a look and captions, build, a draft checked in numbers, the final at full quality, sound and delivery
argument-hint: "<what the film is for>" [--ref <reference.mp4>] [--client <slug>] [--format reel|story|post]
allowed-tools: Bash(python3 tools/*) Bash(python tools/*) Bash(py tools/*) Bash(node remotion-base/scripts/*) Bash(npx tsc *) Bash(mkdir *) Bash(cp *) Read Write Edit Glob Grep
---

You are directing a short film with the cutroom kit. Request: $ARGUMENTS

Work from the root of the cutroom repo (the folder with `tools/pipeline.py`); otherwise stop and tell the user to open Claude Code in their clone. Use `python` or `py` where `python3` does not exist.

Load the `video-direction` skill and follow it (and `reel-families` for a Reel). This command is the whole protocol in one place; each step names the skill rule it applies. Budget: three user turns — the request, the concept choice, the draft approval.

1. **Reference.** If one was given: `python3 tools/verify.py <ref> --analyze --frames <ref>-frames.png`. Write its still share, longest rest, cuts, bursts and t80 into the brief's `decisions`, and look at the frame sheet (R-19).
2. **Brief and material.** `python3 tools/pipeline.py status <brief>` (create it with `brief.py new` if needed); analyse and select material (`material.py`).
3. **Three concepts** that differ in their central idea, each with the claim its picture makes, what carries every boundary and what it rules out (R-01, R-16). For a Reel, families and seeded variations from `reel-families`. Show them together; wait for one choice.
4. **Beat sheet** with uneven lengths, at least one real rest, a survivor at every boundary and a readable end hold (R-03…R-07); check it with `python3 tools/variation.py check`.
5. **Look and captions.** `python3 tools/looks.py list` → `apply <look> <slug>` (`--keep-colors` to keep the client's palette) (R-17); captions through `<Caption>` (R-18).
6. **Build** with moves from the kit (`references/remotion-kit.md`), tracked (R-15); `npx tsc --noEmit`.
7. **Draft.** `python3 tools/pipeline.py render <brief>`; fix every FAIL; decide every WARN into `decisions`. With a reference or a rival cut: `python3 tools/compare.py <draft> <other> --ref <ref> --photos <dir>` and look at `stills.png` yourself.
8. **Sound** from the piece's own events: `python3 tools/sound_events.py <draft>.track.json --out <score.wav>` (C-07 in `reel-families`); re-render.
9. **Approval.** Show the draft and stills; advance with `--approved` only after the user says so (G-02).
10. **Final** at full quality: `python3 tools/pipeline.py render <brief> --final` — PNG frames, whole-frame shutter in linear light, mastering (R-20). A 60 fps copy on request: `node remotion-base/scripts/render.mjs --brief <brief> --final --fps60`.
11. **Delivery.** Caption in the client's voice, `python3 tools/deliver.py <brief>`, `advance`; walk `CHECKLIST.md` with the user.

Rules: state results only from verifier and compare output; never claim parity with another tool; never add attribution to Claude anywhere.
