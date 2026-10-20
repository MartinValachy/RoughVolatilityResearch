from pathlib import Path
import sys,json,time,datetime,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import numpy as np,pandas as pd
from roughnoisy.core import simulate_ou,variogram,apparent_h
def main():
 cfg=json.loads((R/'configs/efficient_price.json').read_text());start=time.perf_counter();rows=[]
 M=cfg['fine_steps_per_session'];days=cfg['days'];rate=np.log(2)/cfg['OU_half_life_days'];var=cfg['stationary_log_variance'];vmean=cfg['mean_daily_variance']
 # Independent 5-path benchmark before all replications. No outcome-based scaling.
 bench=time.perf_counter()
 for j in range(5):simulate_ou(M*days,rate,np.random.default_rng(np.random.SeedSequence([cfg['seed'],991,j])),variance=var,dt=1/M)
 benchmark=time.perf_counter()-bench
 for rep in range(cfg['paths']):
  rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],rep,0]));prng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],rep,1]))
  x=simulate_ou(days*M,rate,rng,variance=var,dt=1/M).reshape(days,M)
  v=vmean*np.exp(x-var/2);iv=v.mean(axis=1)
  # Fine Euler left-point integration vs coupled half-resolution exact OU grid.
  coarse=v[:,::2].mean(axis=1);refine=float(np.mean(np.abs(iv-coarse)/iv))
  efficient_returns=np.sqrt(v/M)*prng.normal(size=v.shape)
  logprice=np.cumsum(efficient_returns.ravel());price_noise=prng.normal(scale=cfg['microstructure_noise_demo_std'],size=logprice.size+1)
  observed_returns=efficient_returns.ravel()+np.diff(price_noise)
  moments={}
  for minutes in cfg['sampling_minutes']:
   block=M*minutes//cfg['session_minutes'];count=M//block
   r=efficient_returns.reshape(days,count,block).sum(axis=2);rv=np.sum(r*r,axis=1);rq=count/3*np.sum(r**4,axis=1)
   obs=observed_returns.reshape(days,count,block).sum(axis=2);rv_obs=np.sum(obs*obs,axis=1)
   moments[minutes]=np.log(rv)-np.log(iv)
   rows.append({'replicate':rep,'sampling_minutes':minutes,'M':count,'mean_RV_over_IV':np.mean(rv/iv),'mean_observed_RV_over_IV':np.mean(rv_obs/iv),'mean_log_error':np.mean(np.log(rv/iv)),'mean_q_plugin':np.mean(2*rq/(count*rv*rv)),'log_error_variance':np.var(np.log(rv/iv)),'IV_refinement_relative_abs':refine,'apparent_H_log_IV':apparent_h(variogram(np.log(iv)),10),'apparent_H_log_RV':apparent_h(variogram(np.log(rv)),10),'nested_1min_5min_error_correlation':np.nan})
  corr=np.corrcoef(moments[1],moments[5])[0,1]
  for row in rows[-4:]:row['nested_1min_5min_error_correlation']=corr
 df=pd.DataFrame(rows);runid=datetime.datetime.now(datetime.timezone.utc).strftime('efficient_%Y%m%dT%H%M%SZ');run=R/'runs'/runid;run.mkdir()
 df.to_csv(run/'path_metrics.csv',index=False);summary=df.groupby('sampling_minutes').mean(numeric_only=True);summary.to_csv(R/'results/efficient_price_summary.csv')
 # Monte Carlo units are paths, not 25,000 dependent days.
 se=df.groupby('sampling_minutes').std(numeric_only=True)/np.sqrt(cfg['paths']);se.to_csv(R/'results/efficient_price_mcse.csv')
 meta={'run_id':runid,'config':cfg,'status':'completed','seconds':time.perf_counter()-start,'benchmark_5_paths_seconds':benchmark,'config_sha256':hashlib.sha256((R/'configs/efficient_price.json').read_bytes()).hexdigest(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'refinement_gate_passed':bool(df.IV_refinement_relative_abs.max()<.001),'maximum_path_average_IV_refinement_relative_error':float(df.IV_refinement_relative_abs.max()),'qualification':'Exact stationary OU at grid nodes; price/IV integrals use explicit left-point refinement. No actual raw-price replication. Price noise is an illustrative addition.'}
 (run/'metadata.json').write_text(json.dumps(meta,indent=2));(R/'results/latest_efficient.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
