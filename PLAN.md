# cutroom — roadmap

The 0.1.0 plan (a six-agent team behind `/reel`) was replaced in 0.2.0 by a single gated pipeline driven by `/cutroom:video`, a Remotion template and a measuring verifier. The reasoning: one director with strict gates and real measurements produced better videos than a team of agents passing files around, and it is far simpler to use.

## Improvement phases (0.4 →)

The current plan comes from a module-by-module comparison with onetake: see [docs/benchmark.md](docs/benchmark.md) for the verdicts, the four phases and what is left in each.

## Done in 0.2.0

- Brief-driven compositions; the brief is the single source of on-screen text.
- Gated pipeline (`tools/pipeline.py`): a stale or failing render can't pass review or delivery.
- Render with one browser per run, parallel frames and a cache; drafts are mastered like finals.
- Verifier: about twice as fast; platform modules for Instagram, TikTok and YouTube Shorts; dated specs with sources.
- Plugin packaging, environment config (`.env`), CI with a real render of every example.

## Next

| # | Item | Done when |
|---|------|-----------|
| 1 | Try it on a real PC (Windows and Linux) with a new client | a video goes brief → delivered without manual fixes |
| 2 | Real music library for the example client | `LIBRARY.json` lists licensed tracks; the test bed is no longer used |
| 3 | Re-check the TikTok and Shorts specs on their official pages | the specs JSON cite only official sources where those exist |
| 4 | Images and carousels through the pipeline (stills, not only video) | a `feed_image` brief renders and verifies through `/cutroom:video` |
| 5 | Faster optical flow | the verifier runs under 3 s per 10 s video without changing verdicts |
| 6 | More examples with other brands and concepts | at least two real-world style clients beside the fictional sample in `clients/` |
