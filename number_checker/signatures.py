"""Fabrication signatures: how LLMs make up numbers (idea #12, adapted for AI).

A plain Benford test catches humans who invent data. It cannot catch an LLM, because LLM digits
already follow Benford: the training text does. LLM errors skew toward small leading digits even
further, so the AI signal is skew BEYOND Benford.

Each function returns a value in [0, 1], where higher means more likely made up.
"""
import math
from collections import Counter

BENFORD = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
STOCK_PCTS = {10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90}


def leading_digit(v):
    v = abs(v)
    if v == 0 or math.isinf(v) or math.isnan(v):
        return None
    while v < 1:
        v *= 10
    while v >= 10:
        v /= 10
    return int(v)


def excess_small_digit_skew(claims, min_n=20):
    """Signature 1. Share of leading digits 1-2 above Benford's 47.7%, over a batch of claims.
    Needs 20+ numbers; returns 0 for smaller batches because the test has no power there."""
    ds = [d for d in (leading_digit(c.value) for c in claims) if d]
    if len(ds) < min_n:
        return 0.0
    obs = sum(1 for d in ds if d <= 2) / len(ds)
    exp = BENFORD[1] + BENFORD[2]
    se = math.sqrt(exp * (1 - exp) / len(ds))
    z = (obs - exp) / se
    return max(0.0, min(1.0, z / 3))  # z of 3 or more = full signal


def roundness(claim):
    """Signature 2. Round or anchor values: trailing 0 or 5, stock percentages."""
    if claim.unit == "%" and claim.decimals == 0 and int(claim.value) in STOCK_PCTS:
        return 1.0
    sig = claim.digits.replace(".", "").rstrip("0") or "0"
    if len(sig) == 1:
        return 0.8
    if sig.endswith("5") and len(sig) <= 2:
        return 0.5
    return 0.0


def false_precision(claim, source_texts):
    """Signature 5. Decimals the sources never use: 37.4% when no source writes any decimal."""
    if claim.decimals == 0:
        return 0.0
    src_has_decimals = any("." in tok and tok.replace(".", "").replace(",", "").isdigit()
                           for t in source_texts for tok in t.split())
    return 0.0 if src_has_decimals else min(1.0, 0.5 * claim.decimals)


def instability(samples):
    """Signature 4. The same question asked several times: retrieved numbers stay put, invented
    ones drift. samples = the value the model gave on each rerun. Returns spread / mean, capped."""
    vals = [s for s in samples if s is not None]
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    if mean == 0:
        return 0.0 if len(set(vals)) == 1 else 1.0
    spread = (max(vals) - min(vals)) / abs(mean)
    return min(1.0, spread * 10)  # 10% spread = full signal


def typical_value(claims, ref_values):
    """Signature 3. Typical-value substitution: invented numbers sit too close to the usual value
    and vary too little. ref_values = real values of the same quantity for other items.
    Returns how much tighter the claims cluster than the reference (0 = same spread or wider)."""
    vals = [c.value for c in claims]
    if len(vals) < 3 or len(ref_values) < 3:
        return 0.0
    def cv(xs):
        m = sum(xs) / len(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)) / abs(m) if m else 0.0
    r, c = cv(ref_values), cv(vals)
    return 0.0 if r == 0 or c >= r else min(1.0, 1 - c / r)
