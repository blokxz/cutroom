#!/usr/bin/env python3
"""models.py — optional local models used by the verifier.

    python3 tools/models.py status            # what is installed, and whether it matches the pinned hash
    python3 tools/models.py fetch             # download, verify SHA-256, write tools/models/LICENSES.md
    python3 tools/models.py fetch --no-verify # skip the hash check (not recommended)

Models live in tools/models/ (git-ignored except LICENSES.md). The face check (tools/quality/faces.py)
also reads env CUTROOM_FACE_MODEL to use a model file somewhere else.
"""
import argparse
import hashlib
import os
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(HERE, "models")

MODELS = {
    "yunet": dict(
        file="face_detection_yunet_2023mar.onnx",
        purpose="face detection for the 'people visible' check (tools/quality/faces.py)",
        urls=[
            "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
            "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx",
        ],
        # SHA-256 of the Git LFS object as published by the OpenCV organisation
        # (huggingface.co/opencv/face_detection_yunet, file details; the opencv_zoo GitHub file is the same object).
        sha256="8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        licence="MIT",
        source="https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet",
        # verbatim from models/face_detection_yunet/LICENSE in opencv_zoo (checked 2026-10-25)
        copyright="Copyright (c) 2020 Shiqi Yu <shiqi.yu@gmail.com>",
    ),
}

LICENSES = """# Third-party models

Files in this folder are downloaded by `python3 tools/models.py fetch`; only this file is in the repo.

{rows}
## MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def write_licenses(folder=MODELS_DIR):
    rows = "".join(f"## {m['file']}\n\n- Purpose: {m['purpose']}\n- Source: {m['source']}\n- Licence: {m['licence']}\n"
                   f"- {m['copyright']}\n- SHA-256: `{m['sha256']}`\n\n" for m in MODELS.values())
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "LICENSES.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(LICENSES.format(rows=rows))
    return path


def download(url, dest):
    with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


def fetch(name, m, verify=True, folder=MODELS_DIR, downloader=download):
    """Download one model into `folder`; keep it only if its SHA-256 matches. Returns True on success."""
    if verify and not m.get("sha256"):
        print(f"{name}: no pinned SHA-256 — refusing to install an unverified file (pass --no-verify to override)", file=sys.stderr)
        return False
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, m["file"])
    if os.path.exists(dest) and verify and sha256(dest) == m["sha256"]:
        print(f"{name}: already installed and verified ({dest})")
        return True
    for url in m["urls"]:
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".part")
        os.close(fd)
        try:
            downloader(url, tmp)
        except Exception as ex:
            print(f"{name}: {url} failed ({type(ex).__name__}: {ex})", file=sys.stderr)
            os.remove(tmp)
            continue
        got = sha256(tmp)
        if verify and got != m["sha256"]:
            print(f"{name}: {url} has SHA-256 {got}, expected {m['sha256']} — discarded", file=sys.stderr)
            os.remove(tmp)
            continue
        os.replace(tmp, dest)
        print(f"{name}: installed {dest}" + ("" if verify else " (NOT verified)"))
        return True
    return False


def status(folder=MODELS_DIR):
    rows = []
    for name, m in MODELS.items():
        path = os.path.join(folder, m["file"])
        if name == "yunet" and os.environ.get("CUTROOM_FACE_MODEL"):
            path = os.environ["CUTROOM_FACE_MODEL"]
        if not os.path.exists(path):
            state = "missing (run: python3 tools/models.py fetch)"
        elif sha256(path) == m["sha256"]:
            state = "installed, verified"
        else:
            state = "installed, SHA-256 does NOT match the pinned hash"
        rows.append((name, path, state))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="download and verify the models")
    f.add_argument("--no-verify", action="store_true", help="install even if the SHA-256 does not match (not recommended)")
    sub.add_parser("status", help="show what is installed")
    a = ap.parse_args(argv)
    if a.cmd == "status":
        for name, path, state in status():
            print(f"  {name:8} {state:52} {path}")
        return 0
    ok = all([fetch(name, m, verify=not a.no_verify) for name, m in MODELS.items()])
    print(f"licences: {write_licenses()}")
    return 0 if ok else 1


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):  # Windows pipes default to a legacy code page; messages use → ≤ —
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
