#!/usr/bin/env python3
"""Compare the picture quality of two renders of the same piece, side by side and in numbers.

  compare.py a.mp4 b.mp4 [--labels cutroom onetake] [--ref reference.mp4] [--photos <dir>]
             [--times 1.6,2.85,10.6] [--every 0.5] [--out compare/] [--blind --seed 7]

Writes to --out:
  side_by_side.mp4   both videos next to each other, labelled, with the audio of the first
  stills.png         the same instants of both, one above the other, plus a 2x crop of the centre (where captions sit)
  metrics.json       every number below, per video, and which one wins each
  blind/             (--blind) the two files under neutral names (X, Y in a seeded random order) and key.json

Numbers (sampled every --every seconds on the luma; higher or lower is better as marked):
  detail     ↑  mean absolute step between neighbouring pixels: texture that survived the render
  flat       ↓  share of neighbouring pixels with exactly the same value: areas washed into a flat field
  blown      ↓  share of pixels at or above 250: highlights burnt to white (a dense steam, an overexposed sky)
  banding    ↓  share of smooth row steps that are 1-level jumps between flat runs: stairs in gradients (grain does not count)
  sharpness  ↑  variance of the Laplacian: crisp edges and type
  blocks     ↓  ffmpeg blockdetect: compression blocks
  fidelity   ↑  (--photos) best SSIM of each sampled frame against the client's photos, cover-cropped and small,
                averaged over the frames that clearly show one: how much the render degrades the material
  rhythm        (--ref) still share, cuts per 10 s, median beat, longest rest and t80 from tools/verify.py, with the
                reference's own values beside them (closer is better)
The two videos must have the same aspect ratio; they may differ in size (both are measured at the smaller one).
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quality.bins import ffmpeg, ffprobe  # noqa: E402

TOOLS = os.path.dirname(os.path.abspath(__file__))
HIGHER = {"detail": True, "flat": False, "blown": False, "banding": False, "sharpness": True, "blocks": False, "fidelity": True}


# ------------------------------------------------------------------ reading frames
def probe(path):
    out = subprocess.run([ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,avg_frame_rate,bit_rate,pix_fmt:format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    num, den = (s.get("avg_frame_rate") or "30/1").split("/")
    return {"width": int(s["width"]), "height": int(s["height"]), "fps": float(num) / float(den or 1),
            "duration": float(j["format"]["duration"]), "bit_rate": int(s.get("bit_rate") or 0), "pix_fmt": s.get("pix_fmt")}


def frame_at(path, t, size):
    """One RGB frame at time t, scaled to size (w, h)."""
    w, h = size
    out = subprocess.run([ffmpeg(), "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    if len(out) < w * h * 3:
        raise RuntimeError(f"no frame at {t:.2f}s in {path}")
    return np.frombuffer(out[: w * h * 3], np.uint8).reshape(h, w, 3)


def luma(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


# ------------------------------------------------------------------ per-frame numbers
def detail_numbers(rgb):
    """detail, flat, blown, banding and sharpness of one frame (8-bit luma)."""
    y = np.round(luma(rgb.astype(np.float64)))
    gx = np.abs(np.diff(y, axis=1))
    gy = np.abs(np.diff(y, axis=0))
    steps = np.concatenate([gx.ravel(), gy.ravel()])
    detail = float(steps.mean())
    flat = float((steps == 0).mean())
    blown = float((y >= 250).mean())
    # banding: a single-level step with a flat run on both sides (≥ RUN pixels each way along the row) is the edge of a
    # band; count those per smooth step. A dithered or grainy ramp has 1-level steps too, but never between plateaus.
    banding = band_edges(gx)
    lap = y[1:-1, 1:-1] * 4 - y[:-2, 1:-1] - y[2:, 1:-1] - y[1:-1, :-2] - y[1:-1, 2:]
    return {"detail": detail, "flat": flat, "blown": blown, "banding": banding, "sharpness": float(lap.var())}


RUN = 3


def band_edges(gx):
    """Share of smooth row steps (≤ 2 levels) that are 1-level jumps between flat runs of at least RUN pixels."""
    smooth = gx <= 2
    if not smooth.any():
        return 0.0
    flat = (gx == 0).astype(np.int32)
    # run of flats ending just before / starting just after each step position
    c = np.pad(flat, ((0, 0), (1, 0))).cumsum(1)
    n = gx.shape[1]
    idx = np.arange(n)
    lo, hi = np.clip(idx - RUN, 0, n), np.clip(idx + 1 + RUN, 0, n)
    left_ok = (c[:, idx] - c[:, lo]) == (idx - lo)          # the RUN steps before are all flat
    right_ok = (c[:, hi] - c[:, idx + 1]) == (hi - idx - 1)  # the RUN steps after are all flat
    edges = (gx == 1) & left_ok & right_ok & (idx >= RUN) & (idx + RUN < n)
    return float(edges.sum() / smooth.sum())


def ssim(a, b):
    """Mean SSIM of two equal-size grey images (float 0–255), 7x7 box windows."""
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2

    def box(x):
        k = 7
        p = np.pad(x, k // 2, mode="edge")
        s = p.cumsum(0).cumsum(1)
        s = np.pad(s, ((1, 0), (1, 0)))
        return (s[k:, k:] - s[:-k, k:] - s[k:, :-k] + s[:-k, :-k]) / (k * k)

    ma, mb = box(a), box(b)
    va, vb = box(a * a) - ma * ma, box(b * b) - mb * mb
    cov = box(a * b) - ma * mb
    m = ((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma * ma + mb * mb + c1) * (va + vb + c2))
    return float(m.mean())


def cover(img, w, h):
    """The photo cover-cropped (centre) to w×h, like object-fit: cover."""
    iw, ih = img.size
    s = max(w / iw, h / ih)
    r = img.resize((max(w, round(iw * s)), max(h, round(ih * s))), Image.LANCZOS)
    x, y = (r.width - w) // 2, (r.height - h) // 2
    return r.crop((x, y, x + w, y + h))


def load_photos(folder, size):
    out = []
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            img = Image.open(os.path.join(folder, name)).convert("RGB")
            out.append((name, luma(np.asarray(cover(img, *size), np.float64))))
    return out


def fidelity(frames_small, photos, shown=0.45):
    """Mean best SSIM over the frames whose best match is at least `shown` (a photo clearly on screen)."""
    best = []
    for f in frames_small:
        y = luma(f.astype(np.float64))
        best.append(max(ssim(y, p) for _, p in photos))
    clear = [b for b in best if b >= shown]
    return (float(np.mean(clear)) if clear else None), len(clear)


def blockiness(path):
    r = subprocess.run([ffmpeg(), "-hide_banner", "-nostats", "-i", path, "-vf", "blockdetect,metadata=print:file=-",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    vals = [float(v) for v in re.findall(r"lavfi\.block=([\d.]+)", r.stdout + r.stderr)]
    return float(np.mean(vals)) if vals else None


def rhythm(path, ref):
    """still share, cuts per 10 s, median beat, longest rest, t80 from verify.py (and the reference's own)."""
    keys = ["still_fraction", "cuts_per_10s", "median_beat_s", "longest_rest_s", "t80_median"]
    with tempfile.TemporaryDirectory() as d:
        out = {}
        for tag, p in (("this", path), ("reference", ref)):
            j = os.path.join(d, f"{tag}.json")
            subprocess.run([sys.executable, os.path.join(TOOLS, "verify.py"), p, "--analyze", "--json", j],
                           capture_output=True, text=True, encoding="utf-8")
            m = json.load(open(j, encoding="utf-8"))["metrics"] if os.path.exists(j) else {}
            out[tag] = {k: m.get(k) for k in keys}
    return out


# ------------------------------------------------------------------ outputs
def side_by_side(a, b, labels, out, height=960):
    lab = [re.sub(r"[^\w .-]", "", x) for x in labels]
    fc = (f"[0:v]scale=-2:{height},drawtext=text='{lab[0]}':x=20:y=20:fontsize=34:fontcolor=white:box=1:boxcolor=black@0.5[a];"
          f"[1:v]scale=-2:{height},drawtext=text='{lab[1]}':x=20:y=20:fontsize=34:fontcolor=white:box=1:boxcolor=black@0.5[b];"
          "[a][b]hstack=inputs=2[v]")
    r = subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", a, "-i", b, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
                        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out],
                       capture_output=True, text=True)
    if r.returncode != 0:  # drawtext needs a font; fall back to unlabelled
        fc = f"[0:v]scale=-2:{height}[a];[1:v]scale=-2:{height}[b];[a][b]hstack=inputs=2[v]"
        subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", a, "-i", b, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
                        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out], check=True)


def stills(a, b, labels, times, size, out):
    """Per instant: a | b at a third of the size, then a 2x crop of the centre band of each."""
    w, h = size
    tw, th = w // 3, h // 3
    cw, ch = w // 2, h // 6  # centre crop, shown at 2x → w × h/3
    rows = []
    for t in times:
        fa, fb = Image.fromarray(frame_at(a, t, size)), Image.fromarray(frame_at(b, t, size))
        row = Image.new("RGB", (tw * 2 + cw * 2 * 2, th), "white")
        row.paste(fa.resize((tw, th)), (0, 0))
        row.paste(fb.resize((tw, th)), (tw, 0))
        box = ((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2)
        za, zb = fa.crop(box).resize((cw * 2, ch * 2)), fb.crop(box).resize((cw * 2, ch * 2))
        row.paste(za.crop((0, 0, cw * 2, min(th, ch * 2))), (tw * 2, 0))
        row.paste(zb.crop((0, 0, cw * 2, min(th, ch * 2))), (tw * 2 + cw * 2, 0))
        d = ImageDraw.Draw(row)
        d.text((6, 6), f"{labels[0]} {t:.2f}s", fill="red")
        d.text((tw + 6, 6), f"{labels[1]} {t:.2f}s", fill="red")
        rows.append(row)
    sheet = Image.new("RGB", (rows[0].width, th * len(rows)), "white")
    for i, r in enumerate(rows):
        sheet.paste(r, (0, i * th))
    sheet.save(out)


def blind(a, b, folder, seed):
    os.makedirs(folder, exist_ok=True)
    pair = [a, b]
    random.Random(seed).shuffle(pair)
    key = {}
    for name, src in zip(("X", "Y"), pair):
        dst = os.path.join(folder, f"{name}{os.path.splitext(src)[1]}")
        shutil.copyfile(src, dst)
        key[name] = os.path.abspath(src)
    with open(os.path.join(folder, "key.json"), "w", encoding="utf-8") as f:
        json.dump(key, f, indent=1)
    return key


def winners(nums):
    """{metric: 0|1|None} — which video wins each number (None: a tie or missing)."""
    w = {}
    for k, hi in HIGHER.items():
        a, b = nums[0].get(k), nums[1].get(k)
        if a is None or b is None or abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b)):
            w[k] = None
        else:
            w[k] = 0 if (a > b) == hi else 1
    return w


def measure(path, size, every, photos):
    info = probe(path)
    ts = np.arange(every / 2, info["duration"] - 0.05, every)
    per = [detail_numbers(frame_at(path, t, size)) for t in ts]
    nums = {k: float(np.mean([p[k] for p in per])) for k in per[0]}
    nums["blocks"] = blockiness(path)
    if photos:
        small = (size[0] // 4, size[1] // 4)
        nums["fidelity"], nums["fidelity_frames"] = fidelity([frame_at(path, t, small) for t in ts], photos)
    nums.update({"bit_rate_mbps": round(info["bit_rate"] / 1e6, 2), "pix_fmt": info["pix_fmt"],
                 "size": f"{info['width']}x{info['height']}", "duration_s": round(info["duration"], 2)})
    return nums


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--labels", nargs=2, default=["A", "B"])
    ap.add_argument("--ref")
    ap.add_argument("--photos")
    ap.add_argument("--times", default="", help="comma-separated seconds for stills.png (default: 5 evenly spaced)")
    ap.add_argument("--every", type=float, default=0.5)
    ap.add_argument("--out", default="compare")
    ap.add_argument("--blind", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--no-video", action="store_true", help="skip side_by_side.mp4")
    a = ap.parse_args(argv)
    ia, ib = probe(a.a), probe(a.b)
    if abs(ia["width"] / ia["height"] - ib["width"] / ib["height"]) > 0.01:
        sys.exit(f"different aspect ratios: {ia['width']}x{ia['height']} vs {ib['width']}x{ib['height']}")
    w = min(ia["width"], ib["width"])
    size = (w - w % 2, round(w * ia["height"] / ia["width"]) // 2 * 2)
    os.makedirs(a.out, exist_ok=True)
    photos = load_photos(a.photos, (size[0] // 4, size[1] // 4)) if a.photos else None
    nums = [measure(p, size, a.every, photos) for p in (a.a, a.b)]
    win = winners(nums)
    result = {"labels": a.labels, "files": [os.path.abspath(a.a), os.path.abspath(a.b)], "metrics": nums, "winner": win}
    if a.ref:
        result["rhythm"] = {lab: rhythm(p, a.ref) for lab, p in zip(a.labels, (a.a, a.b))}
    dur = min(ia["duration"], ib["duration"])
    times = [float(x) for x in a.times.split(",") if x.strip()] or [round(dur * k / 6, 2) for k in range(1, 6)]
    stills(a.a, a.b, a.labels, times, size, os.path.join(a.out, "stills.png"))
    if not a.no_video:
        side_by_side(a.a, a.b, a.labels, os.path.join(a.out, "side_by_side.mp4"))
    if a.blind:
        result["blind"] = sorted(blind(a.a, a.b, os.path.join(a.out, "blind"), a.seed))
    with open(os.path.join(a.out, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)

    arrow = {True: "↑", False: "↓"}
    print(f"{'':12}{a.labels[0]:>14}{a.labels[1]:>14}   better")
    for k, hi in HIGHER.items():
        v = [n.get(k) for n in nums]
        if v[0] is None and v[1] is None:
            continue
        fmt = lambda x: "—" if x is None else f"{x:.4f}" if abs(x) < 10 else f"{x:.1f}"  # noqa: E731
        mark = "" if win[k] is None else a.labels[win[k]]
        print(f"{k + ' ' + arrow[hi]:12}{fmt(v[0]):>14}{fmt(v[1]):>14}   {mark}")
    for k in ("bit_rate_mbps", "size", "pix_fmt"):
        print(f"{k:12}{str(nums[0][k]):>14}{str(nums[1][k]):>14}")
    if a.ref:
        ref = result["rhythm"][a.labels[0]]["reference"]
        print(f"\nrhythm vs reference{'':4}{a.labels[0]:>10}{a.labels[1]:>10}{'reference':>11}")
        for k in ref:
            vals = [result["rhythm"][lab]["this"].get(k) for lab in a.labels]
            print(f"  {k:20}{str(vals[0]):>10}{str(vals[1]):>10}{str(ref[k]):>11}")
    wins = [sum(1 for v in win.values() if v == i) for i in (0, 1)]
    print(f"\nwins: {a.labels[0]} {wins[0]} · {a.labels[1]} {wins[1]} — wrote {a.out}/")
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
