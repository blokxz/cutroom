# Contributing

## Getting started

```bash
git clone https://github.com/blokxz/cutroom.git
cd cutroom
cd remotion-base && npm ci && cd ..
pip install -r tools/requirements.txt
claude --plugin-dir .    # load the plugin locally to try it
```

## Before opening a PR

- [ ] `claude plugin validate --strict .` and `claude plugin validate --strict .claude-plugin/plugin.json` pass.
- [ ] `python3 -m pytest tools/tests -q` passes.
- [ ] `cd remotion-base && npx tsc --noEmit && npm test` passes.
- [ ] If you touched a composition, the move library or the verifier: render the examples (`node scripts/render.mjs --brief ../clients/sample/briefs/<id>.json`) and check there is no FAIL.
- [ ] If you changed a platform's numbers: update its `tools/quality/platforms/specs/<platform>.json`, including `reviewed` and `sources`.
- [ ] If you changed a skill: edit its `spec.md` first (new rule ⇒ new ID), then `SKILL.md` / `guidelines.md` / `references/`, and run `python3 tools/check_skill.py`.
- [ ] If the visible behavior changed, update `README.md` and `CHANGELOG.md`.

## Rules

- **Everything in English**: files, names, code, CLI output, docs, commit messages and PRs. Client copy in `clients/*/` is the only exception, plus the default copy of the client examples in `remotion-base/src/examples/<client>/`, which mirrors their briefs (a test checks it).
- **Kebab-case names** for skills and commands. Don't start a name with `claude-` and don't use "claude" or "anthropic" as a word in it.
- **No `bin/` folder** at the plugin root (it blocks installing from claude.ai).
- **No AI attribution** in commits or PRs (no `Co-Authored-By` trailers or "Generated with" lines).
- **No renders in the repo**: `remotion-base/out/` is ignored on purpose.
- **Only licensed material**: fonts with their licence, music indexed in the client's `LIBRARY.json` with a licence.

## Reporting a bug

Include: Claude Code version, operating system, the exact command or brief, what you expected and what you got (the verifier output if relevant).

## License

By contributing you agree that your contribution is published under the repo's MIT license.
