"""Verify A13 export and frozen coverage before extracting to private storage."""
from pathlib import Path, PurePosixPath
import argparse, csv, hashlib, io, json, runpy, zipfile
from phase1_support import ROOT, record_run, sha
from reconcile_spy import calendar_sessions


def digest(content):
    return hashlib.sha256(content).hexdigest()


def verify_archive(archive, destination, a10):
    archive, destination, a10 = map(lambda p: Path(p).resolve(), (archive, destination, a10))
    if destination == ROOT or ROOT in destination.parents or 'sealed' in [p.lower() for p in destination.parts]:
        raise ValueError('Extract only into external private training storage')
    cfg = json.loads((ROOT/'configs/etf_breadth.json').read_text())
    plan = json.loads((ROOT/'wrds_queries/A13_FIXED_PLAN.json').read_text())
    embedded = runpy.run_path(str(ROOT/'wrds_queries/a13_etf_breadth.py'))
    calendar = embedded['A13_CALENDAR']
    independent = calendar_sessions(cfg['start'], cfg['end'])
    if set(calendar) != set(independent):
        raise ValueError('Frozen calendar differs from independent calendar')
    for day, minutes in independent.items():
        if calendar[day] != dict(date=day, open_seconds=34200,
                                 close_seconds=34200+60*minutes, early_close=minutes < 390):
            raise ValueError('Frozen session hours differ')
    rule = digest(json.dumps(dict(code=plan['code_sha256'], config=cfg, calendar=calendar,
        sql=embedded['aggregate_sql']('audit_source')), sort_keys=True).encode())
    expected = {'paired/'+symbol+'_'+day+'.csv' for day in independent for symbol in cfg['panel']}
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or z.testzip() is not None:
            raise ValueError('Duplicate ZIP member or CRC failure')
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe ZIP member')
            allowed = name in {'A13_PACKAGE_METADATA.json','acquisition_manifest.json','frozen_config.json',
                'frozen_calendar.json','source_code_hashes.json','measurement_template.sql','progress.json'}
            allowed |= name in expected
            allowed |= (str(path.parent) in {'diagnostics','private/query_specs'} and path.suffix == '.json')
            if not allowed:
                raise ValueError('Member outside aggregate/provenance allowlist: '+name)
        meta = json.loads(z.read('A13_PACKAGE_METADATA.json'))
        if (meta['phase'], meta['status'], meta['checked_paired_symbol_days'], meta['expected_paired_symbol_days']) != (
                'FULL', 'passed_checks', len(expected), len(expected)):
            raise ValueError('Full fixed panel not complete')
        if meta['raw_ticks_included'] or meta['closed_period_observations_included']:
            raise ValueError('Forbidden export observations')
        if meta['code_sha256'] != plan['code_sha256'] or meta['rule_hash'] != rule:
            raise ValueError('Acquisition code/rule signature differs')
        member_map = {m['path']: m for m in meta['members']}
        if len(member_map) != len(meta['members']) or set(member_map) != set(names)-{'A13_PACKAGE_METADATA.json'}:
            raise ValueError('Incomplete or duplicate package hash inventory')
        for name, item in member_map.items():
            content = z.read(name)
            if len(content) != item['bytes'] or digest(content) != item['sha256']:
                raise ValueError('Export member integrity differs: '+name)
        if json.loads(z.read('frozen_config.json')) != cfg or json.loads(z.read('frozen_calendar.json')) != calendar:
            raise ValueError('Frozen configuration/calendar differs')
        if json.loads(z.read('source_code_hashes.json')) != plan['components']:
            raise ValueError('Embedded source-component hashes differ')
        manifest = json.loads(z.read('acquisition_manifest.json'))
        if manifest['rule_hash'] != rule or set(n for n in names if n.startswith('paired/')) != expected:
            raise ValueError('Manifest rule/fixed panel differs')
        reused = 0
        for name in sorted(expected):
            item = manifest['files'][name]
            content = z.read(name)
            symbol, day = Path(name).stem.split('_',1)
            signature = digest((rule+symbol+day).encode())
            if (item['sha256'] != digest(content) or item['query_sha256'] != signature or item['rows'] != 30
                    or item.get('independent_check_passed') is not True or item.get('exact_record_alignment') is not True):
                raise ValueError('Daily integrity/independent check missing: '+name)
            reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
            rows = list(reader)
            if len(rows) != 30 or any(r['date'][:10] != day or r['symbol'] != symbol for r in rows):
                raise ValueError('Daily symbol/date count differs')
            if day.startswith(cfg['already_observed_month']):
                if not item.get('reused_A10') or sha(a10/name) != item['sha256']:
                    raise ValueError('Previously observed January aggregate differs')
                reused += 1
            elif item.get('reused_A10'):
                raise ValueError('Unexpected reused date')
        for phase, dates, pairs in [('day',1,1),('month',plan['month_pilot_dates'],4*plan['month_pilot_dates']),
                                    ('full',plan['new_acquisition_dates'],plan['new_paired_symbol_days'])]:
            phase_meta = json.loads(z.read('diagnostics/phase_'+phase+'.json'))
            if (phase_meta['status'],phase_meta['dates'],phase_meta['paired_symbol_days'],phase_meta['rule_hash']) != (
                    'passed_checks',dates,pairs,rule):
                raise ValueError('Bounded acquisition phase differs: '+phase)
        destination.mkdir(parents=True,exist_ok=True)
        for name in names:
            target = destination.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            content = z.read(name)
            if target.exists() and target.read_bytes() != content:
                raise ValueError('Do not overwrite a changed private member: '+name)
            target.write_bytes(content)
    result = dict(status='passed_checks',paired_symbol_days=len(expected),reused_January_pairs=reused,
        new_symbol_days=len(expected)-reused,member_hashes_verified=len(member_map),archive_sha256=sha(archive),
        rule_hash=rule,source_code_matches_local=True,independent_calendar=True,all_daily_checks_present=True,
        raw_ticks_downloaded=False,sealed_observations_opened=False,code_sha256=sha(__file__))
    run = record_run('etf_breadth_export_verified',result)
    (ROOT/'results/etf_breadth_export_verified.json').write_text(json.dumps(dict(result,run_id=run),indent=2)+'\n')
    print(json.dumps(dict(result,run_id=run)))
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--private',type=Path,required=True)
    p.add_argument('--a10',type=Path,required=True)
    a=p.parse_args();verify_archive(a.archive,a.private,a.a10)
