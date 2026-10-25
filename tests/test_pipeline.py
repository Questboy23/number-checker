"""Run: python3 -m pytest tests  (or python3 tests/test_pipeline.py)"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from number_checker import run  # noqa: E402
from number_checker.extract import extract  # noqa: E402
from number_checker import signatures as sig  # noqa: E402

SRC = {"10k.txt": "Acme Corp reported revenue of $3,200,000,000 in fiscal 2023.\n"
                  "Acme Corp revenue in fiscal 2022 was $2.9 billion.\n"
                  "Globex revenue in 2023 was $5.1 billion.\n"
                  "Acme employed 12,400 people at the end of 2023.\n"}


def status(res, raw):
    return next(r["status"] for r in res["rows"] if r["claim"].raw == raw)


def test_extract_scale_and_year():
    c = extract("Acme revenue was $3.2 billion in 2023.")
    assert len(c) == 1 and c[0].value == 3.2e9 and c[0].unit == "$" and c[0].year == "2023"
    assert "acme" in c[0].entity and "revenue" in c[0].entity


def test_exact_line_verifies_across_formats():
    res = run("Acme revenue was $3.2 billion in 2023.", SRC)
    assert status(res, "$3.2 billion") == "VERIFIED"


def test_wrong_year_is_wrong_binding():
    res = run("Acme revenue was $2.9 billion in 2023.", SRC)  # 2.9bn is Acme's 2022 number
    assert status(res, "$2.9 billion") == "WRONG_BINDING"


def test_wrong_entity_is_wrong_binding():
    res = run("Initech revenue was $5.1 billion in 2023.", SRC)  # 5.1bn belongs to Globex
    assert status(res, "$5.1 billion") == "WRONG_BINDING"


def test_derived_percent_change():
    ans = "Acme revenue was $3.2 billion in 2023, up from $2.9 billion in 2022, growth of 10.3%."
    res = run(ans, SRC)
    assert status(res, "10.3%") == "DERIVED"


def test_made_up_number_unverified_and_scored():
    res = run("Acme revenue grew 40% in 2023.", SRC)
    r = next(r for r in res["rows"] if r["claim"].raw == "40%")
    assert r["status"] == "UNVERIFIED" and r["features"]["roundness"] == 1.0 and r["score"] > 0.4


def test_broken_sum():
    res = run("Revenue was $2 billion from cloud and $1 billion from ads, a total of $4 billion.", {})
    assert res["broken_sums"]


def test_instability_signal():
    assert sig.instability([31.0, 31.0, 31.0]) == 0.0
    assert sig.instability([31.0, 44.0, 27.0]) == 1.0


def test_benford_like_batch_does_not_fire_but_excess_skew_does():
    rnd = random.Random(0)
    benford = [10 ** rnd.uniform(0, 6) for _ in range(500)]  # log-uniform = Benford
    ans = " ".join(f"Item {i} cost {v:.0f} units." for i, v in enumerate(benford))
    assert sig.excess_small_digit_skew(extract(ans)) < 0.34
    skewed = [rnd.choice([1, 1, 1, 2, 2, 3]) * 10 ** rnd.randint(0, 5) + rnd.randint(0, 9) for _ in range(500)]
    ans2 = " ".join(f"Item {i} cost {v} units." for i, v in enumerate(skewed))
    assert sig.excess_small_digit_skew(extract(ans2)) == 1.0


if __name__ == "__main__":
    fails = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            try:
                f(); print("PASS", k)
            except AssertionError as e:
                fails += 1; print("FAIL", k, e)
    sys.exit(1 if fails else 0)
