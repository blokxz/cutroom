"""Thresholds of the reading-time, integrity, scene-continuity and face checks, in one place.

Calibrated on cutroom's own renders (remotion-base/out/*) and on synthetic good / bad cases in
tools/tests; see README.md ("Integrity", "Scene changes", "Reading time") for the measured values.
"""

# ------------------------------------------------------------------ reading time (with tracking)
READ_BASE_S = 0.6  # time to notice a text block at all
READ_PER_WORD_S = 0.28  # ≈ 215 words per minute, a comfortable pace for short on-screen lines
READ_FAIL_SHARE = 0.7  # an appearance under 70 % of the required time is a FAIL, under 100 % a WARN
READ_MIN_OPACITY = 0.9  # "fully legible": at least this opacity ...
READ_EDGE_TOLERANCE_PX = 4  # ... and the whole box inside the frame (± this, at the track's size)
READ_GAP_FRAMES = 2  # dips this short (a flicker, a rounding blip) don't split an appearance

# ------------------------------------------------------------------ integrity (any video)
EDGE_IGNORE_S = 0.2  # black frames in the first / last 0.2 s are fades in / out, not a fault
BLACK_MEAN = 8.0  # near-black frame: mean grey level (0–255, full range) below this ...
BLACK_P99 = 24.0  # ... and 99 % of its pixels below this (a dark scene with a lit detail is not black)
FROZEN_DIFF = 0.1  # mean grey change per frame below which two frames are the same picture (encoder noise ≈ 0–0.05)
FROZEN_WARN_S = 2.0  # an identical-picture run this long, away from the final hold, is a frozen picture
FROZEN_END_MAX_S = 5.0  # a final hold longer than this looks like the composition ended early
BORDER_LEVEL = 24  # a row / column whose brightest pixel is at most this counts as black bar
BORDER_UNIFORM_STD = 3.0  # ... and the band is flat: grey-level spread at most this (encoder noise on black ≈ 0–1)
BORDER_EDGE_CONTRAST = 16  # the content past the bar differs from the bar's level by at least this ...
BORDER_EDGE_SHARE = 0.6  # ... over at least 60 % of the rows / columns just inside it (a straight picture edge, not glyphs)
BORDER_EDGE_SKIP_PX = 2  # those rows start 2 px inside the edge (chroma subsampling blurs the boundary) ...
BORDER_EDGE_DEPTH_PX = 4  # ... and are 4 px deep; the content's median background must differ from the bar the same way
BORDER_EDGE_JITTER_PX = 4  # across sampled frames the bar's width varies by at most this (10th–90th percentile)
BORDER_FAIL_PX = 8  # bars at least this thick (full-resolution px) on opposite sides: letterbox / pillarbox
BORDER_SAMPLE_S = 0.5  # full-resolution frames sampled for bars every 0.5 s during the decoding pass
BORDER_PRESENT_SHARE = 0.9  # a bar must be there in 90 % of the sampled non-black frames to count
LUMA_RANGE = (40.0, 235.0)  # mean brightness of the whole video outside this: too dark / washed out

# ------------------------------------------------------------------ scene changes (no tracking)
SCENE_WINDOW_S = 0.3  # content change is measured between frames 0.3 s before and after each frame
SCENE_MIN_CHANGE = 10.0  # mean grey change across that window for a moment to count as a scene change
SCENE_CONTEXT_S = 1.5  # ... and stands out from the change around it (± 1.5 s) ...
SCENE_PROMINENCE = 1.6  # ... by at least this factor over the local median (a steady slow zoom is not a change of moment)
SCENE_SEPARATION_S = 1.0  # two scene changes are at least this far apart
SCENE_EDGE_S = 0.5  # changes centred in the first / last 0.5 s are the opening and the ending, not a change of moment
SCENE_SPAN_SHARE = 0.25  # frames changing at least this share of the peak frame belong to the transition
SCENE_SPAN_MAX_S = 1.5  # a transition is followed at most this far either side of its peak frame
CUT_MIN_DIFF = 8.0  # a hard cut: one frame changes at least this much ...
CUT_NEIGHBOUR_SHARE = 0.15  # ... and both neighbouring frames change less than this share of it
BLEND_NEIGHBOUR_S = 0.1  # each transition frame is compared with a blend of the frames 0.1 s before and after it
DISSOLVE_RESIDUAL = 0.34  # median distance from that blend (share of the neighbours' difference) below which it is a dissolve;
#   measured: still-photo dissolves 0.03–0.04, Ken Burns dissolves 0.27–0.30, cutroom pushes / irises / flips 0.40–0.72
STILL_PEAK_DIFF = 0.35  # a transition whose frames never change more than this per frame happens without visible motion
MOTION_WARN_SHARE = 0.8  # share of scene changes that happen in motion: WARN below
MOTION_FAIL_SHARE = 0.5  # FAIL below
SCENE_MIN_CHANGES = 2  # fewer changes than this: counts only (INFO)

# ------------------------------------------------------------------ faces
FACE_MODEL_FILE = "face_detection_yunet_2023mar.onnx"
FACE_SAMPLE_S = 1.0  # one frame per second
FACE_SCORE = 0.8  # YuNet confidence to count a face (its demo uses 0.9; lower catches small and side faces)
FACE_INPUT_MAX = 640  # frames are downscaled so their long side is at most this before detection
