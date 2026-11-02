# Variation rules [C-04 F-03 F-04 F-05 C-03 L-03 G-04]

## Mutation operators (apply one per variation, name it in `decisions`)

| Operator | Change | Example |
|---|---|---|
| swap-boundary | keep carry, change how scenes open | Thread carried by a `window` instead of a `wipe` |
| swap-carry | keep boundary, change the survivor | iris out of a key instead of a disc |
| hybrid | carry kind of A × boundary of B (`invent`) | Calendar × Match cut |
| invert | reverse direction of the move | dive out instead of in; light runs night → day |
| rescale | same idea at another scale | whole region → one cup, or only the cup |
| re-time | new seed ⇒ new uneven beat lengths | `--seed 4` instead of `--seed 1` |

## Legality

| Check | Rule |
|---|---|
| Registry pair | `(carry_kind, boundary)` ∉ registry ⇒ novel (F-03) |
| Buildable | every move of the boundary parent is `ready`, else proposal only |
| Distinct set | 3 concepts, ≥ 2 carry kinds, ≥ 2 boundaries (F-04) |
| Rhythm | `variation.py check` OK (C-03) |
| Not a refill | new photos in an old piece is not a variation (G-04) |
| Promotion | register only after a shipped piece with 0 FAIL (F-05) |

## Batch (L-03)

`--seed 1…N` per chosen family; show all sheets in one message; the user picks once.
