from pathlib import Path
import json,hashlib,time,datetime,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import numpy as np,pandas as pd
from scipy.integrate import quad
from scipy.special import gamma
from roughnoisy.core import apparent_h
def moment(t,k,H,tol=2e-11):
 a=k*t;C=2*gamma(2*H+1)*np.sin(np.pi*H)/np.pi
 def f(z):return z**(-1-2*H)/(z*z+a*a)
 low=quad(lambda z:2*np.sin(z/2)**2*f(z),0,1,epsabs=tol,epsrel=tol,limit=300)[0]
 tail=quad(f,1,np.inf,epsabs=tol,epsrel=tol,limit=300)[0]-quad(f,1,np.inf,weight='cos',wvar=1,epsabs=tol,limit=300)[0]
 return t**(2*H)*(1-C*a*a*(low+tail))
def main():
 cfg=json.loads((R/'configs/mouti_table2.json').read_text());tic=time.perf_counter();rows=[]
 # Independent Brownian exact-OU check of the spectral-integral constants.
 check=max(abs(moment(t,.02,.5)-(1-np.exp(-.02*t))/.02) for t in [1,10,100])
 if check>1e-7:raise ValueError('Spectral fOU formula fails Brownian special case')
 independent=[]
 # Independent oscillatory covariance transform, not the variogram rewrite.
 for H,k,t in [(.1,.035,1),(.1,.035,10),(.1,.035,100),(.2,.02,100)]:
  pref=gamma(2*H+1)*np.sin(np.pi*H)/np.pi
  cov= pref*quad(lambda w:w**(1-2*H)/(k*k+w*w),0,np.inf,weight='cos',wvar=t,epsabs=1e-10,limlst=300,limit=300)[0]
  alternate=gamma(2*H+1)/k**(2*H)-2*cov
  direct=moment(t,k,H);independent.append({'H':H,'kappa':k,'lag':t,'variogram_rewrite':direct,'independent_covariance_transform':alternate,'absolute_error':abs(direct-alternate)})
 if max(v['absolute_error'] for v in independent)>1e-7:raise ValueError('Independent fOU integral checks disagree')
 for i,H in enumerate(cfg['H']):
  for j,band in enumerate(cfg['lag_max']):
   for z,k in enumerate(cfg['kappa']):
    vals=[moment(t,k,H) for t in range(1,band+1)];estimate=apparent_h(vals,band);target=cfg['printed_rows_H_then_lag'][i*4+j][z]
    rows.append({'H':H,'kappa':k,'lag_max':band,'source_table2':target,'spectral_integral_band_H':estimate,'absolute_error':abs(estimate-target),'within_registered_tolerance':abs(estimate-target)<=cfg['absolute_tolerance']})
 df=pd.DataFrame(rows);df.to_csv(R/'results/mouti_table2_audit.csv',index=False);runid=datetime.datetime.now(datetime.timezone.utc).strftime('mouti_audit_%Y%m%dT%H%M%SZ');run=R/'runs'/runid;run.mkdir();df.to_csv(run/'table2.csv',index=False)
 meta={'run_id':runid,'status':'completed','config':cfg,'cells':len(df),'passed_cells':int(df.within_registered_tolerance.sum()),'max_absolute_error':float(df.absolute_error.max()),'Brownian_special_case_max_absolute_error':check,'independent_integral_checks':independent,'seconds':time.perf_counter()-tic,'config_sha256':hashlib.sha256((R/'configs/mouti_table2.json').read_bytes()).hexdigest(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_pdf_sha256':hashlib.sha256((R/'literature/raw/S08.pdf').read_bytes()).hexdigest(),'scope':'Table2 deterministic population finite-band slopes only. Does not validate noisy Monte Carlo Tables3-6 or all-H proposition proof.'}
 (run/'metadata.json').write_text(json.dumps(meta,indent=2));(R/'results/latest_mouti_audit.json').write_text(json.dumps(meta,indent=2));print(json.dumps({k:meta[k] for k in ['run_id','cells','passed_cells','max_absolute_error','Brownian_special_case_max_absolute_error','seconds']},indent=2))
if __name__=='__main__':main()
