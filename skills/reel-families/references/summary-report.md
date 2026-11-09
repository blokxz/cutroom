# Summary report [C-05 L-01 L-04]

`python3 tools/reel_summary.py [--json] [--client SLUG]` — read-only.

## Sources → fields

| Source | Field |
|---|---|
| `clients/*/briefs/*.json` | `briefs`, `by_stage`, `by_platform`, `concepts_used`, `stuck` (past `concepts`, no composition) |
| `remotion-base/out/<id>/.render-cache.json` | `failing` (any entry `verify: fail`) |
| `tools/quality/platforms/specs/*.json` | `stale_specs` (`reviewed` > 180 days) |
| `families.json` | `families_ready/total`, `families_missing_move` |
| `docs/benchmark.md` | `behind` (rows with verdict *behind*; parked modules skipped) |

## Actions

| Priority | Meaning | Examples |
|---|---|---|
| P0 | blocks shipping | failing render, stuck brief, stale specs |
| P1 | raises quality | family without a move, benchmark gap |
| P2 | hygiene | a concept reused across briefs |

Each action = `{priority, what, do}`; `do` is the command or file to touch. Loop: execute → re-run → list shrinks (L-01). Record seeds and skipped actions in `decisions` (L-04).

## Sample

```
# cutroom summary
briefs 1 · stages {'delivered': 1} · platforms {'instagram': 1}
families 26/30 ready · failing 0 · stuck 0 · stale specs 0 · benchmark gaps 4
## actions
- P1 family 'object_wipe' has no buildable move → `design a move in remotion-base/src/moves + unit test, …`
```
