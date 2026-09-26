"""Read saved waveform, PTS frames and features; do not re-extract."""
import argparse
import csv
import json
import wave
import numpy as np
from matplotlib.patches import Rectangle
from q1_plot_common import ROOT,plt,setup,save


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--input-run',required=True); parser.add_argument('--figure-id',required=True)
    parser.add_argument('--case',choices=['typical','mismatch'],required=True); args=parser.parse_args()
    if not args.input_run.replace('_','').isalnum(): parser.error('Invalid run ID')
    sid={'typical':'-egA8-b7-3M$_$9','mismatch':'-mJ2ud6oKI8$_$6'}[args.case]
    source=ROOT/'output/q1'/args.input_run
    samples=json.loads((source/'dataset_manifest.json').read_text(encoding='utf-8'))['samples']
    sample=next(s for s in samples if s['sample_id']==sid); target=source/'samples'/sample['directory']
    mapping=json.loads((target/'alignment_map.json').read_text(encoding='utf-8')); words=mapping['words']
    media=json.loads((target/'media_report.json').read_text(encoding='utf-8'))['media']
    with (target/'frame_manifest.csv').open(encoding='utf-8-sig') as f: frames=[r for r in csv.DictReader(f) if r['retained_evidence_path']]
    with wave.open(str(target/'media/audio_16k_mono.wav'),'rb') as f: waveform=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)/32768.
    with np.load(target/'raw_audio.npz',allow_pickle=False) as z: audio={k:z[k] for k in z.files}
    with np.load(target/'raw_visual.npz',allow_pickle=False) as z: visual={k:z[k] for k in z.files}
    with np.load(target/'joint_features.npz',allow_pickle=False) as z: joint={k:z[k] for k in z.files}
    out=setup(args.figure_id); fig=plt.figure(figsize=(11,10.4),layout='constrained')
    grid=fig.add_gridspec(6,3,height_ratios=[1.8,1.15,.85,1,1,1])
    for j,row in enumerate(frames):
        ax=fig.add_subplot(grid[0,j]); ax.imshow(plt.imread(source/row['retained_evidence_path'])); ax.axis('off')
        pts=int(row['pts'])*float(__import__('fractions').Fraction(row['time_base']))
        ax.set_title(f"真实帧 {row['frame_index']}，PTS={pts:.3f}s",fontsize=10)
    axes=[fig.add_subplot(grid[i,:]) for i in range(1,6)]
    time_axis=np.arange(len(waveform))/16000+media['audio_first_pts_s']
    axes[0].plot(time_axis[::8],waveform[::8],color='#56616C',lw=.45); axes[0].set_ylabel('PCM幅值\n（归一化）')
    palette=['#327DA0','#B27732','#398767','#9466A5']
    for j,w in enumerate(words):
        if w['media_start_s'] is None: continue
        left,right=w['media_start_s'],w['media_end_s']; color=palette[j%4]; y=j%2
        axes[1].add_patch(Rectangle((left,y+.06),right-left,.33,facecolor=color,alpha=.5))
        axes[1].text((left+right)/2,y+.47,w['word'],ha='center',va='center',fontsize=9)
        for ax in [axes[0],*axes[2:]]: ax.axvspan(left,right,facecolor=color,alpha=.06)
    axes[1].set_ylim(-.05,1.9); axes[1].set_yticks([]); axes[1].set_ylabel('原文条件\n候选区间')
    loudness=list(audio['feature_names']).index('Loudness_sma3')
    axes[2].plot(audio['source_start_s'],audio['values'][:,loudness],color='#B27732',lw=.9); axes[2].set_ylabel('响度\n（工具输出）')
    au=list(visual['feature_names']).index('AU12_r')
    axes[3].plot(visual['intervals'][:,0],visual['values'][:,au],color='#398767',lw=.9); axes[3].set_ylabel('AU12强度\n/工具刻度')
    for j,w in enumerate(words):
        if w['media_start_s'] is not None:
            axes[4].hlines(np.linalg.norm(joint['text'][j]),w['media_start_s'],w['media_end_s'],color=palette[j%4],lw=3)
    axes[4].set_ylabel('文本向量L2范数\n（无量纲）'); axes[4].set_xlabel('原片段媒体PTS时钟 / s（不是长视频绝对时间）')
    right=max(time_axis[-1],visual['intervals'][-1,1])
    for ax in axes: ax.set_xlim(0,right); ax.grid(axis='x',alpha=.15)
    for ax in axes[:-1]: ax.tick_params(labelbottom=False)
    kind='既定中样本：工程追踪展示' if args.case=='typical' else '非理想样本：用户报告文本-音频不匹配'
    fig.suptitle(kind+'\n'+sid+'；候选词时间未经人工语义核验',fontsize=13)
    inputs=[target/p for p in ['alignment_map.json','media_report.json','frame_manifest.csv','raw_audio.npz','raw_visual.npz','joint_features.npz','media/audio_16k_mono.wav']]
    inputs.extend(source/r['retained_evidence_path'] for r in frames)
    save(fig,out,'fig_q1_alignment_'+args.case+'.png',inputs,{'sample_id':sid,'selection':'pre-registered pilot case; not chosen by labels or prediction',
         'meaning':'conditional assignment only; text vector norm is not sentiment; waveform display decimated by 8'})


if __name__=='__main__': main()
