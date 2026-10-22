"""Independent, coupled double-resolution diagnostic for A08; no empirical data."""
from pathlib import Path
import sys,json,copy,time
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from roughnoisy.study import prepare,path
from phase1_support import record_run,sha


def independent_h(values):
    x=np.log(np.arange(1,11));moments=[]
    for lag in range(1,11):
        d=values[lag:]-values[:-lag];moments.append(float(d@d/len(d)))
    y=np.log(moments)
    return float(((x-x.mean())@(y-y.mean()))/(2*((x-x.mean())@(x-x.mean()))))


def main():
    original=json.loads((R/'configs/side_project.json').read_text());cfg=copy.deepcopy(original)
    cfg['fine_steps_per_day']*=2;cfg['seed']+=1701
    paths=16;tolerance=.01;path_tolerance=.03;start=time.perf_counter();records=[]
    for model in cfg['models']:
        spectrum,_=prepare(model,cfg)
        for rep in range(paths):
            _,v,_,_=path(model,cfg,rep,spectrum)
            fine=v.mean(axis=1);half=v[:,::2].mean(axis=1)
            fine_h=independent_h(np.log(fine));half_h=independent_h(np.log(half))
            records.append({'model':model,'replicate':rep,'H_IV_1560':fine_h,'H_IV_780':half_h,
                'delta_H':half_h-fine_h,'mean_absolute_relative_IV_error':float(np.mean(np.abs(half-fine)/fine))})
    frame=pd.DataFrame(records);rows=[]
    for model,g in frame.groupby('model'):
        rows.append({'model':model,'paths':len(g),'mean_delta_H':float(g.delta_H.mean()),
            'mcse_delta_H':float(g.delta_H.std(ddof=1)/np.sqrt(len(g))),
            'max_absolute_path_delta_H':float(g.delta_H.abs().max()),
            'mean_absolute_relative_IV_error':float(g.mean_absolute_relative_IV_error.mean())})
    passed=all(abs(r['mean_delta_H'])<tolerance and r['max_absolute_path_delta_H']<path_tolerance for r in rows)
    metadata={'status':'passed_checks' if passed else 'refinement_limit_exceeded','config':cfg,
        'paths_per_model':paths,'mean_H_difference_tolerance':tolerance,'path_H_difference_tolerance':path_tolerance,
        'rows':rows,'code_sha256':sha(__file__),'seconds':time.perf_counter()-start,
        'meaning':'Coupled numerical-resolution diagnostic only; no continuous-time convergence proof or empirical H inference.'}
    run=record_run('side_project_refinement',metadata)
    frame.assign(run_id=run).to_csv(R/'results/side_project_refinement_paths.csv',index=False)
    pd.DataFrame(rows).assign(run_id=run).to_csv(R/'results/side_project_refinement.csv',index=False)
    (R/'results/side_project_refinement.json').write_text(json.dumps(dict(metadata,run_id=run),indent=2)+'\n')
    print(json.dumps({'run_id':run,'status':metadata['status'],'rows':rows}),flush=True)


if __name__=='__main__': main()
