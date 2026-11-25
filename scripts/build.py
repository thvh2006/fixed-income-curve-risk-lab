"""Rebuild all mathematical research artifacts from the frozen Treasury CSVs."""
import sys,json,hashlib,os,platform
from pathlib import Path
from datetime import date,datetime,timezone
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import numpy as np
from curve_lab.data import load_history,digest
from curve_lab.bonds import Bond,add_months
from curve_lab.curves import bootstrap,TENORS,KEYS,par_rate,fit_nelson_siegel,Curve
from curve_lab.risk import bond_risk,hedge,carry_bridge
from curve_lab.forecast import evaluate

def plain(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(str(type(x)))
def save(path,obj):
    p=R/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,default=plain,allow_nan=False)+'\n')

def main():
    config=json.loads((R/'configs/research.json').read_text());rows,receipts=load_history(R)
    code_hash=hashlib.sha256(''.join(str(p.relative_to(R))+digest(p) for p in sorted((R/'src').rglob('*.py'))+[Path(__file__).resolve()]).encode()).hexdigest()
    config_hash=digest(R/'configs/research.json')
    run='p4-'+hashlib.sha256((''.join(r['sha256'] for r in receipts)+config_hash+code_hash).encode()).hexdigest()[:12]
    curves=[];max_residual=0
    for row in rows:
        c=bootstrap(row['par']);res=[(par_rate(c,t)-p)*10000 for t,p in zip(TENORS,row['par'])]
        max_residual=max(max_residual,max(abs(x) for x in res))
        curves.append(dict(**row,discounts=c.d.tolist(),zero=c.zero(TENORS).tolist(),repricing_bp=res))
    last=curves[-1];base=bootstrap(last['par']);smooth=bootstrap(last['par'],method='linear_df');ns,fit=fit_nelson_siegel(np.array(last['par']))
    settle=date.fromisoformat(config['settlement']);bond=Bond(date(2030,12,31),.04)
    cf=bond.cashflows(settle);p=bond.curve_price(settle,base);y=bond.ytm(settle,p)
    br=bond_risk(bond,settle,base)
    prices=dict(dirty=p,accrued=bond.accrued(settle),clean=p-bond.accrued(settle),ytm=y,**bond.yield_risk(settle,y))
    portfolio={}
    # Equal market capital, with barbell duration matched to the five-year bullet.
    inst={str(n):Bond(add_months(settle,12*n,True),.04) for n in [1,2,3,4,5,7,10,20]}
    risks={n:bond_risk(b,settle,base) for n,b in inst.items()}
    w10=(risks['5']['curve_duration']-risks['2']['curve_duration'])/(risks['10']['curve_duration']-risks['2']['curve_duration'])
    weights={'Bullet':{'5':1},'Barbell':{'2':1-w10,'10':w10},'Ladder':{str(n):.2 for n in [1,2,3,4,5]}}
    shocks={'Parallel +100':np.full(6,.01),'Parallel -100':np.full(6,-.01),'Parallel +200':np.full(6,.02),
            'Steepener':np.array([-.005,-.005,0,.005,.01,.01]),'Flattener':np.array([.005,.005,0,-.005,-.01,-.01]),
            'Butterfly':np.array([-.0025,-.0025,.005,.005,-.0025,-.0025])}
    first25=next(r for r in curves if r['date']>='2025-01-01')
    # Replay the observed 2025 par-rate change, converted to educational zero shifts.
    hist=bootstrap(first25['par']);shocks['2025 curve change replay']=base.zero(KEYS)-hist.zero(KEYS)
    for name,ws in weights.items():
        units={n:config['capital']*w/risks[n]['dirty'] for n,w in ws.items()}
        key=sum((units[n]*np.array(risks[n]['key_dv01']) for n in ws),start=np.zeros(6))
        d=sum(units[n]*risks[n]['parallel_dv01'] for n in ws)
        convex=sum(units[n]*risks[n]['dirty']*risks[n]['curve_convexity'] for n in ws)/config['capital']
        stress={s:sum(units[n]*(inst[n].curve_price(settle,base.bumped(v))-risks[n]['dirty']) for n in ws) for s,v in shocks.items()}
        portfolio[name]=dict(weights=ws,units=units,capital=config['capital'],duration=d/config['capital']/1e-4,dv01=d,convexity=convex,key_dv01=key.tolist(),stress=stress)
    target=np.array(portfolio['Bullet']['key_dv01']);hedge_names=['2','5','10'];h=hedge(target,[risks[n]['key_dv01'] for n in hedge_names])
    # Independent full repricing, cash-financed overlay, including model transaction cost.
    h['instruments']=hedge_names;h['initial_cash']=-sum(u*risks[n]['dirty'] for n,u in zip(hedge_names,h['units']))
    h['gross_notional']=sum(abs(u)*risks[n]['dirty'] for n,u in zip(hedge_names,h['units']))
    h['stress_after']={s:portfolio['Bullet']['stress'][s]+sum(u*(inst[n].curve_price(settle,base.bumped(v))-risks[n]['dirty']) for n,u in zip(hedge_names,h['units'])) for s,v in shocks.items()}
    # Exclude same-bond hedge in the useful cross-maturity comparison.
    h2=hedge(target,[risks[n]['key_dv01'] for n in ['2','10']]);h2['instruments']=['2','10']
    h2['initial_cash']=-sum(u*risks[n]['dirty'] for n,u in zip(h2['instruments'],h2['units']))
    h2['gross_notional']=sum(abs(u)*risks[n]['dirty'] for n,u in zip(h2['instruments'],h2['units']))
    h2['stress_after']={s:portfolio['Bullet']['stress'][s]+sum(u*(inst[n].curve_price(settle,base.bumped(v))-risks[n]['dirty']) for n,u in zip(h2['instruments'],h2['units'])) for s,v in shocks.items()}
    h2['one_way_cost_usd']=h2['gross_notional']*2/10000
    # A conventional one-instrument parallel-DV01 hedge is a useful counterexample:
    # near-zero scalar duration risk can coexist with a larger key-rate norm.
    du=-portfolio['Bullet']['dv01']/risks['10']['parallel_dv01']
    dv=target+du*np.array(risks['10']['key_dv01'])
    duration_hedge=dict(instrument='10',units=du,parallel_residual=portfolio['Bullet']['dv01']+du*risks['10']['parallel_dv01'],
                        key_dv01=dv.tolist(),key_norm=float(np.linalg.norm(dv)),initial_cash=-du*risks['10']['dirty'],
                        one_way_cost_usd=abs(du)*risks['10']['dirty']*2/10000,
                        stress_after={s:portfolio['Bullet']['stress'][s]+du*(inst['10'].curve_price(settle,base.bumped(v))-risks['10']['dirty']) for s,v in shocks.items()})
    start=date(2025,1,2);end=date(2025,7,2);bcarry=Bond(date(2030,1,2),.04)
    c0=bootstrap(next(r['par'] for r in rows if r['date']==start.isoformat()));c1=bootstrap(next(r['par'] for r in rows if r['date']==end.isoformat()))
    bridge=carry_bridge(bcarry,start,end,c0,c1,.04,2)
    forecast=evaluate(rows)
    # Constant-maturity decision experiment. Fully funded, 2/10-year sleeves,
    # maximum 50% in the long sleeve and six-year starting duration cap.
    # Every five observations both legs are liquidated and rebuilt; 2 bp/side.
    # This is a model-implied illustration, not observed bond total returns.
    allocation={m:[] for m in ['fixed_mix','no_change','pca_ar','ridge_change']}
    for record in forecast['origins']:
        i=record['origin_index'];j=record['target_index'];s=date.fromisoformat(record['origin']);e=date.fromisoformat(record['target'])
        cstart=bootstrap(rows[i]['par']);cend=bootstrap(rows[j]['par']);bonds=[Bond(add_months(s,12*n),.04) for n in [2,10]]
        rs=[bond_risk(b,s,cstart) for b in bonds];ps=[r['dirty'] for r in rs]
        cap=max(0,min(.5,(6-rs[0]['curve_duration'])/(rs[1]['curve_duration']-rs[0]['curve_duration'])))
        paid=[sum(x['amount'] for x in b.cashflows(s) if x['date']<=e.isoformat()) for b in bonds]
        close=[b.curve_price(e,cend) for b in bonds]
        realised=[(q+cc-pp-2e-4*(pp+cc))/pp for q,cc,pp in zip(paid,close,ps)]
        for model in allocation:
            if model=='fixed_mix':w=cap
            else:
                pc=bootstrap(record['predictions'][model]);projected=[b.curve_price(e,pc) for b in bonds]
                er=[(q+cc-pp-2e-4*(pp+cc))/pp for q,cc,pp in zip(paid,projected,ps)]
                w=cap if er[1]>er[0] else 0
            rr=(1-w)*realised[0]+w*realised[1]
            allocation[model].append(dict(origin=record['origin'],target=record['target'],long_weight=w,starting_duration=(1-w)*rs[0]['curve_duration']+w*rs[1]['curve_duration'],net_return=rr))
    forecast['allocation']={m:dict(periods=records,terminal_wealth=float(np.prod([1+r['net_return'] for r in records])),mean_long_weight=float(np.mean([r['long_weight'] for r in records])),worst_period=min(r['net_return'] for r in records)) for m,records in allocation.items()}
    forecast['allocation_assumptions']='Model-implied constant-maturity 2/10-year sleeves; <=50% long sleeve, <=6-year starting curve duration, fully funded; complete liquidation/rebuild every 5 source observations; 2 bp each entry/exit; coupon cash earns zero; no bid/ask quotes, taxes or market liquidity.'
    methods=[]
    for name,c in [('Log discount linear',base),('Linear discount',smooth),('Nelson-Siegel',ns)]:
        res=[(par_rate(c,t)-p)*10000 for t,p in zip(TENORS,last['par'])]
        methods.append(dict(method=name,rmse_bp=float(np.sqrt(np.mean(np.array(res)**2))),residual_bp=res,
                            bond_dirty=bond.curve_price(settle,c),zero=c.zero(TENORS).tolist(),discounts=c.d.tolist()))
    grid=np.arange(.5,30.01,.5)
    golden=[]
    for cp in [0,.04,.08]:
        for years in [1,5,10]:
            b=Bond(add_months(settle,years*12,True),cp)
            for yy in [-.01,0,.04,.10]:
                pp=b.yield_price(settle,yy);golden.append(dict(coupon=cp,years=years,yield_rate=yy,dirty=pp,ytm=b.ytm(settle,pp),**b.yield_risk(settle,yy)))
    curve_golden=[]
    for cp in [0,.04,.06]:
        for ss in [settle,date(2026,2,28),date(2026,6,30)]:
            bb=Bond(date(2030,12,31),cp)
            for shock in [-100,0,100]:
                cc=base.bumped(np.full(6,shock/10000));pp=bb.curve_price(ss,cc)
                curve_golden.append(dict(settlement=ss.isoformat(),maturity=bb.maturity.isoformat(),coupon=cp,shock_bp=shock,dirty=pp,accrued=bb.accrued(ss),ytm=bb.ytm(ss,pp)))
    out=dict(version='1.0.0',run_id=run,code_sha256=code_hash,config_hash=config_hash,environment=dict(python=platform.python_version(),numpy=np.__version__),config=config,source_receipts=receipts,as_of=last['date'],published_at=datetime.now(timezone.utc).isoformat(),
             evidence_type='Observed Treasury par rates; model-implied hypothetical cash bonds',
             coverage=dict(rows=len(rows),start=rows[0]['date'],end=rows[-1]['date'],years={str(y):sum(r['date'].startswith(str(y)) for r in rows) for y in [2024,2025]},core_tenors=len(TENORS),missing_core=0),
             history=curves,curve=dict(times=base.t.tolist(),discounts=base.d.tolist(),grid=grid.tolist(),zero=base.zero(grid).tolist(),forward=[base.forward(float(t-.5),float(t)) for t in grid],max_repricing_bp=max_residual),
             bond=dict(settlement=settle.isoformat(),maturity=bond.maturity.isoformat(),coupon=bond.coupon,cashflows=cf,**prices,curve_risk=br),
             methods=methods,nelson_siegel_fit=fit,portfolios=portfolio,hedge=h2,duration_hedge=duration_hedge,same_instrument_control=h,shocks={k:v.tolist() for k,v in shocks.items()},
             hedge_review_inputs=np.array([risks[n]['key_dv01'] for n in ['2','10']]).T.tolist(),
             carry=dict(start=start.isoformat(),end=end.isoformat(),maturity=bcarry.maturity.isoformat(),coupon=.04,**bridge),forecast=forecast,golden_cases=golden,curve_golden_cases=curve_golden)
    save('artifacts/release/research.json',out)
    save('data/manifests/sources.json',dict(retrieved_at=out['published_at'],files=receipts,rights='US federal government interest-rate facts; attribution retained. No seals, images or external security quotes redistributed.',availability='Historical files retrieved in November 2026; no historical vintages. Source usually published by 18:00 America/New_York, may be delayed. Forecast study is retrospective.'))
    print(json.dumps(dict(run_id=run,rows=len(rows),repricing_max_bp=max_residual,bond_dirty=p,forecast=forecast['metrics'],hedge_residual=h2['after_norm'])))

if __name__=='__main__':main()
