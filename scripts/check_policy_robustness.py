"""Independent csv/math implementation of every A11 policy and state summary."""
from pathlib import Path
import argparse
import copy
import csv
import itertools
import json
import math
import statistics

from phase1_support import ROOT, record_run, sha

BASE = 'millisecond_time__millisecond_flags'
LEGACY = 'legacy_time__legacy_flags'


def read(path, columns=None):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        cols = columns or reader.fieldnames
        if not set(cols) <= set(reader.fieldnames):
            raise ValueError('Missing columns')
        list(itertools.islice(reader, 5))
    with Path(path).open(encoding='utf-8', newline='') as stream:
        return [{k: row[k] for k in cols} for row in csv.DictReader(stream)]


def equal(actual, expected):
    actual = float(actual) if actual != '' else math.nan
    expected = float(expected)
    if math.isnan(actual) and math.isnan(expected):
        return
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12):
        raise AssertionError(f'Independent mismatch: {actual}, {expected}')


def summary(a, b, target, cap, annual, gap):
    ua = [target/math.sqrt(annual*x) for x in a]
    ub = [target/math.sqrt(annual*x) for x in b]
    differences = [abs(min(cap,x)-min(cap,y)) for x,y in zip(ua,ub)]
    flags = [d >= gap for d in differences]
    durations = [len(list(group)) for value,group in itertools.groupby(flags) if value]
    raw = statistics.fmean(abs(x-y) for x,y in zip(ua,ub))
    mean = statistics.fmean(differences)
    return dict(origins=len(a), mean_absolute_gap=mean, max_absolute_gap=max(differences),
                uncapped_mean_absolute_gap=raw, cap_attenuation=1-mean/raw if raw else math.nan,
                candidate_saturated_fraction=sum(x>=cap for x in ua)/len(a),
                reference_saturated_fraction=sum(x>=cap for x in ub)/len(a),
                both_saturated_fraction=sum(x>=cap and y>=cap for x,y in zip(ua,ub))/len(a),
                origins_above_5pp=sum(flags), episodes_above_5pp=len(durations),
                longest_episode_sessions=max(durations+[0]))


def check(private):
    cfg = json.loads((ROOT/'configs/source_policy_robustness.json').read_text(encoding='utf-8'))
    result = json.loads((ROOT/'results/source_policy_robustness.json').read_text(encoding='utf-8'))
    for name, digest in result['outputs_sha256'].items():
        if sha(ROOT/name) != digest: raise ValueError('Result hash changed')
    if sha(ROOT/'configs/source_policy_robustness.json') != result['config_sha256']:
        raise ValueError('Configuration changed')
    source = {}
    # Re-read original paired files rather than the analysis's joined derivative.
    for path in sorted((Path(private)/'paired').glob('SPY_*.csv')):
        for row in read(path, ['date','symbol','frequency_seconds','case','RV']):
            if row['symbol'] != 'SPY': raise ValueError('Unexpected symbol')
            key = (row['date'], int(row['frequency_seconds']), row['case'])
            if key in source: raise ValueError('Duplicate source key')
            source[key] = float(row['RV'])
    dates = sorted({d for d,_,_ in source})
    cases = sorted({c for _,_,c in source if c != BASE})
    assert len(dates) == 398 and dates[0] == cfg['start'] and dates[-1] == cfg['end']
    assert len(cases) == 4 and len(source) == 398*6*5
    # Independent direct convolution, including first-state initialization.
    states, series = {}, {}
    for freq,case in itertools.product(cfg['frequencies_seconds'], cases+[BASE]):
        x = [source[(d,freq,case)] for d in dates]
        assert all(math.isfinite(v) and v>0 for v in x)
        series[(freq,case)] = x
        for decay in cfg['decays']:
            states[(freq,case,decay)] = [decay**t*x[0]+(1-decay)*math.fsum(decay**(t-i)*x[i] for i in range(1,t+1)) for t in range(len(x))]
    checks = 0
    policies = read(ROOT/'results/source_policy_policies.csv')
    expected_keys = set(itertools.product(cfg['frequencies_seconds'], cfg['decays'], cases, cfg['annual_targets'], cfg['weight_caps']))
    keys = [(int(r['frequency_seconds']),float(r['decay']),r['case'],float(r['annual_target']),float(r['weight_cap'])) for r in policies]
    assert len(keys) == len(set(keys)) and set(keys) == expected_keys
    def check_policy_row(row):
        f,c,l = int(row['frequency_seconds']),row['case'],float(row['decay'])
        a,b = states[(f,c,l)][cfg['warmup']:],states[(f,BASE,l)][cfg['warmup']:]
        expected = summary(a,b,float(row['annual_target']),float(row['weight_cap']),cfg['annual_sessions'],cfg['large_gap'])
        for name,value in expected.items(): equal(row[name],value)
        return len(expected)
    for row in policies: checks += check_policy_row(row)
    altered = copy.deepcopy(policies[0]);altered['mean_absolute_gap'] = str(float(altered['mean_absolute_gap'])+.001)
    try: check_policy_row(altered)
    except AssertionError: pass
    else: raise AssertionError('Planted policy alteration not detected')
    state_table = read(ROOT/'results/source_policy_states.csv')
    state_keys = [(int(r['frequency_seconds']),float(r['decay']),r['case']) for r in state_table]
    assert len(state_keys)==len(set(state_keys)) and set(state_keys)==set(itertools.product(cfg['frequencies_seconds'],cfg['decays'],cases))
    for row in state_table:
        f,c,l = int(row['frequency_seconds']),row['case'],float(row['decay'])
        x,y = series[(f,c)],series[(f,BASE)]
        a,b = states[(f,c,l)][cfg['warmup']:],states[(f,BASE,l)][cfg['warmup']:]
        logs = sorted(abs(.5*math.log(v/u)) for u,v in zip(a,b))
        position = .95*(len(logs)-1);lo=math.floor(position);hi=math.ceil(position)
        p95=logs[lo]+(position-lo)*(logs[hi]-logs[lo])
        # Sum nonnegative propagation weights explicitly, without closed-form mass.
        potential = [abs(x[i]-y[i])*math.fsum(l**t if i==0 else (1-l)*l**(t-i)
                      for t in range(max(i,cfg['warmup']),len(x))) for i in range(len(x))]
        bound = math.fsum(potential); actual=math.fsum(abs(u-v) for u,v in zip(a,b))
        order = sorted(range(len(x)), key=lambda i: -potential[i])
        expected = dict(origins=len(a), median_absolute_log_uncapped_weight_ratio=statistics.median(logs),
                        p95_absolute_log_uncapped_weight_ratio=p95,max_absolute_log_uncapped_weight_ratio=max(logs),
                        origins_relative_difference_above_factor=sum(v>math.log(cfg['relative_factor']) for v in logs),
                        state_gap_L1=actual,shock_triangle_bound=bound,
                        net_to_bound_ratio=actual/bound if bound else math.nan,
                        top_one_potential_share=potential[order[0]]/bound if bound else math.nan,
                        top_five_potential_share=math.fsum(potential[i] for i in order[:5])/bound if bound else math.nan)
        for name,value in expected.items(): equal(row[name],value);checks+=1
        assert row['top_potential_influence_date']==(dates[order[0]] if bound else '')
        checks+=1
    periods=read(ROOT/'results/source_policy_periods.csv')
    period_keys=[(int(r['frequency_seconds']),float(r['decay']),r['case'],r['block_start'],r['block_end']) for r in periods]
    expected_periods={(f,l,c,lo,hi) for f,l,c in state_keys for lo,hi in cfg['chronological_blocks']}
    assert len(period_keys)==len(set(period_keys)) and set(period_keys)==expected_periods
    for row in periods:
        f,c,l=int(row['frequency_seconds']),row['case'],float(row['decay'])
        indices=[t for t in range(cfg['warmup'],len(dates)) if row['block_start']<=dates[t]<=row['block_end']]
        equal(row['origins'],len(indices));checks+=1
        if not indices:
            assert all(row[name]=='' for name in ['mean_absolute_gap','max_absolute_gap','cap_attenuation'])
            continue
        a=[states[(f,c,l)][i] for i in indices];b=[states[(f,BASE,l)][i] for i in indices]
        for name,value in summary(a,b,.1,1.,cfg['annual_sessions'],cfg['large_gap']).items():
            equal(row[name],value);checks+=1
    primary=read(ROOT/'results/source_replication_risk.csv')
    overlaps=0
    for row in primary:
        if row['case']==BASE: continue
        matches=[p for p in policies if p['case']==row['case'] and p['frequency_seconds']==row['frequency_seconds'] and float(p['decay'])==.94 and float(p['annual_target'])==.1 and float(p['weight_cap'])==1.]
        assert len(matches)==1
        for original,current in [('mean_absolute_weight_difference','mean_absolute_gap'),('max_absolute_weight_difference','max_absolute_gap'),('origins_above_5pp','origins_above_5pp'),('longest_run_above_5pp_sessions','longest_episode_sessions')]:
            equal(row[original],matches[0][current]);overlaps+=1
    output=dict(status='passed_checks',analysis_run_id=result['run_id'],scalar_checks=checks,
                original_A10_overlap_scalars=overlaps,planted_policy_alteration_detected=True,
                arithmetic='csv/math/statistics, original paired inputs, direct state convolution and shock sums; no analysis imports',
                code_sha256=sha(__file__),source_run_id=cfg['source_run_id'],
                analysis_code_sha256=result['code_sha256'],classification=cfg['classification'],
                sealed_observations_opened=False,published_online=False)
    run=record_run('source_policy_check',output)
    (ROOT/'results/source_policy_check.json').write_text(json.dumps(dict(output,run_id=run),indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(run_id=run,scalar_checks=checks,original_A10_overlap_scalars=overlaps,status='passed_checks')))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--private',type=Path,required=True)
    check(parser.parse_args().private)
