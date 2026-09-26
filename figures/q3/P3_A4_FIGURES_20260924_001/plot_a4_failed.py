"""Twenty auditable feature-only cards and three frozen-rule summary figures."""
import argparse
import json
import os
from pathlib import Path
import re
import textwrap

from p3_support import ROOT, existing_run, read_json, record, write_json

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "output/q3/matplotlib_cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import numpy as np

NAMES = ("T", "A", "V")
POSITIVE, NEGATIVE = "#007F83", "#C65C49"
MODALITY_COLORS = ("#4477AA", "#DDAA33", "#CC6677")
CMAP = LinearSegmentedColormap.from_list("p3_signed", [NEGATIVE, "#FFFFFF", POSITIVE])
ROLES = {"stable_dominance": "Concentrated primary modality", "modality_disagreement": "Modality disagreement", "input_quality_limit": "Input-quality limitation"}


def wrapped(text, width):
    return "\n".join(textwrap.fill(line, width=width, break_long_words=True, break_on_hyphens=False) for line in text.splitlines())


def short_flags(sample, evidence):
    issues = []
    if sample["text_truncated"]:
        issues.append(f"truncated: {len(sample['omitted_word_indices'])} omitted words")
    if any(sample["all_content_zero_AV"].values()):
        issues.append("all-zero visual input remains ambiguous")
    sensitive = ["class" if h == "classification" else "intensity" for h, v in sample["heads"].items() if v["baseline_sensitive"]]
    if sensitive:
        issues.append("reference-sensitive primary: " + "/".join(sensitive))
    if sample["class_regression_sign_conflict"]:
        issues.append("class/intensity sign conflict")
    selected = [e for e in evidence if e["sample_id"] == sample["sample_id"] and e["baseline"] == "mean"]
    issues.append(f"top <= random: {sum('local_nonpositive_margin' in e['quality_flags'] for e in selected)}/12 blocks")
    issues.append(f"opposite direction: {sum('local_opposite_direction' in e['quality_flags'] for e in selected)}/12 blocks")
    return "; ".join(issues)


def draw_contributions(ax, sample, head, compact=False):
    h = sample["heads"][head]
    values, shares = np.asarray(h["signed_mean"]), np.asarray(h["share_mean"])
    extent = max(float(np.max(abs(values))), .001)
    y = np.arange(3)
    ax.barh(y, values, height=.5, color=[POSITIVE if v >= 0 else NEGATIVE for v in values])
    ax.axvline(0, color="#666666", linewidth=.7)
    ax.set_yticks(y, ["Text", "Audio", "Vision"])
    ax.invert_yaxis()
    ax.set_xlim(-1.75 * extent, 1.75 * extent)
    for j, (value, share) in enumerate(zip(values, shares, strict=True)):
        ax.text(value + np.sign(value or 1) * .03 * extent, j,
                f"{value:+.3f} ({100*share:.1f}%)", va="center", ha="left" if value >= 0 else "right", fontsize=8 if compact else 9)
    ax.set_xlabel("Signed IG (absolute net share)", fontsize=8 if compact else 9)
    title = "Original-class logit" if head == "classification" else "Signed intensity"
    primary = "/".join(h["primary_mean"] or ["undefined"])
    ax.set_title(title + " | primary: " + primary, loc="left", fontsize=10 if compact else 11)
    ax.grid(axis="x", color="#E7E7E7", linewidth=.5)
    ax.set_axisbelow(True)


def draw_local(ax, sample, cases, evidence):
    sid, length = sample["sample_id"], sample["content_length"]
    rows = []
    selected = []
    for head in ("classification", "regression"):
        case = next(r for r in cases if r["sample_id"] == sid and r["baseline"] == "mean" and r["head"] == head and r["selected_attempt"])
        for m in range(3):
            signed = np.asarray(case["result"]["summary"]["slot_signed"][m][0])[1:length+1]
            denominator = max(float(np.max(abs(signed))), 1e-12)
            rows.append(signed / denominator)
            selected.append(next(e for e in evidence if e["sample_id"] == sid and e["baseline"] == "mean" and e["head"] == head and e["modality"] == NAMES[m] and e["requested_ratio"] == .2))
    image = ax.imshow(np.asarray(rows), cmap=CMAP, vmin=-1, vmax=1, aspect="auto", interpolation="nearest",
                      extent=(.5, length+.5, 5.5, -.5))
    for j, e in enumerate(selected):
        ax.add_patch(Rectangle((e["feature_index_start"]-.5, j-.5), e["feature_index_end"]-e["feature_index_start"], 1,
                              fill=False, edgecolor="#242424", linewidth=1.1))
    ax.set_yticks(range(6), ["Class T", "Class A", "Class V", "Intensity T", "Intensity A", "Intensity V"])
    ticks = sorted(set([1, *range(5,length+1,5), length]))
    ax.set_xticks(ticks)
    ax.set_xlabel("Original feature index, not time | black boxes: 20% key blocks", fontsize=9)
    ax.tick_params(labelsize=8)
    return image


def render(run, output):
    report = read_json(run / "report.json")
    samples = read_json(run / "samples.json")
    selection = read_json(run / "card_selection.json")["selected"]
    evidence = [json.loads(line) for line in (run / "evidence_map.jsonl").read_text(encoding="utf-8").splitlines()]
    for item in report["artifacts"]:
        if record(item["path"]) != item:
            raise ValueError("Frozen A4 output changed: " + item["path"])
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.facecolor": "white", "figure.facecolor": "white", "text.parse_math": False})
    artifacts = []
    cards = output / "explanation_cards"
    cards.mkdir()

    def save(fig, path, detail):
        fig.canvas.draw()
        renderer, bounds = fig.canvas.get_renderer(), fig.bbox
        overflow = []
        for text in fig.findobj(matplotlib.text.Text):
            if text.get_visible() and text.get_text().strip():
                box = text.get_window_extent(renderer)
                if box.width > 0 and (box.x0 < bounds.x0-1 or box.y0 < bounds.y0-1 or box.x1 > bounds.x1+1 or box.y1 > bounds.y1+1):
                    overflow.append(text.get_text())
        if overflow:
            raise ValueError("Figure text outside canvas: " + repr(overflow))
        fig.savefig(path, dpi=300)
        plt.close(fig)
        artifacts.append({"image": record(path), "dpi": 300, "text_outside_canvas": [], "details": detail})

    for sample in samples:
        sid = sample["sample_id"]
        mapping = read_json(run / "mappings" / (sid+".json"))
        represented_end = max(t["char_end"] for t in mapping["tokens"] if t["role"] == "content")
        represented = mapping["raw_text"][:represented_end]
        fig = plt.figure(figsize=(12.6,9.4))
        fig.text(.075,.956,f"A4 / {sid}   Feature-level explanation",fontsize=18,weight="bold")
        fig.text(.075,.917,f"Prediction: {sample['pred_polarity']}    |    Intensity: {sample['pred_intensity']:+.4f}    |    Frozen M3 / mean reference",fontsize=11)
        probabilities = "   ".join(f"{name}: {100*p:.1f}%" for name,p in zip(("Negative","Neutral","Positive"),sample["probabilities"],strict=True))
        fig.text(.075,.885,"Model probabilities (not calibrated certainty): " + probabilities,fontsize=9,color="#484848")
        fig.text(.075,.851,f"Represented original text [0:{represented_end}) | no omitted tail is evidence",fontsize=9,weight="bold")
        fig.text(.075,.825,wrapped(represented,135),fontsize=9.2,va="top",linespacing=1.5)
        ax1,ax2 = fig.add_axes([.09,.455,.38,.205]),fig.add_axes([.58,.455,.38,.205])
        draw_contributions(ax1,sample,"classification")
        draw_contributions(ax2,sample,"regression")
        ax = fig.add_axes([.115,.235,.785,.14])
        image = draw_local(ax,sample,report["cases"],evidence)
        cax = fig.add_axes([.919,.235,.012,.14])
        colorbar = fig.colorbar(image,cax=cax,ticks=[-1,0,1])
        colorbar.ax.tick_params(labelsize=8)
        fig.text(.115,.395,"Signed local IG, normalized separately within each row for display",fontsize=9)
        for head,y in (("classification",.163),("regression",.129)):
            e = next(e for e in evidence if e["sample_id"]==sid and e["head"]==head and e["baseline"]=="mean" and e["modality"]=="T" and e["requested_ratio"]==.2)
            label = "Class text" if head=="classification" else "Intensity text"
            text = f"{label} [{e['char_start']}:{e['char_end']}): {e['text_excerpt']}"
            fig.text(.075,y,wrapped(text,136),fontsize=8.6,va="top",linespacing=1.15)
        fig.text(.075,.077,wrapped(short_flags(sample,evidence),143),fontsize=8.1,va="top",color="#76511F",linespacing=1.2)
        fig.text(.075,.025,"LIMIT: A/V word/time/frame mapping and text-to-speech timing are unverified. Feature IG is not causal word meaning.",fontsize=8.7,color="#923E30")
        save(fig,cards/(sid+".png"),{"sample_id":sid,"reference":"mean","all_AV_times_null":True,"row_normalization_display_only":True,"omitted_tail_displayed_as_evidence":False})
    print("All 20 A4 cards rendered",flush=True)

    fig,axes=plt.subplots(2,1,figsize=(13,6.6))
    fig.subplots_adjust(left=.075,right=.985,top=.83,bottom=.15,hspace=.52)
    fig.suptitle("A4 | Modality shares across all 20 predictions",x=.075,y=.966,ha="left",fontsize=16)
    fig.text(.075,.9,"Absolute net IG shares; mean training reference. Shares are not prediction confidence or causal contributions.",fontsize=10)
    for ax,head in zip(axes,("classification","regression"),strict=True):
        values=np.asarray([s["heads"][head]["share_mean"] for s in samples])*100
        left=np.zeros(20)
        for m,(name,color) in enumerate(zip(("Text","Audio","Vision"),MODALITY_COLORS,strict=True)):
            ax.bar(range(20),values[:,m],bottom=left,width=.7,color=color,label=name)
            left+=values[:,m]
        ax.set_ylim(0,100)
        ax.set_xlim(-.6,19.6)
        ax.set_xticks(range(20),[s["sample_id"]+("*" if s["heads"][head]["baseline_sensitive"] else "") for s in samples])
        ax.set_yticks([0,50,100])
        ax.set_ylabel("Net share (%)")
        ax.set_title("Original-class logit" if head=="classification" else "Signed intensity",loc="left",fontsize=11)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower left",bbox_to_anchor=(.065,.058),ncol=3,frameon=False)
    fig.text(.075,.025,"* Primary modality changes with the median reference. 07/18: truncated text. 13: all-zero visual input, cause unknown.",fontsize=9)
    save(fig,output/"p3_modality_effects.png",{"samples":20,"references":"mean","primary_baseline_sensitivity_marked":True})

    selected=[next(s for s in samples if s["sample_id"]==row["sample_id"]) for row in selection]
    fig=plt.figure(figsize=(15.6,7.8))
    fig.text(.065,.952,"A4 | Three preregistered-rule illustration cases",fontsize=17,weight="bold")
    fig.text(.065,.907,"No correctness labels are available. All 20 full cards are retained; these examples do not establish media localization.",fontsize=10)
    for column,(sample,chosen) in enumerate(zip(selected,selection,strict=True)):
        x=.065+column*.317
        sid=sample["sample_id"]
        fig.text(x,.837,f"{sid} | {ROLES[chosen['role']]}",fontsize=11,weight="bold")
        fig.text(x,.797,f"{sample['pred_polarity']} | intensity {sample['pred_intensity']:+.4f}",fontsize=10)
        cls=fig.add_axes([x+.02,.505,.255,.215])
        regax=fig.add_axes([x+.02,.17,.255,.215])
        draw_contributions(cls,sample,"classification",compact=True)
        draw_contributions(regax,sample,"regression",compact=True)
        note="T/A/V time mapping remains unverified. "
        if chosen["role"]=="stable_dominance":note+="Concentration is not correctness."
        elif chosen["role"]=="modality_disagreement":note+="The targets, references or full-removal diagnostics disagree on primary modality."
        else:note+="Visual input is all zero; it remains observed under the frozen policy."
        fig.text(x,.075,wrapped(note,49),fontsize=8.5,va="top",linespacing=1.35)
    save(fig,output/"p3_case_cards.png",{"selection":selection,"all_twenty_available":True})

    fig,axes=plt.subplots(3,1,figsize=(12.6,8.5))
    fig.subplots_adjust(left=.115,right=.89,top=.83,bottom=.105,hspace=.78)
    fig.suptitle("A4 | Local signed feature attributions in the three fixed-rule cases",x=.075,y=.965,ha="left",fontsize=15)
    fig.text(.075,.903,"Each row is independently normalized for display. A/V feature indices cannot be read as words, seconds or frames.",fontsize=9.8)
    for ax,sample in zip(axes,selected,strict=True):
        image=draw_local(ax,sample,report["cases"],evidence)
        ax.set_title(f"Sample {sample['sample_id']} | {sample['pred_polarity']} | intensity {sample['pred_intensity']:+.4f}",loc="left",fontsize=10,pad=8)
    cax=fig.add_axes([.92,.3,.014,.35])
    fig.colorbar(image,cax=cax,ticks=[-1,0,1])
    fig.text(.115,.035,"Black boxes: top 20% feature blocks. Unnormalized signed values, word sums and random-block comparisons are stored in the audit files.",fontsize=8.5)
    save(fig,output/"p3_local_importance.png",{"sample_ids":[s["sample_id"] for s in selected],"time_evidence":None})
    return {"figures":artifacts,"source_report":record(run/"report.json"),"source_samples":record(run/"samples.json"),
            "source_selection":record(run/"card_selection.json"),"source_evidence":record(run/"evidence_map.jsonl"),
            "script":record(__file__),"cards":20,"summary_figures":3,"original_media_evidence_complete":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--a4-run",required=True)
    parser.add_argument("--verification-run",required=True)
    parser.add_argument("--figure-id",required=True)
    args=parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+",args.figure_id):raise ValueError("Invalid figure ID")
    run=existing_run(args.a4_run)
    verification=read_json(existing_run(args.verification_run)/"verification.json")
    if not verification["accepted"] or verification["source_report"]!=record(run/"report.json"):
        raise ValueError("A4 numerical verification required")
    output=ROOT/"figures/q3"/args.figure_id
    output.mkdir(parents=True,exist_ok=False)
    result=render(run,output)
    write_json(output/"source.json",result)
    print(output,flush=True)


if __name__=="__main__":
    main()
