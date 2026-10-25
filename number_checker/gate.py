"""Exact-line gate (idea #1): a number counts as verified only if one line of a cited source
contains the same number AND, on that same line, the same year, the same unit and at least one
of the claim's entity words. Matching the number alone misses wrong binding: a real number that
belongs to a different company, year or unit.
"""
import re
from .extract import NUM, WORD, YEAR, SCALE, STOP, _is_year, norm

REL_TOL = 0.005  # 0.5%: "3.2 billion" matches "3,200,000,000" and "3.20bn"


def _line_numbers(line):
    out = []
    for m in NUM.finditer(line):
        if _is_year(m):
            continue
        v = float(m.group("num").replace(",", ""))
        sc = (m.group("scale") or "").lower()
        if sc in SCALE:
            v *= SCALE[sc]
        unit = "%" if m.group("pct") else (m.group("cur") or "")
        out.append((v, unit))
    return out


def _same(a, b):
    return a == b or (b != 0 and abs(a - b) / abs(b) <= REL_TOL)


def check(claim, sources):
    """sources: {name: text}. Returns (status, evidence).
    status: VERIFIED, WRONG_BINDING (number found, but its line names another year/unit/entity), or NOT_FOUND."""
    best = None
    for name, text in sources.items():
        for i, line in enumerate(text.splitlines(), 1):
            nums = _line_numbers(line)
            hits = [u for v, u in nums if _same(claim.value, v)]
            if not hits:
                continue
            problems = []
            if claim.unit and claim.unit not in hits and "" not in hits:
                problems.append("unit")
            line_years = set(YEAR.findall(line))
            if claim.year and line_years and claim.year not in line_years:
                problems.append("year")
            words = {norm(w) for w in WORD.findall(line) if w.lower() not in STOP}
            if claim.names and not (claim.names & words):
                problems.append("entity")
            elif claim.entity and not (claim.entity & words):
                problems.append("entity")
            ev = {"source": name, "line": i, "text": line.strip(), "problems": problems}
            if not problems:
                return "VERIFIED", ev
            if best is None or len(problems) < len(best["problems"]):
                best = ev
    if best:
        return "WRONG_BINDING", best
    return "NOT_FOUND", None
