"""Verify local A10 provenance without trusting a successful analysis status."""
from pathlib import Path
import argparse,json
from phase1_support import ROOT as R,record_run,sha
from reconcile_spy import calendar_sessions


def verify(private):
    private=Path(private).resolve()
    if private==R or R in private.parents: raise ValueError('Private export must remain outside repository')
    meta=json.loads((private/'A10_PACKAGE_METADATA.json').read_text())
    cfg=json.loads((R/'configs/source_replication.json').read_text())
    if json.loads((private/'frozen_config.json').read_text())!=cfg: raise ValueError('Frozen configuration differs')
    if meta['phase'] not in ['month','full'] or meta['raw_ticks_included'] or meta['validation_or_final_observations_included']: raise ValueError('Forbidden export phase/content')
    if meta['code_sha256']!=sha(R/'wrds_queries/source_replication.py'): raise ValueError('Acquisition source hash differs')
    manifest=json.loads((private/'acquisition_manifest.json').read_text())
    if meta['rule_hash']!=manifest['rule_hash']: raise ValueError('Rule fingerprint differs')
    dates=sorted(calendar_sessions(cfg['start'],cfg['end']))
    if meta['phase']=='month': dates=[d for d in dates if d.startswith(cfg['panel_month'])]
    expected={'paired/'+s+'_'+d+'.csv' for d in dates for s in (cfg['panel'] if d.startswith(cfg['panel_month']) else ['SPY'])}
    if {p.relative_to(private).as_posix() for p in (private/'paired').glob('*.csv')}!=expected: raise ValueError('Fixed source panel differs')
    if meta['paired_symbol_days']!=len(expected): raise ValueError('Export count differs')
    for member in meta['members']:
        p=private/member['path']
        if p.stat().st_size!=member['bytes'] or sha(p)!=member['sha256']: raise ValueError('Changed exported member: '+member['path'])
    for name in expected:
        item=manifest['files'][name]
        if sha(private/name)!=item['sha256'] or item['rows']!=30: raise ValueError('Acquisition manifest integrity differs')
        if not item['independent_check_passed'] or not item['exact_record_alignment']: raise ValueError('Independent source check absent')
    phase=json.loads((private/'diagnostics'/('phase_'+meta['phase']+'.json')).read_text())
    if phase['status']!='passed_checks' or phase['dates']!=len(dates): raise ValueError('Source phase incomplete')
    result={'status':'passed_checks','phase':meta['phase'],'paired_symbol_days':len(expected),
            'member_hashes_verified':len(meta['members']),'source_code_matches_local':True,
            'all_pairs_have_independent_measure_checks':True,'fixed_panel_and_configuration_verified':True,
            'code_sha256':sha(__file__),'raw_ticks_downloaded':False,'sealed_observations_opened':False}
    run=record_run('source_export_verified',result)
    (R/'results/source_export_verified.json').write_text(json.dumps(dict(result,run_id=run),indent=2)+'\n')
    print(json.dumps(dict(result,run_id=run)))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--private',type=Path,required=True);a=p.parse_args();verify(a.private)
