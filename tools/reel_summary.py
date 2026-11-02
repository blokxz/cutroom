#!/usr/bin/env python3
"""cutroom operational summary — gather data, synthesize one dense report, derive prioritized actions.

  reel_summary.py [--json] [--client SLUG]

Read-only. Sources: clients/*/briefs/*.json (stage, platform, concepts, decisions), remotion-base/out/<id>/
.render-cache.json (verifier verdicts), tools/quality/platforms/specs/*.json (staleness), the family registry
(families that still need a move) and docs/benchmark.md (modules where cutroom is 'behind').
Each action carries a priority (P0 blocks shipping, P1 raises quality, P2 hygiene) and the command or file to
touch, so the caller can execute the list straight away and re-run the summary to confirm it shrank.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGES = ["brief", "material", "concepts", "building", "review", "approved", "delivered"]
STALE_DAYS = 180
PARKED = {8}  # benchmark modules parked by decision (docs/benchmark.md, phase 3: voice and subtitles)


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def briefs(root, client=None):
    out = []
    for p in sorted(glob.glob(os.path.join(root, "clients", client or "*", "briefs", "*.json"))):
        b = _load(p)
        if isinstance(b, dict) and "id" in b:
            out.append((os.path.relpath(p, root), b))
    return out


def verdict(root, b):
    """'pass' | 'fail' | None from the render cache of the brief's composition."""
    cache = _load(os.path.join(root, "remotion-base", "out", b["id"], ".render-cache.json")) or {}
    vals = [e.get("verify") for e in cache.values() if isinstance(e, dict)]
    return "fail" if "fail" in vals else ("pass" if "pass" in vals else None)


def stale_specs(root, today):
    out = []
    for p in sorted(glob.glob(os.path.join(root, "tools", "quality", "platforms", "specs", "*.json"))):
        d = _load(p) or {}
        try:
            age = (today - datetime.date.fromisoformat(d.get("reviewed", ""))).days
        except ValueError:
            age = 10 ** 6
        if age > STALE_DAYS:
            out.append((os.path.basename(p)[:-5], age))
    return out


def behind_modules(root):
    """Rows of docs/benchmark.md whose verdict is 'behind' → (number, module)."""
    try:
        text = open(os.path.join(root, "docs", "benchmark.md"), encoding="utf-8").read()
    except OSError:
        return []
    rows = re.findall(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|[^|]*\|[^|]*\|\s*([^|]+?)\s*\|\s*$", text, re.M)
    return [(int(n), m) for n, m, v in rows if "behind" in v and int(n) not in PARKED]


def gather(root=ROOT, client=None, today=None):
    today = today or datetime.date.today()
    bs = briefs(root, client)
    reg = _load(os.path.join(root, "skills", "reel-families", "references", "families.json")) or {"families": []}
    d = {
        "briefs": len(bs),
        "by_stage": dict(Counter(b.get("status", "brief") for _, b in bs)),
        "by_platform": dict(Counter(b.get("platform", "?") for _, b in bs)),
        "stuck": [], "failing": [], "undecided_warns": [],
        "families_total": len(reg["families"]),
        "families_ready": sum(f.get("status") == "ready" for f in reg["families"]),
        "families_missing_move": [f["id"] for f in reg["families"] if f.get("status") != "ready"],
        "stale_specs": stale_specs(root, today),
        "behind": behind_modules(root),
        "concepts_used": dict(Counter(c.get("name", "?") for _, b in bs for c in b.get("concepts", [])[:3])),
    }
    for rel, b in bs:
        st = b.get("status", "brief")
        v = verdict(root, b)
        if v == "fail":
            d["failing"].append(b["id"])
        if st != "delivered" and STAGES.index(st) >= STAGES.index("building") and not b.get("composition"):
            d["stuck"].append(b["id"])
        if st == "delivered" and not b.get("decisions") and v is None:
            d["undecided_warns"].append(b["id"])
    return d


def actions(d):
    a = []
    for i in d["failing"]:
        a.append(("P0", f"brief '{i}' has a failing render", f"python3 tools/pipeline.py render clients/*/briefs/{i}.json  # fix every FAIL"))
    for i in d["stuck"]:
        a.append(("P0", f"brief '{i}' is past 'concepts' with no composition", f"python3 tools/pipeline.py status clients/*/briefs/{i}.json"))
    for name, age in d["stale_specs"]:
        a.append(("P0", f"platform specs '{name}' reviewed {age} days ago", f"re-check sources in tools/quality/platforms/specs/{name}.json, update 'reviewed'"))
    for fid in d["families_missing_move"]:
        a.append(("P1", f"family '{fid}' has no buildable move", f"design a move in remotion-base/src/moves + unit test, then set status 'ready' in families.json"))
    for n, m in d["behind"]:
        a.append(("P1", f"benchmark module {n} '{m}' is behind", "docs/benchmark.md — see the phase that owns it"))
    used = d["concepts_used"]
    if used and max(used.values()) > 1:
        top = max(used, key=used.get)
        a.append(("P2", f"concept '{top}' reused {used[top]}x — rotate families", "python3 tools/variation.py invent --seed N"))
    return sorted(a, key=lambda x: x[0])


def render(d, acts):
    lines = ["# cutroom summary", "",
             f"briefs {d['briefs']} · stages {d['by_stage'] or '-'} · platforms {d['by_platform'] or '-'}",
             f"families {d['families_ready']}/{d['families_total']} ready · failing {len(d['failing'])} · stuck {len(d['stuck'])} · "
             f"stale specs {len(d['stale_specs'])} · benchmark gaps {len(d['behind'])}", "", "## actions"]
    lines += [f"- {p} {what} → `{cmd}`" for p, what, cmd in acts] or ["- none"]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--client")
    a = ap.parse_args(argv)
    d = gather(client=a.client)
    acts = actions(d)
    if a.json:
        print(json.dumps({"data": d, "actions": [{"priority": p, "what": w, "do": c} for p, w, c in acts]}, indent=1, ensure_ascii=False))
    else:
        print(render(d, acts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
