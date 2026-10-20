from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cp=json.loads((R/'checkpoint.json').read_text());fail=[];checked=0
 for x in json.loads((R/'manifests/raw_inputs.json').read_text()):
  p=R/x['path'];checked+=1
  if not p.exists() or sha(p)!=x['sha256']:fail.append('Missing or changed immutable input:'+x['path'])
 for x in json.loads((R/'manifests/run_index.json').read_text()):
  p=R/x['metadata_path']
  if not p.exists() or sha(p)!=x['metadata_sha256']:fail.append('Run metadata changed:'+x['run_id'])
 for p in (R/'configs').glob('*.json'):
  cfg=json.loads(p.read_text())
  if cfg.get('production_allowed'):fail.append('Production flag unexpectedly enabled:'+str(p))
 if cp['production_allowed'] or cp['final_test']['opened_for_model_development'] or cp['final_test']['observations_acquired']!=0:fail.append('Final-test/production protection invalid')
 tests=cp['tests']
 if tests['failures'] or tests['errors']:fail.append('Scientific tests did not pass')
 import nbformat
 nb=nbformat.read(R/'notebooks/formula_audit.ipynb',as_version=4)
 for cell in nb.cells:
  if cell.cell_type=='code' and (cell.execution_count is None or any(o.output_type=='error' for o in cell.outputs)):fail.append('Notebook contains unexecuted/failed cell')
 for rel in ['README.md','STATUS.md','DECISIONS.md','manuscript/PILOT_REPORT.md','manuscript/POSITIONING_AND_FEASIBILITY.md','data/DATA_CARD.md','literature/novelty_matrix.csv','results/test_results.xml']:
  if not (R/rel).exists():fail.append('Missing deliverable:'+rel)
 result={'status':'passed' if not fail else 'failed','immutable_inputs_verified':checked,'scientific_tests':tests,'latest_run_ids':cp['latest_runs'],'production_allowed':False,'final_test_observations_acquired':0,'failures':fail}
 (R/'results/checkpoint_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 if fail:raise SystemExit(1)
if __name__=='__main__':main()
