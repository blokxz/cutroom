"""What a file is, technically: container, codecs, sizes, rates, colour, structure.

probe_media(path) → dict with kind = "video" | "image".
"""
import json
import os
import struct
import subprocess

from .bins import ffprobe

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif", ".tif", ".tiff", ".bmp"}


def _ffprobe(path, *args):
    out = subprocess.run([ffprobe(), "-v", "error", *args, "-of", "json", path], capture_output=True, text=True)
    return json.loads(out.stdout or "{}")


def _rate(s):
    try:
        n, d = s.split("/")
        return float(n) / float(d) if float(d) else 0.0
    except Exception:
        return 0.0


def moov_first(path):
    """True if the moov atom comes before mdat (a.k.a. 'faststart'). None if not an MP4/MOV."""
    try:
        with open(path, "rb") as f:
            seen = []
            while True:
                head = f.read(8)
                if len(head) < 8:
                    break
                size, kind = struct.unpack(">I4s", head)
                kind = kind.decode("latin1")
                if size == 1:
                    size = struct.unpack(">Q", f.read(8))[0]
                    f.seek(size - 16, 1)
                elif size == 0:
                    seen.append(kind)
                    break
                else:
                    f.seek(size - 8, 1)
                seen.append(kind)
                if kind in ("moov", "mdat") and "moov" in seen and "mdat" in seen:
                    break
            if "moov" not in seen:
                return None
            return "mdat" not in seen or seen.index("moov") < seen.index("mdat")
    except Exception:
        return None


def keyframe_interval(path, limit_s=20):
    j = _ffprobe(path, "-select_streams", "v:0", "-skip_frame", "nokey", "-show_entries", "frame=pts_time", "-read_intervals", f"%+{limit_s}")
    t = [float(fr["pts_time"]) for fr in j.get("frames", []) if fr.get("pts_time") not in (None, "N/A")]
    if len(t) < 2:
        return None
    gaps = [b - a for a, b in zip(t, t[1:])]
    return max(gaps)


def probe_image(path):
    from PIL import Image

    im = Image.open(path)
    icc = im.info.get("icc_profile")
    icc_desc = None
    if icc:
        try:
            from PIL import ImageCms
            import io

            icc_desc = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))).strip()
        except Exception:
            icc_desc = "unknown"
    return dict(kind="image", path=path, format=(im.format or "").upper(), mode=im.mode, w=im.width, h=im.height,
                size_bytes=os.path.getsize(path), icc=icc_desc,
                has_alpha=im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info))


def probe_video(path):
    j = _ffprobe(path, "-show_entries", "format=format_name,duration,bit_rate,size:stream=index,codec_type,codec_name,profile,pix_fmt,width,height,"
                       "r_frame_rate,avg_frame_rate,field_order,bit_rate,sample_rate,channels,color_space,color_primaries,color_transfer")
    fmt = j.get("format", {})
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in j.get("streams", []) if s.get("codec_type") == "audio"), None)
    if v is None:
        raise SystemExit(f"{path}: no video stream")
    dur = float(fmt.get("duration") or 0)
    size = int(fmt.get("size") or os.path.getsize(path))
    vbr = int(v.get("bit_rate") or 0) or (int(fmt.get("bit_rate") or 0) - int((a or {}).get("bit_rate") or 0))
    return dict(
        kind="video", path=path, container=fmt.get("format_name", ""), duration=dur, size_bytes=size,
        vcodec=v.get("codec_name"), profile=v.get("profile"), pix_fmt=v.get("pix_fmt"), w=int(v["width"]), h=int(v["height"]),
        fps=_rate(v.get("avg_frame_rate") or v.get("r_frame_rate")), field_order=v.get("field_order", "progressive"),
        vbitrate=vbr, color_space=v.get("color_space"), color_primaries=v.get("color_primaries"), color_transfer=v.get("color_transfer"),
        audio=a is not None, acodec=(a or {}).get("codec_name"), sample_rate=int((a or {}).get("sample_rate") or 0),
        channels=int((a or {}).get("channels") or 0), abitrate=int((a or {}).get("bit_rate") or 0),
        moov_first=moov_first(path), keyframe_interval=keyframe_interval(path),
    )


def probe_media(path):
    ext = os.path.splitext(path)[1].lower()
    return probe_image(path) if ext in IMAGE_EXT else probe_video(path)
