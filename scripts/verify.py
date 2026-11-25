"""Independent regeneration checks against frozen artifacts; does not overwrite them."""
from pathlib import Path
from datetime import date
import json,sys,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import numpy as np
from curve_lab.data import load_history,digest
from curve_lab.curves import bootstrap,par_rate,TENORS,KEYS
from curve_lab.bonds import Bond,add_months
from curve_lab.risk import bond_risk,carry_bridge,hedge
from curve_lab.forecast import evaluate
def main():
    d=json.loads((R/'artifacts/release/research.json').read_text());rows,receipts=load_history(R);checks=[]
    def check(name,ok):
        if not bool(ok):raise AssertionError(name)
        checks.append(name)
    check('source receipts match',receipts==d['source_receipts']);check('499 observations',len(rows)==499)
    for row,saved in zip(rows,d['history']):
        c=bootstrap(row['par']);check('date '+row['date'],row['date']==saved['date']);check('discount '+row['date'],np.max(abs(c.d-saved['discounts']))<1e-12)
        for t,p in zip(TENORS,row['par']):check('par '+row['date']+'/'+str(t),abs(par_rate(c,t)-p)<1e-10)
    b=Bond(date(2030,12,31),.04);s=date(2025,12,31);c=bootstrap(rows[-1]['par']);r=bond_risk(b,s,c)
    for key in ['dirty','parallel_dv01','curve_duration','curve_convexity']:check('bond '+key,abs(r[key]-d['bond']['curve_risk'][key])<1e-8)
    check('key curve risk',np.max(abs(np.array(r['key_dv01'])-d['bond']['curve_risk']['key_dv01']))<1e-10)
    for j,g in enumerate(d['golden_cases']):
        bb=Bond(date(2025+g['years'],12,31),g['coupon']);p=bb.yield_price(s,g['yield_rate']);check('golden price '+str(j),abs(p-g['dirty'])<1e-9);check('golden yield '+str(j),abs(bb.ytm(s,p)-g['yield_rate'])<1e-10)
    check('duration matched',abs(d['portfolios']['Bullet']['duration']-d['portfolios']['Barbell']['duration'])<1e-10)
    hh=hedge(d['hedge']['before'],np.array(d['hedge_review_inputs']).T);check('hedge regenerated',np.max(abs(np.array(hh['units'])-d['hedge']['units']))<1e-7)
    cc=d['carry'];start=date.fromisoformat(cc['start']);end=date.fromisoformat(cc['end']);cb=carry_bridge(Bond(date.fromisoformat(cc['maturity']),.04),start,end,bootstrap(next(r['par'] for r in rows if r['date']==cc['start'])),bootstrap(next(r['par'] for r in rows if r['date']==cc['end'])),.04,2)
    check('carry rebuilt',abs(cb['net_pnl']-cc['net_pnl'])<1e-9);check('carry identity',abs(cb['reconciliation'])<1e-10)
    f=evaluate(rows)
    for m in f['metrics']:check('forecast '+m,abs(f['metrics'][m]['rmse_bp']-d['forecast']['metrics'][m]['rmse_bp'])<1e-9)
    check('nonoverlapping forecast windows',all(a['target_index']==b['origin_index'] for a,b in zip(f['origins'],f['origins'][1:])))
    for model,a in d['forecast']['allocation'].items():
        check('wealth '+model,abs(np.prod([1+x['net_return'] for x in a['periods']])-a['terminal_wealth'])<1e-12)
        check('constraints '+model,all(0<=x['long_weight']<=.5 and x['starting_duration']<=6+1e-9 for x in a['periods']))
    # Reprice the fixed cashflows for every interval and independently recover
    # each policy's weight decision. Do not validate returns by totals alone.
    for rec in f['origins']:
        ss=date.fromisoformat(rec['origin']);ee=date.fromisoformat(rec['target']);cs=bootstrap(rows[rec['origin_index']]['par']);ce=bootstrap(rows[rec['target_index']]['par'])
        bs=[Bond(add_months(ss,n*12),.04) for n in [2,10]];rr=[bond_risk(bb,ss,cs) for bb in bs]
        ps=[v['dirty'] for v in rr];cap=max(0,min(.5,(6-rr[0]['curve_duration'])/(rr[1]['curve_duration']-rr[0]['curve_duration'])))
        paid=[sum(x['amount'] for x in bb.cashflows(ss) if x['date']<=ee.isoformat()) for bb in bs];cl=[bb.curve_price(ee,ce) for bb in bs]
        realized=[(cc+pp-p0-2e-4*(p0+pp))/p0 for cc,pp,p0 in zip(paid,cl,ps)]
        for model,a in d['forecast']['allocation'].items():
            saved=next(x for x in a['periods'] if x['origin']==rec['origin'])
            if model=='fixed_mix':weight=cap
            else:
                pc=bootstrap(rec['predictions'][model]);pv=[bb.curve_price(ee,pc) for bb in bs]
                expected=[(cc+pp-p0-2e-4*(p0+pp))/p0 for cc,pp,p0 in zip(paid,pv,ps)]
                weight=cap if expected[1]>expected[0] else 0
            check('allocation choice '+model+'/'+rec['origin'],abs(weight-saved['long_weight'])<1e-12)
            check('allocation cash ledger '+model+'/'+rec['origin'],abs((1-weight)*realized[0]+weight*realized[1]-saved['net_return'])<1e-12)
    check('parallel hedge scalar neutral',abs(d['duration_hedge']['parallel_residual'])<1e-10)
    for path in sorted((R/'notebooks').glob('*.ipynb')):
        nb=json.loads(path.read_text());code=[c for c in nb['cells'] if c['cell_type']=='code'];check('executed '+path.name,all(c['execution_count'] and c['outputs'] and not any(o['output_type']=='error' for o in c['outputs']) for c in code))
    excel=json.loads((R/'artifacts/release/excel_checks.json').read_text());check('independent Excel receipt',excel['passed'] and len(excel['comparisons'])>=15)
    manifest=R/'release_manifest.json'
    if manifest.exists():
        for entry in json.loads(manifest.read_text())['files']:check('SHA '+entry['path'],digest(R/entry['path'])==entry['sha256'])
    print(json.dumps(dict(passed=True,checks=len(checks),run_id=d['run_id'],economic_result='No-change forecast remains aggregate-error reference')))
if __name__=='__main__':main()
