"""Frozen A13 breadth summaries. Daily derivatives stay outside this repository."""
from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd
from roughnoisy.core import stationary_bootstrap_means
from analyze_source_replication import BASE, CASES, COLS, ewma, finite_band, longest_run
from phase1_support import ROOT, record_run, sha
from reconcile_spy import calendar_sessions


def load_fixed(private,cfg):
    private=Path(private).resolve()
    if private == ROOT or ROOT in private.parents or 'sealed' in [p.lower() for p in private.parts]:
        raise ValueError('External private training storage required')
    sessions=calendar_sessions(cfg['start'],cfg['end'])
    expected={(day,s) for day in sessions for s in cfg['panel']}
    frames=[]
    for path in sorted((private/'paired').glob('*.csv')):
        # Date-only guard precedes numeric loading; explicit column selection throughout.
        pd.read_csv(path,usecols=['date'],nrows=5)
        dates=pd.read_csv(path,usecols=['date']).date.astype(str).str[:10]
        if not dates.isin(sessions).all(): raise ValueError('Date outside frozen training calendar')
        pd.read_csv(path,usecols=COLS,nrows=5)
        f=pd.read_csv(path,usecols=COLS)
        if len(f)!=30 or f.date.nunique()!=1 or f.symbol.nunique()!=1:
            raise ValueError('One complete fund-day per file required')
        if not f.symbol.isin(cfg['panel']).all(): raise ValueError('Unregistered fund')
        if set(zip(f['case'],f.frequency_seconds)) != {(c,g) for c in CASES for g in cfg['frequencies_seconds']}:
            raise ValueError('Incomplete/duplicate construction-grid matrix')
        day=str(f.date.iloc[0])
        if not f.M_expected.eq(sessions[day]*60//f.frequency_seconds).all():
            raise ValueError('Independent session count differs')
        moments=f[['RV','RQ']].to_numpy(float)
        if np.isinf(moments).any() or np.any(moments<=0) or (f.M_observed>f.M_expected).any() or (f.M_observed<0).any():
            raise ValueError('Invalid measures/grid counts')
        if not (f.RV.isna().eq(f.RQ.isna()) & f.RV.isna().eq(f.M_observed!=f.M_expected)).all():
            raise ValueError('Missing moments disagree with grid completeness')
        frames.append(f)
    data=pd.concat(frames,ignore_index=True)
    if set(zip(data.date,data.symbol))!=expected or data.duplicated(['date','symbol','case','frequency_seconds']).any():
        raise ValueError('Fixed breadth panel incomplete or duplicated')
    return data,sorted(sessions)


def summarize(data,dates,cfg,bootstrap=True):
    base=data[data['case'].eq(BASE)][['date','symbol','frequency_seconds','RV','RQ','selected_exchange']]
    paired=data.merge(base,on=['date','symbol','frequency_seconds'],suffixes=('','_base'),validate='many_to_one')
    eligible=np.array([not d.startswith(cfg['already_observed_month']) and d not in cfg['discovery_dates'] for d in dates])
    incidence=[];hrows=[];risk=[];columns=[];labels=[]
    for symbol in cfg['panel']:
        for frequency in cfg['frequencies_seconds']:
            group=paired[paired.symbol.eq(symbol)&paired.frequency_seconds.eq(frequency)]
            reference=group[group['case'].eq(BASE)].set_index('date').reindex(dates).RV.to_numpy(float)
            for case in sorted(CASES):
                part=group[group['case'].eq(case)].set_index('date').reindex(dates)
                row=dict(symbol=symbol,frequency_seconds=frequency,case=case,eligible_dates=int(eligible.sum()),
                    already_seen_January_dates=int(sum(d.startswith(cfg['already_observed_month']) for d in dates)),
                    venue_switch_days=int(((part.selected_exchange.fillna('NONE')!=part.selected_exchange_base.fillna('NONE'))&eligible).sum()))
                for measure,factor in [('RV',cfg['RV_material_factor']),('RQ',cfg['RQ_material_factor'])]:
                    logs=np.log(part[measure].to_numpy(float)/part[measure+'_base'].to_numpy(float))
                    valid=np.isfinite(logs)&eligible
                    hits=(np.abs(logs)>np.log(factor))&valid
                    row.update({measure+'_valid_pairs':int(valid.sum()),measure+'_missing_pairs':int((eligible&~valid).sum()),
                        measure+'_material_days':int(hits.sum()),measure+'_material_fraction':float(hits.sum()/valid.sum()) if valid.any() else np.nan,
                        measure+'_median_ratio':float(np.exp(np.median(logs[valid]))) if valid.any() else np.nan,
                        measure+'_mean_absolute_log_ratio':float(np.abs(logs[valid]).mean()) if valid.any() else np.nan})
                    columns.extend([hits.astype(float),valid.astype(float)])
                    labels.append((symbol,frequency,case,measure))
                incidence.append(row)
                values=part.RV.to_numpy(float);common=np.isfinite(values)&np.isfinite(reference)
                for band in [5,10,22]:
                    h,counts=finite_band(np.log(values),band)
                    hc,paired_counts=finite_band(np.where(common,np.log(values),np.nan),band)
                    hr,reference_counts=finite_band(np.where(common,np.log(reference),np.nan),band)
                    if paired_counts!=reference_counts: raise ValueError('Paired endpoint supports differ')
                    hrows.append(dict(symbol=symbol,frequency_seconds=frequency,case=case,lag_max=band,
                        H_tilde=h,H_common=hc,reference_H_common=hr,H_difference_common=hc-hr,
                        lag_endpoint_pairs=json.dumps(counts),common_endpoint_pairs=json.dumps(paired_counts),
                        classification='full observed overlap including January/discovery dates; descriptive'))
                common_fields=dict(symbol=symbol,frequency_seconds=frequency,case=case)
                if not (np.isfinite(values).all() and np.isfinite(reference).all()):
                    risk.append(dict(**common_fields,post_warmup_origins=0,
                        classification='withheld: incomplete calendar grid; no imputation/compression'))
                    continue
                state=ewma(values,cfg['EWMA_lambda']);refstate=ewma(reference,cfg['EWMA_lambda'])
                raw=cfg['target_annual_volatility']/np.sqrt(cfg['annual_sessions']*state)
                refraw=cfg['target_annual_volatility']/np.sqrt(cfg['annual_sessions']*refstate)
                capped=np.minimum(cfg['weight_cap'],raw);refcap=np.minimum(cfg['weight_cap'],refraw)
                sl=slice(cfg['EWMA_warmup'],None);gap=np.abs(capped[sl]-refcap[sl]);uncapped=np.abs(raw[sl]-refraw[sl])
                mean_uncapped=float(uncapped.mean());mean_capped=float(gap.mean());ratio=state[sl]/refstate[sl]
                risk.append(dict(**common_fields,post_warmup_origins=len(gap),mean_absolute_weight_difference=mean_capped,
                    mean_absolute_uncapped_difference=mean_uncapped,max_absolute_weight_difference=float(gap.max()),
                    origins_above_5pp=int((gap>=.05).sum()),longest_run_above_5pp_sessions=longest_run(gap>=.05),
                    state_ratio_outside_factor_1_1=int((np.abs(np.log(ratio))>np.log(1.1)).sum()),
                    median_state_ratio=float(np.median(ratio)),max_state_ratio=float(ratio.max()),min_state_ratio=float(ratio.min()),
                    both_capped_fraction=float(((raw[sl]>=cfg['weight_cap'])&(refraw[sl]>=cfg['weight_cap'])).mean()),
                    cap_attenuation_fraction=1-mean_capped/mean_uncapped if mean_uncapped>0 else np.nan,
                    classification='full observed overlap; fixed risk input for next session; no return/profit evaluation'))
    intervals=[]
    if bootstrap:
        matrix=np.column_stack(columns)
        for block in cfg['date_blocks']:
            draws=stationary_bootstrap_means(matrix,np.random.default_rng(np.random.SeedSequence([cfg['bootstrap_seed'],block])),
                draws=cfg['bootstrap_draws'],block=block)
            for index,(symbol,freq,case,measure) in enumerate(labels):
                valid=draws[:,2*index+1]>0
                values=draws[valid,2*index]/draws[valid,2*index+1]
                intervals.append(dict(symbol=symbol,frequency_seconds=freq,case=case,measure=measure,mean_block=block,
                    valid_bootstrap_draws=int(valid.sum()),lower_95_percentile=float(np.quantile(values,.025)) if len(values) else np.nan,
                    upper_95_percentile=float(np.quantile(values,.975)) if len(values) else np.nan,
                    classification='paired shared-date exploratory percentile interval; no simultaneous/multiplicity claim'))
    return dict(incidence=incidence,H=hrows,risk=risk,intervals=intervals),paired


def analyze(private):
    private=Path(private).resolve();cfg=json.loads((ROOT/'configs/etf_breadth.json').read_text())
    verified=json.loads((ROOT/'results/etf_breadth_export_verified.json').read_text())
    if verified['status']!='passed_checks' or verified['archive_sha256'] is None:
        raise ValueError('Verify export before analysis')
    # Bind analysis to the currently verified local package, not a stale acceptance label.
    meta=json.loads((private/'A13_PACKAGE_METADATA.json').read_text())
    if meta['rule_hash']!=verified['rule_hash']:raise ValueError('Local verified rule differs')
    for member in meta['members']:
        if sha(private/member['path'])!=member['sha256']:raise ValueError('Changed private member since verification')
    data,dates=load_fixed(private,cfg)
    tables,paired=summarize(data,dates,cfg)
    paired.to_csv(private/'A13_private_paired_ratios.csv',index=False)
    result=dict(status='passed_checks',input_symbol_days=len(data)//30,calendar_dates=len(dates),panel=cfg['panel'],
        primary_eligible_dates_per_fund=next(iter(tables['incidence']))['eligible_dates'],
        previous_January_pairs=84,new_symbol_days=len(data)//30-84,
        independent_export_run=verified['run_id'],source_rule_hash=verified['rule_hash'],
        code_sha256=sha(__file__),config_sha256=sha(ROOT/'configs/etf_breadth.json'),
        helper_code_sha256=sha(ROOT/'scripts/analyze_source_replication.py'),
        table_rows={name:len(rows) for name,rows in tables.items()},
        classification=cfg['classification'],same_bootstrap_calendar_indices_across_all_funds=True,
        bootstrap_draws=cfg['bootstrap_draws'],date_blocks=cfg['date_blocks'],
        proprietary_daily_rows_in_repo=False,sealed_observations_opened=False,published_online=False)
    run=record_run('etf_breadth_analysis',result)
    for name,rows in tables.items():pd.DataFrame(rows).assign(run_id=run).to_csv(ROOT/('results/etf_breadth_'+name+'.csv'),index=False)
    (ROOT/'results/etf_breadth_analysis.json').write_text(json.dumps(dict(result,run_id=run),indent=2)+'\n')
    print(json.dumps(dict(result,run_id=run)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--private',type=Path,required=True)
    analyze(p.parse_args().private)
