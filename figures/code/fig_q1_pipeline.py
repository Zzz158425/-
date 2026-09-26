"""Show the actual saved P1 configuration and quality branches."""
import argparse
import json
from q1_plot_common import ROOT,plt,setup,save


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--input-run',required=True); parser.add_argument('--figure-id',required=True); args=parser.parse_args()
    if not args.input_run.replace('_','').isalnum(): parser.error('Invalid run ID')
    source=ROOT/'output/q1'/args.input_run
    config=json.loads((source/'config.json').read_text(encoding='utf-8'))
    out=setup(args.figure_id); fig,ax=plt.subplots(figsize=(11,6.5)); ax.set_xlim(0,12); ax.set_ylim(0,8); ax.axis('off')
    def box(x,y,text,color='#E7EDF1',width=2.8):
        ax.text(x,y,text,ha='center',va='center',fontsize=11,bbox={'boxstyle':'square,pad=.7','facecolor':color,'edgecolor':'#77838C'})
    def arrow(a,b): ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':'#56616C','lw':1.2})
    box(6,7.35,'原100条ID、文本、全部标签与只读MP4\n来源哈希 + 默认编辑列表 + 原生PTS')
    for x in [2,6,10]: arrow((6,6.85),(x,5.95))
    box(2,5.45,'原文字符offset\n冻结BERT：768维','#DFEAF0')
    box(6,5.45,'实际音频：16kHz单声道\neGeMAPSv02 LLD：25维','#F3E8D8')
    box(10,5.45,'真实PTS解码帧\nOpenFace CECLM：25维','#E0EDE6')
    arrow((6,4.85),(6,4.1)); box(6,3.65,'原文条件式强制对齐\nWhisperX：候选区间，不改原文','#ECE5F1')
    arrow((2,4.85),(2,2.35)); arrow((10,4.85),(10,2.35)); arrow((6,3.1),(6,2.35))
    box(6,1.85,'区间重叠加权聚合 + 原始三模态全保留\n768/25/25维变长视图 + 逐词来源索引')
    arrow((6,1.25),(6,.6)); box(6,.28,'质量独立记录：可用性 / 未定位 / 自然零 / 对应未知或有证据不匹配','#F1E5E4')
    fig.suptitle('问题1实际流程：'+config['version'],fontsize=14)
    fig.tight_layout()
    save(fig,out,'fig_q1_pipeline.png',[source/'config.json',source/'quality_policy.json'],{'scope':'implemented P1 pipeline; no supervised training'})


if __name__=='__main__': main()
