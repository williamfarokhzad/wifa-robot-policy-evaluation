"""Compare two frozen robot policies on one outcome per independent scenario."""
import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from math import sqrt
from pathlib import Path
import re

HEADER = ["scenario", "baseline", "candidate"]
OUTCOMES = ("success", "failure", "timeout")
Z95 = 1.959963984540054
MAX_PAIRS = 10_000


@dataclass(frozen=True)
class Pair:
    scenario: str
    baseline: str
    candidate: str


def load_pairs(stream):
    reader = csv.reader(stream, strict=True)
    if next(reader, None) != HEADER:
        raise ValueError("header must be scenario,baseline,candidate")
    pairs, seen = [], set()
    for row in reader:
        line = reader.line_num
        if len(row) != 3:
            raise ValueError(f"line {line}: expected three columns")
        scenario, baseline, candidate = row
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", scenario):
            raise ValueError(f"line {line}: invalid scenario ID")
        if scenario in seen:
            raise ValueError(f"line {line}: duplicate scenario {scenario}")
        if any(outcome not in OUTCOMES for outcome in (baseline, candidate)):
            raise ValueError(f"line {line}: each policy needs success, failure or timeout")
        if len(pairs) == MAX_PAIRS:
            raise ValueError(f"limit is {MAX_PAIRS} paired scenarios")
        seen.add(scenario)
        pairs.append(Pair(scenario, baseline, candidate))
    if not pairs:
        raise ValueError("no paired scenarios")
    return pairs


def wilson95(successes, total):
    """Return the two-sided Wilson score interval for one proportion."""
    if not 0 <= successes <= total or total < 1:
        raise ValueError("expected 0 <= successes <= total and total >= 1")
    p = successes / total
    a = Z95 ** 2 / total
    center = (p + a / 2) / (1 + a)
    half = Z95 * sqrt(p * (1 - p) / total + a / (4 * total)) / (1 + a)
    return (0.0 if successes == 0 else center - half,
            1.0 if successes == total else center + half)


def exact_p(baseline_only, candidate_only):
    """Two-sided conditional binomial tail over discordant pairs."""
    if baseline_only < 0 or candidate_only < 0:
        raise ValueError("pair counts cannot be negative")
    n = baseline_only + candidate_only
    if not n:
        return None
    k = min(baseline_only, candidate_only)
    term = tail = 1
    for i in range(1, k + 1):
        term = term * (n - i + 1) // i
        tail += term
    denominator = 1 << n
    return Fraction(min(2 * tail, denominator), denominator)


def summarize(pairs):
    baseline, candidate, cells = Counter(), Counter(), Counter()
    for pair in pairs:
        baseline[pair.baseline] += 1
        candidate[pair.candidate] += 1
        cells[(pair.baseline == "success", pair.candidate == "success")] += 1
    n = baseline.total()
    if not n:
        raise ValueError("no paired scenarios")
    return n, baseline, candidate, cells


def format_report(pairs):
    n, baseline, candidate, cells = summarize(pairs)
    lines = [f"Paired scenarios: {n}"]
    for label, counts in (("Baseline", baseline), ("Candidate", candidate)):
        k = counts["success"]
        low, high = wilson95(k, n)
        lines.append(
            f"{label}: {k}/{n} success ({k/n:.1%}); {counts['failure']} failure; "
            f"{counts['timeout']} timeout; Wilson 95% [{low:.1%}, {high:.1%}]"
        )
    both, b, c, neither = (cells[key] for key in ((True, True), (True, False),
                                                   (False, True), (False, False)))
    lines.append(f"Pairs: both {both}; baseline only {b}; candidate only {c}; neither {neither}")
    lines.append(f"Candidate minus baseline: {100 * (c - b) / n:+.1f} percentage points")
    p = exact_p(b, c)
    if p is None:
        lines.append("Exact paired p: not reported (no discordant pairs)")
    else:
        with localcontext() as context:
            context.prec = 16
            lines.append(f"Exact paired p: {Decimal(p.numerator) / Decimal(p.denominator):.6g}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path, help="scenario,baseline,candidate CSV")
    args = parser.parse_args(argv)
    try:
        with args.csv_path.open(encoding="utf-8-sig", newline="") as stream:
            report = format_report(load_pairs(stream))
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        parser.error(str(exc))
    print(report)


if __name__ == "__main__":
    main()
