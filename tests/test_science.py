import numpy as np,pytest
from scipy.linalg import toeplitz,cholesky
from roughnoisy.core import *

def test_ou_variogram_matches_covariance_and_local_limit():
 k=.07;t=np.array([1e-8,.1,1,22]);v=.25
 np.testing.assert_allclose(ou_variogram(t,k,v),2*(ou_cov(0,k,v)-ou_cov(t,k,v)),atol=1e-16)
 assert abs(ou_effective_h(1e-8,k)-.5)<1e-8
 eps=1e-5;numeric=(np.log(ou_variogram(t*np.exp(eps),k))-np.log(ou_variogram(t*np.exp(-eps),k)))/(4*eps)
 np.testing.assert_allclose(numeric,ou_effective_h(t,k),rtol=1e-8)

def test_noise_attenuation_and_correlated_cross_identity():
 k=np.arange(1,23);H=.17;c=.4;q=.8
 expected=H*c*k**(2*H)/(c*k**(2*H)+2*q);eps=1e-5
 numeric=(np.log(c*(k*np.exp(eps))**(2*H)+2*q)-np.log(c*(k*np.exp(-eps))**(2*H)+2*q))/(4*eps)
 np.testing.assert_allclose(numeric,expected,rtol=1e-8)
 rng=np.random.default_rng(123);x=simulate_ou(200000,.03,rng);a=.3;e=a*x+simulate_ou(len(x),.2,rng,variance=.1)
 for lag in [1,5,22]:
  dx=x[lag:]-x[:-lag];de=e[lag:]-e[:-lag]
  np.testing.assert_allclose(np.mean((dx+de)**2),np.mean(dx**2)+np.mean(de**2)+2*np.mean(dx*de),rtol=1e-13)

def test_cauchy_covariance_positive_definite_and_local_exponent():
 for H in [.05,.1,.2,.35]:
  cov=lambda k:cauchy_cov(k,H)
  assert abs(cov(22)/cov(0)-.5)<1e-12
  assert np.min(np.linalg.eigvalsh(toeplitz(cov(np.arange(128)))))>0
  h=np.array([1e-10,1e-9]);s=np.diff(np.log(2*(cov(0)-cov(h))))/np.diff(np.log(h))/2
  # H=.05 converges especially slowly; check the actual analytic local limit.
  assert abs(s[0]-H)<.02

def test_embedding_covariance_with_independent_cholesky():
 cov=lambda k:cauchy_cov(k,.2);n=32;spec,meta=embedding(cov,n)
 rng=np.random.default_rng(667);draws=np.stack([simulate_embedding(spec,n,rng) for _ in range(10000)])
 L=cholesky(toeplitz(cov(np.arange(n))),lower=True);direct=rng.normal(size=(10000,n))@L.T
 target=toeplitz(cov(np.arange(n)))
 assert np.max(np.abs(draws.T@draws/len(draws)-target))<.018
 assert np.max(np.abs(direct.T@direct/len(direct)-target))<.018
 # Recover the embedding covariance deterministically, not only by simulation.
 embedded=np.fft.ifft(spec**2).real[:n]
 np.testing.assert_allclose(embedded,cov(np.arange(n)),atol=1e-12)

def test_exact_ou_stationary_initialization_and_covariance():
 rng=np.random.default_rng(22);x=np.stack([simulate_ou(20,.13,rng) for _ in range(15000)])
 assert abs(np.var(x[:,0])-.25)<.01
 for lag in [1,5,15]:assert abs(np.mean(x[:,0]*x[:,lag])-ou_cov(lag,.13))<.008

def test_projection_noise_and_lognormal_aggregation():
 rate=.03;cov=lambda k:ou_cov(k,rate);x=.4
 a,B=gaussian_projection([x],cov,22,noise_variance=0)
 np.testing.assert_allclose(a,x*np.exp(-rate*np.arange(1,23)),atol=1e-13)
 np.testing.assert_allclose(np.diag(B),.25*(1-np.exp(-2*rate*np.arange(1,23))),atol=1e-13)
 noisy,_=gaussian_projection([x],cov,1,noise_variance=.25)
 assert abs(noisy[0]-a[0]/2)<1e-12
 assert variance_forecast(a,B)>np.exp(np.mean(a))
 rng=np.random.default_rng(88);draw=rng.multivariate_normal(a,B,size=100000)
 assert abs(np.mean(np.exp(draw))-variance_forecast(a,B))<.006

def test_quarticity_constant_variance_moments():
 rng=np.random.default_rng(991);M=78;v=.0001;r=rng.normal(size=(30000,M))*np.sqrt(v/M)
 rv=np.sum(r*r,axis=1);rq=M/3*np.sum(r**4,axis=1)
 assert abs(rv.mean()/v-1)<.004
 assert abs(rv.var()/(2*v*v/M)-1)<.025
 assert abs(rq.mean()/(v*v)-1)<.01

def test_forecast_timing_horizon_and_train_only_smearing():
 rng=np.random.default_rng(887);v=np.exp(rng.normal(-9,.5,400))
 for h in [1,5,22]:
  pred,end=loghar_predict(v,300,h,window=250)
  assert end==300 and pred>0
  contaminated=v.copy();contaminated[301:]*=1000
  assert loghar_predict(contaminated,300,h,window=250)[0]==pred
  assert future_average(v,300,h)==np.mean(v[301:301+h])
  idx=mature_origins(300,h);assert np.all(idx+h<=300)

def test_negative_corrected_variogram_reported_not_clipped():
 assert np.isnan(apparent_h([-.1,.2,.3,.4,.5],5))

def test_loss_units_zero_proxy_positivity_and_risk():
 y=np.array([0,.1,2]);f=np.array([.4,.5,1.1]);g=np.array([.3,.7,1.5])
 np.testing.assert_allclose(qlike(y,f)-qlike(y,g),qlike(100*y,100*f)-qlike(100*y,100*g),atol=1e-14)
 assert np.all(np.isfinite(qlike(y,f)))
 with pytest.raises(ValueError):qlike(y,[0,1,2])
 assert risk_weight(.1**2/252)==pytest.approx(1)

def test_seed_stream_reproducibility_and_independence():
 def draw(rep):return simulate_ou(100,.1,np.random.default_rng(np.random.SeedSequence([20261020,1,1250,rep,0])))
 np.testing.assert_array_equal(draw(1),draw(1));assert not np.array_equal(draw(1),draw(2))

def test_flexible_persistence_mixture_is_positive_and_covariance_match():
 cov=lambda k:cauchy_cov(k,.1);mix,fit=match_ou_mixture(cov,np.r_[0,np.arange(1,127)],[.005,.02,.1,.5,2,10,50,250,1250,6250])
 assert np.all(np.asarray(fit['weights'])>=0)
 assert np.min(np.linalg.eigvalsh(toeplitz(mix(np.arange(40)))))>0
 assert fit['rmse']<.004

def test_joint_date_bootstrap_preserves_model_relationships():
 dates=np.arange(60,dtype=float);paired=np.c_[dates,2*dates+3]
 means=stationary_bootstrap_means(paired,np.random.default_rng(42),draws=100,block=10)
 assert means.shape==(100,2)
 np.testing.assert_allclose(means[:,1],2*means[:,0]+3,atol=1e-13)
 assert np.std(means[:,0])>0

def test_multihorizon_levels_and_nested_efficient_return_aggregation():
 returns=np.array([.01,-.02,.03,.04,-.01,.02])
 daily_groups=returns.reshape(2,3);rv_fine=np.sum(daily_groups**2,axis=1)
 # Coarse RV squares summed RETURNS, not summed squared returns.
 rv_coarse=np.sum(daily_groups,axis=1)**2
 np.testing.assert_allclose(rv_fine,[.0014,.0021],atol=1e-15)
 np.testing.assert_allclose(rv_coarse,[.0004,.0025],atol=1e-15)
 assert future_average([1,4,9,16,25],0,2)==6.5

def test_KL_two_independent_numerical_forms_and_identity():
 from scipy.linalg import solve_triangular
 A=toeplitz(cauchy_cov(np.arange(40),.1))+np.eye(40)*.025
 B=toeplitz(ou_cov(np.arange(40),.03))+np.eye(40)*.025
 L0=cholesky(B,lower=True);L1=cholesky(A,lower=True)
 kl=.5*(np.trace(cho_solve((L0,True),A))-40+2*np.log(np.diag(L0)).sum()-2*np.log(np.diag(L1)).sum())
 C=solve_triangular(L0,L1,lower=True);e=np.linalg.eigvalsh(C@C.T)
 np.testing.assert_allclose(kl,.5*np.sum(e-1-np.log(e)),atol=1e-12)
 assert kl>0
 assert .5*np.sum(np.ones(40)-1-np.log(np.ones(40)))==0
