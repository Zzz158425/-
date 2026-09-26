"""All registered cells and stability diagnostics from frozen P3 outputs."""
import argparse
import os
from pathlib import Path

from p3_support import ROOT, existing_run, read_json, record, write_json

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "output/q3/matplotlib_cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from plot_export import save_figure_variants


def render(analysis, output):
    summary_path = analysis / "faithfulness_summary.json"
    report_path = analysis / "report.json"
    summary, report = read_json(summary_path), read_json(report_path)
    for path in (summary_path, analysis / "stability.json"):
        expected = next(item for item in report["artifacts"] if item["path"] == str(path.resolve()))
        if record(path) != expected:
            raise ValueError("Frozen plot source changed")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.facecolor": "white", "figure.facecolor": "white"})
    outputs = []

    def save(fig, name, sources):
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bounds = fig.bbox
        for text in fig.findobj(matplotlib.text.Text):
            if text.get_visible() and text.get_text().strip():
                box = text.get_window_extent(renderer)
                if box.width > 0 and (box.x0 < bounds.x0 - 1 or box.y0 < bounds.y0 - 1 or box.x1 > bounds.x1 + 1 or box.y1 > bounds.y1 + 1):
                    raise ValueError("Text outside canvas: " + text.get_text())
        path = output / name
        svg = save_figure_variants(fig, path, dpi=300)
        plt.close(fig)
        outputs.append({"image": record(path), "svg": record(svg), "svg_text_editable": True, "dpi": 300, "text_outside_canvas": [],
                        "sources": [record(p) for p in sources]})

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.2))
    fig.subplots_adjust(left=.085, right=.98, top=.83, bottom=.16, hspace=.56, wspace=.30)
    fig.suptitle("P3 | Key-block fidelity on 60 frozen validation clips", x=.085, y=.965, ha="left", fontsize=16)
    fig.text(.085, .91, "Matched random blocks; fixed original targets; 5,000 video-group bootstrap draws (54 videos).", fontsize=10)
    for ax, (head, ratio) in zip(axes.flat, [(h, r) for h in ("classification", "regression") for r in (.2, .5)], strict=True):
        for baseline, color, shift, marker in (("mean", "#007F83", -.09, "o"), ("median", "#C65C49", .09, "s")):
            rows = [next(s for s in summary if s["head"] == head and s["ratio"] == ratio and s["baseline"] == baseline and s["modality"] == m)
                    for m in ("T", "A", "V", "all")]
            means = np.asarray([r["mean"] for r in rows])
            intervals = np.asarray([r["mean_CI95"] for r in rows])
            ax.errorbar(np.arange(4) + shift, means, yerr=np.stack((means - intervals[:, 0], intervals[:, 1] - means)),
                        fmt=marker, markersize=5, capsize=4, color=color, label=baseline.capitalize() + " reference")
        ax.axhline(0, color="#636363", linewidth=.8)
        ax.set_xticks(range(4), ["Text", "Audio", "Vision", "Clip average"])
        ax.set_xlim(-.45, 3.5)
        ax.set_title(("Class logit" if head == "classification" else "Intensity magnitude") + f" | {int(100 * ratio)}% block", loc="left", fontsize=11)
        ax.set_ylabel("Top minus random effect")
        ax.grid(axis="y", color="#E3E3E3", linewidth=.5)
        ax.set_axisbelow(True)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower left", bbox_to_anchor=(.077, .058), ncol=2, frameon=False)
    fig.text(.085, .028, "Feature replacement + missing mask, not causal word deletion. Intervals are descriptive, without multiplicity correction.", fontsize=9)
    save(fig, "p3_fidelity.png", [summary_path, report_path])

    stable = read_json(analysis / "stability.json")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    fig.subplots_adjust(left=.10, right=.98, top=.78, bottom=.24)
    fig.suptitle("P3 | Stability and modality-removal agreement", x=.10, y=.96, ha="left", fontsize=15)
    fig.text(.10, .865, "All 60 clips retained. Whole-modality removal is a possibly out-of-distribution diagnostic.", fontsize=10)
    for head, color, offset in (("classification", "#007F83", -.17), ("regression", "#C65C49", .17)):
        item = next(s for s in stable["summary"] if s["head"] == head)
        whole = next(s for s in report["whole_primary_agreement"] if s["head"] == head and s["baseline"] == "mean")
        vals = np.asarray([item["exact_primary_rate"], item["exact_window_rate"], whole["rate"]]) * 100
        bars = ax.bar(np.arange(3) + offset, vals, width=.30, color=color, label=head.capitalize())
        ax.bar_label(bars, labels=[f"{v:.1f}%" for v in vals], padding=4, fontsize=10)
    ax.set_xticks(range(3), ["Mean/median\nprimary modality", "Mean/median\nexact key block", "IG / whole removal\nprimary modality"])
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Exact agreement (%)")
    ax.grid(axis="y", color="#E3E3E3", linewidth=.5)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", bbox_to_anchor=(-.01, -.38), ncol=2, frameon=False)
    fig.text(.10, .018, "Agreement is not prediction accuracy. Individual counterexamples are retained in the analysis artifacts.", fontsize=9)
    save(fig, "p3_stability.png", [analysis / "stability.json", report_path])
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-run", required=True)
    parser.add_argument("--figure-id", required=True)
    args = parser.parse_args()
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.figure_id):
        raise ValueError("Invalid figure ID")
    output = ROOT / "figures/q3" / args.figure_id
    output.mkdir(parents=True, exist_ok=False)
    rows = render(existing_run(args.analysis_run), output)
    write_json(output / "source.json", {"code": record(__file__), "figures": rows, "training": False})
    print(output, flush=True)


if __name__ == "__main__":
    main()
