#!/usr/bin/env python3
"""verify.py — quality checks for short-form video and images, per platform.

    python3 tools/verify.py out/draft.mp4                                  # instagram, format auto-detected
    python3 tools/verify.py out/draft.mp4 --format reel --track out/draft.track.json --sheet out/sheet.png
    python3 tools/verify.py out/draft.mp4 --ref client_reference.mp4       # compare rhythm with a reference
    python3 tools/verify.py post.jpg --format feed_image
    python3 tools/verify.py carousel_folder/                               # each slide + consistency
    python3 tools/verify.py reference.mp4 --analyze                        # numbers only, no verdict
    python3 tools/verify.py out/draft.mp4 --platform tiktok                # or youtube_shorts

Core checks (any platform, from pixels and audio)
  rhythm     near-still share, longest rest, uneven beats, metronome cadence
  cuts       regular hard cuts (slideshow) vs deliberate bursts
  curves     t80 of every move: all moves on one curve, or slow/linear starts
  ending     a readable hold at the end for the call to action
  audio      true peak and integrated loudness
  reference  (--ref) still share, cut rate, beat length, curves and energy shape vs a reference

With --track (from remotion-base/scripts/render.mjs)
  continuity no scene boundary where everything is replaced; share of carried boundaries
             (beats may carry kind: move / rest / hold / cut; without it the kind is read from the name)
  framing    elements marked inFrame never leave the frame
  safe       settled text stays out of the areas the platform UI covers
  blur       elements moving > 80 px/frame have motion blur
  legibility text blocks big enough to read on a phone
  reading    every text appearance fully legible for ≥ 0.6 s + 0.28 s per word (needs `t` in the track records)

Integrity (any video, from pixels)
  black      near-black frames away from the first / last 0.2 s
  frozen     identical frames for ≥ 2 s away from the final hold (INFO inside a declared hold)
  borders    black bars on opposite edges (letterbox / pillarbox)
  luma       mean brightness out of a sane range
  scenes     without --track: scene changes classed motion / dissolve / cut / still; most must happen in motion
  faces      people visible (optional local YuNet model: python3 tools/models.py fetch)

Platform modules (tools/quality/platforms, numbers in platforms/specs/<name>.json):
  instagram       reel, story, feed_video, story_image, feed_image, reel_cover, carousel
                  (publishing-API limits, UI-covered areas, the 3:4 profile-grid crop, hook and loop)
  tiktok          video, ad (Content Posting API / Ads limits, caption and action-button areas)
  youtube_shorts  short (≤3 min, square or vertical, recommended encoding, title and button areas)
Each spec file carries the date it was last reviewed; a WARN asks to re-check it after 180 days.

Exit code 1 if any FAIL. WARN = decide consciously. INFO = context.

Environment: FFMPEG / FFPROBE pick the binaries (default: from PATH); CUTROOM_ANALYSIS_CACHE=<dir>
reuses the picture analysis of an unchanged file; CUTROOM_SPECS_DIR replaces platforms/specs;
CUTROOM_FACE_MODEL points the face check at a YuNet .onnx (default tools/models/). Thresholds: quality/limits.py.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quality import faces, motion  # noqa: E402
from quality.audio import audio_stats  # noqa: E402
from quality.media import probe_media  # noqa: E402
from quality.platforms import PLATFORMS, get  # noqa: E402
from quality.platforms.common import check_reviewed  # noqa: E402
from quality.report import Report  # noqa: E402
from quality.track import load_track  # noqa: E402

LEGACY = {"landscape": "feed_video"}  # old instagram format names


def analyze_video(media, keep=()):
    return motion.analyze(media["path"], media["fps"], media["w"], media["duration"], keep=keep)


def frames_to_keep(media, a):
    """Full-resolution frames the checks will look at, kept during the analysis pass instead of seeking later."""
    keep = set()
    if a.sheet:
        keep |= set(motion.sheet_indices(motion.frame_count(media["path"])))
    if not a.track and not a.analyze:
        keep |= set(motion.sample_indices(media["duration"], media["fps"]))
        keep.add(a.cover_frame or 0)
    if not a.analyze and faces.available():  # one frame per second for the face check, from the same decoding pass
        keep |= set(faces.sample_indices(media["duration"], media["fps"]))
    return keep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="video, image, or a folder (carousel)")
    ap.add_argument("--platform", default="instagram", choices=sorted(PLATFORMS))
    ap.add_argument("--format", default="auto", help="platform format, or auto (instagram: reel, story, feed_video, story_image, feed_image, reel_cover, carousel, post; "
                                                 "tiktok: video, ad; youtube_shorts: short)")
    ap.add_argument("--track", help="tracking JSON from scripts/render.mjs")
    ap.add_argument("--ref", help="reference video to compare the rhythm with")
    ap.add_argument("--cover-frame", type=int, help="frame used as the reel cover (default: first frame)")
    ap.add_argument("--analyze", action="store_true", help="print measurements only, no verdict")
    ap.add_argument("--sheet", help="write a contact sheet PNG (videos)")
    ap.add_argument("--frames", help="write a sheet of one frame every 0.5 s (videos): the whole piece, or a reference, on one page")
    ap.add_argument("--json", help="write the report as JSON")
    a = ap.parse_args()

    report = Report()
    media = dict(kind="dir", path=a.path) if os.path.isdir(a.path) else probe_media(a.path)
    platform = get(a.platform)
    fmt = platform.resolve(LEGACY.get(a.format, a.format) if a.platform == "instagram" else a.format, media)

    ctx = dict(media=media, format=fmt, report=report, analysis=None, track=None, lufs=None, peak=None, cover_frame=a.cover_frame)
    if media["kind"] == "video":
        loud = None
        if media["audio"]:  # loudness runs in its own ffmpeg process while the picture is analysed
            from concurrent.futures import ThreadPoolExecutor

            pool = ThreadPoolExecutor(1)
            loud = pool.submit(audio_stats, a.path)
        an = analyze_video(media, frames_to_keep(media, a))
        ctx["analysis"] = an
        report.metrics.update(
            {"resolution": f"{media['w']}x{media['h']}", "fps": round(media["fps"], 2), "duration_s": round(media["duration"], 2),
             "codec": f"{media['vcodec']} {media['pix_fmt']} / {media['acodec'] or 'no audio'}",
             "video_bitrate_mbps": round(media["vbitrate"] / 1e6, 1) if media["vbitrate"] else None,
             "file_mb": round(media["size_bytes"] / 1e6, 1)})
        report.metrics.update(an["metrics"])
        if media["audio"]:
            ctx["lufs"], ctx["peak"] = loud.result()
            pool.shutdown()
            report.metrics["loudness_lufs"], report.metrics["true_peak_dbfs"] = ctx["lufs"], ctx["peak"]
        if a.sheet:
            motion.contact_sheet(a.path, a.sheet, frames=an.get("full_frames"))
            report.metrics["contact_sheet"] = a.sheet
        if a.frames:
            motion.frame_sheet(a.path, a.frames)
            report.metrics["frame_sheet"] = a.frames
        if a.analyze and not a.ref:
            print("\n  energy map  (blank still · @ peak · | cut)")
            for row in motion.energy_map(an["diff"], an["fps"], an["cuts"]):
                print("  " + row)
        if a.ref:
            rm = probe_media(a.ref)
            motion.compare_reference(an, analyze_video(rm), report)
    elif media["kind"] == "image":
        report.metrics.update({"resolution": f"{media['w']}x{media['h']}", "format": media["format"],
                               "file_mb": round(media["size_bytes"] / 1e6, 2), "colour_profile": media["icc"] or "none (treated as sRGB)"})

    if a.analyze:
        report.print(a.path)
        if a.json:
            report.save(a.json)
        return 0

    if a.track:
        ctx["track"] = load_track(a.track)
    if getattr(platform, "SPEC", None):
        check_reviewed(platform.SPEC, report)
    platform.check(ctx)
    report.print(a.path)
    if a.json:
        report.save(a.json)
    return 1 if report.failed else 0


def _utf8_output():
    """Windows consoles and pipes default to a legacy code page; our messages use → ≤ —."""
    import sys as _sys
    for stream in (_sys.stdout, _sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


if __name__ == "__main__":
    _utf8_output()
    sys.exit(main())
