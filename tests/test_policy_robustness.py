import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_policy_robustness import policy_summary, influence, episode_count
from analyze_source_replication import ewma


def test_scale_and_cap_limiting_cases():
    reference = np.full(20, .01**2/252)
    candidate = 4*reference
    # Uncapped weights 10 versus 5: proportional scaling halves candidate weight.
    free = policy_summary(candidate, reference, .1, 20)
    assert free['mean_absolute_gap'] == pytest.approx(5)
    assert free['cap_attenuation'] == 0
    capped = policy_summary(candidate, reference, .1, 1)
    assert capped['mean_absolute_gap'] == 0
    assert capped['both_saturated_fraction'] == 1
    assert capped['cap_attenuation'] == 1
    equal = policy_summary(reference, reference, .1, 1)
    assert np.isnan(equal['cap_attenuation'])


def test_shock_convolution_initialization_and_cancellation():
    n, decay, warm = 40, .94, 7
    reference = np.full(n, .0001)
    candidate = reference.copy(); candidate[0] *= 2; candidate[10] *= 3
    result = influence(candidate, reference, decay, warm)
    # Independent impulse responses include nonstandard initialized first state.
    explicit = sum(sum(abs(candidate[i]-reference[i])*(decay**t if i == 0 else (1-decay)*decay**(t-i))
                       for i in range(t+1)) for t in range(warm, n))
    assert result['shock_triangle_bound'] == pytest.approx(explicit)
    assert result['net_to_bound_ratio'] == pytest.approx(1)
    alternating = reference.copy(); alternating[10] *= 1.5; alternating[11] *= .5
    result = influence(alternating, reference, decay, warm)
    assert 0 < result['net_to_bound_ratio'] < 1
    assert result['top_five_potential_share'] == pytest.approx(1)


def test_future_input_does_not_change_earlier_state():
    x = np.linspace(.0001, .0003, 50); y = x.copy(); y[35:] *= 100
    np.testing.assert_array_equal(ewma(x, .97)[:35], ewma(y, .97)[:35])


def test_episode_boundaries_and_invalid_states():
    assert episode_count([1, 1, 0, 1, 0, 1, 1]) == 3
    assert episode_count([]) == 0
    with pytest.raises(ValueError): policy_summary([1, float('nan')], [1, 1], .1, 1)
    with pytest.raises(ValueError): influence([1], [1], 1., 0)


def test_shock_at_final_origin_and_no_difference():
    reference = np.ones(10); candidate = reference.copy(); candidate[-1] = 2
    result = influence(candidate, reference, .9, 3)
    assert result['shock_triangle_bound'] == pytest.approx(.1)
    assert result['top_date_index'] == 9
    assert result['top_one_potential_share'] == pytest.approx(1)
    equal = influence(reference, reference, .9, 3)
    assert equal['state_gap_L1'] == 0 and equal['top_date_index'] is None
