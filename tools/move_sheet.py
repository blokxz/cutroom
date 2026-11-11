#!/usr/bin/env python3
"""Move sheet: a speed graph of every tracked element of a render, optionally under its contact sheet.

  move_sheet.py <track.json> [--strip contact-sheet.png] [--out sheet.png]

The graph shows each element's centre speed (px/frame) over the frames, with the beat boundaries as
vertical lines and the 80 px/frame blur threshold of the verifier as a dashed line. It is for judging a
move's feel at a glance: a good entrance rises fast and settles, a metronome is a flat line.
"""
import argparse
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BLUR_PX = 80
COLORS = [(198, 93, 74), (61, 74, 122), (60, 130, 90), (170, 120, 40), (110, 70, 150), (30, 30, 30)]


def speeds(track):
    """{id: [(frame, px/frame), ...]} from the centre of each element's box, frame to frame."""
    by = {}
    for r in sorted(track.get("records") or [], key=lambda r: r["f"]):
        by.setdefault(r["id"], []).append(r)
    out = {}
    for i, rs in by.items():
        pts = []
        for a, b in zip(rs, rs[1:]):
            df = b["f"] - a["f"]
            if df <= 0:
                continue
            dx = (b["x"] + b["w"] / 2) - (a["x"] + a["w"] / 2)
            dy = (b["y"] + b["h"] / 2) - (a["y"] + a["h"] / 2)
            pts.append((b["f"], math.hypot(dx, dy) / df))
        out[i] = pts
    return out


def video_speeds(path):
    """{'picture': [(frame, px/frame)]} measured from the pixels (optical flow, as the verifier measures it), the fps
    and the hard cuts: a sheet for any render, with or without tracked elements."""
    import cv2

    from quality import motion

    cap = cv2.VideoCapture(path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.release()
    an = motion.analyze(path, fps, w, n / fps)
    return {"picture": [(i, float(v)) for i, v in enumerate(an["speed"])]}, fps, an["cuts"]


def draw(track, strip=None, width=1400, height=420, sp=None):
    sp = sp if sp is not None else speeds(track)
    last = max([f for pts in sp.values() for f, _ in pts] + [1])
    top = min(max([v for pts in sp.values() for _, v in pts] + [BLUR_PX * 1.2]), BLUR_PX * 3)  # beyond 3x the limit a line is off scale
    pad = 56
    img = Image.new("RGB", (width, height), (250, 248, 243))
    d = ImageDraw.Draw(img)
    x = lambda f: pad + (width - 2 * pad) * f / last  # noqa: E731
    y = lambda v: height - pad - (height - 2 * pad) * v / top  # noqa: E731
    d.line([(pad, height - pad), (width - pad, height - pad)], fill=(120, 120, 120))
    d.line([(pad, pad), (pad, height - pad)], fill=(120, 120, 120))
    for k in range(0, int(top) + 1, 40):
        d.text((8, y(k) - 6), str(k), fill=(120, 120, 120))
    for xx in range(int(pad), int(width - pad), 14):  # dashed blur threshold
        d.line([(xx, y(BLUR_PX)), (xx + 7, y(BLUR_PX))], fill=(190, 60, 60))
    d.text((width - pad - 150, y(BLUR_PX) - 14), f"{BLUR_PX} px/frame blur limit", fill=(190, 60, 60))
    fps = track.get("fps", 30)
    for b in track.get("beats") or []:
        d.line([(x(b["f"]), pad), (x(b["f"]), height - pad)], fill=(215, 210, 200))
        d.text((x(b["f"]) + 3, pad - 14), f"{b.get('name', '')[:14]}", fill=(130, 130, 130))
    for n, (i, pts) in enumerate(sorted(sp.items())):
        c = COLORS[n % len(COLORS)]
        if len(pts) > 1:
            d.line([(x(f), y(min(v, top))) for f, v in pts], fill=c, width=2)
        d.text((pad + 8 + n * 150, height - pad + 12), f"- {i}", fill=c)
    d.text((pad, height - 18), f"frames 0–{last} ({last / fps:.1f} s) · px/frame of each tracked centre, or of the picture's optical flow (clipped at the top)", fill=(120, 120, 120))
    if strip and os.path.exists(strip):
        s = Image.open(strip).convert("RGB")
        s = s.resize((width, int(s.height * width / s.width)))
        both = Image.new("RGB", (width, s.height + height), (250, 248, 243))
        both.paste(s, (0, 0))
        both.paste(img, (0, s.height))
        return both
    return img


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", help="a render's .track.json, or a video (.mp4): speed then comes from the pixels")
    ap.add_argument("--strip", help="a contact sheet PNG to put above the graph")
    ap.add_argument("--out", help="output PNG (default: next to the track file)")
    a = ap.parse_args(argv)
    if a.track.lower().endswith((".mp4", ".mov", ".webm")):
        sp, fps, cuts = video_speeds(a.track)
        track = {"fps": fps, "beats": [{"f": c, "name": "cut"} for c in cuts]}
        strip = a.strip
        if not strip:
            from quality import motion

            strip = os.path.splitext(a.track)[0] + "-strip.png"
            motion.contact_sheet(a.track, strip)
        out = a.out or os.path.splitext(a.track)[0] + "-move-sheet.png"
        draw(track, strip, sp=sp).save(out)
    else:
        with open(a.track, encoding="utf-8") as f:
            track = json.load(f)
        out = a.out or a.track.replace(".track.json", "") + "-move-sheet.png"
        draw(track, a.strip).save(out)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
