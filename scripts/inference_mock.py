from pathlib import Path
import sys,json,time,datetime,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import numpy as np,pandas as pd
from roughnoisy.core import *
def main():
 cfg=json.loads((R/'configs/inference_mock.json').read_text());start=time.perf_counter();rows=[]
 for rep in range(cfg['independent_series']):
  rg=np.random.default_rng(np.random.SeedSequence([cfg['seed'],rep,0]));bg=np.random.default_rng(np.random.SeedSequence([cfg['seed'],rep,1]));x=simulate_ou(cfg['dates'],-np.log(.8),rg,variance=1)
  bs=stationary_bootstrap_means(x,bg,cfg['bootstrap_draws'],cfg['mean_block_length']);lo,hi=np.quantile(bs,[.05,.95]);rows.append({'replicate':rep,'sample_mean':x.mean(),'CI90_lower':lo,'CI90_upper':hi,'contains_known_zero_mean':bool(lo<=0<=hi),'equivalence_conclusion':'not assessed: no margin registered'})
 df=pd.DataFrame(rows);runid=datetime.datetime.now(datetime.timezone.utc).strftime('inference_%Y%m%dT%H%M%SZ');run=R/'runs'/runid;run.mkdir();df.to_csv(run/'intervals.csv',index=False)
 coverage=df.contains_known_zero_mean.mean();meta={'run_id':runid,'status':'completed','config':cfg,'coverage':coverage,'MCSE_coverage':float(np.sqrt(coverage*(1-coverage)/len(df))),'seconds':time.perf_counter()-start,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'config_sha256':hashlib.sha256((R/'configs/inference_mock.json').read_bytes()).hexdigest(),'gate':'Mock completed; 30 paths too few to establish coverage, block22/66 and refitting/long-memory calibration pending'}
 (run/'metadata.json').write_text(json.dumps(meta,indent=2));(R/'results/latest_inference.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
