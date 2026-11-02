#!/usr/bin/env python3
"""Tests for tools/material.py and tools/media: read-only guard, photo / video analysis, select, clip preparation.

    python3 -m pytest tools/tests/test_material.py -q

Everything runs in temporary folders with CUTROOM_CLIENTS pointing at a temporary clients folder; the material is
synthetic (numpy images, ffmpeg lavfi videos) plus copies of the sample client's synthetic photos.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np
import pytest
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import material  # noqa: E402
from media import clips, guard, videos  # noqa: E402
from quality.bins import ffmpeg, ffprobe  # noqa: E402

SAMPLES = sorted(glob.glob(os.path.join(ROOT, "clients", "sample", "assets", "photos", "*.jpg")))


# ------------------------------------------------------------------ fixtures
def scene(seed, size=(1600, 1200)):
    """A photo-like image: multi-scale coloured noise, a few hard-edged shapes, a gradient sky."""
    rng = np.random.default_rng(seed)
    w, h = size
    img = np.zeros((h, w, 3), np.float32)
    for scale in (4, 16, 64):
        n = rng.random((max(2, h // scale), max(2, w // scale), 3)).astype(np.float32)
        img += cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC) * (scale / 84)
    img = img / img.max() * 200
    img[: h // 3] = img[: h // 3] * 0.4 + np.array([200, 160, 90], np.float32) * 0.6  # sky band (BGR)
    for _ in range(6):
        c = tuple(int(x) for x in rng.integers(0, 255, 3))
        x, y = int(rng.integers(0, w - 200)), int(rng.integers(h // 3, h - 200))
        cv2.rectangle(img, (x, y), (x + int(rng.integers(60, 300)), y + int(rng.integers(60, 300))), c, -1)
    cv2.circle(img, (int(w * 0.62), int(h * 0.58)), h // 8, (30, 40, 230), -1)
    noise = rng.normal(0, 6, img.shape).astype(np.float32)
    return np.clip(img + noise, 0, 255).astype(np.uint8)


def write_client(clients, slug="demo", source_folders=()):
    d = os.path.join(clients, slug)
    os.makedirs(os.path.join(d, "briefs"), exist_ok=True)
    with open(os.path.join(d, "client.json"), "w") as f:
        json.dump({"slug": slug, "name": slug.title(), "brand": {}, "source_folders": list(source_folders)}, f)
    return d


def lavfi_video(path, spec, extra=(), dur=2):
    cmd = [ffmpeg(), "-v", "error", "-y", "-f", "lavfi", "-i", f"{spec}:duration={dur}", *extra,
           "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", path]
    subprocess.run(cmd, check=True)
    return path


def stream_info(path):
    out = subprocess.run([ffprobe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


@pytest.fixture
def env(tmp_path, monkeypatch):
    clients = tmp_path / "clients"
    src = tmp_path / "Originals 2026"
    src.mkdir()
    monkeypatch.setenv("CUTROOM_CLIENTS", str(clients))
    monkeypatch.delenv("CUTROOM_READONLY", raising=False)
    write_client(str(clients), "demo", [str(src)])
    return {"tmp": tmp_path, "clients": clients, "src": src, "client": clients / "demo"}


@pytest.fixture(scope="module")
def photo_set(tmp_path_factory):
    """sharp.jpg, blurred copy, a different scene, a resized re-encoded duplicate, two sample photos."""
    d = tmp_path_factory.mktemp("photos")
    a = scene(1)
    cv2.imwrite(str(d / "a-sharp.jpg"), a, [cv2.IMWRITE_JPEG_QUALITY, 92])
    cv2.imwrite(str(d / "b-blurred.jpg"), cv2.GaussianBlur(a, (0, 0), 5), [cv2.IMWRITE_JPEG_QUALITY, 92])
    cv2.imwrite(str(d / "c-other.jpg"), scene(2), [cv2.IMWRITE_JPEG_QUALITY, 92])
    cv2.imwrite(str(d / "d-resized.jpg"), cv2.resize(a, (1200, 900), interpolation=cv2.INTER_AREA),
                [cv2.IMWRITE_JPEG_QUALITY, 80])
    for i, s in enumerate(SAMPLES[:2]):
        shutil.copy(s, d / f"e-sample{i}.jpg")
    return d


# ------------------------------------------------------------------ guard
def test_guard_refuses_source_folder_direct_symlink_and_dotdot(env):
    src, tmp = env["src"], env["tmp"]
    with pytest.raises(guard.ReadOnlyPathError):
        guard.ensure_writable(src / "out.json")
    with pytest.raises(guard.ReadOnlyPathError):
        guard.ensure_writable(src)
    with pytest.raises(guard.ReadOnlyPathError):  # '..' that lands inside
        guard.ensure_writable(tmp / "elsewhere" / ".." / src.name / "x" / "y.png")
    link = tmp / "innocent-looking"
    os.symlink(src, link)
    with pytest.raises(guard.ReadOnlyPathError):  # symlinked parent, file does not exist yet
        guard.ensure_writable(link / "new" / "file.jpg")
    # a sibling with the same prefix is not inside
    assert guard.ensure_writable(tmp / (src.name + "-copy") / "a.jpg")
    assert guard.ensure_writable(env["client"] / "material" / "x" / "analysis.json")


def test_guard_env_and_extra(env, monkeypatch):
    other = env["tmp"] / "other"
    other.mkdir()
    assert not guard.is_protected(other / "a")
    monkeypatch.setenv("CUTROOM_READONLY", os.pathsep.join([str(env["tmp"] / "nothing"), str(other)]))
    assert guard.is_protected(other / "a")
    third = env["tmp"] / "third"
    assert guard.is_protected(third / "f", extra=[third])


def test_guard_strips_entries_and_reads_client_local_json(env, monkeypatch):
    tmp, clients = env["tmp"], env["clients"]
    padded, local = tmp / "padded", tmp / "local originals"
    padded.mkdir()
    local.mkdir()
    d = write_client(str(clients), "other", [f"  {padded}  "])  # trailing / leading spaces must not bypass it
    assert guard.is_protected(padded / "a.jpg")
    assert not guard.is_protected(local / "a.jpg")
    with open(os.path.join(d, "client.local.json"), "w") as f:
        json.dump({"source_folders": [str(local) + " "]}, f)
    hit = guard.protecting_folder(local / "x" / "a.jpg")
    assert hit and "client.local.json" in hit[1]
    assert guard.load_client(d)["source_folders"] == [str(local) + " "]  # merged over client.json
    # a client folder with only client.local.json is still read
    lonely = clients / "lonely"
    lonely.mkdir()
    (lonely / "client.local.json").write_text(json.dumps({"source_folders": [str(tmp / "lonely-src")]}))
    assert guard.is_protected(tmp / "lonely-src" / "f")
    monkeypatch.setenv("CUTROOM_READONLY", f" {tmp / 'envdir'} ")
    assert guard.is_protected(tmp / "envdir" / "f")


def test_guard_relative_entries(env, monkeypatch):
    clients = env["clients"]
    d = write_client(str(clients), "rel", ["originals"])
    # protected where it would resolve (inside the client folder), never silently dropped
    assert guard.is_protected(os.path.join(d, "originals", "a.jpg"))
    assert not guard.is_protected(os.path.join(d, "assets", "a.jpg"))
    monkeypatch.setenv("CUTROOM_READONLY", "relative/dir")
    with pytest.raises(guard.GuardConfigError, match="absolute"):
        guard.ensure_writable(env["tmp"] / "anything.json")
    assert issubclass(guard.GuardConfigError, guard.ReadOnlyPathError)  # every caller already handles it


def test_guard_is_case_insensitive_on_macos_and_windows(env, monkeypatch):
    src = env["src"]
    upper = src.parent / src.name.upper() / "a.jpg"
    monkeypatch.setattr(guard, "_case_insensitive", lambda: True)
    assert guard.is_protected(upper)
    monkeypatch.setattr(guard, "_case_insensitive", lambda: False)
    assert not guard.is_protected(upper)
    monkeypatch.undo()
    for platform, expected in (("darwin", True), ("win32", True), ("linux", guard.os.name == "nt")):
        monkeypatch.setattr(guard.sys, "platform", platform)
        assert guard._case_insensitive() is expected
        monkeypatch.undo()


def test_analyze_refuses_when_client_folder_is_inside_a_source(env, photo_set, monkeypatch):
    # the client folder itself sits inside a protected folder (symlinked clients dir)
    shutil.copy(photo_set / "a-sharp.jpg", env["src"] / "a.jpg")
    inner = env["src"] / "clients"
    write_client(str(inner), "demo2")
    monkeypatch.setenv("CUTROOM_CLIENTS", str(inner))
    write_client(str(inner), "demo", [str(env["src"])])  # the client that declares the source folder
    with pytest.raises(guard.ReadOnlyPathError):
        material.analyze("demo2", [str(env["src"])], quiet=True)
    assert not (inner / "demo2" / "material").exists()


# ------------------------------------------------------------------ analyze
def test_analyze_photos_schema_sheet_ranking_duplicates(env, photo_set):
    src = env["src"]
    for f in photo_set.iterdir():
        shutil.copy(f, src / f.name)
    before = {p.name: p.stat().st_mtime_ns for p in src.iterdir()}
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "material.py"), "analyze", "demo", str(src)],
                       capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 0, r.stderr
    out = env["client"] / "material" / "originals-2026"
    data = json.loads((out / "analysis.json").read_text())
    assert material.validate_analysis(data) == []
    assert data["batch"] == "originals-2026"
    assert (out / "contact_sheet.png").is_file()
    with Image.open(out / "contact_sheet.png") as im:
        assert im.width > 1000 and im.height > 300
    # the originals were not touched and nothing was added next to them
    assert {p.name: p.stat().st_mtime_ns for p in src.iterdir()} == before

    by = {p["file"]: p for p in data["photos"]}
    assert [p["id"] for p in data["photos"]] == list(range(1, len(data["photos"]) + 1))
    sharp, blurred, other, resized = by["a-sharp.jpg"], by["b-blurred.jpg"], by["c-other.jpg"], by["d-resized.jpg"]
    assert blurred["score"] < sharp["score"]
    assert blurred["rank"] > sharp["rank"]
    assert blurred["sharpness"]["relative"] < 0.6 * sharp["sharpness"]["relative"]
    assert any("softer" in n or "out of focus" in n for n in blurred["warnings"] + blurred["errors"])
    assert resized["id"] in sharp["duplicates"] and sharp["id"] in resized["duplicates"]
    assert other["id"] not in sharp["duplicates"]
    assert any(w.startswith("duplicate of") for w in resized["warnings"])
    assert sharp["orientation"] == "landscape" and sharp["width"] == 1600
    for p in data["photos"]:
        assert 0 <= p["focus"]["x"] <= 1 and 0 <= p["focus"]["y"] <= 1
        c = p["crop_9x16"]
        assert abs(c["w"] * p["width"] / (c["h"] * p["height"]) - 9 / 16) < 0.01


def test_focus_finds_the_subject(tmp_path):
    from media import photos
    rng = np.random.default_rng(7)
    bg = np.clip(rng.normal(128, 4, (900, 1600, 3)), 0, 255).astype(np.uint8)
    bg[:300] = (235, 200, 150)                                  # pale blue sky (BGR)
    cv2.circle(bg, (1150, 560), 110, (40, 50, 220), -1)         # red subject right of centre
    cv2.circle(bg, (1150, 560), 40, (240, 240, 240), -1)
    f = tmp_path / "subject.jpg"
    cv2.imwrite(str(f), bg)
    r = photos.measure(str(f))
    # coarse by design (96 px map + centre prior): it must land on the subject's side, below the sky
    assert r["focus"]["x"] > 0.55 and r["focus"]["y"] > 0.33, r["focus"]
    c = r["crop_9x16"]
    assert c["x"] < 1150 / 1600 < c["x"] + c["w"]


def test_analyze_videos(env):
    src = env["src"]
    a = lavfi_video(str(src / "pan.mp4"), "testsrc2=size=320x568:rate=25", dur=3)
    raw = str(env["tmp"] / "cut.mp4")
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=25:duration=3",
                    "-f", "lavfi", "-i", "mandelbrot=size=320x180:rate=25", "-filter_complex",
                    "[1:v]trim=duration=3,setpts=PTS-STARTPTS[b];[0:v][b]concat=n=2:v=1[v]", "-map", "[v]",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", raw], check=True)
    shutil.move(raw, src / "cut.mp4")
    data = material.analyze("demo", [str(src)], with_videos=True, quiet=True)
    assert material.validate_analysis(json.loads(open(data["_path"]).read())) == []
    out = env["client"] / "material" / "originals-2026"
    assert (out / "video_sheet.png").is_file()
    assert data["sheets"] == {"photos": None, "videos": "video_sheet.png"}
    by = {v["file"]: v for v in data["videos"]}
    cut = by["cut.mp4"]
    assert cut["width"] == 320 and abs(cut["duration_s"] - 6) < 0.2 and not cut["hdr"]
    assert cut["cuts"] and abs(cut["cuts"][0] - 3.0) <= 0.3
    for w in cut["windows"]:
        assert 2.0 <= w["duration"] <= 4.0
        assert not (w["start"] < cut["cuts"][0] < w["end"]), w
    assert cut["class"] in ("motion", "mixed", "slideshow")
    assert by["pan.mp4"]["orientation"] == "portrait" and os.path.basename(a) == "pan.mp4"
    # without --videos, folder videos are skipped, not analysed
    cv2.imwrite(str(src / "p.jpg"), scene(5, (800, 600)))
    d2 = material.analyze("demo", [str(src)], batch="photos-only", quiet=True)
    assert d2["videos"] == [] and len(d2["photos"]) == 1 and len(d2["skipped"]) == 2


# ------------------------------------------------------------------ select
def test_select_copies_rescales_and_updates_brief(env, photo_set):
    src = env["src"]
    big = scene(3, (3000, 2000))
    cv2.imwrite(str(src / "1-big.jpg"), big, [cv2.IMWRITE_JPEG_QUALITY, 90])
    # EXIF orientation 6 (rotate 90 CW): stored landscape, shown portrait
    im = Image.fromarray(cv2.cvtColor(scene(4, (1200, 800)), cv2.COLOR_BGR2RGB))
    exif = Image.Exif()
    exif[0x0112] = 6
    im.save(src / "2-rotated.jpg", exif=exif.tobytes(), quality=90)
    shutil.copy(photo_set / "c-other.jpg", src / "3-other.jpg")
    lavfi_video(str(src / "4-clip.mp4"), "testsrc2=size=640x360:rate=25", dur=3)
    data = material.analyze("demo", [str(src)], batch="Trip One", with_videos=True, quiet=True)
    assert data["batch"] == "trip-one"
    rot = next(p for p in data["photos"] if p["file"] == "2-rotated.jpg")
    assert (rot["width"], rot["height"]) == (800, 1200) and rot["orientation"] == "portrait"

    brief_path = env["client"] / "briefs" / "promo.json"
    brief_path.write_text(json.dumps({"id": "promo", "client": "demo", "assets": {"photos": ["assets/photos/logo-bg.jpg"]}}))
    material.select(str(brief_path), [2, 1], [(1, 0.5, 1.5)], preset="ultrafast", quiet=True)
    brief = json.loads(brief_path.read_text())
    assert brief["material"]["batch"] == "trip-one"
    assert brief["material"]["analysis"] == "material/trip-one/analysis.json"
    assert brief["material"]["selected"] == [2, 1]
    assert brief["assets"]["photos"] == ["assets/photos/logo-bg.jpg", "assets/photos/trip-one-02.jpg",
                                         "assets/photos/trip-one-01.jpg"]
    v = brief["material"]["videos"][0]
    assert v["id"] == 1 and v["start"] == 0.5 and v["end"] == 1.5 and v["mode"] == "card"
    assert brief["assets"]["videos"] == [v["file"]]
    with Image.open(env["client"] / "assets/photos/trip-one-01.jpg") as a:
        assert max(a.size) == 2400 and a.size == (2400, 1600) and a.format == "JPEG" and a.mode == "RGB"
        assert 0x0112 not in a.getexif()
    with Image.open(env["client"] / "assets/photos/trip-one-02.jpg") as b:
        assert b.size == (800, 1200)
    assert (env["client"] / v["file"]).is_file()
    # running it again does not duplicate entries
    material.select(str(brief_path), [2, 1], quiet=True)
    brief2 = json.loads(brief_path.read_text())
    assert brief2["assets"]["photos"] == brief["assets"]["photos"]
    assert brief2["material"]["videos"] == brief["material"]["videos"]
    with pytest.raises(ValueError):
        material.select(str(brief_path), [99], quiet=True)


def test_reselect_replaces_the_batch_entries(env, photo_set):
    src = env["src"]
    for i, name in enumerate(("a-sharp.jpg", "c-other.jpg", "e-sample0.jpg"), 1):
        shutil.copy(photo_set / name, src / f"{i}.jpg")
    lavfi_video(str(src / "4-clip.mp4"), "testsrc2=size=640x360:rate=25", dur=3)
    material.analyze("demo", [str(src)], batch="trip", with_videos=True, quiet=True)
    brief_path = env["client"] / "briefs" / "promo.json"
    keep = ["assets/photos/logo-bg.jpg", "assets/photos/other-batch-01.jpg"]
    brief_path.write_text(json.dumps({"id": "promo", "client": "demo",
                                      "assets": {"photos": list(keep), "videos": ["assets/videos/intro.mp4"]}}))
    material.select(str(brief_path), [1, 2, 3], [(1, 0.0, 1.0)], preset="ultrafast", quiet=True)
    material.select(str(brief_path), [3, 1], [(1, 1.0, 2.0)], preset="ultrafast", quiet=True)
    b = json.loads(brief_path.read_text())
    assert b["assets"]["photos"] == keep + ["assets/photos/trip-03.jpg", "assets/photos/trip-01.jpg"]
    assert b["assets"]["videos"] == ["assets/videos/intro.mp4", "assets/videos/trip-v01-0010.mp4"]
    assert [v["file"] for v in b["material"]["videos"]] == ["assets/videos/trip-v01-0010.mp4"]
    # the dropped exports are kept on disk
    assert (env["client"] / "assets/photos/trip-02.jpg").is_file()
    assert (env["client"] / "assets/videos/trip-v01-0000.mp4").is_file()
    # without --videos the batch's videos stay; an empty selection clears the batch's photos
    material.select(str(brief_path), [], quiet=True)
    b = json.loads(brief_path.read_text())
    assert b["assets"]["photos"] == keep and b["material"]["selected"] == []
    assert b["assets"]["videos"] == ["assets/videos/intro.mp4", "assets/videos/trip-v01-0010.mp4"]
    assert material.batch_photo("trip", "assets/photos/trip-07.jpg")
    assert not material.batch_photo("trip", "assets/photos/trip-extra-07.jpg")
    assert not material.batch_photo("trip", "assets/photos/mytrip-07.jpg")


def test_parse_choices():
    assert material.parse_ids("3,7, 2") == [3, 7, 2]
    assert material.parse_video_specs(["1:4.0-7.5", "2,3:1-2"]) == [(1, 4.0, 7.5), (2, None, None), (3, 1.0, 2.0)]
    with pytest.raises(ValueError):
        material.parse_video_specs(["1:5-4"])
    with pytest.raises(ValueError):
        material.parse_ids("1,1")


# ------------------------------------------------------------------ clips
def check_clip(path, w=1080, h=1920, frames=None):
    info = stream_info(path)
    assert [s["codec_type"] for s in info["streams"]] == ["video"]  # no audio
    s = info["streams"][0]
    assert s["codec_name"] == "h264" and s["pix_fmt"] == "yuv420p"
    assert (s["width"], s["height"]) == (w, h)
    assert s["r_frame_rate"] == "30/1" and s["avg_frame_rate"] == "30/1"
    assert s.get("color_space") == "bt709" and s.get("color_transfer") == "bt709" and s.get("color_primaries") == "bt709"
    if frames:
        assert int(s["nb_frames"]) == frames
    return s


def test_clip_vertical_and_card(env):
    v = lavfi_video(str(env["src"] / "talk.mp4"), "testsrc2=size=640x360:rate=25", dur=2,
                    extra=("-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:a", "aac", "-shortest"))
    assert videos.probe(v)["has_audio"]
    out = env["tmp"] / "out" / "v.mp4"
    res = clips.prepare(v, str(out), start=0.5, dur=1.0, mode="vertical", crop_top=0.1, preset="ultrafast")
    check_clip(str(out), frames=30)
    assert not res["hdr"] and res["warnings"] == []
    card = env["tmp"] / "out" / "c.mp4"
    res = clips.prepare(v, str(card), start=1.5, dur=1.0, mode="card", warm=1.0, preset="ultrafast")
    check_clip(str(card), frames=30)  # the window runs past the end: the last frame is held
    assert any("past the end" in w for w in res["warnings"])
    # the CLI refuses to write next to the original
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "material.py"), "clip", v, "--dur", "1",
                        "--out", str(env["src"] / "x.mp4")], capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 3 and "read-only" in r.stderr
    assert not (env["src"] / "x.mp4").exists()


def test_clip_hdr_is_tone_mapped(env):
    v = lavfi_video(str(env["src"] / "hlg.mp4"), "testsrc2=size=360x640:rate=30", dur=1,
                    extra=("-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc"))
    meta = videos.probe(v)
    assert meta["hdr"] and meta["hdr_format"] == "HLG"
    out = env["tmp"] / "out" / "hlg-sdr.mp4"
    res = clips.prepare(v, str(out), start=0, dur=0.5, preset="ultrafast")
    check_clip(str(out), frames=15)
    assert res["hdr"]
    if clips.can_tonemap():
        assert res["tonemapped"] and res["warnings"] == []
    else:
        assert not res["tonemapped"] and res["warnings"]


def test_clip_rotation_metadata(env):
    plain = lavfi_video(str(env["tmp"] / "plain.mp4"), "testsrc2=size=480x270:rate=30", dur=1)
    v = str(env["src"] / "rot.mp4")
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-display_rotation", "90", "-i", plain, "-c", "copy", v])
    if not os.path.isfile(v):
        pytest.skip("this ffmpeg has no -display_rotation")
    meta = videos.probe(v)
    if meta["rotation"] not in (90, 270):
        pytest.skip("this ffmpeg does not write rotation metadata this way")
    assert (meta["width"], meta["height"]) == (270, 480)
    out = env["tmp"] / "out" / "rot-out.mp4"
    clips.prepare(v, str(out), dur=0.5, preset="ultrafast")
    s = check_clip(str(out), frames=15)
    assert not any("rotation" in sd for sd in s.get("side_data_list") or [])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
