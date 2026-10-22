import sys
from pathlib import Path
import numpy as np
from scipy.signal import lfilter
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_source_replication import ewma,finite_band,longest_run


def test_EWMA_independent_linear_filter_and_information_boundary():
    rng=np.random.default_rng(534);x=np.exp(rng.normal(-9,.4,300));decay=.94
    expected=np.r_[x[0],lfilter([1-decay],[1,-decay],x[1:],zi=[decay*x[0]])[0]]
    np.testing.assert_allclose(ewma(x),expected,atol=1e-18,rtol=1e-13)
    altered=x.copy();altered[200:]*=100
    np.testing.assert_array_equal(ewma(x)[:200],ewma(altered)[:200])
    np.testing.assert_allclose(ewma(np.full(300,.0001)),.0001,rtol=1e-13)
    with pytest.raises(ValueError): ewma([.01,np.nan,.02])


def test_missing_dates_preserve_endpoint_lag_counts_and_slope():
    values=np.array([0.,1.,np.nan,3.,4.,5.,6.,7.])
    h,counts=finite_band(values,3)
    assert counts==[5,4,4]
    # Linear calendar trend: E[(X(t+k)-X(t))^2]=k^2 even with a hole.
    assert h==pytest.approx(1.,abs=1e-12)
    compressed,_=finite_band(values[np.isfinite(values)],3)
    assert abs(compressed-h)>.01


def test_disagreement_duration_preserves_both_boundaries():
    assert longest_run([])==0
    assert longest_run([False,False])==0
    assert longest_run([True,True])==2
    assert longest_run([True,True,False,True,True,True])==3


def test_thin_opening_grid_is_reported_missing_without_losing_other_grids():
    import datetime as dt
    import pandas as pd
    root=Path(__file__).resolve().parents[1]
    sys.path[:0]=[str(root/'wrds_queries'),str(root/'tmp/guide_render')]
    pytest.importorskip('duckdb')
    import wrds_download_all as engine
    from source_replication import SourceReplication
    obj=SourceReplication.__new__(SourceReplication);obj.engine=engine
    day='2014-01-02';obj.calendar={day:{'open_seconds':34200,'close_seconds':57600,'early_close':False}}
    seconds=np.arange(34220,57601,5,dtype=float)
    frame=pd.DataFrame({'date':dt.date.fromisoformat(day),'ts_seconds':seconds,'price':100*np.exp((seconds-34200)*1e-7),
        'size':100.,'exchange':'P','sale_condition_raw':'','correction_raw':'00','sequence_raw':None,'time_nano_raw':None})
    rows=obj.compute(frame,day,'QQQ','synthetic_thin_open')
    indexed={r['frequency_seconds']:r for r in rows}
    assert indexed[15]['M_observed']<indexed[15]['M_expected']
    assert indexed[15]['RV'] is None and indexed[15]['RQ'] is None
    assert indexed[30]['M_observed']==indexed[30]['M_expected'] and indexed[30]['RV']>0
