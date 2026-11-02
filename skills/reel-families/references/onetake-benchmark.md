# Quality benchmark [Q-03 Q-04 Q-05 Q-06 Q-07 Q-08 G-02 G-05]

Source: `docs/benchmark.md` (cutroom's own review of onetake's published criteria, reviewed 2026-10-26). onetake is not run and not copied (G-02). Targets are criteria, not parity claims (G-05).

| Q | Criterion | cutroom today | Where closed |
|---|---|---|---|
| Q-03 | Curves by intent; t80 spread | verifier curves check; `EASE.snap/glide`, springs | build |
| Q-04 | Operated camera (key ahead, settle, drift, still on CTA) | `Camera` + `drift`; no chase helper, shake or depth | build; helper = phase 2 |
| Q-05 | Motion blur on fast travel | `MotionBlur` (camera engine, canvas opt-in); final 12 samples | build |
| Q-06 | One room of sound, ducked, −16 LUFS | `sfx.py`, `Music duckAt`, `master.py`; events placed by hand | build; event-driven = phase 2 |
| Q-07 | Move variety | families `ready` count in `reel_summary.py` | phase 2 |
| Q-08 | Proof: cases per piece | none yet | phase 4 |

Parked by decision: voice, subtitles, second language (benchmark phase 3).

Statement template for delivery: "Targets met: Q-01…; open: Q-04, Q-06, Q-07, Q-08." Never "onetake level".
