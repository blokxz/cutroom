"""Contact sheets for reviewing an analysed batch by eye.

photo_sheet  numbered thumbnails (the number is the id used by `material.py select`), the 9:16 window
             centred on the focus point (red), the focus point (yellow ring), size / score / upscale and up to
             two warnings or errors. Border: green = clean, amber = warnings, red = errors.
video_sheet  one row per video: three frames from its best window (start, middle, end) and a caption with the
             id, size, duration, class, HDR and the best windows.
"""
import io
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

from quality.bins import ffmpeg

from .common import open_image
from .guard import ensure_writable

BG = (244, 244, 240)
INK = (34, 34, 30)
SOFT = (96, 92, 84)
RED = (200, 40, 40)
AMBER = (196, 120, 10)
GREEN = (60, 140, 70)
FONT_CANDIDATES = ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                   "/Library/Fonts/Arial.ttf", "C:\\Windows\\Fonts\\arial.ttf", "Arial.ttf")


def font(size, bold=False):
    names = FONT_CANDIDATES
    if bold:
        names = ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "C:\\Windows\\Fonts\\arialbd.ttf") + names
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _fit(text, f, width, draw):
    if draw.textlength(text, font=f) <= width:
        return text
    while text and draw.textlength(text + "...", font=f) > width:
        text = text[:-1]
    return text + "..."


def _badge(d, x, y, label, f, fill):
    tw = d.textlength(label, font=f)
    d.rounded_rectangle([x, y, x + tw + 16, y + 30], radius=6, fill=fill)
    d.text((x + 8, y + 3), label, fill=(255, 255, 255), font=f)


def photo_sheet(records, out, protect=(), cols=5, tile=(260, 340)):
    ensure_writable(out, protect)
    TW, TH = tile
    CAP = 96
    rows = max(1, (len(records) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * (TW + 12) + 12, rows * (TH + CAP + 12) + 12), BG)
    d = ImageDraw.Draw(sheet)
    f_num, f_txt, f_small = font(20, bold=True), font(14), font(13)
    for i, r in enumerate(records):
        x0 = 12 + (i % cols) * (TW + 12)
        y0 = 12 + (i // cols) * (TH + CAP + 12)
        try:
            im, _ = open_image(r["source"], min_side=max(TW, TH) * 2)
            im.thumbnail((TW, TH))
        except Exception:
            im = Image.new("RGB", (TW, TH // 2), (200, 200, 200))
        ox, oy = x0 + (TW - im.width) // 2, y0 + (TH - im.height) // 2
        sheet.paste(im, (ox, oy))
        state = RED if r["errors"] else AMBER if r["warnings"] else GREEN
        d.rectangle([ox - 3, oy - 3, ox + im.width + 2, oy + im.height + 2], outline=state, width=3)
        c = r["crop_9x16"]
        d.rectangle([ox + c["x"] * im.width, oy + c["y"] * im.height,
                     ox + (c["x"] + c["w"]) * im.width - 1, oy + (c["y"] + c["h"]) * im.height - 1],
                    outline=(230, 30, 30), width=2)
        fx, fy = ox + r["focus"]["x"] * im.width, oy + r["focus"]["y"] * im.height
        d.ellipse([fx - 7, fy - 7, fx + 7, fy + 7], outline=(0, 0, 0), width=4)
        d.ellipse([fx - 7, fy - 7, fx + 7, fy + 7], outline=(255, 225, 0), width=2)
        _badge(d, ox + 4, oy + 4, str(r["id"]), f_num, (20, 20, 20))
        if r.get("rank"):
            label = f"rank {r['rank']}"
            _badge(d, ox + im.width - d.textlength(label, font=f_small) - 20, oy + 4, label, f_small, state)
        ty = y0 + TH + 4
        d.text((x0, ty), _fit(f"{r['id']}. {os.path.basename(r['source'])}", f_txt, TW, d), fill=INK, font=f_txt)
        d.text((x0, ty + 18), _fit(f"{r['width']}x{r['height']}  score {r['score']:.2f}  up {r['upscale_9x16']:.2f}x",
                                   f_small, TW, d), fill=SOFT, font=f_small)
        notes = [("x ", t, RED) for t in r["errors"]] + [("! ", t, AMBER) for t in r["warnings"]]
        shown = notes[:3]
        for j, (p, t, col) in enumerate(shown):
            more = f"  (+{len(notes) - 3})" if j == 2 and len(notes) > 3 else ""
            d.text((x0, ty + 36 + 17 * j), _fit(p + t, f_small, TW - d.textlength(more, font=f_small), d) + more,
                   fill=col, font=f_small)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out)
    return out


def grab_frame(path, t, box, meta=None):
    vf = ""
    if meta and meta.get("hdr"):
        from .clips import hdr_to_sdr
        vf = hdr_to_sdr(meta)[0]
    vf += f"scale={box[0]}:{box[1]}:force_original_aspect_ratio=decrease"
    r = subprocess.run([ffmpeg(), "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", path, "-frames:v", "1",
                        "-an", "-vf", vf, "-f", "image2pipe", "-c:v", "png", "-"], capture_output=True)
    try:
        return Image.open(io.BytesIO(r.stdout)).convert("RGB")
    except Exception:
        return None


def video_sheet(records, out, protect=(), box=(200, 356)):
    ensure_writable(out, protect)
    BW, BH = box
    CAP = 60
    W = 3 * (BW + 8) + 12 + 4
    heights = [min(BH, max(80, round(BW * r["height"] / r["width"]))) if r.get("width") else 120 for r in records]
    sheet = Image.new("RGB", (W, sum(h + CAP + 12 for h in heights) + 12), BG)
    d = ImageDraw.Draw(sheet)
    f_num, f_txt, f_small = font(20, bold=True), font(14), font(13)
    y0 = 12
    for r, rh in zip(records, heights):
        win = (r.get("windows") or [None])[0]
        if win:
            for c, frac in enumerate((0.05, 0.5, 0.95)):
                t = win["start"] + frac * win["duration"]
                im = grab_frame(r["source"], t, (BW, rh), r)
                if im:
                    x = 12 + c * (BW + 8) + (BW - im.width) // 2
                    sheet.paste(im, (x, y0 + (rh - im.height) // 2))
        state = RED if r["errors"] else AMBER if r["warnings"] else GREEN
        _badge(d, 16, y0 + 4, str(r["id"]), f_num, (20, 20, 20))
        d.rectangle([8, y0 - 4, W - 8, y0 + rh + CAP], outline=state, width=2)
        line1 = (f"{r['id']}. {os.path.basename(r['source'])}  {r['width']}x{r['height']}  "
                 f"{r['duration_s']:.1f}s  {r.get('class', '?')}" + ("  HDR" if r.get("hdr") else ""))
        d.text((14, y0 + rh + 4), _fit(line1, f_txt, W - 28, d), fill=INK, font=f_txt)
        wins = "  ".join(f"{w['start']:.1f}-{w['end']:.1f}s ({w['score']:.2f})" for w in r.get("windows") or [])
        d.text((14, y0 + rh + 22), _fit("best: " + (wins or "none"), f_small, W - 28, d), fill=SOFT, font=f_small)
        notes = [("x ", t, RED) for t in r["errors"]] + [("! ", t, AMBER) for t in r["warnings"]]
        if notes:
            d.text((14, y0 + rh + 39), _fit("  ".join(p + t for p, t, _ in notes), f_small, W - 28, d),
                   fill=notes[0][2], font=f_small)
        y0 += rh + CAP + 12
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out)
    return out
