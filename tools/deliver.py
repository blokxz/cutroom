#!/usr/bin/env python3
"""Delivery package: everything needed to publish a finished video, in one folder.

    python3 tools/deliver.py clients/<slug>/briefs/<id>.json [--cover-time S]

Builds deliveries/<id>/ at the repo root (git-ignored):
  <Composition>.mp4      the final video (copy of remotion-base/out/<id>/<Composition>.mp4, not the draft)
  cover_9x16.png         the cover frame: --cover-time, else brief delivery.cover_time, else the frame of the
                         first 3.5 s with the most legible text (from <Composition>.track.json, or edge density)
  cover_grid_3x4.png     centre 3:4 crop — how the cover shows in the profile grid
  cover_grid_1x1.png     centre square crop — older grids and link previews
  whatsapp_720p.mp4      light version to send by WhatsApp (720x1280, at most 15 MB, AAC audio kept)
  caption.md             written BEFORE running this, following the client's voice_guide: three versions
                         (short, medium, booking), hashtags and alt text. If it is missing, a template prefilled
                         from voice_guide is written and the run stops with exit code 1.
  sheet.json             what was used: assets with SHA-256, on-screen texts, tool versions, verifier verdict,
                         claims findings, caption checks, files
  CHECKLIST.md           pre-publish checklist

The caption path can be set in the brief (delivery.caption, relative to the repo).
Exit code 1 when something must be fixed (severe claims, caption errors, verification not passed);
the package is still built so it can be reviewed.
Environment: CUTROOM_OUT (render folder, default remotion-base/out), CUTROOM_DELIVERIES (default deliveries/).
"""
import argparse
import datetime
import hashlib
import json
import os
import platform as pyplatform
import re
import shutil
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import brief as briefs  # noqa: E402
from quality import bins, claims  # noqa: E402

COVER_WINDOW_S = 3.5
WHATSAPP_MAX_MB = 15.0
WHATSAPP_SIZE = (720, 1280)
CAPTION_MAX = 2200     # Instagram caption limit
HOOK_MAX = 125         # characters shown before "more"
ALT_MAX = 100
HASHTAG_LIMIT = 30     # Instagram rejects more
VERSIONS = (("short", "Short"), ("medium", "Medium"), ("booking", "Booking"))


def out_root():
    return os.environ.get("CUTROOM_OUT") or os.path.join(ROOT, "remotion-base", "out")


def deliveries_root():
    return os.environ.get("CUTROOM_DELIVERIES") or os.path.join(ROOT, "deliveries")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def mb(path):
    return round(os.path.getsize(path) / 1e6, 2)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"{os.path.basename(cmd[0])} failed: {r.stderr.strip()[-600:]}")
    return r.stdout


def probe(path):
    j = json.loads(run([bins.ffprobe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", path]))
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    num, _, den = (v.get("avg_frame_rate") or "0/1").partition("/")
    fps = round(float(num) / float(den or 1), 3) if float(den or 1) else 0
    return dict(width=v["width"], height=v["height"], duration_s=round(float(j["format"].get("duration", 0)), 3), fps=fps,
                video_codec=v.get("codec_name"), audio_codec=a.get("codec_name") if a else None, size_mb=mb(path))


def ensure_writable(path):
    """Refuse to write inside the client's source folders (tools/media/guard.py, when present)."""
    try:
        from media.guard import ensure_writable as guard
    except ImportError:
        return
    try:
        guard(path)
    except Exception as e:  # ReadOnlyPathError: report it as a plain message
        raise SystemExit(str(e)) from None


# ------------------------------------------------------------------ cover
def cover_from_track(track_path, window_s=COVER_WINDOW_S):
    """Second with the most visible, sharp text in the first `window_s` seconds, from a .track.json; None if no text."""
    try:
        with open(track_path, encoding="utf-8") as f:
            t = json.load(f)
    except (OSError, ValueError):
        return None
    fps, W, H = t.get("fps") or 30, t.get("width") or 1080, t.get("height") or 1920
    last = int(window_s * fps)
    score = {}
    for r in t.get("records", []):
        if r.get("k") != "text" or r.get("f", 0) > last:
            continue
        seen = 0.0  # opacity x on-screen fraction of the element: camera scale does not change it
        if not r.get("blurred") and r.get("o", 0) > 0:
            x0, y0 = max(0, r["x"]), max(0, r["y"])
            x1, y1 = min(W, r["x"] + r["w"]), min(H, r["y"] + r["h"])
            if x1 > x0 and y1 > y0:
                seen = (x1 - x0) * (y1 - y0) / max(1, r["w"] * r["h"]) * min(1.0, r["o"])
        score[r["f"]] = score.get(r["f"], 0.0) + seen
    if not score or max(score.values()) <= 0:
        return None
    frames = range(0, last + 1)
    s = [score.get(f, 0.0) for f in frames]
    # stability: a frame scores what its worst neighbour (±3 frames) scores, so mid-animation frames lose
    stable = [min(s[max(0, i - 3):i + 4]) for i in range(len(s))]
    top = max(stable)
    if top <= 0:
        best = max(range(len(s)), key=lambda i: s[i])
    else:
        # middle of the first run of frames near the top score: the text has settled there
        first = next(i for i, v in enumerate(stable) if v >= top * 0.97)
        end = first
        while end + 1 < len(stable) and stable[end + 1] >= top * 0.97:
            end += 1
        best = (first + end) // 2
    return round(best / fps, 3)


def clipped_in_grid(track_path, t):
    """Grid crops ("3x4", "1x1") that cut a visible text element at second `t`, from a .track.json; [] without one."""
    try:
        with open(track_path, encoding="utf-8") as f:
            tr = json.load(f)
    except (OSError, ValueError):
        return []
    fps, W, H = tr.get("fps") or 30, tr.get("width") or 1080, tr.get("height") or 1920
    frame = round(t * fps)
    texts = [r for r in tr.get("records", []) if r.get("k") == "text" and r.get("f") == frame and r.get("o", 0) > 0.2
             and r["y"] + r["h"] > 0 and r["y"] < H]
    out = []
    for name, ratio in (("3x4", 4 / 3), ("1x1", 1.0)):
        ch = min(H, W * ratio)
        top, bottom = (H - ch) / 2, (H + ch) / 2
        if any(r["y"] < top or r["y"] + r["h"] > bottom for r in texts):
            out.append(name)
    return out


def cover_from_edges(video, duration, window_s=COVER_WINDOW_S, step=0.25):
    """Second with the highest edge density (text and detail) in the first `window_s` seconds."""
    import numpy as np

    w, h = 180, 320
    end = min(window_s, max(0.0, duration - 0.05))
    best, best_t = -1.0, 0.0
    t = 0.0
    while t <= end + 1e-6:
        raw = subprocess.run([bins.ffmpeg(), "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf", f"scale={w}:{h}",
                              "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        if len(raw) == w * h:
            g = np.frombuffer(raw, np.uint8).reshape(h, w).astype(np.float32)
            gx, gy = np.abs(np.diff(g, axis=1))[:-1, :], np.abs(np.diff(g, axis=0))[:, :-1]
            density = float(((gx + gy) > 40).mean())
            if density > best:
                best, best_t = density, t
        t += step
    return round(best_t, 3)


def write_covers(video, t, dest):
    p9 = os.path.join(dest, "cover_9x16.png")
    run([bins.ffmpeg(), "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-update", "1", p9])
    p34 = os.path.join(dest, "cover_grid_3x4.png")
    run([bins.ffmpeg(), "-v", "error", "-y", "-i", p9, "-vf", "crop='min(iw,ih*3/4)':'min(ih,iw*4/3)'", "-update", "1", p34])
    p11 = os.path.join(dest, "cover_grid_1x1.png")
    run([bins.ffmpeg(), "-v", "error", "-y", "-i", p9, "-vf", "crop='min(iw,ih)':'min(iw,ih)'", "-update", "1", p11])
    return [p9, p34, p11]


# ------------------------------------------------------------------ WhatsApp
def whatsapp_version(src, dst, info, limit_mb=WHATSAPP_MAX_MB):
    """720x1280 H.264 (+ AAC when the source has audio) under `limit_mb`. Returns the encoding used."""
    W, H = WHATSAPP_SIZE
    vf = f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    if info["audio_codec"] == "aac":
        audio = ["-c:a", "copy"]
    elif info["audio_codec"]:
        audio = ["-c:a", "aac", "-b:a", "128k"]
    else:
        audio = ["-an"]
    common = [bins.ffmpeg(), "-v", "error", "-y", "-i", src, "-map", "0:v:0", "-map", "0:a:0?", "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p",
              "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
    for crf in (24, 27, 30, 33):
        run(common + ["-preset", "slow", "-crf", str(crf)] + audio + ["-movflags", "+faststart", dst])
        if os.path.getsize(dst) / 1e6 <= limit_mb:
            return dict(crf=crf, audio=info["audio_codec"] and "aac")
    # last resort: a capped bitrate that fits, leaving room for the audio
    dur = max(info["duration_s"], 0.1)
    kbps = max(200, int(limit_mb * 8000 / dur * 0.9) - (160 if info["audio_codec"] else 0))
    run(common + ["-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{2 * kbps}k"]
        + (["-c:a", "aac", "-b:a", "128k"] if info["audio_codec"] else ["-an"]) + ["-movflags", "+faststart", dst])
    return dict(bitrate_kbps=kbps, audio=info["audio_codec"] and "aac")


# ------------------------------------------------------------------ caption
def caption_template(b, c):
    vg = c.get("voice_guide", {})
    tags = " ".join(vg.get("hashtags", [])) or "#Brand #City #Region"
    cta = vg.get("cta") or (b.get("cta") or {}).get("text") or "(call to action)"
    return f"""# Caption — {b['id']}

<!--
Write it in {c.get('language', 'the client language')}, following clients/{b['client']}/client.json voice_guide, then run deliver.py again.
Tone: {vg.get('tone') or c.get('voice') or '(see client.json)'}
Person: {vg.get('person') or '-'}
Use: {', '.join(vg.get('use', [])) or '-'}
Avoid: {', '.join(vg.get('avoid', [])) or '-'}
Emojis: {vg.get('emojis') or '-'}
Structure: hook (one line, under {HOOK_MAX} characters) · body (1-2 lines about what the video shows) · CTA · hashtags.
Every version is pasted as is into the post, hashtags included. No health claims; prices and offers only with dates.
-->

## Short
(hook + CTA + 3-7 hashtags)

{cta}

## Medium
(hook, 1-2 lines of body, CTA, 8-12 hashtags)

{cta}

## Booking
(the medium version + one clear line to ask for availability)

{cta}

## Hashtags
{tags}

## Alt text
(what the video shows, in at most {ALT_MAX} characters)
"""


def parse_caption(text):
    """{section title lower-cased: body} from '## Title' sections, HTML comments removed."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return {m.group(1).strip().lower(): m.group(2).strip()
            for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", text, re.S | re.M)}


def unfilled(body):
    return not body or any(line.strip().startswith("(") and line.strip().endswith(")") for line in body.splitlines())


def check_caption(sections, c):
    """(errors, warnings) for caption.md."""
    errors, warn = [], []
    cta = c.get("voice_guide", {}).get("cta", "")
    cta_key = re.sub(r"[^\w\s·]", "", cta).strip().lower()
    for key, name in VERSIONS:
        body = sections.get(key, "")
        if unfilled(body):
            errors.append(f'caption: the "{name}" version is missing or still has template placeholders')
            continue
        tags = re.findall(r"#\w+", body)
        hook = body.splitlines()[0]
        if len(body) > CAPTION_MAX:
            errors.append(f'caption "{name}": {len(body)} characters (Instagram allows {CAPTION_MAX})')
        if len(tags) > HASHTAG_LIMIT:
            errors.append(f'caption "{name}": {len(tags)} hashtags (Instagram allows {HASHTAG_LIMIT})')
        if len(hook) > HOOK_MAX:
            warn.append(f'caption "{name}": the hook is {len(hook)} characters; Instagram cuts at about {HOOK_MAX} before "more"')
        lo, hi = (3, 7) if key == "short" else (8, 12)
        if not lo <= len(tags) <= hi:
            warn.append(f'caption "{name}": {len(tags)} hashtags ({lo}-{hi} work best)')
        if cta_key and cta_key not in re.sub(r"[^\w\s·]", "", body).lower():
            warn.append(f'caption "{name}": the client\'s standard CTA ("{cta}") is not there')
    alt = sections.get("alt text", "")
    if unfilled(alt):
        errors.append("caption: the alt text is missing")
    elif len(alt) > ALT_MAX:
        warn.append(f"caption: alt text is {len(alt)} characters (keep it under {ALT_MAX})")
    return errors, warn


# ------------------------------------------------------------------ sheet
def asset_entries(b, c, d):
    out = []
    a = b.get("assets", {})
    items = [("photo", p) for p in a.get("photos", [])] + [("video", p) for p in a.get("videos", [])]
    items += [("video", v["file"]) for v in (b.get("material") or {}).get("videos", []) if v.get("file")]
    if a.get("music"):
        items.append(("music", a["music"]))
    if c.get("brand", {}).get("logo"):
        items.append(("logo", c["brand"]["logo"]))
    if b.get("reference"):
        items.append(("reference", b["reference"]))
    seen = set()
    for kind, p in items:
        if p in seen:
            continue
        seen.add(p)
        full = os.path.join(d, p)
        e = dict(kind=kind, path=p)
        if os.path.exists(full):
            e.update(sha256=sha256(full), size_mb=mb(full))
        else:
            e["missing"] = True
        out.append(e)
    return out


def verifier_verdict(out_dir, video):
    cache = os.path.join(out_dir, ".render-cache.json")
    if not os.path.exists(cache):
        return None
    try:
        data = briefs.load(cache)
    except ValueError:
        return None
    return next((e for v, e in data.items() if os.path.basename(v) == os.path.basename(video)), None)


def versions():
    v = dict(python=pyplatform.python_version())
    try:
        pkg = briefs.load(os.path.join(ROOT, "remotion-base", "package.json"))
        deps = {**pkg.get("devDependencies", {}), **pkg.get("dependencies", {})}
        v["remotion"] = deps.get("remotion")
    except (OSError, ValueError):
        v["remotion"] = None
    try:
        v["cutroom"] = briefs.load(os.path.join(ROOT, ".claude-plugin", "plugin.json")).get("version")
    except (OSError, ValueError):
        v["cutroom"] = None
    try:
        v["ffmpeg"] = run([bins.ffmpeg(), "-version"]).splitlines()[0].split(" ")[2]
    except (SystemExit, IndexError, OSError):
        v["ffmpeg"] = None
    return v


def checklist(b, c, sheet, claims_found, cap_errors):
    ok = lambda good: "[x]" if good else "[ ]"  # noqa: E731
    verdict = (sheet.get("verifier") or {}).get("verify")
    severe = [f for f in claims_found if f["severity"] == "severe"]
    contact = (b.get("cta") or {}).get("contact", "")
    client_contacts = [str(v) for v in c.get("contact", {}).values()]
    contact_ok = bool(contact) and contact in client_contacts
    music = b.get("assets", {}).get("music")
    if music:
        e, _ = briefs.music_licence(briefs.client_dir(b["client"]), music)
        music_line = f"{ok(not e)} Music licence: {music} — " + ("licence on file" if not e else "; ".join(e))
    else:
        music_line = ("[ ] Music: the video has no music. If music is added in Instagram, business accounts may not have the "
                      "commercial library: pick a track licensed for commercial use")
    files = "\n".join(f"- `{f}` ({m} MB)" for f, m in sheet["files"].items())
    clipped = sheet.get("cover", {}).get("text_cut_in_grid") or []
    cut = f" — the {' and '.join(clipped)} crop cuts on-screen text" if clipped else ""
    return f"""# Delivery — {b['id']}  ({sheet['date']})

## Files
{files}

## Before publishing
- {ok(verdict == 'pass')} Verifier verdict of the final render: {verdict or 'unknown (no .render-cache.json entry)'}
- {ok(not severe)} Claims reviewed (health, guarantees, prices): {len(severe)} severe, {len(claims_found) - len(severe)} other — see sheet.json
- {ok(not cap_errors)} Caption: three versions and alt text complete{'' if not cap_errors else ' — ' + '; '.join(cap_errors)}
- {ok(contact_ok)} Contact data on screen: "{contact or '(none)'}"{' matches client.json' if contact_ok else ' — check it against client.json contact'}
- [ ] People: everyone recognisable in the video has given permission; nobody is named or tagged without it
- [ ] Cover legible in the grid: upload `cover_9x16.png` as the cover and check the text still reads in `cover_grid_3x4.png` and `cover_grid_1x1.png`{cut}
- {music_line}
- [ ] Nothing on screen belongs to another place (stock footage must not pass for the client's premises)
- [ ] Watched once on a phone, sound on and off; `whatsapp_720p.mp4` sent to the client for a last look
"""


# ------------------------------------------------------------------ main
def build(brief_path, cover_time=None):
    b = briefs.load(brief_path)
    d = briefs.client_dir(b["client"])
    c = briefs.load(os.path.join(d, "client.json"))
    if not b.get("composition"):
        raise SystemExit("the brief has no composition id — nothing has been rendered yet")
    out_dir = os.path.join(out_root(), b["id"])
    video = os.path.join(out_dir, f"{b['composition']}.mp4")
    if not os.path.exists(video):
        raise SystemExit(f"no final render at {briefs.rel(video)} — run: python3 tools/pipeline.py render {brief_path} --final")
    dest = os.path.join(deliveries_root(), b["id"])
    ensure_writable(dest)
    os.makedirs(dest, exist_ok=True)
    # a rebuild starts clean: only the caption (written by hand) survives, so no stale video or cover lingers
    for f in os.listdir(dest):
        full = os.path.join(dest, f)
        if os.path.isfile(full) and f != "caption.md":
            os.remove(full)
    delivery = b.get("delivery") or {}
    cap = os.path.join(ROOT, delivery["caption"]) if delivery.get("caption") else os.path.join(dest, "caption.md")
    if not os.path.exists(cap):
        ensure_writable(cap)
        os.makedirs(os.path.dirname(cap), exist_ok=True)
        with open(cap, "w", encoding="utf-8") as f:
            f.write(caption_template(b, c))
        print(f"wrote the template {briefs.rel(cap)} — write the caption (client.json voice_guide) and run deliver.py again")
        return 1

    in_package = os.path.join(dest, "caption.md")
    if os.path.normcase(os.path.realpath(cap)) != os.path.normcase(os.path.realpath(in_package)):
        shutil.copy2(cap, in_package)  # the package always carries its caption

    info = probe(video)
    # 1) cover
    if cover_time is None:
        cover_time = delivery.get("cover_time")
    how = "given"
    if cover_time is None:
        cover_time = cover_from_track(os.path.splitext(video)[0] + ".track.json")
        how = "track: most visible text"
        if cover_time is None:
            cover_time = cover_from_edges(video, info["duration_s"])
            how = "edge density"
    cover_time = max(0.0, min(float(cover_time), max(0.0, info["duration_s"] - 0.05)))
    shutil.copy2(video, os.path.join(dest, os.path.basename(video)))
    write_covers(video, cover_time, dest)
    clipped = clipped_in_grid(os.path.splitext(video)[0] + ".track.json", cover_time)
    # 2) WhatsApp
    wa = os.path.join(dest, "whatsapp_720p.mp4")
    wa_enc = whatsapp_version(video, wa, info)
    # 3) caption and claims
    with open(cap, encoding="utf-8") as f:
        cap_text = f.read()
    sections = parse_caption(cap_text)
    cap_errors, cap_warn = check_caption(sections, c)
    lang = c.get("language") or "es-AR"
    found = []
    for key, body in sections.items():
        found += claims.check(body, lang, f"caption.md › {key}")
    found += briefs.copy_claims(b, c)
    found_d = [f.to_dict() for f in found]
    severe = [f for f in found_d if f["severity"] == "severe"]
    verdict = verifier_verdict(out_dir, video)
    errors = list(cap_errors) + [f'severe claim: "{f["phrase"]}" ({f["source"]})' for f in severe]
    warn = list(cap_warn) + [f'{f["severity"]} claim: "{f["phrase"]}" ({f["source"]})' for f in found_d if f["severity"] != "severe"]
    for crop in clipped:
        warn.append(f"cover: the {crop} grid crop cuts on-screen text — check cover_grid_{crop}.png or pick another --cover-time")
    if not verdict:
        warn.append("no verifier verdict found for the final render (.render-cache.json)")
    elif verdict.get("verify") != "pass":
        errors.append(f"the final render's verification is {verdict.get('verify')!r}, not 'pass'")
    if os.path.getsize(wa) / 1e6 > WHATSAPP_MAX_MB:
        errors.append(f"whatsapp_720p.mp4 is {mb(wa)} MB (over {WHATSAPP_MAX_MB:g} MB)")
    # 4) sheet + checklist
    files = {f: mb(os.path.join(dest, f)) for f in sorted(os.listdir(dest))
             if os.path.isfile(os.path.join(dest, f)) and f not in ("sheet.json", "CHECKLIST.md")}
    sheet = dict(
        id=b["id"], client=b["client"], platform=b.get("platform"), format=b.get("format"), composition=b["composition"],
        date=datetime.date.today().isoformat(), video=dict(source=briefs.rel(video), **info),
        cover=dict(time_s=cover_time, chosen_by=how, text_cut_in_grid=clipped), whatsapp=dict(**wa_enc, **probe(wa)),
        caption=dict(path=briefs.rel(cap), sections=list(sections), errors=cap_errors, warnings=cap_warn),
        on_screen_texts=[dict(source=s, text=t) for s, t in briefs.on_screen_copy(b)],
        assets=asset_entries(b, c, d), versions=versions(), verifier=verdict,
        claims=found_d, errors=errors, warnings=warn, ready_to_publish=not errors,
        files={f: dict(size_mb=m, sha256=sha256(os.path.join(dest, f))) for f, m in files.items()},
    )
    with open(os.path.join(dest, "sheet.json"), "w", encoding="utf-8") as f:
        json.dump(sheet, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(dest, "CHECKLIST.md"), "w", encoding="utf-8") as f:
        f.write(checklist(b, c, dict(sheet, files=files), found_d, cap_errors))

    print(f"package: {briefs.rel(dest)}")
    for name, m in files.items():
        print(f"  {name:32} {m:7.2f} MB")
    print(f"  {'sheet.json':32}\n  {'CHECKLIST.md':32}")
    n = claims.summary(found)
    print(f"cover at {cover_time:.2f}s ({how}) | caption: {len(cap_errors)} errors · {len(cap_warn)} warnings | "
          f"claims: {n['severe']} severe · {n['medium']} medium · {n['low']} low | verifier: {(verdict or {}).get('verify', 'unknown')}")
    for e in errors:
        print(f"  ERROR  {e}")
    for w in warn:
        print(f"  WARN   {w}")
    print("READY TO PUBLISH (after the manual items in CHECKLIST.md)" if not errors else "FIX BEFORE PUBLISHING")
    return 1 if errors else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief", help="clients/<slug>/briefs/<id>.json")
    ap.add_argument("--cover-time", type=float, help="second of the cover frame (default: delivery.cover_time, else automatic)")
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    return build(a.brief, a.cover_time)


if __name__ == "__main__":
    sys.exit(main())
