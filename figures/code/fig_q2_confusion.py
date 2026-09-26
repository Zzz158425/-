from q2_plot_common import arguments, setup, save, plt, np


def main():
    args = arguments()
    data, out, source = setup(args)
    truth = np.asarray(data["classes"])
    scenarios = ["control", data["worst_f1_scenario"]]
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 5.2), layout="constrained")
    for ax, sid in zip(axes, scenarios, strict=True):
        predicted = np.asarray(data["representative_M3"][sid]["probabilities"]).argmax(1)
        counts = np.zeros((3, 3), dtype=int)
        np.add.at(counts, (truth, predicted), 1)
        fractions = counts / counts.sum(1, keepdims=True)
        image = ax.imshow(fractions, cmap="Blues", vmin=0, vmax=1)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{counts[i,j]}\n({fractions[i,j]:.1%})", ha="center", va="center",
                        fontsize=12, color="white" if fractions[i,j] > 0.55 else "#162b3c")
        title = "清洁验证集" if sid == "control" else "网格内Macro-F1最低场景\n" + sid
        ax.set(xticks=range(3), xticklabels=["负", "中性", "正"], yticks=range(3), yticklabels=["负", "中性", "正"],
               xlabel="预测类别", ylabel="真实类别", title=title)
    fig.colorbar(image, ax=axes, shrink=0.7, label="行内比例", pad=0.02)
    fig.suptitle("M3代表检查点分类误差（种子20260924）", fontsize=14)
    fig.supxlabel("每格为样本数及真实类别内比例；728条验证样本，场景按固定43场景网格内指标描述性选取。", fontsize=10)
    save(fig, out, "p2_confusion.png", source, {"seed": 20260924, "scenarios": scenarios, "class_order": ["Negative", "Neutral", "Positive"]}, __file__)


if __name__ == "__main__":
    main()
