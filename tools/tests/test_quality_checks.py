"""Unit tests for the reading-time, integrity, face and model checks — synthetic data, no video decoding.

    python3 -m pytest tools/tests/test_quality_checks.py -q
"""
import hashlib
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

from quality import integrity, limits as L, track  # noqa: E402
from quality.report import Report  # noqa: E402

W, H, FPS = 1080, 1920, 30


def levels(rep, check):
    return sorted(i["level"] for i in rep.items if i["check"] == check)


# ------------------------------------------------------------------ reading time
def text_track(runs, text="Agua termal sin apuro", element="label", o=1.0, x=200, y=800, w=600, h=90, n=300):
    """A text element fully visible during the frame ranges in `runs` (list of (first, last))."""
    recs = []
    for f in range(n):
        on = any(a <= f <= b for a, b in runs)
        r = dict(f=f, lf=f, id=element, k="text", x=x, y=y, w=w, h=h, o=o if on else 0.0, inFrame=False, blurred=False)
        if text is not None:
            r["t"] = text
        recs.append(r)
    j = dict(width=W, height=H, fps=FPS, scale=1, beats=[], records=recs)
    by_id = {}
    for r in recs:
        by_id.setdefault(r["id"], {})[r["f"]] = r
    return j, by_id


def reading(runs, **kw):
    rep = Report()
    track.reading_time(*text_track(runs, **kw), rep)
    return rep


def frames_for(seconds):
    return round(seconds * FPS)


def test_word_count_and_requirement():
    assert track.word_count("Agua termal sin apuro") == 4
    assert track.word_count("+54 9 11 0000-0000") == 4
    assert track.word_count("Estudio — Ejemplo") == 2
    assert track.word_count("") == 0
    assert track.required_reading_s(4) == pytest.approx(L.READ_BASE_S + 4 * L.READ_PER_WORD_S)


def test_reading_enough_time_passes():
    need = track.required_reading_s(4)  # 1.72 s
    rep = reading([(30, 30 + frames_for(need) + 2)])
    assert not levels(rep, "reading") and rep.metrics["reading_time_min_share"] >= 1


def test_reading_slightly_short_warns():
    need = track.required_reading_s(4)
    rep = reading([(30, 30 + frames_for(0.85 * need))])
    assert levels(rep, "reading") == ["WARN"]


def test_reading_far_too_short_fails():
    need = track.required_reading_s(4)
    rep = reading([(30, 30 + frames_for(0.5 * need))])
    assert levels(rep, "reading") == ["FAIL"]


def test_reading_each_appearance_counts():
    need = track.required_reading_s(4)
    rep = reading([(10, 10 + frames_for(need) + 5), (200, 200 + frames_for(0.4 * need))])
    assert levels(rep, "reading") == ["FAIL"] and rep.metrics["text_appearances_checked"] == 2


def test_reading_short_dips_do_not_split_an_appearance():
    need = track.required_reading_s(4)
    half = frames_for(need / 2) + 2
    rep = reading([(30, 30 + half), (30 + half + 2, 30 + 2 * half + 2)])  # a 1-frame dip in the middle
    assert not levels(rep, "reading") and rep.metrics["text_appearances_checked"] == 1


def test_reading_half_transparent_or_out_of_frame_is_not_legible():
    rep = reading([(0, 299)], o=0.6)
    assert levels(rep, "reading") == ["WARN"] and "never fully legible" in rep.items[0]["msg"]
    rep = reading([(0, 299)], x=900)  # box runs past the right edge
    assert "never fully legible" in rep.items[0]["msg"]


def test_reading_typewriter_is_judged_by_its_full_text():
    """A typewriter's first frames hold "R", "Re"...; the appearance must be judged by the full line."""
    full = "Reservá tu escapada termal hoy mismo"  # 6 words → 2.28 s
    a, b = 30, 30 + frames_for(1.2)  # 1.2 s: plenty for one word, far too short for six
    j, by_id = text_track([(a, b)], text=full)
    for f, r in by_id["label"].items():  # the text exists only while it types on
        r["t"] = full[:max(1, (f - a) * 2)] if a <= f <= b else ""
    rep = Report()
    track.reading_time(j, by_id, rep)
    assert levels(rep, "reading") == ["FAIL"] and "(6 words)" in rep.items[0]["msg"]


def test_reading_reused_id_is_judged_per_appearance():
    """One id showing a short line, then a long one: each appearance is judged by its own text."""
    short, long_ = "Hola", "Agua termal sin apuro todo el año"  # 1 word / 7 words
    first = (10, 10 + frames_for(track.required_reading_s(1)) + 2)
    second = (150, 150 + frames_for(1.6))  # enough for 1 word, not for 7
    j, by_id = text_track([first, second], text=short)
    for f, r in by_id["label"].items():
        if f >= 100:
            r["t"] = long_
    rep = Report()
    track.reading_time(j, by_id, rep)
    msgs = [i["msg"] for i in rep.items if i["check"] == "reading"]
    assert len(msgs) == 1 and "(7 words)" in msgs[0] and f"{150 / FPS:.2f}s" in msgs[0]


def test_reading_without_text_field_is_skipped_with_info():
    rep = reading([(30, 33)], text=None)
    assert [(i["level"], i["check"]) for i in rep.items] == [("INFO", "reading")]


# ------------------------------------------------------------------ integrity
def analysis(n=300, diff=None, mean=None, p99=None, bars=None):
    diff = np.full(n, 1.0) if diff is None else diff
    diff[0] = 0.0
    return dict(fps=FPS, diff=diff, integrity=dict(mean=np.full(n, 200.0) if mean is None else mean,
                                                   p99=np.full(n, 250.0) if p99 is None else p99,
                                                   bars=bars if bars is not None else [(0, 0, 0, 0)] * (n // 15)))


def integ(an, track_=None):
    rep = Report()
    integrity.check_integrity(an, rep, track_)
    return rep


def test_black_frames_mid_video_fail_edges_do_not():
    mean, p99 = np.full(300, 200.0), np.full(300, 250.0)
    mean[:4] = p99[:4] = 0  # fade from black in the first 0.2 s
    mean[-5:] = p99[-5:] = 0  # fade to black in the last 0.2 s
    assert not levels(integ(analysis(mean=mean.copy(), p99=p99.copy())), "black")
    mean[150:153] = p99[150:153] = 2
    rep = integ(analysis(mean=mean, p99=p99))
    assert levels(rep, "black") == ["FAIL"] and rep.metrics["black_frames"] == 3


def test_dark_scene_with_a_lit_detail_is_not_black():
    mean, p99 = np.full(300, 5.0), np.full(300, 180.0)
    assert not levels(integ(analysis(mean=mean, p99=p99)), "black")


def test_frozen_picture_mid_video_warns_final_hold_does_not():
    diff = np.full(300, 1.0)
    diff[240:] = 0.0  # 2 s final hold
    rep = integ(analysis(diff=diff.copy()))
    assert not levels(rep, "frozen") and rep.metrics["final_hold_s"] == pytest.approx(2.03, abs=0.05)
    diff[60:130] = 0.0  # 2.4 s identical frames in the middle
    rep = integ(analysis(diff=diff))
    assert levels(rep, "frozen") == ["WARN"]


def test_frozen_inside_a_declared_hold_is_info():
    diff = np.full(300, 1.0)
    diff[60:130] = 0.0
    j = dict(beats=[{"f": 0, "name": "in", "kind": "move"}, {"f": 58, "name": "hold on the photo", "kind": "hold"}, {"f": 135, "name": "out", "kind": "move"}])
    rep = integ(analysis(diff=diff), (j, {}))
    assert levels(rep, "frozen") == ["INFO"]


def test_overlong_frozen_ending_warns():
    diff = np.full(300, 1.0)
    diff[100:] = 0.0
    assert levels(integ(analysis(diff=diff)), "frozen") == ["WARN"]


def test_bar_widths():
    f = np.full((1920, 1080), 200, np.uint8)
    f[:120] = 0
    f[-120:] = 3
    assert integrity.bar_widths(f) == (120, 120, 0, 0)
    assert integrity.bar_widths(np.zeros((100, 100), np.uint8)) is None


def test_letterbox_fails_one_band_warns_occasional_dark_frames_ignored():
    assert levels(integ(analysis(bars=[(120, 118, 0, 0)] * 20)), "borders") == ["FAIL"]
    assert levels(integ(analysis(bars=[(0, 0, 60, 60)] * 20)), "borders") == ["FAIL"]
    assert levels(integ(analysis(bars=[(30, 0, 0, 0)] * 20)), "borders") == ["WARN"]
    # bars on only a few frames (a dark scene) are not consistent bars
    assert not levels(integ(analysis(bars=[(120, 120, 0, 0)] * 2 + [(0, 0, 0, 0)] * 18 + [None] * 3)), "borders")


def test_bar_widths_ignore_dark_design_margins():
    """Near-black background with centred type: dark margins, but no flat band ending at a straight picture edge."""
    f = np.full((1920, 1080), 10, np.uint8)  # #0a0a0a
    f[900:1000, 200:880:40] = 235  # glyph strokes
    f[900:1000, 201:880:40] = 235
    assert integrity.bar_widths(f) == (0, 0, 0, 0)
    # a real letterbox on the same dark tone still is one
    g = np.full((1920, 1080), 140, np.uint8)
    g[:200] = 10
    g[-200:] = 10
    assert integrity.bar_widths(g) == (200, 200, 0, 0)


def test_unstable_bar_edges_are_not_bars():
    wobbling = [(100 + 30 * (k % 4), 100 + 30 * ((k + 1) % 4), 0, 0) for k in range(20)]
    assert not levels(integ(analysis(bars=wobbling)), "borders")


def test_brightness_range():
    assert levels(integ(analysis(mean=np.full(300, 25.0))), "luma") == ["WARN"]
    assert levels(integ(analysis(mean=np.full(300, 245.0))), "luma") == ["WARN"]
    assert not levels(integ(analysis(mean=np.full(300, 120.0))), "luma")


def test_scene_continuity_verdicts():
    def run(kinds):
        rep = Report()
        integrity.check_scene_continuity({"scene_changes": [dict(t=float(i), kind=k, change=40.0) for i, k in enumerate(kinds)]}, rep)
        return levels(rep, "scenes")

    assert run(["motion"] * 5) == []
    assert run(["motion"] * 3 + ["dissolve"]) == ["WARN"]  # 75 %
    assert run(["motion", "dissolve", "cut", "still"]) == ["FAIL"]  # 25 %
    assert run(["dissolve"]) == ["INFO"]  # too few to judge


# ------------------------------------------------------------------ faces
class FakeDetector:
    def __init__(self, from_frame):
        self.from_frame = from_frame

    def detect(self, bgr):
        return [(10, 10, 80, 80, 0.95)] if bgr[0, 0, 0] >= self.from_frame else []


def test_faces_warn_with_timestamps():
    from quality import faces

    frames = {i: np.full((64, 36, 3), min(i, 255), np.uint8) for i in range(0, 300, 30)}
    media = dict(path="unused.mp4", fps=FPS, duration=10.0)
    rep = Report()
    faces.check_faces(media, dict(full_frames=frames), rep, detector=FakeDetector(150))
    msg = [i for i in rep.items if i["check"] == "faces"]
    assert [i["level"] for i in msg] == ["WARN"] and "permission" in msg[0]["msg"] and "5s" in msg[0]["msg"]
    assert rep.metrics["frames_with_faces"] == "5/10"


def test_faces_no_face_no_warning():
    from quality import faces

    frames = {i: np.zeros((64, 36, 3), np.uint8) for i in range(0, 300, 30)}
    rep = Report()
    faces.check_faces(dict(path="unused.mp4", fps=FPS, duration=10.0), dict(full_frames=frames), rep, detector=FakeDetector(1))
    assert not [i for i in rep.items if i["check"] == "faces"]


def test_faces_missing_model_is_info(monkeypatch, tmp_path):
    from quality import faces

    monkeypatch.setenv("CUTROOM_FACE_MODEL", str(tmp_path / "missing.onnx"))
    rep = Report()
    faces.check_faces(dict(path="unused.mp4", fps=FPS, duration=10.0), {}, rep)
    assert [(i["level"], i["msg"]) for i in rep.items] == [("INFO", "face check skipped (run: python3 tools/models.py fetch)")]


def test_face_sample_indices_one_per_second():
    from quality import faces

    assert faces.sample_indices(4.0, 30) == [0, 30, 60, 90]


# ------------------------------------------------------------------ models.py
def _models():
    import importlib

    sys.path.insert(0, TOOLS)
    return importlib.import_module("models")


def test_models_fetch_verifies_the_hash(tmp_path):
    models = _models()
    payload = b"onnx bytes"
    good = dict(models.MODELS["yunet"], sha256=hashlib.sha256(payload).hexdigest(), urls=["https://a.example/m.onnx"])

    def downloader(url, dest):
        open(dest, "wb").write(payload)

    assert models.fetch("yunet", good, folder=str(tmp_path), downloader=downloader)
    assert open(tmp_path / good["file"], "rb").read() == payload

    bad = dict(good, sha256="0" * 64)
    os.remove(tmp_path / good["file"])
    assert not models.fetch("yunet", bad, folder=str(tmp_path), downloader=downloader)
    assert not os.path.exists(tmp_path / good["file"]) and not [p for p in os.listdir(tmp_path) if p.endswith(".part")]
    assert models.fetch("yunet", bad, verify=False, folder=str(tmp_path), downloader=downloader)


def test_models_fetch_refuses_without_a_pinned_hash(tmp_path):
    models = _models()
    calls = []
    m = dict(models.MODELS["yunet"], sha256="")
    assert not models.fetch("yunet", m, folder=str(tmp_path), downloader=lambda u, d: calls.append(u))
    assert not calls


def test_models_licenses_and_status(tmp_path):
    models = _models()
    path = models.write_licenses(str(tmp_path))
    txt = open(path).read()
    assert "MIT License" in txt and models.MODELS["yunet"]["file"] in txt and models.MODELS["yunet"]["sha256"] in txt
    rows = models.status(str(tmp_path))
    assert rows[0][0] == "yunet" and rows[0][2].startswith(("missing", "installed"))


def test_models_licenses_file_is_in_the_repo_and_current(tmp_path):
    """tools/models/LICENSES.md is committed (the models are not) and matches what models.py writes."""
    models = _models()
    committed = os.path.join(models.MODELS_DIR, "LICENSES.md")
    assert os.path.isfile(committed), "run: python3 tools/models.py fetch and commit tools/models/LICENSES.md"
    fresh = models.write_licenses(str(tmp_path))
    assert open(committed, encoding="utf-8").read() == open(fresh, encoding="utf-8").read()
    assert "Copyright (c) 2020 Shiqi Yu" in open(committed, encoding="utf-8").read()
