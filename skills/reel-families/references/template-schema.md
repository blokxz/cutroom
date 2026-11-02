# Template schema [C-02 C-03 C-04 C-06 G-08]

## Family record (`families.json` → `families[]`)

| Field | Type | Rule |
|---|---|---|
| `id` | snake_case string | unique |
| `name` | string | display |
| `kind` | `photo` \| `generic` | material it suits |
| `carry_kind` | enum | see taxonomy |
| `boundary` | enum | see taxonomy |
| `carry` | string | the survivor named in every beat |
| `moves` | string[] | exports found in `remotion-base/src/moves` (test-enforced) |
| `needs` | string[] | external needs (e.g. `layer masks`); non-empty ⇒ not ready |
| `beats` | [min, max] | beat count incl. rest and CTA hold |
| `status` | `ready` \| `needs-move` | `ready` iff `moves` ≠ ∅ and `needs` = ∅ |

## Beat sheet (`variation.py sheet`) → brief `beats`

```json
{"t": "1.9–4.9", "beat": "window beat 1", "kind": "move",
 "moves": "window out of window outline + opening point", "holds": "ground", "carries": "window outline + opening point"}
```

| Field | Rule |
|---|---|
| `t` | `a–b` seconds, 0.1 resolution, contiguous from 0.0 to `duration_s` |
| `kind` | `move` · `rest` (≥ 0.8 s) · `hold` (last, ≥ 1.5 s, empty `carries`) |
| `carries` | required on every `move`/`rest`; the survivor into the next beat |
| determinism | `(family, duration, seed)` ⇒ identical output (G-08) |

## Invented concept (`variation.py invent`)

```json
{"name": "Calendar × Match cut", "carry_kind": "surface", "boundary": "match", "carry": "calendar block",
 "moves": ["Morph"], "parents": ["calendar", "match_cut"], "idea": "TODO one sentence: …"}
```

Maps to brief `concepts[]` as `{name, idea, carry}` after the model rewrites `idea` (C-06).
