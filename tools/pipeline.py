#!/usr/bin/env python3
"""cutroom pipeline — one brief, one stage at a time, no skipped steps.

Stages (brief.status):  brief → material → concepts → building → review → approved → delivered

  pipeline.py status  <brief.json>               where the brief is, what blocks it, what to do next
  pipeline.py advance <brief.json> [--approved]  move to the next stage only if its gate passes
  pipeline.py render  <brief.json> [--final|--preview]  render + verify through remotion-base/scripts/render.mjs
                                                 (--preview: half-size quick look, not verified, never counts for a gate)

Gates (what advancing out of each stage requires):
  brief     → material   brief.py check passes (no ERROR) for stage "material"
  material  → concepts   the material is analysed and selected (or the piece is typography-only), 3 concepts written
  concepts  → building   a chosen concept and a beat sheet
  building  → review     a composition id and a current draft render whose verification passed (no FAIL)
  review    → approved   the user approved it (pass --approved only after they said so)
  approved  → delivered  a current, mastered --final render that passed, and a delivery package
                         (tools/deliver.py) without severe claims

The /video command drives this file; it can also be run by hand.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
REMOTION = os.path.join(ROOT, "remotion-base")
STAGES = ["brief", "material", "concepts", "building", "review", "approved", "delivered"]
DELIVERIES = os.environ.get("CUTROOM_DELIVERIES") or os.path.join(ROOT, "deliveries")

NEXT_STEP = {
    "brief": "Fill the brief from the user's prompt (skill step 1). Ask only the questions `brief.py check` lists; "
    "record anything you decide in `decisions`.",
    "material": "Analyse the client's photos/videos: `python3 tools/material.py analyze <client> <folder> [--videos]`, "
    "look at the contact sheet, pick by number with `python3 tools/material.py select <brief> 3,7,2` (ask the user "
    "when the choice matters). No material at all → a typography-only piece. Then write three concepts (skill step 2).",
    "concepts": "Show the three concepts to the user and let them choose (skill step 2). Set `chosen_concept`, "
    "then write the beat sheet into `beats` (skill step 3).",
    "building": "Build the composition in remotion-base/src (skill steps 4-6), register it in Root.tsx, put its id "
    "in `composition`, then run `pipeline.py render <brief>` until verification has no FAIL.",
    "review": "Show the draft video and stills to the user. Apply their changes and re-render. When they approve, "
    "run `pipeline.py advance <brief> --approved`.",
    "approved": "Run `pipeline.py render <brief> --final`, then write deliveries/<id>/caption.md following the "
    "client's voice_guide (short, medium and booking versions, hashtags, alt text) and run `python3 tools/deliver.py <brief>`.",
    "delivered": "Done. Send the files in deliveries/<id>/ (video, covers, WhatsApp version, caption, checklist) and "
    "go through CHECKLIST.md with the user.",
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _load_env():
    """Values from the repo's .env (same file scripts/config.mjs reads); the process environment wins."""
    env = os.path.join(ROOT, ".env")
    if os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))
    os.environ.setdefault("PYTHONUTF8", "1")  # child tools print UTF-8 on Windows consoles and pipes


def py():
    return os.environ.get("CUTROOM_PYTHON") or sys.executable


def brief_check(path, as_stage=None):
    """Run brief.py check, optionally pretending the brief is at another stage. Returns (ok, output)."""
    target = path
    if as_stage:
        b = load(path)
        b["status"] = as_stage
        target = path + ".gate.json"
        save(target, b)
    try:
        r = subprocess.run([py(), os.path.join(TOOLS, "brief.py"), "check", target], capture_output=True, text=True, encoding="utf-8", errors="replace")
    finally:
        if as_stage and os.path.exists(target):
            os.remove(target)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def current_key(path, final):
    """The render cache key for the brief's inputs as they are now (computed by render.mjs itself)."""
    cmd = ["node", "scripts/render.mjs", "--brief", os.path.abspath(path), "--print-key"] + (["--final"] if final else [])
    r = subprocess.run(cmd, cwd=REMOTION, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip().splitlines()[-1] if r.returncode == 0 and r.stdout.strip() else None


def last_render(path, b, final):
    """(entry, problem): the cache entry render.mjs wrote for this brief's draft or final video,
    or a problem string when there is none, it failed, or it no longer matches the current inputs."""
    label = "final" if final else "draft"
    cmd = f"pipeline.py render <brief>{' --final' if final else ''}"
    cache = os.path.join(REMOTION, "out", b["id"], ".render-cache.json")
    name = f"{b.get('composition')}{'' if final else '-draft'}.mp4"
    entry = None
    if os.path.exists(cache) and b.get("composition"):
        for video, e in load(cache).items():
            if os.path.basename(video) == name and os.path.exists(video):
                entry = e
    if not entry:
        return None, f"no {label} render yet — run: {cmd}"
    if entry.get("verify") != "pass":
        return entry, f"the last {label} render did not pass verification — fix the FAIL lines and re-render"
    if final and entry.get("mastered") is False:
        return entry, "the final render's audio mastering failed — fix it and re-render with --force"
    key = current_key(path, final)
    if key is None:
        return entry, "could not compute the render key (is Node installed and remotion-base set up?)"
    if entry.get("key") != key:
        return entry, f"the brief, composition or assets changed since the last {label} render — run: {cmd}"
    return entry, None


def delivery_problems(b):
    """The package tools/deliver.py builds must exist and carry no severe claim."""
    d = os.path.join(DELIVERIES, b["id"])
    sheet = os.path.join(d, "sheet.json")
    if not os.path.exists(sheet):
        return [f"no delivery package yet — write {os.path.relpath(d, ROOT)}/caption.md and run: tools/deliver.py <brief>"]
    try:
        data = load(sheet)
    except (OSError, ValueError):
        return ["the delivery sheet.json is unreadable — re-run tools/deliver.py <brief>"]
    findings = data.get("claims", [])
    severe = [f for f in findings if isinstance(f, dict) and f.get("severity") == "severe"]
    if severe:
        return [f"{len(severe)} severe claim(s) in the caption or on-screen copy — fix them and re-run tools/deliver.py"]
    if not os.path.exists(os.path.join(d, "caption.md")):
        return ["the delivery package has no caption.md"]
    if data.get("ready_to_publish") is not True:
        errs = data.get("errors") or ["the package is not ready to publish"]
        return [f"delivery package: {e}" for e in errs]
    # the package must match what exists now: the current final render and the current caption
    files = data.get("files") or {}
    stale = "the {} changed after the package was built — re-run tools/deliver.py <brief>"
    video = os.path.join(REMOTION, "out", b["id"], f"{b.get('composition')}.mp4")
    packed = files.get(os.path.basename(video), {}).get("sha256")
    if not packed or not os.path.exists(video) or packed != _sha256(video):
        return [stale.format("final render")]
    cap_src = os.path.join(ROOT, (data.get("caption") or {}).get("path") or os.path.join("deliveries", b["id"], "caption.md"))
    packed_cap = files.get("caption.md", {}).get("sha256")
    if not packed_cap or not os.path.exists(cap_src) or packed_cap != _sha256(cap_src):
        return [stale.format("caption")]
    return []


def _sha256(path):
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gate(path, b, approved=False):
    """Problems blocking the move out of the current stage (empty list = may advance)."""
    stage = b.get("status", "brief")
    problems = []
    if stage == "delivered":
        return ["already delivered"]
    nxt = STAGES[STAGES.index(stage) + 1]
    if stage in ("brief", "material", "concepts", "building"):
        ok, out = brief_check(path, as_stage=nxt)
        if not ok:
            errors = [line.strip() for line in out.splitlines() if "ERROR" in line]
            # a crash (traceback, bad types) has no ERROR lines but must still block
            problems += errors or [f"brief.py check failed: {(out.splitlines() or ['no output'])[-1]}"]
    if stage == "building":
        _, problem = last_render(path, b, final=False)
        if problem:
            problems.append(problem)
    if stage == "review" and not approved:
        problems.append("waiting for the user's approval — advance with --approved once they approve")
    if stage == "approved":
        _, problem = last_render(path, b, final=True)
        if problem:
            problems.append(problem)
        problems += delivery_problems(b)
    return problems


def stage_of(b):
    stage = b.get("status", "brief")
    if stage not in STAGES:
        sys.exit(f"unknown status {stage!r} — expected one of: {', '.join(STAGES)}")
    return stage


def cmd_status(a):
    b = load(a.brief)
    stage = stage_of(b)
    ok, out = brief_check(a.brief)
    print(out)
    print(f"\nstage: {stage}  ({STAGES.index(stage) + 1}/{len(STAGES)})")
    blockers = gate(a.brief, b)
    if stage != "delivered":
        print("to advance:" if blockers else "gate: open — run `pipeline.py advance` to move on")
        for p in blockers:
            print(f"  - {p}")
    print(f"\nnext: {NEXT_STEP[stage]}")
    return 0 if ok else 1


def cmd_advance(a):
    b = load(a.brief)
    stage = stage_of(b)
    blockers = gate(a.brief, b, approved=a.approved)
    if blockers:
        print(f"cannot leave '{stage}':")
        for p in blockers:
            print(f"  - {p}")
        return 1
    b["status"] = STAGES[STAGES.index(stage) + 1]
    save(a.brief, b)
    print(f"{stage} → {b['status']}\nnext: {NEXT_STEP[b['status']]}")
    return 0


def cmd_render(a):
    b = load(a.brief)
    if not b.get("composition"):
        print("the brief has no composition id yet (stage 'building')")
        return 1
    if a.final and b.get("status") not in ("approved", "delivered"):
        print("final renders come after the user approves the draft (stage 'approved')")
        return 1
    cmd = (["node", "scripts/render.mjs", "--brief", os.path.abspath(a.brief)] + (["--final"] if a.final else [])
           + (["--preview"] if a.preview and not a.final else []) + (["--force"] if a.force else []))
    return subprocess.run(cmd, cwd=REMOTION).returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("brief")
    s.set_defaults(fn=cmd_status)
    v = sub.add_parser("advance")
    v.add_argument("brief")
    v.add_argument("--approved", action="store_true", help="the user approved the draft")
    v.set_defaults(fn=cmd_advance)
    r = sub.add_parser("render")
    r.add_argument("brief")
    r.add_argument("--final", action="store_true")
    r.add_argument("--preview", action="store_true", help="half-size quick look; not verified, never counts for a gate")
    r.add_argument("--force", action="store_true")
    r.set_defaults(fn=cmd_render)
    a = ap.parse_args()
    _load_env()
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
