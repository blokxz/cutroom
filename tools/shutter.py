#!/usr/bin/env python3
"""Whole-frame shutter and 60 fps from several time-shifted renders of the same piece.

render.mjs renders a piece once at offset 0 (the full piece, with audio) and again at fractions of a frame
(input prop `timeOffset`). This tool plans which frames need the extra passes and blends them:

  shutter.py offsets --mult 1 --samples 4 --angle 180    the (sub-frame, sample, offset) list, as JSON
  shutter.py plan <pass0.mp4> [--threshold 8] [--pad 2]   frame ranges faster than 8 px/frame, as JSON [[a, b], ...]
  shutter.py blend --frames N --fps 30 --mult 1 --out out.mp4 --audio pass0.mp4 [--crf 14]
                   --pass m:j:start:end:path ...

Blending averages, per output frame, the samples of its sub-frame in linear light (sRGB decoded, averaged,
encoded again), never in gamma: a gamma average darkens edges and highlights. A sample that does not cover a
frame (a pass rendered only where the piece moves) is simply left out of that frame's average.
`--mult 2` writes 60 fps from a piece timed at 30: sub-frame m of frame f is the piece at f + m/2.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quality.bins import ffmpeg, ffprobe  # noqa: E402

# 8-bit sRGB → linear, and a fine table back
_LIN = np.array([(v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4 for v in range(256)], np.float32)


def to_linear(rgb8):
    return _LIN[rgb8]


def to_srgb8(lin):
    lin = np.clip(lin, 0.0, 1.0)
    s = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    return np.clip(np.round(s * 255), 0, 255).astype(np.uint8)


def offsets(mult=1, samples=4, angle=180.0):
    """[(m, j, offset)]: sub-frame m of every frame, sample j inside its open shutter, offset in source frames."""
    out = []
    open_frames = (angle / 360.0) / mult  # how long the shutter stays open, in source frames
    for m in range(mult):
        for j in range(samples):
            out.append((m, j, round(m / mult + open_frames * j / samples, 6)))
    return out


def probe(path):
    j = json.loads(subprocess.run([ffprobe(), "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                                   "stream=width,height,nb_read_packets", "-of", "json", path],
                                  capture_output=True, text=True, check=True).stdout)["streams"][0]
    return int(j["width"]), int(j["height"]), int(j["nb_read_packets"])


class Reader:
    """Frames of a video as RGB uint8, one at a time, in order."""

    def __init__(self, path, w, h):
        self.w, self.h = w, h
        self.p = subprocess.Popen([ffmpeg(), "-v", "error", "-i", path, "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=rgb24",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)

    def read(self):
        n = self.w * self.h * 3
        buf = self.p.stdout.read(n)
        if len(buf) < n:
            return None
        return np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 3)

    def close(self):
        self.p.stdout.close()
        self.p.wait()


def plan(path, threshold=8.0, pad=2):
    """Inclusive frame ranges where the picture travels faster than `threshold` px/frame (optical flow at the
    video's full width, as the verifier measures it). Below ~8 px/frame a 180° shutter smear is invisible, so slow
    pushes and drifting steam are not rendered again."""
    import cv2

    from quality import motion

    cap = cv2.VideoCapture(path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.release()
    speed = np.asarray(motion.analyze(path, fps, w, n / fps)["speed"], float)
    n = len(speed)
    moving = np.zeros(n, bool)
    for i in np.flatnonzero(speed > threshold):
        moving[max(0, i - 1): i + 1] = True  # speed[i] is the travel from frame i-1 to i
    ranges = []
    for i in np.flatnonzero(moving):
        a, b = max(0, i - pad), min(n - 1, i + pad)
        if ranges and a <= ranges[-1][1] + 1:
            ranges[-1][1] = int(max(ranges[-1][1], b))
        else:
            ranges.append([int(a), int(b)])
    return ranges, n


def blend(passes, frames, fps, mult, out, audio=None, crf=14, gop_s=2):
    """passes: [{m, j, start, end, path}] (inclusive frames of the source). Writes `frames * mult` frames at fps*mult."""
    full = [p for p in passes if p["start"] == 0 and p["end"] >= frames - 1]
    if not full:
        raise ValueError("no pass covers the whole piece")
    w, h, _ = probe(full[0]["path"])
    readers = {id(p): Reader(p["path"], w, h) for p in passes}
    rate = fps * mult
    enc = [ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(rate), "-i", "-"]
    if audio:
        enc += ["-i", audio, "-map", "0:v", "-map", "1:a?", "-c:a", "copy"]
    enc += ["-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-crf", str(crf),
            "-preset", "medium", "-g", str(int(rate * gop_s)), "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", "-shortest", out]
    w_p = subprocess.Popen(enc, stdin=subprocess.PIPE)
    try:
        for f in range(frames):
            for m in range(mult):
                acc, n = None, 0
                for p in passes:
                    if p["m"] != m or not (p["start"] <= f <= p["end"]):
                        continue
                    img = readers[id(p)].read()
                    if img is None:
                        continue
                    lin = to_linear(img)
                    acc = lin if acc is None else acc + lin
                    n += 1
                if n == 0:
                    raise ValueError(f"no sample for frame {f} sub-frame {m}")
                w_p.stdin.write(to_srgb8(acc / n).tobytes())
    finally:
        w_p.stdin.close()
        w_p.wait()
        for r in readers.values():
            r.close()
    if w_p.returncode != 0:
        raise RuntimeError("encoding the blended video failed")


def parse_pass(spec):
    m, j, a, b, path = spec.split(":", 4)
    return {"m": int(m), "j": int(j), "start": int(a), "end": int(b), "path": path}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("offsets")
    o.add_argument("--mult", type=int, default=1)
    o.add_argument("--samples", type=int, default=4)
    o.add_argument("--angle", type=float, default=180.0)
    p = sub.add_parser("plan")
    p.add_argument("video")
    p.add_argument("--threshold", type=float, default=8.0, help="px/frame of optical flow")
    p.add_argument("--pad", type=int, default=2)
    b = sub.add_parser("blend")
    b.add_argument("--frames", type=int, required=True)
    b.add_argument("--fps", type=float, default=30)
    b.add_argument("--mult", type=int, default=1)
    b.add_argument("--out", required=True)
    b.add_argument("--audio")
    b.add_argument("--crf", type=int, default=14)
    b.add_argument("--pass", dest="passes", action="append", required=True, help="m:j:start:end:path")
    a = ap.parse_args(argv)
    if a.cmd == "offsets":
        print(json.dumps([{"m": m, "j": j, "offset": off} for m, j, off in offsets(a.mult, a.samples, a.angle)]))
    elif a.cmd == "plan":
        ranges, n = plan(a.video, a.threshold, a.pad)
        print(json.dumps({"frames": int(n), "ranges": [[int(a), int(b)] for a, b in ranges], "moving": int(sum(r[1] - r[0] + 1 for r in ranges))}))
    else:
        blend([parse_pass(s) for s in a.passes], a.frames, a.fps, a.mult, a.out, a.audio, a.crf)
        print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
