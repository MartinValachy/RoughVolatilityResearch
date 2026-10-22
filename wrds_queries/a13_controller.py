"""A13 controller, combined with frozen A10 definitions by build_a13_notebook.py.

This file is a build input, not a standalone downloader. The generated notebook
and a13_etf_breadth.py contain all owned measurement/acquisition definitions.
"""
import contextlib
import importlib
import shutil
import subprocess
import types
import zipfile


A13_CASES = (
    'millisecond_time__millisecond_flags', 'millisecond_time__legacy_flags',
    'legacy_time__millisecond_flags', 'legacy_time__legacy_flags',
    'legacy_restore_modern_category_B',
)
A13_OUTPUT_NAME = 'A13_etf_breadth_v1'


def a13_validate_config(config, calendar):
    """Reject scope changes rather than treating them as downloader options."""
    if (config != A13_CONFIG or hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
            != A13_COMPONENT_HASHES['config_canonical_sha256']):
        raise ValueError('A13 config differs from the embedded frozen protocol')
    if (config['start'], config['end'], config['panel']) != (
            '2013-01-02', '2014-07-31', ['QQQ', 'IWM', 'EFA', 'TLT']):
        raise ValueError('A13 fixed date/panel boundary changed')
    if config['production_allowed'] or config['already_observed_month'] != '2014-01':
        raise ValueError('A13 production/reuse boundary changed')
    if (calendar != A13_CALENDAR or hashlib.sha256(json.dumps(calendar, sort_keys=True).encode()).hexdigest()
            != A13_COMPONENT_HASHES['calendar_canonical_sha256']):
        raise ValueError('The frozen exchange calendar changed')
    for day, row in calendar.items():
        dt.date.fromisoformat(day)
        if not config['start'] <= day <= config['end']:
            raise ValueError('Calendar escaped the fixed training window')
        if row['date'] != day or row['open_seconds'] != 34200:
            raise ValueError('Unexpected session opening convention')
        if row['close_seconds'] not in (46800, 57600):
            raise ValueError('Unexpected regular/early-close session')


def a13_jobs(config, calendar, phase):
    a13_validate_config(config, calendar)
    if phase == 'day':
        return [(config['pilot_day'], ['QQQ'])]
    if phase not in ('month', 'full'):
        raise ValueError('Unknown bounded A13 phase')
    dates = [day for day in sorted(calendar)
             if not day.startswith(config['already_observed_month'])]
    if phase == 'month':
        dates = [day for day in dates if day.startswith(config['pilot_month'])]
    return [(day, list(config['panel'])) for day in dates]


class A13VerifiedStore(Store):
    def cached(self, relative, query_hash=None):
        valid = super().cached(relative, query_hash)
        if valid and relative.startswith('paired/'):
            row = self.manifest['files'][relative]
            valid = (row.get('independent_check_passed') is True
                     and row.get('exact_record_alignment') is True
                     and row.get('rows') == 30)
        return valid


class A13Breadth(A10FrozenSourceReplication):
    """Unchanged A10 source/measurement methods, different bounded scheduler/store."""
    def __init__(self, config, engine, sas, calendar, output_parent, a10_root):
        a13_validate_config(config, calendar)
        self.config, self.engine, self.sas, self.calendar = config, engine, sas, calendar
        self.code_hash = A13_CODE_HASH
        output_parent, self.a10_root = Path(output_parent).resolve(), Path(a10_root).resolve()
        output = (output_parent / A13_OUTPUT_NAME).resolve()
        if output == self.a10_root or self.a10_root in output.parents:
            raise ValueError('A13 output must be separate from the A10 directory')
        signature = hashlib.sha256(json.dumps({
            'code': A13_CODE_HASH, 'config': config, 'calendar': calendar,
            'sql': engine.aggregate_sql('audit_source'),
        }, sort_keys=True).encode()).hexdigest()
        self.store = A13VerifiedStore(output, signature)
        engine.dump_json(self.store.path('frozen_config.json'), config)
        engine.dump_json(self.store.path('frozen_calendar.json'), calendar)
        engine.dump_json(self.store.path('source_code_hashes.json'), A13_COMPONENT_HASHES)
        self.store.path('measurement_template.sql').write_text(
            engine.aggregate_sql('SELECT * FROM audit_source WHERE date=:day'), encoding='utf-8')

    def allowed(self, day, symbols):
        dt.date.fromisoformat(day)
        if not '2013-01-02' <= day <= '2014-07-31' or day not in self.calendar:
            raise ValueError('Unregistered A13 source-audit day')
        if day.startswith('2014-01'):
            raise ValueError('January 2014 must be reused, not reacquired')
        if len(symbols) != 1 or symbols[0] not in ('QQQ', 'IWM', 'EFA', 'TLT'):
            raise ValueError('A13 reads exactly one registered fund/day at a time')

    def source_frame(self, day, symbols, kind):
        if kind not in ('legacy', 'millisecond'):
            raise ValueError('Unknown A13 source representation')
        return super().source_frame(day, symbols, kind)

    def _signature(self, day, symbol):
        return hashlib.sha256((self.store.rule_hash + symbol + day).encode()).hexdigest()

    def reuse_january(self):
        """Copy existing checked aggregates, never reread their underlying trades."""
        manifest = json.loads((self.a10_root / 'acquisition_manifest.json').read_text())
        expected_grid = {(case, frequency) for case in A13_CASES
                         for frequency in self.config['frequencies_seconds']}
        reused = 0
        for day in sorted(self.calendar):
            if not day.startswith(self.config['already_observed_month']):
                continue
            for symbol in self.config['panel']:
                relative = 'paired/' + symbol + '_' + day + '.csv'
                record = manifest.get('files', {}).get(relative)
                source = (self.a10_root / relative).resolve()
                if self.a10_root not in source.parents or record is None:
                    raise ValueError('Missing A10 January aggregate: ' + relative)
                if not (record.get('independent_check_passed') is True
                        and record.get('exact_record_alignment') is True
                        and record.get('rows') == 30):
                    raise ValueError('A10 January independent/correspondence checks absent: ' + relative)
                if digest_file(source) != record['sha256']:
                    raise ValueError('A10 January aggregate hash changed: ' + relative)
                with source.open(encoding='utf-8-sig', newline='') as stream:
                    rows = list(csv.DictReader(stream))
                if len(rows) != 30 or {(r['case'], int(r['frequency_seconds'])) for r in rows} != expected_grid:
                    raise ValueError('A10 January case/frequency grid changed: ' + relative)
                if any(r['date'][:10] != day or r['symbol'] != symbol for r in rows):
                    raise ValueError('A10 January symbol/date mismatch: ' + relative)
                sig = self._signature(day, symbol)
                if not self.store.cached(relative, sig):
                    target = self.store.path(relative)
                    pending = target.with_name(target.name + '.partial')
                    pending.write_bytes(source.read_bytes())
                    os.replace(pending, target)
                    extras = {key: value for key, value in record.items()
                              if key not in ('sha256', 'bytes', 'rows', 'source', 'query_sha256', 'export_utc')}
                    extras.update(reused_A10=True, original_A10_sha256=record['sha256'],
                                  original_A10_rule_hash=manifest['rule_hash'])
                    self.store.record(relative, 30, record.get('source', 'verified A10 January aggregate'), sig, **extras)
                reused += 1
        self.engine.dump_json(self.store.path('diagnostics/january_reuse.json'), {
            'status': 'passed_checks', 'paired_symbol_days': reused,
            'new_source_reads': 0, 'method': 'Existing A10 aggregate member hashes and check records',
        })
        return reused

    def run(self, phase):
        # Resuming full still reruns the bounded pilot stages against cache before
        # arriving here, so no scheduler can silently bypass those prerequisites.
        if phase != 'day':
            prerequisite = 'day' if phase == 'month' else 'month'
            path = self.store.path('diagnostics/phase_' + prerequisite + '.json')
            accepted = json.loads(path.read_text()) if path.exists() else {}
            if accepted.get('status') != 'passed_checks' or accepted.get('rule_hash') != self.store.rule_hash:
                raise ValueError('A13 prerequisite pilot has not passed: ' + prerequisite)
        jobs = a13_jobs(self.config, self.calendar, phase)
        completed_dates = completed_pairs = 0
        start = time.perf_counter()
        for day, symbols in jobs:
            summaries = []
            for symbol in symbols:
                try:
                    result = super().acquire(day, [symbol])
                    if result['status'] == 'saved':
                        day_diag = self.store.path('diagnostics/day_' + day + '.json')
                        if day_diag.exists():
                            self.engine.dump_json(self.store.path('diagnostics/symbol_' + symbol + '_' + day + '.json'),
                                                  json.loads(day_diag.read_text()))
                except Exception as exc:
                    errors = []
                    for kind in ('legacy', 'millisecond'):
                        log_path = self.store.path('diagnostics/error_' + day + '_' + kind + '.log')
                        if log_path.is_file():
                            for line in log_path.read_text(errors='replace').splitlines():
                                if re.match(r'^\s*(?:ERROR(?:\s+\d+-\d+)?|WARNING):', line):
                                    errors.append({'source_kind': kind, 'message': line.strip()[:500]})
                    if errors:
                        self.engine.dump_json(self.store.path('diagnostics/error_summary_' + symbol + '_' + day + '.json'),
                                              {'errors': errors[:20], 'raw_SAS_log_in_archive': False})
                    progress = {'phase': phase, 'status': 'stopped_on_error', 'date': day, 'symbol': symbol,
                                'completed_dates': completed_dates, 'completed_symbol_days': completed_pairs,
                                'planned_dates': len(jobs), 'error_type': type(exc).__name__,
                                'message': str(exc)[:300], 'seconds': time.perf_counter() - start}
                    self.engine.dump_json(self.store.path('progress.json'), progress)
                    raise
                finally:
                    # Temporary raw subsets stay in SAS WORK on WRDS, never in
                    # the persistent output/archive. Clean them on failure too.
                    with contextlib.suppress(Exception):
                        self.sas.submit('proc datasets lib=work nolist; delete rjn_audit rjn_audit_count; quit;', results='TEXT')
                summaries.append({'symbol': symbol, 'status': result['status']})
                completed_pairs += 1
            self.engine.dump_json(self.store.path('diagnostics/day_' + day + '.json'),
                                  {'date': day, 'status': 'passed_checks', 'symbols': summaries})
            completed_dates += 1
            if completed_dates % 5 == 0 or completed_dates == len(jobs):
                progress = {'phase': phase, 'status': 'running' if completed_dates < len(jobs) else 'passed_checks',
                            'completed_dates': completed_dates, 'planned_dates': len(jobs),
                            'completed_symbol_days': completed_pairs, 'last_date': day,
                            'seconds': time.perf_counter() - start, 'code_sha256': self.code_hash}
                self.engine.dump_json(self.store.path('progress.json'), progress)
                print(json.dumps(progress), flush=True)
        summary = {'phase': phase, 'status': 'passed_checks', 'dates': completed_dates,
                   'paired_symbol_days': completed_pairs, 'seconds': time.perf_counter() - start,
                   'rule_hash': self.store.rule_hash}
        self.engine.dump_json(self.store.path('diagnostics/phase_' + phase + '.json'), summary)
        return summary

    def export(self, completed):
        """Allowlisted aggregates and provenance only, including partial diagnostics."""
        expected = [('paired/' + symbol + '_' + day + '.csv', self._signature(day, symbol))
                    for day in sorted(self.calendar) for symbol in self.config['panel']]
        accepted = [relative for relative, sig in expected if self.store.cached(relative, sig)]
        if completed and len(accepted) != len(expected):
            raise ValueError('A13 full export is missing checked aggregate members')
        phase = 'FULL' if completed else 'PARTIAL'
        archive = self.store.root.parent / ('RJN_A13_ETF_BREADTH_' + phase + '.zip')
        pending = archive.with_name(archive.name + '.partial')
        members = []
        with zipfile.ZipFile(pending, 'w', zipfile.ZIP_DEFLATED) as z:
            # No arbitrary directory scan, raw subset, notebook output, SAS log,
            # credential config or sealed data can enter this allowlist.
            names = set(accepted)
            for relative in ('acquisition_manifest.json', 'frozen_config.json', 'frozen_calendar.json',
                             'source_code_hashes.json', 'measurement_template.sql', 'progress.json'):
                if self.store.path(relative).is_file():
                    names.add(relative)
            names.update(p.relative_to(self.store.root).as_posix()
                         for folder in ('diagnostics', 'private/query_specs')
                         for p in self.store.path(folder).glob('*.json') if p.is_file())
            for relative in sorted(names):
                p = self.store.path(relative)
                content = p.read_bytes()
                z.writestr(relative, content)
                members.append({'path': relative, 'bytes': len(content),
                                'sha256': hashlib.sha256(content).hexdigest()})
            metadata = {'phase': phase, 'status': 'passed_checks' if completed else 'incomplete_stopped',
                        'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                        'expected_paired_symbol_days': len(expected), 'checked_paired_symbol_days': len(accepted),
                        'code_sha256': self.code_hash, 'rule_hash': self.store.rule_hash,
                        'raw_ticks_included': False, 'closed_period_observations_included': False,
                        'published_online': False, 'members': members}
            z.writestr('A13_PACKAGE_METADATA.json', json.dumps(metadata, indent=2))
        os.replace(pending, archive)
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:
                raise ValueError('Archive CRC check failed')
            for row in members:
                if hashlib.sha256(z.read(row['path'])).hexdigest() != row['sha256']:
                    raise ValueError('Export member hash check failed')
        return archive, metadata


def a13_runtime():
    """Start only local STDIO SAS inside an already authenticated WRDS host."""
    if os.name != 'posix' or not Path('/wrds/nyse').is_dir():
        raise RuntimeError('Run this notebook inside WRDS Jupyter, not on your local computer')
    global duckdb
    for package in ('duckdb', 'saspy'):
        if importlib.util.find_spec(package) is None:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', package], timeout=300)
    duckdb = importlib.import_module('duckdb')
    # Locate the existing A10 folder without examining the user's home/config.
    candidates = [Path.cwd(), Path.cwd() / 'RJN_WRDS_DATA',
                  Path.cwd() / 'rough_noisy_setup' / 'RJN_WRDS_DATA']
    roots = {p.resolve() for p in candidates
             if (p / 'A10_source_replication_v2' / 'acquisition_manifest.json').is_file()}
    if len(roots) != 1:
        raise RuntimeError('Upload/open the notebook in RJN_WRDS_DATA beside A10_source_replication_v2, then run it there')
    output_parent = roots.pop()
    existing = globals().get('sas')
    if existing is not None and callable(getattr(existing, 'submit', None)):
        session = existing
    else:
        executable = shutil.which('sas')
        if not executable:
            raise RuntimeError('Local SAS executable is not on PATH. Return this error; do not enter credentials or rerun old acquisition cells')
        config_dir = output_parent / A13_OUTPUT_NAME
        config_dir.mkdir(exist_ok=True)
        cfg = config_dir / '_a13_local_sas_config.py'
        cfg.write_text("SAS_config_names = ['rjn_a13_local']\n"
                       + "SAS_config_options = {'lock_down': True, 'verbose': False}\n"
                       + 'rjn_a13_local = ' + repr({'saspath': executable}) + '\n', encoding='utf-8')
        saspy = importlib.import_module('saspy')
        session = saspy.SASsession(cfgfile=str(cfg), cfgname='rjn_a13_local', results='TEXT')
    health = session.submit('%put RJN_A13_LOCAL_SAS_OK;', results='TEXT').get('LOG', '')
    if 'RJN_A13_LOCAL_SAS_OK' not in health or re.search(r'(?m)^\s*ERROR(?:\s+\d+-\d+)?:', health):
        raise RuntimeError('Local SAS health check failed; no source acquisition started')
    engine = types.SimpleNamespace(Store=Store, dump_json=dump_json, aggregate_sql=aggregate_sql,
                                   independent_measures=independent_measures, write_records=write_records)
    return A13Breadth(A13_CONFIG, engine, session, A13_CALENDAR, output_parent,
                     output_parent / 'A10_source_replication_v2')


def run_a13_notebook():
    audit = a13_runtime()
    print('A13 fixed training-only acquisition. January2014 is reused. No raw ticks leave WRDS.', flush=True)
    print(json.dumps({'calendar_dates': len(A13_CALENDAR), 'new_dates': len(a13_jobs(A13_CONFIG, A13_CALENDAR, 'full')),
                      'panel': A13_CONFIG['panel'], 'fixed_end': A13_CONFIG['end']}), flush=True)
    completed = False
    try:
        reused = audit.reuse_january()
        print(json.dumps({'January2014_checked_aggregate_pairs_reused': reused}), flush=True)
        for phase in ('day', 'month', 'full'):
            print('Starting bounded phase: ' + phase, flush=True)
            audit.run(phase)
        completed = True
    except Exception as exc:
        print('STOPPED: ' + type(exc).__name__ + ': ' + str(exc)[:300], flush=True)
        print('No later phase ran. Keep the saved outputs. Run All resumes checked members after the issue is resolved.', flush=True)
    archive, metadata = audit.export(completed)
    print(json.dumps({'status': metadata['status'], 'archive': archive.name,
                      'checked_paired_symbol_days': metadata['checked_paired_symbol_days'],
                      'expected_paired_symbol_days': metadata['expected_paired_symbol_days'],
                      'sha256': digest_file(archive), 'bytes': archive.stat().st_size}), flush=True)
    from IPython.display import FileLink, display
    display(FileLink(os.path.relpath(archive, Path.cwd())))
    return {'status': metadata['status'], 'archive': archive.name}
