# cutroom — roadmap to 1.0

> The previous CLI (v1) stays in [blokxz/ai-team-tree](https://github.com/blokxz/ai-team-tree); this repo starts clean from the v2 base.
> Visual timeline: [`docs/roadmap.svg`](./docs/roadmap.svg)

## Why change

1. **Two sources of truth.** `.aiteam/team.json` and the generated `.claude/agents/*.md`. Every change goes through `aiteam add/link/set` and then has to be regenerated with `aiteam claude --force`.
2. **"run" doesn't run anything.** `aiteam run` simulates waves with spinners, and statuses are changed by hand. Claude Code already launches subagents in parallel.
3. **Skills are a loose string.** `motionSkills` is a list of names attached by regex to editing roles: they aren't installed, versioned, or checked to exist.

## Goal

- Making a reel = typing `/reel "brief"` in Claude Code.
- Adding a community skill = adding one entry to `skills.json`.
- No custom CLI, no TUI, no build step.

## Target architecture

```
cutroom/                          Claude Code plugin + its own marketplace
├── .claude-plugin/
│   ├── plugin.json               name, version, dependencies (third-party plugins)
│   └── marketplace.json          /plugin marketplace add blokxz/cutroom
├── agents/
│   ├── director.md               orchestrates: reads the brief, writes the plan, delegates in waves
│   ├── writer.md                 research + hooks + script
│   ├── motion.md                 motion graphics (Remotion / HyperFrames / onetake)
│   ├── editor.md                 cuts, ffmpeg, captions, audio, B-roll
│   ├── art.md                    images, thumbnails, title cards
│   └── qa.md                     checks the render with ffprobe and against the brief (read-only)
├── skills/
│   ├── reel/                     entry point: /reel "brief"
│   ├── setup/                    installs the external skills listed in skills.json
│   ├── team/                     draws the team tree (replaces the TUI)
│   └── trama-reel-motion/        own skills, versioned here
├── skills.json                   catalog of community skills and tools
├── brands/                       one profile per brand: palette, fonts, tone
├── examples/                     a sample brief + result
└── README.md                     one page
```

State of each production lives in the project folder (not in a team JSON):

```
productions/<slug>/
├── brief.md      what was asked
├── plan.md       what the director decided (waves, who does what)
├── status.md     checklist; recomputed from which files exist (checking a box is not enough)
├── script.md
├── assets/       original footage, read-only
└── renders/      outputs, with the ffprobe output next to each one
```

## Phases and estimate

Estimate in hours of effective work with Claude Code. At ~1 h per weekday that's about 4 weeks; working in concentrated weekend sessions, about 3.

| # | Phase | Hours | Status |
|---|-------|------:|--------|
| 0 | Prepare: v1 salvage | 1 | ✅ done |
| 1 | Plugin skeleton + validation | 1 | ✅ done |
| 2 | Agents (11 → 6) | 4 | pending |
| 4 | `/reel` flow + brands + review gate + test reel | 6 | pending |
| 3 | Skill catalog + `/setup` (reusing proven skills) | 3 | pending |
| 5 | `/team` (visualization) | 1.5 | pending |
| 6 | Cleanup (✅ done early), final README, 1.0 release | 2 | partly done |
|   | **Total** | **≈ 18.5** | |

Order is 0 → 1 → 2 → 4 → 3 → 5 → 6: first validate one reel end to end with the minimum, then invest in the catalog. The v1 removal part of phase 6 was done early so the repo starts clean.

### Phase 0 · Prepare ✅
- The v1 CLI stays in [blokxz/ai-team-tree](https://github.com/blokxz/ai-team-tree); cutroom is a new repo.
- `docs/v1-salvage.md`: role prompts, non-negotiable rules, verification steps and wave logic, written as prose to reuse in the agents.

### Phase 1 · Plugin skeleton ✅
- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
- `skills.json` with the catalog schema (all entries are candidates until phase 3).
- `agents/` and `skills/` folders in place.
- `claude plugin validate --strict` passes cleanly.
- No `bin/` folder (it blocks installing from claude.ai).

### Phase 2 · Agents (11 → 6)
- Merge roles: research + hooks + script → `writer`; B-roll + captions + music + voice → `editor`.
- Each agent declares its model, tools, which skills it loads, and which files in `productions/<slug>/` it reads and writes.
- `qa` gets no `Write` or `Edit`.
- Check whether subagent frontmatter supports preloading skills; if not, the agent names them in its body.
- **Done when:** `claude plugin validate --strict` passes and `/agents` lists all 6.

### Phase 4 · `/reel` flow
- `skills/reel` creates `productions/<slug>/`, saves the brief and hands off to the director.
- The director writes `plan.md`, launches in parallel everything without pending dependencies, and waits for each delivery.
- Variants: `/reel --from video.mp4` and `/reel --motion-only`.
- Starts with two core skills: Remotion Agent Skills and `video-edit` (heygen-com/skills).
- **Brand profiles** (idea taken from claude-code-video-toolkit): `brands/<name>.json` with palette, fonts, tone and logo. `/reel` asks for the brand or uses the default; `art` and `motion` read it.
- **Status checked against reality:** before each wave, the director recomputes `status.md` from which files exist in `script.md`, `assets/` and `renders/`. If the file isn't there, the task isn't done, even if someone checked the box.
- **Review gate before the final render** (like the toolkit's `/scene-review`): the director shows a lightweight preview (low-res cut or key frames) and waits for approval or change requests before the final render.
- **QA that looks, not just measures:** besides `ffprobe`, QA extracts a frame every ~2 s with ffmpeg and reviews them as images (cut-off text, safe zones, captions covering faces). Free, no APIs needed.
- **Done when:** a real reel end to end produces `renders/final.mp4` and QA pastes the `ffprobe` output into `status.md` (duration, 1080×1920, fps, audio).

### Phase 3 · Skill catalog
- Each `skills.json` entry: repo, pinned commit, agent that uses it, requirements (ffmpeg, node, python).
- `/setup` walks the catalog, runs the installer for each entry, and reports any missing requirement.
- Skills shipped as plugins go into `dependencies` in `plugin.json`.

Three-tier catalog. Details for each add-on in [`docs/add-ons.md`](./docs/add-ons.md).

**Core** (always installed by `/setup`)

| Skill / tool | What for | Agent |
|---|---|---|
| Remotion Agent Skills (official) | React video → MP4 | motion |
| `video-edit` (heygen-com/skills) | direct ffmpeg/ffprobe | editor, qa |
| auto-editor | cut silences and dead time; exports to Premiere/Resolve/FCP | editor |
| onetake + trama-reel-motion | motion with rhythm, no slideshow feel | motion |

**Recommended** (offered by `/setup`)

| Skill / tool | What for | Agent |
|---|---|---|
| HyperFrames (heygen-com/hyperframes) | video from HTML + GSAP; includes explainer, talking-head recut and web-to-video flows | motion |
| WhisperX | word-level caption timing (karaoke style) | editor |
| ffmpeg + moviepy (digitalsamba/claude-code-video-toolkit, MIT) | proven encoding and compositing recipes | editor |
| Pexels MCP | free-license stock B-roll search | editor |

**Optional** (needs an account, API key or extra software)

| Skill / tool | What for | Agent |
|---|---|---|
| ElevenLabs MCP (official) | voice, cloning, sound effects, music (10k free credits/month) | editor |
| claude-vision (Gemini) | "watch" a full video and describe it scene by scene | qa, writer |
| DaVinci Resolve MCP | leave the project assembled in Resolve for manual finishing | editor |
| clipify / Youtube-clipper | reels from long videos | editor |
| Manim | math and engineering animations | motion |

- **Done when:** `/setup` on a clean machine installs everything or says exactly what's missing.

### Phase 5 · Visualization
- `/team` reads `agents/*.md` and draws the tree (Mermaid) plus the status of the active production.

### Phase 6 · Cleanup and release
- ✅ Done early: the v1 CLI (code, build, tests, scripts, schema, examples and its docs) was removed; the repo starts with only the v2 base.
- ✅ Done early: CI checks the JSON files, the catalog entries and the plugin manifest (`.github/workflows/ci.yml`).
- Pending: final one-page README with real usage (`/setup`, `/reel "brief"`, how to add a skill) once the flow exists.
- Pending: extend CI to check that every `skills.json` entry points to an existing repo and commit.
- Pending: CHANGELOG 1.0.0.

## Risks

- **Third-party skills run code on your machine** → pinned commit and review before entering the catalog.
- **Uneven quality** → start with 3–4 core skills and add one at a time, testing each with the sample brief.
- **System requirements** (ffmpeg, Node, Python; especially on Windows) → `/setup` detects them before rendering.
- **Losing the tree view** → covered by `/team`.
- **Overlapping motion engines** (Remotion, HyperFrames, onetake) → the `motion` agent picks one per piece with a simple rule written in its brief; they're never mixed in the same render.

## References

- [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) (MIT): single-agent workspace for generated video. Source of the brand profiles, the file-checked status and the pre-render review gate.
