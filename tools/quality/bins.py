"""External binaries. Set FFMPEG / FFPROBE to use a specific build; otherwise the ones on PATH."""
import os


def ffmpeg():
    return os.environ.get("FFMPEG") or "ffmpeg"


def ffprobe():
    return os.environ.get("FFPROBE") or "ffprobe"
