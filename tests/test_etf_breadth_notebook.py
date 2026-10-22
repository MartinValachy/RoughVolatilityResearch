"""Offline A13 transport/scheduler checks. All records in these tests are synthetic."""
from pathlib import Path
import copy
import csv
import importlib.util
import json
import types
import zipfile

import duckdb
import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('a13_test_subject', ROOT/'wrds_queries/a13_etf_breadth.py')
A13 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A13)
A13.duckdb = duckdb


class FakeSAS:
    def __init__(self, count=1):
        self.count = count
        self.transfers = []

    def submit(self, program, results='TEXT'):
        return {'LOG': 'RJN_A13_LOCAL_SAS_OK'}

    def sasdata2dataframe(self, table, **kwargs):
        self.transfers.append(table)
        if table != 'rjn_audit_count':
            raise AssertionError('Oversized raw subset must never transfer')
        return pd.DataFrame({'n': [self.count]})


def engine():
    return types.SimpleNamespace(Store=A13.Store, dump_json=A13.dump_json,
                                 aggregate_sql=A13.aggregate_sql,
                                 independent_measures=A13.independent_measures,
                                 write_records=A13.write_records)


def audit(tmp_path, cls=A13.A13Breadth, sas=None):
    parent = tmp_path/'RJN_WRDS_DATA'
    parent.mkdir(exist_ok=True)
    return cls(copy.deepcopy(A13.A13_CONFIG), engine(), sas or FakeSAS(),
               copy.deepcopy(A13.A13_CALENDAR), parent, parent/'A10_source_replication_v2')


def fake_rows(day, symbol):
    m = A13.A13_CALENDAR[day]['close_seconds']-34200
    return [dict(date=day, symbol=symbol, case=case, frequency_seconds=frequency,
                 M_expected=m//frequency, M_observed=m//frequency, RV=.0001, RQ=1e-8)
            for case in A13.A13_CASES for frequency in A13.A13_CONFIG['frequencies_seconds']]


def test_fixed_calendar_panel_and_phase_geometry():
    jobs = A13.a13_jobs(A13.A13_CONFIG, A13.A13_CALENDAR, 'full')
    assert len(A13.A13_CALENDAR) == 398
    assert len(jobs) == 377
    assert len(A13.a13_jobs(A13.A13_CONFIG, A13.A13_CALENDAR, 'month')) == 19
    assert A13.a13_jobs(A13.A13_CONFIG, A13.A13_CALENDAR, 'day') == [('2013-02-01', ['QQQ'])]
    assert all('2013-01-02' <= day <= '2014-07-31' and not day.startswith('2014-01')
               and symbols == ['QQQ', 'IWM', 'EFA', 'TLT'] for day, symbols in jobs)
    assert A13.A13_CALENDAR['2013-07-03']['close_seconds'] == 46800


def test_scope_calendar_and_reuse_boundaries_reject_changes(tmp_path):
    a = audit(tmp_path)
    for day, symbols in [('2020-01-02', ['QQQ']), ('2017-01-03', ['QQQ']),
                         ('2014-01-02', ['QQQ']), ('2013-02-01', ['SPY']),
                         ('2013-02-01', ['QQQ', 'IWM'])]:
        with pytest.raises(ValueError):
            a.allowed(day, symbols)
    cfg = copy.deepcopy(A13.A13_CONFIG)
    cfg['EWMA_lambda'] = .95
    with pytest.raises(ValueError, match='frozen protocol'):
        A13.a13_validate_config(cfg, A13.A13_CALENDAR)
    cal = copy.deepcopy(A13.A13_CALENDAR)
    cal['2013-07-03']['close_seconds'] = 57600
    with pytest.raises(ValueError, match='calendar changed'):
        A13.a13_validate_config(A13.A13_CONFIG, cal)


def test_new_store_never_replaces_A10(tmp_path):
    a = audit(tmp_path)
    assert a.store.root.name == 'A13_etf_breadth_v1'
    assert not a.a10_root.exists()
    a.a10_root.mkdir()
    with pytest.raises(ValueError):
        A13.A13Breadth(A13.A13_CONFIG, engine(), FakeSAS(), A13.A13_CALENDAR,
                      a.a10_root.parent, a.store.root)


def make_january(a):
    root = a.a10_root
    (root/'paired').mkdir(parents=True)
    files = {}
    for day in A13.A13_CALENDAR:
        if not day.startswith('2014-01'):
            continue
        for symbol in A13.A13_CONFIG['panel']:
            rel = 'paired/'+symbol+'_'+day+'.csv'
            rows = fake_rows(day, symbol)
            with (root/rel).open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            files[rel] = dict(sha256=A13.digest_file(root/rel), rows=30, source='synthetic fixture',
                              independent_check_passed=True, exact_record_alignment=True)
    (root/'acquisition_manifest.json').write_text(json.dumps(dict(rule_hash='synthetic_a10', files=files)))
    return next(iter(files))


def test_january_reused_from_checked_aggregate_hashes(tmp_path):
    a = audit(tmp_path)
    first = make_january(a)
    assert a.reuse_january() == 84
    assert a.reuse_january() == 84
    assert a.store.manifest['files'][first]['reused_A10'] is True
    assert a.store.manifest['files'][first]['original_A10_rule_hash'] == 'synthetic_a10'
    with (a.a10_root/first).open('a') as stream:
        stream.write('planted corruption')
    with pytest.raises(ValueError, match='hash changed'):
        a.reuse_january()


class SyntheticAudit(A13.A13Breadth):
    def source_frame(self, day, symbols, kind):
        self.allowed(day, symbols)
        self.calls = getattr(self, 'calls', []) + [(day, symbols[0], kind)]
        seconds = np.arange(34200, self.calendar[day]['close_seconds']+1, 15, dtype=float)
        values = 100 + .0008*np.arange(len(seconds)) + .08*np.sin(np.arange(len(seconds))/13)
        frame = pd.DataFrame(dict(symbol=symbols[0], date=A13.dt.date.fromisoformat(day),
                                  ts_seconds=seconds+(.1 if kind=='millisecond' else 0),
                                  price=values, size=100, exchange='P', sale_condition_raw='',
                                  correction_raw='0', sequence_raw=None, time_nano_raw=None))
        return frame, dict(source='synthetic/'+kind, rows=len(frame), subset_sha256=kind)


def test_actual_frozen_SQL_independent_path_and_resume(tmp_path):
    a = audit(tmp_path, SyntheticAudit)
    result = a.acquire('2013-02-01', ['QQQ'])
    assert result['status'] == 'saved'
    assert len(a.calls) == 2
    assert a.acquire('2013-02-01', ['QQQ'])['status'] == 'cached'
    assert len(a.calls) == 2
    record = a.store.manifest['files']['paired/QQQ_2013-02-01.csv']
    assert record['rows'] == 30 and record['independent_check_passed']
    record['independent_check_passed'] = False
    assert a.acquire('2013-02-01', ['QQQ'])['status'] == 'saved'
    assert len(a.calls) == 4


def test_planted_moment_error_fails_independent_check(tmp_path):
    a = audit(tmp_path, SyntheticAudit)
    original = a.engine.independent_measures
    def altered(*args):
        result = original(*args)
        result[0]['RV'] *= 10000
        return result
    a.engine.independent_measures = altered
    with pytest.raises(ValueError, match='Independent moment check failed: RV'):
        a.acquire('2013-02-01', ['QQQ'])
    assert 'paired/QQQ_2013-02-01.csv' not in a.store.manifest['files']


def test_row_bound_stops_before_raw_transfer(tmp_path, monkeypatch):
    sas = FakeSAS(2500001)
    a = audit(tmp_path, sas=sas)
    original = Path.stat
    def stat(path, *args, **kwargs):
        if path.as_posix().startswith('/wrds/'):
            return types.SimpleNamespace(st_size=123, st_mtime_ns=1)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'stat', stat)
    with pytest.raises(ValueError, match='fixed memory bound'):
        a.source_frame('2013-02-01', ['QQQ'], 'legacy')
    assert sas.transfers == ['rjn_audit_count']


def test_pilot_prerequisites_and_stop_on_first_failure(tmp_path, monkeypatch):
    a = audit(tmp_path)
    with pytest.raises(ValueError, match='prerequisite'):
        a.run('full')
    calls = []
    def fail(self, day, symbols):
        calls.append((day, symbols))
        raise PermissionError('synthetic permission denial')
    monkeypatch.setattr(A13.A10FrozenSourceReplication, 'acquire', fail)
    with pytest.raises(PermissionError):
        a.run('day')
    assert calls == [('2013-02-01', ['QQQ'])]
    progress = json.loads(a.store.path('progress.json').read_text())
    assert progress['status'] == 'stopped_on_error' and progress['completed_symbol_days'] == 0
    assert not a.store.path('diagnostics/phase_day.json').exists()


def test_export_allowlist_and_false_full_claim_rejected(tmp_path):
    a = audit(tmp_path, SyntheticAudit)
    a.acquire('2013-02-01', ['QQQ'])
    a.store.path('raw_ticks.csv').write_text('synthetic secret fixture excluded')
    a.store.path('_a13_local_sas_config.py').write_text('synthetic config excluded')
    archive, metadata = a.export(False)
    assert metadata['checked_paired_symbol_days'] == 1
    assert metadata['status'] == 'incomplete_stopped'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert 'raw_ticks.csv' not in z.namelist()
        assert '_a13_local_sas_config.py' not in z.namelist()
        assert 'paired/QQQ_2013-02-01.csv' in z.namelist()
        assert not json.loads(z.read('A13_PACKAGE_METADATA.json'))['raw_ticks_included']
    with pytest.raises(ValueError, match='missing checked aggregate'):
        a.export(True)


def test_run_all_stops_before_month_or_full_and_exports_partial(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = []
    archive = tmp_path/'partial.zip'
    archive.write_bytes(b'synthetic archive placeholder')
    class Controller:
        def reuse_january(self):
            calls.append('reuse')
            return 84
        def run(self, phase):
            calls.append(phase)
            raise PermissionError('synthetic pilot permission failure')
        def export(self, completed):
            calls.append(('export', completed))
            return archive, dict(status='incomplete_stopped', checked_paired_symbol_days=0,
                                 expected_paired_symbol_days=1592)
    monkeypatch.setattr(A13, 'a13_runtime', lambda: Controller())
    import IPython.display
    monkeypatch.setattr(IPython.display, 'display', lambda *args: None)
    result = A13.run_a13_notebook()
    assert calls == ['reuse', 'day', ('export', False)]
    assert result['status'] == 'incomplete_stopped'
