"""A08 study: spot log variance -> grid IV -> Gaussian log-price returns -> RV.

Time is a contiguous trading clock; no overnight, jumps, leverage or quotes.
Gaussian Cauchy covariance determines a stationary process, not fractional OU.
IV and the Ito integral use explicit left-point discretization. Observed price
noise is iid on the fine log-price grid, shared by nested coarse samples.
"""
import numpy as np
from .core import cauchy_cov, embedding, simulate_embedding, simulate_ou, variogram, apparent_h


def covariance(model, times, cfg):
    times=np.asarray(times,dtype=float)
    if model=='OU':
        return cfg['stationary_log_variance']*np.exp(-np.log(2)*np.abs(times)/cfg['half_correlation_days'])
    h={'Cauchy_H01':0.1,'Cauchy_H03':0.3}[model]
    return cauchy_cov(times,H=h,beta=cfg['cauchy_beta'],half_life=cfg['half_correlation_days'],variance=cfg['stationary_log_variance'])


def prepare(model, cfg):
    n=cfg['days']*cfg['fine_steps_per_day']
    if model=='OU': return None,{'sampler':'exact stationary OU recursion'}
    spectrum,meta=embedding(lambda k:covariance(model,k/cfg['fine_steps_per_day'],cfg),n)
    return spectrum,dict(meta,sampler='PSD circulant Gaussian embedding; no spectral truncation')


def path(model, cfg, rep, spectrum=None):
    fid=cfg['models'].index(model);seed=cfg['seed']
    latent_rng=np.random.default_rng(np.random.SeedSequence([seed,fid,rep,0]))
    price_rng=np.random.default_rng(np.random.SeedSequence([seed,fid,rep,1]))
    noise_rng=np.random.default_rng(np.random.SeedSequence([seed,fid,rep,2]))
    n=cfg['days']*cfg['fine_steps_per_day'];m=cfg['fine_steps_per_day']
    if model=='OU':
        x=simulate_ou(n,np.log(2)/cfg['half_correlation_days'],latent_rng,variance=cfg['stationary_log_variance'],dt=1/m)
    else:
        if spectrum is None: raise ValueError('Prepared spectrum required')
        x=simulate_embedding(spectrum,n,latent_rng)
    variance=cfg['mean_daily_variance']*np.exp(x-cfg['stationary_log_variance']/2)
    if not np.isfinite(variance).all(): raise ValueError('Nonfinite latent variance')
    efficient=np.sqrt(variance/m)*price_rng.normal(size=n)
    noise=noise_rng.normal(size=n+1)
    return x.reshape(cfg['days'],m),variance.reshape(cfg['days'],m),efficient.reshape(cfg['days'],m),noise


def measures(returns,block):
    """Nested returns formed by summing fine-grid log-price increments."""
    r=np.asarray(returns,dtype=float)
    if r.ndim!=2 or block<1 or r.shape[1]%block: raise ValueError('Invalid return grid')
    coarse=r.reshape(r.shape[0],r.shape[1]//block,block).sum(axis=2)
    m=coarse.shape[1]
    return np.sum(coarse**2,axis=1),m/3*np.sum(coarse**4,axis=1)


def path_metrics(model,cfg,rep,spectrum=None):
    x,v,efficient,noise=path(model,cfg,rep,spectrum)
    iv=v.mean(axis=1);logiv=np.log(iv);spot=x[:,0]
    fine=cfg['fine_steps_per_day'];h=cfg['local_H'][cfg['models'].index(model)]
    h_iv={b:apparent_h(variogram(logiv,b),b) for b in cfg['lag_bands']}
    h_spot={b:apparent_h(variogram(spot,b),b) for b in cfg['lag_bands']}
    refinement=[float(np.mean(np.abs(v[:,::step].mean(axis=1)-iv)/iv)) for step in [2,4]]
    records=[]
    for sd in cfg['log_price_noise_sd']:
        observed=efficient+sd*np.diff(noise).reshape(efficient.shape)
        for minutes in cfg['sampling_minutes']:
            block=fine*minutes//cfg['session_minutes'];rv,rq=measures(observed,block)
            if np.any(rv<=0) or not np.isfinite(rv).all(): raise ValueError('Invalid RV')
            m=fine//block
            # Conditional expectation with iid endpoint noise: E[RV|v] = IV + 2*M*sd^2.
            rv_expectation=iv+2*m*sd**2
            for band in cfg['lag_bands']:
                records.append({'model':model,'replicate':rep,'local_H':h,'noise_sd':sd,
                    'sampling_minutes':minutes,'lag_max':band,'H_spot':h_spot[band],
                    'H_IV':h_iv[band],'H_RV':apparent_h(variogram(np.log(rv),band),band),
                    'mean_RV_over_IV':float(np.mean(rv/iv)),
                    'mean_RV_over_conditional_expectation':float(np.mean(rv/rv_expectation)),
                    'mean_qhat':float(np.mean(2*rq/(m*rv**2))),
                    'IV_half_resolution_mean_relative_error':refinement[0],
                    'IV_quarter_resolution_mean_relative_error':refinement[1]})
    return records


def validate_covariance(cfg):
    """Independent kernel formula, inverse-spectrum covariance, and dense MC."""
    checks=[];grid=np.arange(48)/cfg['fine_steps_per_day']
    for j,model in enumerate(cfg['models']):
        actual=covariance(model,grid,cfg)
        if model=='OU':
            expected=cfg['stationary_log_variance']*2**(-grid/cfg['half_correlation_days'])
        else:
            h={'Cauchy_H01':.1,'Cauchy_H03':.3}[model]
            # Algebraically independent parametrization, rho(half_correlation)=1/2.
            a=2**(2*h/cfg['cauchy_beta'])-1
            expected=cfg['stationary_log_variance']*(1+a*(grid/cfg['half_correlation_days'])**(2*h))**(-cfg['cauchy_beta']/(2*h))
        if not np.allclose(actual,expected,rtol=2e-12,atol=1e-14): raise ValueError('Independent covariance formula mismatch')
        spectrum,meta=embedding(lambda k:covariance(model,k/cfg['fine_steps_per_day'],cfg),len(grid))
        recovered=np.fft.ifft(spectrum**2).real[:len(grid)]
        if not np.allclose(recovered,expected,rtol=2e-11,atol=1e-14): raise ValueError('FFT implied covariance mismatch')
        from scipy.linalg import toeplitz
        dense=np.linalg.cholesky(toeplitz(expected))
        rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],987,j]))
        samples=rng.normal(size=(12000,len(grid)))@dense.T
        empirical=np.mean(samples[:,0,None]*samples,axis=0)
        max_error=float(np.max(np.abs(empirical-expected))/expected[0])
        if max_error>.06: raise ValueError('Dense covariance Monte Carlo check failed')
        checks.append({'model':model,'status':'passed_checks','FFT_covariance_max_abs_error':float(np.max(np.abs(recovered-expected))),
                       'dense_MC_max_error_over_variance':max_error,'dense_paths':12000,'embedding':meta})
    return checks
