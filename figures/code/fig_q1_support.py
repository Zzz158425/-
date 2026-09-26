"""Plot saved perturbation diagnostics, without rerunning openSMILE."""
import argparse
import json
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'code/common'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'output/q1/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
from plot_export import save_figure_variants, svg_metadata


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--input-run',default='P1_ACOUSTIC_SUPPORT_20260923_001'); parser.add_argument('--figure-id',required=True)
    args=parser.parse_args()
    if not all(s.replace('_','').isalnum() for s in [args.input_run,args.figure_id]): parser.error('Invalid artifact ID')
    source=ROOT/'output/q1'/args.input_run
    report=json.loads((source/'run.json').read_text(encoding='utf-8'))
    protocol=json.loads((source/'registered_protocol.json').read_text(encoding='utf-8'))
    out=ROOT/'figures/q1'/args.figure_id; out.mkdir(parents=True,exist_ok=False)
    font_manager.fontManager.addfont('C:/Windows/Fonts/simhei.ttf')
    plt.rcParams.update({'font.family':'SimHei','axes.unicode_minus':False,'font.size':10})
    fig,axes=plt.subplots(3,1,figsize=(9,7),layout='constrained')
    for ax,record,role in zip(axes,report['records'],['短样本','中样本','长样本']):
        name=record['sample_id'].replace('$_$','__')
        with np.load(source/name/'diagnostic_deltas.npz',allow_pickle=False) as saved:
            times=saved['start_s']; changed=(saved['absolute_difference']>protocol['change_atol']).sum(axis=1); outside=saved['outside_nominal_interval']
        left,right=record['perturb_time_s']
        ax.axvspan(left,right,color='#E7C97F',alpha=.6,label='实际扰动音频区间')
        ax.plot(times,changed,color='#397FA3',linewidth=1.2,label='发生变化的特征数')
        affected=outside & (changed>0)
        ax.scatter(times[affected],changed[affected],s=15,color='#BD5955',label='名义区间外仍变化')
        ax.set_xlim(max(0,left-.6),right+.6); ax.set_ylim(-.5,26); ax.set_yticks([0,5,10,15,20,25])
        ax.set_ylabel('变化列数（共25列）'); ax.set_xlabel('派生WAV名义索引起点（秒）')
        ax.set_title(f"{role}：名义区间外变化 {record['outside_nominal_changed_rows']} 行",loc='left')
        ax.spines[['top','right']].set_visible(False)
    axes[0].legend(loc='upper left',frameon=False,fontsize=9)
    fig.suptitle('时间索引不等于完整物理支持：三条有界扰动诊断',fontsize=13)
    svg = save_figure_variants(fig,out/'fig_q1_support.png',dpi=300,facecolor='white'); plt.close(fig)
    metadata = {'input':str(source),'dpi':300,'scope':'counterexamples only; not exact support estimation or emotion performance'}
    metadata.update(svg_metadata(svg))
    (out/'source.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(out/'fig_q1_support.png')

if __name__=='__main__':
    main()
