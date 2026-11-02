"""Delivery package (tools/deliver.py) on a small synthetic video — no Remotion render.

    python3 -m pytest tools/tests/test_deliver.py -q
"""
import json
import os
import subprocess
import sys

import pytest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import deliver  # noqa: E402
from quality import bins  # noqa: E402

EXAMPLE = os.path.join(ROOT, "clients", "sample", "briefs", "sample-post.json")
COMP = "DemoStory"

CAPTION = """# Caption — deliver-test

## Short
Tenemos algo para mostrarte ✨
💬 Escribinos por WhatsApp · link en bio
#EstudioEjemplo #HechoAMano #Diseño

## Medium
Tenemos algo para mostrarte ✨
Tres palabras que resumen cómo trabajamos: diseño, color y detalle.
💬 Escribinos por WhatsApp · link en bio
📍 Buenos Aires
#EstudioEjemplo #HechoAMano #Diseño #Detalle #Color #Taller #DiseñoLocal #ObjetosConAlma

## Booking
Tenemos algo para mostrarte ✨
Tres palabras que resumen cómo trabajamos: diseño, color y detalle.
Escribinos y te contamos cómo encargar tu pieza.
💬 Escribinos por WhatsApp · link en bio
📍 Buenos Aires
#EstudioEjemplo #HechoAMano #Diseño #Detalle #Color #Taller #DiseñoLocal #ObjetosConAlma

## Hashtags
#EstudioEjemplo #HechoAMano #Diseño #Detalle #Color #Taller #DiseñoLocal #ObjetosConAlma

## Alt text
Las palabras diseño, color y detalle llegan una por una y forman una tarjeta del estudio.
"""


@pytest.fixture()
def env(tmp_path):
    """Temp clients, out and deliveries folders, a brief and a 2 s 1080x1920 video with AAC audio."""
    clients, out, dl = tmp_path / "clients", tmp_path / "out", tmp_path / "deliveries"
    d = clients / "demo"
    (d / "assets" / "photos").mkdir(parents=True)
    (d / "briefs").mkdir()
    with open(os.path.join(ROOT, "clients", "sample", "client.json"), encoding="utf-8") as f:
        c = json.load(f)
    c["slug"] = "demo"
    c["brand"].pop("logo", None)
    (d / "client.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    (d / "assets" / "photos" / "sunset.jpg").write_bytes(b"not really a jpg")
    with open(EXAMPLE, encoding="utf-8") as f:
        b = json.load(f)
    b.update(client="demo", id="deliver-test", composition=COMP, format="story")
    b["assets"]["photos"] = ["assets/photos/sunset.jpg"]
    bp = d / "briefs" / "deliver-test.json"
    bp.write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
    vd = out / "deliver-test"
    vd.mkdir(parents=True)
    video = vd / f"{COMP}.mp4"
    subprocess.run([bins.ffmpeg(), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30:duration=2",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(video)], check=True)
    (vd / ".render-cache.json").write_text(json.dumps({str(video): {"key": "k", "verify": "pass"}}), encoding="utf-8")
    e = dict(os.environ, CUTROOM_CLIENTS=str(clients), CUTROOM_OUT=str(out), CUTROOM_DELIVERIES=str(dl))
    return dict(env=e, brief=bp, dest=dl / "deliver-test", video=video, client=d)


def run(env, *extra):
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "deliver.py"), str(env["brief"]), *extra],
                       capture_output=True, text=True, env=env["env"])
    return r.returncode, r.stdout + r.stderr


def probe(path):
    out = subprocess.run([bins.ffprobe(), "-v", "error", "-show_streams", "-of", "json", str(path)], capture_output=True, text=True).stdout
    return json.loads(out)["streams"]


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def test_missing_caption_writes_a_prefilled_template_and_stops(env):
    code, out = run(env)
    assert code == 1 and "template" in out
    cap = (env["dest"] / "caption.md").read_text(encoding="utf-8")
    assert "## Short" in cap and "## Booking" in cap and "## Alt text" in cap
    assert "#EstudioEjemplo" in cap and "Escribinos por WhatsApp" in cap  # from voice_guide
    assert not (env["dest"] / "sheet.json").exists()
    # the unfilled template does not pass
    code, out = run(env)
    assert code == 1 and "placeholders" in out


def test_full_package(env):
    env["dest"].mkdir(parents=True)
    (env["dest"] / "caption.md").write_text(CAPTION, encoding="utf-8")
    code, out = run(env, "--cover-time", "1.0")
    assert code == 0, out
    for name in (f"{COMP}.mp4", "cover_9x16.png", "cover_grid_3x4.png", "cover_grid_1x1.png", "whatsapp_720p.mp4",
                 "caption.md", "sheet.json", "CHECKLIST.md"):
        assert (env["dest"] / name).exists(), name
    assert png_size(env["dest"] / "cover_9x16.png") == (1080, 1920)
    assert png_size(env["dest"] / "cover_grid_3x4.png") == (1080, 1440)
    assert png_size(env["dest"] / "cover_grid_1x1.png") == (1080, 1080)
    streams = probe(env["dest"] / "whatsapp_720p.mp4")
    v = next(s for s in streams if s["codec_type"] == "video")
    assert (v["width"], v["height"]) == (720, 1280)
    assert any(s["codec_type"] == "audio" and s["codec_name"] == "aac" for s in streams)
    assert os.path.getsize(env["dest"] / "whatsapp_720p.mp4") <= 15e6
    sheet = json.loads((env["dest"] / "sheet.json").read_text(encoding="utf-8"))
    assert sheet["cover"] == {"time_s": 1.0, "chosen_by": "given", "text_cut_in_grid": []}
    assert sheet["verifier"]["verify"] == "pass" and sheet["ready_to_publish"]
    assert sheet["versions"]["remotion"] and sheet["versions"]["python"]
    assert any(a["path"] == "assets/photos/sunset.jpg" and len(a["sha256"]) == 64 for a in sheet["assets"])
    assert any(t["source"] == "copy.headline" for t in sheet["on_screen_texts"])
    assert isinstance(sheet["claims"], list) and not any(c["severity"] == "severe" for c in sheet["claims"])
    assert "cover_9x16.png" in sheet["files"]
    checklist = (env["dest"] / "CHECKLIST.md").read_text(encoding="utf-8")
    assert "[x] Verifier verdict" in checklist and "People" in checklist and "Music" in checklist


def test_severe_claim_in_caption_fails_but_still_builds(env):
    env["dest"].mkdir(parents=True)
    (env["dest"] / "caption.md").write_text(CAPTION.replace("diseño, color y detalle.", "diseño, color y aguas curativas."), encoding="utf-8")
    code, out = run(env)
    assert code == 1 and "severe claim" in out
    sheet = json.loads((env["dest"] / "sheet.json").read_text(encoding="utf-8"))
    assert any(c["severity"] == "severe" and c["phrase"] == "curativas" for c in sheet["claims"])
    assert (env["dest"] / "whatsapp_720p.mp4").exists() and not sheet["ready_to_publish"]
    assert sheet["cover"]["chosen_by"] == "edge density"  # no .track.json next to the video


def test_caption_path_from_the_brief_is_copied_into_the_package(env):
    b = json.loads(env["brief"].read_text(encoding="utf-8"))
    custom = env["client"] / "caption-elsewhere.md"
    custom.write_text(CAPTION, encoding="utf-8")
    b["delivery"] = {"caption": os.path.relpath(custom, ROOT), "cover_time": 0.5}
    env["brief"].write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
    code, out = run(env)
    assert code == 0, out
    assert (env["dest"] / "caption.md").read_text(encoding="utf-8") == CAPTION
    assert json.loads((env["dest"] / "sheet.json").read_text(encoding="utf-8"))["cover"]["time_s"] == 0.5


def test_cover_from_track_prefers_the_frame_with_most_steady_text(tmp_path):
    recs = []
    for f in range(0, 120):
        o = 0.0 if f < 20 else min(1.0, (f - 20) / 10)  # headline fades in from frame 20 to 30
        recs.append(dict(f=f, k="text", id="headline", x=100, y=300, w=800, h=200, o=o, blurred=False))
        if 40 <= f < 70:  # a second line is on screen 40-69
            recs.append(dict(f=f, k="text", id="sub", x=100, y=600, w=800, h=200, o=1, blurred=False))
        recs.append(dict(f=f, k="shape", id="card", x=0, y=0, w=1080, h=1920, o=1, blurred=False))
    track = tmp_path / "x.track.json"
    track.write_text(json.dumps(dict(width=1080, height=1920, fps=30, records=recs)), encoding="utf-8")
    t = deliver.cover_from_track(str(track))
    assert 43 / 30 <= t <= 66 / 30
    track.write_text(json.dumps(dict(width=1080, height=1920, fps=30, records=[r for r in recs if r["k"] != "text"])), encoding="utf-8")
    assert deliver.cover_from_track(str(track)) is None


def test_caption_checks():
    sections = deliver.parse_caption(CAPTION)
    errors, warn = deliver.check_caption(sections, {"voice_guide": {"cta": "💬 Escribinos por WhatsApp · link en bio"}})
    assert not errors and not warn, (errors, warn)
    long_hook = CAPTION.replace("Tenemos algo para mostrarte ✨", "x" * 140, 1)
    _, warn = deliver.check_caption(deliver.parse_caption(long_hook), {})
    assert any("hook" in w for w in warn)


def test_grid_crops_that_cut_text_are_reported(tmp_path):
    recs = [dict(f=30, k="text", id="top", x=100, y=100, w=800, h=120, o=1),      # above the 3:4 and 1:1 windows
            dict(f=60, k="text", id="mid", x=100, y=900, w=800, h=120, o=1)]      # centred: fits both
    track = tmp_path / "x.track.json"
    track.write_text(json.dumps(dict(width=1080, height=1920, fps=30, records=recs)), encoding="utf-8")
    assert deliver.clipped_in_grid(str(track), 1.0) == ["3x4", "1x1"]
    assert deliver.clipped_in_grid(str(track), 2.0) == []
    assert deliver.clipped_in_grid(str(tmp_path / "missing.json"), 1.0) == []
