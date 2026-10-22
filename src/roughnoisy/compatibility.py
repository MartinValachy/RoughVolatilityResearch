"""Local source-compatibility diagnostics, without data acquisition or rescaling.

Inputs must share documented RV/RQ units. Absence of a material warning does
not certify equivalence or authorize pooling. Thresholds are engineering
materiality settings, separate from the stricter original R1 reconciliation.
"""
import numpy as np
import pandas as pd

KEYS=['date','symbol','frequency_seconds']
FIELDS=['RV','RQ','M_expected','M_observed']


def compare_daily(reference,candidate,rv_factor=1.1,rq_factor=2.0):
    """Outer-pair daily grids, preserving missing/invalid rows as audit findings."""
    if not np.isfinite([rv_factor,rq_factor]).all() or rv_factor<=1 or rq_factor<=1:
        raise ValueError('Multiplicative warning factors must be finite and exceed one')
    for name,frame in [('reference',reference),('candidate',candidate)]:
        if not set(KEYS+FIELDS)<=set(frame): raise ValueError('Missing '+name+' columns')
        if frame[KEYS].isna().any().any() or frame.duplicated(KEYS).any(): raise ValueError('Missing/duplicate '+name+' key')
    result=reference[KEYS+FIELDS].merge(candidate[KEYS+FIELDS],on=KEYS,how='outer',suffixes=('_reference','_candidate'),indicator=True,validate='one_to_one')
    paired=result['_merge'].eq('both')
    values={c:pd.to_numeric(result[c],errors='coerce').to_numpy(float) for c in result if c not in KEYS+['_merge']}
    expected_ref=values['M_expected_reference'];expected_candidate=values['M_expected_candidate']
    observed_ref=values['M_observed_reference'];observed_candidate=values['M_observed_candidate']
    counts_valid=np.isfinite(expected_ref)&np.isfinite(expected_candidate)&np.isfinite(observed_ref)&np.isfinite(observed_candidate)
    counts_valid&=(expected_ref>0)&(expected_candidate>0)&(observed_ref>=0)&(observed_candidate>=0)
    counts_valid&=(observed_ref<=expected_ref)&(observed_candidate<=expected_candidate)
    for array in [expected_ref,expected_candidate,observed_ref,observed_candidate]:counts_valid&=np.equal(array,np.floor(array))
    same_session=counts_valid&(expected_ref==expected_candidate)
    complete=same_session&(observed_ref==expected_ref)&(observed_candidate==expected_candidate)
    result['same_session_count']=paired&same_session
    result['complete_grid_pair']=paired&complete
    all_moments_valid=np.ones(len(result),bool);any_material=np.zeros(len(result),bool)
    for field,factor in [('RV',rv_factor),('RQ',rq_factor)]:
        a=values[field+'_reference'];b=values[field+'_candidate']
        valid=paired.to_numpy()&complete&np.isfinite(a)&np.isfinite(b)&(a>0)&(b>0)
        ratio=np.full(len(result),np.nan);np.divide(b,a,out=ratio,where=valid)
        result[field+'_ratio']=ratio;result[field+'_valid_pair']=valid
        material=pd.Series(pd.NA,index=result.index,dtype='boolean')
        material.loc[valid]=np.abs(np.log(ratio[valid]))>np.log(factor)
        result[field+'_material_warning']=material
        all_moments_valid&=valid;any_material|=material.fillna(False).to_numpy(bool)
    result['status']=np.select([
        result['_merge'].eq('left_only'),result['_merge'].eq('right_only'),
        ~counts_valid,~same_session,~complete,~all_moments_valid,any_material],
        ['missing_candidate','missing_reference','invalid_counts','session_count_disagreement','incomplete_grid',
         'invalid_moments','material_difference'],default='no_material_difference')
    result.attrs={'rv_factor':rv_factor,'rq_factor':rq_factor,'units':'must be documented compatible by caller',
                  'source_equivalence_certified':False,'automatic_correction_or_pooling':False}
    return result.drop(columns='_merge')
