from q2_plot_common import arguments, setup, save, plt, np


def main():
    args = arguments()
    data, out, source = setup(args)
    truth = np.asarray(data["intensity"])
    scenarios = ["control", data["worst_mae_scenario"]]
    residual_limit = max(1, int(np.ceil(max(np.abs(np.asarray(data["representative_M3"][sid]["intensity"]) - truth).max() for sid in scenarios))))
    fig, axes = plt.subplots(2, 2, figsize=(10.4, 8.4), layout="constrained")
    for column, sid in enumerate(scenarios):
        estimate = np.asarray(data["representative_M3"][sid]["intensity"])
        mae = np.mean(np.abs(estimate - truth))
        pearson = np.corrcoef(truth, estimate)[0, 1]
        ax = axes[0, column]
        ax.scatter(truth, estimate, s=12, alpha=0.42, color="#197f79", edgecolors="none")
        ax.plot([-3, 3], [-3, 3], color="#666666", linestyle="--", linewidth=1)
        title = "清洁验证集" if sid == "control" else "网格内MAE最高场景\n" + sid
        ax.set(xlim=(-3.1, 3.1), ylim=(-3.1, 3.1), xticks=np.arange(-3, 4), yticks=np.arange(-3, 4),
               xlabel="真实强度", ylabel="预测强度", title=title)
        ax.text(0.04, 0.94, f"MAE={mae:.4f}\nPearson={pearson:.4f}", transform=ax.transAxes, va="top",
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85})
        ax.grid(alpha=0.15)
        ax = axes[1, column]
        ax.scatter(truth, estimate - truth, s=12, alpha=0.42, color="#9b5966", edgecolors="none")
        ax.axhline(0, color="#555555", linestyle="--", linewidth=1)
        ax.set(xlim=(-3.1, 3.1), ylim=(-residual_limit - 0.2, residual_limit + 0.2),
               xticks=np.arange(-3, 4), yticks=np.arange(-residual_limit, residual_limit + 1),
               xlabel="真实强度", ylabel="残差（预测－真实）", title="残差分布")
        ax.grid(alpha=0.15)
    fig.suptitle("M3代表检查点回归误差（种子20260924）", fontsize=14)
    fig.supxlabel("同一728条验证样本；点重叠不表示样本被删除。最差场景只描述本次固定网格。", fontsize=10)
    save(fig, out, "p2_regression.png", source, {"seed": 20260924, "scenarios": scenarios, "population": 728}, __file__)


if __name__ == "__main__":
    main()
