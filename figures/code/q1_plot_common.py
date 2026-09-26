"""Local plotting setup for saved P1 results."""
import hashlib
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
from plot_export import save_figure_variants


def setup(figure_id):
    if not figure_id.replace('_','').isalnum(): raise ValueError('Invalid figure ID')
    out=ROOT/'figures/q1'/figure_id; out.mkdir(parents=True,exist_ok=False)
    font_manager.fontManager.addfont('C:/Windows/Fonts/simhei.ttf')
    plt.rcParams.update({'font.family':'SimHei','axes.unicode_minus':False,'font.size':10,'text.parse_math':False,
                         'axes.spines.top':False,'axes.spines.right':False})
    return out


def save(fig,out,name,inputs,details):
    svg = save_figure_variants(fig,out/name,dpi=300,facecolor='white'); plt.close(fig)
    records=[]
    for path in inputs:
        records.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (out/'source.json').write_text(json.dumps({'inputs':records,'details':details,'dpi':300,
        'svg':str(svg),'svg_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),'svg_text_editable':True},ensure_ascii=False,indent=2),encoding='utf-8')
    print(out/name)
