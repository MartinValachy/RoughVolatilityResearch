"""Build synthetic-only figures/report; optional private empirical annex."""
from pathlib import Path
import argparse,json,shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from phase1_support import ROOT as R,record_run,sha

LABELS={'OU':'Brownian OU (local H=0.5)','Cauchy_H01':'Cauchy (local H=0.1)','Cauchy_H03':'Cauchy (local H=0.3)'}
COLORS=['#147d92','#da8a24','#a64c65']


def load_csv(path,cols=None):
    pd.read_csv(path,usecols=cols,nrows=5)
    return pd.read_csv(path,usecols=cols)


def build(output,empirical=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    figures=R/'docs/figures';figures.mkdir(parents=True,exist_ok=True)
    s=load_csv(R/'results/side_project/summary.csv')
    meta=json.loads((R/'results/side_project/metadata.json').read_text());study_run=meta['run_id']
    refine=json.loads((R/'results/side_project_refinement.json').read_text())
    primary=s[s.lag_max.eq(10)]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
    fig,axes=plt.subplots(1,3,figsize=(13,4.4),layout='constrained')
    names=['Spot\nsamples','Integrated\nvariance','1-minute\nRV','5-minute\nRV','30-minute\nRV']
    for ax,model in zip(axes,meta['config']['models']):
        g=primary[primary.model.eq(model)&primary.noise_sd.eq(0)].set_index('sampling_minutes')
        one=g.loc[1]
        means=[one.H_spot_mean,one.H_IV_mean,one.H_RV_mean,g.loc[5].H_RV_mean,g.loc[30].H_RV_mean]
        errors=1.96*np.array([one.H_spot_mcse,one.H_IV_mcse,one.H_RV_mcse,g.loc[5].H_RV_mcse,g.loc[30].H_RV_mcse])
        ax.bar(np.arange(5),means,yerr=errors,color=['#8b9ea8','#526c86','#147d92','#147d92','#147d92'],capsize=3)
        ax.axhline(one.local_H,color='#a64c65',ls='--',lw=1.2,label='Spot local H (reference)')
        ax.set(title=LABELS[model],ylabel='Mean finite-band H-tilde',ylim=(0,.62))
        ax.set_xticks(np.arange(5),names,fontsize=8);ax.legend(fontsize=7)
    fig.suptitle('The observed object changes the finite-band slope\nNo added price noise; lags 1–10 sessions; 128 independent paths. Bars: mean ± 1.96 Monte Carlo SE.',fontsize=12)
    fig.savefig(figures/'measurement_chain.png',dpi=165);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(13,4.3),layout='constrained')
    for ax,model in zip(axes,meta['config']['models']):
        for color,sd in zip(COLORS,[0,.0001,.0003]):
            g=primary[primary.model.eq(model)&primary.noise_sd.eq(sd)].sort_values('sampling_minutes')
            ax.errorbar(g.sampling_minutes,g.H_RV_mean,yerr=1.96*g.H_RV_mcse,marker='o',color=color,capsize=3,label=f'{sd*10000:g} bp log-price noise')
        g=primary[primary.model.eq(model)]
        ax.axhline(g.H_IV_mean.iloc[0],color='#526c86',ls=':',label='Grid IV slope')
        ax.set(title=LABELS[model],xlabel='Sampling interval (minutes)',ylabel='Mean H-tilde of log RV',xscale='log',ylim=(0,.6))
        ax.set_xticks([1,5,15,30],['1','5','15','30']);ax.legend(fontsize=7)
    fig.suptitle('Finite sampling and price noise both matter\nFixed illustrative noise levels, shared nested grids; error bars show Monte Carlo uncertainty only.',fontsize=12)
    fig.savefig(figures/'sampling_noise.png',dpi=165);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
    for color,model in zip(COLORS,meta['config']['models']):
        g=s[s.model.eq(model)&s.noise_sd.eq(0)&s.sampling_minutes.eq(5)].sort_values('lag_max')
        axes[0].errorbar(g.lag_max,g.H_RV_mean,yerr=1.96*g.H_RV_mcse,marker='o',capsize=3,color=color,label=LABELS[model])
        g=primary[primary.model.eq(model)&primary.noise_sd.eq(.0003)].sort_values('sampling_minutes')
        axes[1].plot(g.sampling_minutes,g.mean_RV_over_IV_mean,'o-',color=color,label=LABELS[model])
    axes[0].set(xlabel='Maximum lag (sessions; minimum lag = 1)',ylabel='Mean H-tilde of log RV',title='Lag-band sensitivity: 5-minute RV, zero added noise')
    axes[0].set_xticks([5,10,22]);axes[0].legend(fontsize=8)
    axes[1].axhline(1,color='gray',ls='--',lw=1)
    axes[1].set(xlabel='Sampling interval (minutes)',ylabel='Mean RV / grid IV',title='Variance-level distortion: 3 bp price noise',xscale='log')
    axes[1].set_xticks([1,5,15,30],['1','5','15','30']);axes[1].legend(fontsize=8)
    fig.savefig(figures/'sensitivity.png',dpi=165);plt.close(fig)
    rows=[]
    for model in meta['config']['models']:
        g=primary[primary.model.eq(model)&primary.noise_sd.eq(0)].set_index('sampling_minutes');a=g.loc[1]
        rows.append(f"| {LABELS[model]} | {a.H_spot_mean:.3f} | {a.H_IV_mean:.3f} | {a.H_RV_mean:.3f} | {g.loc[5].H_RV_mean:.3f} | {g.loc[30].H_RV_mean:.3f} |")
    table='\n'.join(rows)
    ou=primary[primary.model.eq('OU')&primary.noise_sd.eq(0)&primary.sampling_minutes.eq(5)].iloc[0]
    max_refine=max(r['max_absolute_path_delta_H'] for r in refine['rows'])
    report=f'''# Rough or Just Noisy? — a reproducible simulation study

Independent side project by Martin Valachy, with disclosed AI assistance. Version 1: replication and sensitivity analysis, not a novelty claim or completed forecasting study.

## Result

The same volatility model produces different finite-band slopes depending on whether we observe spot samples, integrated variance or realized variance. In the fixed Brownian OU experiment, spot local H is 0.5, but 5-minute log-RV has mean H-tilde **{ou.H_RV_mean:.3f}** (Monte Carlo SE **{ou.H_RV_mcse:.4f}**), even without added price noise. Coarser sampling further lowers the descriptive estimate in these scenarios. This establishes a controlled counterexample to identifying spot roughness from a naive RV slope. It does not identify the latent roughness of market volatility.

## Design, frozen before the run

Run `{study_run}`; config `configs/side_project.json`; source `src/roughnoisy/study.py`; amendment A08. Three stationary Gaussian log-spot-variance models: Brownian OU and generalized Cauchy with local H=0.1/0.3, beta=0.5. Common stationary log variance 0.25, half-correlation time 22 trading days, mean daily variance 0.0001. The Cauchy process is not fractional OU.

128 independent paths per model, 504 sessions each, 780 steps/session (30-second trading-clock intervals). Set v=0.0001 exp(X-0.25/2); approximate daily IV by the mean of the left-point v values. Conditional fine log-price increments are independent Gaussian with variance v/780. Price shocks are independent of volatility. There are no overnight periods, jumps, leverage or quote dynamics. The model is a driftless log-price experiment, not a fitted return or trading model.

Sum fine log returns before squaring on nested 1/5/15/30-minute grids. RV=sum(r²), RQ=M/3 sum(r⁴); qhat=2RQ/(M RV²) is only a finite-sampling diagnostic. Add iid log-price noise with SD 0, 1 or 3 basis points on the fine price grid, sharing the same noise and efficient-price path across nested samples. These noise settings are illustrative, not calibrated to equities.

For each path, compute the mean squared increments of log spot variance, log grid IV or log RV at lags 1 through 10 sessions. H-tilde is half the OLS slope of log variogram against log lag. Sensitivities use bands 1–5 and 1–22. Local H, the finite-band spot slope, and the IV/RV slopes are different quantities. No classification test or confidence interval for market H is constructed.

## Main table

Zero added price noise; lags 1–10. Entries are means of path estimates, not slopes of pooled moments.

| Process | Spot samples | Grid IV | RV 1 min | RV 5 min | RV 30 min |
|---|---:|---:|---:|---:|---:|
{table}

![Measurement chain](../docs/figures/measurement_chain.png)

Integration raises the finite-band slope here; return sampling lowers it. Neither operation preserves the spot local exponent as a naive daily RV regression target. A coarse sampling interval reduces the number of returns and increases finite-sampling variation, even when prices have no added observation noise. With added iid price noise, finer sampling also inflates the RV level. No universal optimal frequency is inferred.

![Sampling and noise](../docs/figures/sampling_noise.png)
![Sensitivity](../docs/figures/sensitivity.png)

## Verification and numerical resolution

The pilot used four paths/model before the fixed full run. The covariance implementation passed an independently parameterized formula, inverse-spectrum implied covariance, and dense Cholesky Monte Carlo checks. Existing OU analytic and Gaussian embedding tests provide separate controls. RV/RQ from summed increments agree with an independent cumulative-price sampling construction. Constant-volatility tests check E[RV]=IV, E[RQ]=IV² and E[qhat]=2/(M+2), and verify endpoint-noise inflation.

For the full experiment, the maximum cell error relative to the exact conditional expectation E[RV|v]=grid IV+2M noise_SD² was **{meta['conditional_RV_expectation_max_error']:.4%}**. This is a check of mean RV, not a proof of all distributional properties.

A separate coupled step-doubling diagnostic used 16 paths/model and 1560 versus 780 steps/session, with an independent centered-cross-product slope implementation. Maximum absolute path change in the IV slope was **{max_refine:.6f}**, below the preset 0.03 path tolerance; all mean changes were below 0.01. Run `{refine['run_id']}`. This supports the stated grid resolution for this diagnostic, not exact continuous-time integration.

Monte Carlo SEs use independent paths as units. Within-path days, frequencies and lags are dependent. Error bars are mean ±1.96 Monte Carlo SE; they describe simulation precision, not estimator coverage or market uncertainty.

## Interpretation and limits

The result replicates and illustrates an established measurement issue. It neither proves that market volatility is smooth nor refutes rough volatility models. Observation-aware inference can still support roughness; no claim is made that accounting for noise must recover H=0.5. The result is conditional on three fixed Gaussian models, one persistence/marginal-variance setting, artificial noise, a finite trading clock and the chosen lag bands. There is no forecasting superiority, trading-profitability, calibrated identification power, equivalence or market latent-H claim. The larger registered forecast study remains deferred and its original boundaries are unchanged.

## Reproduce

From the repository root: `python -m pip install -e ".[demo]"`; `python -m pytest tests/test_science.py tests/test_study.py -q`; `python scripts/run_study.py --pilot` for a short check, then `python scripts/run_study.py` for the fixed experiment; `python scripts/check_study_refinement.py`; `python scripts/build_side_project.py`. The demo notebook provides a smaller executable walk-through. All these paths are synthetic-only and require no account or vendor data. Generated run IDs/timings differ; compare numerical outputs with tolerances. The full run on the recorded local environment took {meta['seconds']:.1f} seconds; this is not a runtime guarantee.

## Literature and attribution

- Cont and Das, *Rough volatility: fact or artefact?* (2024 journal publication; author version https://arxiv.org/abs/2203.13820): realized proxies can display apparent roughness under nonrough spot dynamics. Our naive slope is not their normalized-variation estimator.
- Fukasawa, Takabatake and Westphal, *Is Volatility Rough?* (author version https://arxiv.org/abs/1905.04852): estimation error can create misleading scaling; their observation-aware method still finds empirical roughness.
- Bennedsen, Lunde and Pakkanen, *Decoupling the short- and long-term behavior of stochastic volatility* (2022): generalized Cauchy covariance and separation of short-lag roughness from persistence. The existing source card and pinned source version document the equation used here.

AI assistance: code, analysis, checks and drafting were produced with Codex under Martin's direction. Automated independent checks are recorded; independent human review is not claimed. See AI_USE.md. This synthetic report contains no market observations or restricted data.
'''
    (R/'manuscript/SYNTHETIC_STUDY.md').write_text(report,encoding='utf-8')
    (output/'SYNTHETIC_STUDY.md').write_text(report.replace('../docs/figures/',''),encoding='utf-8')
    for name in ['measurement_chain.png','sampling_noise.png','sensitivity.png']: shutil.copy2(figures/name,output/name)
    shutil.copy2(R/'results/side_project/summary.csv',output/'SIMULATION_SUMMARY.csv')
    artifacts=['docs/figures/measurement_chain.png','docs/figures/sampling_noise.png','docs/figures/sensitivity.png','manuscript/SYNTHETIC_STUDY.md']
    build_run=record_run('side_project_report',{'status':'completed','study_run_id':study_run,'refinement_run_id':refine['run_id'],
        'code_sha256':sha(__file__),'artifacts':{a:sha(R/a) for a in artifacts},'empirical_inputs_read':empirical})
    if empirical:
        v=load_csv(R/'results/volare_training_descriptive.csv',['symbol','frequency_minutes','H_tilde','qhat_median','observed_sessions','run_id'])
        bridge=json.loads((R/'results/legacy_source_review.json').read_text())
        vr='\n'.join(f'| {r.symbol} | {r.frequency_minutes} | {r.H_tilde:.3f} | {r.observed_sessions} |' for r in v.itertuples())
        annex=f'''# Private empirical annex — not included in the distributable package

Training observations only. This annex summarizes earlier independently checked analyses; no additional observations were acquired to force an outcome. Vendor redistribution rights for empirical derivatives remain unverified. Do not publish this annex or its plots without resolving them.

## Stock descriptives

VOLARE, MSFT/JPM/XOM, 2015–2016; log-RV slopes over lags 1–10. Run `volare_training_20261021T174857Z`; independent centered-cross-product check `phase1_training_figures_20261021T175026Z`.

| Symbol | RV grid (minutes) | H-tilde | Sessions |
|---|---:|---:|---:|
{vr}

These are descriptive sample estimates for three stocks. They do not identify spot H or decide between rough and smooth models. RQ units/session definitions remain assumed; qhat is excluded from the headline evidence. The synthetic noise was not fitted to these estimates.

## SPY construction case study

Fixed January-2014 SPYRM comparison: 24/42 RV pairs exceed the frozen 1% plus absolute tolerances; reference RQ scale/construction remain unresolved. Run `phase1_R1_training_pilot_20261021T174751Z`. Unknown RQ units were not converted to improve agreement.

Legacy seconds SAS pilot: 20 January-2007 sessions and two fixed 2014 overlap days. Independent live construction and four exported-minute RV/RQ recomputations passed. The overlap bridge fails {bridge['outside_frozen_tolerance']}/{bridge['comparison_rows']} comparisons. Run `{bridge['run_id']}`. Both routes choose venue D, but eligible counts and timestamp precision differ. Two short sampled-price spikes dominate the January-2 minute discrepancy. Their precise origin is unresolved; no causal label, outlier deletion, condition expansion or source pooling is imposed.

The legacy inventory lacks 2011-02-08 and ends July 2014. The existing millisecond training sample supplies 1008 sessions, below the original 1250-day rolling window. The registered forecasting contest is deferred, not shortened or passed. All validation and final observations remain unopened.

## Overall result

In simulation, the data-generating mechanism is known and we can separate aggregation from sampling/noise. In markets, the current estimates are conditional on vendor construction. The empirical discrepancy therefore limits interpretation rather than validating a preferred latent mechanism. This is an honest descriptive/reproducibility result, not a roughness identification or trading result.

Public version 1 contains the synthetic experiment, tests and report. This private annex records the empirical work without redistributing restricted observations or assuming permission for derived figures. Human understanding/review remains open.
'''
        (output/'PRIVATE_EMPIRICAL_ANNEX.md').write_text(annex,encoding='utf-8')
        for name in ['R1_SPY_reconciliation.png','R2_VOLARE_apparent_roughness.png','LEGACY_SOURCE_DIAGNOSTIC.png']:
            previous=output.parent/name
            if previous.is_file(): shutil.copy2(previous,output/name)
    print(json.dumps({'report_run_id':build_run,'study_run_id':study_run,'output':str(output)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=R/'docs/study_output');p.add_argument('--empirical',action='store_true');a=p.parse_args()
    build(a.output,a.empirical)
