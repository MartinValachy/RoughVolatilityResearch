"""Synthetic acceptance cases prepared before inspecting new A13 observations."""
import copy, json, math, sys, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_etf_breadth import summarize, load_fixed
from analyze_source_replication import BASE, CASES
from check_etf_breadth import check_incidence, segment_bootstrap, states
from roughnoisy.core import stationary_bootstrap_means
from verify_etf_breadth import verify_archive

ROOT=Path(__file__).resolve().parents[1]
LEGACY='legacy_time__legacy_flags'


@pytest.fixture
def artificial_panel():
    cfg=json.loads((ROOT/'configs/etf_breadth.json').read_text())
    dates=list(pd.bdate_range('2013-02-01',periods=48).strftime('%Y-%m-%d'))+['2014-01-02','2014-07-03']
    cfg['EWMA_warmup']=10
    rows=[]
    for index,day in enumerate(dates):
        for symbol in cfg['panel']:
            for frequency in cfg['frequencies_seconds']:
                for case in CASES:
                    multiplier=2.0 if symbol=='EFA' and case==LEGACY else 1.0
                    rv=1e-4*math.exp(.2*math.sin(index/5))*multiplier
                    missing=symbol=='QQQ' and frequency==15 and case==LEGACY and index==6
                    rows.append(dict(date=day,symbol=symbol,frequency_seconds=frequency,case=case,
                        RV=np.nan if missing else rv,RQ=np.nan if missing else rv**2,
                        selected_exchange='P',M_expected=390*60//frequency,
                        M_observed=390*60//frequency-int(missing)))
    return pd.DataFrame(rows),dates,cfg


def test_constant_scale_H_invariance_and_exact_incidence(artificial_panel):
    data,dates,cfg=artificial_panel;tables,_=summarize(data,dates,cfg,bootstrap=False)
    incidence=pd.DataFrame(tables['incidence'])
    assert len(incidence)==4*6*5
    row=incidence.query("symbol=='EFA' and case==@LEGACY and frequency_seconds==60").iloc[0]
    assert row.eligible_dates==48 and row.RV_material_days==48 and row.RQ_material_days==48
    assert row.RV_material_fraction==1 and row.RV_median_ratio==pytest.approx(2)
    for h in tables['H']:
        if h['symbol']=='EFA' and h['case']==LEGACY:assert h['H_difference_common']==pytest.approx(0,abs=2e-14)
    for risk in tables['risk']:
        if risk['symbol']=='EFA' and risk['case']==LEGACY:
            assert risk['median_state_ratio']==pytest.approx(2)
            assert risk['state_ratio_outside_factor_1_1']==40


def test_missing_grid_preserves_denominator_and_withholds_only_affected_EWMA(artificial_panel):
    data,dates,cfg=artificial_panel;tables,_=summarize(data,dates,cfg,bootstrap=False)
    row=next(r for r in tables['incidence'] if (r['symbol'],r['case'],r['frequency_seconds'])==('QQQ',LEGACY,15))
    assert row['RV_valid_pairs']==47 and row['RV_missing_pairs']==1 and row['RV_material_days']==0
    risk=next(r for r in tables['risk'] if (r['symbol'],r['case'],r['frequency_seconds'])==('QQQ',LEGACY,15))
    assert risk['post_warmup_origins']==0 and 'withheld' in risk['classification']
    h=next(r for r in tables['H'] if (r['symbol'],r['case'],r['frequency_seconds'],r['lag_max'])==('QQQ',LEGACY,15,5))
    assert json.loads(h['common_endpoint_pairs'])[0]==47
    unaffected=next(r for r in tables['risk'] if (r['symbol'],r['case'],r['frequency_seconds'])==('QQQ',LEGACY,60))
    assert unaffected['post_warmup_origins']==40


def test_independent_incidence_catches_planted_change(artificial_panel):
    data,dates,cfg=artificial_panel;tables,_=summarize(data,dates,cfg,bootstrap=False)
    source={(r.date,r.symbol,r.frequency_seconds,r.case):dict(RV=r.RV,RQ=r.RQ,selected_exchange=r.selected_exchange)
            for r in data.itertuples(index=False)}
    assert check_incidence(source,dates,cfg,tables['incidence'])>1000
    altered=copy.deepcopy(tables['incidence']);altered[0]['RV_material_days']+=1
    with pytest.raises(AssertionError,match='scalar differs'):check_incidence(source,dates,cfg,altered)


def test_segment_sampler_matches_shared_date_reference_with_missing_denominator():
    matrix=np.array([[1,1,0,1],[0,0,0,0],[0,1,1,1],[1,1,1,1],[0,1,0,1]],float)
    expected=stationary_bootstrap_means(matrix,np.random.default_rng(np.random.SeedSequence([534,3])),draws=99,block=3)
    expected=np.divide(expected[:,::2],expected[:,1::2],out=np.full((99,2),np.nan),where=expected[:,1::2]>0)
    np.testing.assert_allclose(segment_bootstrap(matrix,534,3,99),expected,equal_nan=True)


def test_independent_convolution_handles_initialization_and_future_information():
    from analyze_source_replication import ewma
    values=np.exp(np.random.default_rng(34).normal(-9,.2,60))
    np.testing.assert_allclose(states(values,.94),ewma(values),rtol=1e-13,atol=1e-18)
    changed=values.copy();changed[40:]*=7
    np.testing.assert_array_equal(states(values,.94)[:40],states(changed,.94)[:40])


def test_later_date_stops_before_requesting_numeric_columns(tmp_path,monkeypatch):
    cfg=json.loads((ROOT/'configs/etf_breadth.json').read_text())
    folder=tmp_path/'paired';folder.mkdir()
    # This is a synthetic boundary sentinel, not a held-out observation.
    (folder/'sentinel.csv').write_text('date,RV\n2017-01-03,DO_NOT_LOAD\n')
    calls=[];original=pd.read_csv
    def watched(*args,**kwargs):
        calls.append(kwargs.get('usecols'))
        assert kwargs['usecols']==['date']
        return original(*args,**kwargs)
    monkeypatch.setattr(pd,'read_csv',watched)
    with pytest.raises(ValueError,match='outside frozen'):load_fixed(tmp_path,cfg)
    assert calls==[['date'],['date']]


@pytest.mark.parametrize('member',['../escape.csv','/absolute.csv','private/credential.py','raw/ticks.csv'])
def test_archive_rejects_unsafe_or_unapproved_members_before_extraction(tmp_path,member):
    archive=tmp_path/'bad.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr(member,'no observations')
    with pytest.raises(ValueError,match='Unsafe|allowlist'):
        verify_archive(archive,tmp_path/'private',tmp_path/'a10')
    assert not (tmp_path/'private').exists()
