"""Picture integrity and scene changes, measured from pixels (no tracking needed).

Measurements (computed inside motion.analyze, from the same decoding pass):
  frame_levels     per-frame mean grey level and 99th percentile → near-black frames, overall brightness
  bar_widths       black bars along each edge of a full-resolution frame (letterbox / pillarbox):
                   flat bands with a straight, stable content edge — not the dark margins of a dark design
  scene_changes    moments where the content changes a lot, each classed motion / dissolve / cut / still

Verdicts:
  check_integrity          black frames, frozen picture, black bars, overall brightness
  check_scene_continuity   share of scene changes that happen in motion (only without a .track.json)

Every threshold lives in limits.py.
"""
import numpy as np

from . import limits as L

SCENE_KINDS = ("motion", "dissolve", "cut", "still")


# ------------------------------------------------------------------ measurements
def frame_levels(grey):
    """Per-frame mean grey level and 99th percentile (grey: list of 2-D uint8 frames)."""
    mean = np.array([float(g.mean()) for g in grey])
    p99 = np.array([float(np.partition(g.ravel(), int(0.99 * (g.size - 1)))[int(0.99 * (g.size - 1))]) for g in grey])
    return mean, p99


def bar_widths(grey_full, level=L.BORDER_LEVEL):
    """Thickness in px of the black bars at the top, bottom, left and right of one full-resolution grey frame;
    None when the whole frame is black (no bars to measure).

    A dark edge only counts as a bar when it looks like one: the band is one flat level (no texture, no
    gradient), and the picture starts at a straight edge — the rows / columns just inside are clearly
    brighter across most of their length — on a content region whose background is not the bar's own
    colour. A typographic piece on a near-black background has dark margins, but its first lit row holds
    a few glyph pixels on the same black, so it reports 0 there."""
    rows = grey_full.max(axis=1) > level
    cols = grey_full.max(axis=0) > level
    if not rows.any():
        return None
    top = int(np.argmax(rows))
    bottom = int(np.argmax(rows[::-1]))
    left = int(np.argmax(cols))
    right = int(np.argmax(cols[::-1]))
    h, w = grey_full.shape
    inner = grey_full[top:h - bottom, left:w - right]
    background = float(np.median(inner[::4, ::4])) if inner.size else 0.0
    # (side width, band of the bar, band just inside the content edge) for each side, oriented as rows
    g, gt = grey_full, grey_full.T
    skip, depth = L.BORDER_EDGE_SKIP_PX, L.BORDER_EDGE_DEPTH_PX
    sides = (
        (top, lambda v: g[:v], lambda v: g[v + skip:v + skip + depth]),
        (bottom, lambda v: g[h - v:], lambda v: g[max(0, h - v - skip - depth):h - v - skip]),
        (left, lambda v: gt[:v], lambda v: gt[v + skip:v + skip + depth]),
        (right, lambda v: gt[w - v:], lambda v: gt[max(0, w - v - skip - depth):w - v - skip]),
    )
    return tuple(v if v and _is_bar(band(v), edge(v), background) else 0 for v, band, edge in sides)


def _is_bar(band, edge, background):
    """A flat band followed by a straight, clearly brighter content edge, on content that is not the bar's colour."""
    if band.size == 0 or edge.size == 0:
        return False
    band = band.astype(np.float32)
    level = float(band.mean())
    if float(band.std()) > L.BORDER_UNIFORM_STD:
        return False
    if abs(background - level) < L.BORDER_EDGE_CONTRAST:
        return False
    lit = np.abs(edge.astype(np.float32) - level) >= L.BORDER_EDGE_CONTRAST
    return float(lit.mean()) >= L.BORDER_EDGE_SHARE


def scene_changes(grey, diff, fps):
    """Moments where the picture content changes a lot, each classed as
      motion    the change happens while things move (a push, an iris, a flip, a carried element)
      dissolve  the frames in between are a blend of the picture before and the picture after
      cut       one frame jumps, the frames around it barely change
      still     the content changes but no frame visibly moves (a very slow fade)
    grey: frames as 2-D uint8 arrays (analysis size); diff: per-frame mean grey change (diff[0] = 0)."""
    import cv2

    n = len(grey)
    k = max(1, round(L.SCENE_WINDOW_S * fps))
    if n < 2 * k + 2:
        return []
    window = np.zeros(n)
    for i in range(k, n - k):
        window[i] = float(cv2.absdiff(grey[i + k], grey[i - k]).mean())
    edge = round(L.SCENE_EDGE_S * fps)
    sep = round(L.SCENE_SEPARATION_S * fps)
    r = round(L.SCENE_CONTEXT_S * fps)
    peaks = []
    for i in np.argsort(-window):
        if window[i] < L.SCENE_MIN_CHANGE:
            break
        if not (edge <= i < n - edge) or any(abs(int(i) - j) < sep for j in peaks):
            continue
        # a change of moment stands out from the motion around it (a slow zoom changes the picture steadily, not at once)
        if window[i] < L.SCENE_PROMINENCE * float(np.median(window[max(k, i - r):min(n - k, i + r + 1)])):
            continue
        peaks.append(int(i))
    return [_classify(grey, diff, fps, i, k, float(window[i])) for i in sorted(peaks)]


def _classify(grey, diff, fps, i, k, change):
    n = len(grey)
    lo, hi = max(1, i - k), min(n - 1, i + k)
    j = int(lo + np.argmax(diff[lo:hi + 1]))  # the frame that changes most
    out = dict(t=round(i / fps, 2), change=round(change, 1))
    before = diff[j - 1] if j - 1 >= 1 else 0.0
    after = diff[j + 1] if j + 1 < n else 0.0
    if diff[j] >= L.CUT_MIN_DIFF and max(before, after) < L.CUT_NEIGHBOUR_SHARE * diff[j]:
        return {**out, "kind": "cut"}
    # the transition: frames around j that change at least a share of what j changes
    thr = max(L.STILL_PEAK_DIFF, L.SCENE_SPAN_SHARE * diff[j])
    reach = round(L.SCENE_SPAN_MAX_S * fps)
    s = j
    while s - 1 >= 1 and diff[s - 1] > thr and j - s < reach:
        s -= 1
    e = j
    while e + 1 < n and diff[e + 1] > thr and e - j < reach:
        e += 1
    if diff[s:e + 1].max() < L.STILL_PEAK_DIFF:
        return {**out, "kind": "still"}
    # dissolve test: each frame of the transition against a blend of its neighbours m frames either side.
    # A cross-fade is a blend at every instant (also when the pictures drift slowly underneath);
    # a push, an iris or a flip is not — pixels jump from one picture to the other.
    m = max(1, round(L.BLEND_NEIGHBOUR_S * fps))
    resid = []
    for t in range(s, e):
        p, q = grey[max(0, t - m)].astype(np.float32), grey[min(n - 1, t + m)].astype(np.float32)
        x = grey[t].astype(np.float32)
        pq = q - p
        spread = float(np.abs(pq).mean())
        if spread < 1.0:
            continue
        alpha = float(((x - p) * pq).sum() / (float((pq * pq).sum()) + 1e-9))
        resid.append(float(np.abs(x - (p + alpha * pq)).mean()) / spread)
    rr = float(np.median(resid)) if resid else 1.0
    out["blend_residual"] = round(rr, 2)
    return {**out, "kind": "dissolve" if rr < L.DISSOLVE_RESIDUAL else "motion"}


def summarize_scenes(changes):
    counts = {k: sum(1 for c in changes if c["kind"] == k) for k in SCENE_KINDS}
    share = counts["motion"] / len(changes) if changes else 1.0
    return counts, share


# ------------------------------------------------------------------ verdicts
def _hold_ranges(track):
    """Frame ranges of beats declared as holds in a .track.json (j, by_id) — deliberate stills."""
    if not track:
        return []
    from .track import beat_kind

    j = track[0]
    beats = sorted(j.get("beats", []), key=lambda b: b["f"])
    out = []
    for n, b in enumerate(beats):
        if beat_kind(b) in ("hold", "rest"):
            end = beats[n + 1]["f"] if n + 1 < len(beats) else 10 ** 9
            out.append((b["f"], end))
    return out


def check_integrity(an, report, track=None):
    """Black frames (FAIL), frozen picture (WARN), black bars (FAIL on opposite sides, WARN on one), brightness (WARN)."""
    from .motion import segments

    ig = an.get("integrity")
    if not ig:
        return
    fps, n = an["fps"], len(an["diff"])
    edge = round(L.EDGE_IGNORE_S * fps)

    # black frames
    black = (np.asarray(ig["mean"]) < L.BLACK_MEAN) & (np.asarray(ig["p99"]) < L.BLACK_P99)
    inner = black.copy()
    inner[:edge] = False
    inner[max(0, n - edge):] = False
    runs = segments(inner)
    report.metrics["black_frames"] = int(inner.sum())
    for s, ln in runs:
        report.fail("black", f"near-black frames at {s / fps:.2f}–{(s + ln) / fps:.2f}s — a gap or a missing layer, not a fade at the edges")

    # frozen picture: identical frames (diff below encoder noise); the run that reaches the end is the final hold
    same = np.asarray(an["diff"]) < L.FROZEN_DIFF
    same[0] = False
    holds = _hold_ranges(track)
    longest = 0.0
    for s, ln in segments(same):
        start, end = s - 1, s + ln  # frames start .. end-1 show the same picture
        dur = (end - start) / fps
        if end >= n:
            report.metrics["final_hold_s"] = round(dur, 2)
            if dur > L.FROZEN_END_MAX_S:
                report.warn("frozen", f"the last {dur:.1f}s are one frozen picture — longer than a call-to-action hold needs (≤ {L.FROZEN_END_MAX_S:.0f}s); did the composition end early?")
            continue
        longest = max(longest, dur)
        if dur < L.FROZEN_WARN_S:
            continue
        inside = max((min(end, b) - max(start, a) for a, b in holds), default=0)
        msg = f"the picture is frozen (identical frames) at {start / fps:.2f}–{end / fps:.2f}s ({dur:.1f}s)"
        if inside >= 0.8 * (end - start):
            report.info("frozen", msg + " — inside a declared hold, so deliberate")
        else:
            report.warn("frozen", msg + " — keep something alive (a drift, a breath) or shorten it")
    report.metrics["frozen_max_s"] = round(longest, 2)

    # black bars
    bars = [b for b in ig.get("bars", []) if b is not None]
    if bars:
        arr = np.array(bars)
        side = [int(np.percentile(arr[:, c], 100 * (1 - L.BORDER_PRESENT_SHARE))) for c in range(4)]
        # a real bar has a stable content edge: where it is present, its width barely changes across frames
        for c in range(4):
            present = arr[arr[:, c] > 0, c]
            if side[c] and np.ptp(np.percentile(present, [10, 90])) > L.BORDER_EDGE_JITTER_PX:
                side[c] = 0
        top, bottom, left, right = side
        report.metrics["black_bars_px"] = f"top {top}, bottom {bottom}, left {left}, right {right}"
        lim = L.BORDER_FAIL_PX
        if top >= lim and bottom >= lim:
            report.fail("borders", f"black bars top and bottom ({top}/{bottom}px) — the picture is letterboxed; render at the platform's size instead of fitting a wider frame")
        elif left >= lim and right >= lim:
            report.fail("borders", f"black bars left and right ({left}/{right}px) — the picture is pillarboxed; render at the platform's size instead of fitting a taller frame")
        else:
            for name, v in zip(("top", "bottom", "left", "right"), side):
                if v >= lim:
                    report.warn("borders", f"a black band {v}px thick along the {name} edge for the whole video — check it is part of the design")

    # brightness
    mean = float(np.mean(ig["mean"])) if len(ig["mean"]) else None
    if mean is not None:
        report.metrics["mean_luma"] = round(mean, 1)
        lo, hi = L.LUMA_RANGE
        if mean < lo:
            report.warn("luma", f"mean brightness {mean:.0f}/255 — very dark; phones in daylight will show mostly black")
        elif mean > hi:
            report.warn("luma", f"mean brightness {mean:.0f}/255 — washed out; detail in the whites will be lost")


def check_scene_continuity(an, report):
    """Without tracking: how scene changes happen. Most of them should happen in motion, not as dissolves or cuts between stills."""
    changes = an.get("scene_changes")
    if changes is None:
        return
    counts, share = summarize_scenes(changes)
    total = len(changes)
    report.metrics["scene_change_kinds"] = ", ".join(f"{counts[k]} {k}" for k in SCENE_KINDS)
    report.metrics["changes_in_motion"] = f"{counts['motion']}/{total}" if total else "n/a"
    if total < L.SCENE_MIN_CHANGES:
        report.info("scenes", f"{total} scene change(s) found in the pixels — too few to judge how moments connect")
        return
    detail = f"{counts['dissolve']} dissolves, {counts['cut']} hard cuts, {counts['still']} without visible motion"
    where = ", ".join(f"{c['t']:.1f}s {c['kind']}" for c in changes if c["kind"] != "motion")
    if share < L.MOTION_FAIL_SHARE:
        report.fail("scenes", f"only {counts['motion']}/{total} scene changes happen in motion ({detail}: {where}) — reads as a slideshow; "
                              "carry an element, push or iris from one moment into the next")
    elif share < L.MOTION_WARN_SHARE:
        report.warn("scenes", f"{counts['motion']}/{total} scene changes happen in motion ({detail}: {where}) — aim for ≥ {L.MOTION_WARN_SHARE:.0%}")
