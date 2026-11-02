"""Quality checks for short-form video and images.

core modules (platform-agnostic):  media, motion, integrity, faces, audio, track, checks, report, limits
platform modules:                  platforms/<name>.py  — specs + layout rules for one platform

Add a platform by writing platforms/specs/<name>.json (dated limits + sources) and
platforms/<name>.py with SPEC, FORMATS, resolve(), detect() and check(ctx), then
registering it in platforms/__init__.py (see README.md).
"""
