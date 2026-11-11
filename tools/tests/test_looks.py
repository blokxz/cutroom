"""looks.py: every look reads, faces install from the @fontsource cache (no network in tests), client.json updates."""
import json
import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import looks  # noqa: E402

ROOT = looks.ROOT


def fake_family(cache, family, files, license_="OFL-1.1"):
    d = os.path.join(cache, looks.slug(family), "package")
    os.makedirs(os.path.join(d, "files"), exist_ok=True)
    with open(os.path.join(d, "package.json"), "w") as f:
        json.dump({"name": f"@fontsource/{looks.slug(family)}", "license": license_}, f)
    with open(os.path.join(d, "LICENSE"), "w") as f:
        f.write("SIL Open Font License 1.1")
    for name in files:
        with open(os.path.join(d, "files", name), "wb") as f:
            f.write(b"wOF2")


def test_every_shipped_look_passes_its_contrast_check():
    for lk in looks.load_looks():
        assert looks.check(lk) == [], lk["name"]


def test_check_catches_unreadable_ink():
    lk = {"colors": {"ground": "#FFFFFF", "paper": "#FFFFFF", "ink": "#EEEEEE", "soft": "#999999", "accent": "#FFFF00",
                     "accent2": "#000000", "line": "#DDDDDD"}}
    probs = looks.check(lk)
    assert any("ink on ground" in p for p in probs) and any("accent" in p for p in probs)


def test_contrast_black_on_white_is_21():
    assert looks.contrast("#000000", "#FFFFFF") == pytest.approx(21, abs=0.01)


def test_fetch_uses_the_cache_and_refuses_a_non_ofl_package(tmp_path, monkeypatch):
    monkeypatch.setenv("CUTROOM_FONT_CACHE", str(tmp_path))
    fake_family(str(tmp_path), "Test Serif", ["test-serif-latin-400-normal.woff2", "test-serif-latin-400-italic.woff2"])
    files, lic = looks.fetch("Test Serif", [400], italic=True)
    assert [s for _, _, s in files] == ["normal", "italic"] and lic.endswith("LICENSE")
    fake_family(str(tmp_path), "Closed Sans", ["closed-sans-latin-400-normal.woff2"], license_="Proprietary")
    with pytest.raises(RuntimeError):
        looks.fetch("Closed Sans")
    with pytest.raises(RuntimeError):
        looks.fetch("Test Serif", [700])  # a weight the package does not have


def test_install_writes_fonts_and_client_json(tmp_path, monkeypatch):
    monkeypatch.setenv("CUTROOM_FONT_CACHE", str(tmp_path / "cache"))
    fake_family(str(tmp_path / "cache"), "Test Serif", ["test-serif-latin-400-normal.woff2", "test-serif-latin-400-italic.woff2"])
    fake_family(str(tmp_path / "cache"), "Test Sans", ["test-sans-latin-400-normal.woff2", "test-sans-latin-600-normal.woff2"])
    client = tmp_path / "clients" / "demo"
    os.makedirs(client)
    shutil.copyfile(os.path.join(ROOT, "clients", "sample", "client.json"), client / "client.json")
    look = {"name": "t", "colors": {"ground": "#F0F0F0", "paper": "#FFFFFF", "ink": "#111111", "soft": "#555555",
                                    "accent": "#AA3311", "accent2": "#3366AA", "line": "#DDDDDD"},
            "faces": {"display": {"family": "Test Serif", "weights": [400], "italic": True},
                      "text": {"family": "Test Sans", "weights": [400, 600]}}}
    c = looks.install_look(look, str(client))
    fonts = c["brand"]["fonts"]
    assert fonts["display"] == "Test Serif" and fonts["text"] == "Test Sans"
    assert {"family": "Test Serif", "file": "test-serif-latin-400-italic.woff2", "weight": "400", "style": "italic"} in fonts["files"]
    assert c["brand"]["colors"]["ink"] == "#111111" and c["brand"]["look"] == "t"
    assert (client / "assets" / "fonts" / "test-sans-latin-600-normal.woff2").exists()
    assert (client / "assets" / "fonts" / "test-serif.LICENSE.txt").exists()
    kept = json.loads((client / "client.json").read_text())["brand"]["colors"]["ink"]
    c2 = looks.install_look(dict(look, colors={**look["colors"], "ink": "#000000"}), str(client), keep_colors=True)
    assert c2["brand"]["colors"]["ink"] == kept  # --keep-colors leaves the client's palette alone
