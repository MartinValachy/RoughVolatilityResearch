"""Transparent analytical components. Time is in trading days unless stated.

The daily Gaussian examples model log daily IV directly. Continuous-time
spot log variance is a different object. See notebooks/formula_audit.ipynb.
"""
import numpy as np
from scipy.signal import lfilter
from scipy.linalg import cho_factor,cho_solve,toeplitz
from scipy.optimize import least_squares,nnls

def ou_cov(lags,kappa,variance=0.25):
    if kappa<=0 or variance<=0:raise ValueError('Stationary OU needs positive kappa and variance')
    return variance*np.exp(-kappa*np.abs(np.asarray(lags,dtype=float)))

def ou_variogram(lags,kappa,variance=0.25):
    return 2*variance*(-np.expm1(-kappa*np.asarray(lags,dtype=float)))

def ou_effective_h(lags,kappa):
    z=kappa*np.asarray(lags,dtype=float)
    return np.divide(z,2*np.expm1(z),out=np.full_like(z,0.5),where=z!=0)

def cauchy_cov(lags,H=0.1,beta=0.5,half_life=22,variance=0.25):
    """BLP (2022), author version p6, generalized Cauchy covariance.

    alpha=H-1/2. A scale parameter sets rho(half_life)=1/2.
    This is NOT fractional OU. beta controls the long-lag power tail.
    """
    if not (0<H<1 and beta>0 and half_life>0 and variance>0):raise ValueError('Invalid covariance parameters')
    scale=half_life/np.expm1(np.log(2)*2*H/beta)**(1/(2*H))
    return variance*np.exp(-beta/(2*H)*np.log1p((np.abs(np.asarray(lags))/scale)**(2*H)))

def simulate_ou(n,kappa,rng,variance=0.25,dt=1.0):
    rho=np.exp(-kappa*dt);x0=rng.normal(scale=np.sqrt(variance))
    z=rng.normal(size=n-1)*np.sqrt(variance*(-np.expm1(-2*kappa*dt)))
    return np.r_[x0,lfilter([1.0],[1.0,-rho],z,zi=[rho*x0])[0]]

def embedding(cov,n):
    """Exact Gaussian circulant embedding when eigenvalues are nonnegative.

    Increase embedding size on genuine negative eigenvalues; only roundoff
    eigenvalues within 1e-12 of the spectral scale are rounded to zero.
    No spectral truncation is silently used.
    """
    m=2**int(np.ceil(np.log2(max(2*(n-1),2))))
    for _ in range(7):
        c=cov(np.arange(m//2+1)); row=np.r_[c,c[-2:0:-1]]
        lam=np.fft.fft(row).real;tol=1e-12*max(1.0,np.max(lam))
        if np.min(lam)>=-tol:return np.sqrt(np.maximum(lam,0)),{'m':m,'min_eigenvalue':float(np.min(lam)),'roundoff_tolerance':float(tol)}
        m*=2
    raise ValueError('No positive semidefinite circulant embedding found')

def simulate_embedding(sqrt_spectrum,n,rng):
    return np.fft.ifft(np.fft.fft(rng.normal(size=len(sqrt_spectrum)))*sqrt_spectrum).real[:n]

def variogram(x,max_lag=22):
    x=np.asarray(x)
    return np.array([np.mean((x[k:]-x[:-k])**2) for k in range(1,max_lag+1)])

def apparent_h(moment,lag_max=10):
    y=np.asarray(moment)[:lag_max]
    if len(y)!=lag_max or np.any(~np.isfinite(y)) or np.any(y<=0):return float('nan')
    return float(np.polyfit(np.log(np.arange(1,lag_max+1)),np.log(y),1)[0]/2)

def nlls_h(moment,lag_max=10):
    """BLP p14 b0+b1*k^(2H); descriptive fit, no daily consistency claim.

    Report bound hits and failures; asymptotics for exact power variograms
    do not automatically apply to daily OU or Cauchy variograms.
    """
    y=np.asarray(moment)[:lag_max];scale=np.max(y);k=np.arange(1,lag_max+1)
    f=least_squares(lambda p:p[0]+p[1]*k**(2*p[2])-y/scale,[0.3,0.3,0.2],bounds=([0,0,0.005],[np.inf,np.inf,0.995]),max_nfev=150)
    return {'H':float(f.x[2]),'offset':float(f.x[0]*scale),'success':bool(f.success),'bound_hit':bool(f.x[2]<0.006 or f.x[2]>0.994),'cost':float(f.cost)}

def gaussian_projection(history,cov,horizon=1,noise_variance=0.0,mean=0.0):
    y=np.asarray(history,dtype=float);p=len(y);lags=np.arange(p)
    K=toeplitz(cov(lags))+np.eye(p)*noise_variance
    f=cho_factor(K,lower=True,check_finite=True)
    # history oldest to newest; future j=1 is one step beyond newest
    cross=cov(np.arange(1,horizon+1)[:,None]+np.arange(p-1,-1,-1)[None,:])
    a=mean+cross@cho_solve(f,y-mean)
    B=toeplitz(cov(np.arange(horizon)))-cross@cho_solve(f,cross.T)
    if np.min(np.linalg.eigvalsh(B)) < -1e-9:raise ValueError('Invalid predictive covariance')
    return a,B

def variance_forecast(a,B):
    return float(np.mean(np.exp(np.asarray(a)+np.diag(B)/2)))

def qlike(target,prediction):
    y=np.asarray(target);f=np.asarray(prediction)
    if np.any(f<=0) or np.any(~np.isfinite(f)) or np.any(y<0) or np.any(~np.isfinite(y)):raise ValueError('Invalid forecast or target')
    return np.log(f)+y/f

def risk_weight(prediction,target=0.1,cap=1.0):
    f=np.asarray(prediction)
    if np.any(f<=0) or np.any(~np.isfinite(f)):raise ValueError('Forecast must be positive')
    return np.minimum(cap,target/np.sqrt(252*f))

def future_average(v,origin,h):
    if origin+h>=len(v):raise ValueError('Unmatured outcome')
    return float(np.mean(v[origin+1:origin+h+1]))

def mature_origins(fit_time,h,start=21):
    return np.arange(start,fit_time-h+1,dtype=int)

def har_features(logv,t):
    if t<21:raise ValueError('HAR warmup')
    return np.array([1,logv[t],np.mean(logv[t-4:t+1]),np.mean(logv[t-21:t+1])])

def loghar_predict(v,origin,h,window=1250):
    """Direct forecast of log average FUTURE variance; train-only smearing.

    This is a transparent direct log-HAR baseline, not an implementation
    of HARQ or the 2026 rough HAR. Only fully matured labels enter fitting.
    """
    v=np.asarray(v);lv=np.log(v);idx=mature_origins(origin,h,max(21,origin-window+1))
    if len(idx)<40:raise ValueError('Insufficient matured labels')
    X=np.stack([har_features(lv,t) for t in idx]);Y=np.log([future_average(v,t,h) for t in idx])
    coef=np.linalg.lstsq(X,Y,rcond=None)[0];res=Y-X@coef;smear=np.mean(np.exp(res))
    return float(np.exp(har_features(lv,origin)@coef)*smear),int(idx[-1]+h)

def stationary_bootstrap_means(x,rng,draws=4999,block=44):
    x=np.asarray(x);n=len(x);out=np.empty(draws)
    # All columns share date indices, preserving cross-model dependence.
    for b in range(draws):
        idx=np.empty(n,dtype=int);idx[0]=rng.integers(n)
        restart=rng.random(n-1)<1/block;starts=rng.integers(n,size=n-1)
        for t in range(1,n):idx[t]=starts[t-1] if restart[t-1] else (idx[t-1]+1)%n
        out[b]=np.mean(x[idx])
    return out

def match_ou_mixture(target_cov,lags,half_lives):
    lags=np.asarray(lags);rates=np.log(2)/np.asarray(half_lives)
    A=np.exp(-lags[:,None]*rates[None,:]);weights,residual=nnls(A,target_cov(lags))
    def cov(k):return np.exp(-np.abs(np.asarray(k))[...,None]*rates)@weights
    return cov,{'half_lives':list(map(float,half_lives)),'weights':weights.tolist(),'rmse':float(np.sqrt(np.mean((cov(lags)-target_cov(lags))**2))),'max_abs_error':float(np.max(np.abs(cov(lags)-target_cov(lags)))),'zero_variance_error':float(cov(0)-target_cov(0))}
