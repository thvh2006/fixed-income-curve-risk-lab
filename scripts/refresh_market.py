"""Refresh a separate Treasury market receipt, preserving research and last good data.

No authentication. Official annual CSV, complete core tenors. Candidate is built
and validated before atomic rename. A failure writes health.json only.
"""
import argparse,csv,io,json,os,sys,tempfile,urllib.request,hashlib
from datetime import date,datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from curve_lab.data import FIELDS
from curve_lab.curves import bootstrap,TENORS,par_rate

def atomic(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf8',dir=path.parent,delete=False) as f:
        json.dump(obj,f,indent=2,allow_nan=False);f.write('\n');temp=f.name
    os.replace(temp,path)

def validate_bytes(raw,year):
    rows=[]
    for r in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        d=datetime.strptime(r['Date'],'%m/%d/%Y').date()
        if d.year!=year or d>date.today():raise ValueError('Invalid market date')
        p=[float(r[k])/100 for k in FIELDS];c=bootstrap(p)
        if max(abs(par_rate(c,t)-x) for t,x in zip(TENORS,p))>1e-8:raise ValueError('Candidate curve failed repricing')
        rows.append((d,p))
    if not rows or len({d for d,_ in rows})!=len(rows):raise ValueError('Empty or duplicate source dates')
    return max(rows,key=lambda r:r[0])

def publish(raw,year,directory,source):
    directory=Path(directory);stamp=datetime.now(timezone.utc).isoformat()
    try:
        d,p=validate_bytes(raw,year)
        candidate=dict(status='available',as_of=d.isoformat(),retrieved_at=stamp,source=source,source_sha256=hashlib.sha256(raw).hexdigest(),par=p,tenors=TENORS.tolist(),kind='Separate current-market receipt; frozen study unchanged')
        existing=directory/'latest.json'
        if existing.exists() and json.loads(existing.read_text()).get('as_of','')>d.isoformat():raise ValueError('Source date regressed')
        atomic(existing,candidate);atomic(directory/'health.json',dict(last_attempt=stamp,status='success',as_of=d.isoformat()));return candidate
    except Exception as e:
        atomic(directory/'health.json',dict(last_attempt=stamp,status='failed',error_type=type(e).__name__,last_known_good_retained=True));raise

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--year',type=int,default=date.today().year);p.add_argument('--csv',type=Path);p.add_argument('--directory',type=Path,default=R/'data');a=p.parse_args()
    url=f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{a.year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={a.year}&_format=csv'
    try:
        raw=a.csv.read_bytes() if a.csv else urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FixedIncomeCurveRiskLab/1.0 source research'}),timeout=40).read()
        out=publish(raw,a.year,a.directory,url);print(json.dumps(dict(status=out['status'],as_of=out['as_of'])))
    except Exception as e:
        atomic(a.directory/'health.json',dict(last_attempt=datetime.now(timezone.utc).isoformat(),status='failed',error_type=type(e).__name__,last_known_good_retained=True));print('Refresh failed; last-known-good retained:',type(e).__name__,file=sys.stderr);raise SystemExit(1)
if __name__=='__main__':main()
