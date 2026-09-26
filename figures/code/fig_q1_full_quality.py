"""Plot full P1 quality metadata from an independently audited saved run."""
import argparse
import csv
import json
import numpy as np
from q1_plot_common import ROOT,plt,setup,save


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--audit-run',required=True); parser.add_argument('--figure-id',required=True)
    args=parser.parse_args()
    if not args.audit_run.replace('_','').isalnum(): parser.error('Invalid run ID')
    source=ROOT/'output/q1'/args.audit_run
    s=json.loads((source/'summary.json').read_text(encoding='utf-8'))
    with (source/'coverage_100.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    out=setup(args.figure_id); fig,axes=plt.subplots(2,2,figsize=(11,7.5),layout='constrained')
    counts=[s[k] for k in ['word_count','localized_candidate_words','text_available_words','audio_available_words','visual_available_words']]
    bars=axes[0,0].bar(['原文词','候选定位','文本可用','声学可用','视觉可用'],counts,color=['#6B7077','#9466A5','#327DA0','#B27732','#398767'])
    axes[0,0].bar_label(bars,padding=3,fontsize=9); axes[0,0].set_ylim(0,max(counts)*1.16); axes[0,0].set_ylabel('词数 / 个')
    axes[0,0].set_title('(a) 全100条的词级结构统计')
    counts=[s['sample_correspondence_counts'].get(k,0) for k in ['mismatch_user_report','unknown','matched_verified']]
    bars=axes[0,1].bar(['用户报告不匹配','未知','已核验一致'],counts,color=['#B95650','#81868E','#398767'])
    axes[0,1].bar_label(bars,padding=3); axes[0,1].set_ylim(0,110); axes[0,1].set_ylabel('样本数 / 条'); axes[0,1].set_title('(b) 样本级文本-音频对应状态')
    axes[1,0].hist([int(r['word_count']) for r in rows],bins=np.arange(0,max(int(r['word_count']) for r in rows)+6,5),color='#327DA0',edgecolor='white')
    axes[1,0].set_xlabel('每条原文词数 / 个'); axes[1,0].set_ylabel('样本数 / 条'); axes[1,0].set_title('(c) 变长输出：不统一裁成50词')
    x=np.arange(1,len(rows)+1)
    for key,label,color,marker in [('mean_audio_assignment_coverage','声学分配覆盖','#B27732','o'),('mean_visual_assignment_coverage','视觉分配覆盖','#398767','x')]:
        axes[1,1].scatter(x,[float(r[key]) for r in rows],s=15,label=label,c=color,marker=marker,alpha=.75)
    axes[1,1].set_ylim(-.03,1.05); axes[1,1].set_xlabel('原标签表样本序号'); axes[1,1].set_ylabel('逐词覆盖率均值'); axes[1,1].legend(frameon=False,fontsize=9)
    axes[1,1].set_title('(d) 名义区间并集覆盖，不是对齐准确率')
    fig.suptitle('问题1：提取可用性与语义对应可信度分开报告',fontsize=14)
    save(fig,out,'fig_q1_full_quality.png',[source/'summary.json',source/'coverage_100.csv'],{'scope':'100 samples; structural metrics, not semantic accuracy'})


if __name__=='__main__': main()
