# Worked run [C-01 C-03 C-06 L-02 L-03]

Request (turn 1): `/cutroom:reel "Reel for the cabins, 10 s, 3 variants"` (Spanish client copy stays Spanish).

```bash
python3 tools/reel_summary.py                                   # L-01: no P0; P1 items unrelated → noted
python3 tools/variation.py sheet window --duration 10 --seed 1
python3 tools/variation.py sheet key --duration 10 --seed 2
python3 tools/variation.py invent --seed 3 --n 1                # Calendar × Match cut
python3 tools/variation.py check beats.json --duration 10       # beat sheet OK
```

Shown together (turn 2): 3 concepts

| # | family | carry_kind / boundary | idea | carry |
|---|---|---|---|---|
| 0 | window | shape / window | One arch window changes shape as each place opens out of a point of the last photo. | outline + opening point |
| 1 | key | object / iris | A key turns and each turn unlocks the next place; ends on the open door. | key + rotation |
| 2 | calendar × match_cut | surface / match | Desk calendar pages tear off; each page ends on a shape the next place repeats. | calendar block |

Choice → `chosen_concept: 0`; `beats` from `sheet window --seed 1`; `decisions += ["families window,key,calendar×match_cut; seeds 1,2,3"]`.

Hand-off: `python3 tools/pipeline.py advance <brief>` … render, user approval (turn 3), `--final`, `deliver.py`. Delivery note lists targets met/open (Q-01, Q-02 met; Q-07, Q-08 open) and the summary delta.
