# cutroom — working notes for Claude Code

This repo is **cutroom**: a Claude Code plugin plus the working kit it drives. `/cutroom:video "<what the video is for>"` takes a brief through concepts, beat sheet, a Remotion build, render and an automatic quality check, one gated stage at a time.

## Hard rules

1. **Never add Claude as a co-author or contributor.** No `Co-Authored-By` trailers, no "Generated with Claude Code" lines, no session links, and no Claude/Anthropic attribution of any kind in commit messages, PR titles or descriptions, tags, release notes, `CHANGELOG.md`, `CONTRIBUTORS`, `package.json` or file headers. Commits are authored only by the repo owner (`blokxz`). `.claude/settings.json` disables Claude Code's automatic attribution; never re-enable it or add attribution by hand.
2. **Reply to the user in Spanish (Rioplatense, voseo).** The user writes in English; answer in Spanish anyway, every time.
3. **Everything in the repo is in English.** Code, identifiers, comments, CLI output, error messages, templates, tests, docs, examples, file and folder names, commit messages and PR text.
4. **Never use the `onetake` skill or its scripts** to make videos or animations, and never copy its code. cutroom's criteria and checks are its own implementation.

## Layout

```
.claude-plugin/    plugin.json + marketplace.json (marketplace "blokxz")
commands/video.md  /cutroom:video — the orchestrator: drives tools/pipeline.py stage by stage
commands/reel.md   /cutroom:reel — summary first, families + seeded variations in one batch, then the same pipeline
skills/            video-direction, reel-families — each spec.md (single source of truth) → SKILL.md (router), guidelines.md, references/
schemas/           client.json, brief.json, music LIBRARY.json
clients/<slug>/    client.json, assets/ (logo, photos, fonts, music), briefs/, references/
remotion-base/     Remotion project: src/{lib,moves,components,examples,clients}, scripts/{render,config,sync-clients}.mjs
tools/             pipeline.py, brief.py, material.py (+ media/), verify.py (+ quality/ core, claims, platforms/), deliver.py,
                   brand.py, sfx.py, master.py, models.py, setup.py, doctor.py, check_plugin.py, check_skill.py, variation.py, reel_summary.py
deliveries/<id>/   publish-ready packages built by tools/deliver.py (git-ignored)
```

## Conventions

- The brief is the single source of on-screen text; `client.json` of contact and brand. Compositions read the brief through `useCopy()` in `src/lib/brief.ts`, and contact/brand through the generated `src/clients/<slug>/brand.ts` — re-run `python3 tools/brief.py client ts <slug>` after every `client.json` edit.
- Fonts and music live only in `clients/<slug>/assets/`; `sync-clients.mjs` copies them into `remotion-base/public/clients/<slug>/` (git-ignored).
- Platform limits live in `tools/quality/platforms/specs/<platform>.json` with a `reviewed` date; re-check the official pages when the verifier warns they are stale.
- Skill rules live in `skills/<name>/spec.md` with IDs (C-/G-/R-NN). Change the spec first, then the derived files; `tools/check_skill.py` (run by `check_plugin.py`) fails on an uncited or undefined ID, an unrouted reference, or a router over budget.
- New platform = a module in `tools/quality/platforms/` + its specs JSON + tests (see `tools/quality/README.md`).
- No `bin/` directory at the plugin root (it blocks installing from claude.ai) and no `CLAUDE.md` at the root.
- Machine-specific paths go in a git-ignored `.env` (see `.env.example`), never in code.
- Renders (`remotion-base/out/`), delivery packages (`deliveries/`) and downloaded models (`tools/models/`) never go into the repo.
- A client's original material is read-only: list its folders (absolute paths) in `source_folders` of the git-ignored `clients/<slug>/client.local.json`; tools must call `media.guard.ensure_writable()` before writing.

## Checks

```bash
claude plugin validate --strict .                          # marketplace
claude plugin validate --strict .claude-plugin/plugin.json # plugin manifest
python3 -m pytest tools/tests -q                           # verifier
cd remotion-base && npx tsc --noEmit && npm test           # types + unit tests
cd remotion-base && node scripts/render.mjs --brief ../clients/sample/briefs/sample-post.json   # real render + verify
```

All must pass before a commit; CI (`.github/workflows/ci.yml`) runs the same on every push.
