#!/usr/bin/env python3
"""Client material: analyse a folder of original photos / videos (read-only), pick by number, prepare for Remotion.

    python3 tools/material.py analyze <client> <folder_or_files...> [--batch NAME] [--videos] [--recursive]
        → clients/<client>/material/<batch>/analysis.json (schemas/material-analysis.schema.json)
          + contact_sheet.png (numbered photos) + video_sheet.png (with videos)
    python3 tools/material.py select <brief.json> 3,7,2 [--videos 1:4.0-7.5 2] [--batch NAME]
        → clients/<client>/assets/photos/<batch>-<nn>.jpg and assets/videos/<batch>-v<nn>-<start>.mp4,
          and the brief's `material` block + assets.photos / assets.videos. Re-selecting replaces the batch's
          previous photos (and, with --videos, its videos) in the brief; the exported files are kept.
    python3 tools/material.py clip <video> --start S --dur S --out <path> [--crop-top 0.16] [--mode vertical|card] [--warm 1.0]
    python3 tools/material.py guard <path>...      # is this path protected (read-only)?

The originals are never written: every output path goes through media.guard.ensure_writable, which refuses
anything inside a client's `source_folders` (client.local.json or client.json), inside CUTROOM_READONLY, or inside the folders
being analysed. Set CUTROOM_CLIENTS to use another clients folder.
"""
import argparse
import datetime
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from media import clips, contact_sheet, photos, videos  # noqa: E402
from media.common import (SCHEMAS, client_dir, default_batch, discover, load_json, rel_to,  # noqa: E402
                          save_json, slugify, source_roots)
from media.guard import ReadOnlyPathError, ensure_writable, protecting_folder  # noqa: E402


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def validate_analysis(data):
    """List of schema errors (empty = valid). Needs jsonschema."""
    import jsonschema
    schema = load_json(os.path.join(SCHEMAS, "material-analysis.schema.json"))
    v = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}" for e in v.iter_errors(data)]


# ------------------------------------------------------------------ analyze
def analyze(client, inputs, batch=None, with_videos=False, recursive=False, quiet=False):
    cdir = client_dir(client)
    if not os.path.isfile(os.path.join(cdir, "client.json")):
        raise FileNotFoundError(f"unknown client '{client}': {cdir}/client.json not found "
                                f"(create it with: python3 tools/brief.py client new {client} ...)")
    photo_files, video_files, skipped = discover(inputs, videos=with_videos, recursive=recursive)
    if not photo_files and not video_files:
        raise FileNotFoundError("no photos or videos found in " + ", ".join(inputs))
    roots = source_roots(inputs)
    batch = slugify(batch) if batch else default_batch(inputs)
    out_dir = os.path.join(cdir, "material", batch)
    ensure_writable(out_dir, roots)

    def file_rel(p):
        for r in roots:
            rp = rel_to(p, r)
            if rp != p:
                return rp
        return os.path.basename(p)

    t0 = time.time()
    precs = []
    for i, f in enumerate(photo_files, 1):
        try:
            rec = photos.measure(f)
        except Exception as e:  # unreadable / corrupt file: keep its number, flag it
            rec = {"width": 1, "height": 1, "orientation": "square", "focus": {"x": 0.5, "y": 0.5, "strength": 0.0},
                   "crop_9x16": {"x": 0, "y": 0, "w": 1, "h": 1}, "sharpness": {"laplacian": 0.0, "relative": None},
                   "exposure": {"mean_luma": 0.0, "clipped_shadows": 0.0, "clipped_highlights": 0.0}, "saturation": 0.0,
                   "horizon_tilt_deg": None, "upscale_9x16": 0.0, "hash": "0" * 16, "duplicates": [], "score": 0.0,
                   "rank": 0, "warnings": [], "errors": [f"cannot read image: {e}"], "_broken": True}
        precs.append(dict({"id": i, "source": f, "file": file_rel(f)}, **rec))
        if not quiet and i % 10 == 0:
            print(f"  photos {i}/{len(photo_files)}", flush=True)
    good = [r for r in precs if not r.get("_broken")]
    med = photos.finish(good)
    for r in precs:
        if r.pop("_broken", False):
            r["sharpness"]["relative"] = 0.0
            r["rank"] = len(precs)

    vrecs = []
    for i, f in enumerate(video_files, 1):
        try:
            rec = videos.analyze(f)
        except Exception as e:
            rec = {"width": 0, "height": 0, "duration_s": 0.0, "fps": 0.0, "hdr": False, "class": "unknown",
                   "windows": [], "warnings": [], "errors": [f"cannot analyse video: {e}"]}
        vrecs.append(dict({"id": i, "source": f, "file": file_rel(f)}, **rec))
        if not quiet:
            print(f"  video {i}/{len(video_files)}: {os.path.basename(f)}", flush=True)

    sheet = vsheet = None
    if precs:
        contact_sheet.photo_sheet(precs, os.path.join(out_dir, "contact_sheet.png"), roots)
        sheet = "contact_sheet.png"
    if vrecs:
        contact_sheet.video_sheet(vrecs, os.path.join(out_dir, "video_sheet.png"), roots)
        vsheet = "video_sheet.png"
    data = {
        "version": 1, "client": client, "batch": batch,
        "created": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "sources": roots, "thresholds": photos.THRESHOLDS, "sharpness_median": round(med, 1),
        "skipped": [os.path.abspath(s) for s in skipped],
        "sheets": {"photos": sheet, "videos": vsheet},
        "photos": precs, "videos": vrecs,
    }
    path = os.path.join(out_dir, "analysis.json")
    save_json(path, data, roots)
    return dict(data, _path=path, _seconds=round(time.time() - t0, 2))


def cmd_analyze(a):
    data = analyze(a.client, a.inputs, a.batch, a.videos, a.recursive)
    p, v = data["photos"], data["videos"]
    out = os.path.dirname(data["_path"])
    print(f"{len(p)} photos ({sum(1 for r in p if r['errors'])} with errors, {sum(1 for r in p if r['warnings'])} with warnings)"
          + (f", {len(v)} videos" if v else "") + f" in {data['_seconds']:.1f} s → {out}")
    for r in sorted(p, key=lambda r: r["rank"])[:min(8, len(p))]:
        flags = "; ".join(r["errors"] + r["warnings"])
        print(f"  #{r['id']:<3} rank {r['rank']:<3} score {r['score']:.2f}  {r['file']}" + (f"  [{flags}]" if flags else ""))
    for r in v:
        w = (r["windows"] or [None])[0]
        best = f"best {w['start']:.1f}-{w['end']:.1f}s ({w['score']:.2f})" if w else "no usable window"
        print(f"  video #{r['id']:<3} {r['class']:<9} {r['duration_s']:.1f}s {'HDR ' if r['hdr'] else ''}{best}  {r['file']}")
    vids = [os.path.splitext(s)[1] for s in data["skipped"]]
    if vids:
        print(f"  ({len(vids)} file(s) skipped; pass --videos to analyse the videos too)")
    print(f"look at {os.path.join(out, 'contact_sheet.png')}"
          + (f" and {os.path.join(out, 'video_sheet.png')}" if v else "")
          + "; then: python3 tools/material.py select <brief.json> <ids>")


# ------------------------------------------------------------------ select
VIDEO_SPEC = re.compile(r"^(\d+)(?::(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?))?$")


def parse_ids(text):
    try:
        ids = [int(x) for x in re.split(r"[,\s]+", text.strip()) if x]
    except ValueError:
        raise ValueError(f"photo ids must be numbers separated by commas, got '{text}'")
    if len(set(ids)) != len(ids):
        raise ValueError("a photo id is repeated")
    return ids


def parse_video_specs(specs):
    out = []
    for s in specs or []:
        for part in s.split(","):
            part = part.strip()
            if not part:
                continue
            m = VIDEO_SPEC.match(part)
            if not m:
                raise ValueError(f"bad video choice '{part}': use ID or ID:START-END, e.g. 1:4.0-7.5")
            vid = int(m.group(1))
            start = float(m.group(2)) if m.group(2) else None
            end = float(m.group(3)) if m.group(3) else None
            if start is not None and end <= start:
                raise ValueError(f"bad window in '{part}': end must be after start")
            out.append((vid, start, end))
    return out


def find_batch(cdir, brief, batch):
    if batch:
        return slugify(batch)
    if isinstance(brief.get("material"), dict) and brief["material"].get("batch"):
        return brief["material"]["batch"]
    mdir = os.path.join(cdir, "material")
    found = sorted(d for d in os.listdir(mdir) if os.path.isfile(os.path.join(mdir, d, "analysis.json"))) \
        if os.path.isdir(mdir) else []
    if len(found) == 1:
        return found[0]
    if not found:
        raise FileNotFoundError(f"no analysed batch in {mdir}: run `material.py analyze` first")
    raise ValueError(f"several batches ({', '.join(found)}): pass --batch")


def select(brief_path, ids, video_specs=(), batch=None, video_mode="auto", crop_top=0.0, warm=0.0,
           long_side=2400, preset="medium", quiet=False):
    brief = load_json(brief_path)
    client = brief.get("client")
    if not client:
        raise ValueError(f"{brief_path} has no 'client'")
    cdir = client_dir(client)
    batch = find_batch(cdir, brief, batch)
    analysis_rel = f"material/{batch}/analysis.json"
    analysis = load_json(os.path.join(cdir, analysis_rel))
    roots = analysis.get("sources") or []
    ensure_writable(brief_path, roots)
    by_id = {p["id"]: p for p in analysis["photos"]}
    vby_id = {v["id"]: v for v in analysis["videos"]}
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise ValueError(f"no photo with id {', '.join(map(str, missing))} in batch '{batch}' (1-{len(by_id)})")

    assets = brief.setdefault("assets", {})
    old_photos = list(assets.get("photos") or [])
    old_vids = list(assets.get("videos") or [])
    # a new selection replaces this batch's previous one; other entries (logo, other batches) stay put
    photo_list = assets["photos"] = [p for p in old_photos if not batch_photo(batch, p)]
    video_list = assets["videos"] = [v for v in old_vids if not (video_specs and batch_video(batch, v))]
    for i in ids:
        p = by_id[i]
        if p["errors"] and not quiet:
            print(f"  note: #{i} has errors: {'; '.join(p['errors'])}")
        rel = f"assets/photos/{batch}-{i:02d}.jpg"
        size = photos.export_photo(p["source"], os.path.join(cdir, rel), long_side=long_side, protect=roots)
        if rel not in photo_list:
            photo_list.append(rel)
        if not quiet:
            print(f"  photo #{i} → {rel} ({size[0]}x{size[1]})")

    chosen_videos = []
    for vid, start, end in video_specs:
        v = vby_id.get(vid)
        if not v:
            raise ValueError(f"no video with id {vid} in batch '{batch}'")
        if start is None:
            if not v.get("windows"):
                raise ValueError(f"video #{vid} has no suggested window: give one, e.g. {vid}:0.0-3.0")
            start, end = v["windows"][0]["start"], v["windows"][0]["end"]
        meta = videos.probe(v["source"])
        mode = clips.auto_mode(meta) if video_mode == "auto" else video_mode
        rel = f"assets/videos/{batch}-v{vid:02d}-{int(round(start * 10)):04d}.mp4"
        res = clips.prepare(v["source"], os.path.join(cdir, rel), start, end - start, mode=mode, crop_top=crop_top,
                            warm=warm, preset=preset, protect=roots)
        for w in res["warnings"]:
            print(f"  warning: video #{vid}: {w}", file=sys.stderr)
        if rel not in video_list:
            video_list.append(rel)
        chosen_videos.append({"id": vid, "start": round(start, 3), "end": round(end, 3), "mode": mode, "file": rel})
        if not quiet:
            print(f"  video #{vid} {start:.2f}-{end:.2f}s ({mode}) → {rel}")

    material = brief.get("material") if isinstance(brief.get("material"), dict) else {}
    brief["material"] = {"batch": batch, "analysis": analysis_rel, "selected": ids,
                         "videos": chosen_videos if video_specs else (material.get("videos") or [])}
    dropped = [p for p in old_photos + old_vids if p not in photo_list and p not in video_list]
    if dropped and not quiet:
        print(f"  no longer selected (files kept in {client}/assets): {', '.join(dropped)}")
    save_json(brief_path, brief, roots)
    return brief


def batch_photo(batch, path):
    """True for an assets.photos entry that `select` wrote for `batch` (assets/photos/<batch>-NN.jpg)."""
    return isinstance(path, str) and re.fullmatch(rf"assets/photos/{re.escape(batch)}-\d{{2,}}\.jpg", path) is not None


def batch_video(batch, path):
    """True for an assets.videos entry that `select` wrote for `batch` (assets/videos/<batch>-vNN-SSSS.mp4)."""
    return isinstance(path, str) and re.fullmatch(rf"assets/videos/{re.escape(batch)}-v\d{{2,}}-\d{{4,}}\.mp4", path) is not None


def cmd_select(a):
    ids = parse_ids(a.ids)
    specs = parse_video_specs(a.videos)
    select(a.brief, ids, specs, a.batch, a.video_mode, a.crop_top, a.warm, a.long_side)
    print(f"updated {a.brief}: material.selected = {ids}")


# ------------------------------------------------------------------ clip / guard
def cmd_clip(a):
    res = clips.prepare(a.video, a.out, a.start, a.dur, mode=a.mode, crop_top=a.crop_top, focus_x=a.focus_x,
                        warm=a.warm, preset=a.preset)
    for w in res["warnings"]:
        print(f"warning: {w}", file=sys.stderr)
    print(f"clip ready: {res['out']} · {res['duration_s']:.2f} s · {res['mode']} · source {res['source_size']}"
          + (" · HDR→SDR tone-mapped" if res["tonemapped"] else (" · HDR (not tone-mapped)" if res["hdr"] else "")))


def cmd_guard(a):
    blocked = False
    for p in a.paths:
        hit = protecting_folder(p)
        blocked |= bool(hit)
        print(f"PROTECTED {p}  ({hit[1]}: {hit[0]})" if hit else f"writable  {p}")
    sys.exit(3 if blocked else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("analyze", help="analyse originals (read-only) into clients/<client>/material/<batch>/")
    s.add_argument("client")
    s.add_argument("inputs", nargs="+", help="source folder(s) and/or files")
    s.add_argument("--batch", help="batch name (default: the source folder name, slugified)")
    s.add_argument("--videos", action="store_true", help="also analyse the videos found in the folders")
    s.add_argument("--recursive", action="store_true", help="look into sub-folders too")
    s.set_defaults(fn=cmd_analyze)
    s = sub.add_parser("select", help="copy the chosen photos / video windows into assets/ and record them in the brief")
    s.add_argument("brief")
    s.add_argument("ids", help="photo ids in the order wanted, e.g. 3,7,2 (use '' for none)")
    s.add_argument("--videos", nargs="*", default=[], help="ID (best window) or ID:START-END, e.g. 1:4.0-7.5")
    s.add_argument("--batch")
    s.add_argument("--video-mode", choices=["auto", "vertical", "card"], default="auto")
    s.add_argument("--crop-top", type=float, default=0.0)
    s.add_argument("--warm", type=float, default=0.0)
    s.add_argument("--long-side", type=int, default=2400)
    s.set_defaults(fn=cmd_select)
    s = sub.add_parser("clip", help="prepare one video window for Remotion")
    s.add_argument("video")
    s.add_argument("--start", type=float, default=0.0)
    s.add_argument("--dur", type=float, required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--crop-top", type=float, default=0.0, help="fraction of the height removed from the top")
    s.add_argument("--focus-x", type=float, default=0.5, help="horizontal centre of the 9:16 crop (0..1)")
    s.add_argument("--mode", choices=["vertical", "card"], default="vertical")
    s.add_argument("--warm", type=float, default=0.0)
    s.add_argument("--preset", default="medium", help="x264 preset")
    s.set_defaults(fn=cmd_clip)
    s = sub.add_parser("guard", help="tell whether paths are inside a protected (read-only) folder")
    s.add_argument("paths", nargs="+")
    s.set_defaults(fn=cmd_guard)
    a = ap.parse_args(argv)
    try:
        a.fn(a)
    except ReadOnlyPathError as e:
        die(str(e), 3)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        die(str(e))


if __name__ == "__main__":
    main()
