#!/usr/bin/env python3
"""Diagnose a cutroom install: versions, paths, configuration and a real test render.

    python tools/doctor.py              # full check, including a one-frame render
    python tools/doctor.py --no-render  # skip the render

The output is plain text meant to be pasted into a chat or an issue when something fails.
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTION = os.path.join(ROOT, "remotion-base")
sys.path.insert(0, os.path.join(ROOT, "tools"))


def out(cmd):
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    try:
        r = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        return (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else ""
    except (OSError, subprocess.TimeoutExpired):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-render", action="store_true")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    problems = []
    print("cutroom doctor")
    print(f"  system      {platform.system()} {platform.release()} ({platform.machine()}), {os.cpu_count()} CPUs")
    print(f"  python      {platform.python_version()} ({sys.executable})")
    node = out(["node", "--version"])
    print(f"  node        {node or 'NOT FOUND'}")
    if not node:
        problems.append("Node.js not found — run python tools/setup.py")
    try:
        from quality.bins import ffmpeg, ffprobe
        ff, fp = ffmpeg(), ffprobe()
    except Exception:  # noqa: BLE001
        ff, fp = "ffmpeg", "ffprobe"
    for name, binary in (("ffmpeg", ff), ("ffprobe", fp)):
        v = out([binary, "-version"])
        print(f"  {name:<11} {v or 'NOT FOUND'}")
        if not v:
            problems.append(f"{name} not found — run python tools/setup.py")
    mods = []
    for m in ("cv2", "numpy", "PIL", "jsonschema"):
        try:
            __import__(m)
            mods.append(f"{m} ok")
        except ImportError:
            mods.append(f"{m} MISSING")
            problems.append(f"Python module {m} missing — pip install -r tools/requirements.txt")
    print(f"  modules     {', '.join(mods)}")
    nm = os.path.isdir(os.path.join(REMOTION, "node_modules", "remotion"))
    print(f"  remotion    {'installed' if nm else 'NOT INSTALLED (cd remotion-base && npm ci)'}")
    if not nm:
        problems.append("Remotion dependencies missing — run python tools/setup.py")
    print(f"  .env        {'present' if os.path.exists(os.path.join(ROOT, '.env')) else 'absent (defaults)'}")
    model = os.path.exists(os.path.join(ROOT, "tools", "models", "face_detection_yunet_2023mar.onnx"))
    print(f"  face model  {'installed' if model else 'absent (optional: python tools/models.py fetch)'}")

    if not a.no_render and nm and node:
        print("\nrendering one test frame (first run downloads Remotion's browser)…")
        r = subprocess.run(["node", "scripts/doctor.mjs"], cwd=REMOTION, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", shell=os.name == "nt")
        line = next((ln for ln in (r.stdout or "").splitlines() if ln.startswith("__DOCTOR__")), None)
        if not line:
            problems.append("test render crashed: " + ((r.stderr or r.stdout).strip().splitlines() or ["no output"])[-1])
        else:
            res = json.loads(line[len("__DOCTOR__"):])
            if res.get("ok"):
                print(f"  ok  {res['composition']} frame {res['frame']} ({res['size']}): bundle {res['bundle_s']:.1f} s, "
                      f"frame {res['still_s']:.1f} s — browser: {res['browser']}")
                print("      (the first frame includes page start-up; a full video renders frames in parallel)")
            else:
                problems.append(f"test render failed: {res.get('error', 'unknown error')}")

    print()
    if problems:
        print("problems:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("everything works.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
