"""The full pipeline, run on every number in an AI answer.

1. Extract each number with its entity, year and unit.
2. Exact-line gate: a source line holds the same number with the same binding -> VERIFIED.
3. Derivation: no source line, but it is arithmetic on verified numbers -> DERIVED.
4. Otherwise score the fabrication signatures and combine them in a logistic model.
5. Never show a number bare: VERIFIED, DERIVED, or UNVERIFIED with its score.

The logistic weights below are hand-set placeholders. Step 6 of the design, calibrating them on
questions with known answers, is not done yet.
"""
import math
from . import extract as ex, gate, derive, signatures as sig

WEIGHTS = {"bias": -1.5, "wrong_binding": 3.0, "roundness": 1.2, "false_precision": 1.5,
           "instability": 2.5, "batch_skew": 1.0, "typical_value": 1.5}


def logistic(feats):
    z = WEIGHTS["bias"] + sum(WEIGHTS[k] * v for k, v in feats.items())
    return 1 / (1 + math.exp(-z))


def run(answer, sources, resamples=None, reference=None):
    """answer: AI output text. sources: {name: text}. resamples: optional {claim_raw: [values on reruns]}.
    reference: optional list of real values of the same quantity (for typical-value substitution)."""
    claims = ex.extract(answer)
    rows, verified = [], []
    for c in claims:
        status, ev = gate.check(c, sources)
        rows.append({"claim": c, "status": status, "evidence": ev})
        if status == "VERIFIED":
            verified.append(c)
    batch = sig.excess_small_digit_skew(claims)
    tv = sig.typical_value(claims, reference or [])
    for r in rows:
        c = r["claim"]
        if r["status"] == "VERIFIED":
            continue
        f = derive.derive(c, verified)
        if f:
            r["status"], r["evidence"] = "DERIVED", {"formula": f}
            continue
        feats = {"wrong_binding": 1.0 if r["status"] == "WRONG_BINDING" else 0.0,
                 "roundness": sig.roundness(c),
                 "false_precision": sig.false_precision(c, sources.values()),
                 "instability": sig.instability((resamples or {}).get(c.raw, [])),
                 "batch_skew": batch, "typical_value": tv}
        r["features"], r["score"] = feats, logistic(feats)
        r["status"] = "UNVERIFIED" if r["status"] == "NOT_FOUND" else r["status"]
    return {"rows": rows, "broken_sums": derive.broken_sum(claims), "batch_skew": batch}


def report(result):
    lines = []
    for r in result["rows"]:
        c = r["claim"]
        if r["status"] == "VERIFIED":
            e = r["evidence"]
            lines.append(f"VERIFIED       {c.raw:<16} {e['source']}:{e['line']}  {e['text'][:70]}")
        elif r["status"] == "DERIVED":
            lines.append(f"DERIVED        {c.raw:<16} {r['evidence']['formula']}")
        else:
            why = ""
            if r["status"] == "WRONG_BINDING":
                e = r["evidence"]
                why = f" line {e['source']}:{e['line']} has the number but a different {', '.join(e['problems'])}"
            lines.append(f"{r['status']:<14} {c.raw:<16} p(made up)={r['score']:.2f}{why}")
    for s, parts, total in result["broken_sums"]:
        lines.append(f"BROKEN SUM     parts add to {parts:g}, stated total {total:g}: {s[:70]}")
    return "\n".join(lines)
