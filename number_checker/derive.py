"""Derivation check: a number with no source line can still be honest if it is arithmetic on
verified numbers (a sum, difference, ratio, or percent change). This reruns that arithmetic in
code, so the model's own math is never trusted.
"""
from itertools import permutations

REL_TOL = 0.01


def _close(a, b):
    return b != 0 and abs(a - b) / abs(b) <= REL_TOL


def derive(claim, verified):
    """verified: list of verified Claim objects. Returns a formula string or None."""
    vals = [(c.value, c.raw) for c in verified if c is not claim]
    t = claim.value
    for (a, ra), (b, rb) in permutations(vals, 2):
        cands = [(a + b, f"{ra} + {rb}"), (a - b, f"{ra} - {rb}"), (a * b, f"{ra} * {rb}")]
        if b:
            cands.append((a / b, f"{ra} / {rb}"))
            cands.append((100 * a / b, f"100 * {ra} / {rb}"))
            cands.append((100 * (a - b) / b, f"percent change {rb} -> {ra}"))
        for v, f in cands:
            if _close(v, t):
                return f
    return None


def broken_sum(claims):
    """Signature 7, broken arithmetic: in one sentence that states a total, the parts should add up.
    Returns (parts_sum, total) when they do not, else None."""
    out = []
    by_sentence = {}
    for c in claims:
        by_sentence.setdefault(c.sentence, []).append(c)
    for s, cs in by_sentence.items():
        if "total" not in s.lower() or len(cs) < 3:
            continue
        units = {c.unit for c in cs}
        if len(units) > 1:
            continue
        vals = [c.value for c in cs]
        total = max(vals)
        parts = sum(vals) - total
        if not _close(parts, total):
            out.append((s, parts, total))
    return out
