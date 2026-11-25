"""Finite-difference curve risk, fully repriced stress and constrained hedge."""
import numpy as np
from .curves import KEYS

def bond_risk(bond,settlement,curve):
    p=bond.curve_price(settlement,curve); bump=1e-4
    up=bond.curve_price(settlement,curve.bumped(np.full(len(KEYS),bump)))
    dn=bond.curve_price(settlement,curve.bumped(np.full(len(KEYS),-bump)))
    k=[]
    for i in range(len(KEYS)):
        v=np.zeros(len(KEYS));v[i]=bump
        k.append((bond.curve_price(settlement,curve.bumped(-v))-bond.curve_price(settlement,curve.bumped(v)))/2)
    return dict(dirty=p,parallel_dv01=(dn-up)/2,curve_duration=(dn-up)/(2*bump*p),curve_convexity=(dn+up-2*p)/(p*bump*bump),key_dv01=k,key_sum_residual=sum(k)-(dn-up)/2)

def hedge(target,hedges,max_units=20000):
    """Minimise six-bucket squared USD/bp residual; bounds ±face-100 units.

    Zero initial value is financed through cash. No futures or CTD assumptions.
    """
    a=np.asarray(hedges,dtype=float).T;b=np.asarray(target,dtype=float)
    x=np.clip(np.linalg.lstsq(a,-b,rcond=None)[0],-max_units,max_units)
    for iteration in range(2000):
        old=x.copy()
        for j in range(len(x)):
            residual=b+a@x-a[:,j]*x[j]
            x[j]=np.clip(-a[:,j]@residual/(a[:,j]@a[:,j]),-max_units,max_units)
        if np.max(abs(x-old))<1e-9:break
    return dict(units=x.tolist(),before=b.tolist(),after=(b+a@x).tolist(),
                before_norm=float(np.linalg.norm(b)),after_norm=float(np.linalg.norm(b+a@x)),
                success=bool(iteration<1999),at_bound=bool(np.any(abs(x)>=max_units-1e-4)))

def carry_bridge(bond,start,end,curve0,curve1,financing=.035,cost_bp=2):
    """Exact ordered bridge. Coupons held as non-interest-bearing cash.

    Carry: cashflows + aged bond discounted at initial constant YTM minus start.
    Roll: initial fixed tenor curve minus aged constant-YTM valuation.
    Move: terminal curve minus initial fixed tenor curve. No double-counted AI.
    """
    if end<=start or end>=bond.maturity:raise ValueError('Horizon must precede maturity and follow start')
    p0=bond.curve_price(start,curve0);y=bond.ytm(start,p0)
    paid=sum(x['amount'] for x in bond.cashflows(start) if x['date']<=end.isoformat())
    py=bond.yield_price(end,y);proll=bond.curve_price(end,curve0);p1=bond.curve_price(end,curve1)
    elapsed=(end-start).days/365
    finance=-p0*financing*elapsed;cost=-(p0+p1)*cost_bp/10000
    pieces=dict(carry=paid+py-p0,roll=proll-py,curve_move=p1-proll,financing=finance,transaction_cost=cost)
    net=paid+p1-p0+finance+cost
    return dict(start_dirty=p0,end_dirty=p1,coupons=paid,elapsed=elapsed,financing_rate=financing,cost_bp=cost_bp,
                **pieces,net_pnl=net,net_return=net/p0,reconciliation=sum(pieces.values())-net)
