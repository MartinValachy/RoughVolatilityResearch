"""Run the bounded Level A pilot. Does not open empirical final-test data."""
from pathlib import Path
import sys,json,hashlib,datetime,time,platform,subprocess,traceback
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import numpy as np,pandas as pd
from scipy import stats
from roughnoisy.core import *

def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cfg=json.loads((R/'configs/pilot.json').read_text());base=cfg['base_seed'];reps=cfg['paths_per_cell']
 if reps>100 or cfg['production_allowed']:raise ValueError('Preparation runner capped at 100 paths per cell')
 run_id=datetime.datetime.now(datetime.timezone.utc).strftime('pilot_%Y%m%dT%H%M%SZ')
 run=R/'runs'/run_id;run.mkdir();(run/'config.json').write_text(json.dumps(cfg,indent=2))
 meta={'run_id':run_id,'classification':cfg['classification'],'protocol_version':cfg['protocol_version'],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'config_sha256':hashfile(R/'configs/pilot.json'),'code_hashes':{str(p.relative_to(R)):hashfile(p) for p in [Path(__file__),R/'src/roughnoisy/core.py']},'python':sys.version,'platform':platform.platform(),'processor':platform.processor(),'seed_policy':'SeedSequence([base, family_id, n, replicate, stream]); shared latent and iid-noise draws within paired observation cells','base_seed':base,'status':'running'}
 (run/'metadata.json').write_text(json.dumps(meta,indent=2));start=time.perf_counter();failures=[];rows=[];bench=[]
 try:
  families=[]
  for half in cfg['ou_half_lives']:
   rate=np.log(2)/half;families.append((f'OU_hl{half}',0.5,lambda k,rate=rate:ou_cov(k,rate),rate))
  for H in cfg['rough_H']:
   families.append((f'Cauchy_H{H}',H,lambda k,H=H:cauchy_cov(k,H),None))
  # Runtime/embedding preflight uses separate streams and is recorded before
  # the 100-replicate grid, never used to choose scientific outcomes.
  preflight=[]
  for fid,(name,H,cov,rate) in enumerate(families):
   tick=time.perf_counter();sp,em=embedding(cov,5000)
   for j in range(10):
    rr=np.random.default_rng(np.random.SeedSequence([base,991,fid,j]))
    xx=simulate_ou(5000,rate,rr) if rate is not None else simulate_embedding(sp,5000,rr)
    variogram(xx)
   preflight.append({'family':name,'paths':10,'n':5000,'seconds':time.perf_counter()-tick,**em})
  (run/'preflight_benchmark.json').write_text(json.dumps(preflight,indent=2))
  print('Preflight complete; launching bounded 100-path pilot',flush=True)
  for fid,(name,H,cov,rate) in enumerate(families):
   for n in cfg['sample_sizes']:
    tic=time.perf_counter();spec,emb=embedding(cov,n)
    for rep in range(reps):
     def rng(stream):return np.random.default_rng(np.random.SeedSequence([base,fid,n,rep,stream]))
     x=simulate_ou(n,rate,rng(0)) if rate is not None else simulate_embedding(spec,n,rng(0))
     z=rng(1).normal(size=n);latent_vario=2*(cov(0)-cov(np.arange(1,23)))
     for ratio in cfg['noise_q_over_latent_lag1_increment_variance']:
      q=ratio*float(latent_vario[0]);e=np.sqrt(q)*z;y=x+e;mom=variogram(y)
      expected=latent_vario+2*q
      fit=nlls_h(mom) if ratio==1 else None
      for band in cfg['lag_bands']:
       est=apparent_h(mom,band);corrected=apparent_h(mom-2*q,band);pop=apparent_h(expected,band)
       rows.append({'family':name,'true_local_H':H,'n':n,'replicate':rep,'ratio':ratio,'noise':'iid','lag_max':band,'H_naive':est,'H_population':pop,'H_population_latent':apparent_h(latent_vario,band),'H_known_noise_subtraction':corrected,'correction_invalid':not np.isfinite(corrected),'H_nlls':fit['H'] if fit and band==10 else np.nan,'nlls_bound_hit':fit['bound_hit'] if fit and band==10 else None})
     # Targeted stress at ratio=1 for half-life22 OU, avoiding full crossing.
     if name=='OU_hl22':
      q=float(latent_vario[0]);t=np.arange(n)
      e_het=np.sqrt(q*(0.4+1.2*((t//22)%2)))*z
      rho=0.5;e_ar=simulate_ou(n,-np.log(rho),rng(2),variance=q)
      a=np.sqrt(q/cov(0));e_cross=a*x
      for noise,e in [('heteroskedastic_exogenous',e_het),('AR1_rho0.5',e_ar),('latent_correlated',e_cross)]:
       for band in cfg['lag_bands']:
        mom=variogram(x+e)
        noise_mom=(np.array([np.mean(q*(0.4+1.2*((t[:-k]//22)%2))+q*(0.4+1.2*((t[k:]//22)%2))) for k in range(1,23)]) if noise=='heteroskedastic_exogenous' else 2*q*(1-rho**np.arange(1,23)) if noise=='AR1_rho0.5' else a*a*latent_vario)
        cross=2*a*latent_vario if noise=='latent_correlated' else 0
        expected=latent_vario+noise_mom+cross
        rows.append({'family':name,'true_local_H':H,'n':n,'replicate':rep,'ratio':1,'noise':noise,'lag_max':band,'H_naive':apparent_h(mom,band),'H_population':apparent_h(expected,band),'H_population_latent':apparent_h(latent_vario,band),'H_known_noise_subtraction':apparent_h(mom-2*q,band),'correction_invalid':not np.isfinite(apparent_h(mom-2*q,band)),'H_nlls':np.nan,'nlls_bound_hit':None})
    elapsed=time.perf_counter()-tic;bench.append({'family':name,'n':n,'paths':reps,'seconds':elapsed,**emb});print(name,n,round(elapsed,3),flush=True)
  df=pd.DataFrame(rows);df.to_csv(run/'estimates.csv',index=False)
  summaries=[]
  for key,g in df.groupby(['family','true_local_H','n','ratio','noise','lag_max']):
   a=g.H_naive.to_numpy();correct=g.H_known_noise_subtraction.dropna().to_numpy()
   summaries.append(dict(zip(['family','true_local_H','n','ratio','noise','lag_max'],key))|{'paths':len(a),'mean_H':a.mean(),'sd_H':a.std(ddof=1),'MCSE_mean_H':a.std(ddof=1)/np.sqrt(len(a)),'bias_to_local_H':a.mean()-key[1],'RMSE_to_local_H':np.sqrt(np.mean((a-key[1])**2)),'population_band_H':g.H_population.iloc[0],'population_latent_band_H':g.H_population_latent.iloc[0],'freq_H_below_0p2':np.mean(a<0.2),'MCSE_frequency':np.sqrt(np.mean(a<0.2)*(1-np.mean(a<0.2))/len(a)),'corrected_mean_H':correct.mean() if len(correct) else np.nan,'correction_invalid_fraction':g.correction_invalid.mean(),'nlls_mean_H':g.H_nlls.mean(),'nlls_bound_hit_fraction':pd.to_numeric(g.nlls_bound_hit,errors='coerce').mean()})
  summary=pd.DataFrame(summaries);summary.to_csv(run/'summary.csv',index=False);summary.to_csv(R/'results/toy_summary.csv',index=False)
  pd.DataFrame(bench).to_csv(run/'benchmark.csv',index=False)
  meta.update(status='completed',seconds=time.perf_counter()-start,independent_latent_paths=len(families)*len(cfg['sample_sizes'])*reps,observation_cells=len(summaries)//3,estimate_rows=len(df),failures=failures)
  (R/'results/latest_pilot.json').write_text(json.dumps({'run_id':run_id,'path':str(run),'metadata':meta},indent=2))
 except Exception:
  meta.update(status='failed',traceback=traceback.format_exc());raise
 finally:(run/'metadata.json').write_text(json.dumps(meta,indent=2))
if __name__=='__main__':main()
