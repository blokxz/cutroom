#!/usr/bin/env python3
"""Synthesize a small, soft, license-free sound-effect set (paper / air / wood family).

All effects share one synthetic room (the same impulse response), so they sound
like they belong together. Peaks are normalised to -3 dBFS to leave headroom.

    python3 tools/sfx.py --out remotion-base/public/sfx

Produces: air-in, air-out, pop, paper-slide, tap, flip, chime, click, riser, shimmer (.wav)
With --music DIR also a calm pad bed (and its licence) in DIR, e.g. clients/<slug>/assets/music, to test ducking.
"""
import argparse
import os
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(7)  # fixed seed: the same files every run


def t_axis(dur):
    return np.arange(int(SR * dur)) / SR


def lowpass(x, cutoff):
    # one-pole low-pass, simple and stable
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def bandpass(x, lo, hi):
    return lowpass(x, hi) - lowpass(x, lo)


def env(n, attack, release, shape=2.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    r = np.exp(-np.maximum(t - attack, 0) / max(release, 1e-4) * shape)
    return a * r


def room_ir(dur=0.9, decay=0.35):
    t = t_axis(dur)
    ir = rng.standard_normal(len(t)) * np.exp(-t / decay)
    ir = lowpass(ir, 5000)
    ir[0] = 1.0
    return ir / np.max(np.abs(ir))


IR = room_ir()


def in_room(dry, wet=0.18):
    w = np.convolve(dry, IR)[: len(dry) + int(0.6 * SR)]
    out = np.zeros(len(w))
    out[: len(dry)] += dry
    out += wet * w / (np.max(np.abs(w)) + 1e-9) * np.max(np.abs(dry))
    return out


def norm(x, peak_db=-3.0):
    fade = min(len(x), int(0.02 * SR))
    x = x.copy()
    x[-fade:] *= np.linspace(1, 0, fade)
    return x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)


def write(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    stereo = np.stack([pcm, pcm], axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


def air_in():  # soft rising whoosh
    n = int(0.7 * SR)
    noise = rng.standard_normal(n)
    sweep = np.linspace(300, 2400, n)
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):  # time-varying low-pass = sweep
        a = np.exp(-2 * np.pi * sweep[i] / SR)
        acc = (1 - a) * noise[i] + a * acc
        y[i] = acc
    y *= env(n, 0.35, 0.18)
    return in_room(y)


def pop():  # wax seal: short low thump + click
    t = t_axis(0.25)
    f = 180 * np.exp(-t * 18) + 90
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.002, 0.06)
    click = bandpass(rng.standard_normal(len(t)), 1500, 6000) * env(len(t), 0.0005, 0.008)
    return in_room(body + 0.5 * click)


def paper_slide():  # card sliding out of the envelope
    n = int(1.2 * SR)
    grain = bandpass(rng.standard_normal(n), 800, 5000)
    flutter = 0.6 + 0.4 * np.sin(2 * np.pi * 7 * t_axis(1.2))
    return in_room(grain * flutter * env(n, 0.25, 0.45, 1.5), wet=0.12)


def tap():  # card landing on a table: soft wood tap
    t = t_axis(0.3)
    body = (np.sin(2 * np.pi * 220 * t) + 0.5 * np.sin(2 * np.pi * 517 * t)) * env(len(t), 0.001, 0.05)
    knock = lowpass(rng.standard_normal(len(t)), 2500) * env(len(t), 0.0005, 0.01)
    return in_room(body + 0.6 * knock)


def flip():  # quick paper turn
    n = int(0.45 * SR)
    y = bandpass(rng.standard_normal(n), 1200, 7000) * env(n, 0.12, 0.12)
    return in_room(y, wet=0.15)


def chime():  # soft two-partial bell for the CTA
    t = t_axis(1.6)
    y = 0.0
    for f, a in [(880, 1.0), (1318.5, 0.5), (1760, 0.25)]:
        y = y + a * np.sin(2 * np.pi * f * t) * np.exp(-t * (2.2 + f / 1500))
    return in_room(y * env(len(t), 0.004, 1.2, 1.0), wet=0.25)


def air_out():  # falling whoosh (something leaving)
    return air_in()[::-1].copy()


def click():  # soft UI click
    t = t_axis(0.12)
    y = np.sin(2 * np.pi * 1800 * t) * env(len(t), 0.0005, 0.012) + 0.4 * lowpass(rng.standard_normal(len(t)), 4000) * env(len(t), 0.0003, 0.004)
    return in_room(y, wet=0.1)


def riser():  # short rise into a reveal
    n = int(0.9 * SR)
    t = t_axis(0.9)
    tone = np.sin(2 * np.pi * np.cumsum(np.linspace(220, 660, n)) / SR) * 0.4
    air = bandpass(rng.standard_normal(n), 600, 6000) * 0.6
    shape = (t / 0.9) ** 2
    return in_room((tone + air) * shape * env(n, 0.85, 0.05), wet=0.2)


def shimmer():  # light three-note arpeggio for a payoff
    t = t_axis(1.4)
    y = np.zeros(len(t))
    for k, f in enumerate([1046.5, 1318.5, 1568.0]):
        start = int(k * 0.07 * SR)
        tt = t[: len(t) - start]
        y[start:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3.2) * (0.9 - 0.2 * k)
    return in_room(y, wet=0.3)


def music_bed(seconds=12, bpm=84):
    """A calm, license-free pad + soft pulse bed to test ducking (not a substitute for real music)."""
    t = t_axis(seconds)
    chords = [(220.0, 277.18, 329.63), (196.0, 246.94, 293.66), (174.61, 220.0, 261.63), (196.0, 246.94, 329.63)]
    bar = 4 * 60 / bpm
    y = np.zeros(len(t))
    for i, ch in enumerate(chords * 4):
        s0 = int(i * bar * SR)
        if s0 >= len(t):
            break
        seg = t[: min(len(t) - s0, int(bar * SR * 1.3))]
        e = np.minimum(1, seg / 0.6) * np.exp(-np.maximum(seg - bar, 0) / 0.25)
        for f in ch:
            y[s0: s0 + len(seg)] += 0.18 * e * (np.sin(2 * np.pi * f * seg) + 0.3 * np.sin(2 * np.pi * 2 * f * seg))
    beat = 60 / bpm
    for k in range(int(seconds / beat)):
        s0 = int(k * beat * SR)
        seg = t[: int(0.25 * SR)]
        if s0 + len(seg) > len(t):
            break
        y[s0: s0 + len(seg)] += 0.25 * np.sin(2 * np.pi * 55 * seg) * np.exp(-seg * 18)
    return in_room(lowpass(y, 3500), wet=0.3)[: len(t)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="remotion-base/public/sfx")
    ap.add_argument("--music", metavar="DIR", help="also write a calm test music bed (+ licence) into DIR, e.g. clients/<slug>/assets/music")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    effects = [("air-in", air_in), ("air-out", air_out), ("pop", pop), ("paper-slide", paper_slide), ("tap", tap), ("flip", flip),
               ("chime", chime), ("click", click), ("riser", riser), ("shimmer", shimmer)]
    for name, fn in effects:
        write(os.path.join(a.out, f"{name}.wav"), norm(fn()))
        print("wrote", name)
    if a.music:
        mdir = a.music
        os.makedirs(mdir, exist_ok=True)
        write(os.path.join(mdir, "calm-bed.wav"), norm(music_bed(), -6.0))
        open(os.path.join(mdir, "calm-bed.LICENSE.txt"), "w", encoding="utf-8").write("Generated by tools/sfx.py — no third-party material. Free to use.\n")
        print(f"wrote {os.path.join(mdir, 'calm-bed.wav')} — index it in LIBRARY.json (brief.py music <slug>)")


def _utf8_output():
    """Windows consoles and pipes default to a legacy code page; our messages use → ≤ —."""
    import sys as _sys
    for stream in (_sys.stdout, _sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


if __name__ == "__main__":
    _utf8_output()
    main()
