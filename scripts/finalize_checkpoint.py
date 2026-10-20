"""Write manifests/status/continuation state from evidence, without experiments."""
from pathlib import Path
import sys,os,json,hashlib,datetime,platform,importlib.metadata as im,stat,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')
def main():
 now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 environment={'captured_utc':now,'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),'logical_cpus':os.cpu_count(),'numeric_precision':'float64','packages':{d.metadata['Name']:d.version for d in sorted(im.distributions(),key=lambda d:d.metadata['Name'].lower())},'requirements_lock_sha256':digest(R/'requirements.lock.txt')}
 write(R/'manifests/environment.json',environment)
 sources=json.loads((R/'manifests/source_register_audited.json').read_text(encoding='utf8'))['sources'];byhash={s.get('sha256'):s for s in sources if s.get('sha256')}
 raw=[]
 for folder in ['protocol/inputs','literature/raw','literature/code','data/raw','data/sealed']:
  for p in sorted((R/folder).rglob('*')):
   if not p.is_file():continue
   sha=digest(p);s=byhash.get(sha,{});raw.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':sha,'source_id':s.get('id'),'url':s.get('download_url') or s.get('primary_url'),'license':s.get('license') or 'See source/data/code manifest; no redistribution permission inferred','immutability':'Read-only local input; no analysis of sealed validation values'})
 write(R/'manifests/raw_inputs.json',raw)
 latest={}
 for p in sorted((R/'results').glob('latest_*.json')):
  obj=json.loads(p.read_text());latest[p.stem.removeprefix('latest_')]=obj.get('run_id')
 data=json.loads((R/'results/data_quality.json').read_text());latest['data_audit']=data['run_id']
 index=[]
 for p in sorted((R/'runs').glob('*/metadata.json')):
  obj=json.loads(p.read_text());index.append({'run_id':obj['run_id'],'metadata_path':p.relative_to(R).as_posix(),'metadata_sha256':digest(p),'status':obj.get('status','audit_completed'),'is_current_checkpoint_run':obj['run_id'] in latest.values(),'checkpoint_environment':'manifests/environment.json','environment_capture_note':'Captured at checkpoint; numerical dependencies installed in the same session before runs. Initial core snapshot retained where later multidimensional-bootstrap enhancement changed the source hash.'})
 write(R/'manifests/run_index.json',index)
 context={'original_package':'C:/Users/valac/.codex/.chatgpt-projects/g-p-6908f1c9d0a4819196768eef128fb143/outputs/Rough_or_Just_Noisy_Research_Plan_2026-10-20.zip','user_request_attachment':'C:/Users/valac/.codex/attachments/2d1ae9a4-326b-4561-9a64-2d84f32ce812/Pasted text.txt','Notion':[{'url':'https://app.notion.com/p/3ff65199416f81ee9baff9c65b0867e0','role':'backup draft plan','operation':'read_only','tool_reported_as_of':'2026-10-20T20:25:31.252Z'},{'url':'https://app.notion.com/p/3fb65199416f81f1a80fd091e66595b3','role':'earlier proposal, superseded where in conflict with execution protocol/user steering','operation':'read_only','tool_reported_as_of':'2026-10-16T17:59:55.441Z'}],'later_user_changes':['Save progress to supplied GitHub repository where useful','Treat project as independent research intended for publication, not a thesis'],'repository':{'url':'https://github.com/MartinValachy/RoughVolatilityResearch','visibility_verified':'private','initial_state':'empty','verified_permissions':'admin,push,pull via connector; local Git credentials used only for authorized repository operations'}}
 write(R/'manifests/context_sources.json',context)
 ledger=[
 {'claim':'Daily Gaussian pilot count and allH bias/MCSE/invalid-correction summaries','run':latest['pilot'],'table':'results/toy_summary.csv','config':'configs/pilot.json'},
 {'claim':'Known-law matching, KL/power bound, likelihood-ratio size/power','run':latest['covariance'],'table':'results/latest_covariance.json','config':'configs/covariance_control.json'},
 {'claim':'Paired forecast/RTE/exposure diagnostic','run':latest['covariance'],'table':'results/covariance_forecast_diagnostics.csv','config':'configs/covariance_control.json'},
 {'claim':'Brownian efficient-price refinement and nested measurement error','run':latest['efficient'],'table':'results/efficient_price_summary.csv','config':'configs/efficient_price.json'},
 {'claim':'Baseline forecast counts, positivity/maturity, paired path losses','run':latest['baseline'],'table':'results/baseline_forecast_summary.csv','config':'configs/baseline_pilot.json'},
 {'claim':'Stationary-bootstrap mock coverage','run':latest['inference'],'table':'results/latest_inference.json','config':'configs/inference_mock.json'},
 {'claim':'Published Patton Table1 replication25/27','run':latest['replication'],'table':'results/patton_table1_replication.csv','config':'configs/replication_patton.json','source':'S12PDFp5 /journal250'},
 {'claim':'Mouti preprint Table2 audit35/48 and independent numerical checks','run':latest['mouti_audit'],'table':'results/mouti_table2_audit.csv','config':'configs/mouti_table2.json','source':'S08PDFpp9-10'},
 {'claim':'SPY coverage, missing early closes, scaling flags and final-test sealing','run':latest['data_audit'],'table':'results/data_quality.json','config':'scripts/audit_data.py','source':'D05PDFpp23-26; SPYRM.Rd'},
 {'claim':'Formula identities/limits, conditional-minus implementation and leakage check','run':latest['formulas'],'table':'results/formula_checks.json','source':'Source-referenced notebook'},
 {'claim':'Substantive literature claims and novelty overlap','source':'literature/evidence_cards.json','locations':'Per-card precise PDFpages/sections; targeted scope, no abstract-omission claims'},
 {'claim':'Printed stationary conditional-variance sign in S09','source':'S09PDFp22 beloweq35','verification':'Visually inspected tmp/S09_p22.png; no author-execution-code inference'}]
 write(R/'manifests/claim_ledger.json',ledger)
 tests=ET.parse(R/'results/test_results.xml').getroot();suites=tests.findall('.//testsuite');counts={k:sum(int(x.attrib.get(k,0)) for x in suites) for k in ['tests','failures','errors','skipped']}
 gates={'G0':{'status':'partial','reason':'Closest overlaps and defensible narrowing documented; publication novelty not established'},'G1':{'status':'technical_pass_independent_review_open','reason':'Executed notebook and scientific checks; no human review fabricated'},'G2':{'status':'partial','reason':'PublicSPYpilot acquired/audited;RQunits/sessionM/overnight/rights and full training history unresolved'},'G3':{'status':'partial','reason':'ExactOU/Cauchy/noise/price validation passed;rough spot-to-IV and inferentialH coverage incomplete'},'G4':{'status':'not_passed','reason':'Coverage/margins/estimated structural fits/execution accounting not frozen'}}
 checkpoint={'schema_version':'1.0','captured_utc':now,'project':'Rough or Just Noisy?','scope':'independent research intended for eventual publication','stage':'preparation_and_pilot_checkpoint_complete','workspace':str(R),'protocol_version':'1.1','production_allowed':False,'gates':gates,'latest_runs':latest,'tests':counts,'literature':{'register_entries':len(sources),'local_PDFs':sum(bool(s.get('full_text_downloaded')) for s in sources),'targeted_cards':len(list((R/'literature/cards').glob('*.md')))},'final_test':{'start':'2020-01-01','end':'2025-12-31','observations_acquired':0,'opened_for_model_development':False},'data':{'development_rows':data['pilot_rows'],'development_period':[data['pilot_start'],data['pilot_end']],'quarantined_validation_rows':data['sealed_validation_rows']},'environment':'manifests/environment.json','raw_manifest':'manifests/raw_inputs.json','source_register':'manifests/source_register_audited.json','claim_ledger':'manifests/claim_ledger.json','repository':'https://github.com/MartinValachy/RoughVolatilityResearch','next_command':'.\\.venv\\Scripts\\python.exe scripts/validate_checkpoint.py','next_actions':['Verify checkpoint, then inspect source construction forSPYRM RQ units/session count without opening final data','Validate a source-grounded rough SPOT variance model, integration and observation construction using numerical refinement','Implement/calibrate a source-faithful inferentialH procedure and comparable estimated rough/nonrough/flexible forecasts','Calibrate dependent inference, register numeric equivalence margins, freeze return/overnight/execution/cash/cost conventions','Complete source-version/supplement/rights review before any public release; keep final test sealed until all scientific gates pass']}
 write(R/'checkpoint.json',checkpoint)
 status=f'''# Status - preparation checkpoint

Updated{now}. Workspace: `{R}`. Scope: **independent research intended for eventual publication**. No production study, public publication, registered thesis or supervision is claimed.

## Completed with evidence

- Read all six original specification files and inspected the two Notion source pages; originals unchanged under `protocol/inputs/`.
- Created isolated Python3.12 environment and frozen dependencies, source/data manifests, decisions, amendments, claim ledger and machine-readable continuation state.
- Acquired{checkpoint['literature']['local_PDFs']}localPDFs;{checkpoint['literature']['register_entries']}source entries (24original+3targeted additions),{checkpoint['literature']['targeted_cards']}targeted evidence cards, novelty matrix and positioning memo. Author code pinned and not executed.
- Executed formula notebook and{counts['tests']}scientific tests ({counts['failures']}failures,{counts['errors']}errors).
- Ran1400independent daily latent paths/62observation cells,100continuous-time Brownian price paths,225000baseline forecasts,1000known-law forecast histories and a bounded Gaussian classification-power experiment.
- Attempted published PattonTable1 replication (25/27cells within preregistered tolerance); independently audited Mouti preprintTable2 (35/48cells within tolerance), retaining discrepancies.
- Audited750publicSPYdevelopment rows;745validation rows quarantined. All6missingNYSEsessions are early closes. RQunits and sessionM unresolved. No2020-2025data acquired.

## Material findings

Noise correction targets a finite-band OU slope, not automatically0.5. A fixed flexible finite OU mixture closely approximates one rough dailyGaussian law; its1250point known-law power bound is about7.68%at exact5%size. This is an illustrative finite-grid result, not an empirical mechanism conclusion or practical-equivalence finding. Forecast/risk diagnostics remain separate.

## Gates and blockers

| Gate | Status |
|---|---|
| G0 | Partial: novelty not established; closest literature overlap narrowed |
| G1 | Technical pass; independent review open |
| G2 | Partial: RQunits, sessionM, upstream rights, full estimation history and return alignment unresolved |
| G3 | Partial: rough spot-to-IV mapping and valid inferentialH coverage still open |
| G4 | Not passed: mock coverage0.80at nominal0.90(MCSE0.073), margins/model fit/execution not frozen |

VOLARE requires a login; no existing entitlement verified. The official author-linked data archive returned403 locally. Harvard realized-kernelPDF was readable in the web reader but returned403for local acquisition. Some Crossref lookups failed; those entries are not treated as authoritative matches. No credentials were entered, messages sent or access controls bypassed.

## Continue exactly here

1. Run `.\\.venv\\Scripts\\python.exe scripts/validate_checkpoint.py`.
2. Read `checkpoint.json`, `protocol/PROTOCOL_v1.1.md` and `manuscript/PILOT_REPORT.md`.
3. Resolve source-supportedSPYRMquarticity/session definitions; keep the final test sealed. Extend rough spot-to-IV numerical validation before empiricalHinterpretation.
4. Implement fair estimated structural fits and calibrate inference before freezing a final contest. Do not interpret bootstrap uncertainty or nonsignificance as equivalence.

Reproduction commands: `README.md`. Numerical claims: `manifests/claim_ledger.json`. Exact runs/configurations: `manifests/run_index.json`. No additional user input is needed to inspect/reproduce this checkpoint; further data access can be incorporated when available.
'''
 (R/'STATUS.md').write_text(status,encoding='utf8')
 # Preserve input bytes and make casual accidental rewrites fail on Windows.
 for rec in raw:
  p=R/rec['path'];p.chmod(stat.S_IREAD)
 print('Checkpoint written:',counts,';',checkpoint['literature'])
if __name__=='__main__':main()
