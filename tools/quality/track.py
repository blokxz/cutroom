"""Checks that use the per-frame element boxes written by remotion-base/scripts/render.mjs.
Platform-agnostic: the platform passes the text-safe rectangle and minimum text size.
"""
import json
import re

BEAT_KINDS = ("move", "rest", "hold", "cut")


def beat_kind(b):
    """A beat's kind: explicit `kind` in the track (move / rest / hold / cut), else guessed from its name."""
    k = b.get("kind")
    if k in BEAT_KINDS:
        return k
    name = b.get("name", "")
    if re.search(r"\bcut\b", name, re.I):
        return "cut"
    m = re.search(r"\b(rest|hold)\b", name, re.I)
    return m.group(1).lower() if m else "move"


def load_track(path):
    j = json.load(open(path, encoding="utf-8"))
    by_id = {}
    for r in j["records"]:
        by_id.setdefault(r["id"], {})[r["f"]] = r
    return j, by_id


def visible(r, W, H, min_o=0.3):
    return r is not None and r["o"] > min_o and r["w"] > 2 and r["h"] > 2 and r["x"] < W and r["y"] < H and r["x"] + r["w"] > 0 and r["y"] + r["h"] > 0


def edge_speed(a, b):
    return max(abs(b["x"] - a["x"]), abs(b["y"] - a["y"]), abs(b["x"] + b["w"] - a["x"] - a["w"]), abs(b["y"] + b["h"] - a["y"] - a["h"]))


def runs(frames, min_len):
    frames = sorted(frames)
    out, start, prev = [], None, None
    for f in frames + [None]:
        if f is not None and prev is not None and f == prev + 1:
            prev = f
            continue
        if start is not None and prev - start + 1 >= min_len:
            out.append((start, prev))
        start = prev = f
    return out


def continuity(j, by_id, report):
    W, H, fps = j["width"], j["height"], j["fps"]
    beats = j.get("beats", [])
    w = max(1, round(0.2 * fps))
    mw = max(w, round(0.6 * fps))  # eased moves start slowly: measure motion over a wider window after the boundary
    boundaries = [b for b in beats if b["f"] > 0 and beat_kind(b) != "cut"]
    replaced, carried_names = [], set()
    for b in boundaries:
        f0, f1 = b["f"] - w, b["f"] + w
        survivors = [i for i, fr in by_id.items() if visible(fr.get(f0), W, H) and visible(fr.get(f1), W, H)]
        if not survivors:
            replaced.append(b)
            continue
        for i in survivors:
            fr = by_id[i]
            a, c = fr[f0], fr.get(b["f"] + mw) or fr[f1]
            moved = abs((c["x"] + c["w"] / 2) - (a["x"] + a["w"] / 2)) > 12 or abs((c["y"] + c["h"] / 2) - (a["y"] + a["h"] / 2)) > 12
            resized = abs(c["w"] - a["w"]) > 0.05 * max(a["w"], 1) or abs(c["h"] - a["h"]) > 0.05 * max(a["h"], 1)
            if moved or resized:
                carried_names.add(b["name"])
                break
        else:
            # a new element that opens out of a survivor and grows also carries the cut (iris, reveal from the subject)
            for n, fr in by_id.items():
                if n in survivors or visible(fr.get(f0), W, H):
                    continue
                first = next((fr[f] for f in range(b["f"], b["f"] + mw + 1) if visible(fr.get(f), W, H)), None)
                last = fr.get(b["f"] + mw)
                if not first or not last:
                    continue
                inside = any(by_id[sv][f0]["x"] - 4 <= first["x"] and first["x"] + first["w"] <= by_id[sv][f0]["x"] + by_id[sv][f0]["w"] + 4
                             and by_id[sv][f0]["y"] - 4 <= first["y"] and first["y"] + first["h"] <= by_id[sv][f0]["y"] + by_id[sv][f0]["h"] + 4
                             for sv in survivors)
                if inside and last["w"] * last["h"] > 1.2 * first["w"] * first["h"]:
                    carried_names.add(b["name"])
                    break
    movers = [b for b in boundaries if beat_kind(b) == "move"]
    carried = sum(1 for b in movers if b["name"] in carried_names)
    explicit = sum(1 for b in beats if b.get("kind") in BEAT_KINDS)
    report.metrics["beat_kinds"] = "explicit" if beats and explicit == len(beats) else ("from names" if not explicit else f"{explicit}/{len(beats)} explicit, rest from names")
    report.metrics["scene_boundaries"] = len(boundaries)
    report.metrics["carried_boundaries"] = f"{carried}/{len(movers)} (rests/holds excluded)"
    report.metrics["replaced_boundaries"] = [b["name"] for b in replaced] or "none"
    if not beats:
        report.warn("continuity", "no <Beats> declared — scene boundaries can't be checked")
    for b in replaced:
        report.fail("continuity", f'at "{b["name"]}" (frame {b["f"]}) nothing on screen survives the change — the scene is replaced, not carried')
    if movers and carried / len(movers) < 0.5:
        report.warn("continuity", f"only {carried}/{len(movers)} active boundaries are carried by a moving element")


def _covered(r, W, H, margins, blocks):
    """True if a box crosses the margins (top, bottom, left, right) or overlaps one of the blocked rectangles."""
    top, bottom, left, right = margins
    if r["y"] < top - 4 or r["y"] + r["h"] > H - bottom + 4 or r["x"] < left - 4 or r["x"] + r["w"] > W - right + 4:
        return True
    return any(r["x"] + r["w"] > x0 + 4 and r["x"] < x1 - 4 and r["y"] + r["h"] > y0 + 4 and r["y"] < y1 - 4 for x0, y0, x1, y1 in blocks)


def element_checks(j, by_id, report, text_safe, min_text_h=0, blocked=None, caution=None, caution_blocked=None):
    """framing (inFrame elements), text inside the platform's safe rectangle, motion blur, text size.

    text_safe / caution: margins (top, bottom, left, right) at the platform's recommended size;
    blocked / caution_blocked: {name: (x0, y0, x1, y1)} areas the UI covers (e.g. an action column).
    Settled text in text_safe margins or blocked areas is a FAIL; in the caution ones a WARN."""
    W, H, fps, scale = j["width"], j["height"], j["fps"], j.get("scale", 1)
    margins = tuple(v * scale for v in text_safe)
    blocks = [tuple(v * scale for v in rect) for rect in (blocked or {}).values()]
    c_margins = tuple(v * scale for v in caution) if caution else None
    c_blocks = [tuple(v * scale for v in rect) for rect in (caution_blocked or {}).values()]
    fast_unblurred, small = [], set()
    for i, fr in by_id.items():
        out_of_frame, text_unsafe, text_caution = [], [], []
        for f in sorted(fr):
            r = fr[f]
            if not visible(r, W, H, 0.5):
                continue
            prev = fr.get(f - 1)
            sp = edge_speed(prev, r) if prev else 0
            if r.get("inFrame") and (r["x"] < -4 or r["y"] < -4 or r["x"] + r["w"] > W + 4 or r["y"] + r["h"] > H + 4):
                out_of_frame.append(f)
            if r["k"] == "text" and r["o"] > 0.6 and sp < 3:
                if _covered(r, W, H, margins, blocks):
                    text_unsafe.append(f)
                elif c_margins and _covered(r, W, H, c_margins, c_blocks):
                    text_caution.append(f)
                if min_text_h and r["h"] < min_text_h * scale:
                    small.add(i)
            if sp > 80 and not r.get("blurred"):
                fast_unblurred.append((i, f, sp))
        for a_, b_ in runs(out_of_frame, 3):
            report.fail("framing", f'"{i}" leaves the frame at {a_ / fps:.2f}–{b_ / fps:.2f}s')
        for a_, b_ in runs(text_unsafe, 3):
            report.fail("safe", f'text "{i}" sits in the area the platform UI covers at {a_ / fps:.2f}–{b_ / fps:.2f}s')
        for a_, b_ in runs(text_caution, 3):
            report.warn("safe", f'text "{i}" sits where a long caption or title, or the action buttons, can cover it at {a_ / fps:.2f}–{b_ / fps:.2f}s')
    if fast_unblurred:
        ids = sorted({i for i, _, _ in fast_unblurred})
        report.fail("blur", f"{len(fast_unblurred)} frames where {', '.join(ids)} move > 80 px/frame without motion blur")
    for i in sorted(small):
        report.warn("legibility", f'text "{i}" is under {min_text_h}px tall — hard to read on a phone')


def text_boxes_at(by_id, frame, W, H):
    """Visible text boxes at a frame (for cover / crop checks)."""
    return [(i, fr[frame]) for i, fr in by_id.items() if frame in fr and fr[frame]["k"] == "text" and visible(fr[frame], W, H, 0.6)]


# ------------------------------------------------------------------ reading time
def word_count(text):
    """Words a viewer has to read: whitespace-separated tokens with at least one letter or digit
    ("+54 9 11 0000-0000" is 4, "—" is 0)."""
    return sum(1 for tok in (text or "").split() if any(ch.isalnum() for ch in tok))


def required_reading_s(words):
    from .limits import READ_BASE_S, READ_PER_WORD_S

    return READ_BASE_S + READ_PER_WORD_S * words


def legible(r, W, H):
    """Fully legible: near-full opacity and the whole box inside the frame."""
    from .limits import READ_EDGE_TOLERANCE_PX as tol, READ_MIN_OPACITY

    return (r is not None and r["o"] >= READ_MIN_OPACITY and r["w"] > 2 and r["h"] > 2
            and r["x"] >= -tol and r["y"] >= -tol and r["x"] + r["w"] <= W + tol and r["y"] + r["h"] <= H + tol)


def appearances(frames, gap):
    """Continuous runs of frame numbers; holes of at most `gap` frames are bridged. → [(first, last)]"""
    out = []
    for f in sorted(frames):
        if out and f - out[-1][1] <= gap + 1:
            out[-1][1] = f
        else:
            out.append([f, f])
    return [tuple(a) for a in out]


def longest_text(records):
    """The longest non-empty `t` among track records (by word count, then length)."""
    best = ""
    for r in records:
        t = r.get("t") or ""
        if (word_count(t), len(t)) > (word_count(best), len(best)):
            best = t
    return best


def reading_time(j, by_id, report):
    """Every text element needs READ_BASE_S + READ_PER_WORD_S per word of full legibility in each appearance.
    Uses the `t` field (the element's text) of kind-text track records; without it the check is skipped."""
    from .limits import READ_FAIL_SHARE, READ_GAP_FRAMES

    W, H, fps = j["width"], j["height"], j["fps"]
    texts = {i: fr for i, fr in by_id.items() if any(r.get("k") == "text" for r in fr.values())}
    if not texts:
        return
    with_text = {i: fr for i, fr in texts.items() if any(r.get("t") for r in fr.values())}
    missing = sorted(set(texts) - set(with_text))
    if missing:
        report.info("reading", f"reading time not checked for {', '.join(missing)} — the track has no text (`t`) for them; re-render with the current render.mjs")
    worst = None
    checked = 0
    for i, fr in sorted(with_text.items()):
        legible_frames = [f for f, r in fr.items() if legible(r, W, H)]
        runs_ = appearances(legible_frames, READ_GAP_FRAMES)
        if not runs_ and any(visible(r, W, H) for r in fr.values()):
            sample = longest_text(r for r in fr.values())
            report.warn("reading", f'"{sample[:40]}" is on screen but never fully legible (opacity ≥ 0.9, whole box in frame) — intended as texture?')
        for a, b in runs_:
            # Judge each appearance by the longest text it shows: a typewriter's first frame is "R",
            # and a reused id may carry a different line each time it appears.
            text = longest_text(r for f, r in fr.items() if a <= f <= b)
            words = word_count(text)
            if not words:
                continue
            need = required_reading_s(words)
            checked += 1
            got = (b - a + 1) / fps
            share = got / need
            worst = share if worst is None else min(worst, share)
            if share >= 1:
                continue
            short = text if len(text) <= 40 else text[:37] + "…"
            msg = (f'"{short}" ({words} word{"s" if words != 1 else ""}) is fully legible for {got:.2f}s at {a / fps:.2f}s — '
                   f"needs ≈{need:.1f}s to be read; hold it longer or cut words")
            report.add("FAIL" if share < READ_FAIL_SHARE else "WARN", "reading", msg)
    report.metrics["text_appearances_checked"] = checked
    if worst is not None:
        report.metrics["reading_time_min_share"] = round(worst, 2)
