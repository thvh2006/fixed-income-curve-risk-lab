"""Generate standard review notebooks; execute separately with run_notebooks.py."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
SETUP="""import sys,json
from pathlib import Path
from datetime import date
import numpy as np
R=Path.cwd()
if R.name=='notebooks':R=R.parent
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(R/'scripts'))
from curve_lab.data import load_history
from curve_lab.bonds import Bond
from curve_lab.curves import bootstrap,par_rate,TENORS,KEYS,fit_nelson_siegel
from curve_lab.risk import bond_risk,hedge,carry_bridge
from curve_lab.forecast import predict,evaluate
from review_display import table,figure
if 'display_bundle' not in globals():
    from IPython.display import display
    def display_bundle(bundle):display(bundle,raw=True)
D=json.loads((R/'artifacts/release/research.json').read_text());rows,receipts=load_history(R)
print('Run',D['run_id'],'| source through',D['as_of'],'| hypothetical bond valuations')
"""
BOOKS=[
 ('01_curve_data_and_conventions','Curve data and conventions','Which inputs are observed and complete?',[
  ('Audit the annual source files',"display_bundle(table(['Year','Rows','Source SHA-256'],[[r['year'],sum(x['date'].startswith(str(r['year'])) for x in rows),r['sha256']] for r in receipts]));assert len(rows)==499;assert len({r['date'] for r in rows})==499"),
  ('Inspect observed and derived rates',"display_bundle(table(['Tenor','Observed par','Model zero'],zip(TENORS,rows[-1]['par'],D['history'][-1]['zero'])));display_bundle(figure('curve'))"),
  ('Make convention boundaries visible',"display_bundle(table(['Convention','Choice'],D['config']['conventions'].items()));assert D['coverage']['missing_core']==0")
 ],'The nine core tenors are complete in this snapshot. Short-tenor series outside that grid are retained raw and not imputed. Treasury par rates are observed; all discount curves and bond prices are derived. No vintage archive is available.'),
 ('02_bond_cashflows_and_pricing','Bond cash flows and pricing','Do dated cash flows, accrued interest and YTM reconcile?',[
  ('Generate the complete dated schedule',"b=Bond(date(2030,12,31),.04);s=date(2025,12,31);c=bootstrap(rows[-1]['par']);cf=b.cashflows(s);display_bundle(table(['Payment','ACT/365 time','Yield periods','Cashflow'],[[x['date'],x['time'],x['periods'],x['amount']] for x in cf]));assert len(cf)==10"),
  ('Solve the price-yield round trip',"p=b.curve_price(s,c);y=b.ytm(s,p);ai=b.accrued(s);display_bundle(table(['Item','Value'],[['Dirty',p],['Accrued',ai],['Clean',p-ai],['YTM',y],['Round-trip difference',b.yield_price(s,y)-p]]));assert abs(b.yield_price(s,y)-p)<1e-9"),
  ('Challenge a mid-period date and coupon date',"inside=date(2026,2,28);a=b.accrued(inside);display_bundle(table(['Case','Accrued'],[['28 Feb 2026',a],['30 Jun 2026',b.accrued(date(2026,6,30))]]));assert abs(a-2*59/181)<1e-12;assert b.accrued(date(2026,6,30))==0;assert abs(Bond(date(2030,12,31),0).yield_price(s,.05)-100/1.025**10)<1e-10")
 ],'Clean plus accrued equals dirty. Actual/Actual coupon periods differ deliberately from Actual/365 curve time. The schedule is regular and unadjusted, with no actual-security or stub-convention claim.'),
 ('03_curve_bootstrap_and_fit','Curve bootstrap and fit','Does the curve reprice its idealised inputs, and what does fitting change?',[
  ('Rebuild the educational bootstrap',"c=bootstrap(rows[-1]['par']);res=[(par_rate(c,t)-p)*10000 for t,p in zip(TENORS,rows[-1]['par'])];display_bundle(table(['Tenor','Input par','Repriced par','Residual bp'],[[t,p,par_rate(c,t),r] for t,p,r in zip(TENORS,rows[-1]['par'],res)]));assert max(abs(x) for x in res)<1e-8"),
  ('Fit the parametric challenger',"ns,fit=fit_nelson_siegel(np.array(rows[-1]['par']));display_bundle(table(['Parameter','Value'],zip(['Level','Slope','Curvature','Tau'],fit['parameters'])));print('Par RMSE bp:',fit['rmse_bp']);display_bundle(figure('residuals'))"),
  ('Bootstrap three periods by hand',"coupons=[.04,.042,.044];dd=[]\nfor cp in coupons:dd.append((1-cp/2*sum(dd))/(1+cp/2))\ndisplay_bundle(table(['Half-year period','Coupon','Discount'],[[j+1,cp,d] for j,(cp,d) in enumerate(zip(coupons,dd))]));assert abs(dd[0]-1/1.02)<1e-12")
 ],'Exact idealised repricing is a calibration identity. Linear and log-discount interpolation share nodes but differ off grid. The Nelson-Siegel residual is retained; no fit improvement is treated as security-price validation.'),
 ('04_duration_convexity_keyrates','Duration, convexity and key rates','Which perturbation does each risk number measure?',[
  ('Compare analytic and finite-difference yield risk',"s=date(2025,12,31);b=Bond(date(2030,12,31),.04);c=bootstrap(rows[-1]['par']);p=b.curve_price(s,c);y=b.ytm(s,p);r=b.yield_risk(s,y);fd=(b.yield_price(s,y-1e-5)-b.yield_price(s,y+1e-5))/(2e-5*p);display_bundle(table(['Measure','Value'],list(r.items())+[['FD modified duration',fd]]));assert abs(fd-r['modified'])<1e-7"),
  ('Reprice each key-rate bump',"kr=bond_risk(b,s,c);display_bundle(table(['Key tenor','DV01 per 100'],zip(KEYS,kr['key_dv01'])));print('Sum minus parallel DV01',kr['key_sum_residual']);display_bundle(figure('keyrates'));assert abs(kr['key_sum_residual'])<1e-7"),
  ('Compare small and large shocks',"display_bundle(table(['Shock bp','Full P&L','Duration','Duration + convexity'],[[bp,b.curve_price(s,c.bumped(np.full(6,bp/10000)))-p,-p*kr['curve_duration']*bp/10000,p*(-kr['curve_duration']*bp/10000+.5*kr['curve_convexity']*(bp/10000)**2)] for bp in [-200,-100,1,100,200]]))")
 ],'Yield and curve duration are distinct. Zero-rate hats partition unity and central finite-bump key DV01 aggregates approximately. Full repricing remains the stress reference.'),
 ('05_portfolio_stress_and_hedging','Portfolio stress and hedging','Does matching parallel duration eliminate nonparallel risk?',[
  ('Read equal-capital portfolio exposures',"display_bundle(table(['Portfolio','Capital','Duration','DV01'],[[n,p['capital'],p['duration'],p['dv01']] for n,p in D['portfolios'].items()]));assert abs(D['portfolios']['Bullet']['duration']-D['portfolios']['Barbell']['duration'])<1e-10"),
  ('Independently resolve the bounded hedge',"h=hedge(D['hedge']['before'],np.array(D['hedge_review_inputs']).T);display_bundle(table(['Key','Before','After'],zip(KEYS,h['before'],h['after'])));assert np.max(abs(np.array(h['units'])-D['hedge']['units']))<1e-7;assert h['after_norm']<h['before_norm'];display_bundle(figure('hedge'))"),
  ('Challenge full repricing after the hedge',"display_bundle(table(['Scenario','Bullet','Barbell','Hedged bullet'],[[s,D['portfolios']['Bullet']['stress'][s],D['portfolios']['Barbell']['stress'][s],D['hedge']['stress_after'][s]] for s in D['shocks']]));print('Hedge one-way cost USD',D['hedge']['one_way_cost_usd'])")
 ],'Two hedge instruments cannot span six independent buckets. The saved solution reduces an explicit L2 objective and leaves residual twist risk. Instantaneous stress P&L excludes overlay costs and future financing.'),
 ('06_carry_rolldown_and_returns','Carry, roll-down and returns','Can every dollar of a fixed holding be reconciled?',[
  ('Rebuild the fixed holding bridge',"start=date(2025,1,2);end=date(2025,7,2);c0=bootstrap(next(r['par'] for r in rows if r['date']==str(start)));c1=bootstrap(next(r['par'] for r in rows if r['date']==str(end)));b=Bond(date(2030,1,2),.04);r=carry_bridge(b,start,end,c0,c1,.04,2);display_bundle(table(['Component','Per 100 face'],[[k,r[k]] for k in ['carry','roll','curve_move','financing','transaction_cost','net_pnl','reconciliation']]));assert abs(r['reconciliation'])<1e-10"),
  ('Check the cash identity separately',"ledger=r['coupons']+r['end_dirty']-r['start_dirty']+r['financing']+r['transaction_cost'];print('Coupon cash',r['coupons'],'Ledger net',ledger);assert r['coupons']==2;assert abs(ledger-r['net_pnl'])<1e-10"),
  ('Challenge financing and round-trip costs',"display_bundle(table(['Financing','Cost bp per side','Net P&L'],[[f,cost,carry_bridge(b,start,end,c0,c1,f,cost)['net_pnl']] for f,cost in [(0,0),(.04,2),(.08,10)]]))")
 ],'Coupons and accrued interest are not double counted. The ordered bridge is descriptive, and its labels depend on the chosen sequence. Constant-maturity rebalancing requires a separate trade and cost ledger.'),
 ('07_curve_factor_forecasting','Curve factor forecasting','Can either challenger improve a simple rate forecast or its decision?',[
  ('Inspect every candidate error',"display_bundle(table(['Model','RMSE bp','MAE bp','Origins'],[[n,m['rmse_bp'],m['mae_bp'],m['origins']] for n,m in D['forecast']['metrics'].items()]));display_bundle(figure('forecast'))"),
  ('Rebuild the first forecast from eligible history',"r=D['forecast']['origins'][0];y=np.array([x['par'] for x in rows]);pred,fit=predict(y[:r['origin_index']+1]);assert fit['max_target_index']==r['origin_index'];display_bundle(table(['Model','Reconstruction max absolute error'],[[n,float(np.max(abs(pred[n]-r['predictions'][n])))] for n in pred]));assert max(np.max(abs(pred[n]-r['predictions'][n])) for n in pred)<1e-12"),
  ('Inspect costed hypothetical decision value',"display_bundle(table(['Policy','Terminal wealth','Mean long weight','Worst period'],[[n,a['terminal_wealth'],a['mean_long_weight'],a['worst_period']] for n,a in D['forecast']['allocation'].items()]));display_bundle(figure('allocation'));assert all(x['starting_duration']<=6+1e-9 for a in D['forecast']['allocation'].values() for x in a['periods'])")
 ],'No-change has the lowest aggregate forecast RMSE. The allocation illustration is model-implied, not a traded bond return series. All policies remain visible and none is promoted from this short retrospective sample.'),
 ('08_validation_and_monitoring','Validation and monitoring','What fails explicitly, and what survives a source failure?',[
  ('Audit all historical calibration identities',"errs=[]\nfor row in rows:\n c=bootstrap(row['par']);errs.extend(abs(par_rate(c,t)-p)*10000 for t,p in zip(TENORS,row['par']))\nprint('Curves',len(rows),'input repricing checks',len(errs),'max error bp',max(errs));assert max(errs)<1e-8"),
  ('Challenge invalid data and unsupported tenor',"failures=[]\nfor name,fn in [('missing tenor',lambda:bootstrap([float('nan')]*9)),('extrapolation',lambda:bootstrap(rows[-1]['par']).df(31)),('settle at maturity',lambda:Bond(date(2030,1,1),.04).cashflows(date(2030,1,1)))]:\n try:fn()\n except ValueError:failures.append(name)\nassert len(failures)==3;display_bundle(table(['Rejected case'],[[x] for x in failures]))"),
  ('Read release and operational boundaries',"print('Research is frozen:',D['as_of']);print('Market refresh is separate; failed refresh retains last-known-good.');print('Source vintages absent; native Jupyter kernel not claimed by sequential executor.');display_bundle(table(['Source','SHA-256'],[[r['path'],r['sha256']] for r in receipts]))")
 ],'Validation confirms stated mathematical and failure contracts. Source correctness, historical availability and actual-security execution remain separate evidence requirements. See docs/runbook.md for refresh and rollback steps.')
]
def md(text):return dict(cell_type='markdown',metadata={},source=text.splitlines(True))
def code(text):return dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=text.splitlines(True))
for name,title,question,sections,conclusion in BOOKS:
    cells=[md('# '+title+'\n\nResearch question: '+question+'\n\nInputs: frozen Treasury 2024–2025 CSVs. Rates are decimals, prices per 100 face. Release 1.0.0. No live signal.'),code(SETUP)]
    for heading,text in sections:cells.extend([md('## '+heading),code(text)])
    cells.append(md('## Interpretation\n\n'+conclusion+'\n\nCanonical evidence: `artifacts/release/research.json`; source receipts: `data/manifests/sources.json`.'))
    nb=dict(cells=cells,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3',language='python'),language_info=dict(name='python',version='3.12'),execution_method='Sequential Python executor; rich display bundles; native Jupyter kernel not claimed'),nbformat=4,nbformat_minor=5)
    for j,c in enumerate(cells):c['id']=name[:2]+'-'+str(j)
    (R/'notebooks'/(name+'.ipynb')).write_text(json.dumps(nb,indent=2)+'\n')
print('Generated eight independent notebooks')
