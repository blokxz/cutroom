"""Per-video analysis, read-only.

probe(path)    metadata: size after rotation, rotation, fps, duration, codec, audio, HDR (HLG / PQ / BT.2020).
analyze(path)  frames at 4 fps, 320 px wide, grey: per frame sharpness (Laplacian), luma, histogram change
               (scene cuts) and camera motion (Farneback optical flow; jitter = second difference of the flow).
               Windows of 2, 3 and 4 s are scored sharpness x exposure x stability x interest; windows containing
               a hard cut are discarded, dissolves are penalised. The best non-overlapping ones are kept.
               class: slideshow (mostly still frames), motion (real movement), mixed.
"""
import json
import math
import os
import subprocess

import cv2
import numpy as np

from quality.bins import ffmpeg, ffprobe

FPS = 4
WIDTH = 320
WINDOW_LENGTHS = (2.0, 3.0, 4.0)
HDR_TRANSFERS = {"arib-std-b67": "HLG", "smpte2084": "PQ"}
CUT = 0.35         # histogram change above this between two samples = hard cut
DISSOLVE = 0.08    # above this = transition / dissolve


def _rate(s):
    try:
        n, d = str(s).split("/")
        return float(n) / float(d) if float(d) else 0.0
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe(path):
    r = subprocess.run([ffprobe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe cannot read the file: {r.stderr.strip()[-300:]}")
    j = json.loads(r.stdout or "{}")
    vs = [s for s in j.get("streams", []) if s.get("codec_type") == "video"
          and not (s.get("disposition") or {}).get("attached_pic")]
    if not vs:
        raise RuntimeError("no video stream")
    v = vs[0]
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"])) % 360
    rot = rot or int(float((v.get("tags") or {}).get("rotate", 0))) % 360
    if rot in (90, 270):
        w, h = h, w
    transfer = v.get("color_transfer")
    primaries = v.get("color_primaries")
    hdr = transfer in HDR_TRANSFERS or primaries == "bt2020"
    dur = float((j.get("format") or {}).get("duration") or v.get("duration") or 0)
    fps = _rate(v.get("avg_frame_rate")) or _rate(v.get("r_frame_rate"))
    return {
        "width": w, "height": h, "rotation": rot, "fps": round(fps, 3), "duration_s": round(dur, 3),
        "codec": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
        "has_audio": any(s.get("codec_type") == "audio" for s in j.get("streams", [])),
        "hdr": bool(hdr), "hdr_format": HDR_TRANSFERS.get(transfer, "BT.2020" if hdr else None),
        "color": {"transfer": transfer, "primaries": primaries, "matrix": v.get("color_space")},
        "orientation": "portrait" if h > w * 1.05 else "landscape" if w > h * 1.05 else "square",
    }


def frames(path, meta):
    """Grey frames at FPS, WIDTH wide (ffmpeg applies the rotation)."""
    hh = max(2, int(round(WIDTH * meta["height"] / meta["width"] / 2)) * 2)
    r = subprocess.run([ffmpeg(), "-v", "error", "-i", path, "-an", "-vf",
                        f"fps={FPS},scale={WIDTH}:{hh},format=gray", "-f", "rawvideo", "-"], capture_output=True)
    a = np.frombuffer(r.stdout, np.uint8)
    n = len(a) // (WIDTH * hh)
    return a[: n * WIDTH * hh].reshape(n, hh, WIDTH)


def per_frame(F):
    n = len(F)
    m = {k: np.zeros(n) for k in ("lap", "luma", "p5", "p95", "change", "mag", "fx", "fy")}
    prev = prev_hist = None
    for i, f in enumerate(F):
        m["lap"][i] = cv2.Laplacian(f, cv2.CV_64F).var()
        m["luma"][i] = f.mean()
        m["p5"][i], m["p95"][i] = np.percentile(f, [5, 95])
        hist = cv2.calcHist([f], [0], None, [32], [0, 256]).flatten()
        hist /= hist.sum() + 1e-9
        if prev is not None:
            m["change"][i] = 0.5 * np.abs(hist - prev_hist).sum()
            half = (f.shape[1] // 2, f.shape[0] // 2)
            flow = cv2.calcOpticalFlowFarneback(cv2.resize(prev, half), cv2.resize(f, half), None,
                                                0.5, 2, 15, 2, 5, 1.1, 0)
            m["mag"][i] = np.median(np.hypot(flow[..., 0], flow[..., 1]))
            m["fx"][i] = np.median(flow[..., 0])
            m["fy"][i] = np.median(flow[..., 1])
        prev, prev_hist = f, hist
    return m


def windows(m, length_s, step=2):
    n = len(m["lap"])
    L = min(n, int(round(length_s * FPS)))
    out = []
    for a in range(0, max(1, n - L + 1), step):
        b = a + L
        s = slice(a, b)
        lap = float(np.median(m["lap"][s]))
        luma = float(m["luma"][s].mean())
        p5, p95 = float(m["p5"][s].min()), float(m["p95"][s].max())
        change = float(m["change"][a + 1:b].max()) if L > 1 else 0.0
        if change > CUT:
            continue
        mag = float(m["mag"][a + 1:b].mean()) if L > 1 else 0.0
        ax, ay = np.diff(m["fx"][a + 1:b]), np.diff(m["fy"][a + 1:b])
        jitter = float(np.sqrt((np.diff(ax) ** 2 + np.diff(ay) ** 2).mean())) if len(ax) > 2 else 0.0
        sharp = min(1.0, math.log1p(lap) / math.log1p(1200))
        exposure = 1.0 if (p5 > 12 and p95 < 248 and 55 < luma < 195) else 0.55
        stability = math.exp(-(jitter / (1.0 + mag)) / 0.5)   # shake relative to the movement: a smooth pan is fine
        interest = 0.7 if mag < 0.12 else 1.0 if mag < 12.0 else 0.6
        clean = 0.45 if change > DISSOLVE else 1.0
        length_bonus = 0.9 + 0.05 * (L / FPS - 2.0)              # slight preference for longer usable windows
        out.append({
            "start": round(a / FPS, 2), "end": round(b / FPS, 2), "duration": round(L / FPS, 2),
            "score": round(sharp * exposure * stability * interest * clean * length_bonus, 4),
            "sharpness": round(lap, 1), "luma": round(luma, 1), "jitter": round(jitter, 3),
            "motion": round(mag, 3), "change": round(change, 3),
        })
    return out


def best(ws, k=3):
    chosen = []
    for w in sorted(ws, key=lambda x: -x["score"]):
        if all(w["end"] <= c["start"] or w["start"] >= c["end"] for c in chosen):
            chosen.append(w)
        if len(chosen) == k:
            break
    return chosen


def analyze(path, k=3):
    meta = probe(path)
    rec = dict(meta, windows=[], cuts=[], warnings=[], errors=[])
    F = frames(path, meta)
    if len(F) < 4:
        rec["errors"].append("too short to analyse (under 1 s of frames)")
        rec.update({"class": "unknown", "still_fraction": 0.0, "motion_fraction": 0.0, "transition_fraction": 0.0})
        return rec
    m = per_frame(F)
    ws = []
    for L in WINDOW_LENGTHS:
        if L * FPS <= len(F):
            ws += windows(m, L)
    if not ws:
        ws = windows(m, len(F) / FPS)
    still = float((m["mag"][1:] < 0.03).mean())
    moving = float((m["mag"][1:] > 0.25).mean())
    trans = float((m["change"][1:] > DISSOLVE).mean())
    rec["class"] = "slideshow" if still > 0.55 else "motion" if moving > 0.25 else "mixed"
    rec["still_fraction"], rec["motion_fraction"], rec["transition_fraction"] = round(still, 3), round(moving, 3), round(trans, 3)
    rec["cuts"] = [round(i / FPS, 2) for i in np.nonzero(m["change"] > CUT)[0]]
    rec["windows"] = best(ws, k)
    if not rec["windows"]:
        rec["errors"].append("no usable window without a scene cut")
    if min(meta["width"], meta["height"]) < 720:
        rec["warnings"].append(f"low resolution ({meta['width']}x{meta['height']})")
    if meta["hdr"]:
        rec["warnings"].append(f"HDR ({meta['hdr_format']}): clips are tone-mapped to SDR BT.709")
    if rec["class"] == "slideshow":
        rec["warnings"].append("mostly still frames (slideshow / edited piece?)")
    if rec["windows"] and rec["windows"][0]["jitter"] > 1.0:
        rec["warnings"].append("shaky camera in the best window")
    return rec
