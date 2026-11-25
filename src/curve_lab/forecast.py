"""Retrospective five-observation-ahead study; train-only PCA and fixed ridge.

Origins start in 2025; next origin is five source observations later.
No-change is the baseline. Model settings fixed in configs/research.json.
"""
import numpy as np

def predict(history):
    y=np.asarray(history,dtype=float)
    if len(y)<180 or y.ndim!=2 or not np.all(np.isfinite(y)):raise ValueError('180 complete prior observations required')
    mean=y.mean(axis=0);z=y-mean
    _,s,vt=np.linalg.svd(z,full_matrices=False);v=vt[:3].T;scores=z@v
    x=np.c_[np.ones(len(y)-5),scores[:-5]];target=scores[5:]
    beta=np.linalg.lstsq(x,target,rcond=None)[0]
    pca=mean+np.r_[1,scores[-1]]@beta@v.T
    # Three lagged 5-observation differences. All training targets mature by origin.
    def features(i):return np.r_[y[i]-y[i-5],y[i-5]-y[i-10],y[i-10]-y[i-15]]
    ids=list(range(15,len(y)-5));xx=np.array([features(i) for i in ids]);yy=np.array([y[i+5]-y[i] for i in ids])
    xm=xx.mean(0);ym=yy.mean(0);scale=xx.std(0);scale[scale<1e-10]=1
    a=(xx-xm)/scale;b=yy-ym
    coef=np.linalg.solve(a.T@a+100*np.eye(a.shape[1]),a.T@b)
    ridge=y[-1]+ym+(features(len(y)-1)-xm)/scale@coef
    return dict(no_change=y[-1],pca_ar=pca,ridge_change=ridge),dict(train_rows=len(y),max_target_index=len(y)-1,pca_variance=(s[:3]**2/np.sum(s*s)).tolist())

def evaluate(rows):
    y=np.array([r['par'] for r in rows]);records=[]
    start=next(i for i,r in enumerate(rows) if r['date']>='2025-01-01')
    for i in range(start,len(y)-5,5):
        preds,fit=predict(y[:i+1]);actual=y[i+5]
        records.append(dict(origin=rows[i]['date'],target=rows[i+5]['date'],origin_index=i,target_index=i+5,fit=fit,
                            actual=actual.tolist(),predictions={k:v.tolist() for k,v in preds.items()},
                            squared_error_bp={k:float(np.mean(((v-actual)*10000)**2)) for k,v in preds.items()}))
    metrics={}
    for m in ['no_change','pca_ar','ridge_change']:
        errors=np.array([(np.array(r['predictions'][m])-r['actual'])*10000 for r in records])
        metrics[m]=dict(rmse_bp=float(np.sqrt(np.mean(errors**2))),mae_bp=float(np.mean(abs(errors))),tenor_rmse_bp=np.sqrt(np.mean(errors**2,axis=0)).tolist(),origins=len(records))
    return dict(horizon_observations=5,origins=records,metrics=metrics,protocol='Retrospective pre-specified comparison, not an untouched or prospective test')
