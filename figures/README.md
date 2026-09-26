# PNG / SVG 图件说明

## 本次交付

2026-09-24 为 q1、q2、q3 的全部 78 张历史 PNG 补齐了同目录、同名 SVG，包括早期版本和重复核验图。原 PNG、旧 `source.json`、历史脚本、说明和 ZIP 均未改动；早期图仅补格式，不代表被升级为论文采用版本。

全文技术路线图为本目录的 `overall_technical_route.svg`，另有 `overall_technical_route.png` 供预览。图中保留问题1质量限制及附件4原词、秒、帧映射未核验的边界，不代表问题3原媒体定位已完成。

## 生成方式

不是把 PNG 嵌入 SVG 外壳。已有绘图 Python 代码已经接入 `code/common/plot_export.py`，同一个 Matplotlib Figure 直接导出 PNG 和 SVG。SVG 使用 `svg.fonttype = none`，保留可编辑文字、线条、形状等元素；图中原有视频截图等栅格内容仍为位图，不会自动变成可编辑矢量。

为补齐旧图，`code/figures/backfill_svg.py` 只读取已保存结果，重放原绘图过程；每张重绘 PNG 与历史 PNG 逐字节一致后，才将 SVG 复制到历史目录。早期 q3 图使用对应留存源码重放原版排版，没有用新版图冒充旧版。没有重新训练、预测或计算归因。

## 代码入口

以下路径相对 `D:\个人资料\数学建模比赛\E题解答`。

| 内容 | 绘图代码 |
| --- | --- |
| 问题1采用图 | `code/figures/fig_q1_pipeline.py`、`fig_q1_alignment.py`、`fig_q1_full_quality.py`、`fig_q1_visual_quality.py` |
| 问题1早期质量与支持图 | `code/figures/fig_q1_quality.py`、`fig_q1_support.py` |
| 问题2图 | `code/figures/fig_q2_robustness.py`、`fig_q2_ablation.py`、`fig_q2_confusion.py`、`fig_q2_regression.py` |
| 问题3附件4解释图 | `code/q3/plot_a4.py` |
| 问题3验证图 | `code/q3/plot_validation.py` |
| 全文技术路线图 | `code/figures/overall_technical_route.py` |
| 公共导出与接入 | `code/common/plot_export.py`、`code/figures/q1_plot_common.py`、`code/figures/q2_plot_common.py` |

后续只需运行原绘图入口，会同时生成两种格式。使用新的 `--figure-id`；已存在的图目录或输出文件会拒绝覆盖，以保护历史图和队友改稿。完整参数可用各入口的 `--help` 查看。不要为了改图重跑训练或预测入口。

例如，基于保存的分析结果重新绘制问题2消融图：

```powershell
& 'D:\anaconda3\envs\mathmodel\python.exe' -X utf8 -B 'D:\个人资料\数学建模比赛\E题解答\code\figures\fig_q2_ablation.py' --analysis-run P2_ANALYSIS_20260924_001 --figure-id P2_ABLATION_EDIT_001
```

路线图默认输出已经存在，修改代码后应指定新的文件名；`--output` 接收 PNG 路径，并自动生成同名 SVG：

```powershell
& 'D:\anaconda3\envs\mathmodel\python.exe' -X utf8 -B 'D:\个人资料\数学建模比赛\E题解答\code\figures\overall_technical_route.py' --output 'D:\个人资料\数学建模比赛\E题解答\figures\overall_technical_route_edit_001.png'
```

文字采用黑体（SimHei）或微软雅黑（Microsoft YaHei）。队友编辑时应安装对应字体；替换字体后需检查换行和位置。建议另存改稿，保留本次核验过的 SVG。

## 核验记录

审计目录：`output/figures/SVG_EXPORT_20260924_001/`。

- `figures_before.json`：修改前 114 个历史文件的大小与 SHA256。
- `before/`：原绘图源码快照。
- `backfill_verification.json`：78 张图的精确 PNG 比较、SVG 路径及哈希。
- `replays/`：重绘命令、日志及中间图件。
- `route_svg_preview.png`：浏览器实际渲染路线图 SVG 的预览。
- `final_verification.json`：最终文件数量、XML/文字元素、哈希和测试核验记录。

旧 `source.json` 没有追加 SVG 字段，以保留历史记录原字节；本次新增 SVG 的来源在单独的核验报告中。旧 ZIP 也未重新打包，不包含这次代码更新，后续请使用上述当前 `.py` 文件。
