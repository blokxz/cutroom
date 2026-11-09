"""Prepare a window of a video for Remotion (<OffthreadVideo>). The original is only read.

Output: no audio, constant 30 fps, H.264 yuv420p tagged BT.709 (tv range), short GOP (15) so frame-accurate
seeking is cheap and deterministic, moov atom first.
  mode 'vertical'  crop to 9:16 (after removing --crop-top of the height, e.g. to hide a watermark) and scale to 1080x1920
  mode 'card'      the whole frame centred over a blurred, darkened copy of itself (for landscape footage)
  HDR (HLG / PQ / BT.2020) is tone-mapped to SDR BT.709 with zscale + tonemap (hable) when this ffmpeg has them;
  otherwise it is only converted (no tone mapping) and a warning says so.
  Rotation metadata is applied by ffmpeg while decoding; the output carries none.
  --warm lifts the shadows and warms the image slightly (0 = off, 1 = full), to match graded photos.
"""
import functools
import os
import subprocess

from quality.bins import ffmpeg

from .guard import ensure_writable
from .videos import probe

OUT_W, OUT_H, OUT_FPS, GOP = 1080, 1920, 30, 15
ZSCALE_TRANSFER = {"arib-std-b67": "arib-std-b67", "smpte2084": "smpte2084", "bt2020-10": "2020_10",
                   "bt2020-12": "2020_12", "bt709": "709"}
ZSCALE_MATRIX = {"bt2020nc": "2020_ncl", "bt2020c": "2020_cl", "bt709": "709"}


@functools.lru_cache(maxsize=None)
def ffmpeg_filters():
    r = subprocess.run([ffmpeg(), "-hide_banner", "-filters"], capture_output=True, text=True)
    names = set()
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3 and len(parts[0]) == 3:
            names.add(parts[1])
    return names


def can_tonemap():
    f = ffmpeg_filters()
    return "zscale" in f and "tonemap" in f


def hdr_to_sdr(meta):
    """(filter prefix that leaves SDR BT.709 yuv, tone-mapped?) for an HDR source."""
    c = meta.get("color") or {}
    if can_tonemap():
        tin = ZSCALE_TRANSFER.get(c.get("transfer") or "", "arib-std-b67")
        mat = ZSCALE_MATRIX.get(c.get("matrix") or "", "2020_ncl")
        return (f"zscale=tin={tin}:pin=2020:min={mat}:t=linear:npl=100,format=gbrpf32le,"
                "zscale=p=709,tonemap=tonemap=hable:desat=0,zscale=t=709:m=709:r=tv,format=yuv420p,"), True
    return "scale=in_color_matrix=bt2020:out_color_matrix=bt709:out_range=tv,format=yuv420p,", False


def warm_filter(amount):
    if amount <= 0:
        return ""
    g = 1 - 0.26 * amount
    rr, gg, bb = 1 + 0.05 * amount, 1 + 0.015 * amount, 1 - 0.08 * amount
    return (f",eq=gamma={1 / g:.3f}:saturation={1 + 0.05 * amount:.3f},"
            f"colorchannelmixer=rr={rr:.3f}:gg={gg:.3f}:bb={bb:.3f}")


def build_filter(meta, mode="vertical", crop_top=0.0, focus_x=0.5, warm=0.0, hold=0.5):
    """(filter_complex string, tone-mapped?) from source metadata."""
    w, h = meta["width"], meta["height"]
    pre, tonemapped = ("", None)
    if meta.get("hdr"):
        pre, tonemapped = hdr_to_sdr(meta)
    else:
        pre = "scale=out_color_matrix=bt709:out_range=tv,"
    top = int(round(h * max(0.0, min(0.5, crop_top)) / 2)) * 2
    hh = h - top
    if mode == "vertical":
        cw = min(w, int(hh * 9 / 16) // 2 * 2)
        ch = min(hh, int(cw * 16 / 9) // 2 * 2)
        x0 = int(round(min(max(focus_x * w - cw / 2, 0), w - cw)))
        body = f"[0:v]{pre}crop={cw}:{ch}:{x0}:{top},scale={OUT_W}:{OUT_H}:flags=lanczos,setsar=1"
    elif mode == "card":
        cut = f"crop={w}:{hh}:0:{top}," if top else ""
        body = (f"[0:v]{pre}{cut}split[a][b];"
                # blur at quarter size, then scale up: same look as a heavy full-size blur, many times faster
                f"[a]scale={OUT_W // 4}:{OUT_H // 4}:force_original_aspect_ratio=increase,crop={OUT_W // 4}:{OUT_H // 4},"
                f"boxblur=10:3,eq=brightness=-0.18,scale={OUT_W}:{OUT_H}:flags=bicubic[bg];"
                f"[b]scale=w=1000:h=1700:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos,setsar=1[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2")
    else:
        raise ValueError(f"unknown mode '{mode}' (vertical | card)")
    # tpad clones the last frame so a window ending at the end of the file still fills its frame count
    return (body + warm_filter(warm) + f",fps={OUT_FPS},tpad=stop_mode=clone:stop_duration={hold:.3f},format=yuv420p[out]",
            tonemapped)


def prepare(src, out, start=0.0, dur=3.0, mode="vertical", crop_top=0.0, focus_x=0.5, warm=0.0,
            preset="medium", crf=16, protect=()):
    """Write the clip; returns a summary dict. Raises ReadOnlyPathError / RuntimeError.
    The folder of the source video is always protected, besides the client source folders and `protect`."""
    protect = tuple(protect) + (os.path.dirname(os.path.abspath(src)),)
    ensure_writable(out, protect)
    meta = probe(src)
    if meta["duration_s"] and start >= meta["duration_s"]:
        raise RuntimeError(f"start {start:.2f} s is past the end of the video ({meta['duration_s']:.2f} s)")
    if dur <= 0:
        raise RuntimeError("duration must be positive")
    fc, tonemapped = build_filter(meta, mode, crop_top, focus_x, warm, hold=dur + 0.5)
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    n_frames = max(1, int(round(dur * OUT_FPS)))
    cmd = [ffmpeg(), "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{dur + 0.25:.3f}", "-i", src,
           "-filter_complex", fc, "-map", "[out]", "-frames:v", str(n_frames), "-an", "-sn", "-dn", "-map_metadata", "-1",
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-profile:v", "high",
           "-g", str(GOP), "-keyint_min", str(GOP), "-sc_threshold", "0", "-bf", "2",
           "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709",
           # also write the VUI through x264 itself: newer ffmpeg builds no longer carry -color_trc into the stream
           "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709",
           "-r", str(OUT_FPS), "-movflags", "+faststart", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + r.stderr[-1200:])
    warnings = []
    if meta["duration_s"] and start + dur > meta["duration_s"] + 0.05:
        warnings.append(f"window runs past the end of the video ({meta['duration_s']:.2f} s): last frame held")
    if meta["hdr"] and not tonemapped:
        warnings.append("HDR source converted WITHOUT tone mapping (this ffmpeg lacks zscale/tonemap): "
                        "colours may look flat or clipped; install an ffmpeg with zimg")
    got = probe(out)
    return {"out": out, "source": src, "start": round(start, 3), "duration_s": got["duration_s"],
            "mode": mode, "source_size": f"{meta['width']}x{meta['height']}", "hdr": meta["hdr"],
            "tonemapped": bool(tonemapped), "warnings": warnings}


def auto_mode(meta):
    """'vertical' when a 9:16 crop keeps most of the frame, else 'card'."""
    return "vertical" if meta["height"] / max(1, meta["width"]) >= 1.3 else "card"
