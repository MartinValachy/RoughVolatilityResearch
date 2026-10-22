"""Build and execute the portable source-audit notebook using synthetic data only."""
import json
import nbformat as nb
from nbclient import NotebookClient
from phase1_support import ROOT as R,record_run,sha


def build():
    cells=[nb.v4.new_markdown_cell('''# Audit daily volatility sources

Synthetic-only executable demonstration. No WRDS account, market observations or private files are used. Equal schema does not establish equal units or information. The audit reports findings and makes no repairs.'''),
    nb.v4.new_code_cell('''import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from roughnoisy.compatibility import compare_daily
dates = pd.bdate_range('2014-01-02', periods=80).strftime('%Y-%m-%d')
reference = pd.DataFrame({'date': dates, 'symbol': 'SYNTHETIC', 'frequency_seconds': 60,
    'RV': .0001 * np.exp(.1*np.sin(np.arange(80))), 'RQ': 1e-8,
    'M_expected': 390, 'M_observed': 390})
candidate = reference.copy(deep=True)
candidate.loc[10, 'RV'] *= 10000
candidate.loc[10, 'RQ'] *= 100000000  # decimal-to-percent return-unit mismatch
candidate.loc[20, ['M_expected', 'M_observed']] = 210
candidate = candidate.drop(index=30)
candidate.loc[40, 'M_observed'] = 388
candidate.loc[40, ['RV', 'RQ']] = np.nan
candidate.loc[50, 'RV'] *= 8
candidate.loc[50, 'RQ'] *= 500
audit = compare_daily(reference, candidate)
expected = {10: 'material_difference', 20: 'session_count_disagreement',
            30: 'missing_candidate', 40: 'incomplete_grid', 50: 'material_difference'}
for index, status in expected.items():
    assert audit.set_index('date').loc[dates[index], 'status'] == status
findings = audit[audit.status.ne('no_material_difference')]
assert len(findings) == 5
assert audit.attrs['source_equivalence_certified'] is False
print('Passed planted checks: 5 findings; no repairs or equivalence certification.')'''),
    nb.v4.new_code_cell("findings[['date', 'status', 'RV_ratio', 'RQ_ratio']]"),
    nb.v4.new_code_cell('''fig, ax = plt.subplots(figsize=(10, 3.5), layout='constrained')
ax.semilogy(pd.to_datetime(audit.date), audit.RV_ratio, '.', color='#2369a0')
ax.axhline(1.1, color='#b33c49', linestyle='--', label='Materiality boundaries')
ax.axhline(1/1.1, color='#b33c49', linestyle='--')
ax.set(title='Synthetic source ratio: invalid/missing comparisons remain absent',
       ylabel='Candidate / reference RV (log scale)', xlabel='Synthetic date')
ax.legend(frameon=False)
plt.show()'''),
    nb.v4.new_markdown_cell('''## Interpret the findings

The tool flags a difference; it does not infer its cause. Missing rows or invalid grids are not agreements. You must verify common units, calendars, security mapping, sampling origin and data provenance. If both sources share a calendar error, a third calendar check is needed.

Before using the tool on real data: explain why percent-return units multiply RV by 10,000 and RQ by 100,000,000; predict how an early close changes M; explain why matching aggregates do not certify information equivalence. See docs/SOURCE_AUDIT.md and docs/OWNERSHIP_REVIEW.md.''')]
    book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'synthetic_only':True})
    NotebookClient(book,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(R)}}).execute()
    path=R/'notebooks/source_audit_demo.ipynb';nb.write(book,path)
    run=record_run('source_portfolio_demo',{'status':'passed_checks','synthetic_only':True,'code_cells_executed':3,
        'notebook_sha256':sha(path),'code_sha256':sha(__file__),'empirical_observations_included':False,'published_online':False})
    (R/'results/source_portfolio_demo.json').write_text(json.dumps({'run_id':run,'status':'passed_checks','synthetic_only':True,'code_cells_executed':3},indent=2)+'\n')
    print(json.dumps({'run_id':run,'status':'passed_checks','synthetic_only':True}))


if __name__=='__main__':build()
