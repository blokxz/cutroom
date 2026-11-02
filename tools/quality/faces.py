"""People in the picture: a local face detector (OpenCV's YuNet) on one frame per second.

It does not identify anyone; it only says "a face is visible here" so whoever publishes asks the
people in it for permission. Optional: without the model file the check is skipped with an INFO.

Model path: env CUTROOM_FACE_MODEL, else tools/models/face_detection_yunet_2023mar.onnx
(`python3 tools/models.py fetch` downloads and verifies it).
"""
import os

from . import limits as L

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(TOOLS, "models")


def model_path():
    return os.environ.get("CUTROOM_FACE_MODEL") or os.path.join(MODELS_DIR, L.FACE_MODEL_FILE)


def available():
    return os.path.isfile(model_path())


def sample_indices(duration, fps, every=L.FACE_SAMPLE_S):
    """Frame indices sampled once per `every` seconds (starting at 0)."""
    step = max(1, round(every * fps))
    total = max(1, int(duration * fps))
    return list(range(0, total, step))


class YuNet:
    """cv2.FaceDetectorYN wrapper: detect(bgr) → [(x, y, w, h, score)] in the frame's pixels."""

    def __init__(self, path=None, score=L.FACE_SCORE):
        import cv2

        self.cv2 = cv2
        self.score = score
        self.net = cv2.FaceDetectorYN.create(path or model_path(), "", (320, 320), score, 0.3, 5000)

    def detect(self, bgr):
        h, w = bgr.shape[:2]
        s = min(1.0, L.FACE_INPUT_MAX / max(h, w))
        im = self.cv2.resize(bgr, (int(w * s), int(h * s)), interpolation=self.cv2.INTER_AREA) if s < 1 else bgr
        self.net.setInputSize((im.shape[1], im.shape[0]))
        _, det = self.net.detect(im)
        out = []
        for d in (det if det is not None else []):
            if d[-1] >= self.score:
                x, y, ww, hh = (float(v) / s for v in d[:4])
                out.append((int(x), int(y), int(ww), int(hh), float(d[-1])))
        return out


def find_faces(frames, fps, detector):
    """frames: {index: bgr frame}. → [(seconds, number of faces)] for the frames with faces."""
    hits = []
    for idx in sorted(frames):
        f = frames[idx]
        if f is None:
            continue
        found = detector.detect(f)
        if found:
            hits.append((round(idx / fps, 1), len(found)))
    return hits


def check_faces(media, analysis, report, detector=None):
    """WARN with timestamps when faces are visible; INFO when the model is not installed."""
    if detector is None:
        if not available():
            report.info("faces", "face check skipped (run: python3 tools/models.py fetch)")
            return
        try:
            detector = YuNet()
        except Exception as ex:  # an OpenCV build without the dnn module, a corrupt file
            report.info("faces", f"face check skipped — the face model could not be loaded ({type(ex).__name__}: {ex})")
            return
    from .motion import frame_at

    kept = (analysis or {}).get("full_frames") or {}
    idx = sample_indices(media["duration"], media["fps"])
    frames = {i: frame_at(media["path"], i, kept) for i in idx}
    hits = find_faces(frames, media["fps"], detector)
    report.metrics["frames_with_faces"] = f"{len(hits)}/{len(idx)}"
    if hits:
        ts = ", ".join(f"{t:.0f}s" for t, _ in hits[:10]) + (" …" if len(hits) > 10 else "")
        report.warn("faces", f"people visible — get their permission before publishing (faces at {ts})")
