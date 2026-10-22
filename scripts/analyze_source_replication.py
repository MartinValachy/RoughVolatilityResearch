"""A10 aggregate analysis; row-level derivatives stay private. Never opens sealed data."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
from roughnoisy.core import stationary_bootstrap_means
from roughnoisy.compatibility import compare_daily
from phase1_support import ROOT as R,record_run,sha
from reconcile_spy import calendar_sessions

BASE='millisecond_time__millisecond_flags'
LEGACY='legacy_time__legacy_flags'
CASES={BASE,LEGACY,'millisecond_time__legacy_flags','legacy_time__millisecond_flags','legacy_restore_modern_category_B'}
COLS=['date','symbol','case','frequency_seconds','RV','RQ','M_expected','M_observed','selected_exchange','raw_trades','after_conditions','after_venue']


def finite_band(values,maximum=10):
    """Calendar array with NaNs: retain endpoint lags, never compress missing dates."""
    x=np.asarray(values,float);moments=[];counts=[]
    for lag in range(1,maximum+1):
        valid=np.isfinite(x[lag:])&np.isfinite(x[:-lag]);d=x[lag:][valid]-x[:-lag][valid]
        counts.append(len(d));moments.append(float(d@d/len(d)) if len(d) else np.nan)
    if not np.isfinite(moments).all() or np.any(np.asarray(moments)<=0): return np.nan,counts
    a=np.log(np.arange(1,maximum+1));b=np.log(moments)
    return float(((a-a.mean())@(b-b.mean()))/(2*((a-a.mean())@(a-a.mean())))),counts


def ewma(values,decay=.94):
    x=np.asarray(values,float)
    if not len(x) or not np.isfinite(x).all() or np.any(x<=0): raise ValueError('EWMA requires complete positive history')
    result=np.empty_like(x);result[0]=x[0]
    for i in range(1,len(x)):result[i]=decay*result[i-1]+(1-decay)*x[i]
    return result


def longest_run(mask):
    """Duration on the uncompressed ordered session array, including boundaries."""
    padded=np.r_[False,np.asarray(mask,bool),False]
    starts=np.flatnonzero(np.diff(padded.astype(int))==1)
    ends=np.flatnonzero(np.diff(padded.astype(int))==-1)
    return int((ends-starts).max()) if len(starts) else 0


def analyze(private,pilot=False):
    private=Path(private).resolve()
    if private==R or R in private.parents: raise ValueError('Vendor derivatives must remain private outside repository')
    cfg=json.loads((R/'configs/source_replication.json').read_text())
    sessions=calendar_sessions(cfg['start'],cfg['end'])
    paths=sorted((private/'paired').glob('*.csv'))
    if not paths: raise ValueError('No A10 paired aggregates')
    frames=[]
    for p in paths:
        pd.read_csv(p,usecols=COLS,nrows=5);f=pd.read_csv(p,usecols=COLS)
        if not f.date.between(cfg['start'],cfg['end']).all() or not f.symbol.isin(cfg['panel']).all(): raise ValueError('A10 boundary violation')
        if len(f)!=30 or f.duplicated(['date','symbol','case','frequency_seconds']).any(): raise ValueError('Incomplete/duplicate case matrix')
        if set(f['case'])!=CASES or set(f.frequency_seconds)!={15,30,60,300,900,1800}: raise ValueError('Unexpected construction/grid')
        if f.date.nunique()!=1 or f.symbol.nunique()!=1: raise ValueError('Source file must hold one symbol-day')
        day=str(f.date.iloc[0])
        if day not in sessions or not f.M_expected.eq(sessions[day]*60//f.frequency_seconds).all(): raise ValueError('Grid count disagrees with independent exchange calendar')
        if not f.symbol.eq(cfg['main_symbol']).all() and not f.date.str.startswith(cfg['panel_month']).all(): raise ValueError('Cross-asset day outside fixed month')
        if np.isinf(f[['RV','RQ']].to_numpy(float)).any(): raise ValueError('Infinite source moment')
        if (f.M_observed>f.M_expected).any() or (f[['RV','RQ']]<=0).any().any(): raise ValueError('Invalid source measures')
        missing=f[['RV','RQ']].isna().any(axis=1)
        if not (missing==(f.M_observed!=f.M_expected)).all(): raise ValueError('Missing moments do not agree with grid counts')
        frames.append(f)
    data=pd.concat(frames,ignore_index=True)
    if data.duplicated(['date','symbol','case','frequency_seconds']).any(): raise ValueError('Duplicate source-date input')
    base=data[data['case'].eq(BASE)][['date','symbol','frequency_seconds','RV','RQ','selected_exchange']]
    joined=data.merge(base,on=['date','symbol','frequency_seconds'],suffixes=('','_base'),validate='many_to_one')
    joined=joined.assign(log_RV_ratio=np.log(joined.RV/joined.RV_base),log_RQ_ratio=np.log(joined.RQ/joined.RQ_base))
    # Independent, key-based outer audit: missing/invalid pairs never become agreement.
    audit_fields=['date','symbol','frequency_seconds','RV','RQ','M_expected','M_observed']
    audit_reference=data.loc[data['case'].eq(BASE),audit_fields]
    audit_counts={}
    for case in sorted(CASES):
        audited=compare_daily(audit_reference,data.loc[data['case'].eq(case),audit_fields])
        if audited.status.isin(['missing_candidate','missing_reference','invalid_counts','session_count_disagreement','invalid_moments']).any():
            raise ValueError('Independent compatibility audit rejected '+case)
        direct=joined[joined['case'].eq(case)].set_index(['date','symbol','frequency_seconds'])
        cross=audited.set_index(['date','symbol','frequency_seconds']).reindex(direct.index)
        for field in ['RV','RQ']:
            np.testing.assert_allclose(np.exp(direct['log_'+field+'_ratio']),cross[field+'_ratio'],rtol=1e-12,atol=0,equal_nan=True)
        audit_counts[case]={str(k):int(v) for k,v in audited.status.value_counts().items()}
    joined.to_csv(private/'A10_private_case_ratios.csv',index=False)
    new=joined[~joined.date.isin(cfg['discovery_dates'])]
    rows=[]
    for (symbol,freq,case),g in new.groupby(['symbol','frequency_seconds','case']):
        valid_RV=np.isfinite(g.log_RV_ratio);valid_RQ=np.isfinite(g.log_RQ_ratio)
        rows.append({'symbol':symbol,'frequency_seconds':freq,'case':case,'new_paired_days':len(g),
            'RV_valid_pairs':int(valid_RV.sum()),'RQ_valid_pairs':int(valid_RQ.sum()),
            'RV_missing_pairs':int((~valid_RV).sum()),'RQ_missing_pairs':int((~valid_RQ).sum()),
            'RV_material_days':int((g.log_RV_ratio.abs()>cfg['RV_material_log_ratio']).sum()),
            'RQ_material_days':int((g.log_RQ_ratio.abs()>cfg['RQ_material_log_ratio']).sum()),
            'RV_material_fraction':float((g.loc[valid_RV,'log_RV_ratio'].abs()>cfg['RV_material_log_ratio']).mean()),
            'RQ_material_fraction':float((g.loc[valid_RQ,'log_RQ_ratio'].abs()>cfg['RQ_material_log_ratio']).mean()),
            'venue_switch_days':int((g.selected_exchange.fillna('NONE')!=g.selected_exchange_base.fillna('NONE')).sum()),
            'median_RV_ratio':float(np.exp(g.log_RV_ratio.median())),
            'median_RQ_ratio':float(np.exp(g.log_RQ_ratio.median())),
            'mean_absolute_log_RV_ratio':float(g.log_RV_ratio.abs().mean()),
            'mean_absolute_log_RQ_ratio':float(g.log_RQ_ratio.abs().mean())})
    dates=sorted(sessions)
    primary=joined[joined.symbol.eq('SPY')];covered=sorted(primary.date.unique())
    missing=sorted(set(dates)-set(covered));full=len(missing)==0
    if not pilot:
        expected_pairs={(d,'SPY') for d in dates}|{(d,s) for d in dates if d.startswith(cfg['panel_month']) for s in cfg['panel']}
        actual_pairs=set(zip(data.date,data.symbol))
        if actual_pairs!=expected_pairs: raise ValueError('Full fixed symbol-day sample is incomplete or contaminated')
    Hrows=[];riskrows=[];intervals=[]
    if full:
        indicator_columns=[];indicator_labels=[]
        eligible=np.array([d not in cfg['discovery_dates'] for d in dates],float)
        for freq in [15,30,60,300,900,1800]:
            g=primary[primary.frequency_seconds.eq(freq)]
            for case,part in g.groupby('case'):
                values=part.set_index('date').reindex(dates).RV.to_numpy(float)
                reference=g[g['case'].eq(BASE)].set_index('date').reindex(dates).RV.to_numpy(float)
                common=np.isfinite(values)&np.isfinite(reference)
                for band in [5,10,22]:
                    h,counts=finite_band(np.log(values),band)
                    hc,common_counts=finite_band(np.where(common,np.log(values),np.nan),band)
                    hr,ref_counts=finite_band(np.where(common,np.log(reference),np.nan),band)
                    if common_counts!=ref_counts: raise ValueError('Paired H endpoint support diverged')
                    Hrows.append({'symbol':'SPY','frequency_seconds':freq,'case':case,'lag_max':band,'H_tilde':h,
                        'H_tilde_common_endpoints':hc,'reference_H_tilde_common_endpoints':hr,
                        'H_difference_common_endpoints':hc-hr,'common_endpoint_pairs':json.dumps(common_counts),
                        'lag_endpoint_pairs':json.dumps(counts),'classification':'full overlap including discovery dates; descriptive only'})
                if case==LEGACY:
                    pg=part.set_index('date').reindex(dates)
                    for field,threshold in [('RV',cfg['RV_material_log_ratio']),('RQ',cfg['RQ_material_log_ratio'])]:
                        logratio=pg['log_'+field+'_ratio'].to_numpy();valid=np.isfinite(logratio)*eligible
                        indicator_columns.extend([(np.abs(logratio)>threshold)*valid,valid])
                        indicator_labels.append((freq,field))
                if not np.isfinite(values).all():
                    riskrows.append({'symbol':'SPY','frequency_seconds':freq,'case':case,'post_warmup_origins':0,
                        'classification':'not computed: grid gaps retained; no imputation or compressed EWMA'})
                    continue
                predicted=ewma(values,cfg['EWMA_lambda'])
                weights=np.minimum(cfg['weight_cap'],cfg['target_annual_volatility']/np.sqrt(cfg['annual_sessions']*predicted))
                if not np.isfinite(reference).all():
                    riskrows.append({'symbol':'SPY','frequency_seconds':freq,'case':case,'post_warmup_origins':0,
                        'classification':'not computed: reference grid gaps; no imputation'})
                    continue
                ref_pred=ewma(reference,cfg['EWMA_lambda'])
                ref_weight=np.minimum(cfg['weight_cap'],cfg['target_annual_volatility']/np.sqrt(cfg['annual_sessions']*ref_pred))
                delta=weights-ref_weight;start=cfg['EWMA_warmup'];use=delta[start:]
                riskrows.append({'symbol':'SPY','frequency_seconds':freq,'case':case,'post_warmup_origins':len(use),
                    'mean_absolute_weight_difference':float(np.mean(np.abs(use))),
                    'max_absolute_weight_difference':float(np.max(np.abs(use))),
                    'origins_above_5pp':int((np.abs(use)>=.05).sum()),
                    'longest_run_above_5pp_sessions':longest_run(np.abs(use)>=.05),
                    'mean_signed_weight_difference':float(np.mean(use)),
                    'mean_daily_weight_turnover':float(np.abs(np.diff(weights[start:])).mean()),
                    'reference_mean_daily_weight_turnover':float(np.abs(np.diff(ref_weight[start:])).mean()),
                    'information_boundary':'end-of-session t RV available; weight is an input for t+1, no return evaluation',
                    'classification':'fixed-EWMA risk input disagreement; no portfolio returns/profitability'})
        arr=np.column_stack(indicator_columns)
        for block in cfg['date_blocks']:
            boot=stationary_bootstrap_means(arr,np.random.default_rng(np.random.SeedSequence([cfg['bootstrap_seed'],block])),draws=cfg['bootstrap_draws'],block=block)
            for k,(freq,field) in enumerate(indicator_labels):
                valid=boot[:,2*k+1]>0;values=boot[valid,2*k]/boot[valid,2*k+1]
                if not len(values): continue
                intervals.append({'frequency_seconds':freq,'measure':field,'mean_block':block,
                    'lower_95_percentile':float(np.quantile(values,.025)),'upper_95_percentile':float(np.quantile(values,.975)),
                    'classification':'exploratory paired-date interval; no multiple-comparison correction or latent-H inference'})
    elif not pilot: raise ValueError('Incomplete main SPY overlap: '+str(len(missing))+' missing sessions; no compressed-calendar analysis')
    summary={'status':'pilot_complete' if pilot else 'passed_checks','input_symbol_days':len(data)//30,
        'matched_input_records':int(data.loc[data['case'].eq(BASE)&data.frequency_seconds.eq(60),'raw_trades'].sum()),
        'main_SPY_expected_days':len(dates),'main_SPY_covered_days':len(covered),'missing_main_dates':missing,
        'full_main_coverage':full,'pilot':pilot,'code_sha256':sha(__file__),'config_sha256':sha(R/'configs/source_replication.json'),
        'discovery_dates_excluded_from_primary_incidence':cfg['discovery_dates'],
        'independent_source_measure_checks':'passed on WRDS before export; preserved in acquisition manifest',
        'independent_outer_comparison_audit':audit_counts,
        'no_latent_H_or_profit_claim':True,'published_online':False,'sealed_observations_opened':False}
    run=record_run('source_replication_pilot' if pilot else 'source_replication_analysis',summary)
    for filename,table in [('source_replication_incidence.csv',rows),('source_replication_H.csv',Hrows),
                           ('source_replication_risk.csv',riskrows),('source_replication_intervals.csv',intervals)]:
        if table: pd.DataFrame(table).assign(run_id=run).to_csv(R/'results'/filename,index=False)
    (R/'results/source_replication_analysis.json').write_text(json.dumps(dict(summary,run_id=run),indent=2)+'\n')
    print(json.dumps({'run_id':run,'status':summary['status'],'input_symbol_days':summary['input_symbol_days'],'main_days':len(covered),'missing_main_days':len(missing)}))
    return run


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--private',type=Path,required=True);p.add_argument('--pilot',action='store_true');a=p.parse_args();analyze(a.private,a.pilot)
