#!/usr/bin/env python3
"""Calibration tests for verify.py and brief.py: synthetic good and bad cases with known verdicts.

    python3 -m pytest tools/tests -q
    python3 tools/tests/test_verify.py          # same cases, no pytest needed

Each synthetic video is written once and analysed once: the runs share an analysis cache
(CUTROOM_ANALYSIS_CACHE), so further runs on the same file only redo the platform checks.
"""
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
VERIFY = os.path.join(TOOLS, "verify.py")
BRIEF = os.path.join(TOOLS, "brief.py")
sys.path.insert(0, TOOLS)

from quality.bins import ffmpeg  # noqa: E402

W, H, FPS = 1080, 1920, 30


# ------------------------------------------------------------------ synthetic material
def write_video(path, frame_fn, n, audio=None, size=(W, H), fps=FPS, extra=()):
    raw = path + ".raw.mp4"
    vw = cv2.VideoWriter(raw, cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    for i in range(n):
        vw.write(frame_fn(i))
    vw.release()
    cmd = [ffmpeg(), "-v", "error", "-y", "-i", raw]
    if audio:
        cmd += ["-f", "lavfi", "-i", audio, "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", *extra, path]
    subprocess.run(cmd, check=True)
    os.remove(raw)


def canvas(color=(239, 244, 245), size=(W, H)):
    f = np.zeros((size[1], size[0], 3), np.uint8)
    f[:] = color
    return f


def ease(t):
    t = min(max(t, 0), 1)
    return 1 - (1 - t) ** 3


def good(i):
    """An object arrives, rests, moves again, then a long still CTA. Uneven beats."""
    f = canvas()
    t = i / FPS
    x = 140 + 600 * ease(t / 0.8) if t < 3 else 740 - 500 * ease((t - 3) / 0.6)
    y = 900 if t < 5 else 900 - 200 * ease((t - 5) / 1.2)
    cv2.rectangle(f, (int(x), int(y)), (int(x) + 260, int(y) + 160), (82, 74, 140), -1)
    if t > 6.5:
        cv2.putText(f, "+54 9 11 0000-0000", (170, 1200), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (70, 96, 79), 5)
    return f


def constant_motion(i):
    f = canvas()
    cv2.circle(f, (540 + int(380 * np.sin(i / 6)), 960 + int(500 * np.cos(i / 9))), 120, (60, 60, 160), -1)
    return f


def slideshow(i):
    colors = [(60, 60, 200), (200, 60, 60), (60, 160, 60), (40, 40, 40), (200, 200, 200)]
    f = canvas(colors[(i // 60) % 5])
    cv2.putText(f, f"slide {i // 60 + 1}", (300, 960), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 6)
    return f


def wide(i):
    f = canvas(size=(640, 360))
    cv2.rectangle(f, (40 + 4 * i, 140), (140 + 4 * i, 220), (82, 74, 140), -1)
    return f


def moves(profiles, move_frames=24, rest_frames=18, tail=90):
    """A box making one move per easing profile, separated by rests, then a long still end."""
    period = move_frames + rest_frames
    n = len(profiles) * period + tail

    def frame(i):
        k, r = divmod(i, period)
        if k >= len(profiles):
            pos = len(profiles)
        elif r < move_frames:
            pos = k + profiles[k](r / (move_frames - 1))
        else:
            pos = k + 1
        f = canvas()
        x = 80 + pos * 150
        cv2.rectangle(f, (int(x), 860), (int(x) + 200, 1060), (82, 74, 140), -1)
        return f

    return frame, n


linear = lambda t: t  # noqa: E731
snap = lambda t: 1 - (1 - t) ** 4  # noqa: E731
slow_in = lambda t: t ** 3  # noqa: E731


def rec(f, i, x, y, w=300, h=200, o=1.0, k="subject", **kw):
    return dict(f=f, lf=f, id=i, k=k, x=x, y=y, w=w, h=h, o=o, inFrame=kw.get("inFrame", False), blurred=kw.get("blurred", False))


BEATS = [{"f": 0, "name": "a"}, {"f": 150, "name": "b"}]


class Env:
    """Temp folder with lazily built material shared by all cases."""

    def __init__(self):
        self.d = tempfile.mkdtemp(prefix="cutroom-tests-")
        self.env = {**os.environ, "CUTROOM_ANALYSIS_CACHE": os.path.join(self.d, "cache")}
        self._made = {}

    def close(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def path(self, name):
        return os.path.join(self.d, name)

    def video(self, name, frame_fn, n, **kw):
        p = self.path(name)
        if name not in self._made:
            write_video(p, frame_fn, n, **kw)
            self._made[name] = p
        return p

    def good(self):
        return self.video("good.mp4", good, 300)

    def track(self, name, records, beats=BEATS):
        p = self.path(name)
        json.dump(dict(width=W, height=H, fps=FPS, scale=1, beats=beats, records=records), open(p, "w"))
        return p

    def image(self, name, size, fmt=None, **save):
        from PIL import Image

        p = self.path(name)
        if name not in self._made:
            Image.new("RGB", size, (240, 240, 235)).save(p, fmt, **save)
            self._made[name] = p
        return p

    def run(self, video, *extra, fmt="story", platform="instagram", env=None):
        out = self.path(os.path.basename(video.rstrip("/")) + f".{len(os.listdir(self.d))}.json")
        r = subprocess.run([sys.executable, VERIFY, video, "--platform", platform, "--format", fmt, "--json", out, *extra],
                           capture_output=True, text=True, env={**self.env, **(env or {})})
        if not os.path.exists(out):
            raise RuntimeError(r.stderr or r.stdout)
        rep = json.load(open(out))
        os.remove(out)
        return r.returncode, {(x["level"], x["check"]) for x in rep["report"]}, rep

    def brief(self, *args, clients):
        r = subprocess.run([sys.executable, BRIEF, *args], capture_output=True, text=True, env={**self.env, "CUTROOM_CLIENTS": clients})
        return r.returncode, r.stdout + r.stderr


CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn

    return deco


def msgs(rep, level=None, check=None):
    return [x["msg"] for x in rep["report"] if (level is None or x["level"] == level) and (check is None or x["check"] == check)]


# ------------------------------------------------------------------ core checks (instagram story)
@case("good: no FAIL")
def _(e):
    code, found, _ = e.run(e.good())
    return code == 0, found


@case("constant motion: rhythm/ending FAIL")
def _(e):
    code, found, _ = e.run(e.video("constant.mp4", constant_motion, 300))
    return code == 1 and (("FAIL", "rhythm") in found or ("FAIL", "ending") in found), found


@case("slideshow: cuts FAIL")
def _(e):
    code, found, _ = e.run(e.video("slideshow.mp4", slideshow, 300))
    return ("FAIL", "cuts") in found, found


@case("clipping audio: audio FAIL")
def _(e):
    code, found, _ = e.run(e.video("loud.mp4", good, 300, audio="sine=f=440:sample_rate=48000,volume=8"))
    return ("FAIL", "audio") in found, found


# ------------------------------------------------------------------ tracking
@case("scene replaced: continuity FAIL")
def _(e):
    t = e.track("replaced.json", [rec(f, "A", 300, 800) for f in range(0, 150)] + [rec(f, "B", 300, 800) for f in range(150, 300)])
    code, found, _ = e.run(e.good(), "--track", t)
    return ("FAIL", "continuity") in found, found


@case("scene carried: no continuity FAIL")
def _(e):
    t = e.track("carried.json", [rec(f, "A", 200 + f, 800) for f in range(0, 300)])
    code, found, _ = e.run(e.good(), "--track", t)
    return ("FAIL", "continuity") not in found, found


@case("text in top UI band: safe FAIL")
def _(e):
    t = e.track("unsafe.json", [rec(f, "A", 200, 800) for f in range(300)] + [rec(f, "title", 200, 120, 600, 90, k="text") for f in range(300)])
    code, found, _ = e.run(e.good(), "--track", t)
    return ("FAIL", "safe") in found, found


@case("fast without blur: blur FAIL")
def _(e):
    t = e.track("fast.json", [rec(f, "A", 100 + (f % 10) * 90, 800) for f in range(300)])
    code, found, _ = e.run(e.good(), "--track", t)
    return ("FAIL", "blur") in found, found


@case("fast with blur: no blur FAIL")
def _(e):
    t = e.track("fast_blurred.json", [rec(f, "A", 100 + (f % 10) * 90, 800, blurred=True) for f in range(300)])
    code, found, _ = e.run(e.good(), "--track", t)
    return ("FAIL", "blur") not in found, found


@case("subject off frame: framing FAIL")
def _(e):
    t = e.track("offframe.json", [rec(f, "A", 900, 800, inFrame=True) for f in range(300)])
    code, found, _ = e.run(e.good(), "--track", t)
    return ("FAIL", "framing") in found, found


# ------------------------------------------------------------------ beat kinds
@case("beat kinds: explicit kind wins over the name, names are the fallback")
def _(e):
    from quality.track import beat_kind

    got = [beat_kind(b) for b in ({"name": "hard cut"}, {"name": "hold on logo"}, {"name": "rest"}, {"name": "push in"},
                                  {"name": "hard cut", "kind": "move"}, {"name": "x", "kind": "hold"}, {"name": "cut", "kind": "bogus"})]
    want = ["cut", "hold", "rest", "move", "move", "hold", "cut"]
    return got == want, set(got)


@case("beat kind cut: a replaced scene at an explicit cut is not a continuity FAIL")
def _(e):
    recs = [rec(f, "A", 300, 800) for f in range(0, 150)] + [rec(f, "B", 300, 800) for f in range(150, 300)]
    t = e.track("kind_cut.json", recs, [{"f": 0, "name": "a", "kind": "move"}, {"f": 150, "name": "b", "kind": "cut"}])
    code, found, rep = e.run(e.good(), "--track", t)
    return ("FAIL", "continuity") not in found and rep["metrics"].get("beat_kinds") == "explicit", found


@case("beat kind move: a beat named 'cut' but marked move is checked")
def _(e):
    recs = [rec(f, "A", 300, 800) for f in range(0, 150)] + [rec(f, "B", 300, 800) for f in range(150, 300)]
    t = e.track("kind_move.json", recs, [{"f": 0, "name": "a", "kind": "move"}, {"f": 150, "name": "hard cut", "kind": "move"}])
    code, found, _ = e.run(e.good(), "--track", t)
    return ("FAIL", "continuity") in found, found


@case("beat kind rest: rests are left out of the carried share")
def _(e):
    t = e.track("kind_rest.json", [rec(f, "A", 300, 800) for f in range(300)], [{"f": 0, "name": "a"}, {"f": 150, "name": "b", "kind": "rest"}])
    code, found, rep = e.run(e.good(), "--track", t)
    return rep["metrics"].get("carried_boundaries", "").startswith("0/0") and ("WARN", "continuity") not in found, found


# ------------------------------------------------------------------ motion curves
@case("all moves on one linear curve: curves WARN")
def _(e):
    fr, n = moves([linear] * 5)
    code, found, _ = e.run(e.video("linear.mp4", fr, n))
    return ("WARN", "curves") in found, found


@case("mixed curves: no curves WARN")
def _(e):
    fr, n = moves([snap, slow_in, snap, linear, slow_in])
    code, found, rep = e.run(e.video("mixed.mp4", fr, n))
    return ("WARN", "curves") not in found, found | {("t80_iqr", str(rep["metrics"].get("t80_iqr")))}


# ------------------------------------------------------------------ reference comparison
@case("same as reference: no reference WARN")
def _(e):
    code, found, _ = e.run(e.good(), "--ref", e.good())
    return ("WARN", "reference") not in found, found


@case("far from reference: reference WARN")
def _(e):
    code, found, _ = e.run(e.good(), "--ref", e.video("slideshow.mp4", slideshow, 300))
    return ("WARN", "reference") in found, found


# ------------------------------------------------------------------ instagram technical
@case("15 fps reel: tech FAIL")
def _(e):
    v = e.video("lowfps.mp4", lambda i: good(i * 2), 150, fps=15, extra=("-r", "15"))
    code, found, _ = e.run(v, fmt="reel")
    return ("FAIL", "tech") in found, found


@case("2 s story: tech FAIL")
def _(e):
    code, found, _ = e.run(e.video("short.mp4", good, 60), fmt="story")
    return ("FAIL", "tech") in found, found


@case("moov at the end: tech WARN")
def _(e):
    code, found, rep = e.run(e.good(), fmt="reel")
    return any("moov" in m for m in msgs(rep)), found


@case("2:1 PNG feed image: ratio FAIL + format WARN")
def _(e):
    code, found, rep = e.run(e.image("wide.png", (2000, 1000)), fmt="feed_image")
    return code == 1 and any("JPEG" in m for m in msgs(rep)), found


@case("clean 1080x1350 JPEG: no FAIL/WARN")
def _(e):
    code, found, _ = e.run(e.image("ok.jpg", (1080, 1350), quality=90), fmt="feed_image")
    return not any(lv in ("FAIL", "WARN") for lv, _ in found), found


@case("carousel with mixed ratios: carousel FAIL")
def _(e):
    car = e.path("carousel")
    os.makedirs(car, exist_ok=True)
    e.image("carousel/1.jpg", (1080, 1350))
    e.image("carousel/2.jpg", (1080, 1080))
    code, found, _ = e.run(car + "/", fmt="carousel")
    return ("FAIL", "carousel") in found, found


# ------------------------------------------------------------------ dated specs
@case("specs reviewed today: no specs WARN")
def _(e):
    code, found, rep = e.run(e.image("ok.jpg", (1080, 1350), quality=90), fmt="feed_image")
    return ("WARN", "specs") not in found and rep["metrics"].get("specs_reviewed"), found


@case("stale specs (old reviewed date): specs WARN asking to re-check")
def _(e):
    from quality.platforms import common

    stale = e.path("stale_specs")
    if not os.path.exists(stale):
        shutil.copytree(common.SPECS_DIR, stale)
        for f in os.listdir(stale):
            s = json.load(open(os.path.join(stale, f)))
            s["reviewed"] = "2020-01-01"
            json.dump(s, open(os.path.join(stale, f), "w"))
    code, found, rep = e.run(e.image("ok.jpg", (1080, 1350), quality=90), fmt="feed_image", env={"CUTROOM_SPECS_DIR": stale})
    warned = any("re-check the official specs" in m for m in msgs(rep, "WARN", "specs"))
    return warned and code == 0, found


@case("spec age: 181 days is stale, 180 is not")
def _(e):
    from quality.platforms import common
    from quality.report import Report

    spec = {**common.load_spec("tiktok"), "reviewed": "2026-01-01"}
    r1, r2 = Report(), Report()
    common.check_reviewed(spec, r1, today=datetime.date(2026, 1, 1) + datetime.timedelta(days=180))
    common.check_reviewed(spec, r2, today=datetime.date(2026, 1, 1) + datetime.timedelta(days=181))
    return not r1.items and [i["check"] for i in r2.items] == ["specs"], {(i["level"], i["check"]) for i in r2.items}


@case("every spec file has a reviewed date, sources and the formats its module uses")
def _(e):
    from quality.platforms import PLATFORMS

    bad = set()
    for name, mod in PLATFORMS.items():
        s = mod.SPEC
        try:
            datetime.date.fromisoformat(s["reviewed"])
        except (KeyError, ValueError):
            bad.add((name, "reviewed"))
        if not s.get("sources") or not all(x.get("url", "").startswith("https://") for x in s["sources"]):
            bad.add((name, "sources"))
        if not s.get("formats") or mod.FORMATS is not s["formats"]:
            bad.add((name, "formats"))
    return not bad, bad


# ------------------------------------------------------------------ tiktok
@case("tiktok: good 9:16 video, auto format → video, no FAIL")
def _(e):
    code, found, rep = e.run(e.good(), platform="tiktok", fmt="auto")
    return code == 0 and rep["metrics"].get("platform/format") == "tiktok / video", found


@case("tiktok ad: bitrate under 516 kbps is a tech FAIL")
def _(e):
    code, found, rep = e.run(e.good(), platform="tiktok", fmt="ad")
    return any("kbps" in m for m in msgs(rep, "FAIL", "tech")), found


@case("tiktok: text under the action buttons is a safe FAIL")
def _(e):
    t = e.track("tt_buttons.json", [rec(f, "A", 200 + f, 800) for f in range(300)] + [rec(f, "like", 940, 1000, 120, 80, k="text") for f in range(300)])
    code, found, _ = e.run(e.good(), "--track", t, platform="tiktok", fmt="video")
    return ("FAIL", "safe") in found, found


@case("tiktok: text where a long caption reaches is a safe WARN, not a FAIL")
def _(e):
    t = e.track("tt_caption.json", [rec(f, "A", 200 + f, 800) for f in range(300)] + [rec(f, "cta", 200, 1300, 500, 80, k="text") for f in range(300)])
    code, found, _ = e.run(e.good(), "--track", t, platform="tiktok", fmt="video")
    return ("WARN", "safe") in found and ("FAIL", "safe") not in found, found


@case("tiktok: an image is a format FAIL")
def _(e):
    code, found, _ = e.run(e.image("ok.jpg", (1080, 1350), quality=90), platform="tiktok", fmt="auto")
    return ("FAIL", "format") in found, found


@case("tiktok: unknown format is refused with the list")
def _(e):
    r = subprocess.run([sys.executable, VERIFY, e.good(), "--platform", "tiktok", "--format", "feed_image"], capture_output=True, text=True, env=e.env)
    return r.returncode != 0 and "video, ad" in r.stderr, {r.stderr.strip()}


# ------------------------------------------------------------------ youtube shorts
@case("youtube_shorts: good 9:16 video, auto format → short, no FAIL")
def _(e):
    code, found, rep = e.run(e.good(), platform="youtube_shorts", fmt="auto")
    return code == 0 and rep["metrics"].get("platform/format") == "youtube_shorts / short", found


@case("youtube_shorts: 16:9 is a tech FAIL (wider than square)")
def _(e):
    code, found, rep = e.run(e.video("wide.mp4", wide, 60, size=(640, 360)), platform="youtube_shorts", fmt="auto")
    return any("square or vertical" in m for m in msgs(rep, "FAIL", "tech")), found


@case("youtube_shorts: over 3 minutes is a tech FAIL")
def _(e):
    from quality.platforms import common, youtube_shorts
    from quality.report import Report

    m = dict(container="mov,mp4,m4a,3gp,3g2,mj2", vcodec="h264", pix_fmt="yuv420p", field_order="progressive", fps=30.0, w=1080, h=1920,
             vbitrate=8_000_000, size_bytes=200_000_000, duration=181.0, audio=False, moov_first=True, keyframe_interval=1.0, color_primaries="bt709")
    r = Report()
    common.tech_video(m, youtube_shorts.SPEC["video"], youtube_shorts.FORMATS["short"], r, "YouTube Shorts")
    ok181 = any("duration" in i["msg"] for i in r.items if i["level"] == "FAIL")
    r2 = Report()
    common.tech_video({**m, "duration": 179.0}, youtube_shorts.SPEC["video"], youtube_shorts.FORMATS["short"], r2, "YouTube Shorts")
    return ok181 and not r2.failed, {(i["level"], i["msg"]) for i in r.items + r2.items}


@case("youtube_shorts: text in the title / channel area is a safe FAIL")
def _(e):
    t = e.track("yt_bottom.json", [rec(f, "A", 200 + f, 800) for f in range(300)] + [rec(f, "cta", 200, 1500, 500, 80, k="text") for f in range(300)])
    code, found, _ = e.run(e.good(), "--track", t, platform="youtube_shorts", fmt="short")
    return ("FAIL", "safe") in found, found


# ------------------------------------------------------------------ binaries
@case("FFMPEG / FFPROBE env vars choose the binaries")
def _(e):
    from quality import bins

    old = {k: os.environ.pop(k, None) for k in ("FFMPEG", "FFPROBE")}
    try:
        default = (bins.ffmpeg(), bins.ffprobe())
        os.environ.update(FFMPEG="/opt/ff/ffmpeg", FFPROBE="/opt/ff/ffprobe")
        custom = (bins.ffmpeg(), bins.ffprobe())
    finally:
        for k, v in old.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
    return default == ("ffmpeg", "ffprobe") and custom == ("/opt/ff/ffmpeg", "/opt/ff/ffprobe"), {default, custom}


# ------------------------------------------------------------------ briefs and music
def _client(e):
    clients = e.path("clients")
    if not os.path.exists(os.path.join(clients, "acme", "client.json")):
        code, out = e.brief("client", "new", "acme", "--name", "Acme Co", clients=clients)
        assert code == 0, out
        c = json.load(open(os.path.join(clients, "acme", "client.json")))
        c["brand"]["taglines"] = ["Fast · Fair"]
        json.dump(c, open(os.path.join(clients, "acme", "client.json"), "w"))
    return clients


@case("brief: tiktok brief with a tiktok format is accepted; an instagram format is an ERROR")
def _(e):
    clients = _client(e)
    code_new, out_new = e.brief("new", "acme", "tt-promo", "--platform", "tiktok", "--format", "video", clients=clients)
    path = os.path.join(clients, "acme", "briefs", "tt-promo.json")
    b = json.load(open(path))
    b["format"] = "reel"
    json.dump(b, open(path, "w"))
    code_bad, out_bad = e.brief("check", path, clients=clients)
    code_refused, out_refused = e.brief("new", "acme", "yt", "--platform", "youtube_shorts", "--format", "story", clients=clients)
    ok = code_new == 0 and "What is the piece for?" in out_new and code_bad == 1 and "not a tiktok format" in out_bad and code_refused != 0
    return ok, {out_new.strip()[-80:], out_bad.strip()[-120:], out_refused.strip()[-80:]}


@case("brief: music needs a licence (sidecar file or LIBRARY.json entry); `brief.py music` lists the library")
def _(e):
    clients = _client(e)
    d = os.path.join(clients, "acme")
    e.brief("new", "acme", "music-promo", "--format", "reel", clients=clients)
    path = os.path.join(d, "briefs", "music-promo.json")
    b = json.load(open(path))
    b["assets"]["music"] = "assets/music/bed.mp3"
    json.dump(b, open(path, "w"))
    open(os.path.join(d, "assets", "music", "bed.mp3"), "wb").write(b"\0")
    code_none, out_none = e.brief("check", path, clients=clients)
    json.dump({"tracks": [{"title": "Bed", "file": "bed.mp3", "licence": "CC0", "source": "https://example.org/bed", "mood": ["calm"], "bpm": 92}]},
              open(os.path.join(d, "assets", "music", "LIBRARY.json"), "w"))
    code_lib, out_lib = e.brief("check", path, clients=clients)
    code_ls, out_ls = e.brief("music", "acme", clients=clients)
    json.dump({"tracks": [{"title": "Bed", "file": "bed.mp3"}]}, open(os.path.join(d, "assets", "music", "LIBRARY.json"), "w"))
    code_badlib, out_badlib = e.brief("music", "acme", clients=clients)
    ok = (code_none == 1 and "no licence" in out_none and code_lib == 0 and "ERROR" not in out_lib
          and code_ls == 0 and "Bed" in out_ls and "92 bpm" in out_ls and code_badlib == 1 and "licence" in out_badlib)
    return ok, {out_none.strip()[-100:], out_lib.strip()[-100:], out_ls.strip()[-100:], out_badlib.strip()[-100:]}


@case("brief: client ts exports CLIENT (name, taglines)")
def _(e):
    clients = _client(e)
    out = e.path("brand.ts")
    code, txt = e.brief("client", "ts", "acme", "--out", out, clients=clients)
    ts = open(out).read() if os.path.exists(out) else ""
    return code == 0 and 'export const CLIENT = {"name": "Acme Co", "taglines": ["Fast · Fair"]} as const;' in ts, {txt.strip()}


# ------------------------------------------------------------------ runners
try:
    import pytest
except ImportError:  # the script runner below needs no pytest
    pytest = None

if pytest:
    @pytest.fixture(scope="module")
    def env():
        e = Env()
        yield e
        e.close()

    @pytest.mark.parametrize("fn", [fn for _, fn in CASES], ids=[name for name, _ in CASES])
    def test_case(env, fn):
        passed, found = fn(env)
        assert passed, f"got {sorted(map(str, found))}"


def main():
    e = Env()
    ok = True
    try:
        for name, fn in CASES:
            try:
                passed, found = fn(e)
            except Exception as ex:  # report and continue
                passed, found = False, {f"{type(ex).__name__}: {ex}"}
            print(f"{'ok  ' if passed else 'FAIL'}  {name}" + ("" if passed else f"   got {sorted(map(str, found))}"))
            ok &= bool(passed)
    finally:
        e.close()
    print("\nall passed" if ok else "\nsome cases failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
