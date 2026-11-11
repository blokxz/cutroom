#!/usr/bin/env python3
"""Looks: a palette and a pair of typefaces chosen together, applied to a client in one step.

  looks.py list                                   the looks, their colours, faces and contrast
  looks.py check [<look>]                         contrast of every look (ink on ground ≥ 4.5, accent on ground ≥ 3)
  looks.py fonts <family> [--weights 400 600] [--italic]   fetch an OFL family from npm (@fontsource) into the cache
  looks.py apply <look> <client> [--keep-colors]  install the look's faces in clients/<client>/assets/fonts, write
                                                   them (and the colours, unless --keep-colors) into client.json,
                                                   then regenerate src/clients/<client>/brand.ts

Faces come only from @fontsource packages on npm (SIL OFL); each family's LICENSE is copied next to its files.
The cache is ~/.cache/cutroom/fontsource (CUTROOM_FONT_CACHE overrides it). Colours follow the brand.ts tokens:
ground, paper, ink, soft, accent, accent2, line. `brand.py` measures a palette from a logo or screenshots; a look
gives the faces and a palette that already work together — keep the client's colours with --keep-colors.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOKS_FILE = os.path.join(ROOT, "tools", "looks", "looks.json")


def cache_dir():
    return os.environ.get("CUTROOM_FONT_CACHE") or os.path.join(os.path.expanduser("~"), ".cache", "cutroom", "fontsource")


def load_looks():
    with open(LOOKS_FILE, encoding="utf-8") as f:
        return json.load(f)["looks"]


# ------------------------------------------------------------------ contrast
def _lum(hex_):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check(look):
    """Problems with a look's colours, as strings (empty when it reads)."""
    c = look["colors"]
    out = []
    if contrast(c["ink"], c["ground"]) < 4.5:
        out.append(f"ink on ground {contrast(c['ink'], c['ground']):.2f} < 4.5")
    if contrast(c["ink"], c["paper"]) < 4.5:
        out.append(f"ink on paper {contrast(c['ink'], c['paper']):.2f} < 4.5")
    if contrast(c["accent"], c["ground"]) < 3:
        out.append(f"accent on ground {contrast(c['accent'], c['ground']):.2f} < 3")
    if contrast(c["soft"], c["ground"]) < 3:
        out.append(f"soft on ground {contrast(c['soft'], c['ground']):.2f} < 3")
    for k in ("ground", "paper", "ink", "soft", "accent", "accent2", "line"):
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", c.get(k, "")):
            out.append(f"colour {k} missing or not #rrggbb")
    return out


# ------------------------------------------------------------------ fonts from @fontsource
def slug(family):
    return re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-")


def fetch(family, weights=(400,), italic=False):
    """Woff2 files (latin subset) of an OFL family, downloaded once with `npm pack` into the cache.
    Returns [(path, weight, style)] and the LICENSE path."""
    pkg = f"@fontsource/{slug(family)}"
    dest = os.path.join(cache_dir(), slug(family))
    if not os.path.isdir(os.path.join(dest, "package")):
        os.makedirs(dest, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(["npm", "pack", pkg, "--silent"], cwd=tmp, capture_output=True, text=True)
            tgz = glob.glob(os.path.join(tmp, "*.tgz"))
            if r.returncode != 0 or not tgz:
                raise RuntimeError(f"npm pack {pkg} failed: {r.stderr.strip() or r.stdout.strip()}")
            with tarfile.open(tgz[0]) as t:
                members = [m for m in t.getmembers() if m.isfile() and not m.name.startswith("/") and ".." not in m.name]
                t.extractall(dest, members=members)
    pdir = os.path.join(dest, "package")
    meta = json.load(open(os.path.join(pdir, "package.json"), encoding="utf-8"))
    if "OFL" not in str(meta.get("license", "")):
        raise RuntimeError(f"{pkg} is not OFL-licensed ({meta.get('license')})")
    files = []
    for w in weights:
        for style in (("normal", "italic") if italic else ("normal",)):
            p = os.path.join(pdir, "files", f"{slug(family)}-latin-{w}-{style}.woff2")
            if not os.path.exists(p):
                raise RuntimeError(f"{pkg} has no latin {w} {style} woff2")
            files.append((p, str(w), style))
    lic = os.path.join(pdir, "LICENSE")
    return files, lic if os.path.exists(lic) else None


def install_look(look, client_dir, keep_colors=False):
    """Copy the look's faces into the client's assets and write them into client.json. Returns the new client dict."""
    cj = os.path.join(client_dir, "client.json")
    with open(cj, encoding="utf-8") as f:
        client = json.load(f)
    fonts_dir = os.path.join(client_dir, "assets", "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    entries, roles = [], {}
    for role, face in look["faces"].items():
        files, lic = fetch(face["family"], face.get("weights", [400]), face.get("italic", False))
        for src, weight, style in files:
            name = os.path.basename(src)
            shutil.copyfile(src, os.path.join(fonts_dir, name))
            e = {"family": face["family"], "file": name, "weight": weight}
            if style == "italic":
                e["style"] = "italic"
            if e not in entries:
                entries.append(e)
        if lic:
            shutil.copyfile(lic, os.path.join(fonts_dir, f"{slug(face['family'])}.LICENSE.txt"))
        roles[role] = face["family"]
    brand = client.setdefault("brand", {})
    old = brand.get("fonts", {})
    # a script face the look does not replace stays, with its files
    if "script" not in roles and old.get("script") and old.get("script") not in roles.values():
        entries += [e for e in old.get("files", []) if e.get("family") == old["script"] and e not in entries]
    brand["fonts"] = {"display": roles.get("display", old.get("display")), "text": roles.get("text", old.get("text")),
                      "script": roles.get("script", old.get("script", roles.get("display"))), "files": entries}
    if not keep_colors:
        brand["colors"] = dict(look["colors"])
    brand["look"] = look["name"]
    with open(cj, "w", encoding="utf-8") as f:
        json.dump(client, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return client


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    c = sub.add_parser("check")
    c.add_argument("look", nargs="?")
    fo = sub.add_parser("fonts")
    fo.add_argument("family")
    fo.add_argument("--weights", nargs="+", type=int, default=[400])
    fo.add_argument("--italic", action="store_true")
    a_ = sub.add_parser("apply")
    a_.add_argument("look")
    a_.add_argument("client")
    a_.add_argument("--keep-colors", action="store_true")
    a = ap.parse_args(argv)
    looks = {lk["name"]: lk for lk in load_looks()}
    if a.cmd == "list":
        for lk in looks.values():
            faces = " / ".join(f["family"] for f in lk["faces"].values())
            print(f"{lk['name']:10} {faces:42} {lk['mood']}")
            print("           " + "  ".join(f"{k} {v}" for k, v in lk["colors"].items()))
        return 0
    if a.cmd == "check":
        bad = 0
        for name in [a.look] if a.look else looks:
            probs = check(looks[name])
            print(f"{name:10} " + ("ok" if not probs else "; ".join(probs)))
            bad += bool(probs)
        return 1 if bad else 0
    if a.cmd == "fonts":
        files, lic = fetch(a.family, a.weights, a.italic)
        for p, w, s in files:
            print(w, s, p)
        print("license", lic)
        return 0
    if a.look not in looks:
        sys.exit(f"unknown look {a.look!r}; choose from {', '.join(looks)}")
    cdir = os.path.join(os.environ.get("CUTROOM_CLIENTS") or os.path.join(ROOT, "clients"), a.client)
    if not os.path.isfile(os.path.join(cdir, "client.json")):
        sys.exit(f"no client {a.client!r} (expected {cdir}/client.json)")
    install_look(looks[a.look], cdir, a.keep_colors)
    print(f"applied {a.look} to {a.client}" + (" (faces only)" if a.keep_colors else ""))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "brief.py"), "client", "ts", a.client])
    return r.returncode


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
