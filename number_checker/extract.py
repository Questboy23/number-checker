"""Pull every number out of a piece of AI output, with what it claims to be about.

Each number becomes a Claim: the value, its unit, the year it names, the words around it
(the entity it is bound to), and the sentence it came from.
"""
import re
from dataclasses import dataclass, field

SCALE = {"thousand": 1e3, "k": 1e3, "million": 1e6, "m": 1e6, "mn": 1e6,
         "billion": 1e9, "bn": 1e9, "b": 1e9, "trillion": 1e12, "tn": 1e12, "t": 1e12}
STOP = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or", "by", "with", "from",
        "is", "was", "were", "are", "be", "been", "it", "its", "this", "that", "than", "as", "about",
        "around", "roughly", "approximately", "nearly", "over", "under", "per", "percent", "year",
        "million", "billion", "thousand", "trillion", "which", "who", "has", "had", "have"}

NUM = re.compile(
    r"(?P<cur>[$€£])?\s?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?:\s?(?P<scale>thousand|million|billion|trillion|bn|mn|tn|[kKmMbBtT])\b)?"
    r"\s?(?P<pct>%|percent\b|per cent\b)?")
YEAR = re.compile(r"\b(1[89]\d{2}|20\d{2})\b")
WORD = re.compile(r"[A-Za-z][A-Za-z\-'\u2019]+")


@dataclass
class Claim:
    raw: str            # the text as written, e.g. "$3.2 billion"
    value: float        # 3.2e9
    digits: str         # significant digits as written, e.g. "3.2"
    decimals: int       # decimals as written (false-precision signal)
    unit: str           # "%", "$", "€", "£" or ""
    year: str | None    # a year named in the same sentence, if any
    entity: set = field(default_factory=set)  # content words near the number
    names: set = field(default_factory=set)   # capitalized words near the number (company, person, place)
    sentence: str = ""
    start: int = 0


def sentences(text):
    """Split on . ! ? followed by whitespace or the end, and on newlines. A period inside a
    number (3.2) is not followed by whitespace, so it never splits."""
    out, start = [], 0
    for m in re.finditer(r"[.!?]+(?=\s|$)|\n", text):
        s = text[start:m.end()]
        if s.strip():
            out.append((start, s))
        start = m.end()
    if text[start:].strip():
        out.append((start, text[start:]))
    return out


def _is_year(m):
    return (m.group("cur") is None and m.group("pct") is None and m.group("scale") is None
            and "," not in m.group("num") and "." not in m.group("num")
            and YEAR.fullmatch(m.group("num")) is not None)


def norm(w):
    """Lowercase and drop a possessive: "Acme's" and "Acme" are the same entity."""
    w = w.lower().replace("\u2019", "'")
    return w[:-2] if w.endswith("'s") else w


def entity_words(s, lo, hi, width=6):
    """Content words within `width` words either side of the number, plus the capitalized ones."""
    left = WORD.findall(s[:lo])[-width:]
    right = WORD.findall(s[hi:])[:width]
    near = [w for w in left + right if w.lower() not in STOP and len(w) > 2]
    return {norm(w) for w in near}, {norm(w) for w in near if w[0].isupper()}


def nearest_year(s, lo, hi):
    """The year closest to the number, measured gap to gap ("$2.9bn in 2022" binds 2022)."""
    ys = [((lo - m.end()) if m.end() <= lo else (m.start() - hi), m.group(0)) for m in YEAR.finditer(s)]
    return min(ys)[1] if ys else None


def extract(text):
    claims = []
    for off, s in sentences(text):
        for m in NUM.finditer(s):
            if _is_year(m):
                continue
            num = m.group("num")
            # skip list markers like "1." at a line start and citation markers like [3]
            before = s[:m.start()].rstrip()
            if before.endswith("[") or (not before and s[m.end():m.end() + 1] == "."):
                continue
            v = float(num.replace(",", ""))
            sc = (m.group("scale") or "").lower()
            if sc in SCALE:
                v *= SCALE[sc]
            unit = "%" if m.group("pct") else (m.group("cur") or "")
            dec = len(num.split(".")[1]) if "." in num else 0
            ent, names = entity_words(s, m.start(), m.end())
            claims.append(Claim(raw=m.group(0).strip(), value=v, digits=num.replace(",", ""),
                                decimals=dec, unit=unit, year=nearest_year(s, m.start(), m.end()),
                                entity=ent, names=names, sentence=s.strip(), start=off + m.start()))
    return claims
