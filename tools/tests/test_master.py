"""tools/master.py: the encoded file, not the first pass, must respect the true-peak ceiling."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quality.audio import audio_stats  # noqa: E402
from quality.bins import ffmpeg  # noqa: E402

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def loud_clip(path):
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=3:r=30",
                    "-f", "lavfi", "-i", "sine=frequency=1000:duration=3,volume=0.98,aeval=val(0)*1.0+0.0:c=mono",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path], check=True)


def test_master_keeps_the_encoded_peak_under_the_ceiling(tmp_path):
    src, out = tmp_path / "loud.mp4", tmp_path / "mastered.mp4"
    loud_clip(str(src))
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "master.py"), str(src), "--out", str(out)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    lufs, peak = audio_stats(str(out))
    assert peak is not None and peak <= -1.4, (lufs, peak, r.stdout)
    assert lufs is not None and abs(lufs + 16) < 1.5, (lufs, peak)


def test_master_without_audio_does_nothing(tmp_path):
    src = tmp_path / "mute.mp4"
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=1:r=30",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(src)], check=True)
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "master.py"), str(src)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and "nothing to master" in r.stdout


def test_master_encodes_again_with_a_lower_ceiling_when_the_encode_overshoots(tmp_path, monkeypatch):
    import master

    ceilings, peaks = [], iter([-0.2, -1.6])
    monkeypatch.setattr(master, "encode", lambda v, d, lufs, tp: (ceilings.append(tp), open(d, "wb").close(), {"input_i": "0", "input_tp": "0"})[2])
    monkeypatch.setattr(master, "audio_stats", lambda p: (-16.0, next(peaks)))
    monkeypatch.setattr(master.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": "0\n"})())
    monkeypatch.setattr(sys, "argv", ["master.py", str(tmp_path / "in.mp4"), "--out", str(tmp_path / "out.mp4")])
    assert master.main() == 0
    assert len(ceilings) == 2 and ceilings[0] == -1.5 and ceilings[1] < -2.5  # lowered by the 1.3 dB overshoot + 0.1
