import numpy as np
import pytest
from roughnoisy.study import covariance,measures,validate_covariance


@pytest.fixture
def cfg():
    return {'models':['OU','Cauchy_H01','Cauchy_H03'],'seed':20261022,'fine_steps_per_day':780,
            'half_correlation_days':22,'stationary_log_variance':.25,'cauchy_beta':.5}


def test_cauchy_and_OU_dense_and_spectral_covariance(cfg):
    assert len(validate_covariance(cfg))==3
    for model in cfg['models']:
        assert covariance(model,22,cfg)==pytest.approx(.125,rel=1e-12)


def test_RV_RQ_against_independent_sampled_price_construction():
    rng=np.random.default_rng(123);increments=rng.normal(size=(5,780))*.0001
    for block in [2,10,30,60]:
        rv,rq=measures(increments,block)
        prices=np.r_[0,np.cumsum(increments.ravel())]
        sampled=prices[::block];returns=np.diff(sampled).reshape(5,780//block)
        independent_rv=np.einsum('ij,ij->i',returns,returns)
        independent_rq=(780//block)/3*np.sum(returns**4,axis=1)
        np.testing.assert_allclose(rv,independent_rv,rtol=1e-12)
        np.testing.assert_allclose(rq,independent_rq,rtol=1e-12)


def test_constant_volatility_finite_sampling_and_endpoint_noise():
    rng=np.random.default_rng(945);days=30000;m=78;iv=.0001;sd=.0003
    efficient=np.sqrt(iv/m)*rng.normal(size=(days,m))
    noise=sd*rng.normal(size=(days,m+1))
    clean,rq=measures(efficient,1);noisy,_=measures(efficient+np.diff(noise,axis=1),1)
    assert abs(clean.mean()/iv-1)<.004
    assert abs(noisy.mean()/(iv+2*m*sd**2)-1)<.004
    # Gaussian direction on the M-sphere gives exact E[qhat]=2/(M+2).
    assert abs(np.mean(2*rq/(m*clean**2))/(2/(m+2))-1)<.004


def test_invalid_sampling_grid_refused():
    with pytest.raises(ValueError): measures(np.ones((2,7)),2)
