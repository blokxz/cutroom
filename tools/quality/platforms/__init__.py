"""Platform registry. To add one: write <name>.py exposing NAME, SPEC (loaded from specs/<name>.json),
FORMATS, resolve(fmt, media), detect(media) and check(ctx), then add it to PLATFORMS."""
from . import instagram, tiktok, youtube_shorts

PLATFORMS = {m.NAME: m for m in (instagram, tiktok, youtube_shorts)}


def get(name):
    if name not in PLATFORMS:
        raise SystemExit(f"unknown platform {name!r}; available: {', '.join(PLATFORMS)}")
    return PLATFORMS[name]
