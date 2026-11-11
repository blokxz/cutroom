"""Move sheet: speeds from track records and a PNG that has a graph under the strip."""
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import move_sheet as ms  # noqa: E402


def rec(f, i, x, y=0, w=100, h=100):
    return {"f": f, "id": i, "k": "shape", "x": x, "y": y, "w": w, "h": h, "o": 1}


def track():
    return {"fps": 30, "width": 1080, "height": 1920,
            "beats": [{"f": 0, "name": "open", "kind": "move"}, {"f": 10, "name": "rest", "kind": "rest"}],
            "records": [rec(f, "a", x) for f, x in enumerate([0, 10, 30, 60, 60, 60, 60, 60, 60, 60, 60])]
                       + [rec(f, "b", 0, y=f * 3) for f in range(11)]}


def test_speeds_are_centre_distance_per_frame():
    sp = ms.speeds(track())
    assert [round(v) for _, v in sp["a"]][:4] == [10, 20, 30, 0]
    assert all(abs(v - 3) < 1e-9 for _, v in sp["b"])


def test_speeds_skip_repeated_frames():
    t = {"records": [rec(1, "a", 0), rec(1, "a", 50), rec(2, "a", 60)]}
    assert [round(v) for _, v in ms.speeds(t)["a"]] == [10]


def test_empty_track_still_draws(tmp_path):
    img = ms.draw({"records": []})
    assert img.size == (1400, 420)


def test_cli_writes_png_with_strip_on_top(tmp_path):
    tp = tmp_path / "x.track.json"
    tp.write_text(json.dumps(track()), encoding="utf-8")
    Image.new("RGB", (1600, 300), (10, 20, 30)).save(tmp_path / "strip.png")
    out = tmp_path / "sheet.png"
    assert ms.main([str(tp), "--strip", str(tmp_path / "strip.png"), "--out", str(out)]) == 0
    im = Image.open(out)
    assert im.width == 1400 and im.height == 1400 * 300 // 1600 + 420
    assert im.getpixel((5, 5)) == (10, 20, 30)


def test_a_video_gets_a_sheet_from_its_pixels(tmp_path):
    import subprocess

    import numpy as np
    from quality.bins import ffmpeg

    frames = []
    for k in range(40):
        f = np.full((128, 72, 3), 230, np.uint8)
        x = min(60, max(0, (k - 10) * 3))  # still, then a square slides right, then still
        f[50:70, x:x + 12] = 30
        frames.append(f)
    path = tmp_path / "m.mp4"
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "72x128", "-r", "30", "-i", "-",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(path)], input=b"".join(f.tobytes() for f in frames), check=True)
    sp, fps, cuts = ms.video_speeds(str(path))
    v = [s for _, s in sp["picture"]]
    assert fps == 30 and cuts == []
    assert max(v[12:28]) > max(v[:8]) and max(v[12:28]) > max(v[34:])
    out = tmp_path / "sheet.png"
    assert ms.main([str(path), "--out", str(out)]) == 0
    assert Image.open(out).width == 1400
