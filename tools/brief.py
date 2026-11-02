#!/usr/bin/env python3
"""Clients and briefs: the structured input of cutroom.

A free prompt plus material becomes:
  clients/<slug>/client.json        what stays the same for the client (contact, brand, voice)
  clients/<slug>/assets/            logo, photos, videos, fonts, music (synced into Remotion on render)
  clients/<slug>/references/        clips whose rhythm to match
  clients/<slug>/briefs/<id>.json   one per video: goal, format, copy, CTA, assets, concepts, beats, status

    python3 tools/brief.py client new hotel-sol --name "Hotel Sol" --logo ~/logo.png --whatsapp "+54 9 11 ..."
    python3 tools/brief.py client brand hotel-sol shots/*.jpg      # colours from the logo + screenshots
    python3 tools/brief.py client ts hotel-sol                      # write the Remotion brand.ts from client.json
    python3 tools/brief.py new hotel-sol summer-promo --format reel
    python3 tools/brief.py check clients/hotel-sol/briefs/summer-promo.json   # stage rules, avoid lists, claims in the copy
    python3 tools/brief.py show  clients/hotel-sol/briefs/summer-promo.json
    python3 tools/brief.py music hotel-sol                          # the client's music library (assets/music/LIBRARY.json)

Music: assets.music must be royalty-free or client-supplied, with its licence either in a file next to it
(<name>.LICENSE.txt / .license.txt / .txt) or in the track's entry of assets/music/LIBRARY.json.
Set CUTROOM_CLIENTS to use another clients folder.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENTS = os.environ.get("CUTROOM_CLIENTS") or os.path.join(ROOT, "clients")
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus"}
LICENCE_SUFFIXES = (".LICENSE.txt", ".license.txt", ".LICENCE.txt", ".licence.txt", ".txt")
SCHEMAS = os.path.join(ROOT, "schemas")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def client_dir(slug):
    return os.path.join(CLIENTS, slug)


def rel(path):
    """Path for messages: relative to the repo when inside it."""
    try:
        r = os.path.relpath(path, ROOT)
    except ValueError:  # another drive on Windows
        return path
    return path if r.startswith("..") else r


def validate(data, schema_name):
    try:
        import jsonschema
    except ImportError:
        sys.exit("jsonschema is not installed — run: pip install -r tools/requirements.txt")
    v = jsonschema.Draft202012Validator(load(os.path.join(SCHEMAS, schema_name)))
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}" for e in v.iter_errors(data)]


# ------------------------------------------------------------------ clients
def client_new(a):
    d = client_dir(a.slug)
    if os.path.exists(os.path.join(d, "client.json")):
        sys.exit(f"{d}/client.json already exists")
    for sub in ("assets/photos", "assets/videos", "assets/fonts", "assets/music", "references", "briefs"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    logo = None
    if a.logo:
        ext = os.path.splitext(a.logo)[1]
        logo = f"assets/logo{ext}"
        shutil.copy(os.path.expanduser(a.logo), os.path.join(d, logo))
    contact = {k: v for k, v in dict(whatsapp=a.whatsapp, instagram=a.instagram, website=a.website).items() if v}
    data = dict(slug=a.slug, name=a.name, language=a.language, contact=contact,
                brand=dict(colors=dict(ground="#F4F4F2", ink="#222222", accent="#3A5BA0"), fonts={}, **({"logo": logo} if logo else {})),
                voice="", notes="Colours are placeholders until `brief.py client brand` runs.")
    save(os.path.join(d, "client.json"), data)
    lib = os.path.join(d, "assets", "music", "LIBRARY.json")
    if not os.path.exists(lib):
        save(lib, dict(tracks=[]))
    print(f"created {rel(d)}/ — photos in assets/photos, fonts in assets/fonts, music in assets/music (index it in LIBRARY.json), reference clips in references/")
    print(f"list the folders holding the client's originals (absolute paths) as source_folders in {rel(d)}/client.local.json "
          "(git-ignored, machine-specific); every cutroom tool refuses to write there")


def client_brand(a):
    d = client_dir(a.slug)
    c = load(os.path.join(d, "client.json"))
    images = ([os.path.join(d, c["brand"]["logo"])] if c["brand"].get("logo") else []) + a.images
    if not images:
        sys.exit("no logo in client.json and no images given")
    tmp = os.path.join(d, ".brand")
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "brand.py"), *images, "--name", c["name"], "--out", tmp], check=True)
    with open(os.path.join(tmp, "brand.ts"), encoding="utf-8") as f:
        ts = f.read()
    colors = dict(re.findall(r'(\w+): "(#[0-9A-F]{6})"', ts))
    c["brand"]["colors"] = colors
    save(os.path.join(d, "client.json"), c)
    shutil.move(os.path.join(tmp, "palette.png"), os.path.join(d, "palette.png"))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"colours written to client.json; swatches in {rel(d)}/palette.png — check them against the client's material")


def client_ts(a):
    """client.json → remotion-base/src/clients/<slug>/brand.ts (single source of truth)."""
    c = load(os.path.join(client_dir(a.slug), "client.json"))
    const = re.sub(r"[^A-Z0-9]+", "_", c["name"].upper()).strip("_")
    b = c["brand"]
    fonts = b.get("fonts", {})
    files = fonts.get("files", [])
    colors = {**dict(paper=b["colors"].get("ground"), soft=b["colors"].get("ink"), accent2=b["colors"].get("accent"), line=b["colors"].get("ink")), **b["colors"]}
    contact = c.get("contact", {})
    out = getattr(a, "out", None) or os.path.join(ROOT, "remotion-base", "src", "clients", a.slug, "brand.ts")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lines = [
        "// Generated by tools/brief.py from clients/%s/client.json — edit the JSON, not this file." % a.slug,
        'import { Brand, loadFonts } from "../../lib/brand";',
        'import { staticFile } from "remotion";',
        "",
        f"export const {const}: Brand = {{",
        f'  name: {json.dumps(c["name"])},',
        "  colors: {",
        *[f'    {k}: "{colors[k]}",' for k in ("ground", "paper", "ink", "soft", "accent", "accent2", "line")],
        "  },",
        f'  fonts: {{ display: {json.dumps(fonts.get("display", "serif"))}, text: {json.dumps(fonts.get("text", "sans-serif"))}'
        + (f', script: {json.dumps(fonts["script"])}' if fonts.get("script") else "") + " },",
        "};",
        "",
        f"export const CLIENT = {json.dumps(dict(name=c['name'], taglines=b.get('taglines', [])), ensure_ascii=False)} as const;",
        f"export const CONTACT = {json.dumps(contact, ensure_ascii=False)} as const;",
        f'export const asset = (path: string) => staticFile(`clients/{a.slug}/${{path}}`);',
        "",
    ]
    if files:
        lines += ["loadFonts(", "  ["]
        lines += [f'    {{ family: {json.dumps(f["family"])}, file: {json.dumps(f["file"])}, weight: {json.dumps(f.get("weight", "400"))}, style: {json.dumps(f.get("style", "normal"))} }},' for f in files]
        lines += ["  ],", f'  "clients/{a.slug}/fonts",', ");"]
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {rel(out)}")


# ------------------------------------------------------------------ briefs
def brief_new(a):
    from quality.platforms import get

    c = load(os.path.join(client_dir(a.client), "client.json"))
    plat = get(a.platform)
    if a.format not in plat.FORMATS:
        sys.exit(f"format {a.format!r} is not a {a.platform} format; choose from {', '.join(plat.FORMATS)}")
    spec = plat.FORMATS[a.format]
    contact = c.get("contact", {})
    data = dict(
        id=a.id, client=a.client, platform=a.platform, format=a.format,
        duration_s=spec["rec_dur"][0] * 2 if "rec_dur" in spec else None,
        goal="", audience="",
        cta=dict(text="", contact=contact.get("whatsapp") or contact.get("phone") or contact.get("instagram") or ""),
        copy=dict(headline="", subtitle="", lines=[], avoid=[]),
        assets=dict(photos=[], videos=[], music=None),
        reference=None, concepts=[], chosen_concept=None, beats=[], composition=None, status="brief", decisions=[], notes="",
    )
    path = os.path.join(client_dir(a.client), "briefs", f"{a.id}.json")
    if os.path.exists(path):
        sys.exit(f"{path} already exists")
    save(path, data)
    print(f"created {rel(path)}")
    check(path)


# ------------------------------------------------------------------ music
def library_path(d):
    return os.path.join(d, "assets", "music", "LIBRARY.json")


def load_library(d):
    """(tracks, errors) from clients/<slug>/assets/music/LIBRARY.json; no file = empty library."""
    p = library_path(d)
    if not os.path.exists(p):
        return [], []
    try:
        lib = load(p)
    except ValueError as e:
        return [], [f"{rel(p)} is not valid JSON: {e}"]
    errs = [f"{rel(p)} → {e}" for e in validate(lib, "music-library.schema.json")]
    return lib.get("tracks", []) if isinstance(lib, dict) else [], errs


def licence_file(path):
    base = os.path.splitext(path)[0]
    return next((base + s for s in LICENCE_SUFFIXES if os.path.exists(base + s)), None)


def music_licence(d, music):
    """Errors and warnings for the brief's music: it must exist and carry a licence (sidecar file or LIBRARY.json entry)."""
    errors, warn = [], []
    mp = os.path.join(d, music)
    if not os.path.exists(mp):
        return [f"missing music {music}"], []
    tracks, lib_errors = load_library(d)
    errors += lib_errors
    music_dir = os.path.join(d, "assets", "music")
    entry = next((t for t in tracks if os.path.normpath(os.path.join(music_dir, t.get("file", ""))) == os.path.normpath(mp)), None)
    lic = (entry or {}).get("licence", "").strip()
    if lic and os.path.splitext(lic)[1].lower() in (".txt", ".pdf", ".md", ".html"):
        if not os.path.exists(os.path.join(music_dir, lic)):
            errors.append(f"music licence file {lic} (from LIBRARY.json) is missing")
    elif not lic and not licence_file(mp):
        errors.append(f"music {music} has no licence: add {os.path.basename(os.path.splitext(mp)[0])}.LICENSE.txt next to it or a "
                      "'licence' in its LIBRARY.json entry — only royalty-free or client-supplied music")
    if entry is None and os.path.dirname(os.path.normpath(mp)) == os.path.normpath(music_dir):
        warn.append(f"music {music} is not indexed in assets/music/LIBRARY.json (title, licence, source, mood, bpm)")
    return errors, warn


def music_list(a):
    """List a client's music library and flag tracks with missing files or licences."""
    d = client_dir(a.slug)
    if not os.path.isdir(d):
        sys.exit(f"client {a.slug!r} not found in {rel(CLIENTS)}")
    music_dir = os.path.join(d, "assets", "music")
    tracks, errors = load_library(d)
    print(f"\n{rel(library_path(d))}")
    for e in errors:
        print(f"  ERROR  {e}")
    if not tracks:
        print("  (no tracks indexed)")
    for t in tracks:
        path = os.path.join(music_dir, t.get("file", ""))
        flags = []
        if not os.path.exists(path):
            flags.append("FILE MISSING")
        lic = t.get("licence", "").strip()
        if not lic and not licence_file(path):
            flags.append("NO LICENCE")
        bpm = f"{t['bpm']:g} bpm" if t.get("bpm") else "– bpm"
        mood = ", ".join(t["mood"]) if isinstance(t.get("mood"), list) else (t.get("mood") or "–")
        print(f"  {t.get('title', '?'):28} {t.get('file', '?'):28} {bpm:9} {mood:22} {lic or '–'}" + (f"   [{'; '.join(flags)}]" if flags else ""))
        if t.get("source"):
            print(f"  {'':28} source: {t['source']}")
    indexed = {os.path.normpath(t.get("file", "")) for t in tracks}
    loose = sorted(f for f in (os.listdir(music_dir) if os.path.isdir(music_dir) else [])
                   if os.path.splitext(f)[1].lower() in AUDIO_EXT and os.path.normpath(f) not in indexed)
    for f in loose:
        print(f"  WARN   {f} is in assets/music but not in LIBRARY.json")
    return 1 if errors or any(not os.path.exists(os.path.join(music_dir, t.get("file", ""))) for t in tracks) else 0


STAGES = ["brief", "material", "concepts", "building", "review", "approved", "delivered"]


def at_least(stage, name):
    """True when `stage` (a status) is `name` or later."""
    return STAGES.index(stage) >= STAGES.index(name)


def norm_text(text):
    """Lower case without accents, for avoid-word matching."""
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()


def on_screen_copy(b):
    """[(source, text)] of every on-screen text in the brief."""
    cp = b.get("copy", {})
    out = [("copy.headline", cp.get("headline", "")), ("copy.subtitle", cp.get("subtitle", ""))]
    out += [(f"copy.lines[{i}]", t) for i, t in enumerate(cp.get("lines", []))]
    out.append(("cta.text", b.get("cta", {}).get("text", "")))
    return [(s, t) for s, t in out if t]


def copy_claims(b, c):
    """Claims findings (tools/quality/claims.py) over the brief's on-screen copy, in the client's language."""
    from quality import claims
    lang = (c or {}).get("language") or "es-AR"
    return [f for src, t in on_screen_copy(b) for f in claims.check(t, lang, src)]


def avoid_hits(b, c):
    """Errors for copy.avoid (substring) and client voice_guide.avoid (whole words) found in the on-screen copy."""
    texts = norm_text(" ".join(t for _, t in on_screen_copy(b)).replace(" / ", " "))
    errors = []
    for w in b.get("copy", {}).get("avoid", []):
        if w and norm_text(w) in texts:
            errors.append(f'the copy uses "{w.lower()}", which is listed under copy.avoid')
    for w in (c or {}).get("voice_guide", {}).get("avoid", []):
        if w and re.search(r"(?<!\w)" + re.escape(norm_text(w)) + r"(?!\w)", texts):
            errors.append(f'the copy uses "{w}", which the client voice_guide.avoid rules out')
    return errors


def client_local(d, c):
    """(errors, merged client) for clients/<slug>/client.local.json (git-ignored, merged over client.json)
    and for the source_folders entries of both files."""
    from media.guard import LOCAL_FILE, is_absolute, source_folder_entries
    errors = []
    lpath = os.path.join(d, LOCAL_FILE)
    if os.path.exists(lpath):
        try:
            local = load(lpath)
        except ValueError as e:
            local = None
            errors.append(f"{LOCAL_FILE} is not valid JSON: {e}")
        if local is not None and not isinstance(local, dict):
            errors.append(f"{LOCAL_FILE} must be a JSON object")
        elif local is not None:
            merged = {**c, **local}
            known = set(validate(c, "client.schema.json"))  # already reported against client.json
            errors += [f"{LOCAL_FILE} → {e}" for e in validate(merged, "client.schema.json") if e not in known]
            c = merged
    for entry, origin in source_folder_entries(d):
        if not is_absolute(entry):
            errors.append(f"{origin} → source_folders entries must be absolute paths, got {entry!r}")
    return errors, c


def material_problems(b, d):
    """(errors, warnings) for leaving the material stage."""
    errors, warn = [], []
    m = b.get("material") or {}
    photos = b.get("assets", {}).get("photos", [])
    if m.get("batch"):
        an = m.get("analysis")
        if not an:
            errors.append(f"material.batch {m['batch']!r} is set but material.analysis is empty — run the material analysis first")
        elif not os.path.exists(os.path.join(d, an)):
            errors.append(f"material analysis {an} does not exist")
        elif m.get("selected"):
            try:
                analysis = load(os.path.join(d, an))
            except ValueError as e:
                analysis = None
                errors.append(f"material analysis {an} is not valid JSON: {e}")
            if analysis is not None:
                by_id = {p.get("id"): p for p in analysis.get("photos", []) if isinstance(p, dict)} if isinstance(analysis, dict) else {}
                have = set(photos)
                have_names = {os.path.basename(p) for p in photos}
                for i in m["selected"]:
                    exported = f"assets/photos/{m['batch']}-{i:02d}.jpg"  # what tools/material.py select writes
                    if i not in by_id:
                        errors.append(f"material.selected {i} is not a photo id of {an}")
                    elif exported not in have and os.path.basename(str(by_id[i].get("file", ""))) not in have_names:
                        errors.append(f"selected photo #{i} is not in assets.photos (expected {exported}) — run: tools/material.py select")
        for v in m.get("videos", []):
            if v.get("file") and not os.path.exists(os.path.join(d, v["file"])):
                errors.append(f"material video {v['file']} (id {v.get('id')}) does not exist")
        if not m.get("selected") and not m.get("videos") and not b.get("assets", {}).get("videos"):
            warn.append(f"material batch {m['batch']!r} chosen but nothing selected — typography-only? "
                        "(pick with tools/material.py select, or confirm a type-only piece with the user)")
    elif not photos and not b.get("assets", {}).get("videos"):
        warn.append("no material, photos or videos: a typography-only piece (type and brand only) — confirm it once with the user")
    return errors, warn


def check(path):
    """Validate a brief and list what is missing — phrased as questions to ask the user."""
    from quality.platforms import get

    b = load(path)
    errors = validate(b, "brief.schema.json")
    ask, warn = [], []
    d = client_dir(b.get("client", ""))
    cpath = os.path.join(d, "client.json")
    if not os.path.exists(cpath):
        errors.append(f"client {b.get('client')!r} not found — run: brief.py client new {b.get('client')} --name …")
        c = {}
    else:
        c = load(cpath)
        errors += [f"client.json → {e}" for e in validate(c, "client.schema.json")]
        e, c = client_local(d, c)
        errors += e
    if errors:
        # wrong types or shapes: report them before the checks below trip over them
        print(f"\n{rel(path)}  [{b.get('status', 'brief')}]")
        for e in errors:
            print(f"  ERROR  {e}")
        return 1
    stage = b.get("status", "brief")

    # what any brief needs
    if not b.get("goal"):
        ask.append("What is the piece for? (the goal in one sentence)")
    if not b.get("cta", {}).get("text"):
        ask.append("What should the viewer do? (call to action)")
    if not b.get("cta", {}).get("contact") and not c.get("contact"):
        ask.append("Which contact goes on screen? (WhatsApp, website, handle)")
    if not b.get("copy", {}).get("headline"):
        ask.append("Is there a required headline, or should I propose one?")
    try:
        plat = get(b.get("platform", "instagram"))
        spec = plat.FORMATS.get(b.get("format"))
        if not spec:
            errors.append(f"format {b.get('format')!r} is not a {plat.NAME} format; choose from {', '.join(plat.FORMATS)}")
        elif "dur" in spec and b.get("duration_s"):
            lo, hi = spec["dur"]
            if not (lo <= b["duration_s"] <= hi):
                errors.append(f"duration {b['duration_s']}s outside {lo}–{hi}s for {b['format']}")
            rlo, rhi = spec["rec_dur"]
            if not (rlo <= b["duration_s"] <= rhi):
                warn.append(f"{b['duration_s']}s — {rlo}–{rhi}s works best for {b['format']}")
    except SystemExit as e:
        errors.append(str(e))

    # material
    for kind in ("photos", "videos"):
        for p in b.get("assets", {}).get(kind, []):
            if not os.path.exists(os.path.join(d, p)):
                errors.append(f"missing asset {p}")
    if b.get("assets", {}).get("music"):
        e, w = music_licence(d, b["assets"]["music"])
        errors += e
        warn += w
    if b.get("reference") and not os.path.exists(os.path.join(d, b["reference"])):
        errors.append(f"missing reference {b['reference']}")
    no_material = not b.get("assets", {}).get("photos") and not b.get("assets", {}).get("videos") and not (b.get("material") or {}).get("batch")
    if no_material and not at_least(stage, "concepts"):
        ask.append("Are there photos or videos to use? (if not, I work with type and the brand only)")
    if c and not c.get("brand", {}).get("logo"):
        ask.append("Do you have the client's logo?")

    # on-screen copy: avoid lists and claims
    errors += avoid_hits(b, c)
    for f in copy_claims(b, c):
        line = f'{f.what}: "{f.phrase}" in {f.source} → {f.suggestion}'
        (errors if f.severity == "severe" else warn).append(f"claim ({f.severity}) {line}")

    # what each stage needs
    if at_least(stage, "concepts"):
        e, w = material_problems(b, d)
        errors += e
        warn += w
        if len(b.get("concepts", [])) < 3:
            errors.append("status is past 'material' but there are fewer than 3 concepts")
    if at_least(stage, "building"):
        if b.get("chosen_concept") is None:
            errors.append("building without a chosen concept")
        elif not 0 <= b["chosen_concept"] < len(b.get("concepts", [])):
            errors.append(f"chosen_concept {b['chosen_concept']} does not point at one of the {len(b.get('concepts', []))} concepts (0-based)")
        if not b.get("beats"):
            errors.append("building without a beat sheet")
    if at_least(stage, "review") and not b.get("composition"):
        errors.append("in review without a composition id")

    print(f"\n{rel(path)}  [{b.get('status', 'brief')}]")
    for e in errors:
        print(f"  ERROR  {e}")
    for w in warn:
        print(f"  WARN   {w}")
    if ask:
        print("  To ask (or decide and record in decisions):")
        for q in ask:
            print(f"   - {q}")
    if not (errors or ask or warn):
        print("  OK — brief complete for its stage")
    return 1 if errors else 0


def show(path):
    b = load(path)
    print(json.dumps(b, indent=2, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    cl = sub.add_parser("client").add_subparsers(dest="sub", required=True)
    n = cl.add_parser("new")
    n.add_argument("slug")
    n.add_argument("--name", required=True)
    n.add_argument("--logo")
    n.add_argument("--whatsapp")
    n.add_argument("--instagram")
    n.add_argument("--website")
    n.add_argument("--language", default="es-AR")
    br = cl.add_parser("brand")
    br.add_argument("slug")
    br.add_argument("images", nargs="*")
    ts = cl.add_parser("ts")
    ts.add_argument("slug")
    ts.add_argument("--out", help="write brand.ts here instead of remotion-base/src/clients/<slug>/brand.ts")

    nb = sub.add_parser("new")
    nb.add_argument("client")
    nb.add_argument("id")
    nb.add_argument("--format", required=True)
    nb.add_argument("--platform", default="instagram", help="instagram, tiktok or youtube_shorts")
    ck = sub.add_parser("check")
    ck.add_argument("brief")
    sh = sub.add_parser("show")
    sh.add_argument("brief")
    mu = sub.add_parser("music", help="list a client's music library (assets/music/LIBRARY.json)")
    mu.add_argument("slug")

    a = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if a.cmd == "client":
        return {"new": client_new, "brand": client_brand, "ts": client_ts}[a.sub](a) or 0
    if a.cmd == "new":
        return brief_new(a) or 0
    if a.cmd == "check":
        return check(a.brief)
    if a.cmd == "show":
        return show(a.brief) or 0
    if a.cmd == "music":
        return music_list(a)


if __name__ == "__main__":
    sys.exit(main())
