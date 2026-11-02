#!/usr/bin/env python3
"""cutroom variation engine — seeded beat sheets and invented concept variations from the family registry.

  variation.py list [--ready]                         families (skills/reel-families/references/families.json)
  variation.py sheet <family> --duration S [--seed N] a beat sheet that satisfies the rhythm rules
  variation.py invent [--seed N] [--n 3]              novel (carry_kind, boundary) pairings not in the registry
  variation.py check <beats.json> --duration S        validate any beat list against the rhythm rules

Everything is deterministic: same family, duration and seed give the same output. Output is JSON shaped like
brief.schema.json `beats` / `concepts`, so it can be pasted into a brief. The model still writes the concept
sentence and designs the piece; this tool only guarantees the structure is legal.
"""
import argparse
import json
import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "skills", "reel-families", "references", "families.json")

MIN_BEAT = 0.3      # s, shortest allowed beat
RATIO = 3.0         # longest / shortest
REST = 0.8          # s, shortest real rest
CTA_HOLD = 1.5      # s, final still hold


def load_registry(path=REGISTRY):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def family(reg, fid):
    for f in reg["families"]:
        if f["id"] == fid:
            return f
    raise SystemExit(f"unknown family '{fid}' (variation.py list)")


def _fmt(a, b):
    return f"{a:.1f}–{b:.1f}"


def sheet(fam, duration, seed=0):
    """Beat list for `fam` over `duration` seconds. Raises ValueError when the rules cannot be met."""
    rng = random.Random(f"{fam['id']}:{duration}:{seed}")
    cta = max(CTA_HOLD, round(duration * 0.18, 1))
    lo, hi = fam["beats"]
    room = duration - cta - REST
    n_active = max(2, min(hi - 2, int(room / 0.9)))  # active beats besides the rest and the CTA hold
    n_active = max(lo - 2, n_active) if room / max(lo - 2, 1) >= MIN_BEAT * 2 else n_active
    if room < n_active * MIN_BEAT * 2:
        raise ValueError(f"{duration}s is too short for family '{fam['id']}'")
    w = [math.exp(rng.uniform(0, math.log(6))) for _ in range(n_active)]
    scale = room / sum(w)
    d = [max(MIN_BEAT, x * scale) for x in w]
    for _ in range(40):  # repair: stretch the longest, squeeze the shortest until the ratio holds
        allb = d + [REST, cta]
        if max(allb) / min(allb) >= RATIO + 0.2:
            break
        i, j = d.index(min(d)), d.index(max(d))
        take = min(0.15 * d[i], d[i] - 0.25)
        if take <= 0:
            break
        d[i] -= take
        d[j] += take
    d = [round(x, 1) for x in d]
    d[d.index(max(d))] = round(d[d.index(max(d))] + (duration - cta - REST - sum(d)), 1)
    for _ in range(60):  # rounding can land exactly on the limit: repair on the rounded values
        if max(d + [REST, cta]) / min(d + [REST, cta]) >= RATIO + 0.05 or min(d) <= MIN_BEAT:
            break
        i, j = d.index(min(d)), d.index(max(d))
        d[i], d[j] = round(d[i] - 0.1, 1), round(d[j] + 0.1, 1)
    rest_at = rng.randint(1, max(1, len(d) - 1))
    durs = d[:rest_at] + [REST] + d[rest_at:] + [cta]
    kinds = ["move"] * rest_at + ["rest"] + ["move"] * (len(d) - rest_at) + ["hold"]
    beats, t = [], 0.0
    for i, (x, k) in enumerate(zip(durs, kinds)):
        a, b = round(t, 1), round(t + x, 1)
        last = i == len(durs) - 1
        name = {"rest": "rest", "hold": "CTA hold"}.get(k, "open" if i == 0 else f"{fam['id']} beat {i}")
        beats.append({"t": _fmt(a, b), "beat": name, "kind": k,
                      "moves": "" if k != "move" else f"{fam['boundary']} out of {fam['carry']}",
                      "holds": "everything" if last else ("almost everything" if k == "rest" else "ground"),
                      "carries": "" if last else fam["carry"]})
        t = b
    return beats


def check(beats, duration, tol=0.15):
    """Problems (list of strings) of a beat list; empty = legal. Accepts 't' as 'a–b' strings."""
    probs, spans = [], []
    for b in beats:
        a, z = (float(x) for x in b["t"].replace("-", "–").split("–"))
        spans.append((a, z, b))
    if not spans:
        return ["no beats"]
    if abs(spans[0][0]) > tol:
        probs.append("first beat does not start at 0")
    if abs(spans[-1][1] - duration) > tol:
        probs.append(f"last beat ends at {spans[-1][1]}, not {duration}")
    for (a, z, _), (a2, _, _) in zip(spans, spans[1:]):
        if abs(z - a2) > tol:
            probs.append(f"gap or overlap at {z}")
    durs = [z - a for a, z, _ in spans]
    if min(durs) < MIN_BEAT - 0.05:
        probs.append(f"beat shorter than {MIN_BEAT}s")
    if max(durs) / min(durs) < RATIO:
        probs.append(f"beats too even: longest/shortest = {max(durs) / min(durs):.1f} < {RATIO}")
    rests = [z - a for a, z, b in spans if b.get("kind") in ("rest", "hold") or "rest" in b["beat"].lower()]
    if not rests or max(rests) < REST - 0.05:
        probs.append(f"no real rest (>= {REST}s)")
    if durs[-1] < CTA_HOLD - 0.05:
        probs.append(f"CTA hold {durs[-1]:.1f}s < {CTA_HOLD}s")
    for a, z, b in spans[:-1]:
        if b.get("kind", "move") == "move" and not b.get("carries"):
            probs.append(f"beat at {a}s names no survivor (carries)")
    return probs


def invent(reg, seed=0, n=3):
    """Novel concept skeletons: carry kind of one family x boundary of another, absent from the registry."""
    rng = random.Random(f"invent:{seed}")
    have = {(f["carry_kind"], f["boundary"]) for f in reg["families"]}
    ready = [f for f in reg["families"] if f["status"] == "ready" and f["boundary"] != "none"]
    combos = sorted({(a["carry_kind"], b["boundary"]) for a in reg["families"] for b in ready} - have)
    rng.shuffle(combos)
    out = []
    for ck, bd in combos[:n]:
        a = rng.choice([f for f in reg["families"] if f["carry_kind"] == ck])
        b = rng.choice([f for f in ready if f["boundary"] == bd])
        out.append({"name": f"{a['name']} × {b['name']}", "carry_kind": ck, "boundary": bd,
                    "carry": a["carry"], "moves": b["moves"], "parents": [a["id"], b["id"]],
                    "idea": f"TODO one sentence: {a['carry']} survives every scene; each change is a {bd} out of it."})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--ready", action="store_true")
    s = sub.add_parser("sheet"); s.add_argument("family"); s.add_argument("--duration", type=float, required=True); s.add_argument("--seed", type=int, default=0)
    s = sub.add_parser("invent"); s.add_argument("--seed", type=int, default=0); s.add_argument("--n", type=int, default=3)
    s = sub.add_parser("check"); s.add_argument("beats"); s.add_argument("--duration", type=float, required=True)
    a = ap.parse_args(argv)
    reg = load_registry()
    if a.cmd == "list":
        for f in reg["families"]:
            if not a.ready or f["status"] == "ready":
                print(f"{f['id']:22} {f['status']:10} carry={f['carry_kind']:8} boundary={f['boundary']:8} moves={','.join(f['moves']) or '-'}")
    elif a.cmd == "sheet":
        try:
            print(json.dumps(sheet(family(reg, a.family), a.duration, a.seed), indent=1, ensure_ascii=False))
        except ValueError as e:
            print(f"ERROR {e}", file=sys.stderr)
            return 1
    elif a.cmd == "invent":
        print(json.dumps(invent(reg, a.seed, a.n), indent=1, ensure_ascii=False))
    else:
        with open(a.beats, encoding="utf-8") as f:
            data = json.load(f)
        probs = check(data.get("beats", data) if isinstance(data, dict) else data, a.duration)
        for p in probs:
            print("FAIL", p)
        print("beat sheet OK" if not probs else f"{len(probs)} problem(s)")
        return 1 if probs else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
