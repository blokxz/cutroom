"""compare.py: the numbers move the right way on renders made worse on purpose, and the outputs are written."""
import json
import os
import subprocess
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import compare  # noqa: E402
from quality.bins import ffmpeg  # noqa: E402


def still_video(img_path, out, vf=None, dur=2, size="360x640"):
    cmd = [ffmpeg(), "-v", "error", "-y", "-loop", "1", "-i", str(img_path), "-t", str(dur), "-r", "30",
           "-vf", f"scale={size.replace('x', ':')}" + (f",{vf}" if vf else ""), "-c:v", "libx264", "-crf", "12",
           "-pix_fmt", "yuv420p", str(out)]
    subprocess.run(cmd, check=True)
    return str(out)


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    d = tmp_path_factory.mktemp("cmp")
    photos = d / "photos"
    photos.mkdir()
    rng = np.random.default_rng(4)
    # a photo with texture, edges and a smooth gradient
    y, x = np.mgrid[0:640, 0:360]
    base = np.stack([x / 360 * 200 + 20, y / 640 * 180 + 40, np.full_like(x, 120.0)], -1)
    base += rng.normal(0, 18, base.shape)
    base[200:260, 40:320] = 245
    Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).save(photos / "p.png")
    sharp = still_video(photos / "p.png", d / "sharp.mp4")
    soft = still_video(photos / "p.png", d / "soft.mp4", "gblur=sigma=4")
    washed = still_video(photos / "p.png", d / "washed.mp4", "curves=all='0/0.3 0.45/1 1/1'")
    return {"dir": d, "photos": str(photos), "sharp": sharp, "soft": soft, "washed": washed}


def test_blur_loses_detail_and_sharpness(media):
    size = (360, 640)
    s = compare.measure(media["sharp"], size, 0.5, None)
    b = compare.measure(media["soft"], size, 0.5, None)
    assert s["sharpness"] > 3 * b["sharpness"]
    assert s["detail"] > b["detail"]
    w = compare.winners([s, b])
    assert w["sharpness"] == 0 and w["detail"] == 0


def test_a_washed_out_render_is_flat_and_blown(media):
    size = (360, 640)
    s = compare.measure(media["sharp"], size, 0.5, None)
    w = compare.measure(media["washed"], size, 0.5, None)
    assert w["blown"] > s["blown"] + 0.2
    assert w["flat"] > s["flat"]
    assert compare.winners([s, w])["blown"] == 0


def test_fidelity_prefers_the_faithful_render(media):
    size = (360, 640)
    photos = compare.load_photos(media["photos"], (90, 160))
    s = compare.measure(media["sharp"], size, 0.5, photos)
    b = compare.measure(media["soft"], size, 0.5, photos)
    assert s["fidelity"] is not None and s["fidelity"] > b["fidelity"]
    assert s["fidelity"] > 0.6


def test_ssim_is_one_for_identical_images_and_lower_otherwise():
    a = np.random.default_rng(1).uniform(0, 255, (50, 40))
    assert compare.ssim(a, a) == pytest.approx(1.0, abs=1e-9)
    assert compare.ssim(a, a * 0.5) < 0.95


def test_flat_field_has_no_detail_and_no_banding():
    flat = np.full((64, 64, 3), 128, np.uint8)
    n = compare.detail_numbers(flat)
    assert n["detail"] == 0 and n["flat"] == 1.0 and n["sharpness"] == 0


def test_stairs_score_higher_banding_than_a_dithered_ramp():
    y = np.repeat(np.repeat(np.arange(0, 32), 8)[None, :], 64, 0).astype(np.uint8)  # 32 flat plateaus, 1-level steps
    stairs = np.stack([y] * 3, -1)
    rng = np.random.default_rng(2)
    ramp = np.clip(np.linspace(0, 32, 256)[None, :] + rng.normal(0, 0.8, (64, 256)), 0, 255).round().astype(np.uint8)
    dithered = np.stack([ramp] * 3, -1)
    assert compare.detail_numbers(stairs)["banding"] > compare.detail_numbers(dithered)["banding"]


def test_cover_crop_keeps_the_aspect():
    img = Image.new("RGB", (400, 200))
    assert compare.cover(img, 90, 160).size == (90, 160)


def test_cli_writes_stills_metrics_side_by_side_and_a_seeded_blind_pair(media, capsys):
    out = media["dir"] / "out"
    code = compare.main([media["sharp"], media["soft"], "--labels", "nitido", "suave", "--photos", media["photos"],
                         "--times", "0.5,1.5", "--out", str(out), "--blind", "--seed", "3"])
    assert code == 0
    m = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    assert m["labels"] == ["nitido", "suave"] and m["winner"]["sharpness"] == 0
    assert Image.open(out / "stills.png").size[1] == 2 * (640 // 3)
    assert (out / "side_by_side.mp4").stat().st_size > 1000
    key = json.loads((out / "blind" / "key.json").read_text(encoding="utf-8"))
    assert sorted(key) == ["X", "Y"] and set(key.values()) == {os.path.abspath(media["sharp"]), os.path.abspath(media["soft"])}
    again = compare.blind(media["sharp"], media["soft"], str(media["dir"] / "b2"), 3)
    assert again == key
    printed = capsys.readouterr().out
    assert "sharpness" in printed and "wins:" in printed


def test_different_aspect_ratios_are_refused(media, tmp_path):
    wide = still_video(os.path.join(media["photos"], "p.png"), tmp_path / "wide.mp4", size="640x360")
    with pytest.raises(SystemExit):
        compare.main([media["sharp"], wide, "--out", str(tmp_path / "o"), "--no-video"])


def test_a_difference_under_five_percent_is_a_tie():
    w = compare.winners([{"detail": 1.00, "blown": 0.10}, {"detail": 1.03, "blown": 0.20}])
    assert w["detail"] is None and w["blown"] == 0
