"""Variation engine and operational summary: determinism, rhythm rules (seeded fuzz), novelty, report content."""
import json
import os
import sys
import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import reel_summary  # noqa: E402
import variation  # noqa: E402

REG = variation.load_registry()
FAMS = [f["id"] for f in REG["families"]]


def test_registry_is_consistent():
    ck, bd = set(REG["carry_kinds"]), set(REG["boundaries"])
    assert len(set(FAMS)) == len(FAMS) >= 30
    for f in REG["families"]:
        assert f["carry_kind"] in ck and f["boundary"] in bd, f["id"]
        assert f["beats"][0] <= f["beats"][1]
        assert (f["status"] == "ready") == bool(f["moves"] and not f["needs"]), f["id"]


def test_registry_moves_exist_in_remotion():
    src = os.path.join(variation.ROOT, "remotion-base", "src", "moves")
    text = "".join(open(os.path.join(src, n), encoding="utf-8").read() for n in os.listdir(src))
    for f in REG["families"]:
        for m in f["moves"]:
            assert m in text, f"{f['id']}: move {m} not found in remotion-base/src/moves"


def test_sheet_is_deterministic():
    f = variation.family(REG, "window")
    assert variation.sheet(f, 12, 3) == variation.sheet(f, 12, 3)
    assert variation.sheet(f, 12, 3) != variation.sheet(f, 12, 4)


@pytest.mark.parametrize("fid", FAMS)
@pytest.mark.parametrize("duration", [6, 9.5, 15, 30])
def test_fuzz_sheets_obey_the_rhythm_rules(fid, duration):
    fam = variation.family(REG, fid)
    for seed in range(8):
        beats = variation.sheet(fam, duration, seed)
        assert variation.check(beats, duration) == [], (fid, duration, seed, beats)
        assert beats[-1]["kind"] == "hold" and len({b["t"] for b in beats}) == len(beats)


def test_too_short_is_refused():
    with pytest.raises(ValueError):
        variation.sheet(variation.family(REG, "window"), 2.0, 0)


def test_check_catches_each_rule():
    even = [{"t": f"{i}.0–{i + 1}.0", "beat": "b", "kind": "move", "carries": "x"} for i in range(5)]
    even[-1]["kind"] = "hold"
    assert any("too even" in p for p in variation.check(even, 5))
    assert any("CTA hold" in p for p in variation.check(even, 5))  # 1.0s hold < 1.5s
    ok = variation.sheet(variation.family(REG, "key"), 8, 1)
    ok[0]["carries"] = ""
    assert any("survivor" in p for p in variation.check(ok, 8))
    assert any("ends at" in p for p in variation.check(variation.sheet(variation.family(REG, "key"), 8, 1), 9))


def test_invent_is_novel_and_deterministic():
    have = {(f["carry_kind"], f["boundary"]) for f in REG["families"]}
    got = variation.invent(REG, 5, 3)
    assert got == variation.invent(REG, 5, 3) and len(got) == 3
    for c in got:
        assert (c["carry_kind"], c["boundary"]) not in have
        assert all(m for m in c["moves"]), "invented concept must be buildable from existing moves"


def _brief(root, slug, i, **kw):
    d = root / "clients" / slug / "briefs"
    d.mkdir(parents=True, exist_ok=True)
    b = {"id": i, "client": slug, "platform": "instagram", "status": "delivered", **kw}
    (d / f"{i}.json").write_text(json.dumps(b), encoding="utf-8")


def test_summary_flags_failing_stuck_and_stale(tmp_path):
    _brief(tmp_path, "c", "a", status="building", composition=None)
    _brief(tmp_path, "c", "b", status="review", composition="B")
    out = tmp_path / "remotion-base" / "out" / "b"
    out.mkdir(parents=True)
    (out / ".render-cache.json").write_text(json.dumps({"B-draft.mp4": {"verify": "fail"}}), encoding="utf-8")
    spec = tmp_path / "tools" / "quality" / "platforms" / "specs"
    spec.mkdir(parents=True)
    (spec / "instagram.json").write_text(json.dumps({"reviewed": "2020-01-01"}), encoding="utf-8")
    d = reel_summary.gather(str(tmp_path), today=datetime.date(2026, 11, 2))
    assert d["failing"] == ["b"] and d["stuck"] == ["a"] and d["stale_specs"][0][0] == "instagram"
    acts = reel_summary.actions(d)
    assert [p for p, _, _ in acts] == ["P0", "P0", "P0"]
    assert "P0" in reel_summary.render(d, acts)


def test_summary_of_the_repo_is_readable_and_sorted():
    d = reel_summary.gather(today=datetime.date(2026, 11, 2))
    acts = reel_summary.actions(d)
    assert [p for p, _, _ in acts] == sorted(p for p, _, _ in acts)
    assert d["families_total"] == len(FAMS)
    assert all(n != 8 for n, _ in d["behind"]), "parked modules are not actions"
    assert all(n != 3 for n, _ in d["behind"]), "mixed verdicts (ahead for brands) are not gaps"
