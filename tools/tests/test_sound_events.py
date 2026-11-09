"""Event-driven sound: cues from a track.json — one per beat, spaced, text-free, panned, deterministic."""
import json
import os
import sys
import wave

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sound_events as se  # noqa: E402


def rec(f, i, k, x, w=100, o=1.0):
    return {"f": f, "lf": f, "id": i, "k": k, "x": x, "y": 0, "w": w, "h": 100, "o": o, "inFrame": True, "blurred": False}


def track():
    return {
        "width": 1080, "height": 1350, "fps": 30, "scale": 1,
        "beats": [
            {"f": 0, "name": "open", "kind": "move"},
            {"f": 40, "name": "rest", "kind": "rest"},
            {"f": 55, "name": "next", "kind": "move"},
            {"f": 100, "name": "CTA hold", "kind": "hold"},
        ],
        "records": [
            rec(1, "card", "subject", 900, o=0),      # invisible at first
            rec(60, "card", "subject", 900, o=1),     # appears at f60 on the right
            rec(1, "word", "text", 10),               # text never sounds
            rec(5, "word", "text", 10),
            rec(30, "logo", "logo", 100, o=1),        # appears at f30 on the left (beat 0)
            rec(110, "end", "image", 400, o=1),
        ],
    }


def test_text_never_triggers_a_sound():
    assert all("word" not in c["why"] for c in se.candidates(track()))


def test_at_most_one_cue_per_beat_and_never_more_than_beats():
    t = track()
    cl = se.cues(t)
    assert len(cl) <= len(t["beats"])
    beats = t["beats"]
    idx = [se._beat_index(beats, c["f"]) for c in cl]
    assert len(idx) == len(set(idx))


def test_highest_priority_wins_inside_a_beat():
    cl = se.cues(track())
    last = [c for c in cl if c["f"] >= 100]
    assert len(last) == 1 and last[0]["effect"] == "chime"  # hold chime beats the image paper-slide at f110


def test_rest_makes_no_sound():
    assert not any(c["f"] == 40 for c in se.candidates(track()))


def test_cues_are_spaced_by_the_gap():
    t = track()
    t["beats"] = [{"f": 0, "name": "a", "kind": "move"}, {"f": 1, "name": "b", "kind": "move"}]
    t["records"] = [rec(10, "a", "subject", 100), rec(11, "b", "logo", 100)]
    cl = se.cues(t, gap_s=0.5)
    assert all(b["t"] - a["t"] >= 0.5 for a, b in zip(cl, cl[1:]))
    assert len(se.cues(t, gap_s=0.0)) >= len(cl)


def test_pan_follows_x_and_stays_in_range():
    assert se.pan_of(0, 100, 1080) < 0
    assert se.pan_of(980, 100, 1080) > 0
    assert se.pan_of(490, 100, 1080) == pytest.approx(0, abs=0.01)
    assert se.pan_of(-5000, 10, 1080) == -0.6
    assert se.pan_of(9000, 10, 1080) == 0.6
    assert se.pan_of(0, 10, 0) == 0.0
    by = {c["why"]: c for c in se.candidates(track())}
    assert by["'card' appears"]["pan"] > 0 > by["'logo' appears"]["pan"]


def test_deterministic():
    assert se.cues(track()) == se.cues(track())


def test_fuzz_random_tracks_keep_the_rules():
    rng = np.random.default_rng(3)
    for _ in range(40):
        n = int(rng.integers(2, 9))
        fs = sorted(rng.choice(np.arange(0, 300), n, replace=False).tolist())
        fs[0] = 0
        kinds = ["move", "rest", "hold", "cut"]
        t = {"width": 1080, "height": 1920, "fps": 30,
             "beats": [{"f": f, "name": f"b{i}", "kind": kinds[int(rng.integers(0, 4))]} for i, f in enumerate(fs)],
             "records": [rec(int(rng.integers(2, 300)), f"e{i}", ["subject", "text", "image", "logo", "shape"][int(rng.integers(0, 5))],
                             int(rng.integers(-200, 1200)), o=float(rng.random())) for i in range(15)]}
        cl = se.cues(t, 0.04)
        assert len(cl) <= len(t["beats"])
        assert all(b["t"] - a["t"] >= 0.04 for a, b in zip(cl, cl[1:]))
        assert all(-0.6 <= c["pan"] <= 0.6 for c in cl)
        assert [c["f"] for c in cl] == sorted(c["f"] for c in cl)


def test_mix_is_stereo_panned_and_peaks_at_minus_three(tmp_path):
    t = track()
    cl = [c for c in se.cues(t) if c["effect"] == "tap"]
    assert cl, "the fixture has a tap cue"
    cl[0]["pan"] = 0.6  # hard right
    stereo = se.mix(cl, 3.0)
    assert stereo.shape[1] == 2
    assert np.abs(stereo[:, 1]).sum() > 2 * np.abs(stereo[:, 0]).sum()
    assert np.max(np.abs(stereo)) == pytest.approx(10 ** (-3 / 20), rel=1e-3)
    path = tmp_path / "score.wav"
    se.write_wav(str(path), stereo)
    with wave.open(str(path)) as w:
        assert (w.getnchannels(), w.getframerate()) == (2, 48000)
        assert w.getnframes() == len(stereo)


def test_mix_is_deterministic_and_order_independent():
    """The docstring promises the same audio for the same track: noise must not depend on history."""
    cl = [c for c in se.cues(track()) if c["effect"] in ("tap", "air-in", "chime")]
    assert len({c["effect"] for c in cl}) >= 2
    a = se.mix(cl, 3.0)
    b = se.mix(cl, 3.0)  # second call in the same process
    assert np.array_equal(a, b)
    taps = [dict(c) for c in cl if c["effect"] == "tap"]
    alone = se.mix(taps, 3.0)
    again = se.mix(list(reversed(cl)), 3.0)
    assert np.array_equal(a, again)  # cue order does not change the audio
    assert np.max(np.abs(alone)) > 0


def test_mix_covers_a_cue_after_the_given_duration():
    late = [{"f": 300, "t": 10.0, "effect": "click", "volume": 0.7, "pan": 0.0, "why": "x"}]
    assert len(se.mix(late, 1.0)) >= int(10.0 * 48000)


def test_cli_writes_cues_and_wav(tmp_path, capsys):
    tp = tmp_path / "x.track.json"
    tp.write_text(json.dumps(track()), encoding="utf-8")
    out = tmp_path / "score.wav"
    js = tmp_path / "cues.json"
    assert se.main([str(tp), "--out", str(out), "--json", str(js)]) == 0
    cues = json.loads(js.read_text(encoding="utf-8"))
    assert cues and out.stat().st_size > 1000
    assert "cue(s) for 4 beat(s)" in capsys.readouterr().out
