"""Independent standard-library recomputation of the A10 empirical tables.

Scientific arithmetic below uses csv/math/statistics, not the analysis module.
Discovery-date removal is an explicitly post-result sensitivity, not a refit.
"""
from pathlib import Path
import argparse,csv,json,math,statistics,itertools,copy
from phase1_support import ROOT as R,record_run,sha

BASE='millisecond_time__millisecond_flags'
LEGACY='legacy_time__legacy_flags'
RESTORE='legacy_restore_modern_category_B'


def read(path,columns):
    with Path(path).open(newline='') as f:
        reader=csv.DictReader(f)
        if not set(columns)<=set(reader.fieldnames): raise ValueError('Columns absent')
        sample=list(itertools.islice(reader,5))
    with Path(path).open(newline='') as f:
        return [{k:row[k] for k in columns} for row in csv.DictReader(f)]


def number(value): return float(value) if value else math.nan


def slope(values,maximum):
    variances=[]
    for k in range(1,maximum+1):
        differences=[(values[t]-values[t-k])**2 for t in range(k,len(values)) if math.isfinite(values[t]) and math.isfinite(values[t-k])]
        variances.append(math.fsum(differences)/len(differences))
    return statistics.linear_regression([math.log(k) for k in range(1,maximum+1)],[math.log(x) for x in variances]).slope/2


def weights(values,cfg):
    lam=cfg['EWMA_lambda']
    states=[lam**t*values[0]+(1-lam)*math.fsum(lam**(t-j)*values[j] for j in range(1,t+1)) for t in range(len(values))]
    return [min(cfg['weight_cap'],cfg['target_annual_volatility']/math.sqrt(cfg['annual_sessions']*x)) for x in states]


def close(a,b):
    if not math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-12): raise AssertionError(f'Independent scalar mismatch: {a}, {b}')


def check(private):
    cfg=json.loads((R/'configs/source_replication.json').read_text());source={}
    columns=['date','symbol','case','frequency_seconds','RV','RQ','selected_exchange']
    for path in sorted((Path(private)/'paired').glob('*.csv')):
        for row in read(path,columns):
            key=(row['date'],row['symbol'],int(row['frequency_seconds']),row['case'])
            if key in source: raise ValueError('Duplicate source key')
            source[key]=dict(RV=number(row['RV']),RQ=number(row['RQ']),venue=row['selected_exchange'])
    dates=sorted({key[0] for key in source if key[1]=='SPY'});assert len(dates)==398
    incidence=read(R/'results/source_replication_incidence.csv',['symbol','frequency_seconds','case','RV_valid_pairs','RQ_valid_pairs','RV_material_days','RQ_material_days'])
    checks=0
    def check_incidence(table):
        for row in table:
            symbol=row['symbol'];freq=int(row['frequency_seconds']);case=row['case']
            records=[(v,source[(day,sym,f,BASE)]) for (day,sym,f,c),v in source.items() if sym==symbol and f==freq and c==case and day not in cfg['discovery_dates']]
            for field,factor in [('RV',1.1),('RQ',2.)]:
                valid=[a[field]/b[field] for a,b in records if math.isfinite(a[field]) and math.isfinite(b[field])]
                assert int(row[field+'_valid_pairs'])==len(valid)
                assert int(row[field+'_material_days'])==sum(x>factor or x<1/factor for x in valid)
    check_incidence(incidence);checks+=4*len(incidence)
    planted=copy.deepcopy(incidence);planted[0]['RV_material_days']=str(int(planted[0]['RV_material_days'])+1)
    try: check_incidence(planted)
    except AssertionError: pass
    else: raise AssertionError('Planted altered incidence was not caught')
    for row in read(R/'results/source_replication_H.csv',['frequency_seconds','case','lag_max','H_tilde','H_difference_common_endpoints']):
        freq=int(row['frequency_seconds']);case=row['case'];band=int(row['lag_max'])
        x=[math.log(source[(d,'SPY',freq,case)]['RV']) for d in dates]
        y=[math.log(source[(d,'SPY',freq,BASE)]['RV']) for d in dates]
        close(slope(x,band),row['H_tilde']);close(slope(x,band)-slope(y,band),row['H_difference_common_endpoints']);checks+=2
    episodes=[]
    for row in read(R/'results/source_replication_risk.csv',['frequency_seconds','case','post_warmup_origins','mean_absolute_weight_difference','max_absolute_weight_difference','origins_above_5pp','longest_run_above_5pp_sessions']):
        freq=int(row['frequency_seconds']);case=row['case']
        x=[source[(d,'SPY',freq,case)]['RV'] for d in dates];y=[source[(d,'SPY',freq,BASE)]['RV'] for d in dates]
        if not all(math.isfinite(v) for v in x+y): assert int(row['post_warmup_origins'])==0;continue
        wx=weights(x,cfg);wy=weights(y,cfg);start=cfg['EWMA_warmup'];delta=[a-b for a,b in zip(wx[start:],wy[start:])]
        mask=[abs(v)>=.05 for v in delta];duration=max([len(list(g)) for value,g in itertools.groupby(mask) if value]+[0])
        close(statistics.fmean(map(abs,delta)),row['mean_absolute_weight_difference']);close(max(map(abs,delta)),row['max_absolute_weight_difference'])
        assert sum(mask)==int(row['origins_above_5pp']) and duration==int(row['longest_run_above_5pp_sessions']);checks+=4
        if freq==60 and case==LEGACY:
            for value,group in itertools.groupby(enumerate(mask),lambda pair:pair[1]):
                items=list(group)
                if value: episodes.append({'start_origin':dates[start+items[0][0]],'end_origin':dates[start+items[-1][0]],'sessions':len(items)})
    sensitivity={}
    for freq in [60,300]:
        x=[source[(d,'SPY',freq,LEGACY)]['RV'] for d in dates];y=[source[(d,'SPY',freq,BASE)]['RV'] for d in dates]
        xr=[b if day in cfg['discovery_dates'] else a for day,a,b in zip(dates,x,y)]
        wx=weights(xr,cfg);wy=weights(y,cfg);delta=[a-b for a,b in zip(wx[cfg['EWMA_warmup']:],wy[cfg['EWMA_warmup']:])]
        logs_x=[math.nan if d in cfg['discovery_dates'] else math.log(v) for d,v in zip(dates,x)]
        logs_y=[math.nan if d in cfg['discovery_dates'] else math.log(v) for d,v in zip(dates,y)]
        sensitivity[str(freq)]={'origins_above_5pp_discovery_effect_standardized':sum(abs(v)>=.05 for v in delta),
            'mean_absolute_weight_difference_discovery_effect_standardized':statistics.fmean(map(abs,delta)),
            'H_legacy_discovery_endpoints_omitted':slope(logs_x,10),'H_modern_discovery_endpoints_omitted':slope(logs_y,10)}
    main=json.loads((R/'results/source_replication_analysis.json').read_text())
    result={'status':'passed_checks','source_run_id':main['run_id'],'scalar_checks':checks,'planted_altered_incidence_detected':True,
        'arithmetic':'csv/math/statistics independent of pandas/NumPy/analysis EWMA and slope',
        'legacy_one_minute_5pp_episodes':episodes,'post_result_discovery_sensitivity':sensitivity,
        'sensitivity_classification':'exploratory after full result; no compressed dates; standardize only two discovery-day variance effects, not a cleaning rule',
        'code_sha256':sha(__file__),'published_online':False,'sealed_observations_opened':False}
    run=record_run('source_result_check',result)
    (R/'results/source_result_check.json').write_text(json.dumps(dict(result,run_id=run),indent=2)+'\n')
    print(json.dumps(dict(result,run_id=run)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--private',type=Path,required=True);a=p.parse_args();check(a.private)
