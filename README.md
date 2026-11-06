# Robot Policy Evaluation in Python

Compare two frozen policies on the same docking scenarios. The project reads a paired CSV, counts success, failure and timeout separately, and reports Wilson intervals and an exact paired comparison. The [full WIFA Robotics lesson](https://wifarobotics.com/learn/robot-policy-evaluation/) explains the design and calculations.

## Start from zero

1. Install [Python](https://www.python.org/downloads/) 3.11 or newer. On Windows, enable the Python launcher during installation. No pip packages, robot, simulator or GPU are needed to run the project.
2. Download this repository with **Code → Download ZIP**, then extract it.
3. Open a terminal inside the extracted folder. It should contain `evaluate.py` and `examples`. Run:

```sh
python3 --version
python3 evaluate.py examples/dock-pilot.csv
python3 evaluate.py examples/same-score.csv
python3 evaluate.py examples/perfect-five.csv
python3 -m unittest discover -s tests -v
```

On Windows, replace `python3` with `py -3`.

| Fixture | Check |
|---|---|
| `dock-pilot.csv` | 6/12 baseline, 9/12 candidate, four candidate only and one baseline only, +25.0 percentage points, exact paired p = 0.375. |
| `same-score.csv` | Both 6/8, with two wins each on different scenarios. The baseline has two timeouts and the candidate has two failures. |
| `perfect-five.csv` | Both 5/5 with individual 95% Wilson intervals of 56.6% to 100.0%. The program omits the paired p value because there are no discordant pairs. |
| `missing-run.csv` | Running the same command on this file exits 2, names the missing outcome on line 3, and prints no results. |

## Make a trace

Use the header `scenario,baseline,candidate` and one row per independent matched scenario. Start scenario IDs with an ASCII letter or digit. IDs can then also contain dots, underscores and hyphens and must be at most 64 characters. Enter exactly one of `success`, `failure` or `timeout` in each policy column. The lab accepts at most 10,000 rows.

Freeze both policy versions, task criteria, the time budget and the scenario selection before evaluating. For example, define a docking success as reaching the goal with no collision within 100 steps. Save any missing telemetry or infrastructure abort in a separate incident log and resolve it before comparing paired outcomes. A measured timeout is an unsuccessful attempt by that deadline and stays in the denominator. The program cannot detect a scenario missing from both columns, so check the trace against your scenario manifest.

If Python cannot open the file, check the working directory and extracted filename. If the parser rejects a trace, keep the original evidence, then fix the exported copy. Do not replace unknown outcomes with `failure` to make a file pass. A large p value does not establish equivalence. The two Wilson intervals describe the policies individually and do not quantify the difference.

## Diagrams and tests

The `diagrams` folder contains SVG originals and lossless WebP exports. To regenerate them, install Inkscape with its command on PATH and DejaVu Sans, then install Pillow in a virtual environment with `python3 -m pip install Pillow`. Run `python3 -B diagrams/render.py`. These dependencies are only for rendering. Figure alt text and captions are in the lesson.

The tests enumerate all fair coin sequences up to nine discordant pairs to verify the exact result, check the Wilson endpoints against the inverted score equation, and run the CLI with valid and invalid input.

## What was tested

The fixtures are authored synthetic outcome logs. They contain no robot, simulator, field, or hardware measurements. The script evaluates logs; it neither trains a policy nor runs a robot. Related repeats from one map, environment seed family or hardware session may not be independent. The reported intervals and paired p value are not suitable for such clustered logs without a different study design or analysis. This project does not validate motion, timing, safety or deployment readiness.

- [NIST: Wilson score confidence intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
- [NIST Dataplot: McNemar test](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/mcnemar.htm)
- [Farama Foundation: termination and truncation](https://farama.org/Gymnasium-Terminated-Truncated-Step-API)
