"""Spec-conformance of skills/<name>/ (spec.md → SKILL.md, guidelines.md, references/)."""
import os
import random
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import check_skill  # noqa: E402

ROOT = check_skill.ROOT
SKILL = os.path.join(ROOT, "skills", "video-direction")


@pytest.fixture
def copy(tmp_path):
    """A writable copy of the skill; repo paths it mentions still resolve against the real ROOT."""
    dst = tmp_path / "video-direction"
    shutil.copytree(SKILL, dst)
    return ROOT, str(dst)


def edit(path, fn):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    with open(path, "w", encoding="utf-8") as f:
        f.write(fn(text))


def test_repo_skill_conforms():
    assert check_skill.check(SKILL) == []


@pytest.mark.parametrize("d", check_skill.skill_dirs())
def test_every_spec_driven_skill_conforms(d):
    assert check_skill.check(d) == []


def test_every_skill_with_spec_is_checked():
    assert SKILL in check_skill.skill_dirs()


def test_range_expansion():
    assert check_skill.expand("[R-03…R-05 G-01]") == {"R-03", "R-04", "R-05", "G-01"}


def test_undefined_citation_fails(copy):
    root, d = copy
    edit(os.path.join(d, "guidelines.md"), lambda t: t + "\n- extra [R-99]\n")
    assert any("R-99" in e for e in check_skill.check(d, root))


def test_unapplied_rule_fails(copy):
    root, d = copy
    edit(os.path.join(d, "spec.md"), lambda t: t + "\n| G-98 | New guardrail nobody applies. |\n")
    assert any("G-98 is not applied" in e for e in check_skill.check(d, root))


def test_orphan_reference_fails(copy):
    root, d = copy
    with open(os.path.join(d, "references", "orphan.md"), "w", encoding="utf-8") as f:
        f.write("# orphan [G-01]\n")
    assert any("references/orphan.md" in e for e in check_skill.check(d, root))


def test_router_budget_fails(copy):
    root, d = copy
    edit(os.path.join(d, "SKILL.md"), lambda t: t + "\nfiller line\n" * 60)
    assert any("over budget" in e for e in check_skill.check(d, root))


def test_missing_tool_path_fails(copy):
    root, d = copy
    edit(os.path.join(d, "guidelines.md"), lambda t: t + "\n- run `python3 tools/nope.py` [G-01]\n")
    assert any("tools/nope.py" in e for e in check_skill.check(d, root))


@pytest.mark.parametrize("seed", range(12))
def test_fuzz_dropping_a_rule_citation_is_caught(copy, seed):
    """Seeded mutation: rename one spec ID everywhere outside spec.md — the check must report it."""
    root, d = copy
    with open(os.path.join(d, "spec.md"), encoding="utf-8") as f:
        ids = sorted(set(check_skill.DEFINE.findall(f.read())))
    victim = random.Random(seed).choice(ids)
    derived = ["SKILL.md", "guidelines.md"] + [os.path.join("references", f) for f in os.listdir(os.path.join(d, "references"))]
    for rel in derived:
        edit(os.path.join(d, rel), lambda t: t.replace(victim, "X-00"))
    errors = check_skill.check(d, root)
    assert any(f"{victim} is not applied" in e for e in errors), (victim, errors)
