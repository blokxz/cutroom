#!/usr/bin/env python3
"""cutroom event-driven sound — sound cues placed from a render's .track.json instead of by hand.

  sound_events.py <track.json> [--out score.wav] [--json cues.json] [--gap 0.04]

Reads the beats (`f, name, kind`) and the per-frame element records the render logged, and derives
a short list of cues: {f, t, effect, volume, pan, why}. Rules (one sound room, fewer sounds than beats):
  - at most ONE cue per beat: the highest-priority candidate in it (ties: the earliest)
  - no two cues closer than --gap seconds (default 0.04): the lower priority one is dropped
  - text never triggers a sound; a subject, image or logo does when it first becomes visible
  - a hold (the CTA) gets the chime, a cut a click, a move boundary an air-in, a rest nothing
  - pan follows the element's x position on screen (±0.6 at the frame edges); beat cues are centred
--out also mixes the cues into one stereo WAV with the palette of tools/sfx.py (peak −3 dBFS; the
final −16 LUFS mastering still happens in tools/master.py). Use it as a single <Audio> in the piece,
or read cues.json to place <Audio> by frame. Deterministic: the same track gives the same cues and audio.
"""
import argparse
import json
import os
import sys
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PRIORITY = {"chime": 4, "tap": 3, "paper-slide": 3, "pop": 3, "click": 2, "air-in": 1}
APPEAR = {"subject": "tap", "shape": "tap", "image": "paper-slide", "logo": "pop"}  # text: none
VOLUME = {"chime": 0.8, "tap": 0.9, "paper-slide": 0.8, "pop": 0.8, "click": 0.7, "air-in": 0.6}
VISIBLE = 0.5
PAN_MAX = 0.6


def _beats(track):
    beats = sorted(track.get("beats") or [], key=lambda b: b["f"])
    return beats


def _beat_index(beats, f):
    i = 0
    for k, b in enumerate(beats):
        if f >= b["f"]:
            i = k
    return i


def pan_of(x, w, width):
    """Equal-power pan position −0.6…0.6 from a box's centre on screen."""
    if not width:
        return 0.0
    c = (x + w / 2) / width
    return round(max(-PAN_MAX, min(PAN_MAX, (c - 0.5) * 2 * PAN_MAX)), 3)


def candidates(track):
    """Every sound the track could justify, before the one-per-beat and spacing rules."""
    fps = track.get("fps", 30)
    width = track.get("width", 0)
    beats = _beats(track)
    out = []
    for b in beats:
        kind = b.get("kind") or ("hold" if "hold" in b["name"].lower() else "cut" if "cut" in b["name"].lower()
                                 else "rest" if "rest" in b["name"].lower() else "move")
        eff = {"hold": "chime", "cut": "click", "move": "air-in"}.get(kind)
        if eff and (b["f"] > 0 or kind in ("hold", "cut")):
            out.append({"f": b["f"], "effect": eff, "pan": 0.0, "why": f"beat '{b['name']}' ({kind})"})
    seen = set()
    for r in sorted(track.get("records") or [], key=lambda r: r["f"]):
        eff = APPEAR.get(r.get("k"))
        if not eff or r["id"] in seen or r.get("o", 0) < VISIBLE or r["f"] <= 1:
            continue
        seen.add(r["id"])
        out.append({"f": r["f"], "effect": eff, "pan": pan_of(r["x"], r["w"], width), "why": f"'{r['id']}' appears"})
    for c in out:
        c["t"] = round(c["f"] / fps, 3)
    return out


def cues(track, gap_s=0.04):
    """The final cue list: one per beat, spaced at least gap_s apart, in time order."""
    beats = _beats(track)
    best = {}
    for c in candidates(track):
        k = _beat_index(beats, c["f"]) if beats else 0
        cur = best.get(k)
        key = (PRIORITY[c["effect"]], -c["f"])
        if cur is None or key > (PRIORITY[cur["effect"]], -cur["f"]):
            best[k] = c
    chosen = sorted(best.values(), key=lambda c: c["f"])
    kept = []
    for c in chosen:
        if kept and c["t"] - kept[-1]["t"] < gap_s:
            if PRIORITY[c["effect"]] > PRIORITY[kept[-1]["effect"]]:
                kept[-1] = c
            continue
        kept.append(c)
    return [{**c, "volume": VOLUME[c["effect"]]} for c in kept]


def mix(cue_list, duration_s, sr=48000):
    """Stereo float array: each cue's effect placed at its time, equal-power panned, peak −3 dBFS."""
    import sfx  # tools/sfx.py: the palette and its room

    makers = {"air-in": sfx.air_in, "pop": sfx.pop, "paper-slide": sfx.paper_slide, "tap": sfx.tap,
              "chime": sfx.chime, "click": sfx.click}
    fx = {name: sfx.norm(makers[name]()) for name in sorted({c["effect"] for c in cue_list})}
    tail = max([len(v) for v in fx.values()] + [0])
    out = np.zeros((int(duration_s * sr) + tail, 2))
    for c in cue_list:
        x = fx[c["effect"]] * c["volume"]
        a = (c["pan"] + 1) * np.pi / 4  # equal power: −1 → left, +1 → right
        i = int(c["t"] * sr)
        out[i:i + len(x), 0] += x * np.cos(a)
        out[i:i + len(x), 1] += x * np.sin(a)
    peak = np.max(np.abs(out))
    if peak > 0:
        out *= 10 ** (-3 / 20) / peak
    return out[: int(duration_s * sr) + tail // 2]


def write_wav(path, stereo, sr=48000):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def duration_of(track):
    fs = [r["f"] for r in track.get("records") or []] + [b["f"] for b in track.get("beats") or []]
    return (max(fs) + 1) / track.get("fps", 30) if fs else 0.0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track")
    ap.add_argument("--out", help="write the mix as a stereo WAV")
    ap.add_argument("--json", help="write the cue list as JSON")
    ap.add_argument("--gap", type=float, default=0.04, help="minimum seconds between two cues")
    a = ap.parse_args(argv)
    with open(a.track, encoding="utf-8") as f:
        track = json.load(f)
    cl = cues(track, a.gap)
    for c in cl:
        print(f"  {c['t']:6.2f}s  f{c['f']:<4} {c['effect']:12} pan {c['pan']:+.2f}  {c['why']}")
    print(f"{len(cl)} cue(s) for {len(track.get('beats') or [])} beat(s)")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(cl, f, indent=1, ensure_ascii=False)
    if a.out:
        write_wav(a.out, mix(cl, duration_of(track)))
        print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
