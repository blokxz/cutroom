# cutroom — working notes for Claude Code

This repo is **cutroom**: a **Claude Code plugin** where `/reel "brief"` hands the work to a team of six agents (director, writer, motion, editor, art, qa) that produce vertical reels. It replaces an earlier TypeScript CLI that lives in a separate repo (blokxz/ai-team-tree); none of that code is here.

Read `PLAN.md` first. It is the source of truth for phases, scope and "done when" criteria.

## Hard rules

1. **Never add Claude as a co-author or contributor.** No `Co-Authored-By` trailers, no "Generated with Claude Code" lines, no session links, and no Claude/Anthropic attribution of any kind in commit messages, PR titles or descriptions, tags, release notes, `CHANGELOG.md`, `CONTRIBUTORS`, `package.json` or file headers. Commits are authored only by the repo owner (`blokxz`). `.claude/settings.json` disables Claude Code's automatic attribution; never re-enable it or add attribution by hand.
2. **Reply to the user in Spanish (Rioplatense, voseo).** The user writes in English; answer in Spanish anyway, every time.
3. **Everything in the repo is in English.** Code, identifiers, comments, CLI output, error messages, templates, tests, docs, examples, file and folder names, commit messages and PR text. No Spanish (or any other language) anywhere in the repo, even though the conversation with the user is in Spanish.

## Where things stand

- Phases 0 and 1 are done: plan, v1 salvage, plugin skeleton (`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`) and the add-on catalog (`skills.json`).
- The v1 CLI was removed; the repo contains only the v2 base. What was worth keeping from v1 is in `docs/v1-salvage.md`.
- **Next: phase 2 — the six agents** in `agents/`. Base them on `docs/v1-salvage.md` (role prompts, rules, "before saying done" steps, wave logic).
- Then phase 4 (`/reel` flow), 3 (catalog + `/setup`), 5 (`/team`) and what's left of 6 (final README, release).

## Conventions

- Production state lives in `productions/<slug>/` (`brief.md`, `plan.md`, `status.md`, `script.md`, `assets/`, `renders/`). `assets/` is read-only.
- Brand profiles live in `brands/<name>.json`.
- Agents and skills use kebab-case names. Never start a name with `claude-` or use "claude"/"anthropic" as a word in it; the plugin validator rejects or flags those.
- No `bin/` directory at the plugin root: it blocks installing the plugin from claude.ai.
- No `CLAUDE.md` at the repo root: at a plugin root it isn't loaded and the validator warns. Keep these notes in `.claude/CLAUDE.md`.
- Third-party skills and tools are added to `skills.json` with a pinned commit and only move from `candidate` to `active` after being tested with the sample brief.
- `productions/` is git-ignored: footage, renders and drafts never go into the repo.
- No secrets in the repo: API keys go in environment variables or a git-ignored `.env`.

## Checks

```bash
claude plugin validate --strict .                         # marketplace
claude plugin validate --strict .claude-plugin/plugin.json # plugin manifest
claude --plugin-dir .                                      # load the plugin locally to try it
```

Both validations must pass before any commit that touches `.claude-plugin/`, `agents/` or `skills/`.

## Phase 2 checklist

- [ ] `agents/director.md`, `writer.md`, `motion.md`, `editor.md`, `art.md`, `qa.md`
- [ ] Each one: `name`, `description` (when to use it), `tools`, `model` in the frontmatter; a body with role, inputs, outputs (which `productions/<slug>/` files it reads and writes), the non-negotiable rules and its "before saying done" check
- [ ] `qa` has no `Write` or `Edit`
- [ ] Check the current Claude Code docs for whether subagent frontmatter can preload skills; if not, name the skills in the body
- [ ] Validation passes and `/agents` lists all six
