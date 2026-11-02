---
description: Make a Reel through template families in the fewest prompts — operational summary first, several rhythm-legal variations at once, one choice, then the gated video pipeline
argument-hint: "<what the reel is for>" [--variants N]
allowed-tools: Bash(python3 tools/*) Bash(python tools/*) Bash(py tools/*) Bash(npx tsc *) Bash(mkdir *) Bash(cp *) Read Write Edit Glob Grep
---

You are directing a Reel with the cutroom kit. Request: $ARGUMENTS

Work from the root of the cutroom repo (the folder with `tools/pipeline.py`); otherwise stop and tell the user to open Claude Code in their clone. Use `python` or `py` where `python3` does not exist.

Load the `reel-families` skill and follow it; it builds on `video-direction`, which owns brief, build, render, verify and delivery. Budget: at most 3 user turns (request, concept choice, draft approval).

1. `python3 tools/reel_summary.py` — execute the P0 actions and the P1 actions that touch this request, then re-run it.
2. Create or open the brief as `video-direction` says; ask only what `brief.py check` lists.
3. Generate all variants in one batch with `python3 tools/variation.py sheet|invent`, validate each with `variation.py check`, write 3 concepts, show them together and wait for one choice.
4. Continue with `python3 tools/pipeline.py status|advance|render <brief>` exactly as `/cutroom:video` does; never approve on the user's behalf.

Rules: state results only from verifier output; record seeds and decisions in the brief's `decisions`; never claim onetake parity.
