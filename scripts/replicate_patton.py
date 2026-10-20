from pathlib import Path
import json,datetime,time,hashlib,sys
import numpy as np,pandas as pd
from scipy import stats,special,integrate,optimize
R=Path(__file__).resolve().parents[1]
def main():
 cfg=json.loads((R/'configs/replication_patton.json').read_text());rows=[];checks=[];start=time.perf_counter()
 for col,nu in [('t6',6),('t10',10),('normal',np.inf)]:
  dist=stats.norm() if np.isinf(nu) else stats.t(nu,scale=np.sqrt((nu-2)/nu))
  meanabs=2*integrate.quad(lambda r:r*dist.pdf(r),0,np.inf,epsabs=1e-10)[0]
  elog=2*integrate.quad(lambda r:np.log(r*r)*dist.pdf(r),0,np.inf,epsabs=1e-9)[0]
  fourth=2*integrate.quad(lambda r:r**4*dist.pdf(r),0,np.inf,epsabs=1e-9)[0]
  median=dist.ppf(0.75)**2
  # d E|y/h-1| / dh = -E[y sign(y-h)] / h^2.
  root=optimize.brentq(lambda h:2*integrate.quad(lambda r:r*r*dist.pdf(r),0,np.sqrt(h),epsabs=1e-11)[0]-0.5,0.01,20,xtol=1e-11)
  values={'MSE':1.0,'QLIKE':1.0,'MSE-LOG':np.exp(elog),'MSE-SD':meanabs**2,'MSE-prop':fourth,'MAE':median,'MAE-LOG':median,'MAE-SD':median,'MAE-prop':root}
  closed_log=np.exp(special.digamma(.5)+np.log(2)) if np.isinf(nu) else np.exp(special.digamma(.5)-special.digamma(nu/2))*(nu-2)
  checks.append({'column':col,'log_moment_quadrature_vs_closed_abs_error':abs(values['MSE-LOG']-closed_log),'fourth_moment_quadrature_vs_closed_abs_error':abs(fourth-(3 if np.isinf(nu) else 3*(nu-2)/(nu-4)))})
  for loss,val in values.items():
   target=cfg['printed_targets'][loss][cfg['columns'].index(col)];err=abs(val-target)
   rows.append({'loss':loss,'distribution':col,'source_printed':target,'reproduced':val,'absolute_difference':err,'within_registered_tolerance':bool(err<=cfg['accuracy_absolute_tolerance'])})
 run_id=datetime.datetime.now(datetime.timezone.utc).strftime('replication_patton_%Y%m%dT%H%M%SZ');run=R/'runs'/run_id;run.mkdir()
 pd.DataFrame(rows).to_csv(run/'table1.csv',index=False);pd.DataFrame(rows).to_csv(R/'results/patton_table1_replication.csv',index=False)
 meta={'run_id':run_id,'status':'completed','source_pdf_sha256':hashlib.sha256((R/'literature/raw/S12.pdf').read_bytes()).hexdigest(),'config_sha256':hashlib.sha256((R/'configs/replication_patton.json').read_bytes()).hexdigest(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'seconds':time.perf_counter()-start,'checks':checks,'cells':len(rows),'passed_cells':sum(r['within_registered_tolerance'] for r in rows),'max_absolute_error':max(r['absolute_difference'] for r in rows),'interpretation':'Numerical reproduction of published theoretical table; MAE-prop was approximate in source.'}
 (run/'metadata.json').write_text(json.dumps(meta,indent=2));(R/'results/latest_replication.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
if __name__=='__main__':main()
