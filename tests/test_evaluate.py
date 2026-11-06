from fractions import Fraction
import io
from itertools import product
from pathlib import Path
import subprocess
import sys
import unittest

from evaluate import Pair, Z95, exact_p, format_report, load_pairs, summarize, wilson95

ROOT = Path(__file__).resolve().parents[1]


class EvaluationTests(unittest.TestCase):
    def test_pair_table_and_timeout_accounting(self):
        with (ROOT / "examples/dock-pilot.csv").open() as stream:
            n, baseline, candidate, cells = summarize(load_pairs(stream))
        self.assertEqual((n, baseline["timeout"], candidate["timeout"]), (12, 3, 1))
        self.assertEqual(tuple(cells[key] for key in product((True, False), repeat=2)),
                         (5, 1, 4, 2))
        self.assertEqual(candidate["success"] - baseline["success"], 3)

    def test_exact_tail_against_enumerated_fair_coin_outcomes(self):
        for n in range(1, 10):
            deviations = [abs(2 * sum(seq) - n) for seq in product((0, 1), repeat=n)]
            for b in range(n + 1):
                tail = sum(d >= abs(2 * b - n) for d in deviations)
                self.assertEqual(exact_p(b, n-b), Fraction(tail, 2**n))

    def test_wilson_endpoints_invert_score_statistic(self):
        for n, k in ((5, 1), (12, 9), (50, 1), (100, 50), (100, 99)):
            low, high = wilson95(k, n)
            self.assertLess(low, k/n)
            self.assertGreater(high, k/n)
            for p in (low, high):
                self.assertAlmostEqual(abs(k - n*p) / (n*p*(1-p))**0.5, Z95, places=10)

    def test_all_success_closed_form_and_all_failure_symmetry(self):
        self.assertEqual(wilson95(5, 5)[1], 1.0)
        self.assertEqual(wilson95(0, 5)[0], 0.0)
        self.assertAlmostEqual(wilson95(5, 5)[0], 5 / (5 + Z95**2))
        self.assertAlmostEqual(wilson95(0, 5)[1], 1 - wilson95(5, 5)[0])

    def test_direction_and_equal_margins(self):
        rows = [Pair("a", "success", "timeout"), Pair("b", "failure", "success")]
        self.assertIn("baseline only 1; candidate only 1", format_report(rows))
        self.assertIn("Exact paired p: 1", format_report(rows))
        self.assertEqual(exact_p(1, 4), exact_p(4, 1))
        self.assertIsNone(exact_p(0, 0))

    def test_missing_duplicate_unrecognized_and_malformed_rows(self):
        head = "scenario,baseline,candidate\n"
        for body in ("", "a,success,\n", "a,pass,success\n",
                     "a,success,success\na,failure,success\n",
                     "a,success,success,timeout\n", "bad id,success,success\n"):
            with self.subTest(body=body), self.assertRaises(ValueError):
                load_pairs(io.StringIO(head + body))
        with self.assertRaises(ValueError):
            load_pairs(io.StringIO("run,a,b\nx,success,success\n"))

    def test_extreme_tail_keeps_exact_value(self):
        p = exact_p(0, 10_000)
        self.assertEqual(p, Fraction(1, 2**9999))
        self.assertGreater(p, 0)

    def test_cli_examples(self):
        for name, expected in [
            ("dock-pilot", "Exact paired p: 0.375"),
            ("same-score", "baseline only 2; candidate only 2"),
            ("perfect-five", "Wilson 95% [56.6%, 100.0%]"),
        ]:
            with self.subTest(name=name):
                result = subprocess.run([sys.executable, "evaluate.py", f"examples/{name}.csv"],
                                        cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, result.stdout)
        bad = subprocess.run([sys.executable, "evaluate.py", "examples/missing-run.csv"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(bad.stdout, "")
        self.assertIn("line 3", bad.stderr)


if __name__ == "__main__":
    unittest.main()
