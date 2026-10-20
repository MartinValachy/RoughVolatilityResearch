from pathlib import Path
import sys,json,datetime,time,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import numpy as np,pandas as pd
from roughnoisy.core import *
def main():
 cfg=json.loads((R/'configs/baseline_pilot.json').read_text());start=time.perf_counter();rows=[];truths={};q=2/78
 runid=datetime.datetime.now(datetime.timezone.utc).strftime('baseline_%Y%m%dT%H%M%SZ');run=R/'runs'/runid;run.mkdir()
 for rep in range(cfg['paths']):
  rg=np.random.default_rng(np.random.SeedSequence([cfg['seed'],rep,0]));x=simulate_ou(cfg['days'],np.log(2)/22,rg)
  iv=.0001*np.exp(x-.25/2);rv=iv*np.exp(rg.normal(scale=np.sqrt(q),size=len(x))-q/2);truths[rep]=iv
  lv=np.log(rv);X=np.zeros((len(rv),4))
  for t in range(21,len(rv)):X[t]=har_features(lv,t)
  ey=np.empty(len(rv));ey[0]=rv[0]
  for t in range(1,len(rv)):ey[t]=.94*ey[t-1]+.06*rv[t]
  # Labels precomputed, but never eligible until complete horizon has matured.
  Y={h:np.log(np.convolve(rv,np.ones(h)/h,mode='valid')[1:]) for h in cfg['horizons']}
  fits={}
  for origin in range(cfg['origins'][0],cfg['origins'][1]+1):
   if (origin-cfg['origins'][0])%cfg['refit_every']==0:
    for h in cfg['horizons']:
     idx=mature_origins(origin,h,max(21,origin-cfg['rolling_training_window']+1));design=X[idx];label=Y[h][idx]
     coef=np.linalg.lstsq(design,label,rcond=None)[0];smear=np.mean(np.exp(label-design@coef));fits[h]=(coef,smear,origin,int(idx[-1]+h))
   for h in cfg['horizons']:
    coef,smear,fit_time,label_end=fits[h]
    assert label_end<=fit_time<=origin
    for model,pred in [('last_RV',rv[origin]),('EWMA_lambda0.94',ey[origin]),('direct_log_HAR_training_smearing',np.exp(X[origin]@coef)*smear)]:
     if not np.isfinite(pred) or pred<=0:raise ValueError('Invalid forecast')
     rows.append({'replicate':rep,'origin':origin,'horizon':h,'target_start':origin+1,'target_end':origin+h,'information_cutoff':origin,'fit_time':fit_time if model.startswith('direct') else origin,'last_matured_training_label':label_end if model.startswith('direct') else None,'model':model,'forecast':float(pred)})
 forecast=pd.DataFrame(rows);forecast.to_csv(run/'forecasts_before_evaluation.csv',index=False)
 # Evaluation only after forecasts have been persisted.
 forecast['true_IV_target']=[future_average(truths[int(row.replicate)],int(row.origin),int(row.horizon)) for row in forecast.itertuples()]
 forecast['QLIKE_true_IV']=qlike(forecast.true_IV_target,forecast.forecast)
 forecast.to_csv(run/'forecasts_evaluated.csv',index=False)
 perpath=forecast.groupby(['replicate','model','horizon']).QLIKE_true_IV.mean().reset_index();perpath.to_csv(run/'path_mean_losses.csv',index=False)
 rows=[]
 for h in cfg['horizons']:
  pivot=perpath.loc[perpath.horizon==h].pivot(index='replicate',columns='model',values='QLIKE_true_IV')
  for model in cfg['models']:
   diff=pivot[model]-pivot['last_RV'];rows.append({'model':model,'horizon':h,'paths':len(diff),'daily_origins_per_path':250,'mean_QLIKE_true_IV':pivot[model].mean(),'mean_difference_vs_last':diff.mean(),'MCSE_paired_path_difference':diff.std(ddof=1)/np.sqrt(len(diff)),'classification':cfg['classification']})
 pd.DataFrame(rows).to_csv(R/'results/baseline_forecast_summary.csv',index=False)
 meta={'run_id':runid,'status':'completed','config':cfg,'seconds':time.perf_counter()-start,'forecasts':len(forecast),'positivity_failures':0,'matured_label_failures':0,'config_sha256':hashlib.sha256((R/'configs/baseline_pilot.json').read_bytes()).hexdigest(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'qualification':'No fitted rough/nonrough contest. Refitting every22 origins; horizon-specific train-only smearing. HAR predictors need21 pre-window warmup observations. Risk economics not evaluated.'}
 (run/'metadata.json').write_text(json.dumps(meta,indent=2));(R/'results/latest_baseline.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
