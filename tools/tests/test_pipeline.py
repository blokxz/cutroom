"""Gate tests for tools/pipeline.py — fast, no rendering.

    python3 -m pytest tools/tests/test_pipeline.py -q
"""
import copy
import json
import os
import shutil
import sys
import tempfile

import pytest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

import pipeline  # noqa: E402

EXAMPLE = os.path.join(ROOT, "clients", "sample", "briefs", "sample-post.json")


@pytest.fixture()
def brief_dir():
    """A copy of the example brief inside the sample client (brief.py resolves the client by slug)."""
    d = tempfile.mkdtemp(dir=os.path.join(ROOT, "clients", "sample", "briefs"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def write(d, data, name="b.json"):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return p


def base(status):
    with open(EXAMPLE, encoding="utf-8") as f:
        b = json.load(f)
    b = copy.deepcopy(b)
    b["status"] = status
    b["id"] = "pipeline-test"
    return b


def test_crashing_or_malformed_brief_blocks_the_gate(brief_dir):
    b = base("brief")
    b["copy"]["lines"] = [1, 2]  # wrong type: used to crash brief.py and open the gate
    problems = pipeline.gate(write(brief_dir, b), b)
    assert problems, "a malformed brief must not pass the gate"


def test_chosen_concept_must_point_at_a_concept(brief_dir):
    b = base("concepts")
    b["chosen_concept"] = 9
    problems = pipeline.gate(write(brief_dir, b), b)
    assert any("chosen_concept" in p for p in problems)
    b["chosen_concept"] = 1
    assert not pipeline.gate(write(brief_dir, b), b)


def test_unknown_status_is_refused():
    with pytest.raises(SystemExit):
        pipeline.stage_of({"status": "Review"})


def test_review_needs_explicit_approval(brief_dir):
    b = base("review")
    p = write(brief_dir, b)
    assert pipeline.gate(p, b)
    assert not pipeline.gate(p, b, approved=True)


def _fake_render(tmp, b, entry, final=False):
    out = os.path.join(pipeline.REMOTION, "out", b["id"])
    os.makedirs(out, exist_ok=True)
    video = os.path.join(out, f"{b['composition']}{'' if final else '-draft'}.mp4")
    open(video, "wb").close()
    with open(os.path.join(out, ".render-cache.json"), "w", encoding="utf-8") as f:
        json.dump({video: entry}, f)
    return out


def test_building_gate_checks_verdict_and_staleness(brief_dir, monkeypatch):
    b = base("building")
    p = write(brief_dir, b)
    monkeypatch.setattr(pipeline, "current_key", lambda path, final: "KEY-NOW")
    out = _fake_render(brief_dir, b, {"key": "KEY-NOW", "verify": "fail"})
    try:
        assert any("did not pass" in x for x in pipeline.gate(p, b))
        _fake_render(brief_dir, b, {"key": "KEY-OLD", "verify": "pass"})
        assert any("changed since" in x for x in pipeline.gate(p, b))
        _fake_render(brief_dir, b, {"key": "KEY-NOW", "verify": "pass"})
        assert not pipeline.gate(p, b)
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_delivery_refuses_unmastered_final(brief_dir, monkeypatch):
    b = base("approved")
    p = write(brief_dir, b)
    monkeypatch.setattr(pipeline, "current_key", lambda path, final: "K")
    out = _fake_render(brief_dir, b, {"key": "K", "verify": "pass", "mastered": False}, final=True)
    try:
        assert any("mastering" in x for x in pipeline.gate(p, b))
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_delivery_needs_a_clean_package(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "DELIVERIES", str(tmp_path / "deliveries"))
    monkeypatch.setattr(pipeline, "REMOTION", str(tmp_path / "remotion"))
    monkeypatch.setattr(pipeline, "ROOT", str(tmp_path))
    b = {"id": "pkg-test", "composition": "Comp"}
    assert any("no delivery package" in x for x in pipeline.delivery_problems(b))
    out = tmp_path / "remotion" / "out" / "pkg-test"
    out.mkdir(parents=True)
    (out / "Comp.mp4").write_bytes(b"video-v1")
    d = tmp_path / "deliveries" / "pkg-test"
    d.mkdir(parents=True)
    (d / "caption.md").write_text("caption", encoding="utf-8")
    sha = pipeline._sha256

    def sheet(**kw):
        data = {"claims": [], "ready_to_publish": True, "errors": [],
                "caption": {"path": "deliveries/pkg-test/caption.md"},
                "files": {"Comp.mp4": {"sha256": sha(str(out / "Comp.mp4"))}, "caption.md": {"sha256": sha(str(d / "caption.md"))}}}
        data.update(kw)
        (d / "sheet.json").write_text(json.dumps(data), encoding="utf-8")

    sheet(claims=[{"severity": "severe", "phrase": "cura"}])
    assert any("severe claim" in x for x in pipeline.delivery_problems(b))
    sheet(ready_to_publish=False, errors=["caption has placeholders"])
    assert any("placeholders" in x for x in pipeline.delivery_problems(b))
    sheet(claims=[{"severity": "low", "phrase": "promo"}])
    assert pipeline.delivery_problems(b) == []
    (d / "caption.md").write_text("caption with aguas curativas", encoding="utf-8")
    assert any("caption changed" in x for x in pipeline.delivery_problems(b))
    (d / "caption.md").write_text("caption", encoding="utf-8")
    (out / "Comp.mp4").write_bytes(b"video-v2")
    assert any("final render changed" in x for x in pipeline.delivery_problems(b))
