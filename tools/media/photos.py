"""Per-photo analysis, read-only. No models: classic image measures only (numpy + OpenCV).

For each photo:
  focus point     saliency map = spectral residual (Hou & Zhang 2007) + edges + saturation, with a penalty for
                  bright blue sky in the upper part and a centre prior; focus = weighted centroid of the top 20 %.
  sharpness       variance of the Laplacian at a common measuring size (long side 800 px, never upscaled),
                  judged against the median of the set (so a soft photo stands out among sharp ones).
  exposure        mean luma and the fraction of crushed shadows / blown highlights.
  horizon tilt    median angle of long near-horizontal lines (Hough); only warned when the lines agree.
  upscale         factor needed for a full-screen 1080x1920 crop.
  duplicates      64-bit difference hash; Hamming distance <= DUP_BITS = same picture.
  score           0..1 ranking aid (see score()).
"""
import math

import cv2
import numpy as np

from .common import open_image

MEASURE = 800          # px, long side used for sharpness / exposure / horizon
SALIENCY = 96          # px, long side of the saliency map
DUP_BITS = 6           # Hamming distance (of 64) for duplicates
FRAME = (1080, 1920)   # full-screen 9:16

THRESHOLDS = {
    "upscale_warn": 1.6, "upscale_error": 2.0,
    "sharp_abs_error": 40.0, "sharp_rel_error": 0.2, "sharp_rel_warn": 0.6,
    "luma_dark": 60.0, "luma_bright": 190.0, "clip_fraction": 0.10,
    "tilt_deg": 1.5,
}


def _gray(a):
    return cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)


def saliency(rgb):
    """(map 0..1 at <=96 px, (fx, fy) normalised, strength 0..1: how peaked the map is)."""
    h, w = rgb.shape[:2]
    s = SALIENCY / max(h, w)
    p = cv2.resize(rgb, (max(8, round(w * s)), max(8, round(h * s))), interpolation=cv2.INTER_AREA)
    g = _gray(p).astype(np.float32) / 255
    spec = np.fft.fft2(g)
    log_amp = np.log(np.abs(spec) + 1e-8)
    residual = log_amp - cv2.blur(log_amp, (3, 3))
    sr = np.abs(np.fft.ifft2(np.exp(residual + 1j * np.angle(spec)))) ** 2
    sr = cv2.GaussianBlur(sr.astype(np.float32), (0, 0), 2.0)
    sr = (sr - sr.min()) / (np.ptp(sr) + 1e-8)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)
    edges = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 1.5)
    edges = edges / (edges.max() + 1e-8)
    hsv = cv2.cvtColor(p, cv2.COLOR_RGB2HSV).astype(np.float32)
    sat = hsv[..., 1] / 255
    rows = np.linspace(0, 1, p.shape[0])[:, None] * np.ones((1, p.shape[1]))
    sky = ((hsv[..., 0] > 90) & (hsv[..., 0] < 130) & (hsv[..., 2] > 150) & (rows < 0.4)).astype(np.float32)
    sky = cv2.GaussianBlur(sky, (0, 0), 2)
    m = (0.5 * sr + 0.3 * edges + 0.2 * sat) * (1 - 0.5 * np.clip(sky, 0, 1))
    xs = (np.linspace(0, 1, p.shape[1])[None, :] - 0.5) / 0.35
    ys = (np.linspace(0, 1, p.shape[0])[:, None] - 0.5) / 0.35
    m = m * (0.5 + 0.5 * np.exp(-(xs ** 2 + ys ** 2) / 2))
    m = (m - m.min()) / (np.ptp(m) + 1e-8)
    top = np.where(m >= np.quantile(m, 0.80), m, 0)
    yi, xi = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    tot = top.sum() + 1e-8
    fx = float((top * xi).sum() / tot / max(1, m.shape[1] - 1))
    fy = float((top * yi).sum() / tot / max(1, m.shape[0] - 1))
    return m, (fx, fy), float(1 - m.mean())


def horizon(gray):
    """(tilt in degrees, number of supporting lines, spread in degrees) or (None, n, None) without evidence.
    Only long lines (half the width or more) count: in interiors, shorter near-horizontal edges are mostly
    perspective (tables, shelves) and would report a tilt that is not there."""
    e = cv2.Canny(gray, 60, 160)
    lines = cv2.HoughLinesP(e, 1, np.pi / 720, threshold=80, minLineLength=gray.shape[1] // 2, maxLineGap=8)
    if lines is None:
        return None, 0, None
    ang = []
    for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
        a = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if a > 90:
            a -= 180
        elif a < -90:
            a += 180
        if abs(a) < 10:
            ang.append(a)
    if len(ang) < 3:
        return None, len(ang), None
    med = float(np.median(ang))
    spread = float(np.median(np.abs(np.array(ang) - med)))
    return med, len(ang), spread


def dhash(gray):
    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA).astype(np.int16)
    bits = (small[:, 1:] > small[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def hamming(a, b):
    return bin(a ^ b).count("1")


def crop_window(width, height, fx, fy):
    """Largest 9:16 window inside the image, centred on the focus as far as the edges allow (normalised)."""
    cw = min(width, height * 9 / 16)
    ch = cw * 16 / 9
    cx = min(max(fx * width, cw / 2), width - cw / 2)
    cy = min(max(fy * height, ch / 2), height - ch / 2)
    return {"x": round((cx - cw / 2) / width, 4), "y": round((cy - ch / 2) / height, 4),
            "w": round(cw / width, 4), "h": round(ch / height, 4)}


def measure(path):
    """First pass: everything that does not depend on the rest of the set."""
    im, (w, h) = open_image(path, min_side=MEASURE)
    a = np.asarray(im)
    s = min(1.0, MEASURE / max(a.shape[:2]))
    n = cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else a
    g = _gray(n)
    lap = float(cv2.Laplacian(g, cv2.CV_64F).var())
    luma = float(g.mean())
    dark, bright = float((g < 8).mean()), float((g > 247).mean())
    _, (fx, fy), strength = saliency(n)
    sat = float(cv2.cvtColor(n, cv2.COLOR_RGB2HSV)[..., 1].mean() / 255)
    tilt, tilt_lines, tilt_spread = horizon(g)
    aspect = w / h
    orientation = "portrait" if aspect < 0.95 else "landscape" if aspect > 1.05 else "square"
    upscale = max(FRAME[0] / w, FRAME[1] / h)
    warnings, errors = [], []
    t = THRESHOLDS
    if upscale > t["upscale_error"]:
        errors.append(f"too small: full-screen needs {upscale:.1f}x upscale")
    elif upscale > t["upscale_warn"]:
        warnings.append(f"soft full-screen: {upscale:.1f}x upscale")
    if luma < t["luma_dark"]:
        warnings.append(f"underexposed (luma {luma:.0f})")
    elif luma > t["luma_bright"]:
        warnings.append(f"overexposed (luma {luma:.0f})")
    if dark > t["clip_fraction"]:
        warnings.append(f"crushed shadows ({dark:.0%} pure black)")
    if bright > t["clip_fraction"]:
        warnings.append(f"blown highlights ({bright:.0%} pure white)")
    # above ~6 deg a long near-horizontal line is far more often perspective than a crooked camera
    if tilt is not None and t["tilt_deg"] < abs(tilt) <= 6.0 and tilt_spread is not None and tilt_spread < 0.5:
        warnings.append(f"tilted horizon ({tilt:+.1f} deg)")
    return {
        "width": w, "height": h, "orientation": orientation,
        "focus": {"x": round(fx, 3), "y": round(fy, 3), "strength": round(strength, 3)},
        "crop_9x16": crop_window(w, h, fx, fy),
        "sharpness": {"laplacian": round(lap, 1), "relative": None},
        "exposure": {"mean_luma": round(luma, 1), "clipped_shadows": round(dark, 4), "clipped_highlights": round(bright, 4)},
        "saturation": round(sat, 3),
        "horizon_tilt_deg": None if tilt is None else round(tilt, 2),
        "upscale_9x16": round(upscale, 3),
        "hash": f"{dhash(g):016x}",
        "duplicates": [], "score": 0.0, "rank": 0,
        "warnings": warnings, "errors": errors,
    }


def score(r):
    """0..1. Detail (half relative to the set, half absolute) 45 %, colour 25 %, a clear subject 30 %;
    x0.85 per exposure warning, x0.7 when soft full-screen, x0.4 with any error."""
    rel = r["sharpness"]["relative"] or 0.0
    detail = 0.5 * min(1.0, rel / 2) + 0.5 * min(1.0, r["sharpness"]["laplacian"] / 1500)
    s = 0.45 * detail + 0.25 * r["saturation"] + 0.30 * r["focus"]["strength"]
    exposure_issues = sum(1 for w in r["warnings"] if w.startswith(("underexposed", "overexposed", "crushed", "blown")))
    s *= 0.85 ** exposure_issues
    if any(w.startswith("soft full-screen") for w in r["warnings"]):
        s *= 0.7
    if r["errors"]:
        s *= 0.4
    return round(s, 4)


def finish(records):
    """Second pass over the set: relative sharpness, duplicates, score, rank. Mutates and returns the median."""
    if not records:
        return 0.0
    t = THRESHOLDS
    med = float(np.median([r["sharpness"]["laplacian"] for r in records])) or 1e-6
    for r in records:
        lap = r["sharpness"]["laplacian"]
        r["sharpness"]["relative"] = round(lap / med, 3)
        if lap < t["sharp_abs_error"] and lap < t["sharp_rel_error"] * med:
            r["errors"].append(f"out of focus (sharpness {lap:.0f}, set median {med:.0f})")
        elif lap < t["sharp_rel_warn"] * med:
            r["warnings"].append(f"softer than the set ({lap:.0f} vs median {med:.0f})")
    for r in records:
        r["score"] = score(r)
    hashes = [int(r["hash"], 16) for r in records]
    for i, a in enumerate(records):
        for j, b in enumerate(records):
            if i != j and hamming(hashes[i], hashes[j]) <= DUP_BITS:
                a["duplicates"].append(b["id"])
    for r in records:
        better = [o for o in records if o["id"] in r["duplicates"] and (o["score"], -o["id"]) > (r["score"], -r["id"])]
        if better:
            r["warnings"].insert(0, f"duplicate of #{better[0]['id']} (keep that one)")
    for pos, r in enumerate(sorted(records, key=lambda r: -r["score"]), 1):
        r["rank"] = pos
    return med


def export_photo(src, out, long_side=2400, quality=92, protect=()):
    """Copy for the Remotion build: EXIF-rotated, long side <= long_side (never upscaled), sRGB, JPEG, no metadata
    (drops GPS and camera data). Returns (width, height)."""
    import io
    import os

    from PIL import Image, ImageCms, ImageOps

    from .guard import ensure_writable

    ensure_writable(out, protect)
    im = Image.open(src)
    icc = im.info.get("icc_profile")
    im = ImageOps.exif_transpose(im)
    if icc:
        try:
            src_prof = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            if im.mode not in ("RGB", "CMYK", "L"):
                im = im.convert("RGB")
            im = ImageCms.profileToProfile(im, src_prof, ImageCms.createProfile("sRGB"), outputMode="RGB")
        except Exception:
            pass
    if im.mode != "RGB":
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
    if max(im.size) > long_side:
        s = long_side / max(im.size)
        im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    im.save(out, "JPEG", quality=quality, optimize=True, progressive=True, subsampling="4:2:0", icc_profile=srgb)
    return im.size
