"""Visual quality example selected by unavailable-word count, not labels."""
import argparse
import csv
from fractions import Fraction
import json
import numpy as np
from q1_plot_common import ROOT,plt,setup,save


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--input-run',required=True)
    parser.add_argument('--audit-run',required=True); parser.add_argument('--figure-id',required=True); args=parser.parse_args()
    if not all(s.replace('_','').isalnum() for s in [args.input_run,args.audit_run]): parser.error('Invalid run ID')
    source=ROOT/'output/q1'/args.input_run; audit=ROOT/'output/q1'/args.audit_run
    with (audit/'coverage_100.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    row=max(rows,key=lambda r:int(r['word_count'])-int(r['visual_available_words']))
    target=source/'samples'/row['directory']
    with (target/'frame_manifest.csv').open(encoding='utf-8-sig') as f: frames=[r for r in csv.DictReader(f) if r['retained_evidence_path']]
    with np.load(target/'raw_visual.npz',allow_pickle=False) as z: v={k:z[k] for k in z.files}
    with np.load(target/'joint_features.npz',allow_pickle=False) as z: j={k:z[k] for k in z.files}
    out=setup(args.figure_id); fig=plt.figure(figsize=(11,6.5),layout='constrained')
    grid=fig.add_gridspec(3,3,height_ratios=[2,1,1])
    for k,frame in enumerate(frames):
        ax=fig.add_subplot(grid[0,k]); ax.imshow(plt.imread(source/frame['retained_evidence_path'])); ax.axis('off')
        ax.set_title(f"真实帧{frame['frame_index']}，PTS={float(int(frame['pts'])*Fraction(frame['time_base'])):.3f}s",fontsize=10)
    ax=fig.add_subplot(grid[1,:]); ax.step(v['intervals'][:,0],v['success'],where='post',color='#B95650',lw=1.5)
    ax.set_ylim(-.1,1.1); ax.set_yticks([0,1],['检测失败','检测成功']); ax.set_xlabel('媒体PTS时钟 / s')
    ax.set_title(f"原始视觉输出保留：{len(v['success'])}帧，success=1共{int(v['success'].sum())}帧")
    ax=fig.add_subplot(grid[2,:]); masks=np.stack([j[m+'_available'] for m in ['text','audio','visual']])
    from matplotlib.colors import ListedColormap
    ax.imshow(masks,aspect='auto',interpolation='nearest',cmap=ListedColormap(['#C76B63','#68A187']),vmin=0,vmax=1)
    ax.set_yticks([0,1,2],['文本可用','声学候选可用','视觉候选可用']); ax.set_xticks(np.arange(len(j['text'])),np.arange(1,len(j['text'])+1))
    ax.set_xlabel('原文词序号（非时间）；绿=可用，红=不可用')
    fig.suptitle(row['sample_id']+'：视觉不可用不等于删除样本或自然零\n仅依据提取器success标记，不推断文本错误或真实情感',fontsize=13)
    inputs=[audit/'coverage_100.csv',target/'frame_manifest.csv',target/'raw_visual.npz',target/'joint_features.npz']
    inputs.extend(source/f['retained_evidence_path'] for f in frames)
    save(fig,out,'fig_q1_visual_quality.png',inputs,{'sample_id':row['sample_id'],'selection':'maximum unavailable visual words; first worksheet occurrence breaks ties','no_new_threshold':True})


if __name__=='__main__': main()
