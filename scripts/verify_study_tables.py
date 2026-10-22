"""Second arithmetic path for synthetic path-mean/MCSE tables; no market data."""
from pathlib import Path
import csv,math,statistics,json
from collections import defaultdict
from phase1_support import ROOT as R,record_run,sha

KEYS=['model','local_H','noise_sd','sampling_minutes','lag_max']
METRICS=['H_spot','H_IV','H_RV','mean_RV_over_IV','mean_RV_over_conditional_expectation','mean_qhat',
         'IV_half_resolution_mean_relative_error','IV_quarter_resolution_mean_relative_error']


def compare(paths,summaries):
    groups=defaultdict(list)
    for row in paths: groups[tuple(row[k] for k in KEYS)].append(row)
    checked=0
    for summary in summaries:
        key=tuple(summary[k] for k in KEYS);g=groups.pop(key)
        if len(g)!=int(summary['paths']) or len({r['replicate'] for r in g})!=len(g):
            raise ValueError('Missing/duplicate Monte Carlo path')
        for metric in METRICS+['RV_minus_IV_H']:
            values=[float(r[metric]) if metric!='RV_minus_IV_H' else float(r['H_RV'])-float(r['H_IV']) for r in g]
            mean=math.fsum(values)/len(values)
            mcse=statistics.stdev(values)/math.sqrt(len(values))
            if not math.isclose(mean,float(summary[metric+'_mean']),abs_tol=1e-11,rel_tol=1e-10):
                raise ValueError('Independent table mean mismatch: '+metric)
            if not math.isclose(mcse,float(summary[metric+'_mcse']),abs_tol=1e-11,rel_tol=1e-10):
                raise ValueError('Independent table MCSE mismatch: '+metric)
            checked+=2
    if groups: raise ValueError('Unreported simulation cells')
    return checked


def main():
    with (R/'results/side_project/path_metrics.csv').open(newline='') as f: paths=list(csv.DictReader(f))
    with (R/'results/side_project/summary.csv').open(newline='') as f: summaries=list(csv.DictReader(f))
    checked=compare(paths,summaries)
    planted=[dict(r) for r in summaries];planted[0]['H_RV_mean']=str(float(planted[0]['H_RV_mean'])+.1)
    caught=False
    try: compare(paths,planted)
    except ValueError: caught=True
    if not caught: raise ValueError('Planted summary error was not detected')
    run=record_run('side_project_table_check',{'status':'passed_checks','scalar_values_recomputed':checked,
        'planted_error_detected':caught,'method':'Standard-library csv + math.fsum/statistics.stdev; separate from pandas/NumPy summarizer',
        'path_metrics_sha256':sha(R/'results/side_project/path_metrics.csv'),'summary_sha256':sha(R/'results/side_project/summary.csv'),
        'code_sha256':sha(__file__)})
    (R/'results/side_project_table_check.json').write_text(json.dumps({'run_id':run,'status':'passed_checks','scalar_values_recomputed':checked,'planted_error_detected':caught},indent=2)+'\n')
    print(json.dumps({'run_id':run,'scalar_values_recomputed':checked,'planted_error_detected':caught}))


if __name__=='__main__': main()
