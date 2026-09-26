from q2_plot_common import arguments, setup, save, plt, np


def main():
    args = arguments(lambda parser: parser.add_argument("--metric", choices=("macro_f1", "mae"), required=True))
    data, out, source = setup(args)
    combos = ["T", "A", "V", "TA", "TV", "AV", "TAV"]
    positions = ["start", "middle", "end"]
    metric = args.metric
    name = "Macro-F1" if metric == "macro_f1" else "MAE"
    matrices = [np.array([[data["heat"][f"{combo}_{pos}_{ratio}"][metric] for pos in positions] for combo in combos]) for ratio in (20, 50)]
    deltas = [np.array([[data["heat"][f"{combo}_{pos}_{ratio}"]["delta_" + metric] for pos in positions] for combo in combos]) for ratio in (20, 50)]
    lo, hi = min(x.min() for x in matrices), max(x.max() for x in matrices)
    span = max(abs(x).max() for x in deltas)
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 9.0), layout="constrained")
    for column, ratio in enumerate((20, 50)):
        for row, matrix in enumerate((matrices[column], deltas[column])):
            ax = axes[row, column]
            if row == 0:
                image = ax.imshow(matrix, vmin=lo, vmax=hi, cmap="YlGnBu" if metric == "macro_f1" else "YlOrRd", aspect="auto")
                title = f"目标比例{ratio}%：{name}"
            else:
                image = ax.imshow(matrix, vmin=-span, vmax=span, cmap="RdBu" if metric == "macro_f1" else "RdBu_r", aspect="auto")
                title = f"目标比例{ratio}%：相对清洁的变化"
            ax.set(xticks=range(3), xticklabels=["起始", "中部", "末尾"], yticks=range(7), yticklabels=combos, title=title)
            for i in range(7):
                for j in range(3):
                    rgba = image.cmap(image.norm(matrix[i, j]))
                    luminance = 0.2126 * rgba[0] + 0.7152 * rgba[1] + 0.0722 * rgba[2]
                    ax.text(j, i, f"{matrix[i,j]:+.3f}" if row else f"{matrix[i,j]:.3f}",
                            ha="center", va="center", color="white" if luminance < 0.52 else "#152326", fontsize=10)
            fig.colorbar(image, ax=ax, shrink=0.85, pad=0.02)
    fig.suptitle(f"M3缺失规律：三种子逐场景{name}均值", fontsize=14)
    direction = "Macro-F1下降为负值" if metric == "macro_f1" else "MAE上升为正值"
    fig.supxlabel(f"T/A/V为被遮挡模态；仅为内容位置比例，不是秒数。{direction}。\n主指标包含全部728条；4条不可构造局部块的短样本保持原输入。", fontsize=10)
    save(fig, out, "p2_robustness_" + ("f1" if metric == "macro_f1" else "mae") + ".png", source,
         {"metric": metric, "seed_aggregation": "mean of three per-seed metrics; not ensemble", "population": 728}, __file__)


if __name__ == "__main__":
    main()
