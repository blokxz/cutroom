"""Reading a reference: the energy map, bursts of cuts, the frame sheet, and moving water that is not a cut."""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quality import motion  # noqa: E402
from quality.bins import ffmpeg  # noqa: E402


def raw_video(path, frames, fps=30):
    h, w, _ = frames[0].shape
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(path)], input=b"".join(f.tobytes() for f in frames), check=True)
    return str(path)


def test_bursts_group_close_cuts_only():
    fps = 30
    cuts = [30, 36, 42, 48, 200, 400, 405]  # four within 0.2 s, one alone, two close
    assert motion.bursts(cuts, fps) == [(1.0, 1.6, 4)]
    assert motion.bursts([], fps) == []


def test_energy_map_marks_still_moving_and_cut():
    fps = 30
    diff = np.zeros(240)
    diff[60:120] = 20.0  # 2–4 s moving
    rows = motion.energy_map(diff, fps, cuts=[180], row_s=4.0, cols=40)
    assert len(rows) == 2
    first = rows[0].split("|")[1]
    assert first[:15].strip() == ""       # the first 1.5 s are still
    assert "@" in first[20:40]            # the moving stretch peaks
    assert "|" in rows[1]                  # the cut at 6 s


def test_moving_water_is_not_a_cut_but_a_scene_switch_is(tmp_path):
    rng = np.random.default_rng(5)
    h, w = 180, 320
    water = rng.integers(40, 200, (h, w * 2, 3), dtype=np.uint8)
    water[..., 2] = 200  # blue-ish texture
    frames = [water[:, k * 6: k * 6 + w].copy() for k in range(45)]          # texture sliding fast, same colours
    other = np.zeros((h, w, 3), np.uint8)
    other[..., 0] = 220
    other[60:120, 100:220] = 30
    frames += [other.copy() for _ in range(30)]                                # a hard switch to another scene
    path = raw_video(tmp_path / "w.mp4", frames)
    an = motion.analyze(path, 30, w, len(frames) / 30)
    cuts_s = [c / 30 for c in an["cuts"]]
    assert len(cuts_s) == 1 and abs(cuts_s[0] - 1.5) < 0.1


def test_frame_sheet_tiles_the_whole_piece(tmp_path):
    frames = [np.full((64, 36, 3), v, np.uint8) for v in np.linspace(0, 255, 60).astype(np.uint8)]
    path = raw_video(tmp_path / "s.mp4", frames)
    out = motion.frame_sheet(path, str(tmp_path / "sheet.png"), every_s=0.5, cols=2, width=36)
    im = Image.open(out)
    assert im.width == 72 and im.height >= 64 * 2


def test_burnt_haze_counts_but_a_crisp_white_card_does_not():
    from quality import integrity

    h, w = 160, 90
    card = np.full((h, w), 60, np.uint8)
    card[30:130, 15:75] = 255                       # a white card with a hard edge
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(yy - h / 2, xx - w / 2)
    haze = np.clip(255 - np.maximum(0, r - 30) * 2.2, 60, 255).astype(np.uint8)  # white core melting into grey
    assert integrity.burnt_frames([card]) == []
    assert integrity.burnt_frames([haze]) == [0]
    assert integrity.burnt_frames([np.full((h, w), 120, np.uint8)]) == []
