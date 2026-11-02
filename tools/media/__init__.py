"""Client material: read-only analysis of a client's original photos and videos, and preparation of the chosen ones.

modules:
  guard          ensure_writable(path): refuses writes inside a client's read-only source folders
  common         paths, slugs, file discovery, image loading
  photos         per-photo analysis: focus point, sharpness, exposure, horizon, upscale, duplicates, score
  videos         per-video analysis: metadata, HDR, best 2-4 s windows, slideshow / motion / mixed
  clips          ffmpeg preparation of a video window for Remotion (<OffthreadVideo>)
  contact_sheet  numbered contact sheets for photos and videos

CLI: tools/material.py (analyze, select, clip, guard).
"""
