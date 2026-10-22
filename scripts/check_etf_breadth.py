"""Independent A13 arithmetic, including block intervals and planted alterations.

Uses csv/math/statistics and explicit EWMA convolution, without importing the
analysis module. The block sampler constructs restart segments independently.
"""
from pathlib import Path
import argparse, copy, csv, itertools, json, math, statistics
import numpy as np
from phase1_support import ROOT, record_run, sha
from reconcile_spy import calendar_sessions

BASE='millisecond_time__millisecond_flags'
CASES=sorted([BASE,'millisecond_time__legacy_flags','legacy_time__millisecond_flags',
              'legacy_time__legacy_flags','legacy_restore_modern_category_B'])


def read(path,columns):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if not set(columns)<=set(reader.fieldnames):raise ValueError('Missing independent-check fields')
        list(itertools.islice(reader,5))
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        return [{key:row[key] for key in columns} for row in csv.DictReader(stream)]


def number(value):return float(value) if value else math.nan


def close(expected,actual):
    actual=number(actual) if isinstance(actual,str) else float(actual)
    if math.isnan(expected) and math.isnan(actual):return
    if not math.isclose(expected,actual,rel_tol=1e-9,abs_tol=1e-11):
        raise AssertionError('Independent A13 scalar differs: '+str((expected,actual)))


def slope(values,band):
    variances=[];counts=[]
    for lag in range(1,band+1):
        diffs=[(values[t]-values[t-lag])**2 for t in range(lag,len(values))
               if math.isfinite(values[t]) and math.isfinite(values[t-lag])]
        counts.append(len(diffs));variances.append(statistics.fmean(diffs) if diffs else math.nan)
    if not all(math.isfinite(v) and v>0 for v in variances):return math.nan,counts
    return statistics.linear_regression([math.log(k) for k in range(1,band+1)],list(map(math.log,variances))).slope/2,counts


def states(values,lam):
    return [lam**t*values[0]+(1-lam)*math.fsum(lam**(t-j)*values[j] for j in range(1,t+1))
            for t in range(len(values))]


def segment_bootstrap(matrix,seed,block,draws):
    """Same registered RNG draws, independent vectorized restart-segment indexing."""
    n=len(matrix);rng=np.random.default_rng(np.random.SeedSequence([seed,block]));position=np.arange(n)
    output=np.empty((draws,matrix.shape[1]//2))
    for draw in range(draws):
        first=rng.integers(n);restart=np.r_[True,rng.random(n-1)<1/block]
        anchors=np.r_[first,rng.integers(n,size=n-1)]
        origin=np.maximum.accumulate(np.where(restart,position,0))
        index=(anchors[origin]+position-origin)%n
        totals=np.sum(matrix[index],axis=0)
        output[draw]=np.divide(totals[::2],totals[1::2],out=np.full(matrix.shape[1]//2,np.nan),where=totals[1::2]>0)
    return output


def check_incidence(source,dates,cfg,table):
    eligible=[d for d in dates if not d.startswith(cfg['already_observed_month']) and d not in cfg['discovery_dates']]
    checks=0
    for row in table:
        symbol,freq,case=row['symbol'],int(row['frequency_seconds']),row['case']
        close(len(eligible),row['eligible_dates']);checks+=1
        records=[(source[(d,symbol,freq,case)],source[(d,symbol,freq,BASE)]) for d in eligible]
        close(sum(a['selected_exchange']!=b['selected_exchange'] for a,b in records),row['venue_switch_days']);checks+=1
        for field,factor in [('RV',cfg['RV_material_factor']),('RQ',cfg['RQ_material_factor'])]:
            ratios=[a[field]/b[field] for a,b in records if math.isfinite(a[field]) and math.isfinite(b[field])]
            logs=[math.log(v) for v in ratios];hits=sum(v>factor or v<1/factor for v in ratios)
            values={field+'_valid_pairs':len(ratios),field+'_missing_pairs':len(eligible)-len(ratios),
                    field+'_material_days':hits,field+'_material_fraction':hits/len(ratios) if ratios else math.nan,
                    field+'_median_ratio':math.exp(statistics.median(logs)) if logs else math.nan,
                    field+'_mean_absolute_log_ratio':statistics.fmean(map(abs,logs)) if logs else math.nan}
            for key,value in values.items():close(value,row[key]);checks+=1
    return checks


def check(private):
    cfg=json.loads((ROOT/'configs/etf_breadth.json').read_text());dates=sorted(calendar_sessions(cfg['start'],cfg['end']))
    source={}
    for path in sorted((Path(private)/'paired').glob('*.csv')):
        for row in read(path,['date','symbol','case','frequency_seconds','RV','RQ','selected_exchange']):
            key=(row['date'],row['symbol'],int(row['frequency_seconds']),row['case'])
            if key in source:raise ValueError('Duplicate private source key')
            source[key]=dict(RV=number(row['RV']),RQ=number(row['RQ']),selected_exchange=row['selected_exchange'])
    expected={(d,s,f,c) for d in dates for s in cfg['panel'] for f in cfg['frequencies_seconds'] for c in CASES}
    if set(source)!=expected:raise ValueError('Independent fixed panel check failed')
    incidence_columns=['symbol','frequency_seconds','case','eligible_dates','venue_switch_days']+[
        f+'_'+field for f in ['RV','RQ'] for field in ['valid_pairs','missing_pairs','material_days','material_fraction','median_ratio','mean_absolute_log_ratio']]
    incidence=read(ROOT/'results/etf_breadth_incidence.csv',incidence_columns)
    checks=check_incidence(source,dates,cfg,incidence)
    altered=copy.deepcopy(incidence);altered[0]['RV_material_days']=str(int(altered[0]['RV_material_days'])+1)
    try:check_incidence(source,dates,cfg,altered)
    except AssertionError:pass
    else:raise AssertionError('Planted incidence change escaped')
    for row in read(ROOT/'results/etf_breadth_H.csv',['symbol','frequency_seconds','case','lag_max','H_tilde','H_common',
                'reference_H_common','H_difference_common','lag_endpoint_pairs','common_endpoint_pairs']):
        s,f,c,k=row['symbol'],int(row['frequency_seconds']),row['case'],int(row['lag_max'])
        values=[source[(d,s,f,c)]['RV'] for d in dates];reference=[source[(d,s,f,BASE)]['RV'] for d in dates]
        x=[math.log(v) if math.isfinite(v) else math.nan for v in values]
        y=[math.log(v) if math.isfinite(v) else math.nan for v in reference]
        common=[math.isfinite(a) and math.isfinite(b) for a,b in zip(x,y)]
        h,counts=slope(x,k);hc,pc=slope([v if ok else math.nan for v,ok in zip(x,common)],k)
        hr,rc=slope([v if ok else math.nan for v,ok in zip(y,common)],k)
        assert counts==json.loads(row['lag_endpoint_pairs']) and pc==rc==json.loads(row['common_endpoint_pairs'])
        for value,key in [(h,'H_tilde'),(hc,'H_common'),(hr,'reference_H_common'),(hc-hr,'H_difference_common')]:
            close(value,row[key]);checks+=1
    risk_columns=['symbol','frequency_seconds','case','post_warmup_origins','mean_absolute_weight_difference',
        'mean_absolute_uncapped_difference','max_absolute_weight_difference','origins_above_5pp','longest_run_above_5pp_sessions',
        'state_ratio_outside_factor_1_1','median_state_ratio','max_state_ratio','min_state_ratio','both_capped_fraction','cap_attenuation_fraction']
    risk=read(ROOT/'results/etf_breadth_risk.csv',risk_columns)
    for row in risk:
        s,f,c=row['symbol'],int(row['frequency_seconds']),row['case']
        x=[source[(d,s,f,c)]['RV'] for d in dates];y=[source[(d,s,f,BASE)]['RV'] for d in dates]
        if not all(math.isfinite(v) for v in x+y):close(0,row['post_warmup_origins']);checks+=1;continue
        state,ref=states(x,cfg['EWMA_lambda']),states(y,cfg['EWMA_lambda'])
        scale=cfg['target_annual_volatility']/math.sqrt(cfg['annual_sessions']);cap=cfg['weight_cap'];start=cfg['EWMA_warmup']
        raw=[scale/math.sqrt(v) for v in state[start:]];refraw=[scale/math.sqrt(v) for v in ref[start:]]
        gaps=[abs(min(cap,a)-min(cap,b)) for a,b in zip(raw,refraw)];ungaps=[abs(a-b) for a,b in zip(raw,refraw)]
        ratios=[a/b for a,b in zip(state[start:],ref[start:])];mask=[v>=.05 for v in gaps]
        duration=max([len(list(g)) for value,g in itertools.groupby(mask) if value]+[0])
        mean,unmean=statistics.fmean(gaps),statistics.fmean(ungaps)
        expected_values=dict(post_warmup_origins=len(gaps),mean_absolute_weight_difference=mean,
            mean_absolute_uncapped_difference=unmean,max_absolute_weight_difference=max(gaps),origins_above_5pp=sum(mask),
            longest_run_above_5pp_sessions=duration,state_ratio_outside_factor_1_1=sum(v>1.1 or v<1/1.1 for v in ratios),
            median_state_ratio=statistics.median(ratios),max_state_ratio=max(ratios),min_state_ratio=min(ratios),
            both_capped_fraction=sum(a>=cap and b>=cap for a,b in zip(raw,refraw))/len(raw),
            cap_attenuation_fraction=1-mean/unmean if unmean>0 else math.nan)
        for key,value in expected_values.items():close(value,row[key]);checks+=1
    columns=[];labels=[]
    for s in cfg['panel']:
        for f in cfg['frequencies_seconds']:
            for c in CASES:
                for field,factor in [('RV',cfg['RV_material_factor']),('RQ',cfg['RQ_material_factor'])]:
                    denominator=[];numerator=[]
                    for d in dates:
                        a,b=source[(d,s,f,c)][field],source[(d,s,f,BASE)][field]
                        valid=math.isfinite(a) and math.isfinite(b) and not d.startswith(cfg['already_observed_month']) and d not in cfg['discovery_dates']
                        denominator.append(float(valid));numerator.append(float(valid and (a/b>factor or a/b<1/factor)))
                    columns.extend([numerator,denominator]);labels.append((s,f,c,field))
    intervals=read(ROOT/'results/etf_breadth_intervals.csv',['symbol','frequency_seconds','case','measure','mean_block',
        'valid_bootstrap_draws','lower_95_percentile','upper_95_percentile'])
    lookup={(r['symbol'],int(r['frequency_seconds']),r['case'],r['measure'],int(r['mean_block'])):r for r in intervals}
    for block in cfg['date_blocks']:
        boot=segment_bootstrap(np.array(columns).T,cfg['bootstrap_seed'],block,cfg['bootstrap_draws'])
        for k,label in enumerate(labels):
            row=lookup[label+(block,)];values=boot[np.isfinite(boot[:,k]),k]
            close(len(values),row['valid_bootstrap_draws'])
            close(float(np.quantile(values,.025)) if len(values) else math.nan,row['lower_95_percentile'])
            close(float(np.quantile(values,.975)) if len(values) else math.nan,row['upper_95_percentile']);checks+=3
    summary=json.loads((ROOT/'results/etf_breadth_analysis.json').read_text())
    result=dict(status='passed_checks',analysis_run_id=summary['run_id'],scalar_checks=checks,
        planted_incidence_change_detected=True,independent_convolution_H_incidence_and_segment_bootstrap=True,
        all_funds_grids_constructions_reported=True,code_sha256=sha(__file__),sealed_observations_opened=False)
    run=record_run('etf_breadth_independent_check',result)
    (ROOT/'results/etf_breadth_independent_check.json').write_text(json.dumps(dict(result,run_id=run),indent=2)+'\n')
    print(json.dumps(dict(result,run_id=run)));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--private',type=Path,required=True);check(p.parse_args().private)
