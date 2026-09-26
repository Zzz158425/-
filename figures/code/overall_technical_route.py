"""Draw the paper's actual workflow, including unresolved evidence boundaries."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/common"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "output/figures/matplotlib_cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, FancyArrowPatch
from plot_export import save_figure_variants


def build_figure():
    for filename in ("msyh.ttc", "msyhbd.ttc"):
        font_manager.fontManager.addfont("C:/Windows/Fonts/" + filename)
    with plt.rc_context({"font.family": "Microsoft YaHei", "axes.unicode_minus": False,
                         "text.parse_math": False, "font.size": 12}):
        fig = plt.figure(figsize=(16, 11.6), facecolor="white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set(xlim=(0, 16), ylim=(0, 11.6))
        ax.axis("off")
        ink, muted = "#20262B", "#545E66"
        colors = ["#26728A", "#31795D", "#9C4D64"]
        fills = ["#EDF5F8", "#EFF6F1", "#FAF0F3"]
        xs, width = [.55, 5.75, 10.95], 4.5

        def text(x, y, value, size=12, color=ink, **kwargs):
            return ax.text(x, y, value, fontsize=size, color=color, va="center", **kwargs)

        def box(column, y, title, body, height=1.24):
            x = xs[column]
            patch = Rectangle((x, y-height/2), width, height, facecolor=fills[column],
                              edgecolor=colors[column], linewidth=1.05)
            ax.add_patch(patch)
            text(x+.19, y+height/2-.28, title, 13.5, colors[column], weight="bold")
            text(x+.19, y-.17, body, 11.6, linespacing=1.55)

        def arrow(start, end, color=muted):
            ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>",
                                        mutation_scale=13, linewidth=1.25, color=color))

        text(.55, 11.08, "复杂场景下多模态情感预测", 24, weight="bold")
        text(.55, 10.60, "全文技术路线：独立特征提取、缺失鲁棒预测与特征级解释", 14, muted)
        titles = ["问题1  特征提取与候选对齐", "问题2  缺失鲁棒情感预测", "问题3  冻结模型的可解释分析"]
        for i, title in enumerate(titles):
            text(xs[i], 10.00, title, 15, colors[i], weight="bold")
            ax.plot([xs[i], xs[i]+width], [9.70, 9.70], color=colors[i], lw=2)

        box(0, 8.91, "附件1：100条原始样本", "原始文本、音视频、全部标签与ID保留\n媒体时钟 / 配对核验 / 来源记录")
        box(0, 7.28, "三模态独立提取", "冻结BERT / openSMILE / OpenFace\n原文条件式WhisperX候选对齐")
        box(0, 5.65, "候选区间聚合与独立质量记录", "区间重叠加权聚合；原序列完整保留\n提取可用性与语义对应状态分别记录")
        box(0, 4.02, "问题1交付", "100条特征、来源索引与质量掩码\n典型样本、异常样本及全量统计")

        box(1, 8.91, "附件2：统一对齐版接口", "train 3395：拟合与训练；valid 728：选型\ntest 727封存；不并入问题1自提特征")
        box(1, 7.28, "连续缺失场景与严格文本通路", "BERT输入端遮挡，编码后屏蔽对应输出\n训练集统计归一化；显式缺失掩码")
        box(1, 5.65, "CNN编码、门控融合与双任务", "分类头 + 强度回归头；B0 / M0-M3对照\n6次神经训练；固定规则冻结代表M3")
        box(1, 4.02, "评价与附件3冻结预测", "43场景、消融、三种子与误差分析\n附件3全30条预测；无专项真值准确率")

        box(2, 8.91, "附件4与冻结验证样本", "附件4对齐版20条；验证集固定60条\n复用M3及训练集均值 / 中位数参考")
        box(2, 7.28, "固定解释目标与参考", "原预测类别logit / 强度输出\n双头、双参考；数值收敛检查")
        box(2, 5.65, "IG归因与特征级忠实性", "局部关键块干预，对照匹配随机块\n按原视频分组区间；稳定性与反例")
        box(2, 4.02, "问题3限定交付", "全20条预测、模态贡献与解释图卡\n文本字符证据 + A/V特征位置索引")

        for i in range(3):
            center = xs[i]+width/2
            for upper, lower in [(8.91, 7.28), (7.28, 5.65), (5.65, 4.02)]:
                arrow((center, upper-.64), (center, lower+.64), colors[i])
        arrow((xs[1]+width+.03, 5.65), (xs[2]-.03, 5.65), colors[1])

        text(xs[0], 2.92, "边界：5条词级视觉全不可用；\n全词语义对应仍未知，不等于对齐正确。", 11, "#814138", linespacing=1.5)
        text(xs[1], 2.92, "边界：首种子领先不代表稳定优势；\n附件3无真值，不报告专项准确率。", 11, "#814138", linespacing=1.5)
        text(xs[2], 2.92, "边界：附件4原词 / 秒 / 帧映射未核验；\n特征级解释不等于原音视频证据定位。", 11, "#814138", linespacing=1.5)

        ax.add_patch(Rectangle((.55, 1.18), 14.9, 1.08, facecolor="#F3F4F5", edgecolor="#AFB7BC", lw=1))
        text(.78, 1.95, "综合评价与论文组织", 14, weight="bold")
        text(.78, 1.53, "质量统计与适用范围  |  预测性能、鲁棒性与误差  |  解释忠实性、稳定性及反例  |  复现代码、图表与局限披露", 12)
        for x in [xs[i]+width/2 for i in range(3)]:
            arrow((x, 2.56), (x, 2.29))
        text(.55, .66, "实线表示本地已实施流程；问题1特征不输入问题2/3训练。待核验映射保留为缺口，不用推测时间替代。", 11, muted)
        return fig


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "figures/overall_technical_route.png")
    args = parser.parse_args()
    fig = build_figure()
    try:
        svg = save_figure_variants(fig, args.output, dpi=300, facecolor="white")
    finally:
        plt.close(fig)
    print(svg)


if __name__ == "__main__":
    main()
