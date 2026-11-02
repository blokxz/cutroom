#!/usr/bin/env python3
"""One-command setup for cutroom on a new machine (Windows, macOS or Linux).

    python tools/setup.py                 # check requirements, install dependencies, create .env
    python tools/setup.py --with-models   # also fetch the optional face model (hash-verified)
    python tools/setup.py --check         # only check, change nothing

Steps:
  1. Node.js (20.19+ or 22.13+), Python (3.10+), ffmpeg and ffprobe — prints how to install what's missing
  2. npm ci in remotion-base/ (skipped when node_modules matches package-lock.json)
  3. pip install -r tools/requirements.txt
  4. .env from .env.example if there is none
  5. optional: tools/models.py fetch
Then run `python tools/doctor.py` to render a test frame.
"""
import argparse
import os
import platform
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTION = os.path.join(ROOT, "remotion-base")
sys.path.insert(0, os.path.join(ROOT, "tools"))

HINTS = {
    "node": {
        "Windows": "winget install OpenJS.NodeJS.LTS",
        "Darwin": "brew install node@22",
        "Linux": "use your package manager or https://nodejs.org (22 LTS)",
    },
    "ffmpeg": {
        "Windows": "winget install Gyan.FFmpeg   (then open a new terminal)",
        "Darwin": "brew install ffmpeg",
        "Linux": "sudo apt install ffmpeg   (or your distro's package)",
    },
    "python": {
        "Windows": "winget install Python.Python.3.12",
        "Darwin": "brew install python@3.12",
        "Linux": "sudo apt install python3 python3-pip",
    },
}


def hint(tool):
    return HINTS[tool].get(platform.system(), HINTS[tool]["Linux"])


def run(cmd, cwd=None, check=True):
    print(f"  $ {' '.join(cmd)}")
    shell = os.name == "nt" and cmd[0] in ("npm", "npx")  # npm is a .cmd script on Windows
    r = subprocess.run(cmd, cwd=cwd, shell=shell)
    if check and r.returncode != 0:
        raise SystemExit(f"command failed ({r.returncode}): {' '.join(cmd)}")
    return r.returncode


def version_of(cmd, pattern=r"(\d+)\.(\d+)(?:\.(\d+))?"):
    exe = shutil.which(cmd)
    if not exe:
        return None, None
    try:
        out = subprocess.run([exe, "--version" if cmd != "ffmpeg" else "-version"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace").stdout
    except OSError:
        return exe, None
    m = re.search(pattern, out)
    return exe, tuple(int(x or 0) for x in m.groups()) if m else None


def node_ok(v):
    return v is not None and (v >= (22, 13, 0) or ((20, 19, 0) <= v < (21, 0, 0)) or v >= (24, 0, 0))


def check_requirements():
    problems = []
    exe, v = version_of("node")
    if not exe or not node_ok(v):
        problems.append(f"Node.js 20.19+ or 22.13+ needed (found {'.'.join(map(str, v)) if v else 'none'}) — {hint('node')}")
    else:
        print(f"  ok  node {'.'.join(map(str, v))}")
    if not shutil.which("npm"):
        problems.append(f"npm not found (comes with Node.js) — {hint('node')}")
    if sys.version_info < (3, 10):
        problems.append(f"Python 3.10+ needed (this is {platform.python_version()}) — {hint('python')}")
    else:
        print(f"  ok  python {platform.python_version()}")
    try:
        from quality.bins import ffmpeg, ffprobe  # honours FFMPEG / FFPROBE
        ff, fp = ffmpeg(), ffprobe()
    except Exception:  # noqa: BLE001
        ff, fp = "ffmpeg", "ffprobe"
    for name, binary in (("ffmpeg", ff), ("ffprobe", fp)):
        if shutil.which(binary) or os.path.exists(binary):
            print(f"  ok  {name} ({shutil.which(binary) or binary})")
        else:
            problems.append(f"{name} not found — {hint('ffmpeg')}")
    return problems


def npm_up_to_date():
    lock = os.path.join(REMOTION, "package-lock.json")
    marker = os.path.join(REMOTION, "node_modules", ".package-lock.json")
    return os.path.exists(marker) and os.path.getmtime(marker) >= os.path.getmtime(lock)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only check requirements")
    ap.add_argument("--with-models", action="store_true", help="also fetch the optional face model")
    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    print("1. requirements")
    problems = check_requirements()
    if problems:
        print("\nmissing:")
        for p in problems:
            print(f"  - {p}")
        print("\ninstall them, open a new terminal and run this again.")
        return 1
    if a.check:
        print("\nall requirements found.")
        return 0

    print("\n2. Remotion dependencies")
    if npm_up_to_date():
        print("  ok  node_modules matches package-lock.json")
    else:
        run(["npm", "ci"], cwd=REMOTION)

    print("\n3. Python dependencies")
    req = os.path.join(ROOT, "tools", "requirements.txt")
    if run([sys.executable, "-m", "pip", "install", "-r", req], check=False) != 0:
        print("  pip refused (externally managed Python?). Either use a virtual environment:")
        print(f"    {sys.executable} -m venv .venv  and activate it, then run this again")
        print("  or add --break-system-packages:")
        print(f"    {sys.executable} -m pip install --break-system-packages -r tools/requirements.txt")
        return 1

    print("\n4. .env")
    env, example = os.path.join(ROOT, ".env"), os.path.join(ROOT, ".env.example")
    if os.path.exists(env):
        print("  ok  .env exists (left as is)")
    else:
        shutil.copyfile(example, env)
        print("  wrote .env from .env.example — every value is optional, edit only if something isn't found")

    if a.with_models:
        print("\n5. face model")
        run([sys.executable, os.path.join(ROOT, "tools", "models.py"), "fetch"], check=False)

    print("\ndone. Next: python tools/doctor.py   (renders a test frame and reports timings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
