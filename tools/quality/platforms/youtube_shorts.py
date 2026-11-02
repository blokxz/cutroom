"""YouTube Shorts: square or vertical videos up to 3 minutes.

Length and aspect are official (YouTube Help); encoding follows YouTube's recommended upload
settings; safe zones are creator guidance (YouTube publishes none for Shorts).
The numbers live in specs/youtube_shorts.json, with the date they were last reviewed and their sources.
"""
from . import common

NAME = "youtube_shorts"
SPEC = common.load_spec(NAME)
FORMATS = SPEC["formats"]
ALIASES = {"shorts": "short", "video": "short", "reel": "short", "post": "short"}


def resolve(fmt, media):
    if fmt in (None, "auto"):
        return detect(media)
    fmt = ALIASES.get(fmt, fmt)
    if fmt not in FORMATS:
        raise SystemExit(f"unknown youtube_shorts format {fmt!r}; choose from {', '.join(FORMATS)} (or auto)")
    return fmt


def detect(media):
    return "short"


def check(ctx):
    common.vertical_video_check(ctx, SPEC, ctx["format"])
