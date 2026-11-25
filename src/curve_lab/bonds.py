"""Regular semiannual hypothetical cash bonds; no stubs or payment adjustment.

Accrual and yield exponents: Actual/Actual ICMA for regular coupon periods.
Curve discount time: Actual/365 Fixed. Settlement-date cashflows are excluded.
"""
from dataclasses import dataclass
from datetime import date
import calendar
import math

def add_months(d, n, eom=False):
    m = d.year * 12 + d.month - 1 + n
    y, m = divmod(m, 12); m += 1
    end = calendar.monthrange(y, m)[1]
    return date(y, m, end if eom else min(d.day, end))

@dataclass(frozen=True)
class Bond:
    maturity: date
    coupon: float
    face: float = 100.0
    frequency: int = 2

    def __post_init__(self):
        if self.frequency != 2 or not math.isfinite(self.coupon) or self.coupon < 0 or not math.isfinite(self.face) or self.face <= 0:
            raise ValueError('Regular semiannual, nonnegative coupon, positive face required')

    def schedule(self, settlement):
        if settlement >= self.maturity:
            raise ValueError('Settlement must precede maturity')
        eom = self.maturity.day == calendar.monthrange(self.maturity.year,self.maturity.month)[1]
        n = 0; nxt = self.maturity; future = []
        while nxt > settlement:
            future.append(nxt); n += 1; nxt = add_months(self.maturity,-6*n,eom)
            if n > 200: raise ValueError('Maturity exceeds 100-year support')
        return nxt, list(reversed(future))

    def cashflows(self, settlement):
        prev, dates = self.schedule(settlement)
        fraction = (dates[0]-settlement).days/(dates[0]-prev).days
        return [dict(date=d.isoformat(),time=(d-settlement).days/365,
                     periods=fraction+i,amount=self.face*self.coupon/2+(self.face if d==self.maturity else 0))
                for i,d in enumerate(dates)]

    def accrued(self,settlement):
        prev,dates=self.schedule(settlement)
        return self.face*self.coupon/2*(settlement-prev).days/(dates[0]-prev).days

    def yield_price(self,settlement,y):
        if not math.isfinite(y) or y<=-2: raise ValueError('Yield must exceed -200%')
        return sum(x['amount']/(1+y/2)**x['periods'] for x in self.cashflows(settlement))

    def ytm(self,settlement,dirty):
        if not math.isfinite(dirty) or dirty<=0: raise ValueError('Positive dirty price required')
        lo,hi=-1.9,10.0
        if not self.yield_price(settlement,lo)>dirty>self.yield_price(settlement,hi):raise ValueError('Price outside solver bracket')
        for _ in range(100):
            mid=(lo+hi)/2
            if self.yield_price(settlement,mid)>dirty:lo=mid
            else:hi=mid
        return (lo+hi)/2

    def yield_risk(self,settlement,y):
        cf=self.cashflows(settlement); p=self.yield_price(settlement,y)
        mac=sum(x['periods']/2*x['amount']/(1+y/2)**x['periods'] for x in cf)/p
        mod=mac/(1+y/2)
        conv=sum(x['periods']*(x['periods']+1)/4*x['amount']/(1+y/2)**(x['periods']+2) for x in cf)/p
        return dict(macaulay=mac,modified=mod,convexity=conv,dv01=p*mod*1e-4)

    def curve_price(self,settlement,curve):
        return sum(x['amount']*float(curve.df(x['time'])) for x in self.cashflows(settlement))
