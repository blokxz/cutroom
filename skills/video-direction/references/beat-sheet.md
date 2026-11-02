# Beat sheet format [R-03 R-04 R-05 R-06 R-07 R-15]

Write before code. Mirror it in the composition header comment and in `brief.beats` (`[{t, beat}]`).

| t (s) | beat | what moves | what holds still | what carries into the next beat |
|---|---|---|---|---|

## Constraints

| Check | Pass condition | Rule |
|---|---|---|
| Uneven durations | longest ≥ 3–4× shortest | R-03 |
| Real rest | ≥ 1 beat ≥ 0.8 s near-still (CTA hold counts) | R-04 |
| End hold | final CTA still + readable ≥ 1.5 s | R-05 |
| Survivor | every boundary names an element that moves/scales into the next scene | R-06 |
| One story | one idea developed, no feature catalogue | R-07 |
| Ground | generous empty space; ≤ 1 full-bleed hero moment | R-07 |

## Beat kinds (`<Beat kind>`, `.track.json` `{ f, name, kind? }`)

| kind | Meaning | Continuity check |
|---|---|---|
| `move` | boundary must carry an element | counted |
| `rest` / `hold` | expected still | exempt |
| `cut` | deliberate hard cut (bursts, end card) | exempt |
| *(none)* | name decides: "cut" → cut; "rest"/"hold" → rest; else move | — |
