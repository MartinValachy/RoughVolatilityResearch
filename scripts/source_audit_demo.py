"""Public, synthetic-only demonstration of material source-compatibility warnings."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from roughnoisy.compatibility import compare_daily
from phase1_support import record_run,sha


def demo():
    dates=pd.bdate_range('2014-01-02',periods=80).strftime('%Y-%m-%d')
    reference=pd.DataFrame({'date':dates,'symbol':'SYNTHETIC','frequency_seconds':60,
        'RV':.0001*np.exp(.1*np.sin(np.arange(80))),'RQ':1e-8,'M_expected':390,'M_observed':390})
    candidate=reference.copy(deep=True)
    candidate.loc[10,['RV','RQ']]*=10000 # planted unit mismatch; never repaired
    candidate.loc[20,'M_expected']=210;candidate.loc[20,'M_observed']=210
    candidate=candidate.drop(index=30) # absent day retained by outer pairing
    candidate.loc[40,'M_observed']=388;candidate.loc[40,['RV','RQ']]=np.nan
    candidate.loc[50,'RV']*=8;candidate.loc[50,'RQ']*=500 # planted spike
    result=compare_daily(reference,candidate)
    statuses=result.set_index('date').status
    expected={10:'material_difference',20:'session_count_disagreement',30:'missing_candidate',40:'incomplete_grid',50:'material_difference'}
    for i,status in expected.items(): assert statuses.loc[dates[i]]==status
    assert result.status.ne('no_material_difference').sum()==5
    output=R/'results/source_audit_demo';output.mkdir(parents=True,exist_ok=True)
    result.to_csv(output/'synthetic_findings.csv',index=False)
    summary={'status':'passed_checks','synthetic_only':True,'planted_findings_detected':5,
             'no_automatic_rescaling':True,'source_equivalence_certified':False,'counts':result.status.value_counts().to_dict()}
    summary['code_sha256']=sha(__file__)
    summary['audit_module_sha256']=sha(R/'src/roughnoisy/compatibility.py')
    summary['run_id']=record_run('source_audit_demo',summary)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))


if __name__=='__main__':demo()
