"""shutter.py: linear-light averaging, offsets, the moving-range plan and the blend/interleave of real videos."""
import json
import os
import subprocess
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shutter  # noqa: E402
from quality.bins import ffmpeg, ffprobe  # noqa: E402


def solid_video(path, colors, size="64x48", fps=30):
    """One frame per colour (R,G,B) in yuv444p, near lossless."""
    w, h = map(int, size.split("x"))
    raw = b"".join(np.full((h, w, 3), c, np.uint8).tobytes() for c in colors)
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", size, "-r", str(fps), "-i", "-",
                    "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv444p", "-c:v", "libx264", "-qp", "0", str(path)],
                   input=raw, check=True)
    return str(path)


def frames_of(path, w=64, h=48):
    r = shutter.Reader(path, w, h)
    out = []
    while (f := r.read()) is not None:
        out.append(f)
    r.close()
    return out


def test_srgb_round_trip_is_exact_on_8_bit():
    v = np.arange(256, dtype=np.uint8)
    assert np.array_equal(shutter.to_srgb8(shutter.to_linear(v)), v)


def test_linear_average_of_black_and_white_is_brighter_than_the_gamma_average():
    mid = shutter.to_srgb8((shutter.to_linear(np.uint8(0)) + shutter.to_linear(np.uint8(255))) / 2)
    assert 185 <= int(mid) <= 189  # 50 % light is sRGB ~188, not 128


def test_offsets_spread_inside_the_shutter_and_split_sub_frames():
    o = shutter.offsets(1, 4, 180)
    assert [x[2] for x in o] == [0.0, 0.125, 0.25, 0.375]
    o2 = shutter.offsets(2, 2, 180)
    assert [(m, off) for m, _, off in o2] == [(0, 0.0), (0, 0.125), (1, 0.5), (1, 0.625)]


def test_plan_resamples_only_fast_travel(tmp_path):
    h, w = 120, 240
    xs, x = [], 20.0
    for k in range(45):  # 0–14 still · 15–24 drift 1 px/frame · 25–34 fast 14 px/frame · 35–44 still
        x += 1 if 15 <= k < 25 else 14 if 25 <= k < 35 else 0
        xs.append(int(x))
    frames = []
    for x in xs:
        f = np.full((h, w, 3), 210, np.uint8)
        f[45:75, x % (w - 20): x % (w - 20) + 20] = 25
        frames.append(f)
    path = str(tmp_path / "p.mp4")
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", "30", "-i", "-",
                    "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", path], input=b"".join(f.tobytes() for f in frames), check=True)
    ranges, n = shutter.plan(path, threshold=6.0, pad=1)
    assert n == 45
    moving = {f for a, b in ranges for f in range(a, b + 1)}
    assert moving, ranges
    assert min(moving) >= 22 and max(moving) <= 37, ranges  # the fast stretch (with padding), never the slow drift


def test_blend_averages_in_linear_light_only_where_a_ranged_pass_covers(tmp_path):
    base = solid_video(tmp_path / "p0.mp4", [(0, 0, 0)] * 6)
    extra = solid_video(tmp_path / "p1.mp4", [(255, 255, 255)] * 2)  # covers source frames 2..3 only
    out = str(tmp_path / "o.mp4")
    shutter.blend([{"m": 0, "j": 0, "start": 0, "end": 5, "path": base},
                   {"m": 0, "j": 1, "start": 2, "end": 3, "path": extra}], 6, 30, 1, out, crf=0)
    fs = frames_of(out)
    assert len(fs) == 6
    lum = [int(f[..., 1].mean()) for f in fs]
    assert lum[0] < 20 and lum[5] < 20
    assert 175 <= lum[2] <= 200 and 175 <= lum[3] <= 200


def test_blend_interleaves_two_sub_frames_into_double_rate(tmp_path):
    a = solid_video(tmp_path / "a.mp4", [(40, 40, 40)] * 4)
    b = solid_video(tmp_path / "b.mp4", [(200, 200, 200)] * 4)
    out = str(tmp_path / "o60.mp4")
    shutter.blend([{"m": 0, "j": 0, "start": 0, "end": 3, "path": a},
                   {"m": 1, "j": 0, "start": 0, "end": 3, "path": b}], 4, 30, 2, out, crf=0)
    fs = frames_of(out)
    assert len(fs) == 8
    lum = [int(f[..., 1].mean()) for f in fs]
    assert all(x < 70 for x in lum[0::2]) and all(x > 170 for x in lum[1::2])
    rate = subprocess.run([ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    assert rate == "60/1"


def test_blend_refuses_without_a_full_pass(tmp_path):
    a = solid_video(tmp_path / "a.mp4", [(1, 1, 1)] * 2)
    with pytest.raises(ValueError):
        shutter.blend([{"m": 0, "j": 0, "start": 1, "end": 2, "path": a}], 4, 30, 1, str(tmp_path / "x.mp4"))


def test_cli_offsets_prints_json(capsys):
    assert shutter.main(["offsets", "--mult", "1", "--samples", "2"]) == 0
    assert json.loads(capsys.readouterr().out)[1]["offset"] == 0.25
