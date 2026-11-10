"""The blur check measures speed between two laid-out boxes, never from an unmeasured (zero-size) frame."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from quality.report import Report  # noqa: E402
from quality.track import element_checks  # noqa: E402

J = {"width": 1080, "height": 1920, "fps": 30, "scale": 1}


def rec(f, x, y, w, h, blurred=False):
    return {"f": f, "id": "photo", "k": "image", "x": x, "y": y, "w": w, "h": h, "o": 1, "inFrame": False, "blurred": blurred}


def blur_fails(by_id):
    rep = Report()
    element_checks(J, by_id, rep, (0, 0, 0, 0))
    return [i for i in rep.items if i["check"] == "blur"]


def test_a_zero_size_first_frame_is_not_a_jump():
    fr = {1: rec(1, 0, 0, 0, 0), 2: rec(2, 0, 0, 1080, 1920), 3: rec(3, 0, 0, 1080, 1920)}
    assert blur_fails({"photo": fr}) == []


def test_a_real_fast_move_without_blur_still_fails():
    fr = {1: rec(1, 0, 0, 400, 400), 2: rec(2, 300, 0, 400, 400)}
    assert blur_fails({"photo": fr})
    fr_b = {1: rec(1, 0, 0, 400, 400, True), 2: rec(2, 300, 0, 400, 400, True)}
    assert blur_fails({"photo": fr_b}) == []
