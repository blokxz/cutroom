#!/usr/bin/env python3
"""Static checks of the plugin packaging (run in CI; `claude plugin validate ./` does the full check locally)."""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []


def jload(rel):
    try:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        errors.append(f"{rel}: {e}")
        return {}


def frontmatter(rel, required):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        errors.append(f"missing {rel}")
        return
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        errors.append(f"{rel}: no YAML frontmatter")
        return
    keys = {line.split(":", 1)[0].strip() for line in m.group(1).splitlines() if ":" in line and not line.startswith(" ")}
    for k in required:
        if k not in keys:
            errors.append(f"{rel}: frontmatter lacks '{k}'")


plugin = jload(".claude-plugin/plugin.json")
if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", plugin.get("name", "")):
    errors.append("plugin.json: name must be kebab-case")
market = jload(".claude-plugin/marketplace.json")
for k in ("name", "owner", "plugins"):
    if k not in market:
        errors.append(f"marketplace.json: missing '{k}'")
names = [p.get("name") for p in market.get("plugins", [])]
if plugin.get("name") not in names:
    errors.append("marketplace.json does not list the plugin")
for d in sorted(os.listdir(os.path.join(ROOT, "skills"))):
    frontmatter(f"skills/{d}/SKILL.md", ["name", "description"])
for f in sorted(os.listdir(os.path.join(ROOT, "commands"))):
    if f.endswith(".md"):
        frontmatter(f"commands/{f}", ["description"])
        body = open(os.path.join(ROOT, "commands", f), encoding="utf-8").read()
        for script in re.findall(r"(tools/[\w.]+\.py|scripts/[\w.]+\.mjs)", body):
            base = ROOT if not script.startswith("scripts/") else os.path.join(ROOT, "remotion-base")
            if not os.path.exists(os.path.join(base, script)):
                errors.append(f"commands/{f} references missing {script}")

for e in errors:
    print("ERROR", e)
print("plugin packaging OK" if not errors else f"{len(errors)} problem(s)")
sys.exit(1 if errors else 0)
