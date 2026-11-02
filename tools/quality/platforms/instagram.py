"""Instagram: reels, stories (video and image), feed videos, feed images, carousels, reel covers.

Technical limits follow the Instagram Graph API publishing requirements (the strictest
path; the app accepts a bit more). Layout rules: the UI-covered areas of stories and
reels, and the 3:4 crop the profile grid applies to every post.

The numbers live in specs/instagram.json, with the date they were last reviewed and their sources.
"""
import os

from . import common
from .. import checks
from ..media import probe_media
from ..track import text_boxes_at

NAME = "instagram"
SPEC = common.load_spec(NAME)
LABEL = SPEC["label"]
VIDEO = SPEC["video"]
IMAGE = SPEC["image"]
FORMATS = SPEC["formats"]  # ui = margins text must respect (top, bottom, left, right) in px at the recommended size
ALIASES = {"post": None, "feed": None, "image": None}  # resolved by media kind in resolve()


def resolve(fmt, media):
    if fmt in (None, "auto"):
        return detect(media)
    if fmt in ALIASES:
        return "feed_video" if media["kind"] == "video" else "feed_image"
    if fmt == "story" and media["kind"] == "image":
        return "story_image"
    if fmt not in FORMATS:
        raise SystemExit(f"unknown instagram format {fmt!r}; choose from {', '.join(FORMATS)} (or post/story/auto)")
    return fmt


def detect(media):
    if media["kind"] == "dir":
        return "carousel"
    r = media["w"] / media["h"]
    tall = abs(r - 9 / 16) < 0.02
    if media["kind"] == "image":
        return "story_image" if tall else "feed_image"
    return "reel" if tall else "feed_video"


_ratio_name = common.ratio_name


# ------------------------------------------------------------------ technical
def tech_video(m, spec, report):
    common.tech_video(m, VIDEO, spec, report, LABEL)


def tech_image(m, spec, report):
    if m["format"] not in IMAGE["formats"]:
        report.warn("tech", f"{m['format']} — the API publishes JPEG only (the app converts other formats, with recompression)")
    if m["size_bytes"] > IMAGE["max_mb"] * 1e6:
        report.fail("tech", f"file is {m['size_bytes'] / 1e6:.1f} MB — max {IMAGE['max_mb']} MB")
    if m["w"] < IMAGE["min_w"]:
        report.fail("tech", f"width {m['w']}px — under {IMAGE['min_w']}px gets upscaled and soft")
    if m["w"] > IMAGE["max_w"]:
        report.warn("tech", f"width {m['w']}px — Instagram scales anything over {IMAGE['max_w']}px down; export at 1080")
    r = m["w"] / m["h"]
    if spec is FORMATS["feed_image"] and not (IMAGE["ratio"][0] - 0.005 <= r <= IMAGE["ratio"][1] + 0.005):
        report.fail("tech", f"aspect {_ratio_name(m['w'], m['h'])} — feed images must be between 4:5 and 1.91:1 (they get cropped)")
    if m["icc"] and "srgb" not in m["icc"].lower():
        report.warn("tech", f"colour profile '{m['icc']}' — convert to sRGB or colours will shift")
    if m["has_alpha"]:
        report.warn("tech", "transparency gets flattened onto black or white — flatten it yourself on the right background")
    _size_advice(m, spec, report)


def _size_advice(m, spec, report):
    common.size_advice(m, spec, report, LABEL)


# ------------------------------------------------------------------ layout
def grid_crop_rect(w, h):
    """The 3:4 window the profile grid shows (x0, y0, x1, y1)."""
    if w / h > 0.75:  # wider than 3:4: sides are trimmed
        cw = round(h * 0.75)
        return ((w - cw) // 2, 0, (w + cw) // 2, h)
    ch = round(w / 0.75)
    return (0, (h - ch) // 2, w, (h + ch) // 2)


def grid_regions(w, h):
    x0, y0, x1, y1 = grid_crop_rect(w, h)
    regs = {}
    if x0 > 4:
        regs["left strip cut by the 3:4 grid"] = (0, 0, x0, h)
        regs["right strip cut by the 3:4 grid"] = (x1, 0, w, h)
    if y0 > 4:
        regs["top strip cut by the 3:4 grid"] = (0, 0, w, y0)
        regs["bottom strip cut by the 3:4 grid"] = (0, y1, w, h)
    return regs


def layout_image(img, w, h, spec, report, label=""):
    """Heuristic (no tracking available): dense detail where the UI or the grid crop will cut."""
    common.layout_image(img, w, h, spec, report, label, extra=grid_regions(w, h) if spec.get("grid_crop") else None)


def layout_track(j, by_id, spec, fmt, report, cover_frame):
    W, H = j["width"], j["height"]
    common.layout_track(j, by_id, spec, report)
    if spec.get("grid_crop"):
        x0, y0, x1, y1 = grid_crop_rect(W, H)
        f = cover_frame if cover_frame is not None else 0
        for i, r in text_boxes_at(by_id, f, W, H):
            if r["x"] < x0 - 2 or r["y"] < y0 - 2 or r["x"] + r["w"] > x1 + 2 or r["y"] + r["h"] > y1 + 2:
                what = "cover frame" if fmt == "reel" else "frame"
                report.warn("grid", f'text "{i}" on the {what} ({f}) falls outside the 3:4 profile-grid crop — it will be cut on the grid')


# ------------------------------------------------------------------ check entry point
def check(ctx):
    m, fmt, report = ctx["media"], ctx["format"], ctx["report"]
    if fmt == "carousel":
        return check_carousel(ctx)
    spec = FORMATS[fmt]
    if spec["kind"] != m["kind"]:
        report.fail("format", f"{fmt} expects a {spec['kind']}, got a {m['kind']}")
        return
    report.metrics["platform/format"] = f"instagram / {fmt}"
    report.metrics["size"] = f"{m['w']}x{m['h']} ({_ratio_name(m['w'], m['h'])})"

    if m["kind"] == "image":
        tech_image(m, spec, report)
        import cv2

        img = cv2.imread(m["path"])
        if img is not None:
            layout_image(img, m["w"], m["h"], spec, report)
        return

    tech_video(m, spec, report)
    common.core_video(ctx, spec)
    if ctx.get("track"):
        from ..track import continuity

        j, by_id = ctx["track"]
        continuity(j, by_id, report)
        layout_track(j, by_id, spec, fmt, report, ctx.get("cover_frame"))
        common.track_reading(ctx)
    else:
        common.pixel_continuity(ctx)
        checks.speed_without_track(ctx["analysis"], report)
        kept = ctx["analysis"].get("full_frames")
        common.sample_frames_layout(m, spec, report, ctx_frames=kept)
        if spec.get("grid_crop"):
            from ..motion import frame_at

            f = frame_at(m["path"], ctx.get("cover_frame") or 0, kept)
            if f is not None:
                layout_image(f, m["w"], m["h"], {**spec, "ui": (0, 0, 0, 0)}, report, label="cover: ")
    checks.audio_levels(m, ctx["lufs"], ctx["peak"], report)
    if not m["audio"] and fmt == "reel":
        report.info("audio", "reels without sound rely entirely on on-screen text — add audio or make sure the message reads muted")


def check_carousel(ctx):
    report = ctx["report"]
    folder = ctx["media"]["path"]
    files = sorted(f for f in os.listdir(folder) if not f.startswith("."))
    items = [os.path.join(folder, f) for f in files if os.path.splitext(f)[1].lower() in (".jpg", ".jpeg", ".png", ".mp4", ".mov", ".webp")]
    report.metrics["platform/format"] = "instagram / carousel"
    report.metrics["items"] = len(items)
    lo, hi = FORMATS["carousel"]["items"]
    if not (lo <= len(items) <= hi):
        report.fail("carousel", f"{len(items)} items — a carousel takes {lo}–{hi}")
    ratios = []
    for p in items:
        m = probe_media(p)
        ratios.append(round(m["w"] / m["h"], 3))
        sub = type(report)()
        if m["kind"] == "image":
            tech_image(m, FORMATS["feed_image"], sub)
            import cv2

            img = cv2.imread(p)
            if img is not None:
                layout_image(img, m["w"], m["h"], FORMATS["feed_image"], sub)
        else:
            tech_video(m, FORMATS["feed_video"], sub)
        for it in sub.items:
            report.add(it["level"], it["check"], f"{os.path.basename(p)}: {it['msg']}")
    if ratios and len(set(ratios)) > 1:
        report.fail("carousel", f"mixed aspect ratios {sorted(set(ratios))} — Instagram crops every slide to the first one's ratio")
