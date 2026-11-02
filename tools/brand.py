#!/usr/bin/env python3
"""Start a client's brand tokens from what they already use: a logo, screenshots of
their posts or site, frames from a previous video.

    python3 tools/brand.py logo.png shots/*.jpg --name "Hotel Sol" --out remotion-base/src/clients/hotel-sol

Writes <out>/brand.ts (same shape as src/lib/brand.ts) and <out>/palette.png (swatches),
and prints contrast ratios so you can see which pairings are readable.
Fonts can't be detected from pixels: the file leaves the template defaults with a TODO.
"""
import argparse
import colorsys
import os
import re
import sys

import cv2
import numpy as np


def load_pixels(paths, max_side=400):
    px = []
    for p in paths:
        im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if im is None:
            print(f"skip {p} (unreadable)")
            continue
        if im.ndim == 3 and im.shape[2] == 4:  # drop transparent pixels of logos
            alpha = im[:, :, 3] > 128
            im = im[:, :, :3][alpha].reshape(-1, 1, 3)
        else:
            h, w = im.shape[:2]
            s = max_side / max(h, w)
            if s < 1:
                im = cv2.resize(im, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
            im = im.reshape(-1, 1, 3)
        px.append(im.reshape(-1, 3))
    if not px:
        sys.exit("no readable images")
    return np.concatenate(px).astype(np.float32)


def palette(px, k=8):
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(3)
    _, labels, centers = cv2.kmeans(px, k, None, criteria, 4, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=k)
    out = []
    for c, n in sorted(zip(centers, counts), key=lambda t: -t[1]):
        b, g, r = c
        out.append(((int(r), int(g), int(b)), n / len(px)))
    return out


def lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hexc(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(v))) for v in rgb)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def sat(rgb):
    return colorsys.rgb_to_hls(*(v / 255 for v in rgb))[2]


def hue(rgb):
    return colorsys.rgb_to_hls(*(v / 255 for v in rgb))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--name", default="Client")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    px = load_pixels(a.images[:1])
    if len(a.images) > 1:  # the first image (usually the logo) weighs 3× — it is the brand's own statement
        px = np.concatenate([px, px, px, load_pixels(a.images[1:])])
    pal = palette(px)
    colors = [c for c, _ in pal]
    # saturated colours are often small in area (a logo mark, a button): cluster them separately
    hls = np.array([colorsys.rgb_to_hls(*(v / 255 for v in p[::-1])) for p in px[:: max(1, len(px) // 60000)]])
    keep = px[:: max(1, len(px) // 60000)][(hls[:, 2] > 0.15) & (hls[:, 1] > 0.15) & (hls[:, 1] < 0.8)]
    chroma_pal = palette(keep, k=5) if len(keep) > 200 else []
    ground = max(colors, key=lambda c: lum(c) - 0.5 * sat(c))       # light, quiet
    ink = min(colors, key=lambda c: lum(c) + 0.3 * sat(c))          # dark, quiet
    if contrast(ground, ink) < 7:  # push ink darker until body text is comfortably readable
        while contrast(ground, ink) < 7 and lum(ink) > 0.005:
            ink = mix(ink, (0, 0, 0), 0.15)
    chroma = [c for c, share in sorted(chroma_pal, key=lambda t: -t[1] * (0.5 + sat(t[0])))] or \
        sorted([c for c in colors if sat(c) > 0.18 and c not in (ground, ink)], key=lambda c: -sat(c))
    accent = chroma[0] if chroma else mix(ink, ground, 0.35)
    accent2 = next((c for c in chroma[1:] if min(abs(hue(c) - hue(accent)), 1 - abs(hue(c) - hue(accent))) > 0.08), mix(accent, ink, 0.4))
    for name in ("accent", "accent2"):  # make sure accents can carry text on the ground
        c = locals()[name]
        while contrast(ground, c) < 4.5 and lum(c) > 0.01:
            c = mix(c, (0, 0, 0), 0.12)
        locals()[name]  # noqa
        if name == "accent":
            accent = c
        else:
            accent2 = c
    paper = mix(ground, (255, 255, 255), 0.45)
    soft = mix(ink, ground, 0.45)
    line = mix(ink, ground, 0.82)

    tokens = dict(ground=ground, paper=paper, ink=ink, soft=soft, accent=accent, accent2=accent2, line=line)
    os.makedirs(a.out, exist_ok=True)

    # swatches
    sw = np.zeros((160, 140 * len(tokens), 3), np.uint8)
    for i, (k, c) in enumerate(tokens.items()):
        sw[:, i * 140:(i + 1) * 140] = c[::-1]
        txt = (20, 20, 20) if lum(c) > 0.35 else (240, 240, 240)
        cv2.putText(sw, k, (i * 140 + 8, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.55, txt, 1, cv2.LINE_AA)
        cv2.putText(sw, hexc(c), (i * 140 + 8, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.45, txt, 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(a.out, "palette.png"), sw)

    const = re.sub(r"[^A-Z0-9]+", "_", a.name.upper()).strip("_") or "BRAND"
    ts = f'''import {{ Brand }} from "../../lib/brand";

// Generated by tools/brand.py from: {", ".join(os.path.basename(p) for p in a.images)}
// Check it against the client's material before using it — it is a starting point.
export const {const}: Brand = {{
  name: "{a.name}",
  colors: {{
{chr(10).join(f'    {k}: "{hexc(c)}",' for k, c in tokens.items())}
  }},
  // TODO: fonts can't be read from pixels — put the client's font files in clients/<slug>/assets/fonts, list them under
  // brand.fonts in client.json and regenerate this file with `brief.py client ts <slug>` (loads them from clients/<slug>/fonts)
  fonts: {{ display: "serif", text: "sans-serif" }},
}};
'''
    open(os.path.join(a.out, "brand.ts"), "w", encoding="utf-8").write(ts)

    print("palette (share of pixels):")
    for c, share in pal:
        print(f"  {hexc(c)}  {share:5.1%}")
    print("\ntokens:")
    for k, c in tokens.items():
        print(f"  {k:8} {hexc(c)}")
    print("\ncontrast on ground (≥4.5 body text, ≥3 large text):")
    for k in ("ink", "soft", "accent", "accent2"):
        print(f"  {k:8} {contrast(ground, tokens[k]):.1f}")
    print(f"\nwrote {os.path.join(a.out, 'brand.ts')} and palette.png")


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
    main()
