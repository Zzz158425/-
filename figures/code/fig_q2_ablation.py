from q2_plot_common import arguments, setup, save, plt, np


def main():
    args = arguments()
    data, out, source = setup(args)
    first = data["ablation"][:5]
    labels = ["B0", "M0", "M1", "M2", "M3\n首种子", "M3\n三种子"]
    colors = ["#747c83", "#476f96", "#b16c32", "#8b6c9e", "#198678", "#66aca1"]
    fig, axes = plt.subplots(2, 2, figsize=(10.4, 7.0), layout="constrained")
    panels = [("clean_macro_f1", "清洁验证集 Macro-F1", 0.8), ("clean_mae", "清洁验证集 MAE", 0.85),
              ("mean_43_macro_f1", "43场景平均 Macro-F1", 0.8), ("mean_43_mae", "43场景平均 MAE", 0.85)]
    for ax, (field, title, upper) in zip(axes.flat, panels, strict=True):
        values = [row[field] for row in first] + [data["M3_seed_summary"][field]["mean"]]
        sd = data["M3_seed_summary"][field]["sample_sd"]
        ax.bar(range(6), values, color=colors, width=0.62)
        ax.errorbar(5, values[-1], yerr=sd, color="#263238", capsize=4, fmt="none", linewidth=1.2)
        for i, value in enumerate(values):
            ax.text(i, value + (sd if i == 5 else 0) + 0.016, f"{value:.4f}", ha="center", fontsize=9)
        ax.set(xticks=range(6), xticklabels=labels, ylim=(0, upper), title=title)
        ax.grid(axis="y", alpha=0.18)
        ax.set_axisbelow(True)
    fig.suptitle("问题2基线与消融：首种子比较和候选模型种子波动", fontsize=14)
    fig.supxlabel("B0、M0-M3首种子均为20260924；最右列误差线为3个种子的样本标准差，不是置信区间。", fontsize=10)
    save(fig, out, "p2_ablation.png", source, {"models": "B0/M0-M3 initial; M3 seed mean and sample SD", "ensemble": False}, __file__)


if __name__ == "__main__":
    main()
