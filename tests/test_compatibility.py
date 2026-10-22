import numpy as np
import pandas as pd
import pytest
from roughnoisy.compatibility import compare_daily


def example():
    return pd.DataFrame({'date':['2014-01-02','2014-01-03'],'symbol':'TEST','frequency_seconds':60,
        'RV':.0001,'RQ':1e-8,'M_expected':390,'M_observed':390})


def test_material_ratio_flags_do_not_rescale_or_mutate():
    ref=example();candidate=ref.copy();candidate.loc[0,['RV','RQ']]*=10000
    original=candidate.copy(deep=True);result=compare_daily(ref,candidate)
    assert result.loc[0,'status']=='material_difference' and result.loc[0,'RV_ratio']==pytest.approx(10000)
    assert result.loc[1,'status']=='no_material_difference'
    pd.testing.assert_frame_equal(candidate,original)
    assert result.attrs['source_equivalence_certified'] is False


def test_missing_session_and_grid_errors_are_not_passes():
    ref=example();candidate=ref.copy();candidate.loc[0,['M_expected','M_observed']]=210
    out=compare_daily(ref,candidate)
    assert out.loc[0,'status']=='session_count_disagreement' and pd.isna(out.loc[0,'RV_material_warning'])
    candidate=ref.iloc[:1].copy();candidate.loc[0,'M_observed']=388;candidate.loc[0,['RV','RQ']]=np.nan
    out=compare_daily(ref,candidate)
    assert out.loc[0,'status']=='incomplete_grid' and out.loc[1,'status']=='missing_candidate'
    assert not out.RV_valid_pair.any()


def test_outer_pairing_is_key_based_and_duplicate_keys_fail():
    ref=example();reordered=ref.iloc[::-1].copy()
    assert compare_daily(ref,reordered).status.eq('no_material_difference').all()
    with pytest.raises(ValueError): compare_daily(ref,pd.concat([ref,ref]))
    bad=ref.copy();bad.loc[0,'RV']=-1
    assert compare_daily(ref,bad).loc[0,'status']=='invalid_moments'
def test_nonfinite_warning_factors_cannot_silently_disable_findings():
    import pandas as pd
    import numpy as np
    import pytest
    from roughnoisy.compatibility import compare_daily
    frame=pd.DataFrame({'date':['2014-01-02'],'symbol':['SYNTHETIC'],'frequency_seconds':[60],
        'RV':[.0001],'RQ':[1e-8],'M_expected':[390],'M_observed':[390]})
    for value in [np.nan,np.inf,-np.inf,1.]:
        with pytest.raises(ValueError):compare_daily(frame,frame,rv_factor=value)
        with pytest.raises(ValueError):compare_daily(frame,frame,rq_factor=value)
    invalid=frame.copy();invalid['M_observed']=391
    assert compare_daily(frame,invalid).status.iloc[0]=='invalid_counts'
