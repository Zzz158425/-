"""Replay saved plots and add sibling SVGs only after exact PNG comparison."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SVG_NS = "{http://www.w3.org/2000/svg}"


def record(path):
    path = Path(path)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def copy_verified_companion(original, replay):
    original, replay = Path(original), Path(replay)
    if original.read_bytes() != replay.read_bytes():
        raise ValueError("Replayed PNG differs from historical PNG: " + str(original))
    source, target = replay.with_suffix(".svg"), original.with_suffix(".svg")
    root = ET.parse(source).getroot()
    text_count = len(list(root.iter(SVG_NS + "text")))
    if root.tag != SVG_NS + "svg" or not text_count:
        raise ValueError("Editable SVG required: " + str(source))
    with target.open("xb") as handle:
        handle.write(source.read_bytes())
    return {"png": record(original), "svg": record(target), "replay_png": record(replay),
            "png_byte_identical": True, "editable_text_elements": text_count,
            "embedded_images": len(list(root.iter(SVG_NS + "image")))}


def job_for(directory, pngs):
    area = directory.parent.name
    meta_path = directory / "source.json"
    meta = read_json(meta_path) if meta_path.exists() else {}
    name = pngs[0].name
    if area == "q1":
        inputs = [Path(r["path"]) for r in meta.get("inputs", [])]
        if name == "fig_q1_pipeline.png":
            args = ["--input-run", inputs[0].parent.name]
        elif name == "fig_q1_full_quality.png":
            args = ["--audit-run", inputs[0].parent.name]
        elif name.startswith("fig_q1_alignment_"):
            args = ["--input-run", inputs[0].parents[2].name, "--case", name.split("_")[-1][:-4]]
        elif name == "fig_q1_visual_quality.png":
            args = ["--audit-run", inputs[0].parent.name, "--input-run", inputs[1].parents[2].name]
        elif name == "fig_q1_quality.png":
            args = ["--input-run", Path(meta["input"]).parent.name]
        elif name == "fig_q1_support.png":
            args = ["--input-run", Path(meta["input"]).name]
        else:
            raise ValueError("Unknown Q1 plot: " + name)
        script = "fig_q1_alignment.py" if name.startswith("fig_q1_alignment_") else Path(name).with_suffix(".py").name
        return area, ROOT / "code/figures" / script, args, False
    if area == "q2":
        args = ["--analysis-run", Path(meta["source"]).parent.name]
        if "metric" in meta["details"]:
            args += ["--metric", meta["details"]["metric"]]
        return area, ROOT / "code/figures" / Path(meta["script"]).name, args, False
    if area == "q3":
        if "VALID60" in directory.name:
            run = Path(meta["figures"][0]["sources"][0]["path"]).parent.name
            return area, ROOT / "code/q3/plot_validation.py", ["--analysis-run", run], False
        historic = next(iter(sorted(directory.glob("plot_a4*.py"))), None)
        if historic:
            return area, historic, [], True
        run = Path(meta["source_report"]["path"]).parent.name
        return area, ROOT / "code/q3/plot_a4.py", ["--a4-run", run, "--verification-run", "P3_A4_VERIFY_20260924_001"], False
    raise ValueError("Unknown figure directory: " + str(directory))


def replay_historical(script, output):
    # Execute the preserved layout unchanged; attach an SVG writer only at savefig.
    sys.path.insert(0, str(ROOT / "code/q3"))
    spec = importlib.util.spec_from_file_location("historical_a4_plot", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from matplotlib.figure import Figure
    import matplotlib
    savefig = Figure.savefig

    def save_pair(fig, path, *args, **kwargs):
        path = Path(path)
        for candidate in (path, path.with_suffix(".svg")):
            if candidate.exists():
                raise FileExistsError(candidate)
        savefig(fig, path, *args, **kwargs)
        with matplotlib.rc_context({"svg.fonttype": "none", "svg.hashsalt": "emotion-figures"}):
            savefig(fig, path.with_suffix(".svg"), *args, metadata={"Date": None}, **kwargs)

    output.mkdir(parents=True, exist_ok=False)
    Figure.savefig = save_pair
    try:
        module.render(ROOT / "output/q3/P3_A4_20260924_001", output)
    except ValueError as error:
        if script.name != "plot_a4_failed.py" or "Figure text outside canvas" not in str(error):
            raise
        write_json(output / "historical_stop.json", {"expected_historical_failure": str(error)})
    finally:
        Figure.savefig = savefig


def backfill(audit):
    audit = audit.resolve()
    if not audit.is_relative_to(ROOT / "output/figures"):
        raise ValueError("Audit must stay inside output/figures")
    before = read_json(audit / "figures_before.json")
    for item in before:
        if record(item["path"])["sha256"] != item["sha256"]:
            raise ValueError("Protected original changed: " + item["path"])
    pngs = [Path(row["path"]) for row in before if Path(row["path"]).suffix == ".png"]
    if any(path.with_suffix(".svg").exists() for path in pngs):
        raise FileExistsError("Backfill will not replace existing SVGs")
    groups = {}
    for path in pngs:
        relative = path.relative_to(ROOT / "figures")
        directory = ROOT / "figures" / relative.parts[0] / relative.parts[1]
        groups.setdefault(directory, []).append(path)
    stage = audit / "replays"
    stage.mkdir(exist_ok=False)
    replays, rows, jobs = {}, [], []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    for directory, originals in sorted(groups.items()):
        area, script, args, historical = job_for(directory, originals)
        key = (str(script), tuple(args))
        if key not in replays:
            number = len(replays) + 1
            target = stage / f"{number:02d}_{script.stem}"
            if historical:
                command = [sys.executable, "-X", "utf8", "-B", __file__, "--historical-script", str(script), "--historical-output", str(target)]
                fresh = None
            else:
                figure_id = audit.name + f"_REPLAY_{number:02d}"
                fresh = ROOT / "figures" / area / figure_id
                if fresh.exists():
                    raise FileExistsError(fresh)
                command = [sys.executable, "-X", "utf8", "-B", str(script), *args, "--figure-id", figure_id]
            print("Replay:", script.name, args, flush=True)
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
            write_json(stage / f"{number:02d}_command.json", {"command": command, "returncode": result.returncode,
                       "stdout": result.stdout, "stderr": result.stderr, "script": record(script)})
            if result.returncode:
                raise RuntimeError(result.stderr)
            if fresh:
                # Both resolved paths are checked before moving this newly created directory.
                if not fresh.resolve().is_relative_to(ROOT / "figures") or not target.resolve().is_relative_to(audit):
                    raise ValueError("Replay move escaped its workspace")
                shutil.move(str(fresh), str(target))
            replays[key] = target
            jobs.append({"script": record(script), "args": args, "historical_layout": historical, "replay_directory": str(target)})
        replay_root = replays[key]
        for original in originals:
            rows.append(copy_verified_companion(original, replay_root / original.relative_to(directory)))
        print("Added:", directory.name, len(originals), flush=True)
    unchanged = all(record(row["path"])["sha256"] == row["sha256"] for row in before)
    report = {"accepted": unchanged and len(rows) == len(pngs), "original_png_count": len(pngs),
              "svg_count": len(rows), "all_original_figure_files_unchanged": unchanged,
              "method": "original plot code replay; exact PNG bytes checked; SVG companion only copied",
              "training": False, "inference": False, "jobs": jobs, "figures": rows}
    write_json(audit / "backfill_verification.json", report)
    print(json.dumps({k: v for k, v in report.items() if k not in ("jobs", "figures")}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path)
    parser.add_argument("--historical-script", type=Path)
    parser.add_argument("--historical-output", type=Path)
    args = parser.parse_args()
    if args.historical_script and args.historical_output:
        replay_historical(args.historical_script, args.historical_output)
    elif args.audit_dir:
        backfill(args.audit_dir)
    else:
        parser.error("Supply --audit-dir or both historical replay arguments")


if __name__ == "__main__":
    main()
