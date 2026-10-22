"""Reproduce the fixed synthetic side project; never reads empirical data."""
from pathlib import Path
import argparse,json,time,sys,hashlib
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from roughnoisy.study import prepare,path_metrics,validate_covariance
from phase1_support import record_run,sha


def summarize(frame):
    keys=['model','local_H','noise_sd','sampling_minutes','lag_max']
    metrics=['H_spot','H_IV','H_RV','mean_RV_over_IV','mean_RV_over_conditional_expectation','mean_qhat',
             'IV_half_resolution_mean_relative_error','IV_quarter_resolution_mean_relative_error']
    rows=[]
    for key,g in frame.groupby(keys,sort=True):
        row=dict(zip(keys,key));row['paths']=len(g)
        for metric in metrics:
            values=g[metric].to_numpy(float)
            row[metric+'_mean']=float(values.mean())
            row[metric+'_mcse']=float(values.std(ddof=1)/np.sqrt(len(values)))
        # Paired errors within each path, not independent intervals over daily observations.
        delta=g.H_RV-g.H_IV
        row['RV_minus_IV_H_mean']=float(delta.mean())
        row['RV_minus_IV_H_mcse']=float(delta.std(ddof=1)/np.sqrt(len(g)))
        rows.append(row)
    return pd.DataFrame(rows)


def run(cfg,output,pilot=False):
    start=time.perf_counter();checks=validate_covariance(cfg);records=[];samplers={}
    for model in cfg['models']:
        spectrum,info=prepare(model,cfg);samplers[model]=info
        for rep in range(cfg['paths']): records.extend(path_metrics(model,cfg,rep,spectrum))
        print(json.dumps({'model':model,'paths_completed':cfg['paths'],'seconds':round(time.perf_counter()-start,2)}),flush=True)
    frame=pd.DataFrame(records);summary=summarize(frame)
    if not np.isfinite(frame.select_dtypes(include='number')).all().all(): raise ValueError('Nonfinite simulation output')
    expectation=summary[summary.lag_max.eq(cfg['primary_lag_band'])]
    worst=float(np.max(np.abs(expectation.mean_RV_over_conditional_expectation_mean-1)))
    # Independent exact conditional expectation, conservative pilot check; no H target fitted.
    allowance=.06 if pilot else .025
    if worst>allowance: raise ValueError('Conditional RV expectation check failed')
    metadata={'status':'passed_checks','config':cfg,'config_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
        'code_sha256':sha(R/'src/roughnoisy/study.py'),'runner_sha256':sha(__file__),
        'pilot':pilot,'seconds':time.perf_counter()-start,'covariance_checks':checks,'samplers':samplers,
        'conditional_RV_expectation_max_error':worst,'conditional_RV_expectation_tolerance':allowance,
        'path_rows':len(frame),'summary_rows':len(summary),'empirical_data_read':False,
        'qualification':'Trading-clock discretized Ito log-price experiment, fixed illustrative noise; finite-band H is descriptive, no latent-market inference.'}
    run_id=record_run('side_project_pilot' if pilot else 'side_project_study',metadata)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    frame.assign(run_id=run_id).to_csv(output/'path_metrics.csv',index=False)
    summary.assign(run_id=run_id).to_csv(output/'summary.csv',index=False)
    (output/'metadata.json').write_text(json.dumps(dict(metadata,run_id=run_id),indent=2)+'\n')
    print(json.dumps({'run_id':run_id,'status':metadata['status'],'seconds':metadata['seconds'],'conditional_RV_expectation_max_error':worst}),flush=True)
    return run_id


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pilot',action='store_true');p.add_argument('--output',type=Path)
    a=p.parse_args();cfg=json.loads((R/'configs/side_project.json').read_text())
    if a.pilot: cfg['paths']=4
    run(cfg,a.output or R/'results'/('side_project_pilot' if a.pilot else 'side_project'),a.pilot)
