"""Educational curves calibrated to idealised par instruments, not actual CUSIPs."""
import numpy as np

TENORS=np.array([.5,1,2,3,5,7,10,20,30.])
KEYS=np.array([.5,2,5,10,20,30.])

class Curve:
    def __init__(self,times,discounts,method='log_linear'):
        self.t=np.asarray(times,dtype=float);self.d=np.asarray(discounts,dtype=float);self.method=method
        if len(self.t)!=len(self.d) or not np.all(np.diff(self.t)>0) or self.t[0]!=0 or self.d[0]!=1 or not np.all(np.isfinite(self.d)) or np.any(self.d<=0):
            raise ValueError('Ordered times, positive finite discount factors and D(0)=1 required')
        if method not in ['log_linear','linear_df']:raise ValueError('Unknown interpolation')

    def df(self,t):
        a=np.asarray(t,dtype=float)
        if np.any(~np.isfinite(a)) or np.any(a<0) or np.any(a>self.t[-1]+1e-9):raise ValueError('No extrapolation beyond curve support')
        return np.interp(a,self.t,self.d) if self.method=='linear_df' else np.exp(np.interp(a,self.t,np.log(self.d)))

    def zero(self,t):
        a=np.asarray(t,dtype=float)
        if np.any(a<=0): raise ValueError('Positive zero-rate tenor required')
        return -np.log(self.df(a))/a

    def forward(self,a,b):
        if b<=a:raise ValueError('Forward end must exceed start')
        return np.log(self.df(a)/self.df(b))/(b-a)

    def bumped(self,shifts,keys=KEYS):
        shifts=np.asarray(shifts,dtype=float)
        if len(shifts)!=len(keys) or not np.all(np.isfinite(shifts)):raise ValueError('Invalid key-rate shifts')
        return ShiftedCurve(self,keys,shifts)

class ShiftedCurve(Curve):
    """Apply continuous-zero hats at each cashflow time, not interpolated bump PVs."""
    def __init__(self,base,keys,shifts):
        self.base=base;self.keys=np.asarray(keys);self.shifts=np.asarray(shifts)
        self.t=base.t;self.method=base.method;self.d=self.df(self.t)
    def df(self,t):
        a=np.asarray(t,dtype=float)
        return self.base.df(a)*np.exp(-a*np.interp(a,self.keys,self.shifts))

def bootstrap(par,tenors=TENORS,method='log_linear'):
    par=np.asarray(par,dtype=float); tenors=np.asarray(tenors,dtype=float)
    if len(par)!=len(tenors) or not np.all(np.isfinite(par)) or np.any(par<=-1) or np.any(par>1) or tenors[0]!=.5 or np.any(np.diff(tenors)<=0):
        raise ValueError('Complete decimal par grid starting at 6 months required')
    grid=np.arange(.5,tenors[-1]+.25,.5)
    coupons=np.interp(grid,tenors,par); discounts=[1.];total=0
    for c in coupons:
        d=(1-c/2*total)/(1+c/2)
        if d<=0 or not np.isfinite(d):raise ValueError('Bootstrap generated nonpositive discount factor')
        discounts.append(d);total+=d
    return Curve(np.r_[0,grid],discounts,method)

def par_rate(curve,t):
    if abs(t*2-round(t*2))>1e-10 or t<=0:raise ValueError('Semiannual grid tenor required')
    grid=np.arange(.5,t+.25,.5)
    return 2*(1-float(curve.df(t)))/float(np.sum(curve.df(grid)))

def ns_zero(t,b):
    t=np.asarray(t);x=t/b[3];l=-np.expm1(-x)/x
    return b[0]+b[1]*l+b[2]*(l-np.exp(-x))

def fit_nelson_siegel(par,tenors=TENORS):
    grid=np.arange(.5,30.25,.5)
    def residual(b):
        d=np.exp(-grid*ns_zero(grid,b));cs=np.cumsum(d)
        idx=(tenors*2-1).astype(int)
        return (2*(1-d[idx])/cs[idx]-par)*10000
    # Damped Gauss-Newton with multistart tau, fitted to par residuals in bp.
    results=[]
    for tau in [1.,3.,7.]:
        b=np.array([float(par[-1]),float(par[0]-par[-1]),0.,tau]);lam=1e-3
        for iteration in range(150):
            r=residual(b);steps=np.array([1e-6,1e-6,1e-6,1e-4])
            jac=np.column_stack([(residual(b+np.eye(4)[j]*steps[j])-r)/steps[j] for j in range(4)])
            delta=np.linalg.solve(jac.T@jac+lam*np.eye(4),-jac.T@r)
            trial=np.clip(b+delta,[-.1,-.3,-.3,.1],[.2,.3,.3,15])
            if np.sum(residual(trial)**2)<np.sum(r*r):
                if np.linalg.norm(trial-b)<1e-9:b=trial;break
                b=trial;lam=max(1e-9,lam/3)
            else:lam=min(1e10,lam*10)
        results.append((float(np.sum(residual(b)**2)),b,iteration))
    _,b,it=min(results,key=lambda x:x[0]);res=residual(b)
    curve=Curve(np.r_[0,grid],np.r_[1,np.exp(-grid*ns_zero(grid,b))])
    return curve,dict(parameters=b.tolist(),residual_bp=res.tolist(),rmse_bp=float(np.sqrt(np.mean(res**2))),success=bool(np.all(np.isfinite(res))),iterations=it+1,solver='Damped Gauss-Newton, three fixed starting taus')
