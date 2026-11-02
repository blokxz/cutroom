"""Platform-agnostic checks on the picture analysis and the audio."""
import numpy as np


def rhythm(an, report):
    m = an["metrics"]
    beats = an["beats"]
    if m["still_fraction"] < 0.12:
        report.fail("rhythm", f'only {m["still_fraction"]:.0%} of the time is near-still — the frame never rests')
    elif m["still_fraction"] > 0.8:
        report.warn("rhythm", f'{m["still_fraction"]:.0%} near-still — check it is not a static slide')
    if m["longest_rest_s"] < 0.8:
        report.fail("rhythm", f'longest rest is {m["longest_rest_s"]}s; give the viewer at least one ≥0.8s rest')
    if len(beats) >= 3 and m["beat_length_cv"] < 0.3:
        report.fail("rhythm", f'beats have almost equal length (cv {m["beat_length_cv"]}) — reads as a metronome / slideshow')
    if len(beats) >= 2 and m["beat_length_ratio"] < 3:
        report.warn("rhythm", f'longest beat is only {m["beat_length_ratio"]}× the shortest; aim for ≥3–4×')


def cuts(an, report):
    c, fps = an["cuts"], an["fps"]
    if len(c) >= 3:
        gaps = np.diff(c) / fps
        if np.std(gaps) / (np.mean(gaps) + 1e-9) < 0.25:
            report.fail("cuts", f"{len(c)} hard cuts at a regular interval — slideshow cadence")
    if len(c) >= 2 and not any(g < 0.6 for g in np.diff(c) / fps):
        report.warn("cuts", "hard cuts are isolated scene changes; prefer carrying an element across, or group cuts into a quick burst")


def curves(an, report):
    m = an["metrics"]
    if m["moves"] >= 4 and m["t80_iqr"] is not None and m["t80_iqr"] <= 0.08:
        report.warn("curves", f'all {m["moves"]} moves share one curve (t80 {m["t80_median"]} ± {m["t80_iqr"]}) — mix snaps, springs and glides')
    if m["t80_median"] is not None and m["t80_median"] > 0.82:
        report.warn("curves", f'moves start slowly or run linear (median t80 {m["t80_median"]}) — arrivals land better front-loaded (snap / spring)')


def speed_without_track(an, report):
    fast = [i for i, v in enumerate(an["speed"]) if v > 80]
    if fast:
        ts = ", ".join(f"{i / an['fps']:.2f}" for i in fast[:6])
        report.warn("speed", f"{len(fast)} frames move faster than 80 px/frame (max {an['metrics']['max_speed_px_per_frame']}) at {ts}s — make sure they have motion blur")


def ending_hold(an, report, level="FAIL"):
    m = an["metrics"]
    if m["end_still_fraction"] < 0.7:
        report.add(level, "ending", f'the last seconds are still only {m["end_still_fraction"]:.0%} of the time — the call to action needs a readable hold')


def audio_levels(media, lufs, peak, report, lufs_range=(-20, -12), peak_max=-1.0, required=False):
    if not media["audio"]:
        report.add("FAIL" if required else "WARN", "audio", "no audio track")
        return
    if peak is not None and peak > peak_max:
        report.fail("audio", f"true peak {peak} dBFS — keep it ≤ {peak_max}")
    if lufs is not None and not (lufs_range[0] <= lufs <= lufs_range[1]):
        report.warn("audio", f"integrated loudness {lufs} LUFS; aim for {lufs_range[0]}…{lufs_range[1]} (≈ −16 for social)")
