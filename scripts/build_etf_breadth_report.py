"""Report all frozen A13 outcomes after independent numerical acceptance."""
from pathlib import Path
import argparse, html, json, shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from phase1_support import ROOT, record_run, sha

BASE='millisecond_time__millisecond_flags';LEGACY='legacy_time__legacy_flags'
RESTORE='legacy_restore_modern_category_B'
CASE_LABELS={BASE:'Modern reference', LEGACY:'Legacy','millisecond_time__legacy_flags':'Modern time only',
 'legacy_time__millisecond_flags':'Modern conditions only', RESTORE:'B restored (diagnostic)'}
GRIDS=[15,30,60,300,900,1800];GRID_LABELS=['15s','30s','1m','5m','15m','30m']


def load(name, columns):
    path=ROOT/('results/etf_breadth_'+name+'.csv')
    pd.read_csv(path, usecols=columns, nrows=5)
    return pd.read_csv(path, usecols=columns)


def build(output):
    output=Path(output).resolve();output.mkdir(parents=True, exist_ok=True)
    figures=output/'figures';figures.mkdir(exist_ok=True)
    cfg=json.loads((ROOT/'configs/etf_breadth.json').read_text())
    analysis=json.loads((ROOT/'results/etf_breadth_analysis.json').read_text())
    checked=json.loads((ROOT/'results/etf_breadth_independent_check.json').read_text())
    if checked['status']!='passed_checks' or checked['analysis_run_id']!=analysis['run_id']:
        raise ValueError('Independent check must bind current A13 analysis')
    inc=load('incidence',['symbol','frequency_seconds','case','eligible_dates','RV_valid_pairs','RV_missing_pairs',
        'RV_material_days','RV_material_fraction','RQ_valid_pairs','RQ_missing_pairs','RQ_material_days','RQ_material_fraction'])
    hs=load('H',['symbol','frequency_seconds','case','lag_max','H_tilde','H_common','reference_H_common','H_difference_common',
        'lag_endpoint_pairs','common_endpoint_pairs'])
    risk=load('risk',['symbol','frequency_seconds','case','post_warmup_origins','mean_absolute_weight_difference',
        'mean_absolute_uncapped_difference','origins_above_5pp','state_ratio_outside_factor_1_1','both_capped_fraction','cap_attenuation_fraction'])
    intervals=load('intervals',['symbol','frequency_seconds','case','measure','mean_block','valid_bootstrap_draws',
        'lower_95_percentile','upper_95_percentile'])
    panel=cfg['panel'];plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    captions={};files=[]
    def save(fig, name, caption):
        fig.savefig(figures/(name+'.png'), dpi=180, bbox_inches='tight')
        fig.savefig(figures/(name+'.pdf'), bbox_inches='tight');plt.close(fig)
        captions[name]=caption;files.extend([figures/(name+'.png'), figures/(name+'.pdf')])
    legacy=inc[inc['case'].eq(LEGACY)]
    for measure in ['RV','RQ']:
        fig, ax=plt.subplots(figsize=(10,4.8), layout='constrained')
        data=legacy.pivot(index='symbol', columns='frequency_seconds', values=measure+'_material_fraction').reindex(index=panel, columns=GRIDS)
        im=ax.imshow(data.to_numpy(), vmin=0, vmax=1, cmap='Blues', aspect='auto')
        for i, symbol in enumerate(panel):
            for j, freq in enumerate(GRIDS):
                row=legacy[legacy.symbol.eq(symbol)&legacy.frequency_seconds.eq(freq)].iloc[0]
                value=data.iloc[i, j]
                ax.text(j, i, f"{int(row[measure+'_material_days'])}/{int(row[measure+'_valid_pairs'])}",
                    ha='center', va='center', color='white' if value>.55 else 'black', fontsize=11)
        ax.set_xticks(range(6), GRID_LABELS);ax.set_yticks(range(4), panel);ax.set_xlabel('Within-session sampling interval')
        ax.set_title(f'Legacy versus modern {measure}: material dates / valid eligible pairs')
        fig.colorbar(im, ax=ax, label='Fraction of valid eligible dates')
        save(fig,'incidence_'+measure.lower(), f'All four funds and all six grids. Primary sample excludes already observed January 2014 and fixed discovery dates. '
             f'{measure} materiality factor is {cfg[measure+"_material_factor"]}; reciprocal lower boundary. Missing pairs do not count as agreement. Each cell reports its denominator.')
    crossed=[LEGACY,'millisecond_time__legacy_flags','legacy_time__millisecond_flags', RESTORE]
    fig, axes=plt.subplots(2,2, figsize=(12,8), layout='constrained', sharey=True)
    for ax,(measure, freq) in zip(axes.flat,[('RV',60),('RV',300),('RQ',60),('RQ',300)]):
        for i, case in enumerate(crossed):
            y=[inc.loc[inc.symbol.eq(s)&inc.frequency_seconds.eq(freq)&inc['case'].eq(case), measure+'_material_fraction'].iloc[0] for s in panel]
            ax.bar(np.arange(4)+(i-1.5)*.19, y, width=.19, label=CASE_LABELS[case])
        ax.set_xticks(range(4), panel);ax.set_ylim(0,1);ax.set_title(f'{freq//60}-minute {measure}');ax.set_ylabel('Material fraction of valid pairs')
    handles, labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles, labels, loc='outside lower center', ncol=2)
    save(fig,'crossed_conditions','All fixed crossed constructions at 1/5 minutes; full numeric denominators and all other grids are in the incidence table. Component effects can interact through selection, venue choice and medians. B restoration remains diagnostic.')
    fig, axes=plt.subplots(2,2, figsize=(11,7.8), layout='constrained', sharey=True)
    for ax, symbol in zip(axes.flat, panel):
        for case in [BASE, LEGACY, RESTORE]:
            part=hs[hs.symbol.eq(symbol)&hs['case'].eq(case)&hs.lag_max.eq(10)].set_index('frequency_seconds').reindex(GRIDS)
            ax.plot(range(6), part.H_tilde, marker='o', label=CASE_LABELS[case])
        ax.set_xticks(range(6), GRID_LABELS);ax.set_title(symbol);ax.set_ylabel('Finite-band H-tilde, unitless')
    handles, labels=axes.flat[0].get_legend_handles_labels();fig.legend(handles, labels, loc='outside lower center', ncol=3)
    save(fig,'finite_band_slopes','Descriptive lags 1-10 over the full 398-session calendar, including already observed January/discovery dates. Gaps retain calendar endpoints. Source-comparison slopes with common endpoint support, and bands 5/22, are included in the full H table. No latent-H inference.')
    fig, axes=plt.subplots(1,2, figsize=(11,4.7), layout='constrained', sharey=True)
    for ax, freq in zip(axes,[60,300]):
        rows=risk[risk['case'].eq(LEGACY)&risk.frequency_seconds.eq(freq)].set_index('symbol').reindex(panel)
        x=np.arange(4)
        ax.bar(x-.18,100*rows.mean_absolute_uncapped_difference, width=.36, label='Before cap')
        ax.bar(x+.18,100*rows.mean_absolute_weight_difference, width=.36, label='After 100% cap')
        ax.set_xticks(x, panel);ax.set_title(f'{freq//60}-minute RV input');ax.set_ylabel('Mean absolute position gap, percentage points')
        for i, origins in enumerate(rows.post_warmup_origins):
            if origins==0:ax.text(i,.3,'withheld', ha='center', color='#555555', fontsize=9)
    axes[0].legend()
    save(fig,'cap_comparison','Fixed lambda .94,10% annual volatility target,100% exposure cap,126-session warmup; 272 dependent origins if histories are complete. Compare raw gaps as well as attenuation percentages: a large attenuation of a tiny gap is not a large economic effect. No returns or profitability evaluated.')
    fig, ax=plt.subplots(figsize=(10,4.7), layout='constrained')
    for i, freq in enumerate([60,300]):
        point=[];lower=[];upper=[]
        for s in panel:
            point.append(legacy.loc[legacy.symbol.eq(s)&legacy.frequency_seconds.eq(freq),'RV_material_fraction'].iloc[0])
            row=intervals[intervals.symbol.eq(s)&intervals.frequency_seconds.eq(freq)&intervals['case'].eq(LEGACY)&intervals.measure.eq('RV')&intervals.mean_block.eq(22)].iloc[0]
            lower.append(row.lower_95_percentile);upper.append(row.upper_95_percentile)
        y=np.arange(4)+(i-.5)*.2
        ax.hlines(y, lower, upper, color=f'C{i}', lw=3);ax.scatter(point, y, label=f'{freq//60}-minute RV', color=f'C{i}')
    ax.set_yticks(range(4), panel);ax.set_xlim(0,1);ax.set_xlabel('Material-date fraction; paired stationary-bootstrap 95% percentile interval');ax.legend()
    save(fig,'paired_intervals','Primary mean-date block 22, 3,999 draws. The same resampled calendar indices are shared across every fund/construction/grid; 11/44 sensitivities are fully reported. Intervals are exploratory, assumption-dependent and not corrected simultaneous comparisons. Funds are not independent replications.')
    full_tables={'incidence':inc,'H':hs,'risk':risk,'intervals':intervals}
    for name, frame in full_tables.items():
        path=output/('A13_'+name+'.csv');frame.to_csv(path, index=False);files.append(path)
    key=legacy[legacy.frequency_seconds.isin([60,300])].merge(risk[risk['case'].eq(LEGACY)], on=['symbol','frequency_seconds','case'], validate='one_to_one')
    rows=[]
    for symbol in panel:
        for freq in [60,300]:
            r=key[key.symbol.eq(symbol)&key.frequency_seconds.eq(freq)].iloc[0]
            rows.append(f"| {symbol} | {freq//60} | {int(r.RV_material_days)}/{int(r.RV_valid_pairs)} | {int(r.RQ_material_days)}/{int(r.RQ_valid_pairs)} | "
                +(f'{100*r.mean_absolute_weight_difference:.4f}' if r.post_warmup_origins else 'withheld')+' | '
                +(f'{100*r.mean_absolute_uncapped_difference:.4f}' if r.post_warmup_origins else 'withheld')+' | '
                +(str(int(r.origins_above_5pp)) if r.post_warmup_origins else 'withheld')+' |')
    report=f'''# A13: fixed four-fund breadth extension

Analysis: {analysis['run_id']}. Independent check: {checked['run_id']}. Export: {analysis['independent_export_run']}.

Acquired 1,508 new paired fund-days and reused 84 previously observed January 2014 pairs: 1,592 total, 398 sessions per fund. Primary incidence has 376 eligible dates per fund before grid missingness. The fixed funds/window are QQQ, IWM, EFA, TLT over 2013-01-02 through2014-07-31. January 2014 and the fixed discovery dates are excluded from primary incidence. Full-calendar H/risk histories include them and are explicitly descriptive.

## Complete headline comparison: legacy versus modern

RV materiality: ratio outside [1/1.1,1.1]. RQ: outside [1/2,2]. Counts use valid eligible pairs; missing denominators are retained below. Gaps are percentage points of portfolio weight, not percentages of returns. The policy is fixed and does not evaluate returns.

| Fund | Grid, min | RV hits/valid | RQ hits/valid | Mean capped gap, pp | Mean uncapped gap, pp | Origins with gap>=5pp |
|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(rows)+f'''

## Interpretation boundaries

Every fund, grid and construction is reported in the accompanying tables; zero effects and missing values remain. This follow-up shares the SPY historical source regime and known prior results. It broadens asset coverage but is not untouched chronological validation, an independent-fund experiment, a profitability backtest or evidence identifying latent roughness. The original longer forecast study remains deferred. A large cap-masking percentage must be read with its underlying absolute gap. Crossed-condition comparisons diagnose this exact pipeline, not a universal trade filter.

The independent checker recalculated {checked['scalar_checks']} scalars using separate incidence/slope/convolution arithmetic and a restart-segment bootstrap, including a planted altered incidence. Export hashes, independent exchange hours, all 1,592 pairs and daily measurement/correspondence checks passed. These checks do not certify provider semantics, economic truth or independent human review.

## Figures and complete tables

'''
    for name, caption in captions.items():report+=f'\n![{name}](figures/{name}.png)\n\n{caption}\n'
    report+='\nTables: A13_incidence.csv (all 120 rows), A13_H.csv (360), A13_risk.csv (120), A13_intervals.csv (720). Proprietary daily observations remain excluded.\n'
    (output/'A13_BREADTH_REPORT.md').write_text(report, encoding='utf8');files.append(output/'A13_BREADTH_REPORT.md')
    body='<h1>A13: fixed four-fund breadth extension</h1><p>'+html.escape(report.split('## Complete')[0].split('\n',1)[1])+'</p>'
    body+='<h2>Interpretation</h2><p>'+html.escape(report.split('## Interpretation boundaries\n\n')[1].split('## Figures')[0])+'</p>'
    for name, caption in captions.items():body+=f'<figure><img src="figures/{name}.png" alt="{name}"><figcaption>{html.escape(caption)}</figcaption></figure>'
    for name, frame in full_tables.items():body+='<h2>Complete '+name+' table</h2>'+frame.to_html(index=False, float_format=lambda x:f'{x:.6g}')
    page='<!doctype html><html><meta charset="utf-8"><title>A13 breadth report</title><style>body{font:18px system-ui;margin:40px;line-height:1.5;color:#182b3a}img{max-width:1100px;width:100%}table{font-size:13px;border-collapse:collapse}td, th{padding:6px;border:1px solid #ccd5dc}figure{margin:40px 0}p{white-space:pre-line;max-width:1100px}</style>'+body+'</html>'
    (output/'A13_BREADTH_REPORT.html').write_text(page, encoding='utf8');files.append(output/'A13_BREADTH_REPORT.html')
    summary=dict(status='passed_checks', analysis_run=analysis['run_id'], independent_run=checked['run_id'], figures=len(captions),
        source_summary_hashes={n:sha(ROOT/('results/etf_breadth_'+n+'.csv')) for n in full_tables},
        output_files_sha256={p.relative_to(output).as_posix():sha(p) for p in files},
        code_sha256=sha(__file__), proprietary_daily_observations_in_delivery=False)
    run=record_run('etf_breadth_report', summary)
    (ROOT/'results/etf_breadth_report.json').write_text(json.dumps(dict(summary, run_id=run), indent=2)+'\n')
    print(json.dumps(dict(run_id=run, figures=len(captions), output=str(output))));return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output', type=Path, required=True);build(p.parse_args().output)
