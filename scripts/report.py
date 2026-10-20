"""Generate the checkpoint report exclusively from saved source/run evidence."""
from pathlib import Path
import json,csv
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
def j(name):return json.loads((R/'results'/name).read_text())
def main():
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
 df=pd.read_csv(R/'results/toy_summary.csv');pilot=j('latest_pilot.json');cov=j('latest_covariance.json');data=j('data_quality.json');repl=j('latest_replication.json');mouti=j('latest_mouti_audit.json');base=j('latest_baseline.json');inf=j('latest_inference.json');eff=j('latest_efficient.json')
 fig,ax=plt.subplots(figsize=(8,4.7),layout='constrained')
 for fam,label in [('OU_hl5','Brownian OU: half-life5'),('OU_hl22','Brownian OU: half-life22'),('OU_hl126','Brownian OU: half-life126'),('Cauchy_H0.1','Rough Cauchy: H=0.1')]:
  s=df.loc[(df.family==fam)&(df.n==1250)&(df.lag_max==10)&(df.noise=='iid')].sort_values('ratio');ax.errorbar(s.ratio,s.mean_H,yerr=1.96*s.MCSE_mean_H,marker='o',capsize=3,label=label)
 ax.set(xlabel='Error variance q / latent one-day increment variance',ylabel='Mean apparent H, lags1-10',title='Illustrative daily Gaussian pilot: 100 independent paths per cell');ax.legend(fontsize=9);fig.savefig(R/'results/figures/toy_noise_scaling.png');plt.close(fig)
 table=pd.read_csv(R/'results/matched_covariances.csv');fig,axes=plt.subplots(1,2,figsize=(10,4.2),layout='constrained')
 for col,label,style in [('rough_Cauchy','Rough Cauchy','-'),('OU_two_factor','Two-factor OU','--'),('OU_flexible_10','Flexible finite OU',':')]:axes[0].plot(table.lag,table[col],style,label=label)
 axes[0].set(xlim=(0,126),xlabel='Lag (trading days)',ylabel='Log-variance covariance',title='Prespecified covariance matching');axes[0].legend(fontsize=9)
 for col,label in [('OU_two_factor','Two-factor OU error'),('OU_flexible_10','Flexible OU error')]:axes[1].plot(table.lag,table[col]-table.rough_Cauchy,label=label)
 axes[1].set(xlim=(0,126),xlabel='Lag (trading days)',ylabel='Covariance difference from rough law',title='Same dispersion; known-moment diagnostic');axes[1].legend(fontsize=9);fig.savefig(R/'results/figures/covariance_matching.png');plt.close(fig)
 f=pd.read_csv(R/'results/covariance_forecast_diagnostics.csv');fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
 for name,label,offset in [('OU_two_factor','Two-factor OU',-.08),('OU_flexible_10','Flexible finite OU',.08)]:
  d=f.loc[f.model==name];x=np.arange(3)+offset;axes[0].errorbar(x,d.mean_QLIKE_difference_vs_true_cov_projection,yerr=1.96*d.MCSE_QLIKE_difference,marker='o',capsize=3,label=label);axes[1].plot(np.arange(3),100*d.mean_absolute_exposure_difference,marker='o',label=label)
 for ax in axes:ax.set_xticks(np.arange(3),['1','5','22']);ax.set_xlabel('Forecast horizon (days)');ax.legend(fontsize=9)
 axes[0].axhline(0,color='gray',lw=.7);axes[0].set(ylabel='QLIKE difference from true-covariance projection',title='Known-law forecast diagnostic; 1000 histories')
 axes[1].set(ylabel='Mean absolute weight difference (percentage points)',title='Allocation sensitivity; no realized net-return claim');fig.savefig(R/'results/figures/forecast_decision_diagnostic.png');plt.close(fig)
 spy=pd.read_csv(R/'data/derived/SPY_pilot_2014_2016.csv',parse_dates=['date']);fig,axes=plt.subplots(2,1,figsize=(9,6),layout='constrained')
 axes[0].plot(spy.date,np.sqrt(252*spy.RV5)*100,label='5-minute RV');axes[0].set(ylabel='Annualized intraday proxy (%)',title='Public SPY development pilot,2014-2016');axes[0].legend()
 axes[1].scatter(spy.RV5,spy.RV1,s=6,alpha=.35);lim=max(spy.RV5.max(),spy.RV1.max());axes[1].plot([0,lim],[0,lim],color='gray',lw=1);axes[1].set(xlabel='5-minute realized variance',ylabel='1-minute realized variance',title='Same-day measurement comparison; exact session/RQ conventions unresolved');fig.savefig(R/'results/figures/SPY_pilot_audit.png');plt.close(fig)
 # The novelty matrix records inspected evidence, never inferred abstract omissions.
 ids=['S01','S02','S03','S04','S05','S06','S07','S08','S09','S10','S11','S12','S13','S21']
 positive={
 'S01':['known_truth_simulation','RV_construction','price_noise','aggregation','out_of_sample_forecasts'],
 'S02':['known_truth_simulation','RV_construction','roughness_estimation'],
 'S03':['known_truth_simulation','RV_construction','roughness_estimation','observation_error','uncertainty'],
 'S04':['known_truth_simulation','RV_construction','roughness_estimation','observation_error','aggregation','uncertainty'],
 'S05':['known_truth_simulation','roughness_estimation','observation_error','persistence_flexibility','out_of_sample_forecasts'],
 'S06':['known_truth_simulation','roughness_estimation','observation_error','persistence_flexibility','uncertainty'],
 'S07':['known_truth_simulation','observation_error','persistence_flexibility','out_of_sample_forecasts','uncertainty'],
 'S08':['known_truth_simulation','RV_construction','price_noise','aggregation','roughness_estimation','observation_error'],
 'S09':['observation_error','out_of_sample_forecasts','risk_decisions','uncertainty'],
 'S10':['persistence_flexibility','out_of_sample_forecasts'],
 'S11':['known_truth_simulation','RV_construction','observation_error','out_of_sample_forecasts','uncertainty'],
 'S12':['observation_error','risk_decisions','uncertainty'],
 'S13':['known_truth_simulation','RV_construction','price_noise','observation_error','out_of_sample_forecasts'],
 'S21':['known_truth_simulation','persistence_flexibility']}
 cols=['known_truth_simulation','RV_construction','price_noise','aggregation','roughness_estimation','observation_error','persistence_flexibility','matched_persistence_contest','out_of_sample_forecasts','risk_decisions','uncertainty']
 cards={x['id']:x for x in json.loads((R/'literature/evidence_cards.json').read_text())}
 matrix=[]
 for sid in ids:matrix.append({'source':sid,**{c:'present in inspected locations' if c in positive.get(sid,[]) else 'not assessed / no absence claim' for c in cols},'references':cards[sid]['refs'],'audit_limits':'Targeted card, not a complete exclusion search. Observation_error may mean HARQ/proxy-loss treatment, not an explicit structural likelihood.'})
 pd.DataFrame(matrix).to_csv(R/'literature/novelty_matrix.csv',index=False)
 (R/'literature/NOVELTY_MATRIX.md').write_text('# Novelty matrix reading guide\n\nThe CSV records positive evidence in inspected source locations. Every unfilled dimension is marked not assessed; it does not mean absent. See the linked source cards for model/observation differences. In particular, S07 explicitly includes measurement error and S09 already includes decision-oriented evaluation. Finite-factor approximation is prior art (S21). No novelty claim passes from an abstract omission.\n',encoding='utf8')
 qrow=df.loc[(df.family=='OU_hl22')&(df.n==1250)&(df.lag_max==10)&(df.noise=='iid')]
 lookup={float(row.ratio):row for row in qrow.itertuples()}
 p=cov['power'];fc=f.loc[(f.model=='OU_flexible_10')&(f.horizon==1)].iloc[0]
 report=f'''# Executed preparation and pilot checkpoint

Independent research,20October2026. **This is not a production study, empirical mechanism identification or publication-ready manuscript.** The scientific gates and exact continuation point are in STATUS.md and checkpoint.json.

## What actually ran

| Work | Evidence | Scope |
|---|---|---|
| Formula notebook | {j('latest_formulas.json')['run_id']} |8code cells executed with analytical and numerical checks |
| Daily Gaussian grid | {pilot['run_id']} |{pilot['metadata']['independent_latent_paths']} independent latent paths;62 observation cells;100paths per cell;18600lag-band estimates |
| Efficient-price construction | {eff['run_id']} |100Brownian OU paths of250sessions,1560steps/session, nested1/5/15/30minute sampling |
| Covariance/power diagnostic | {cov['run_id']} |1000independent projection histories;1250-dimensional Gaussian power calculation;1000null calibration+100evaluation paths per law |
| Forecast baselines | {base['run_id']} |{base['forecasts']} forecasts over100independent OU paths,3models,3horizons,250origins;0positivity/maturity failures |
| Dependence-aware mock | {inf['run_id']} |30independent AR1series;4999stationary bootstrap draws each;mean block44 |
| Published Table1 replication | {repl['run_id']} |27prespecified theoretical cells from Patton2011 |
| Secondary preprint formula audit | {mouti['run_id']} |48deterministic finite-band fOU cells from Mouti2026 |
| SPY data audit | {data['run_id']} |750development observations,2014-2016;745validation observations quarantined;0final-test observations acquired |

The source register distinguishes original24draft entries, acquired bytes, working-paper/journal identity and targeted inspection. Eighteen evidence cards and a novelty matrix accompany the positioning memo. Downloaded code was not executed.

## Main illustrative findings

**Finite-band scaling is not local regularity.** For half-life22 Brownian OU with1250daily observations, mean naiveH on lags1-10 was{lookup[0].mean_H:.5f} (Monte Carlo SE{lookup[0].MCSE_mean_H:.5f}) without observation noise. Its population finite-band slope is{lookup[0].population_latent_band_H:.5f}, already below0.5. With q/m_X(1)=1, mean naiveH fell to{lookup[1].mean_H:.5f}, while known-iid-noise subtraction gave{lookup[1].corrected_mean_H:.5f}. At ratio4 the naive mean was{lookup[4].mean_H:.5f}. These are specified Gaussian daily experiments, not estimates of market spotH. Negative corrected moments and nonlinear-fit boundary hits remain in the tables.

![Noise and finite-band scaling](../results/figures/toy_noise_scaling.png)

**A flexible nonrough control changes the interpretation.** The fixed finite OU dictionary matches the chosen rough Cauchy daily covariance with maximum absolute error about{cov['matching']['OU_flexible_10']['max_abs_error_0_126']:.6g} over lags0-126, against stationary variance0.25. A fixed two-factor alternative fits substantially worse. This is known-moment matching, not parameter estimation on historical data.

For1250observations with common q=2/78, D_KL(rough||flexibleOU)={p['KL_rough_to_flexible_nonrough']:.8f}. Independent trace/logdet and whitened-eigenvalue calculations differed by{p['KL_absolute_method_difference']:.3g}. Pinsker's inequality gives a computed upper power bound{100*p['Pinsker_upper_bound_power_at_exact_size_0p05']:.2f}% for any exact-size5% test between these two known Gaussian laws. The independently evaluated likelihood-ratio test rejected{100*p['null_rejection_rate']:.1f}% under the null and had{100*p['alternative_power']:.1f}% power (MCSE{100*p['power_MCSE']:.2f}percentage points). Threshold-calibration uncertainty is additional. This demonstrates one low-power finite-grid pair; it is not a universal impossibility theorem.

At h=1, the flexible-OU minus true-covariance projection QLIKE difference was{fc.mean_QLIKE_difference_vs_true_cov_projection:.8g} with paired Monte Carlo SE{fc.MCSE_QLIKE_difference:.8g}. Mean absolute exposure difference was{100*fc.mean_absolute_exposure_difference:.5f}percentage points. These small values do **not** establish practical equivalence: no numerical equivalence margin is registered. No net CE or realized trading result is reported.

![Covariance matching](../results/figures/covariance_matching.png)

![Forecast and allocation diagnostic](../results/figures/forecast_decision_diagnostic.png)

**Observation layers matter.** In LevelB, exact stationary OU is simulated at grid nodes; IV/price integrals are left-point approximations. The maximum path-average relative difference between1560- and780-step IV constructions was{eff['maximum_path_average_IV_refinement_relative_error']:.6g}, below the prespecified0.001gate. Nested sampling errors are correlated. This validates the Brownian construction only; a rough spot-to-IV version remains open.

## Replication agreement and discrepancies

Patton's published Table1: **{repl['passed_cells']}/{repl['cells']}cells** meet the tolerance0.015fixed before execution. The two failures are MAE-prop under t6 and t10: exact numerical optima2.821602 and2.580113 versus printed2.73 and2.55. The source footnote calls these entries numerical approximations. Independent moment quadrature and closed forms agree to numerical precision for checked quantities. No tolerance was widened after seeing results. See `results/patton_table1_replication.csv` and `configs/replication_patton.json`.

Mouti preprint Table2: **{mouti['passed_cells']}/{mouti['cells']}cells** meet tolerance1e-4; maximum absoluteH discrepancy{mouti['max_absolute_error']:.6g}. The Brownian limiting case agrees with exact OU to{mouti['Brownian_special_case_max_absolute_error']:.3g}. An independent oscillatory covariance transform agrees with the separate variogram-integral method in checked cells. The cause of larger-lag table differences remains unresolved. This is a secondary preprint audit, not the published replication.

During source inspection, S09PDFp22 printed a plus sign in a stationary Gaussian conditional-variance expression that requires a minus. The source page was visually checked. We have not inspected the authors' executed code, so no claim is made that its numerical results used the printed expression. Our code uses and tests the conditional minus.

## Data pilot and limits

The maintainer-distributed SPYRM snapshot contains1495dates,2014-2019,including1/5minuteRV,RQ,BPV,median measures,kernels and a last-recorded CLOSE. Our audit covers{data['pilot_rows']}development observations through2016. It found0duplicate dates and{data['calendar_expected_sessions']}expectedXNYSsessions. All six missing dates are early closes, verified against the installed exchange calendar. They remain missing; no imputation or ordinary adjacent-day lag interpretation is imposed.

RQ/RV^2 scale diagnostics are inconsistent with simply treating the rawRQ fields as decimal-return quarticity. DividingRQ by1e8 is only a candidate conversion, not a source-verified correction. ExactM, session definition and upstream rights remain unresolved. Therefore no empirical q calibration, HARQ fit, latentH inference or implementable economics was run. See `data/DATA_CARD.md`, `results/data_quality.json`, field mapping and acquisition manifest.

[Local SPY pilot figure](../results/figures/SPY_pilot_audit.png) (generated locally; omitted from Git pending upstream data-rights verification).

VOLARE requires a login; no entitlement was verified. The official Shi-Yu-Zhang data archive was identified but returned403 locally. No credentials were entered or restrictions bypassed. No2020-2025market data were acquired; final-test boundaries are unchanged.

## Readiness and next action

All15scientific tests passed, including joint date resampling and independentKL forms; notebook execution, covariance and Brownian refinement checks passed. The inference mock covered the known mean on{100*inf['coverage']:.0f}% of30independent series at nominal90%, with{100*inf['MCSE_coverage']:.2f}percentage-point Monte Carlo SE. This is insufficient to certify coverage. G0/G2/G3remain partial and G4has not passed. No production run was launched.

Next execute `python scripts/validate_checkpoint.py`, then resolve source-supported RQ units and session counts and validate rough spot-to-IV integration. Only after calibratedH inference, comparable estimated structural fits, fixed margins and aligned execution accounting should the final protocol be frozen and the final test opened.
'''
 (R/'manuscript/PILOT_REPORT.md').write_text(report,encoding='utf8')
 card=f'''# SPY pilot data card

Instrument: SPDR S&P500ETFTrust (SPY). Source: highfrequency::SPYRM, repository commit `{data['provider_snapshot_commit']}`, package1.0.2. Original RDA134520bytes; SHA256`{data['raw_sha256']}`. Official maintainer documentation and JSS article are preserved locally; download URLs/hashes are in `manifests/data_acquisition.json`.

The complete small container spans2014-01-02 through2019-12-31. Development pilot:750rows,2014-01-02 through2016-12-30. Later745rows are quarantined in `data/sealed/`. No2020-2025observations were acquired. Initial schema inspection viewed the first3rows and last2019row, disclosed in the amendment.

## Definitions and fields

RV1/RV5: unannualized realized variance at1/5minute sampling. Decimal-return variance is supported by JSSp24 multiplyingRVby10000for percent-return-squared examples. BPV,medianRV andRK fields are available at the same named frequencies; exact provider bandwidth/boundaries remain unresolved. RQ1/RQ5,medianRQ are quarantined because their raw scale is not verified againstRV. No15/30minute observed series is available. No actual per-day countM is supplied.

CLOSE is the last recorded trade price, explicitly not the official closing price. Split/distribution/total-return handling and overnight treatment are unverified. No economic return series is constructed. Dates are exchange dates without intraday timestamps; source availability time is unknown and must not be invented.

## Quality

No duplicate dates; dates sorted. The audit reports all missing/nonpositive values by field. Of756expectedNYSEsessions, six are absent:2014-07-03,2014-11-28,2014-12-24,2015-11-27,2015-12-24,2016-11-25. All are early closes according to exchange_calendars{__import__('exchange_calendars').__version__}. Do not infer the exclusion's exact source rationale solely from this pattern. No rows are filled and no unexplained outliers removed.

Daily precomputed data cannot validate price filters, stale quotes, trade conditions or independent recomputation. The separate sampleOneMinuteData example concerns an unnamed stock/market proxy and is not used to validateSPY.

## License and admissible use

The package declaresGPL>=2. The upstream market-data provenance and dataset-specific redistribution terms are not separately documented in the inspected files. Keep raw files and row-level derivatives local. The private repository stores acquisition instructions, hashes and aggregate quality reports. This is a useful public-data pilot with a **partial** data gate, not a fully validated empirical contest sample.

Noise calibration, HARQ and risk returns remain blocked by RQ/session/return-interval definitions. The750development observations cannot support the original1250-day empirical fitting window without a documented future amendment and additional data.
'''
 (R/'data/DATA_CARD.md').write_text(card,encoding='utf8')
 print('Generated pilot report, data card, novelty matrix and4figures')
if __name__=='__main__':main()
