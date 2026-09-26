"""Read-only plotting of frozen P2 analysis artifacts."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/common"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "output/q2/matplotlib_cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
from plot_export import save_figure_variants


def arguments(extra=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-run", required=True)
    parser.add_argument("--figure-id", required=True)
    if extra:
        extra(parser)
    return parser.parse_args()


def setup(args):
    if not all(re.fullmatch(r"[A-Za-z0-9_-]+", value) for value in (args.analysis_run, args.figure_id)):
        raise ValueError("Invalid run/figure ID")
    source = ROOT / "output/q2" / args.analysis_run / "plot_data.json"
    report = json.loads(source.with_name("report.json").read_text(encoding="utf-8"))
    item = next(x for x in report["artifacts"] if Path(x["path"]) == source)
    if hashlib.sha256(source.read_bytes()).hexdigest() != item["sha256"]:
        raise ValueError("Plot source changed")
    out = ROOT / "figures/q2" / args.figure_id
    out.mkdir(parents=True, exist_ok=False)
    font_manager.fontManager.addfont("C:/Windows/Fonts/simhei.ttf")
    plt.rcParams.update({"font.family": "SimHei", "axes.unicode_minus": False, "font.size": 10,
                         "text.parse_math": False, "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.facecolor": "white", "figure.facecolor": "white"})
    return json.loads(source.read_text(encoding="utf-8")), out, source


def save(fig, out, name, source, details, script):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = fig.bbox
    clipped = []
    for text in fig.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        box = text.get_window_extent(renderer)
        if box.width > 0 and (box.x0 < bounds.x0 - 1 or box.y0 < bounds.y0 - 1 or box.x1 > bounds.x1 + 1 or box.y1 > bounds.y1 + 1):
            clipped.append(text.get_text())
    if clipped:
        raise ValueError("Text exceeds figure canvas: " + repr(clipped))
    path = out / name
    svg = save_figure_variants(fig, path, dpi=300)
    plt.close(fig)
    metadata = {"source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "script": str(script), "script_sha256": hashlib.sha256(Path(script).read_bytes()).hexdigest(),
                "common_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "image": str(path), "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "svg": str(svg), "svg_sha256": hashlib.sha256(svg.read_bytes()).hexdigest(), "svg_text_editable": True,
                "dpi": 300, "text_outside_canvas": clipped, "details": details}
    with (out / "source.json").open("x", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
    print(path, flush=True)
