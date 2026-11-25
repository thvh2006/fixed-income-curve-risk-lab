"""Vector research figures, with a single 12-point Times New Roman type size."""
from pathlib import Path
import json,math,os
from reportlab.graphics.shapes import Drawing,Line,String,PolyLine,Rect
from reportlab.graphics import renderSVG
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[1];D=json.loads((R/'artifacts/release/research.json').read_text())
FONT_DIR=Path(os.environ.get('P4_TIMES_FONT_DIR','/System/Library/Fonts/Supplemental'))
for n,f in [('TNR','Times New Roman.ttf'),('TNR-Bold','Times New Roman Bold.ttf'),('TNR-Italic','Times New Roman Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(n,str(FONT_DIR/f)))
pdfmetrics.registerFontFamily('TNR',normal='TNR',bold='TNR-Bold',italic='TNR-Italic',boldItalic='TNR-Bold')
COLORS=['#28686e','#aa764f','#65738c','#7f667d']
def figure(title,series,unit='',x_title='Tenor (years)'):
    d=Drawing(470,286);xs=[p[0] for _,s in series for p in s];ys=[p[1] for _,s in series for p in s]
    lo=min(ys);hi=max(ys);pad=(hi-lo)*.1 or .1;lo-=pad;hi+=pad;a=min(xs);b=max(xs)
    sx=lambda x:60+(x-a)/(b-a or 1)*400;sy=lambda y:96+(y-lo)/(hi-lo)*145
    d.add(String(0,267,title,fontName='TNR-Bold',fontSize=12))
    for i in range(5):
        y=lo+(hi-lo)*i/4;d.add(Line(60,sy(y),460,sy(y),strokeColor=HexColor('#dbe3e1'),strokeWidth=.5));d.add(String(0,sy(y)-4,f'{y:,.2f}{unit}',fontName='TNR',fontSize=12))
    for j,(name,ss) in enumerate(series):
        pts=[v for x,y in ss for v in [sx(x),sy(y)]];d.add(PolyLine(pts,strokeColor=HexColor(COLORS[j%4]),strokeWidth=1.5))
        yy=52-(j//2)*19;xx=(j%2)*240;d.add(Line(xx,yy+3,xx+20,yy+3,strokeColor=HexColor(COLORS[j%4]),strokeWidth=1.5));d.add(String(xx+27,yy,name,fontName='TNR',fontSize=12))
    d.add(String(60,76,f'{a:g}',fontName='TNR',fontSize=12));d.add(String(431,76,f'{b:g}',fontName='TNR',fontSize=12));d.add(String(185,76,x_title,fontName='TNR',fontSize=12))
    return d

def figures():
    T=D['config']['core_tenors_years'];c=D['curve'];b=D['bond'];p=D['portfolios'];h=D['hedge']
    return {
      'curve':figure('Par, zero and forward curves, 31 December 2025',[
          ('Observed par',list(zip(T,[x*100 for x in D['history'][-1]['par']]))),
          ('Model zero, continuous',list(zip(c['grid'],[x*100 for x in c['zero']]))),
          ('Model forward, continuous',list(zip(c['grid'],[x*100 for x in c['forward']]))),
      ],'%'),
      'residuals':figure('Par calibration residuals (basis points)',[(m['method'],list(zip(T,m['residual_bp']))) for m in D['methods']],''),
      'keyrates':figure('Key-rate DV01, USD per bp on USD 1 million',[(n,list(zip(D['config']['key_tenors_years'],v['key_dv01']))) for n,v in p.items()]),
      'hedge':figure('Bullet key-rate exposure before and after hedge',[('Before',list(zip(D['config']['key_tenors_years'],h['before']))),('After 2/10-year hedge',list(zip(D['config']['key_tenors_years'],h['after']))),('Parallel-neutral hedge',list(zip(D['config']['key_tenors_years'],D['duration_hedge']['key_dv01'])))]),
      'forecast':figure('Forecast RMSE by tenor, basis points',[(n.replace('_',' '),list(zip(T,v['tenor_rmse_bp']))) for n,v in D['forecast']['metrics'].items()]),
      'allocation':figure('Model-implied allocation wealth, starting at 1',[(n.replace('_',' '),[(0,1)]+[(j+1,math.prod(1+r['net_return'] for r in v['periods'][:j+1])) for j in range(len(v['periods']))]) for n,v in D['forecast']['allocation'].items()],x_title='Five-observation periods'),
    }
if __name__=='__main__':
    out=R/'artifacts/release/figures';out.mkdir(parents=True,exist_ok=True)
    for name,d in figures().items():renderSVG.drawToFile(d,str(out/(name+'.svg')))
    print('Saved six vector figures')
