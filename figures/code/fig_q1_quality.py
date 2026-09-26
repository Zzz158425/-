"""Render saved three-sample quality metadata; never re-extract features."""
import argparse
import json
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/common'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'output/q1/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
from plot_export import save_figure_variants, svg_metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-run', default='P1_QUALITY_PILOT_20260923_001')
    parser.add_argument('--figure-id', required=True)
    args = parser.parse_args()
    if not all(s.replace('_', '').isalnum() for s in [args.input_run, args.figure_id]):
        parser.error('Invalid artifact ID')
    source = ROOT / 'output/q1' / args.input_run / 'run.json'
    data = json.loads(source.read_text(encoding='utf-8'))['records']
    out = ROOT / 'figures/q1' / args.figure_id; out.mkdir(parents=True, exist_ok=False)
    font_manager.fontManager.addfont('C:/Windows/Fonts/simhei.ttf')
    plt.rcParams.update({'font.family':'SimHei', 'axes.unicode_minus':False, 'font.size':11})
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), layout='constrained')
    x = np.arange(len(data))
    for offset, key, title, color in [(-.25,'text_available','文本','#397FA3'),(0,'audio_available','声学候选','#B17328'),(.25,'visual_available','视觉候选','#4C956C')]:
        axes[0].bar(x+offset,[r[key] for r in data],width=.23,label=title,color=color)
    axes[0].set_xticks(x,['短样本（5词）','中样本（10词）','长样本（49词）'])
    axes[0].set_ylabel('结构可用的词级向量数量（个）'); axes[0].set_title('三条工程小试：不是全100条统计')
    axes[0].legend(frameon=False); axes[0].spines[['top','right']].set_visible(False)
    counts=[sum(r['sample_text_audio_status']=='mismatch_user_report' for r in data),sum(r['sample_text_audio_status']=='unknown' for r in data),sum(r['sample_text_audio_status']=='matched_verified' for r in data)]
    bars=axes[1].bar(['用户报告不匹配','对应关系未知','已核验一致'],counts,color=['#BD5955','#878C91','#4C956C'])
    axes[1].bar_label(bars,padding=4); axes[1].set_ylim(0,3); axes[1].set_yticks([0,1,2,3])
    axes[1].set_ylabel('样本数量（条）'); axes[1].set_title('文本与音频：样本级对应状态')
    axes[1].spines[['top','right']].set_visible(False)
    svg = save_figure_variants(fig,out/'fig_q1_quality.png',dpi=300,facecolor='white'); plt.close(fig)
    metadata = {'input':str(source),'scope':'three pilot samples; structural availability is not semantic accuracy','dpi':300}
    metadata.update(svg_metadata(svg))
    (out/'source.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(out/'fig_q1_quality.png')

if __name__=='__main__':
    main()
