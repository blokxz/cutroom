"""Shared pieces of the platform modules: dated spec files, technical checks, UI-area layout
checks and the core video flow. A platform module keeps only what is specific to it.

Spec files live in platforms/specs/<name>.json (override the folder with CUTROOM_SPECS_DIR).
Each carries "reviewed": "YYYY-MM-DD" and source URLs; verify.py warns when it is stale.
"""
import datetime
import json
import os

from .. import checks, integrity

SPECS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specs")
STALE_DAYS = 180
CODEC_NAMES = {"h264": "H.264", "hevc": "HEVC", "vp8": "VP8", "vp9": "VP9", "av1": "AV1", "aac": "AAC", "mp3": "MP3", "opus": "Opus"}


def load_spec(name):
    folder = os.environ.get("CUTROOM_SPECS_DIR") or SPECS_DIR
    path = os.path.join(folder, f"{name}.json")
    spec = json.load(open(path, encoding="utf-8"))
    spec["_path"] = path
    return spec


def spec_age_days(spec, today=None):
    today = today or datetime.date.today()
    try:
        reviewed = datetime.date.fromisoformat(spec["reviewed"])
    except (KeyError, ValueError):
        return None
    return (today - reviewed).days


def check_reviewed(spec, report, today=None, max_days=STALE_DAYS):
    age = spec_age_days(spec, today)
    report.metrics["specs_reviewed"] = spec.get("reviewed", "unknown")
    if age is None:
        report.warn("specs", f"{spec.get('label', spec.get('platform'))} specs have no valid 'reviewed' date — re-check the official specs")
    elif age > max_days:
        urls = ", ".join(s["url"] for s in spec.get("sources", [])[:2])
        report.warn("specs", f"{spec.get('label', spec.get('platform'))} specs were last reviewed {spec['reviewed']} ({age} days ago) — "
                             f"re-check the official specs ({urls}) and update {os.path.basename(spec['_path'])}")


def ratio_name(w, h):
    r = w / h
    for name, v in (("9:16", 9 / 16), ("4:5", 0.8), ("3:4", 0.75), ("1:1", 1.0), ("1.91:1", 1.91), ("16:9", 16 / 9)):
        if abs(r - v) < 0.01:
            return name
    return f"{r:.2f}:1"


def _names(codes):
    return " or ".join(CODEC_NAMES.get(c, c.upper()) for c in codes)


# ------------------------------------------------------------------ technical
def tech_video(m, video, fmt, report, label):
    """Technical limits. `video` = the platform's shared video limits, `fmt` = the format's (overrides)."""
    containers = fmt.get("containers", video["containers"])
    if not any(c in m["container"] for c in containers):
        report.fail("tech", f"container {m['container']} — use {' or '.join(c.upper() for c in containers[:2])}")
    if m["vcodec"] not in video["vcodecs"]:
        report.fail("tech", f"video codec {m['vcodec']} — use {_names(video['vcodecs'][:2])}")
    if m["pix_fmt"] and "420" not in m["pix_fmt"]:
        report.fail("tech", f"pixel format {m['pix_fmt']} — needs 4:2:0 (yuv420p)")
    if m["pix_fmt"] and m["pix_fmt"].startswith("yuvj"):
        report.warn("tech", f"{m['pix_fmt']} is full-range — encode yuv420p (limited range) so colours don't shift after processing")
    if m["field_order"] not in (None, "progressive", "unknown"):
        report.fail("tech", f"interlaced ({m['field_order']}) — needs progressive scan")
    lo, hi = video["fps"]
    if not (lo <= m["fps"] <= hi + 0.01):
        report.fail("tech", f"{m['fps']:.2f} fps — {label} accepts {lo}–{hi}")
    if "max_w" in video and m["w"] > video["max_w"]:
        report.fail("tech", f"width {m['w']}px — max {video['max_w']}px")
    if "max_side" in video and max(m["w"], m["h"]) > video["max_side"]:
        report.fail("tech", f"{m['w']}x{m['h']} — {label} takes at most {video['max_side']}px per side")
    if "min_side" in video and min(m["w"], m["h"]) < video["min_side"]:
        report.fail("tech", f"{m['w']}x{m['h']} — {label} needs at least {video['min_side']}px per side")
    if "min_res" in fmt:
        mw, mh = fmt["min_res"]
        if m["w"] < mw or m["h"] < mh:
            report.fail("tech", f"{m['w']}x{m['h']} — this format needs at least {mw}x{mh}")
    if "max_ratio" in video and m["w"] / m["h"] > video["max_ratio"] + 0.005:
        report.fail("tech", f"aspect {ratio_name(m['w'], m['h'])} is wider than square — {label} only takes square or vertical video")
    vbr = m["vbitrate"]
    if vbr and "max_vbr" in video and vbr > video["max_vbr"]:
        report.fail("tech", f"video bitrate {vbr / 1e6:.1f} Mbps — max {video['max_vbr'] / 1e6:.0f} Mbps")
    if vbr and "min_vbr" in fmt and vbr < fmt["min_vbr"]:
        report.fail("tech", f"video bitrate {vbr / 1e3:.0f} kbps — this format needs at least {fmt['min_vbr'] / 1e3:.0f} kbps")
    rec_vbr = video.get("rec_vbr_hfr" if m["fps"] > 45 else "rec_vbr", video.get("rec_vbr"))
    if vbr and rec_vbr and max(m["w"], m["h"]) >= 1900 and vbr < 0.5 * rec_vbr:
        report.info("tech", f"video bitrate {vbr / 1e6:.1f} Mbps — {label} recommends ≈{rec_vbr / 1e6:.0f} Mbps at 1080p for uploads; fine for flat graphics, raise it for photos and footage")
    if m["size_bytes"] > fmt["max_mb"] * 1e6:
        report.fail("tech", f"file is {m['size_bytes'] / 1e6:.0f} MB — max {fmt['max_mb']} MB for this format")
    elif "warn_mb" in video and m["size_bytes"] > video["warn_mb"] * 1e6:
        report.warn("tech", f"file is {m['size_bytes'] / 1e6:.0f} MB — the {label} mobile apps may refuse files over ≈{video['warn_mb']} MB; upload from the web")
    lo, hi = fmt["dur"]
    if not (lo <= m["duration"] <= hi):
        report.fail("tech", f"duration {m['duration']:.1f}s — this format takes {lo}–{hi}s")
    rlo, rhi = fmt["rec_dur"]
    if lo <= m["duration"] <= hi and not (rlo <= m["duration"] <= rhi):
        report.warn("duration", f"{m['duration']:.1f}s — {rlo}–{rhi}s works best for this format")
    if m["audio"]:
        if m["acodec"] not in video["acodecs"]:
            report.fail("tech", f"audio codec {m['acodec']} — use {_names(video['acodecs'][:1])}")
        if m["sample_rate"] > video["max_sr"]:
            report.fail("tech", f"audio sample rate {m['sample_rate']} Hz — max {video['max_sr'] // 1000} kHz")
        if m["channels"] > video["max_ch"]:
            report.fail("tech", f"{m['channels']} audio channels — mono or stereo only")
    if m["moov_first"] is False:
        report.warn("tech", f"moov atom is at the end — {video['moov_note']}")
    if m["keyframe_interval"] and m["keyframe_interval"] > 5:
        report.warn("tech", f"keyframes every {m['keyframe_interval']:.1f}s — use ≤2s (closed GOP) for clean processing")
    if m["color_primaries"] not in (None, "unknown", "bt709", "bt470bg", "smpte170m"):
        report.warn("tech", f"colour primaries {m['color_primaries']} — {label} expects SDR BT.709; HDR/wide gamut may shift colours")
    size_advice(m, fmt, report, label)


def size_advice(m, fmt, report, label):
    rw, rh = fmt["rec"]
    if (m["w"], m["h"]) != (rw, rh):
        if abs(m["w"] / m["h"] - rw / rh) > 0.01:
            report.warn("size", f"{m['w']}x{m['h']} ({ratio_name(m['w'], m['h'])}) — recommended {rw}x{rh} ({ratio_name(rw, rh)}); expect cropping or bars")
        elif m["w"] < rw:
            report.warn("size", f"{m['w']}x{m['h']} — under {rw}px wide looks soft after {label}'s processing")


# ------------------------------------------------------------------ layout
def _scaled_blocks(blocks, scale):
    return {name: tuple(int(v * scale) for v in rect) for name, rect in (blocks or {}).items()}


def ui_regions(w, h, fmt, scale, caution=False):
    """Named rectangles the platform UI covers, in pixels of a w x h frame."""
    t, b, l, r = (v * scale for v in fmt["ui_caution" if caution and "ui_caution" in fmt else "ui"])
    regs = {}
    if t:
        regs["top UI band"] = (0, 0, w, int(t))
    if b:
        regs["bottom UI band"] = (0, int(h - b), w, h)
    if r > 64 * scale:
        regs["right action bar"] = (int(w - r), int(t), w, int(h - b))
    regs.update(_scaled_blocks(fmt.get("ui_caution_blocks" if caution else "ui_blocks"), scale))
    return regs


def layout_image(img, w, h, fmt, report, label="", extra=None):
    """Heuristic (no tracking available): dense detail where the UI (or `extra` regions) will cover it."""
    from ..motion import busy_regions

    scale = w / fmt["rec"][0]
    regs = ui_regions(w, h, fmt, scale)
    regs.update(extra or {})
    centre = (int(w * 0.2), int(h * 0.3), int(w * 0.8), int(h * 0.7))
    for name, d in busy_regions(img, regs, centre):
        report.warn("layout", f"{label}dense detail in the {name} (edge density {d}) — check no text or logo sits there")


def layout_track(j, by_id, fmt, report):
    from ..track import element_checks

    element_checks(j, by_id, report, fmt["ui"], min_text_h=fmt.get("min_text", 0), blocked=fmt.get("ui_blocks"),
                   caution=fmt.get("ui_caution"), caution_blocked=fmt.get("ui_caution_blocks"))


def sample_frames_layout(m, fmt, report, n=6, ctx_frames=None):
    """Without tracking: look for dense detail under the UI on a few frames spread over the video."""
    from ..motion import frame_at, sample_indices

    kept = (ctx_frames or {})
    for idx in sample_indices(m["duration"], m["fps"], n):
        f = frame_at(m["path"], idx, kept)
        if f is not None:
            layout_image(f, m["w"], m["h"], fmt, report, label=f"{idx / m['fps']:.1f}s: ")


# ------------------------------------------------------------------ core video flow
def core_video(ctx, fmt):
    """Rhythm, cuts, curves, ending hold, picture integrity, faces; hook and loop for formats that autoplay in a feed."""
    an, report = ctx["analysis"], ctx["report"]
    integrity.check_integrity(an, report, ctx.get("track"))
    checks.rhythm(an, report)
    checks.cuts(an, report)
    checks.curves(an, report)
    checks.ending_hold(an, report, fmt["end_hold"])
    mm = an["metrics"]
    if fmt.get("hook") and mm["first_second_motion"] < 0.3:
        report.warn("hook", "the first second is nearly static — viewers decide in the first second; open on movement or a strong frame")
    if fmt.get("loop"):
        report.info("loop", f"last→first frame difference {mm['loop_seam_diff']} (low = seamless loop, which helps replays)")
    from ..faces import check_faces

    check_faces(ctx["media"], an, report)


def track_reading(ctx):
    """With --track: reading time of every text element."""
    from ..track import reading_time

    j, by_id = ctx["track"]
    reading_time(j, by_id, ctx["report"])


def pixel_continuity(ctx):
    """Without --track: how scene changes happen, from the pixels (the track's continuity check rules when there is one)."""
    integrity.check_scene_continuity(ctx["analysis"], ctx["report"])


def track_or_heuristic(ctx, fmt):
    """With --track: continuity + element checks against the UI areas. Without: speed and busy-region heuristics."""
    m, report = ctx["media"], ctx["report"]
    if ctx.get("track"):
        from ..track import continuity

        j, by_id = ctx["track"]
        continuity(j, by_id, report)
        layout_track(j, by_id, fmt, report)
        track_reading(ctx)
        return True
    pixel_continuity(ctx)
    checks.speed_without_track(ctx["analysis"], report)
    sample_frames_layout(m, fmt, report, ctx_frames=ctx["analysis"].get("full_frames"))
    return False


def vertical_video_check(ctx, spec, fmt_name):
    """The whole check for a vertical-video platform (TikTok, YouTube Shorts)."""
    m, report = ctx["media"], ctx["report"]
    fmt = spec["formats"][fmt_name]
    report.metrics["platform/format"] = f"{spec['platform']} / {fmt_name}"
    if m["kind"] != "video":
        report.fail("format", f"{spec['label']} {fmt_name} expects a video, got a {m['kind']}")
        return
    report.metrics["size"] = f"{m['w']}x{m['h']} ({ratio_name(m['w'], m['h'])})"
    tech_video(m, spec["video"], fmt, report, spec["label"])
    core_video(ctx, fmt)
    track_or_heuristic(ctx, fmt)
    checks.audio_levels(m, ctx["lufs"], ctx["peak"], report)
    if not m["audio"]:
        report.info("audio", f"{spec['label']} without sound relies entirely on on-screen text — add audio or make sure the message reads muted")
