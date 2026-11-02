"""Loudness and peak of a file's audio (EBU R128 via ffmpeg)."""
import re
import subprocess

from .bins import ffmpeg


def audio_stats(path):
    r = subprocess.run([ffmpeg(), "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = r.stderr
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
    peak = re.findall(r"Peak:\s+(-?[\d.inf]+) dBFS", txt)
    return (float(lufs[-1]) if lufs else None, float(peak[-1]) if peak and peak[-1] != "-inf" else None)
