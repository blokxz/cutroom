# Contributing

## Getting started

```bash
git clone https://github.com/blokxz/cutroom.git
cd cutroom
claude --plugin-dir .    # load the plugin locally to try it
```

## Before opening a PR

- [ ] `claude plugin validate --strict .` passes (marketplace).
- [ ] `claude plugin validate --strict .claude-plugin/plugin.json` passes (plugin manifest).
- [ ] If you added a skill or tool to `skills.json`, it has a pinned commit, the agents that use it and its requirements, and it was tested with the sample brief before being marked `active`.
- [ ] If the visible behavior changed, update `README.md` and `CHANGELOG.md`.

## Rules

- **Everything in English**: files, names, agents, skills, docs, commit messages and PRs.
- **Kebab-case names** for agents and skills. Don't start a name with `claude-` and don't use "claude" or "anthropic" as a word in it.
- **No `bin/` folder** at the plugin root (it blocks installing from claude.ai).
- **No AI attribution** in commits or PRs (no `Co-Authored-By` trailers or "Generated with" lines).
- **No production material in the repo**: `productions/` is ignored on purpose.

## Reporting a bug

Include: Claude Code version, operating system, the exact command or brief, what you expected and what you got.

## License

By contributing you agree that your contribution is published under the repo's MIT license.
