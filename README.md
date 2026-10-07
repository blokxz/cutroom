# cutroom

A video studio for Claude Code. You type `/reel "brief"` and a team of agents — director, writer, motion, editor, art and QA — produces a vertical reel, using community skills for editing, motion and captions.

> **Status: early development.** The plugin skeleton is in place; the agents and the `/reel` flow are being built. See [`PLAN.md`](./PLAN.md) for the phases, scope and estimates ([timeline](./docs/roadmap.svg)).

## How it will work

1. `/reel "brief"` creates `productions/<slug>/` and saves the brief.
2. The **director** writes a plan and launches the agents in waves: whatever has no pending dependencies runs in parallel.
3. The **writer**, **motion**, **editor** and **art** agents produce their pieces, using the skills listed in [`skills.json`](./skills.json).
4. You review a lightweight preview before the final render.
5. **QA** checks the render with `ffprobe` and by looking at sampled frames before anything is called done.

## Repo layout

```
.claude-plugin/   plugin manifest and marketplace
agents/           the six agents (phase 2)
skills/           /reel, /setup, /team and own skills (phases 3-5)
skills.json       catalog of community skills and tools, by tier
docs/             timeline, add-ons survey and the role notes salvaged from v1
PLAN.md           plan, phases and estimates
```

## Install (once the agents ship)

```
/plugin marketplace add blokxz/cutroom
/plugin install cutroom@blokxz
```

## Requirements

- [Claude Code](https://code.claude.com)
- `ffmpeg` / `ffprobe`
- Node.js 18+ for Remotion; other add-ons list their own requirements in `skills.json`

## Background

cutroom replaces an earlier TypeScript CLI that managed the same team as a JSON tree. That code stays in [blokxz/ai-team-tree](https://github.com/blokxz/ai-team-tree); what was worth keeping is in [`docs/v1-salvage.md`](./docs/v1-salvage.md).

## License

MIT — see [`LICENSE`](./LICENSE).
