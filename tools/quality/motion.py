"""Picture-level analysis of a video: rhythm, cuts, speed, motion curves, and
comparison against a reference clip. Platform-agnostic.

The same decoding pass feeds integrity.py (frame levels, black bars, scene changes).
"""
import os

import cv2
import numpy as np

from .limits import BORDER_SAMPLE_S  # full-resolution frames are measured for black bars every 0.5 s

ANALYSIS_W = 270  # frames are analysed downscaled to this width
STILL_THR = 0.35  # mean grey-level change per frame that counts as "nothing is moving"
STILL_SPEED = 2.0  # px/frame (full resolution) of the fastest-moving pixels below which nothing travels


DILATE = np.ones((5, 5), np.uint8)
WORKERS = max(1, min(8, os.cpu_count() or 1))  # frame pairs are independent: optical flow runs in parallel threads


def read_frames(path, width=ANALYSIS_W, keep=(), bars_every=0):
    """All frames downscaled to `width`; full-resolution copies of the frame indices in `keep`
    (contact sheet, layout samples) are kept from the same pass so the file is decoded once.
    With bars_every=N, every Nth full-resolution frame is also measured for black bars (integrity.bar_widths)."""
    from .integrity import bar_widths

    cap = cv2.VideoCapture(path)
    frames, full, bars, keep = [], {}, [], set(keep)
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if len(frames) in keep:
            full[len(frames)] = f
        if bars_every and len(frames) % bars_every == 0:
            bars.append(bar_widths(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)))
        h, w = f.shape[:2]
        frames.append(cv2.resize(f, (width, int(h * width / w)), interpolation=cv2.INTER_AREA))
    cap.release()
    if bars_every:
        return frames, full, bars
    return frames, full


def frame_count(path):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return n


def video_fps(path):
    cap = cv2.VideoCapture(path)
    f = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return f or None


def sheet_indices(total, n=8):
    return [int((k + 0.5) * total / n) for k in range(n)]


def sample_indices(duration, fps, n=6):
    total = max(1, int(duration * fps))
    return [int((k + 0.5) * total / n) for k in range(n)]


def _flow_speed(prev_g, g, ad):
    """95th-percentile optical-flow speed (analysis px/frame) where the picture actually changed.
    Flat areas produce phantom vectors, so only pixels near a real change count; with 50 or fewer
    such pixels the speed is 0 whatever the flow says, so the flow is skipped (still frames)."""
    changed = cv2.dilate(ad, DILATE) > 4
    if np.count_nonzero(changed) <= 50:
        return 0.0
    flow = cv2.calcOpticalFlowFarneback(prev_g, g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag = np.linalg.norm(flow, axis=2)
    moving = mag[(mag > 0.3) & changed]
    return float(np.percentile(moving, 95)) if moving.size > 50 else 0.0


def motion_series(frames, scale, grey=None):
    """Per-frame mean absolute change, 95th-percentile optical-flow speed (full-res px/frame), histogram correlation."""
    grey = grey if grey is not None else [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    diff, hist_corr = [0.0], [1.0]
    ads = []
    prev_h = cv2.calcHist([frames[0]], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
    cv2.normalize(prev_h, prev_h)
    for k in range(1, len(frames)):
        ad = cv2.absdiff(grey[k], grey[k - 1])
        ads.append(ad)
        diff.append(float(np.mean(ad)))
        h = cv2.calcHist([frames[k]], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
        cv2.normalize(h, h)
        hist_corr.append(float(cv2.compareHist(prev_h, h, cv2.HISTCMP_CORREL)))
        prev_h = h

    def one(k):
        return _flow_speed(grey[k - 1], grey[k], ads[k - 1]) * scale

    ks = range(1, len(frames))
    if WORKERS > 1 and len(frames) > 8:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(WORKERS) as ex:
            flows = list(ex.map(one, ks, chunksize=8))
    else:
        flows = [one(k) for k in ks]
    return np.array(diff), np.array([0.0] + flows), np.array(hist_corr)


def segments(mask):
    """Runs of True in a boolean array → list of (start, length)."""
    out, start = [], None
    for i, m in enumerate(list(mask) + [False]):
        if m and start is None:
            start = i
        elif not m and start is not None:
            out.append((start, i - start))
            start = None
    return out


def smooth(x, n):
    return x if n <= 1 else np.convolve(x, np.ones(n) / n, mode="same")


def motion_curves(speed, still, fps, min_len=0.25):
    """For each active stretch, t80 = share of the stretch's duration needed to cover 80 % of its motion.
    ≈0.35–0.5 front-loaded (snaps, springs), ≈0.6–0.7 ease-in-out, ≈0.8 linear, >0.85 slow starts."""
    out = []
    for s, l in segments(~still):
        if l / fps < min_len:
            continue
        v = speed[s:s + l]
        total = v.sum()
        if total < 30:  # almost no measurable travel
            continue
        cum = np.cumsum(v) / total
        t80 = (int(np.argmax(cum >= 0.8)) + 1) / l
        out.append(dict(start_s=round(s / fps, 2), dur_s=round(l / fps, 2), t80=round(float(t80), 2)))
    return out


CACHE_VERSION = 3  # 2: integrity measurements and scene changes


def _cache_file(path):
    folder = os.environ.get("CUTROOM_ANALYSIS_CACHE")
    if not folder:
        return None
    import hashlib

    st = os.stat(path)
    key = f"{CACHE_VERSION}|{os.path.abspath(path)}|{st.st_size}|{st.st_mtime_ns}|{ANALYSIS_W}|{STILL_THR}|{STILL_SPEED}"
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, hashlib.sha1(key.encode()).hexdigest() + ".pkl")


def analyze(path, fps, width, duration, keep=()):
    """Picture analysis. `keep`: frame indices to return at full resolution in an["full_frames"].
    Set CUTROOM_ANALYSIS_CACHE=<dir> to reuse the analysis of an unchanged file (same path, size, mtime);
    a cached analysis has no full-resolution frames (callers fall back to seeking)."""
    import pickle

    cf = _cache_file(path)
    if cf and os.path.exists(cf):
        try:
            return pickle.load(open(cf, "rb"))
        except Exception:
            pass
    an = _analyze(path, fps, width, duration, keep)
    if cf:
        try:
            pickle.dump({**an, "full_frames": {}}, open(cf, "wb"))
        except OSError:
            pass
    return an


def _analyze(path, fps, width, duration, keep):
    from . import integrity

    frames, full, bars = read_frames(path, keep=keep, bars_every=max(1, round(BORDER_SAMPLE_S * fps)))
    scale = width / ANALYSIS_W
    grey = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    diff, speed, hist_corr = motion_series(frames, scale, grey)
    level_mean, level_p99 = integrity.frame_levels(grey)
    scenes = integrity.scene_changes(grey, diff, fps)
    burnt = integrity.burnt_frames(grey)
    _, scene_share = integrity.summarize_scenes(scenes)
    # still = little change overall AND no measurable travel (small elements on a big ground barely change the mean)
    still = (smooth(diff, 3) < STILL_THR) & (smooth(speed, 3) < STILL_SPEED)
    rests = [(s / fps, l / fps) for s, l in segments(still) if l / fps >= 0.25]
    active = [(s / fps, l / fps) for s, l in segments(~still) if l / fps >= 0.1]
    cuts = [i for i in range(1, len(diff)) if diff[i] > 18 and hist_corr[i] < 0.55]
    beats = [l for _, l in rests + active]
    curves = motion_curves(speed, still, fps)
    t80 = [c["t80"] for c in curves]
    tail = int(min(1.5, duration / 4) * fps)
    first = frames[0] if frames else None
    last = frames[-1] if frames else None
    loop_diff = float(np.mean(cv2.absdiff(first, last))) if first is not None else None
    hook = float(np.mean(diff[1:int(fps) + 1])) if len(diff) > fps else 0.0
    return dict(
        full_frames=full, diff=diff, speed=speed, still=still, fps=fps, rests=rests, active=active, cuts=cuts, beats=beats, curves=curves,
        integrity=dict(mean=level_mean, p99=level_p99, bars=bars), scene_changes=scenes, burnt=burnt,
        metrics=dict(
            still_fraction=round(float(np.mean(still)), 2),
            longest_rest_s=round(max([l for _, l in rests], default=0), 2),
            rests=len(rests), active_stretches=len(active),
            beat_length_ratio=round(max(beats) / min(beats), 1) if len(beats) >= 2 else 1.0,
            beat_length_cv=round(float(np.std(beats) / np.mean(beats)), 2) if len(beats) >= 3 else 1.0,
            median_beat_s=round(float(np.median(beats)), 2) if beats else 0,
            hard_cuts=[round(c / fps, 2) for c in cuts],
            bursts=bursts(cuts, fps),
            cuts_per_10s=round(len(cuts) / max(duration, 1e-6) * 10, 2),
            max_speed_px_per_frame=round(float(speed.max())) if len(speed) else 0,
            fast_frames=int((speed > 80).sum()),
            moves=len(curves),
            t80_median=round(float(np.median(t80)), 2) if t80 else None,
            t80_iqr=round(float(np.percentile(t80, 75) - np.percentile(t80, 25)), 2) if len(t80) >= 2 else None,
            end_still_fraction=round(float(np.mean(still[-tail:])), 2) if tail else 0.0,
            first_second_motion=round(hook, 2),
            loop_seam_diff=round(loop_diff, 1) if loop_diff is not None else None,
            scene_changes_found=len(scenes),
            scene_changes_in_motion=round(scene_share, 2),
            burnt_frames=len(burnt),
        ),
    )


LEVELS = " .:-=+*#%@"


def energy_map(diff, fps, cuts=(), row_s=4.0, cols=48):
    """The motion energy as text, one row per `row_s` seconds: blank = still, @ = the most energetic moment of the
    piece, | = a hard cut. Reads like a score: where the piece rests, where it moves, where it cuts."""
    if len(diff) == 0:
        return []
    e = smooth(np.asarray(diff, float), 3)
    top = max(float(np.percentile(e, 99)), 1e-6)
    per = row_s * fps / cols  # frames per column
    cut_cols = {int(c / per) for c in cuts}
    rows, n_cols = [], int(np.ceil(len(e) / per))
    for r0 in range(0, n_cols, cols):
        chars = []
        for c in range(r0, min(r0 + cols, n_cols)):
            if c in cut_cols:
                chars.append("|")
                continue
            seg = e[int(c * per): max(int(c * per) + 1, int((c + 1) * per))]
            lv = min(len(LEVELS) - 1, int(round(float(seg.mean()) / top * (len(LEVELS) - 1))))
            chars.append(LEVELS[lv])
        rows.append(f"{r0 * per / fps:5.1f}s |{''.join(chars)}|")
    return rows


def bursts(cuts, fps, gap_s=0.5, min_cuts=3):
    """Groups of at least `min_cuts` hard cuts each within `gap_s` of the previous one: [(t0, t1, n)]."""
    out, cur = [], []
    for c in sorted(cuts):
        if cur and (c - cur[-1]) / fps > gap_s:
            if len(cur) >= min_cuts:
                out.append((round(cur[0] / fps, 2), round(cur[-1] / fps, 2), len(cur)))
            cur = []
        cur.append(c)
    if len(cur) >= min_cuts:
        out.append((round(cur[0] / fps, 2), round(cur[-1] / fps, 2), len(cur)))
    return out


def frame_sheet(path, out, every_s=0.5, cols=8, width=180):
    """Every `every_s` seconds of a video, tiled `cols` across, with the time in a corner: the whole piece on one page."""
    import subprocess

    from .bins import ffmpeg

    n = frame_count(path)
    fps_in = video_fps(path) or 30
    rows = max(1, int(np.ceil(n / (every_s * fps_in) / cols)))
    vf = (f"fps={1 / every_s},scale={width}:-2,drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize=12:fontcolor=white:box=1:boxcolor=black@0.5,"
          f"tile={cols}x{rows}")
    r = subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", path, "-vf", vf, "-frames:v", "1", out], capture_output=True, text=True)
    if r.returncode != 0:  # drawtext needs a font; fall back to untimed tiles
        subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", path, "-vf", f"fps={1 / every_s},scale={width}:-2,tile={cols}x{rows}",
                        "-frames:v", "1", out], check=True)
    return out


def energy_profile(diff, n=100):
    """Motion energy resampled to n points and normalised — the 'shape' of a video's rhythm."""
    x = np.interp(np.linspace(0, len(diff) - 1, n), np.arange(len(diff)), smooth(diff, 5))
    return (x - x.mean()) / (x.std() + 1e-9)


def compare_reference(an, ref, report):
    """Rhythm of this video vs a reference clip the client likes. WARNs where they diverge."""
    a, r = an["metrics"], ref["metrics"]
    rows = [("still_fraction", 0.15), ("cuts_per_10s", 1.5), ("median_beat_s", None), ("t80_median", 0.15), ("longest_rest_s", None)]
    print("\n  vs reference               this      reference")
    for k, tol in rows:
        print(f"  {k:26} {str(a.get(k)):9} {r.get(k)}")
    corr = float(np.corrcoef(energy_profile(an["diff"]), energy_profile(ref["diff"]))[0, 1])
    print(f"  {'energy_profile_corr':26} {corr:.2f}")
    for title, x in (("this", an), ("reference", ref)):
        print(f"\n  energy map — {title}  (blank still · @ peak · | cut)")
        for row in energy_map(x["diff"], x["fps"], x["cuts"]):
            print("  " + row)
    report.metrics["reference_energy_corr"] = round(corr, 2)
    if abs(a["still_fraction"] - r["still_fraction"]) > 0.15:
        report.warn("reference", f"still time {a['still_fraction']:.0%} vs reference {r['still_fraction']:.0%}")
    if abs(a["cuts_per_10s"] - r["cuts_per_10s"]) > 1.5:
        report.warn("reference", f"{a['cuts_per_10s']} cuts per 10 s vs reference {r['cuts_per_10s']}")
    if a["median_beat_s"] and r["median_beat_s"] and not (0.5 <= a["median_beat_s"] / r["median_beat_s"] <= 2):
        report.warn("reference", f"median beat {a['median_beat_s']}s vs reference {r['median_beat_s']}s")
    if a["t80_median"] is not None and r["t80_median"] is not None and abs(a["t80_median"] - r["t80_median"]) > 0.15:
        kind = lambda t: "snappier" if t < r["t80_median"] else "softer/slower"
        report.warn("reference", f"moves are {kind(a['t80_median'])} than the reference (t80 {a['t80_median']} vs {r['t80_median']})")
    if corr < 0.1:
        report.info("reference", f"the energy over time has a different shape from the reference (corr {corr:.2f}) — fine if intended")


def contact_sheet(path, out, n=8, frames=None):
    """n frames side by side. `frames` = {index: full-res frame} already decoded (from analyze(keep=...))."""
    frames = frames or {}
    total = None
    tiles = []
    cap = None
    for k in range(n):
        if total is None:
            total = frame_count(path)
        idx = int((k + 0.5) * total / n)
        f = frames.get(idx)
        if f is None:
            cap = cap or cv2.VideoCapture(path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, f = cap.read()
            f = f if ok else None
        if f is not None:
            h, w = f.shape[:2]
            tiles.append(cv2.resize(f, (200, int(h * 200 / w))))
    if cap is not None:
        cap.release()
    if tiles:
        cv2.imwrite(out, np.hstack(tiles))


def frame_at(path, index, frames=None):
    """Full-resolution frame `index`; taken from `frames` ({index: frame}) when it was kept during analysis."""
    if frames and index in frames:
        return frames[index]
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, f = cap.read()
    cap.release()
    return f if ok else None


def busy_regions(img, regions, centre):
    """Edge density inside named regions (x0, y0, x1, y1) compared with a reference 'centre' region.
    Returns [(name, density)] for regions with dense, text-like detail."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    e = cv2.Canny(g, 80, 200) > 0
    cx0, cy0, cx1, cy1 = centre
    c = e[cy0:cy1, cx0:cx1].mean() + 1e-6
    out = []
    for name, (x0, y0, x1, y1) in regions.items():
        band = e[max(0, y0):y1, max(0, x0):x1]
        if band.size and band.mean() > 0.035 and band.mean() > 0.6 * c:
            out.append((name, round(float(band.mean()), 3)))
    return out
