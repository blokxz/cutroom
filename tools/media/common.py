"""Shared helpers for tools/media: repo paths, slugs, file discovery, image loading, JSON output."""
import json
import os
import re
import sys
import unicodedata

from PIL import Image, ImageOps

from .guard import clients_dir, ensure_writable

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
SCHEMAS = os.path.join(ROOT, "schemas")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".heic"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".mts"}


def client_dir(slug):
    return os.path.join(clients_dir(), slug)


def slugify(text):
    t = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "batch"


def kind_of(path):
    ext = os.path.splitext(path)[1].lower()
    return "photo" if ext in PHOTO_EXT else "video" if ext in VIDEO_EXT else None


def discover(inputs, videos=False, recursive=False):
    """(photos, videos, skipped) from folders and files. Folders: photos always, videos only with videos=True.
    Explicit video files are always included. Order: sorted by path, case-insensitively, per input."""
    photos, vids, skipped = [], [], []
    for inp in inputs:
        if os.path.isdir(inp):
            found = []
            if recursive:
                for d, dirs, files in os.walk(inp):
                    dirs[:] = sorted(x for x in dirs if not x.startswith("."))
                    found += [os.path.join(d, f) for f in files if not f.startswith(".")]
            else:
                found = [os.path.join(inp, f) for f in os.listdir(inp) if not f.startswith(".")]
            for f in sorted(found, key=lambda p: p.lower()):
                if not os.path.isfile(f):
                    continue
                k = kind_of(f)
                if k == "photo":
                    photos.append(f)
                elif k == "video":
                    (vids if videos else skipped).append(f)
        elif os.path.isfile(inp):
            k = kind_of(inp)
            if k == "photo":
                photos.append(inp)
            elif k == "video":
                vids.append(inp)
            else:
                skipped.append(inp)
        else:
            raise FileNotFoundError(f"no such file or folder: {inp}")
    dedup = lambda xs: list(dict.fromkeys(os.path.abspath(x) for x in xs))  # noqa: E731
    return dedup(photos), dedup(vids), skipped


def source_roots(inputs):
    """Folders the inputs live in: protected for the run so analysis can never write next to the originals."""
    return sorted({os.path.abspath(i if os.path.isdir(i) else os.path.dirname(os.path.abspath(i))) for i in inputs})


def default_batch(inputs):
    first = inputs[0]
    base = first if os.path.isdir(first) else os.path.dirname(os.path.abspath(first))
    return slugify(os.path.basename(os.path.normpath(os.path.abspath(base))))


def open_image(path, min_side=None):
    """EXIF-rotated RGB image. With min_side, JPEGs are decoded at a reduced scale (draft) keeping the long
    side >= min_side. Returns (image, (width, height)) where the size is the full, rotated original size."""
    im = Image.open(path)
    w, h = im.size
    try:
        orient = im.getexif().get(0x0112, 1)
    except Exception:
        orient = 1
    if orient in (5, 6, 7, 8):
        w, h = h, w
    if min_side and im.format == "JPEG" and max(w, h) > min_side:
        s = min_side / max(w, h)
        im.draft("RGB", (int(im.size[0] * s) + 1, int(im.size[1] * s) + 1))
    im = ImageOps.exif_transpose(im)
    if im.mode != "RGB":
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
    return im, (w, h)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data, protect=()):
    ensure_writable(path, protect)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def rel_to(path, base):
    try:
        r = os.path.relpath(path, base)
    except ValueError:
        return path
    return path if r.startswith("..") else r.replace(os.sep, "/")
