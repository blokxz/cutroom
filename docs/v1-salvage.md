# v1 salvage (phase 0)

What's worth carrying over from the v1 CLI (repo [blokxz/ai-team-tree](https://github.com/blokxz/ai-team-tree)) into the v2 plugin's agents and skills. Everything else — the JSON tree, manual statuses, pipeline simulation, terminal themes — is dropped.

Sources in that repo: `src/core/templates.ts` (`youtube` and `instagram` templates), `src/core/claude.ts` (`renderAgentFile`) and `src/core/topology.ts`.

## 1. Role map: 11 → 6 agents

| v2 agent | Absorbs these v1 roles |
|---|---|
| `director` | Creative Director / Instagram Lead, Strategist |
| `writer` | Trend Researcher, Hook Specialist, Scriptwriter |
| `motion` | (new; in v1 it was part of Editing via `motionSkills`) |
| `editor` | Video Editor, B-roll, Captions, Music & SFX, Voice Producer |
| `art` | Art Director / Thumbnail, Title-card Designer |
| `qa` | (new; in v1 it was the "Before saying done" section) |

Out of scope for v2: SEO/distribution, community and analytics. They're post-publishing work, not production; they can be added later as standalone skills.

## 2. Role prompts to reuse

Translated from the v1 templates, to seed each agent's body.

**Director** — Defines the concept, tone and goal of the video, unblocks the team and approves every deliverable before it moves on. Delivers: creative brief + acceptance criteria. (Instagram variant: the goal of each piece — reach, saves or DMs — and acceptance criteria per piece.)

**Writer**
- Research: what's working right now in the niche (topics, angles, formats, sounds; last 72 h). Delivers: 10 ranked ideas with source and differentiating angle.
- Hooks: hook in the first 2 s (reel) or 15 s (long video): visual + verbal hook, concrete promise and pattern interrupt. Delivers: 5 variants with the hypothesis of why each retains.
- Script: scene by scene — hook, context, development, proof and CTA — for a 20–40 s reel. Delivers: timestamped script with voice-over, B-roll notes and a `script.srt` for captions.

**Art** — Visual identity and a clickable thumbnail (1 idea, 3 words, high contrast). Full-bleed 4:5 title cards and reel covers, respecting bold/italic markup and the brand highlight. Delivers: 2–3 variants per piece + palette and fonts.

**Editor**
- Vertical-paced cut: edit to the voice-over, graphics, zooms and basic sound design.
- B-roll: supporting footage for each script line, respecting licenses and resolution; clips named by scene + a credits sheet.
- Burned-in captions: 3–5 words per line, in sync, brand font, never covering the UI or faces (safe zones). Delivers: SRT + burned version.
- Music & SFX: emotional beats marked, mix with ducking, licensed stems.
- Voice: voice-over aligned to the script, clean WAV, version without music.
- Delivers: 9:16 1080×1920 (feed and stories) + 4:5 for feed, with resolution measured with `ffprobe`.

## 3. Non-negotiable rules (go into every agent)

- Original footage is read-only: never overwritten or deleted (`assets/`).
- Respect the plan's order: don't start if a dependency isn't done.
- Record your progress in `productions/<slug>/status.md` (in v1 this was `aiteam set <id> --status`).
- Don't invent metrics or results: if you didn't measure it, say "not measured".

## 4. "Before saying done" (goes to the `qa` agent and to every agent's wrap-up)

1. Run the check that fits your role (exact command, not an estimate).
2. Paste the real output of that check.
3. Mark `done` (or `error` with the concrete error) in `status.md` and notify whoever consumes your delivery.
4. If the piece is motion, run it through the motion skill's oracle: a piece whose cuts don't carry is rejected.
5. If you need to change scope, ask the director instead of deciding alone.

## 5. Wave logic (for the director, as prose)

v1 computed this in code (`executionWaves`, Kahn's topological sort and critical path). In v2 the director reasons about the plan:

- **Wave 1:** everything with no dependencies (research, hooks, B-roll search if there's footage).
- **Next wave:** every agent whose dependencies are already `done` in `status.md`. Agents in the same wave run in parallel.
- **Cycles:** if two pieces wait on each other, the plan is wrong; the director fixes it before launching anything.
- **Critical path:** the longest chain (typically script → editor → qa) sets the duration; the director flags anything that blocks it.

Typical reel plan:

1. `writer` (research + hooks + script)
2. `art` and `motion` in parallel, with `editor` preparing B-roll/music
3. `editor` assembles the final cut with everything above
4. `qa` checks and approves or sends back
