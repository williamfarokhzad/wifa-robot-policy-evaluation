"""Build editable SVG from fixture results, then render lossless WebP with Inkscape and Pillow."""
import io
from pathlib import Path
import subprocess
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from evaluate import load_pairs, summarize, wilson95  # noqa: E402


def text(x, y, words, size=24, weight="normal", anchor="start", color="#102641"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{color}">{words}</text>')


def rect(x, y, w, h, fill, radius=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"/>'


def line(x1, y1, x2, y2, color, width):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')


def write(name, body, title):
    svg = HERE / f"{name}.svg"
    svg.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="420" '
        f'viewBox="0 0 760 420" font-family="DejaVu Sans"><title>{title}</title>'
        + rect(0, 0, 760, 420, "#f0f6fc", 0) + "\n".join(body) + "</svg>\n",
        encoding="utf-8",
    )
    png = subprocess.check_output(["inkscape", str(svg), "--export-type=png",
                                   "--export-filename=-"])
    with Image.open(io.BytesIO(png)) as image:
        image.convert("RGB").save(svg.with_suffix(".webp"), lossless=True, method=6)


with (HERE.parent / "examples/dock-pilot.csv").open() as stream:
    _, _, _, cells = summarize(load_pairs(stream))

pair = [text(30, 49, "Same scenario. Two outcomes.", 34, "bold"),
        text(30, 82, "Synthetic docking pilot · 12 matched trials", 23)]
for x, y, key, label, color in (
    (30, 112, (True, True), "Both succeed", "#d9e9f7"),
    (390, 112, (False, True), "Candidate only", "#c9f0e2"),
    (30, 252, (True, False), "Baseline only", "#fae1b9"),
    (390, 252, (False, False), "Neither succeeds", "#d9e9f7"),
):
    pair.extend([rect(x, y, 340, 120, color), text(x+18, y+37, label, 26, "bold"),
                 text(x+18, y+95, str(cells[key]), 46, "bold")])
write("policy-paired-outcomes", pair, "Docking pilot paired outcomes")

chart = [text(30, 48, "Same score. Different precision.", 32, "bold"),
         text(30, 84, "95% Wilson intervals · hypothetical all success runs", 22)]
x = lambda fraction: 245 + 452 * (fraction - .5) / .5
for i in range(6):
    p = .5 + .1 * i
    xx = x(p)
    chart.extend([line(xx, 123, xx, 323, "#c4d4e3", 2),
                  text(xx, 355, f"{p:.0%}", 21, anchor="middle")])
for y, n in ((169, 5), (270, 30)):
    low, high = wilson95(n, n)
    a, b = x(low), x(high)
    chart.extend([text(30, y+7, f"{n}/{n} success", 24, "bold"),
                  line(a, y, b, y, "#146456", 8),
                  line(a, y-11, a, y+11, "#146456", 4),
                  f'<circle cx="{b}" cy="{y}" r="8" fill="#146456"/>',
                  text(a+8, y-20, f"{low:.1%}", 23, "bold")])
chart.append(text(30, 398, "The horizontal scale starts at 50%.", 21))
write("policy-wilson-precision", chart, "Wilson intervals for five and thirty successes")
