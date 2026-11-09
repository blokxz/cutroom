#!/usr/bin/env python3
"""Spec-conformance checks for a skill built as spec.md + SKILL.md + guidelines.md + references/.

  spec.md        defines rule IDs (C-NN contracts, G-NN guardrails, R-NN creative rules) in table rows
  SKILL.md       router: small token budget, routes to guidelines.md and every references/*.md
  guidelines.md  + references/*.md cite spec IDs; every ID must be cited directly (not only inside a
                 range like R-03…R-06), every citation must exist

Usage: check_skill.py [skill_dir ...]   (default: every skills/<name>/ that has a spec.md)
Exit 1 on any problem. tools/check_plugin.py runs it in CI.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKILL_MAX_LINES = 40
SKILL_MAX_WORDS = 350
ID = r"(?<![A-Za-z0-9])[A-Z]-\d{2}(?!\d)"
DEFINE = re.compile(rf"^\|\s*({ID})\s*\|", re.M)
RANGE = re.compile(rf"({ID})\s*(?:…|\.\.\.)\s*({ID})")
CITE = re.compile(ID)
PREFIX = re.compile(r"^[A-Z]-")
PATHS = re.compile(r"(?<![\w/.-])((?:tools|schemas)/[\w./-]+\.(?:py|json)|scripts/[\w.-]+\.mjs)")
LOCAL = re.compile(r"(?<![\w/.-])((?:references/[\w.-]+|guidelines|spec)\.md|references/[\w.-]+\.md)")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def expand(text):
    """All IDs cited in text, with ranges like R-03…R-06 expanded."""
    ids = set(CITE.findall(text))
    for a, b in RANGE.findall(text):
        if a[0] == b[0]:
            ids.update(f"{a[0]}-{n:02d}" for n in range(int(a[2:]), int(b[2:]) + 1))
    return ids


def body(text):
    m = re.match(r"^---\n.*?\n---\n", text, re.S)
    return text[m.end():] if m else text


def check(skill_dir, root=ROOT):
    errors = []
    try:
        rel = os.path.relpath(skill_dir, root)
    except ValueError:  # Windows: the skill and the root are on different drives
        rel = skill_dir
    spec_p, skill_p, guide_p = (os.path.join(skill_dir, n) for n in ("spec.md", "SKILL.md", "guidelines.md"))
    ref_dir = os.path.join(skill_dir, "references")
    for p in (spec_p, skill_p, guide_p, ref_dir):
        if not os.path.exists(p):
            errors.append(f"{rel}: missing {os.path.basename(p)}")
    if errors:
        return errors

    spec = read(spec_p)
    defined = DEFINE.findall(spec)
    dupes = sorted({i for i in defined if defined.count(i) > 1})
    if dupes:
        errors.append(f"{rel}/spec.md: duplicate IDs {', '.join(dupes)}")
    defined = set(defined)
    if not defined:
        errors.append(f"{rel}/spec.md: defines no rule IDs")

    skill = body(read(skill_p))
    lines = [l for l in skill.strip().splitlines()]
    words = len(skill.split())
    if len(lines) > SKILL_MAX_LINES or words > SKILL_MAX_WORDS:
        errors.append(f"{rel}/SKILL.md: router over budget ({len(lines)} lines / {words} words; "
                      f"max {SKILL_MAX_LINES} / {SKILL_MAX_WORDS}) — move detail to guidelines.md or references/")

    refs = sorted(f"references/{f}" for f in os.listdir(ref_dir) if f.endswith(".md"))
    routed = set(LOCAL.findall(skill))
    for r in refs + ["guidelines.md", "spec.md"]:
        if r not in routed:
            errors.append(f"{rel}/SKILL.md: does not route to {r}")

    derived = {"SKILL.md": skill, "guidelines.md": read(guide_p)}
    derived.update({r: read(os.path.join(skill_dir, r)) for r in refs})
    applied = set()  # direct (non-range) citations in guidelines.md / references/ — the router does not count
    for name, text in derived.items():
        ids = expand(text)
        if name != "SKILL.md" and not ids:
            errors.append(f"{rel}/{name}: cites no spec ID (untraceable to spec.md)")
        for i in sorted(ids - defined):
            errors.append(f"{rel}/{name}: cites {i}, not defined in spec.md")
        if name != "SKILL.md":
            applied |= set(CITE.findall(RANGE.sub("", text)))
        for p in sorted(set(LOCAL.findall(text))):
            if not os.path.exists(os.path.join(skill_dir, p)):
                errors.append(f"{rel}/{name}: links missing {p}")
    for i in sorted(defined - applied):
        errors.append(f"{rel}/spec.md: {i} is not applied (cited directly) in guidelines.md or references/")

    for name, text in [("spec.md", spec)] + list(derived.items()):
        for p in sorted(set(PATHS.findall(text))):
            base = os.path.join(root, "remotion-base") if p.startswith("scripts/") else root
            if "<" not in p and not os.path.exists(os.path.join(base, p)):
                errors.append(f"{rel}/{name}: references missing {p}")
    return errors


def skill_dirs(root=ROOT):
    sk = os.path.join(root, "skills")
    return [os.path.join(sk, d) for d in sorted(os.listdir(sk)) if os.path.exists(os.path.join(sk, d, "spec.md"))]


def main(argv):
    dirs = [os.path.abspath(a) for a in argv] or skill_dirs()
    errors = [e for d in dirs for e in check(d)]
    for e in errors:
        print("ERROR", e)
    print(f"skill spec OK ({len(dirs)} skill(s))" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
