"""A11: all-policy descriptive sensitivity using existing private A10 aggregates."""
from pathlib import Path
import argparse
import itertools
import json

import numpy as np
import pandas as pd

from analyze_source_replication import BASE, CASES, ewma, longest_run
from phase1_support import ROOT, record_run, sha
from reconcile_spy import calendar_sessions


def episode_count(mask):
    mask = np.asarray(mask, bool)
    return int(np.count_nonzero(mask & ~np.r_[False, mask[:-1]])) if len(mask) else 0


def policy_summary(candidate_state, reference_state, target, cap, annual=252, gap=.05):
    """Summaries of next-session inputs; both state arrays already exclude warmup."""
    a, b = np.asarray(candidate_state, float), np.asarray(reference_state, float)
    if a.shape != b.shape or a.ndim != 1 or not len(a):
        raise ValueError('Equal nonempty state vectors required')
    if not np.isfinite(np.r_[a, b]).all() or np.any(np.r_[a, b] <= 0):
        raise ValueError('Positive finite states required')
    if not all(np.isfinite(v) and v > 0 for v in [target, cap, annual, gap]):
        raise ValueError('Positive finite policy parameters required')
    ua, ub = target / np.sqrt(annual * a), target / np.sqrt(annual * b)
    wa, wb = np.minimum(cap, ua), np.minimum(cap, ub)
    delta = np.abs(wa - wb)
    uncapped = float(np.mean(np.abs(ua - ub)))
    large = delta >= gap
    mean = float(delta.mean())
    return dict(origins=len(a), mean_absolute_gap=mean, max_absolute_gap=float(delta.max()),
                uncapped_mean_absolute_gap=uncapped,
                cap_attenuation=1 - mean / uncapped if uncapped > 0 else np.nan,
                candidate_saturated_fraction=float(np.mean(ua >= cap)),
                reference_saturated_fraction=float(np.mean(ub >= cap)),
                both_saturated_fraction=float(np.mean((ua >= cap) & (ub >= cap))),
                origins_above_5pp=int(large.sum()), episodes_above_5pp=episode_count(large),
                longest_episode_sessions=longest_run(large))


def influence(candidate, reference, decay, warmup):
    """L1 potential shock influence, not nonlinear weight-gap attribution.

    Initialized EWMA gives date zero coefficient decay**t; subsequent dates have
    coefficient (1-decay)*decay**(t-i). Sum only over evaluated origins.
    """
    x, y = np.asarray(candidate, float), np.asarray(reference, float)
    if x.shape != y.shape or x.ndim != 1 or not 0 <= warmup < len(x) or not 0 < decay < 1:
        raise ValueError('Complete matched vectors and valid EWMA settings required')
    if not np.isfinite(np.r_[x, y]).all() or np.any(np.r_[x, y] <= 0):
        raise ValueError('Positive finite RV required')
    n = len(x)
    mass = np.empty(n)
    mass[0] = decay**warmup * (1 - decay**(n-warmup)) / (1-decay)
    for i in range(1, n):
        first = max(i, warmup)
        mass[i] = decay**(first-i) * (1-decay**(n-first))
    potential = np.abs(x-y) * mass
    bound = float(potential.sum())
    actual = float(np.abs(ewma(x, decay)[warmup:] - ewma(y, decay)[warmup:]).sum())
    order = np.argsort(-potential, kind='stable')
    return dict(state_gap_L1=actual, shock_triangle_bound=bound,
                net_to_bound_ratio=actual/bound if bound else np.nan,
                top_one_potential_share=float(potential[order[0]]/bound) if bound else np.nan,
                top_five_potential_share=float(potential[order[:5]].sum()/bound) if bound else np.nan,
                top_date_index=int(order[0]) if bound else None)


def load_private(private, cfg):
    private = Path(private).resolve()
    if private == ROOT or ROOT in private.parents:
        raise ValueError('Private derivatives must be outside the repository')
    path = private/'A10_private_case_ratios.csv'
    cols = ['date', 'symbol', 'case', 'frequency_seconds', 'RV']
    pd.read_csv(path, usecols=cols, nrows=5)
    frame = pd.read_csv(path, usecols=cols)
    frame = frame[frame.symbol.eq(cfg['symbol'])].copy()
    dates = sorted(calendar_sessions(cfg['start'], cfg['end']))
    expected = set(itertools.product(dates, cfg['frequencies_seconds'], CASES))
    keys = list(zip(frame.date, frame.frequency_seconds, frame['case']))
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError('Duplicate, missing or out-of-window source-date matrix')
    if not np.isfinite(frame.RV).all() or (frame.RV <= 0).any():
        raise ValueError('No imputation: complete positive SPY moments required')
    return path, frame, dates


def analyze(private):
    cfg = json.loads((ROOT/'configs/source_policy_robustness.json').read_text(encoding='utf-8'))
    main = json.loads((ROOT/'results/source_replication_analysis.json').read_text(encoding='utf-8'))
    if main['run_id'] != cfg['source_run_id'] or main['status'] != 'passed_checks' or main['pilot']:
        raise ValueError('Frozen complete A10 source run required')
    path, data, dates = load_private(private, cfg)
    warm = cfg['warmup']; evaluated = np.asarray(dates[warm:])
    if not 0 < warm < len(dates):
        raise ValueError('Warmup must retain evaluated origins')
    policy_rows, state_rows, period_rows = [], [], []
    for freq, decay in itertools.product(cfg['frequencies_seconds'], cfg['decays']):
        grid = data[data.frequency_seconds.eq(freq)].pivot(index='date', columns='case', values='RV').reindex(dates)
        reference = grid[BASE].to_numpy()
        ref_state = ewma(reference, decay)[warm:]
        for case in sorted(CASES - {BASE}):
            candidate = grid[case].to_numpy()
            state = ewma(candidate, decay)[warm:]
            common = dict(frequency_seconds=freq, decay=decay, case=case)
            logratio = .5*np.log(ref_state/state)
            item = influence(candidate, reference, decay, warm)
            index = item.pop('top_date_index')
            state_rows.append(dict(common, origins=len(state),
                median_absolute_log_uncapped_weight_ratio=float(np.median(np.abs(logratio))),
                p95_absolute_log_uncapped_weight_ratio=float(np.quantile(np.abs(logratio), .95)),
                max_absolute_log_uncapped_weight_ratio=float(np.max(np.abs(logratio))),
                origins_relative_difference_above_factor=int(np.sum(np.abs(logratio) > np.log(cfg['relative_factor']))),
                top_potential_influence_date=dates[index] if index is not None else '', **item))
            for target, cap in itertools.product(cfg['annual_targets'], cfg['weight_caps']):
                policy_rows.append(dict(common, annual_target=target, weight_cap=cap,
                    **policy_summary(state, ref_state, target, cap, cfg['annual_sessions'], cfg['large_gap'])))
            # Chronological slices use the original A10 policy and uncompressed states.
            for lo, hi in cfg['chronological_blocks']:
                mask = (evaluated >= lo) & (evaluated <= hi)
                row = dict(common, block_start=lo, block_end=hi, origins=int(mask.sum()))
                if mask.any():
                    row.update(policy_summary(state[mask], ref_state[mask], .1, 1., cfg['annual_sessions'], cfg['large_gap']))
                period_rows.append(row)
    policies = pd.DataFrame(policy_rows)
    states = pd.DataFrame(state_rows)
    periods = pd.DataFrame(period_rows)
    outputs = {}
    for name, frame in [('policies', policies), ('states', states), ('periods', periods)]:
        output = ROOT/f'results/source_policy_{name}.csv'
        frame.to_csv(output, index=False)
        outputs[output.relative_to(ROOT).as_posix()] = sha(output)
    result = dict(status='computed_pending_independent_check', source_run_id=main['run_id'],
                  source_input_sha256=sha(path), code_sha256=sha(__file__),
                  config_sha256=sha(ROOT/'configs/source_policy_robustness.json'),
                  protocol_sha256=sha(ROOT/'protocol/A11_POLICY_ROBUSTNESS.md'),
                  source_sessions=len(dates), evaluated_origins=len(evaluated),
                  policies_per_construction_grid=27, policy_rows=len(policies), state_rows=len(states),
                  period_rows=len(periods), outputs_sha256=outputs,
                  classification=cfg['classification'], sealed_observations_opened=False, published_online=False)
    run = record_run('source_policy_robustness', result)
    (ROOT/'results/source_policy_robustness.json').write_text(json.dumps(dict(result, run_id=run), indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(run_id=run, policy_rows=len(policies), state_rows=len(states), period_rows=len(periods))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private', type=Path, required=True)
    analyze(parser.parse_args().private)
