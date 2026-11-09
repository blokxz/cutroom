#!/usr/bin/env python3
"""Master the audio of a rendered video for social: two-pass EBU R128 loudness
normalisation to -16 LUFS integrated, -1.5 dBTP ceiling. The video stream is copied.

    python3 tools/master.py out/final.mp4               # writes out/final-master.mp4
    python3 tools/master.py in.mp4 --out out.mp4 --lufs -14
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quality.audio import audio_stats  # noqa: E402
from quality.bins import ffmpeg, ffprobe  # noqa: E402


def encode(video, dest, lufs, tp):
    """Two-pass loudnorm to `lufs` with a `tp` dBTP ceiling, AAC 192k, video copied. Returns the first-pass measurement."""
    target = f"I={lufs}:TP={tp}:LRA=11"
    p1 = subprocess.run([ffmpeg(), "-hide_banner", "-i", video, "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True)
    m = json.loads(p1.stderr[p1.stderr.rindex("{"): p1.stderr.rindex("}") + 1])
    af = (f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", video, "-c:v", "copy", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", dest], check=True)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--lufs", type=float, default=-16.0)
    ap.add_argument("--tp", type=float, default=-1.5)
    a = ap.parse_args()
    out = a.out or re.sub(r"\.mp4$", "", a.video) + "-master.mp4"

    has_audio = subprocess.run([ffprobe(), "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", a.video],
                               capture_output=True, text=True).stdout.strip()
    if not has_audio:
        print("no audio track — nothing to master")
        return 0

    dest = out + ".tmp.mp4" if os.path.abspath(out) == os.path.abspath(a.video) else out  # allow in-place
    ceiling = a.tp
    for attempt in range(3):
        m = encode(a.video, dest, a.lufs, ceiling)
        _, peak = audio_stats(dest)  # AAC can overshoot the ceiling it was normalised to; measure the encoded file
        if peak is None or peak <= a.tp + 0.05:
            break
        ceiling -= (peak - a.tp) + 0.1
        print(f"encoded true peak {peak} dBFS is above {a.tp}; encoding again with a {ceiling:.2f} dBTP ceiling")
    if dest != out:
        os.replace(dest, out)
    print(f"input {m['input_i']} LUFS / {m['input_tp']} dBTP  →  {out}" + (f" (true peak {peak} dBFS)" if peak is not None else ""))
    return 0


def _utf8_output():
    """Windows consoles and pipes default to a legacy code page; our messages use → ≤ —."""
    import sys as _sys
    for stream in (_sys.stdout, _sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


if __name__ == "__main__":
    _utf8_output()
    sys.exit(main())
