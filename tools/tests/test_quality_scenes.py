"""Scene changes and picture integrity on real (synthetic) video files.

Slideshows of still "photos" — joined by dissolves or by hard cuts — must fail the pixel continuity
check; the same photos pushed into each other must pass. Black gaps and letterboxing must be found.
Videos are small (540x960) and analysed once per module; the full verifier runs on one of them.

    python3 -m pytest tools/tests/test_quality_scenes.py -q
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import cv2
import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)

from quality import integrity, motion  # noqa: E402
from quality.report import Report  # noqa: E402
from quality.bins import ffmpeg  # noqa: E402

SW, SH, FPS = 540, 960, 30
HOLD, TRANSITION, PHOTOS = 66, 14, 4  # 2.2 s per photo, ~0.47 s transitions


def write_video(path, frame_fn, n):
    """Frames piped straight into x264 (ultrafast): no intermediate file."""
    p = subprocess.Popen([ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{SW}x{SH}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(np.ascontiguousarray(frame_fn(i)).tobytes())
    p.stdin.close()
    assert p.wait() == 0


def photo(seed):
    """A photo-like still: smooth colour fields, a horizon, some texture and shapes."""
    rng = np.random.default_rng(seed)
    small = rng.integers(0, 256, (12, 7, 3), dtype=np.uint8)
    img = cv2.resize(small, (SW, SH), interpolation=cv2.INTER_CUBIC)
    img = cv2.add(img, rng.integers(0, 40, (SH, SW, 3), dtype=np.uint8))
    y = int(rng.integers(300, 700))
    img[y:] = (img[y:] * 0.6).astype(np.uint8)
    for _ in range(6):
        c = tuple(int(v) for v in rng.integers(0, 256, 3))
        cv2.circle(img, (int(rng.integers(0, SW)), int(rng.integers(0, SH))), int(rng.integers(30, 140)), c, -1)
    return cv2.GaussianBlur(img, (5, 5), 0)


PICS = [photo(s) for s in range(PHOTOS)]


def slideshow(mode):
    period = HOLD + TRANSITION
    n = PHOTOS * period - TRANSITION + 45  # last photo held a little longer

    def frame(i):
        k, r = divmod(i, period)
        if k >= PHOTOS - 1:
            return PICS[-1]
        a, b = PICS[k], PICS[k + 1]
        if r < HOLD:
            return a
        t = (r - HOLD + 1) / TRANSITION
        if mode == "cut":
            return b
        if mode == "dissolve":
            return cv2.addWeighted(a, 1 - t, b, t, 0)
        off = int(SW * (1 - (1 - t) ** 3))  # push: the next photo slides in and shoves the current one out
        out = np.empty_like(a)
        out[:, :SW - off] = a[:, off:]
        out[:, SW - off:] = b[:, :off]
        return out

    return frame, n


def letterboxed_with_gap(i):
    f = np.zeros((SH, SW, 3), np.uint8)
    if 60 <= i < 66:  # 0.2 s black gap in the middle
        return f
    f[80:SH - 80] = PICS[0][80:SH - 80]
    x = 60 + 4 * min(i, 15)  # a short move, then still (keeps the optical flow cheap)
    cv2.rectangle(f, (x, 400), (x + 80, 480), (240, 240, 240), -1)
    return f


def dark_typography(i):
    """A typographic piece on #0a0a0a: centred lines that type on and drift — dark margins, no bars."""
    f = np.full((SH, SW, 3), 10, np.uint8)
    words = ("AGUA", "TERMAL", "SIN APURO")
    for k, word in enumerate(words):
        shown = word[:max(0, min(len(word), (i - 10 * k) // 3))]
        if shown:
            size = cv2.getTextSize(shown, cv2.FONT_HERSHEY_DUPLEX, 2.0, 3)[0]
            y = 400 + 90 * k + (i % 40) // 4
            cv2.putText(f, shown, ((SW - size[0]) // 2, y), cv2.FONT_HERSHEY_DUPLEX, 2.0, (235, 235, 235), 3, cv2.LINE_AA)
    return f


@pytest.fixture(scope="module")
def vids():
    d = tempfile.mkdtemp(prefix="cutroom-scenes-")
    old = os.environ.get("CUTROOM_ANALYSIS_CACHE")
    os.environ["CUTROOM_ANALYSIS_CACHE"] = os.path.join(d, "cache")  # the CLI test reuses the in-process analysis
    out = {}
    for name in ("dissolve", "cut", "push"):
        fn, n = slideshow(name)
        out[name] = os.path.join(d, f"{name}.mp4")
        write_video(out[name], fn, n)
    out["letterbox"] = os.path.join(d, "letterbox.mp4")
    write_video(out["letterbox"], letterboxed_with_gap, 120)
    out["dark_type"] = os.path.join(d, "dark_type.mp4")
    write_video(out["dark_type"], dark_typography, 120)
    out["_dir"] = d
    yield out
    if old is None:
        os.environ.pop("CUTROOM_ANALYSIS_CACHE", None)
    else:
        os.environ["CUTROOM_ANALYSIS_CACHE"] = old
    shutil.rmtree(d, ignore_errors=True)


_cache = {}


def analysed(path):
    if path not in _cache:
        cap = cv2.VideoCapture(path)
        fps, n = cap.get(cv2.CAP_PROP_FPS), cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        _cache[path] = motion.analyze(path, fps, SW, n / fps)
    return _cache[path]


def scene_verdict(path):
    rep = Report()
    an = analysed(path)
    integrity.check_scene_continuity(an, rep)
    return [i["level"] for i in rep.items if i["check"] == "scenes"], an["scene_changes"]


def test_dissolve_slideshow_fails(vids):
    lv, ch = scene_verdict(vids["dissolve"])
    assert lv == ["FAIL"], ch
    assert [c["kind"] for c in ch] == ["dissolve"] * (PHOTOS - 1)


def test_hard_cut_slideshow_fails(vids):
    lv, ch = scene_verdict(vids["cut"])
    assert lv == ["FAIL"], ch
    assert [c["kind"] for c in ch] == ["cut"] * (PHOTOS - 1)


def test_pushed_photos_pass(vids):
    lv, ch = scene_verdict(vids["push"])
    assert lv == [], ch
    assert [c["kind"] for c in ch] == ["motion"] * (PHOTOS - 1)


def test_slideshow_stills_are_frozen_pictures(vids):
    rep = Report()
    integrity.check_integrity(analysed(vids["cut"]), rep)
    assert "WARN" in [i["level"] for i in rep.items if i["check"] == "frozen"]


def test_black_gap_and_letterbox_found(vids):
    rep = Report()
    integrity.check_integrity(analysed(vids["letterbox"]), rep)
    found = {(i["level"], i["check"]) for i in rep.items}
    assert ("FAIL", "black") in found and ("FAIL", "borders") in found, rep.items
    assert "top 80, bottom 80" in rep.metrics["black_bars_px"]


def test_dark_typographic_piece_has_no_bars(vids):
    """Centred type on a near-black background must not read as a letterbox (the real one above still fails)."""
    rep = Report()
    integrity.check_integrity(analysed(vids["dark_type"]), rep)
    assert not [i for i in rep.items if i["check"] == "borders"], (rep.items, rep.metrics.get("black_bars_px"))


def test_verifier_end_to_end_without_track(vids):
    """The full CLI: the dissolve slideshow fails on scenes; the scene metrics are reported."""
    out = os.path.join(vids["_dir"], "dissolve.json")
    subprocess.run([sys.executable, os.path.join(TOOLS, "verify.py"), vids["dissolve"], "--format", "story", "--json", out],
                   capture_output=True, text=True, env={**os.environ, "CUTROOM_FACE_MODEL": os.path.join(vids["_dir"], "none.onnx")})
    rep = json.load(open(out))
    found = {(i["level"], i["check"]) for i in rep["report"]}
    assert ("FAIL", "scenes") in found and ("INFO", "faces") in found, found
    assert rep["metrics"]["changes_in_motion"] == f"0/{PHOTOS - 1}"
