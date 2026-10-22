"""Read-only training SPY comparison; report findings, never adjust data."""
from pathlib import Path
import argparse
import csv
import json
import sys
import numpy as np
import pandas as pd
import exchange_calendars as xc
from phase1_support import ROOT, record_run, sha

TOLERANCES = {'RV': {'absolute': 1e-10, 'relative': 0.01},
              'RQ': {'absolute': 1e-14, 'relative': 0.01}}


def calendar_sessions(start, end):
    cal = xc.get_calendar('XNYS')
    schedule = cal.schedule.loc[start:end]
    # Calendar times are UTC-aware in the installed version. No market rows read.
    opens = pd.to_datetime(schedule['open'], utc=True)
    closes = pd.to_datetime(schedule['close'], utc=True)
    minutes = ((closes-opens).dt.total_seconds()/60).astype(int)
    return {str(date.date()): int(m) for date, m in minutes.items()}


def read_training_csv(path, candidates):
    path = Path(path).resolve()
    if 'sealed' in [part.lower() for part in path.parts]:
        raise ValueError('Sealed path refused')
    with path.open(newline='', encoding='utf-8-sig') as stream:
        header = next(csv.reader(stream))
    cols = [name for name in candidates if name in header]
    if 'date' not in cols:
        raise ValueError('date column required')
    # Date-only preflight rejects a misplaced later-period file before numeric loading.
    dates = pd.read_csv(path, usecols=['date'])['date'].astype(str).str[:10]
    parsed = pd.to_datetime(dates, errors='raise')
    if (parsed >= pd.Timestamp('2017-01-01')).any():
        raise ValueError('Training loader refuses later-period rows')
    sample = pd.read_csv(path, usecols=cols, nrows=5)
    print(json.dumps({'file': path.name, 'sample_shape': list(sample.shape)}))
    data = pd.read_csv(path, usecols=cols)
    data['date'] = dates
    return data


def reference_long(frame):
    if {'frequency_seconds','RV','RQ'} <= set(frame):
        return frame.copy()
    parts = []
    for minutes in (1,5):
        needed = {'date', 'RV'+str(minutes), 'RQ'+str(minutes)}
        if not needed <= set(frame):
            raise ValueError('SPYRM needs RV1/RV5/RQ1/RQ5 or long format')
        block = frame[['date','RV'+str(minutes),'RQ'+str(minutes)]].copy()
        block.columns = ['date','RV','RQ']
        block['frequency_seconds'] = 60*minutes
        parts.append(block)
    return pd.concat(parts, ignore_index=True)


def compare(own, reference, sessions, reference_rq_scale=None):
    """Inputs are canonical long frames; calendar is independent of own flags/M."""
    required = {'date','frequency_seconds','RV','RQ','M_observed','early_close'}
    if not required <= set(own):
        raise ValueError('Own file missing required columns: '+str(sorted(required-set(own))))
    ref = reference_long(reference)
    if own.empty:
        raise ValueError('Empty own comparison input')
    findings = []

    def add(date, freq, code, field='', observed=None, expected=None):
        def safe(value):
            if value is None or pd.isna(value):
                return None
            if isinstance(value,(int,float,np.number)) and not np.isfinite(value):
                return str(value)
            return value.item() if hasattr(value, 'item') else value
        findings.append({'date': str(date), 'frequency_seconds': int(freq), 'code': code,
                         'field': field, 'observed': safe(observed), 'expected': safe(expected)})

    # Unknown units are a global block even when raw values happen to match.
    if reference_rq_scale is not None and (not np.isfinite(reference_rq_scale) or reference_rq_scale <= 0):
        raise ValueError('RQ scale must be positive and source-documented')
    for name, frame in [('own',own), ('reference',ref)]:
        if (pd.to_datetime(frame.date) >= pd.Timestamp('2017-01-01')).any():
            raise ValueError('Comparison restricted to training')
        if 'symbol' in frame and set(frame.symbol) != {'SPY'}:
            raise ValueError('SPY-only comparison')
        for row in frame[frame.duplicated(['date','frequency_seconds'], keep=False)].itertuples():
            add(row.date, row.frequency_seconds, 'duplicate_'+name)
        for row in frame.itertuples():
            for field in ('RV','RQ'):
                value = getattr(row,field)
                if not np.isfinite(value) or value <= 0:
                    add(row.date,row.frequency_seconds,'invalid_'+name,field,value)
    if any(item['code'].startswith('duplicate') for item in findings):
        return {'status':'failed','findings':findings,'matched_rows':0,'rq_units_resolved':reference_rq_scale is not None}
    for row in own.itertuples():
        freq = row.frequency_seconds
        if not np.isfinite(freq) or freq <= 0 or freq != int(freq):
            raise ValueError('Invalid frequency')
        minutes = sessions.get(row.date)
        if minutes is None:
            add(row.date,freq,'off_calendar_date')
            continue
        expected_m = minutes*60//int(freq)
        if row.M_observed != expected_m:
            add(row.date,freq,'session_M_mismatch','M_observed',row.M_observed,expected_m)
        if hasattr(row,'M_expected') and row.M_expected != expected_m:
            add(row.date,freq,'expected_M_mismatch','M_expected',row.M_expected,expected_m)
        flag = row.early_close
        # Never interpret the nonempty string "False" as True.
        if isinstance(flag,str):
            mapping = {'true':True,'false':False,'1':True,'0':False,'t':True,'f':False}
            flag = mapping.get(flag.lower())
        if flag is None or pd.isna(flag) or bool(flag) != (minutes<390):
            add(row.date,freq,'early_close_mismatch','early_close',row.early_close,minutes<390)
        if hasattr(row,'session_minutes') and row.session_minutes != minutes:
            add(row.date,freq,'session_minutes_mismatch','session_minutes',row.session_minutes,minutes)
    # Calendar coverage for own, not an assumption that SPYRM contains early closes.
    own_freqs = set(own.frequency_seconds)
    for date in sessions:
        for freq in own_freqs:
            if not ((own.date==date)&(own.frequency_seconds==freq)).any():
                add(date,freq,'missing_own_session')
    common_freqs = sorted(set(ref.frequency_seconds)&own_freqs)
    if not common_freqs and not ref.empty:
        raise ValueError('No common frequencies')
    if ref.empty:
        common_freqs = sorted(own_freqs)
    merged = own[own.frequency_seconds.isin(common_freqs)].merge(
        ref[ref.frequency_seconds.isin(common_freqs)],on=['date','frequency_seconds'],
        how='outer',suffixes=('_own','_ref'),indicator=True)
    matched = 0
    for row in merged.to_dict('records'):
        date, freq = row['date'], row['frequency_seconds']
        if row['_merge'] != 'both':
            add(date,freq,'missing_reference' if row['_merge']=='left_only' else 'missing_own')
            continue
        matched += 1
        for field in ('RV','RQ'):
            value, target = row[field+'_own'], row[field+'_ref']
            if field == 'RQ' and reference_rq_scale is not None:
                target *= reference_rq_scale
            tol = TOLERANCES[field]
            if np.isfinite(value) and np.isfinite(target) and abs(value-target)>tol['absolute']+tol['relative']*abs(target):
                code = 'rq_raw_units_diagnostic' if field=='RQ' and reference_rq_scale is None else 'value_mismatch'
                add(date,freq,code,field,value,target)
    status = 'failed' if findings else ('blocked_reference_RQ_units' if reference_rq_scale is None else 'passed_checks')
    return {'status':status,'findings':findings,'matched_rows':matched,
            'compared_frequency_seconds':common_freqs,
            'own_frequencies_without_reference':sorted(own_freqs-set(common_freqs)),
            'rq_units_resolved':reference_rq_scale is not None,
            'reference_rq_scale':reference_rq_scale,'tolerances':TOLERANCES,
            'rules':'A07-P1_ASSUMED vendor semantics','canonical_RQ_pass_possible':reference_rq_scale is not None}


def planted_check():
    sessions = {'2014-11-26':390,'2014-11-28':210}
    own = pd.DataFrame([{'date':date,'frequency_seconds':freq,'RV':0.0001,'RQ':1e-8,
                         'M_observed':minutes*60//freq,'M_expected':minutes*60//freq,
                         'early_close':minutes<390,'session_minutes':minutes}
                        for date, minutes in sessions.items() for freq in (60,300)])
    ref = own[['date','frequency_seconds','RV','RQ']].copy()
    clean = compare(own, ref, sessions, reference_rq_scale=1)
    broken = own.copy()
    broken.loc[0,'RV'] *= 10000
    broken.loc[0,'RQ'] *= 100000000
    broken.loc[2,'M_observed'] = 390
    broken.loc[2,'early_close'] = False
    report = compare(broken, ref, sessions, reference_rq_scale=1)
    codes = {(r['code'],r['field']) for r in report['findings']}
    passed = clean['status']=='passed_checks' and {
        ('value_mismatch','RV'),('value_mismatch','RQ'),('session_M_mismatch','M_observed'),
        ('early_close_mismatch','early_close')} <= codes
    output = ROOT/'results/reconciliation_planted_findings.csv'
    metadata = {'status':'completed' if passed else 'failed','checks_passed':bool(passed),
                'clean_control':clean,'planted':report,'source_sha256':sha(__file__),
                'classification':'synthetic Tier A planted unit and early-close errors; no vendor data'}
    run_id = record_run('reconcile_planted', metadata)
    for frame, name in [(own,'clean'),(broken,'planted'),(ref,'reference')]:
        frame.to_csv(ROOT/f'tmp/reconcile_{name}.csv',index=False)
    pd.DataFrame([dict(row, run_id=run_id) for row in report['findings']]).to_csv(output,index=False)
    (ROOT/'results/reconciliation_planted_check.json').write_text(json.dumps(dict(metadata,run_id=run_id),indent=2)+'\n')
    print(json.dumps({'run_id':run_id,'checks_passed':bool(passed),'planted_findings':len(report['findings'])}))
    if not passed:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--own',type=Path)
    parser.add_argument('--reference',type=Path,default=ROOT/'data/derived/SPY_pilot_2014_2016.csv')
    parser.add_argument('--documented-reference-rq-scale',type=float)
    parser.add_argument('--scale-source')
    parser.add_argument('--self-test',action='store_true')
    args = parser.parse_args()
    if args.self_test:
        planted_check()
        return
    if not args.own:
        parser.error('--own or --self-test required')
    if args.documented_reference_rq_scale is not None and not args.scale_source:
        parser.error('--scale-source is required for any documented RQ scaling')
    own = read_training_csv(args.own,['date','symbol','frequency_seconds','RV','RQ','M_expected',
                                    'M_observed','early_close','session_minutes'])
    ref = read_training_csv(args.reference,['date','frequency_seconds','RV','RQ','RV1','RV5','RQ1','RQ5'])
    # Restrict comparison to own pilot window, preserving missing sessions within it.
    ref = ref[(ref.date>=own.date.min())&(ref.date<=own.date.max())].copy()
    sessions = calendar_sessions(own.date.min(),own.date.max())
    report = compare(own,ref,sessions,args.documented_reference_rq_scale)
    report.update({'scale_source':args.scale_source,'input_sha256':sha(args.own),
                   'reference_sha256':sha(args.reference),'source_sha256':sha(__file__),
                   'coverage_window':[own.date.min(),own.date.max()],
                   'coverage_limitation':'Edges inferred from own input; specify/prescreen export window separately'})
    run_id = record_run('reconcile_spy',report)
    pd.DataFrame([dict(row,run_id=run_id) for row in report['findings']],
                 columns=['date','frequency_seconds','code','field','observed','expected','run_id']).to_csv(
                     ROOT/'results/R1_reconciliation_findings.csv',index=False)
    (ROOT/'results/R1_reconciliation_summary.json').write_text(json.dumps(dict(report,run_id=run_id),indent=2)+'\n')
    print(json.dumps({'run_id':run_id,'status':report['status'],'findings':len(report['findings'])}))
    if report['status'] != 'passed_checks':
        raise SystemExit(2)


if __name__=='__main__':
    main()
