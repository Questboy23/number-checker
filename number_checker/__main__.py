"""python3 -m number_checker ANSWER.txt SOURCE1.txt [SOURCE2.txt ...]
Exit 0 when every number is VERIFIED or DERIVED, 2 when any number is unverified or a sum is broken."""
import sys
from pathlib import Path
from .check import run, report


def main(argv=None):
    a = argv or sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 1
    answer = Path(a[0]).read_text()
    sources = {Path(p).name: Path(p).read_text() for p in a[1:]}
    res = run(answer, sources)
    print(report(res))
    bad = res["broken_sums"] or any(r["status"] not in ("VERIFIED", "DERIVED") for r in res["rows"])
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
