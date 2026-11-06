# Number Checker: labels every number in an AI answer as verified, derived, wrongly bound or unverified against the cited source.

**Work in progress: 9 of 9 tests pass, and the made-up-number score is not calibrated yet.**

A Python tool that labels every number in an AI answer as verified, derived, wrongly bound or unverified against the cited source lines.

**Status: work in progress.** The pipeline runs end to end and passes its 9 tests. The fabrication-score weights are hand-set placeholders, because the calibration step is not done.

## AI disclosure

Reed Ostrov supplied the ideas: an exact-line citation gate and a detector for made-up numbers. Claude Code (Anthropic) wrote the code, the tests and this README at his direction. The AI did not originate the ideas. The code has no independent audit.

## Labels

| Label | Meaning |
|---|---|
| `VERIFIED` | One line of a cited source holds the same number, with the same year, unit and entity |
| `DERIVED` | No source line holds it, but code reproduces it from verified numbers (sum, difference, ratio, percent change) within 1% |
| `WRONG_BINDING` | The number is in the source, but its line is about a different year, unit or entity |
| `UNVERIFIED` | Nothing supports it. Comes with p(made up) from the fabrication signatures |

## Run

Standard library only, Python 3.

```bash
git clone https://github.com/Questboy23/number-checker && cd number-checker && python3 -m number_checker examples/answer.txt examples/source.txt
```

Output on the bundled example (recomputed 2026-11-06):

```
VERIFIED       $3.2 billion     source.txt:1  Acme Corp reported revenue of $3,200,000,000 in fiscal 2023.
VERIFIED       $2.9 billion     source.txt:2  Acme Corp revenue in fiscal 2022 was $2.9 billion.
DERIVED        10.3%            percent change $2.9 billion -> $3.2 billion
VERIFIED       12,400           source.txt:4  Acme employed 12,400 people at the end of 2023.
WRONG_BINDING  $5.1 billion     p(made up)=0.82 line source.txt:3 has the number but a different entity
UNVERIFIED     30%              p(made up)=0.43
UNVERIFIED     17.4%            p(made up)=0.18
```

Tests: `python3 tests/test_pipeline.py` (9 pass).

## How it works

1. **Extract.** Each number is pulled out with its unit, nearest year and the words around it.
2. **Exact-line gate.** A source line must hold the same number (3.2 billion matches 3,200,000,000) and name the same year, unit and entity.
3. **Derivation check.** Pairs of verified numbers are combined in code. One combination within 1% of the claim makes it derived.
4. **Fabrication score.** Remaining numbers are scored by a logistic model over six signals: excess small-leading-digit skew beyond Benford (needs 20+ numbers), round or anchor values, false precision, instability across reruns, typical-value substitution, and wrong binding.
5. **Broken sums.** In a sentence that states a total, the parts must add up.

## Limitations

- The p(made up) weights are hand-set. They are not fitted to labeled data, so read p(made up) as a ranking and not as a probability.
- The hypothesis that LLM errors skew toward leading digits 1 and 2 beyond Benford's law is not tested here. The skew signal has no measured hit rate.
- Reruns: `instability` needs the model asked the same question several times. No model caller is included.
- Reference values: `typical_value` needs real values of the same quantity. None are bundled.
- Entity extraction uses nearby words and capitalized names. It can bind the wrong entity in long sentences.
- No benchmark on a real legal, tax or financial question set. The only test data are 4 hand-written example lines.
- Prior art: semantic entropy (Farquhar et al. 2024), the Benford digit-bias literature and citation benchmarks such as ALCE. The source gate and the entity, year and unit binding on the cited line are the parts not taken from them. This is the author's claim and was not checked against a literature search.
