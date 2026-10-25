# number-checker

**Status: work in progress.** The pipeline runs end to end and passes its 9 tests. The fabrication-score weights are hand-set placeholders, because the calibration step (below) is not done yet.

Every number in an AI answer gets one of four labels, so none is ever shown bare:

| Label | Meaning |
|---|---|
| `VERIFIED` | One line of a cited source holds the same number, with the same year, unit and entity |
| `DERIVED` | No source line holds it, but code reproduces it from verified numbers (sum, difference, ratio, percent change) |
| `WRONG_BINDING` | The number is real, but its source line is about a different year, unit or entity |
| `UNVERIFIED` | Nothing supports it. Comes with p(made up) from the fabrication signatures |

```
$ python3 -m number_checker examples/answer.txt examples/source.txt
VERIFIED       $3.2 billion     source.txt:1  Acme Corp reported revenue of $3,200,000,000 in fiscal 2023.
VERIFIED       $2.9 billion     source.txt:2  Acme Corp revenue in fiscal 2022 was $2.9 billion.
DERIVED        10.3%            percent change $2.9 billion -> $3.2 billion
WRONG_BINDING  $5.1 billion     p(made up)=0.82 line source.txt:3 has the number but a different entity
UNVERIFIED     30%              p(made up)=0.43
```

## How it works

1. **Extract.** Each number is pulled out with its unit, its closest year, and the words around it (the entity it claims to describe).
2. **Exact-line gate.** A source line must hold the same number (3.2 billion matches 3,200,000,000) and also name the same year, unit and entity. A number-only search misses wrong binding, which is the most common way a real-looking number is wrong.
3. **Derivation check.** Pairs of verified numbers are combined in code. If one combination reproduces the claim within 1%, it is derived. The model's own arithmetic is never trusted.
4. **Fabrication score.** Everything left is scored on how LLMs invent numbers, and a logistic model combines the signals:
   - **Excess small-digit skew.** LLM digits already follow Benford's law because their training text does. A plain Benford test therefore cannot catch them. Their errors lean even further toward leading 1s and 2s, so the signal is skew beyond Benford.
   - **Round or anchor values,** such as 30%, 50% or a single significant digit.
   - **False precision,** such as 37.4% when no source uses decimals.
   - **Instability across reruns.** Numbers read from a source stay fixed, while invented ones drift. This is the idea behind semantic entropy (Farquhar et al. 2024).
   - **Typical-value substitution.** Invented values cluster too tightly around the usual value for that quantity.
   - **Wrong binding,** carried over from the gate.
5. **Broken sums.** In a sentence that states a total, the parts must add up.

## Not done yet

- **Calibration.** Build a set of questions with known answers, and run each with and without sources. Label which numbers were made up, then fit the weights. Until then, treat p(made up) as a ranking only.
- **Reruns.** `instability` needs the model asked the same question several times. The scorer accepts those values, but no model caller is built in.
- **Reference values.** `typical_value` needs real values of the same quantity, and none are bundled.
- **Entity extraction** comes from nearby words and capitalized names. An LLM extractor would bind entities better on long sentences.
- **Benchmark.** No numbers yet on a real legal, tax or financial question set.

## Prior art and the original part

- **Already exists:** semantic entropy, the "Benford's Curse" finding on LLM digit bias, and citation benchmarks such as ALCE, which grade citations after the answer is written.
- **Original here:** a hard source gate that removes a number before the user sees it, entity, year and unit binding on the cited line, and a fabrication fingerprint aimed at how LLMs specifically invent numbers.

## Test

```bash
python3 tests/test_pipeline.py
```

Reed Ostrov, Denison University. Built out of ideas #1 (exact-line citation gate) and #12 (made-up-number detection).
