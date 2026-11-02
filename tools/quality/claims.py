#!/usr/bin/env python3
"""Claims check: phrases in captions and on-screen copy that can get a client in trouble.

    python3 tools/quality/claims.py FILE_OR_TEXT... [--language es]

Three severities:
  severe  health, cure or therapeutic promises (a hospitality or wellness business must not make them)
  medium  guarantees, unproven superlatives, gratuity or availability claims, false urgency
  low     prices, offers and discounts with no validity date (skipped when the same sentence states a real
          date: "hasta el 30/11", "until Dec 15"; "hasta el 30%", "24/7" or "14/16 hs" are not dates)

Matching is case- and accent-insensitive and respects word boundaries. Rule sets are data (RULES below),
one per language; a BCP-47 tag like es-AR uses the "es" set, an unknown language falls back to English.
It is an aid, not a lawyer: false negatives exist, and a human still reads the text.
Exit code 1 when any finding is severe.
"""
import argparse
import bisect
import os
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass

SEVERITIES = ("severe", "medium", "low")


@dataclass
class Finding:
    severity: str      # "severe" | "medium" | "low"
    phrase: str        # the matched text, as written
    what: str          # what kind of claim it is
    suggestion: str    # what to write instead
    context: str = ""  # a few words around the phrase
    source: str = ""   # where it was found (file, copy.headline, …)

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Rule:
    severity: str
    pattern: str            # regex over lower-cased, accent-free text
    what: str
    suggestion: str
    needs_dates: bool = False  # skipped when the same sentence states a validity date


HEALTH_ES = 'talk about the feeling instead: "relax", "descanso", "bienestar", "agua termal", "te devuelve el eje"'
HEALTH_EN = 'talk about the feeling instead: "unwind", "rest", "warm thermal water", "slow mornings"'

# Spanish attached pronouns: curarte, curarse, sanarnos, curandote (accents are already stripped)
ENCLITIC = r"(?:te|se|nos|me|lo|la|los|las|le|les)?"
NOT_CURING_FOOD = (r"(?! (?:(?:el|la|los|las|un|una|tu|tus|su|sus) )?(?:maderas?|carnes?|jamon(?:es)?|cueros?|embutidos?"
                   r"|quesos?|fiambres?|tablas?|mates?|calabazas?|hormigon|cemento)\b)")

RULES = {
    "es": [
        # "el cura" / "un cura" is a priest; "la cura", "te cura", "curar" are cure claims
        # curing wood, meat, leather or a mate gourd is not a health claim
        Rule("severe", r"(?:(?<!\bel )(?<!\bun )(?<!\blos )(?<!\bunos )\bcuras?\b|\bcura(?:r|n|ra|ran|ria|rian|ndo)" + ENCLITIC + r"\b"
             r"|\bcurate\b)" + NOT_CURING_FOOD + r"|\bcurativ[oa]s?\b",
             "cure claim", HEALTH_ES),
        # "sana" is mostly an adjective (vida sana, comida sana): flag only verb uses and the unambiguous forms
        Rule("severe", r"\bsana(?:r|ndo)" + ENCLITIC + r"\b|\bsanate\b|\bsana(?:dor|dora|dores|doras)\b|\bsanacion(?:es)?\b|\b(?:que|te|nos|lo|la|los|las|se) sanan?\b"
             r"|\bsanan? (?:tu|tus|el|la|los|las|cuerpo|alma|heridas)\b",
             "healing claim", HEALTH_ES),
        Rule("severe", r"\bterapeutic[oa]s?\b|\bterapias?\b|\bmedicinal(?:es)?\b"
             r"|\bmilagros[oa]s?\b|\bmilagros?\b",
             "medical or therapeutic claim", 'say "agua termal", "descanso"'),
        Rule("severe", r"\balivia(?:r|n|s|ndo)?\b|\balivio\b|\bprevien(?:e|en)\b|\bprevenir\b|\bmejora(?:r|n)? (?:tu|la|su) salud\b"
             r"|\bdolor(?:es)? (?:de )?(?:espalda|cabeza|cuello|huesos|articulaciones|rodillas?|cintura|piernas|musculares|articulares|cronicos?)\b"
             r"|\breumat\w*|\breuma\b|\bartrosis\b|\bartritis\b|\bcontractura\w*|\bestres cronico\b"
             r"|\bdesintoxic\w*|\bdetox\b|\bdepurativ[oa]s?\b",
             "claim about health or ailments", HEALTH_ES),
        Rule("medium", r"\btratamientos?\b(?! de (?:datos|residuos))",
             "treatment: reads as medical unless it is clearly a spa service", "name the service plainly (masaje, baño)"),
        # "dolor" alone is often idiomatic ("no hay dolor más lindo que…"); with a body part it is severe (above)
        Rule("medium", r"\bdolor(?:es)?\b",
             "mentions pain: make sure it does not read as a health promise", HEALTH_ES),
        Rule("medium", r"\brejuvenec\w*|\badelgaz\w*",
             "body-effect claim", "describe the experience, not an effect on the body"),
        Rule("medium", r"\bgarantizad[oa]s?\b|\bgarantia\b|\b100 ?%|\bel mejor\b|\bla mejor\b|\blos mejores\b|\blas mejores\b"
             r"|\bel unico\b|\bla unica\b|\bsin igual\b|\bnumero (?:uno|1)\b|\bimperdible\b|\binigualable\b",
             "guarantee or unproven superlative", "describe what is concrete: what there is, how it feels"),
        Rule("medium", r"\bsiempre disponible\b|\btodo el ano\b|\bsin cargo\b|\bsin costo\b|\bgratis\b|\bgratuit[oa]s?\b",
             "availability or gratuity claim", "confirm the condition with the client, or drop it"),
        Rule("medium", r"\bultimos? (?:lugares|cupos|dias|cabanas|habitaciones)\b|\bquedan pocos\b|\bsolo por hoy\b|\bno te lo pierdas\b"
             r"|\bapurate\b",
             "false urgency", "no pressure: invite instead of rushing"),
        Rule("low", r"\bofertas?\b|\bdescuentos?\b|\bpromos?\b|\bpromocion(?:es)?\b|\b\d+ ?x ?\d+\b|\$ ?\d+|\busd ?\d+|\b\d+ ?% ?off\b"
             r"|\b\d+ ?% de descuento\b|\bprecio especial\b|\b1/2 precio\b|\bmitad de precio\b|\bmedio precio\b",
             "price or offer: needs validity dates and conditions", "add dates and conditions, or remove it", needs_dates=True),
    ],
    "en": [
        Rule("severe", r"\bcur(?:e|es|ed|ing)\b|\bcurative\b|\bheal(?:s|ed|ing|er)?\b",
             "cure or healing claim", HEALTH_EN),
        Rule("severe", r"\btherapeutic\b|\btherapy\b|\bmedicinal\b|\bmedical benefits?\b|\bmiracle\w*|\bmiraculous\b"
             r"|\btreats? (?:your |the )?(?:pain|aches?|arthritis|stress|anxiety|insomnia|skin)\b|\bclinically proven\b",
             "medical or therapeutic claim", 'say "thermal water", "rest"'),
        Rule("severe", r"\brelie(?:f|ve|ves|ving)\b|\balleviat\w*|\bprevents?\b|\b(?:improves?|boosts?) (?:your )?(?:health|immunity|immune system)\b"
             r"|\bpain\b|\baches?\b|\barthritis\b|\brheumat\w*|\bdetox\w*|\bcleans(?:es|ing) your body\b",
             "claim about health or ailments", HEALTH_EN),
        Rule("medium", r"\btreatments?\b",
             "treatment: reads as medical unless it is clearly a spa service", "name the service plainly (massage, bath)"),
        Rule("medium", r"\brejuvenat\w*|\bweight loss\b|\banti-?aging\b",
             "body-effect claim", "describe the experience, not an effect on the body"),
        Rule("medium", r"\bguarantee[ds]?\b|\b100 ?%|\bthe best\b|\bbest in\b|\bthe only\b|\bunmatched\b|\bunbeatable\b|\bunrivall?ed\b"
             r"|\bnumber (?:one|1)\b|#1\b|\bworld-class\b|\bmust-see\b",
             "guarantee or unproven superlative", "describe what is concrete: what there is, how it feels"),
        Rule("medium", r"\balways available\b|\ball year(?: round)?\b|\bfree of charge\b|(?<!feel )(?<!-)\bfree\b(?!-)|\bcomplimentary\b",
             "availability or gratuity claim", "confirm the condition with the client, or drop it"),
        Rule("medium", r"\blast (?:few )?(?:rooms|spots|places|days)\b|\bonly \d+ left\b|\btoday only\b|\bhurry\b|\bdon'?t miss (?:out|it)\b",
             "false urgency", "no pressure: invite instead of rushing"),
        Rule("low", r"\boffers?\b|\bdiscounts?\b|\bdeals?\b|\bsale\b|\bpromo(?:tion)?s?\b|\b\d+ ?% ?off\b|\$ ?\d+|\busd ?\d+|\b\d+ for \d+\b|\bbogo\b"
             r"|\bspecial price\b",
             "price or offer: needs validity dates and conditions", "add dates and conditions, or remove it", needs_dates=True),
    ],
}

MONTHS = {
    "es": r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre",
    "en": r"january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec",
}
# A validity needs a real date: "hasta el 30 de noviembre", "hasta el 30/11", "valido hasta 15/12/2026",
# "del 1 al 15 de diciembre", "until Dec 15", "until 12/15", "through March". Numeric dates are checked
# separately (NUMERIC_DATE + plausible_date), so "hasta el 30%", "14/16 hs", "24/7" and "1/2 precio" do not count.
VALIDITY = {
    "es": r"\b\d{1,2} de (?:%s)\b|\bdel \d{1,2} al \d{1,2}\b|\bhasta (?:el )?(?:%s)\b|\bhasta fin de (?:%s)\b",
    "en": r"\b(?:%s)\.? \d{1,2}(?:st|nd|rd|th)?\b|\b\d{1,2}(?:st|nd|rd|th)? (?:of )?(?:%s)\b"
          r"|\b(?:until|through|thru|till|ends|ending) (?:the end of )?(?:%s)\b",
}
# dd/mm, mm/dd, dd/mm/yyyy, dd.mm.yyyy, dd-mm-yyyy, yyyy-mm-dd ("2-3 noches" and "$ 1.20" are not dates)
NUMERIC_DATE = re.compile(r"(?<![\d/.,$-])(?:(\d{1,2})/(\d{1,2})(?:/(\d{2}|\d{4}))?|(\d{1,2})([.-])(\d{1,2})\5(\d{4})"
                          r"|(\d{4})-(\d{2})-(\d{2}))(?![\d/.,-]\d|\d)(?! ?(?:hs?|hrs?|horas|hours|precio|price|off)\b)(?! ?%)")
SENTENCE_END = re.compile(r"[.!?;…](?=\s|$)|\n")


def plausible_date(m):
    """True when a NUMERIC_DATE match reads as a calendar date (day/month or month/day), not 24/7 or a ratio."""
    if m.group(8):
        return 1 <= int(m.group(9)) <= 12 and 1 <= int(m.group(10)) <= 31
    if m.group(4):
        a, b = int(m.group(4)), int(m.group(6))
    else:
        a, b = int(m.group(1)), int(m.group(2))
        if (a, b) == (24, 7) and not m.group(3):
            return False
    return (1 <= a <= 31 and 1 <= b <= 12) or (1 <= a <= 12 and 1 <= b <= 31)


def rule_set(language):
    lang = (language or "en").lower().replace("_", "-").split("-")[0]
    return (lang if lang in RULES else "en"), RULES.get(lang, RULES["en"])


def normalize(text):
    """(normalized text, index map): lower case, no accents, whitespace collapsed; map[i] = index in `text`."""
    out, idx = [], []
    prev_space = False
    for i, ch in enumerate(text):
        if ch.isspace():
            if prev_space:
                continue
            out.append(" ")
            idx.append(i)
            prev_space = True
            continue
        prev_space = False
        for c in unicodedata.normalize("NFKD", ch):
            if unicodedata.combining(c):
                continue
            for low in c.lower():
                out.append(low)
                idx.append(i)
    return "".join(out), idx


def validity_spans(norm, lang):
    """[(start, end)] in `norm` of every stated validity date."""
    months = MONTHS.get(lang, MONTHS["en"])
    pat = VALIDITY.get(lang, VALIDITY["en"]).replace("%s", months)
    spans = [m.span() for m in re.finditer(pat, norm)]
    spans += [m.span() for m in NUMERIC_DATE.finditer(norm) if plausible_date(m)]
    return spans


def has_validity(norm, lang):
    return bool(validity_spans(norm, lang))


def sentence_of(text):
    """Function: index in `text` → sentence number (sentences end at . ! ? ; … before a space, or a line break)."""
    ends = [m.end() for m in SENTENCE_END.finditer(text)]
    return lambda i: bisect.bisect_right(ends, i)


def check(text, language="es", source=""):
    """Findings for one text, ordered by position."""
    if not text:
        return []
    lang, rules = rule_set(language)
    norm, idx = normalize(text)
    sentence = sentence_of(text)
    # a date only covers the offers in its own sentence
    dated = {sentence(idx[a]) for a, _ in validity_spans(norm, lang)}
    found, spans = [], []
    for rule in rules:
        for m in re.finditer(rule.pattern, norm):
            if m.end() <= m.start():
                continue
            a, b = idx[m.start()], idx[m.end() - 1] + 1
            if rule.needs_dates and sentence(a) in dated:
                continue
            if any(x <= a and b <= y for x, y in spans):  # same text or inside a finding already made
                continue
            spans.append((a, b))
            ctx = " ".join(text[max(0, a - 30):min(len(text), b + 30)].split())
            found.append((a, Finding(rule.severity, text[a:b].strip(), rule.what, rule.suggestion, f"…{ctx}…", source)))
    return [f for _, f in sorted(found, key=lambda x: x[0])]


def summary(findings):
    return {s: sum(1 for f in findings if f.severity == s) for s in SEVERITIES}


def format_finding(f):
    src = f" ({f.source})" if f.source else ""
    return f'{f.severity.upper():6}  {f.what}: "{f.phrase}"{src} {f.context}  → {f.suggestion}'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="files to read, or literal text")
    ap.add_argument("--language", default="es", help="BCP-47 language of the text (es, es-AR, en …); default es")
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    findings = []
    for item in a.inputs:
        if os.path.isfile(item):
            with open(item, encoding="utf-8") as f:
                findings += check(f.read(), a.language, os.path.basename(item))
        else:
            findings += check(item, a.language, "text")
    for f in findings:
        print(format_finding(f))
    n = summary(findings)
    print(f"claims: {n['severe']} severe · {n['medium']} medium · {n['low']} low")
    return 1 if n["severe"] else 0


if __name__ == "__main__":
    sys.exit(main())
