"""Claims check (tools/quality/claims.py) and how brief.py uses it, plus brief.py's stage rules.

    python3 -m pytest tools/tests/test_claims.py -q
"""
import json
import os
import subprocess
import sys

import pytest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

from quality import claims  # noqa: E402


def severities(text, lang):
    return [(f.severity, f.phrase.lower()) for f in claims.check(text, lang)]


# ------------------------------------------------------------------ Spanish
@pytest.mark.parametrize("text, phrase", [
    ("Aguas termales curativas", "curativas"),
    ("Un baño que te cura el alma", "cura"),
    ("Propiedades TERAPÉUTICAS", "terapéuticas"),
    ("Alivia el dolor de espalda", "alivia"),
    ("Ideal para la artrosis", "artrosis"),
    ("El agua que sana", "que sana"),
    ("Agua medicinal", "medicinal"),
    ("Te ayuda a curarte", "curarte"),
    ("Venir a curarse del todo", "curarse"),
    ("Sanate en el agua", "sanate"),
    ("Vení a sanarte", "sanarte"),
    ("Un lugar para sanarse", "sanarse"),
    ("Vamos a sanarnos", "sanarnos"),
    ("Chau dolor de espalda", "dolor de espalda"),
])
def test_spanish_health_claims_are_severe(text, phrase):
    assert ("severe", phrase) in severities(text, "es-AR")


@pytest.mark.parametrize("text", [
    "Descanso, bosque y agua termal",
    "El cura del pueblo bendijo la capilla",   # a priest, not a cure
    "Comida sana y vida tranquila",            # adjective
    "Una zona segura para los chicos",         # 'cura' inside a word
    "Tenemos algo para vos. Gift card para regalar. Pedí la tuya.",
    "Jamón curado y vino de la zona",
])
def test_spanish_negatives(text):
    assert not [f for f in claims.check(text, "es") if f.severity == "severe"], claims.check(text, "es")


@pytest.mark.parametrize("text", [
    "No hay dolor más lindo que irse",          # idiomatic: medium at most
    "Hay que curar la madera antes del invierno",
    "Curá el mate antes de usarlo",
    "Tratamiento facial y masajes",              # a spa service: medium
    "Un tratamiento para vos",
])
def test_spanish_idioms_and_spa_services_are_not_severe(text):
    assert not [f for f in claims.check(text, "es") if f.severity == "severe"], claims.check(text, "es")


def test_spanish_treatment_and_lone_pain_are_medium_and_curing_wood_is_nothing():
    assert ("medium", "tratamiento") in severities("Tratamiento facial", "es")
    assert ("medium", "dolor") in severities("No hay dolor más lindo que irse", "es")
    assert severities("Hay que curar la madera", "es") == []
    # the body-part form is one severe finding, not also a medium "dolor"
    assert severities("Dolor de espalda", "es") == [("severe", "dolor de espalda")]


def test_sin_costo_is_a_gratuity_claim():
    assert ("medium", "sin costo") in severities("Late check-out sin costo", "es")


@pytest.mark.parametrize("text, lang", [
    ("Descuentos de hasta el 30%", "es"),
    ("Promo 2x1. Check-in 14/16 hs", "es"),
    ("Promo 2x1, abierto 24/7", "es"),
    ("1/2 precio en la segunda noche", "es"),
    ("Promo 2x1 por 2-3 noches", "es"),
    ("Oferta 2x1 en cabañas. Reservas hasta el 30/11.", "es"),  # the date is in another sentence
    ("Up to 30% off until you book", "en"),
    ("30% off. Gift cards valid until Dec 15.", "en"),
])
def test_offers_without_a_real_date_in_their_sentence_are_flagged(text, lang):
    assert [f for f in claims.check(text, lang) if f.severity == "low"], text


@pytest.mark.parametrize("text, lang", [
    ("Promo 2x1 hasta el 30 de noviembre", "es"),
    ("Descuento del 20% hasta el 30/11", "es"),
    ("Oferta válida hasta 15/12/2026", "es"),
    ("Promo 2x1 del 1 al 15 de diciembre", "es"),
    ("Promo hasta 2026-12-15", "es"),
    ("20% off until Dec 15", "en"),
    ("Special deal until 12/15", "en"),
])
def test_offers_with_a_real_date_are_not_flagged(text, lang):
    assert not [f for f in claims.check(text, lang) if f.severity == "low"], claims.check(text, lang)


def test_spanish_superlatives_and_offers():
    found = severities("El mejor lugar, garantizado. Oferta 2x1 y desayuno gratis", "es")
    assert ("medium", "el mejor") in found and ("medium", "garantizado") in found and ("medium", "gratis") in found
    assert ("low", "oferta") in found and ("low", "2x1") in found


def test_offers_with_a_validity_are_not_flagged():
    assert not [f for f in claims.check("Promo 20% de descuento hasta el 30/11", "es") if f.severity == "low"]
    assert not [f for f in claims.check("Special offer: 20% off until Dec 15", "en") if f.severity == "low"]


# ------------------------------------------------------------------ English
@pytest.mark.parametrize("text, phrase", [
    ("Healing waters", "healing"),
    ("It cures stress", "cures"),
    ("Therapeutic baths", "therapeutic"),
    ("Relieves joint pain", "relieves"),
    ("Good for arthritis", "arthritis"),
    ("A full body detox", "detox"),
])
def test_english_health_claims_are_severe(text, phrase):
    assert ("severe", phrase) in severities(text, "en-US")


@pytest.mark.parametrize("text", [
    "Slow mornings by the thermal pool",
    "Feel free to write to us",
    "A stress-free weekend",
    "Wear comfortable heels",
    "A healthy breakfast",
])
def test_english_negatives(text):
    assert not [f for f in claims.check(text, "en") if f.severity in ("severe", "medium")], claims.check(text, "en")


def test_english_superlatives_free_and_offers():
    found = severities("The best spa, guaranteed. Free breakfast. Last rooms! 30% off", "en")
    assert ("medium", "the best") in found and ("medium", "guaranteed") in found
    assert ("medium", "free") in found and ("medium", "last rooms") in found and ("low", "30% off") in found


def test_phrase_keeps_original_spelling_and_language_fallback():
    f = claims.check("Aguas CURATIVAS", "es")[0]
    assert f.phrase == "CURATIVAS" and f.what and f.suggestion and "CURATIVAS" in f.context
    assert claims.rule_set("pt-BR")[0] == "en"
    assert claims.check("", "es") == []


def test_cli_exit_code(tmp_path):
    p = tmp_path / "caption.md"
    p.write_text("Aguas curativas en el bosque", encoding="utf-8")
    cli = os.path.join(TOOLS, "quality", "claims.py")
    r = subprocess.run([sys.executable, cli, str(p), "--language", "es"], capture_output=True, text=True)
    assert r.returncode == 1 and "SEVERE" in r.stdout and "1 severe" in r.stdout
    r = subprocess.run([sys.executable, cli, "Relax in the forest", "--language", "en"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


# ------------------------------------------------------------------ brief.py
EXAMPLE = os.path.join(ROOT, "clients", "sample", "briefs", "sample-post.json")


@pytest.fixture()
def client(tmp_path):
    """A copy of the sample client in a temp clients folder (CUTROOM_CLIENTS), with one photo."""
    d = tmp_path / "clients" / "demo"
    (d / "assets" / "photos").mkdir(parents=True)
    (d / "briefs").mkdir()
    with open(os.path.join(ROOT, "clients", "sample", "client.json"), encoding="utf-8") as f:
        c = json.load(f)
    c["slug"] = "demo"
    c["brand"].pop("logo", None)
    (d / "client.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    (d / "assets" / "photos" / "sunset.jpg").write_bytes(b"jpg")
    return d


def brief(status="brief", **changes):
    with open(EXAMPLE, encoding="utf-8") as f:
        b = json.load(f)
    b.update(client="demo", status=status, id="claims-test")
    b["assets"]["photos"] = ["assets/photos/sunset.jpg"]
    b.update(changes)
    return b


def run_check(client_dir, b):
    p = client_dir / "briefs" / "b.json"
    p.write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
    env = dict(os.environ, CUTROOM_CLIENTS=str(client_dir.parent))
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "brief.py"), "check", str(p)], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def test_example_briefs_stay_valid():
    for name in ("sample-post",):
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "brief.py"), "check",
                            os.path.join(ROOT, "clients", "sample", "briefs", f"{name}.json")], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout


def test_severe_claim_in_copy_is_an_error_and_medium_a_warning(client):
    b = brief()
    b["copy"]["headline"] = "Aguas curativas"
    code, out = run_check(client, b)
    assert code == 1 and "ERROR  claim (severe)" in out
    b["copy"]["headline"] = "Desayuno gratis"
    code, out = run_check(client, b)
    assert code == 0 and "WARN   claim (medium)" in out


def test_voice_guide_avoid_is_an_error(client):
    b = brief()
    b["copy"]["subtitle"] = "Un garantizado / fin de semana"
    code, out = run_check(client, b)
    assert code == 1 and "voice_guide.avoid" in out


def test_material_stage_exists_and_needs_nothing_extra(client):
    code, out = run_check(client, brief("material", concepts=[], chosen_concept=None, beats=[], composition=None))
    assert code == 0, out
    code, out = run_check(client, brief("concepts", concepts=[], chosen_concept=None, beats=[], composition=None))
    assert code == 1 and "fewer than 3 concepts" in out


def test_leaving_material_needs_the_analysis_and_selected_photos(client):
    b = brief("concepts", material=dict(batch="spring", analysis="material/spring/analysis.json", selected=[1, 2]))
    code, out = run_check(client, b)
    assert code == 1 and "does not exist" in out
    an = client / "material" / "spring"
    an.mkdir(parents=True)
    (an / "analysis.json").write_text(json.dumps({"photos": [{"id": 1, "file": "IMG_1.jpg"}, {"id": 2, "file": "IMG_2.jpg"}]}), encoding="utf-8")
    (client / "assets" / "photos" / "spring-01.jpg").write_bytes(b"jpg")
    b["assets"]["photos"].append("assets/photos/spring-01.jpg")
    code, out = run_check(client, b)
    assert code == 1 and "#2 is not in assets.photos" in out and "spring-02.jpg" in out
    b["material"]["selected"] = [1, 7]
    code, out = run_check(client, b)
    assert code == 1 and "material.selected 7 is not a photo id" in out
    b["material"]["selected"] = [1]
    code, out = run_check(client, b)
    assert code == 0, out


def test_typography_only_piece_is_allowed_with_a_warning(client):
    b = brief("concepts", assets=dict(photos=[], videos=[], music=None))
    code, out = run_check(client, b)
    assert code == 0 and "typography-only" in out


def test_schema_accepts_material_and_delivery(client):
    b = brief("delivered", delivery=dict(caption="deliveries/claims-test/caption.md", cover_time=1.2),
              material=dict(videos=[dict(id=1, start=1.5, dur=2.0, file="assets/photos/sunset.jpg"),
                                     dict(id=2, start=0.0, end=3.0, mode="card", file="assets/photos/sunset.jpg")]))
    code, out = run_check(client, b)
    assert code == 0, out
    b["status"] = "materials"
    code, out = run_check(client, b)
    assert code == 1 and "status" in out


def test_material_batch_with_nothing_selected_warns(client):
    an = client / "material" / "spring"
    an.mkdir(parents=True)
    (an / "analysis.json").write_text(json.dumps({"photos": [{"id": 1, "file": "IMG_1.jpg"}]}), encoding="utf-8")
    b = brief("concepts", material=dict(batch="spring", analysis="material/spring/analysis.json", selected=[]),
              assets=dict(photos=[], videos=[], music=None))
    code, out = run_check(client, b)
    assert code == 0 and "nothing selected" in out and "typography-only" in out, out
    b["material"]["selected"] = [1]
    b["assets"]["photos"] = ["assets/photos/sunset.jpg"]
    (client / "assets" / "photos" / "spring-01.jpg").write_bytes(b"jpg")
    b["assets"]["photos"].append("assets/photos/spring-01.jpg")
    code, out = run_check(client, b)
    assert code == 0 and "nothing selected" not in out, out


def test_source_folders_must_be_absolute_in_client_and_local_files(client, tmp_path):
    c = json.loads((client / "client.json").read_text(encoding="utf-8"))
    assert "source_folders" not in c  # machine paths stay out of the committed sample client.json
    (client / "client.local.json").write_text(json.dumps({"source_folders": [str(tmp_path / "originals")]}), encoding="utf-8")
    code, out = run_check(client, brief())
    assert code == 0, out
    (client / "client.local.json").write_text(json.dumps({"source_folders": ["Downloads/originals "]}), encoding="utf-8")
    code, out = run_check(client, brief())
    assert code == 1 and "client.local.json → source_folders entries must be absolute paths" in out, out
    (client / "client.local.json").write_text(json.dumps({"source_folders": "/not/a/list"}), encoding="utf-8")
    code, out = run_check(client, brief())
    assert code == 1 and "client.local.json → source_folders" in out, out
    (client / "client.local.json").write_text("{oops", encoding="utf-8")
    code, out = run_check(client, brief())
    assert code == 1 and "client.local.json is not valid JSON" in out, out
    (client / "client.local.json").unlink()
    c["source_folders"] = ["relative/folder"]
    (client / "client.json").write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
    code, out = run_check(client, brief())
    assert code == 1 and "client.json → source_folders entries must be absolute paths" in out, out


def test_client_new_does_not_write_source_folders(tmp_path):
    env = dict(os.environ, CUTROOM_CLIENTS=str(tmp_path / "clients"))
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "brief.py"), "client", "new", "acme", "--name", "Acme"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    c = json.loads((tmp_path / "clients" / "acme" / "client.json").read_text(encoding="utf-8"))
    assert "source_folders" not in c and "client.local.json" in r.stdout
