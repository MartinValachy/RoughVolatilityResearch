"""Build/execute the synthetic-only portfolio demo with the current Python kernel."""
from pathlib import Path
import argparse,sys,json
import nbformat as nbf
from phase1_support import ROOT as R,record_run,sha


def main(execute):
    md=nbf.v4.new_markdown_cell;code=nbf.v4.new_code_cell
    nb=nbf.v4.new_notebook(cells=[
        md('''# Rough or Just Noisy?

A reproducible demonstration of how the observation process changes a descriptive volatility-roughness estimate. This notebook uses **synthetic data only**. It does not estimate market spot H, compare trading strategies, or claim a novel estimator.

The fixed full study uses 128 independent paths per model. The small fresh run below is an implementation demonstration; its sampling variation is larger. See `manuscript/SYNTHETIC_STUDY.md` for the full experiment and limitations. AI assistance and human-review status are disclosed in `AI_USE.md`.'''),
        code('''from pathlib import Path
import json, sys, copy
import numpy as np
import pandas as pd
root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'configs/side_project.json').is_file())
sys.path.insert(0, str(root / 'src'))
from roughnoisy.study import prepare, path_metrics, validate_covariance
cfg = json.loads((root / 'configs/side_project.json').read_text())
print({k: cfg[k] for k in ['models', 'days', 'paths', 'sampling_minutes', 'log_price_noise_sd', 'primary_lag_band']})'''),
        md('''## Independent construction checks

The covariance formula is compared with an independent parametrization, the inverse FFT of the embedding spectrum, and dense Cholesky Gaussian draws. These check the finite-dimensional Gaussian law, not whether the law describes a market.'''),
        code('''checks = validate_covariance(cfg)
for check in checks:
    print(check['model'], check['status'], 'FFT max error:', check['FFT_covariance_max_abs_error'])
assert all(c['status'] == 'passed_checks' for c in checks)'''),
        md('''## Run a small fresh experiment

For every path: simulate log spot variance, integrate on the fine trading-clock grid, simulate conditional Gaussian log-price returns, add endpoint price noise, and construct nested RV measures. Means below use four paths/model and are not the frozen full-study estimates.'''),
        code('''fresh = []
for model in cfg['models']:
    spectrum, _ = prepare(model, cfg)
    for replicate in range(4):
        fresh.extend(path_metrics(model, cfg, replicate, spectrum))
fresh = pd.DataFrame(fresh)
small = fresh[(fresh.noise_sd == 0) & (fresh.lag_max == 10) & (fresh.sampling_minutes == 5)]
display(small.groupby('model')[['local_H', 'H_spot', 'H_IV', 'H_RV']].mean().round(3))
assert np.isfinite(fresh.select_dtypes(include='number')).all().all()'''),
        md('''## Read the fixed full-study results

The committed summary is synthetic. H-tilde is half the log-variogram slope over lags 1–10. Different columns describe different observed objects; none should automatically equal the local spot exponent.'''),
        code('''columns = ['model', 'noise_sd', 'sampling_minutes', 'lag_max', 'local_H', 'H_spot_mean', 'H_IV_mean', 'H_RV_mean', 'H_RV_mcse', 'run_id']
pd.read_csv(root / 'results/side_project/summary.csv', usecols=columns, nrows=5)
full = pd.read_csv(root / 'results/side_project/summary.csv', usecols=columns)
selected = full[(full.noise_sd == 0) & (full.lag_max == 10) & (full.sampling_minutes == 5)]
display(selected[['model', 'local_H', 'H_spot_mean', 'H_IV_mean', 'H_RV_mean', 'H_RV_mcse']].round(4))
print('Full-study run:', full.run_id.iloc[0])'''),
        code('''from IPython.display import Image, display
display(Image(filename=str(root / 'docs/figures/measurement_chain.png')))
display(Image(filename=str(root / 'docs/figures/sampling_noise.png')))'''),
        md('''## What follows—and what does not

The OU counterexample shows that a low naive slope from log RV need not identify rough spot volatility. Temporal aggregation and finite return sampling matter even without added price noise. Conversely, this example does not establish that actual volatility is smooth, and accounting for measurement error does not guarantee H=0.5.

The figures show mean ±1.96 Monte Carlo SE across independent paths. They do not provide coverage for an estimator of market H. Noise levels are illustrative, model parameters are fixed, integration uses a finite trading clock, and the empirical forecasting extension remains deferred.

To extend the demonstration, predict the effect of a different sampling grid before changing a separate config. Preserve the frozen study and report both results.''')
    ])
    nb.metadata['kernelspec']={'display_name':'Python 3','language':'python','name':'python3'}
    target=R/'notebooks/side_project_demo.ipynb';nbf.write(nb,target)
    if execute:
        from nbclient import NotebookClient
        from jupyter_client.manager import KernelManager
        km=KernelManager(kernel_name='python3')
        km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
        NotebookClient(nb,timeout=180,resources={'metadata':{'path':str(R)}},km=km).execute()
        nbf.write(nb,target)
        assert all(c.execution_count is not None and not any(o.output_type=='error' for o in c.outputs) for c in nb.cells if c.cell_type=='code')
        run=record_run('side_project_demo',{'status':'passed_checks','code_cells_executed':sum(c.cell_type=='code' for c in nb.cells),
            'notebook_sha256':sha(target),'builder_sha256':sha(__file__),'empirical_data_read':False})
        (R/'results/side_project_demo.json').write_text(json.dumps({'run_id':run,'status':'passed_checks','path':str(target.relative_to(R))},indent=2)+'\n')
        print(json.dumps({'run_id':run,'status':'passed_checks','notebook':str(target)}))
    else: print('Built '+str(target))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');a=p.parse_args();main(a.execute)
