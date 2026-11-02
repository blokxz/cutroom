"""TikTok: vertical video posts and in-feed ads.

Technical limits come from the Content Posting API (the strictest publishing path) and the
Ads Help Center; safe zones are creator guidance (TikTok only publishes overlay images).
The numbers live in specs/tiktok.json, with the date they were last reviewed and their sources.
"""
from . import common

NAME = "tiktok"
SPEC = common.load_spec(NAME)
FORMATS = SPEC["formats"]
ALIASES = {"post": "video", "reel": "video", "short": "video", "story": "video", "in_feed_ad": "ad"}


def resolve(fmt, media):
    if fmt in (None, "auto"):
        return detect(media)
    fmt = ALIASES.get(fmt, fmt)
    if fmt not in FORMATS:
        raise SystemExit(f"unknown tiktok format {fmt!r}; choose from {', '.join(FORMATS)} (or auto)")
    return fmt


def detect(media):
    # an ad and a post look the same in the file; ads are chosen explicitly with --format ad
    return "video"


def check(ctx):
    common.vertical_video_check(ctx, SPEC, ctx["format"])
