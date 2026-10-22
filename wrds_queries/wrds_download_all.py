"""User-executed WRDS acquisition engine. Importing never connects or reads market data.

All source queries are SELECT-only. Market values stay in the user's filesystem.
No credentials, market rows, automatic emails or uploads are included in diagnostics.
"""
from pathlib import Path
import base64
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import re
import sys
import time
import zipfile
import zlib

import numpy as np
import pandas as pd

def text(statement):
    # The local VOLARE-only path does not need WRDS/SQLAlchemy installed.
    from sqlalchemy import text as sqlalchemy_text
    return sqlalchemy_text(statement)

VERSION = 'rjn-wrds-download-1.0'
ACQUISITION_REVISION = 'permission-resume-2'  # Transport fix; scientific/cache signatures stay unchanged.
DEFAULT_CONFIG = {
    'profile': 'all',  # all or pilot; all automatically passes through pilot first
    'output_directory': 'RJN_WRDS_DATA',
    'training_start': '2007-01-03', 'training_end': '2016-12-31',
    'support_start': '2006-12-29',
    'export_validation_blind': True,
    'validation_start': '2017-01-01', 'validation_end': '2019-12-31',
    'etfs': ['SPY','QQQ','IWM','EFA','TLT'],
    'frequencies_seconds': [15,30,60,300,900,1800],
    'raw_slice_dates': ['2014-11-28','2014-11-26','2015-12-24','2015-08-24','2016-01-20','2016-06-24'],
    # Strict regular-print implementation default. Flags are not mapped to invented vendor labels.
    'accepted_sale_conditions': ['', '@'],
    'query_timeout_seconds': 540,
    'csv_chunk_rows': 50000,
    'independent_check_max_rows': 2000000,
    'independent_relative_tolerance': 1e-7,
    'independent_RV_absolute_tolerance': 1e-12,
    'independent_RQ_absolute_tolerance': 1e-16,
    'independent_BV_absolute_tolerance': 1e-12,
    'volare_archive_path': r'C:\Users\valac\Downloads\realized_variance_stocks.zip',
    'optional_etf_aggregates': False,
    'optional_stock_comparison': False,
}
SOURCES = {
    'wrds_python': 'https://github.com/wharton/wrds',
    'nyse_2014': 'https://people.stern.nyu.edu/jhasbrou/Teaching/POST%202015%20Spring/TAQ/Daily_TAQ_Client_Spec_v2%200.pdf',
    'nyse_later': 'https://wrds-www.wharton.upenn.edu/documents/1967/Daily_TAQ_Client_Spec_v4.0.pdf',
    'policy': 'https://wrds-www.wharton.upenn.edu/pages/about/ai-policy-on-chatgpt-and-other-generative-ai-tools/',
}


def iso(value):
    return dt.date.fromisoformat(str(value)[:10]).isoformat()


def guard_date(value):
    value = iso(value)
    if not '2006-12-29' <= value <= '2019-12-31':
        raise ValueError('Date outside the registered acquisition boundary')
    return value


def identifier(value):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', value):
        raise ValueError('Unsafe SQL identifier')
    return '"'+value+'"'


def relation(schema, table):
    return identifier(schema)+'.'+identifier(table)


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024), b''):
            h.update(part)
    return h.hexdigest()


def dump_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name+'.partial')
    pending.write_text(json.dumps(value,indent=2,default=str,allow_nan=False)+'\n',encoding='utf-8')
    os.replace(pending,path)


def decode_calendar(encoded):
    records = json.loads(zlib.decompress(base64.b64decode(encoded)))
    out = {}
    for r in records:
        guard_date(r['date'])
        if not (r['open_seconds']==34200 and r['close_seconds'] in (46800,57600)):
            raise ValueError('Unexpected session calendar boundary')
        out[r['date']] = r
    return out


def validate_config(config):
    if config['profile'] not in ('all','pilot'):
        raise ValueError('profile must be all or pilot')
    for key in ('training_start','training_end','support_start','validation_start','validation_end'):
        guard_date(config[key])
    if config['training_end']>'2016-12-31' or config['training_start']<='2006-12-29':
        raise ValueError('Training bounds changed')
    if (config['training_start'],config['training_end']) != ('2007-01-03','2016-12-31'):
        raise ValueError('Do not silently change the registered training period')
    if (config['validation_start'],config['validation_end']) != ('2017-01-01','2019-12-31'):
        raise ValueError('Validation export bounds changed')
    if config['etfs'] != DEFAULT_CONFIG['etfs'] or config['frequencies_seconds'] != DEFAULT_CONFIG['frequencies_seconds']:
        raise ValueError('Panel/frequency changes require protocol handling')
    if config['raw_slice_dates'] != DEFAULT_CONFIG['raw_slice_dates']:
        raise ValueError('Only the fixed six raw slice days are permitted')
    if not config['accepted_sale_conditions']:
        raise ValueError('Empty sale-condition rule')


class Store:
    """Atomic, hashed, resumable output store; no credential fields."""
    def __init__(self, root, rule_hash):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True,exist_ok=True)
        self.rule_hash = rule_hash
        self.manifest_path = self.root/'acquisition_manifest.json'
        if self.manifest_path.exists():
            self.manifest = json.loads(self.manifest_path.read_text())
            if self.manifest['rule_hash'] != rule_hash:
                raise RuntimeError('Output folder belongs to different rules/version. Choose a new folder, do not mix runs.')
        else:
            self.manifest = {'engine':VERSION,'rule_hash':rule_hash,'sources':SOURCES,'files':{},'events':[]}
        self.manifest.setdefault('query_specs',[])

    def path(self, relative):
        path = (self.root/relative).resolve()
        if path!=self.root and self.root not in path.parents:
            raise ValueError('Output path escapes the acquisition folder')
        path.parent.mkdir(parents=True,exist_ok=True)
        return path

    def cached(self, relative, query_hash=None):
        record = self.manifest['files'].get(relative)
        if not record or not self.path(relative).exists():
            return False
        if query_hash and record.get('query_sha256') != query_hash:
            return False
        return digest_file(self.path(relative)) == record['sha256']

    def record(self, relative, rows, source, query_hash=None, **extra):
        path = self.path(relative)
        self.manifest['files'][relative] = {
            'sha256':digest_file(path),'bytes':path.stat().st_size,'rows':rows,
            'source':source,'query_sha256':query_hash,'export_utc':dt.datetime.now(dt.timezone.utc).isoformat(),**extra}
        dump_json(self.manifest_path,self.manifest)

    def event(self, kind, **fields):
        self.manifest['events'].append({'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'kind':kind,**fields})
        dump_json(self.manifest_path,self.manifest)

    def save_query(self, statement, params, source, query_hash):
        relative='private/query_specs/'+query_hash+'.json'
        if not self.path(relative).exists():
            dump_json(self.path(relative),{'source':source,'statement':statement,'parameters':params,
                'engine':VERSION,'query_sha256':query_hash,'backend_job_id':self.manifest.get('backend_job_id')})
        if relative not in self.manifest['query_specs']:
            self.manifest['query_specs'].append(relative)


class Client:
    def __init__(self, db, store, config):
        self.db,self.store,self.config = db,store,config
        self._columns = {}
        self._tables = {}
        self.denied_trade_families = set()
        self.access_gaps = []

    def deny_trade_source(self, source, day, exc):
        # A taqmsec/taq alias may expose a view of a forbidden taqm_YEAR namespace.
        # Scope the denial to this table family and year, never all years of an alias.
        key=trade_access_key(source['schema'],source['table'],day)
        self.denied_trade_families.add(key)
        gap={'source':source['schema']+'.'+source['table'],'family':key[1],
             'year':day[:4],'first_denied_date':day,**clean_error(exc)}
        self.access_gaps.append(gap)
        self.store.event('trade_source_permission_denied',**gap)
        connection=getattr(self.db,'connection',None)
        if connection is not None and hasattr(connection,'rollback'):
            connection.rollback()

    def sql(self, statement, params=None, **kwargs):
        # TextClause is essential: pandas exec_driver_sql misinterprets raw LIKE percent signs.
        return self.db.raw_sql(text(statement),params=params,**kwargs)

    def schemas(self):
        return self.sql("SELECT nspname FROM pg_catalog.pg_namespace WHERE has_schema_privilege(nspname,'USAGE') ORDER BY nspname")['nspname'].tolist()

    def tables(self, schema):
        if schema not in self._tables:
            frame = self.sql("SELECT table_name FROM information_schema.tables WHERE table_schema=:schema ORDER BY table_name",{'schema':schema})
            self._tables[schema] = set(frame.table_name)
        return self._tables[schema]

    def columns(self, schema, table):
        key=(schema,table)
        if key not in self._columns:
            f=self.sql("SELECT column_name,data_type FROM information_schema.columns WHERE table_schema=:schema AND table_name=:table ORDER BY ordinal_position",{'schema':schema,'table':table})
            self._columns[key]=dict(zip(f.column_name,f.data_type))
        return self._columns[key]

    def preload_trade_columns(self, schemas):
        if not schemas: return
        frame=self.sql('''SELECT table_schema,table_name,column_name,data_type FROM information_schema.columns
WHERE table_schema=ANY(:schemas) AND (table_name LIKE 'ct%' OR table_name LIKE 'mast%')
ORDER BY table_schema,table_name,ordinal_position''',{'schemas':list(schemas)})
        for (schema,table),block in frame.groupby(['table_schema','table_name'],sort=False):
            self._columns[(schema,table)]=dict(zip(block.column_name,block.data_type))

    def export(self, statement, params, relative, source):
        query_hash=hashlib.sha256((statement+json.dumps(params,sort_keys=True,default=str)).encode()).hexdigest()
        self.store.save_query(statement,params,source,query_hash)
        if self.store.cached(relative,query_hash):
            return self.store.manifest['files'][relative]['rows']
        path=self.store.path(relative)
        pending=path.with_name(path.name+'.partial')
        rows=0; header=True
        opener=gzip.open if str(path).endswith('.gz') else open
        sa_connection=getattr(self.db,'connection',None)
        proxy=getattr(sa_connection,'connection',None) if sa_connection is not None else None
        driver=getattr(proxy,'driver_connection',proxy)
        if driver is not None:
            cursor=driver.cursor()
        else:
            cursor=None
        try:
            if cursor is not None and hasattr(cursor,'copy_expert'):
                # COPY TO STDOUT streams directly to disk; no multi-million-row client frame.
                compiled=text(statement).bindparams(**params).compile(dialect=sa_connection.dialect)
                bound=cursor.mogrify(str(compiled),compiled.params)
                query=bound.decode(getattr(driver,'encoding','utf-8')) if isinstance(bound,bytes) else bound
                with opener(pending,'wt',encoding='utf-8',newline='') as stream:
                    cursor.copy_expert('COPY ('+query+') TO STDOUT WITH (FORMAT CSV, HEADER TRUE)',stream)
                rows=cursor.rowcount if cursor.rowcount>=0 else None
                if rows is None and not relative.startswith('sealed/'):
                    with opener(pending,'rt',encoding='utf-8',newline='') as stream:
                        rows=max(sum(1 for _ in csv.reader(stream))-1,0)
            else:
                chunks=self.sql(statement,params,chunksize=self.config['csv_chunk_rows'],return_iter=True,coerce_float=False)
                with opener(pending,'wt',encoding='utf-8',newline='') as stream:
                    for chunk in chunks:
                        chunk.to_csv(stream,index=False,header=header)
                        header=False; rows+=len(chunk)
        finally:
            if cursor is not None: cursor.close()
        os.replace(pending,path)
        self.store.record(relative,rows,source,query_hash)
        return rows


def choose_source(client, schemas, table, required, preferred):
    for schema in preferred:
        if schema in schemas and table in client.tables(schema):
            columns=client.columns(schema,table)
            if set(required)<=set(columns):
                return schema,table
    raise RuntimeError('Required source/columns unavailable: '+table+'; metadata mapping needs correction')


def trade_access_key(schema, table, day):
    return schema,re.sub(r'\d{4,8}$','{date}',table),day[:4]


def is_permission_denied(exc):
    seen=set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        if getattr(exc,'pgcode',None)=='42501' or getattr(exc,'sqlstate',None)=='42501': return True
        if re.search(r'permission denied for (schema|table|view|relation)\b',str(exc),re.I): return True
        exc=getattr(exc,'orig',None) or getattr(exc,'__cause__',None)
    return False


def trade_source(client, schemas, day):
    """Daily millisecond first, then bounded older daily/monthly TAQ tables if actually exposed."""
    day=guard_date(day); stamp=day.replace('-',''); year=day[:4]
    candidates=[('taqm_'+year,'ctm_'+stamp)]
    for schema in ('taqmsec','taq','taq'+year,'taq_'+year):
        candidates.extend((schema,t) for t in ['ctm_'+stamp,'ct_'+stamp,'ct_'+stamp[:6],'ct_'+year,'ct'])
    required={'date','price','size'}
    for schema,table in candidates:
        if trade_access_key(schema,table,day) in getattr(client,'denied_trade_families',set()):
            continue
        if schema not in schemas or table not in client.tables(schema):
            continue
        cols=client.columns(schema,table)
        if not required<=set(cols):
            continue
        pick=lambda opts:next((v for v in opts if v in cols),None)
        mapping={'time':pick(['time_m','time']),'symbol':pick(['sym_root','symbol','symbol_root']),
                 'suffix':pick(['sym_suffix','symbol_suffix']),'venue':pick(['ex','exchange']),
                 'condition':pick(['tr_scond','cond']),'correction':pick(['tr_corr','corr']),
                 'sequence':pick(['tr_seqnum','seqnum']),'nano':pick(['time_m_nano'])}
        if not all(mapping[k] for k in ['time','symbol','venue','condition','correction']):
            continue
        dtype=cols[mapping['time']]
        if dtype.startswith('time without') or dtype.startswith('time with'):
            seconds='extract(epoch FROM '+identifier(mapping['time'])+')'
        elif dtype in ('integer','smallint','bigint','numeric','double precision','real') and mapping['time']=='time':
            seconds=identifier(mapping['time'])+'::numeric'  # Legacy TAQ seconds from midnight, ASSUMED/tagged.
        else:
            continue
        if mapping['nano']:
            seconds+=' + coalesce('+identifier(mapping['nano'])+',0)::numeric/1000000000'
        suffix=('coalesce(trim('+identifier(mapping['suffix'])+"),'')=''" if mapping['suffix'] else 'TRUE')
        null_or=lambda key,typ:identifier(mapping[key])+'::'+typ if mapping[key] else 'NULL::'+typ
        sql=f'''SELECT date, {seconds} AS ts_seconds, price::double precision AS price,
 size::double precision AS size, {identifier(mapping['venue'])}::text AS exchange,
 {identifier(mapping['condition'])}::text AS sale_condition_raw,
 {identifier(mapping['correction'])}::text AS correction_raw,
 {null_or('sequence','text')} AS sequence_raw, {null_or('nano','integer')} AS time_nano_raw
FROM {relation(schema,table)} WHERE date=:day AND {identifier(mapping['symbol'])}=:symbol AND {suffix}'''
        return {'schema':schema,'table':table,'sql':sql,'mapping':mapping,
                'legacy_time_assumed':mapping['time']=='time' and not dtype.startswith('time')}
    return None


def aggregate_sql(source_sql):
    """Pure SELECT/CTEs. Only daily measures and one-minute grid prices leave the server."""
    return '''WITH
raw AS MATERIALIZED ('''+source_sql+'''),
session_trades AS MATERIALIZED (
 SELECT * FROM raw WHERE ts_seconds BETWEEN :open_seconds AND :close_seconds),
positive AS MATERIALIZED (SELECT * FROM session_trades WHERE price>0 AND size>0
 AND price<'Infinity'::double precision AND size<'Infinity'::double precision),
uncorrected AS MATERIALIZED (
 SELECT * FROM positive WHERE trim(correction_raw) IN ('00','0')),
conditioned AS MATERIALIZED (
 SELECT * FROM uncorrected WHERE regexp_replace(coalesce(sale_condition_raw,''),'\\s','','g')=ANY(:conditions)),
venue AS (
 SELECT exchange FROM conditioned WHERE exchange IS NOT NULL AND trim(exchange)<>''
 GROUP BY exchange ORDER BY count(*) DESC,exchange ASC LIMIT 1),
selected AS MATERIALIZED (SELECT c.* FROM conditioned c JOIN venue v USING(exchange)),
clean AS MATERIALIZED (
 SELECT ts_seconds,percentile_cont(0.5) WITHIN GROUP(ORDER BY price) AS price
 FROM selected GROUP BY ts_seconds),
first_tick AS (SELECT ts_seconds,price FROM clean ORDER BY ts_seconds LIMIT 1),
tick_returns AS (SELECT ts_seconds,ln(price/lag(price) OVER(ORDER BY ts_seconds)) AS r FROM clean),
tick_pairs AS (SELECT r,lag(r) OVER(ORDER BY ts_seconds) AS previous FROM tick_returns),
acov AS (SELECT covar_pop(r,previous) AS tick_lag1_autocov FROM tick_pairs),
bins AS (
 SELECT DISTINCT ON (bucket) bucket,price,ts_seconds FROM
 (SELECT ceil((ts_seconds-:open_seconds)/15.0)::integer AS bucket,price,ts_seconds FROM clean) b
 ORDER BY bucket,ts_seconds DESC),
grid_base AS (
 SELECT i.n,b.price AS anchor_price,b.ts_seconds AS anchor_seconds,
 sum(CASE WHEN b.price IS NULL THEN 0 ELSE 1 END) OVER(ORDER BY i.n) AS anchor_group
 FROM generate_series(0,CAST(:m15 AS integer)) i(n) LEFT JOIN bins b ON b.bucket=i.n),
carried AS (
 SELECT n,max(anchor_price) OVER(PARTITION BY anchor_group) AS carried_price,
 max(anchor_seconds) OVER(PARTITION BY anchor_group) AS carried_seconds FROM grid_base),
grid15 AS MATERIALIZED (
 SELECT n,:open_seconds+15*n AS grid_seconds,
 CASE WHEN n=0 THEN coalesce(carried_price,(SELECT price FROM first_tick)) ELSE carried_price END AS price,
 CASE WHEN n=0 THEN coalesce(carried_seconds,(SELECT ts_seconds FROM first_tick)) ELSE carried_seconds END AS last_tick_seconds
 FROM carried),
grid_all AS (
 SELECT g.*,f.frequency_seconds FROM grid15 g
 CROSS JOIN (VALUES(15),(30),(60),(300),(900),(1800)) f(frequency_seconds)
 WHERE mod(15*g.n,f.frequency_seconds)=0),
returns AS (
 SELECT *,ln(price/lag(price) OVER(PARTITION BY frequency_seconds ORDER BY n)) AS r FROM grid_all),
adjacent AS (
 SELECT *,lag(r) OVER(PARTITION BY frequency_seconds ORDER BY n) AS r_previous FROM returns),
ss_returns AS (
 SELECT mod(n,20) AS phase_offset,
 ln(price/lag(price) OVER(PARTITION BY mod(n,20) ORDER BY n)) AS r FROM grid15),
ss_rv AS (SELECT phase_offset,
 CASE WHEN count(r)=floor((:m15-phase_offset)*1.0/20) THEN sum(r*r) END AS rv,
 count(r) AS m FROM ss_returns GROUP BY phase_offset),
ss AS (SELECT CASE WHEN count(rv)=20 THEN avg(rv) END AS rv5_ss,
 min(m) AS rv5_ss_M_min,max(m) AS rv5_ss_M_max,count(*) AS rv5_ss_offsets FROM ss_rv),
counts AS (
 SELECT (SELECT count(*) FROM raw) AS raw_trades,
 (SELECT count(*) FROM session_trades) AS after_session,
 (SELECT count(*) FROM positive) AS after_positive,
 (SELECT count(*) FROM uncorrected) AS after_corrections,
 (SELECT count(*) FROM conditioned) AS after_conditions,
 (SELECT count(*) FROM selected) AS after_venue,
 (SELECT count(*) FROM clean) AS retained_timestamps,
 (SELECT count(*) FROM raw WHERE time_nano_raw<0 OR time_nano_raw>=1000) AS invalid_nano_records),
daily_base AS (
 SELECT :symbol AS symbol,CAST(:day AS date) AS date,frequency_seconds,
 CAST(:session_seconds/60 AS integer) AS session_minutes,CAST(:early_close AS boolean) AS early_close,
 CAST(floor(:session_seconds*1.0/frequency_seconds) AS integer) AS "M_expected",
 count(r) AS "M_observed",
 CAST(floor(:session_seconds*1.0/frequency_seconds) AS integer)-count(r) AS missing_grid,
 CASE WHEN count(r)=floor(:session_seconds*1.0/frequency_seconds) THEN sum(r*r) END AS "RV",
 CASE WHEN count(r)=floor(:session_seconds*1.0/frequency_seconds) THEN count(r)/3.0*sum(power(r,4)) END AS "RQ",
 CASE WHEN count(r)=floor(:session_seconds*1.0/frequency_seconds) AND count(r)>1
 THEN pi()/2*count(r)/(count(r)-1.0)*sum(abs(r)*abs(r_previous)) END AS "BV",
 max(price) FILTER(WHERE n=0) AS first_price,max(price) FILTER(WHERE n=:m15) AS last_price,
 max(grid_seconds-last_tick_seconds) AS max_price_age_seconds,
 coalesce((SELECT ts_seconds>:open_seconds FROM first_tick),FALSE) AS opening_approximation
 FROM adjacent GROUP BY frequency_seconds),
daily AS (
 SELECT d.*,c.*,c.raw_trades-c.after_venue AS removed_trades,
 (SELECT exchange FROM venue) AS selected_exchange,a.tick_lag1_autocov,s.*,
 'decimal_unannualised' AS units,:rule_tag AS rules FROM daily_base d CROSS JOIN counts c CROSS JOIN acov a CROSS JOIN ss s),
bars AS (
 SELECT :symbol AS symbol,CAST(:day AS date) AS date,
 (CAST(:day AS date)+TIME '00:00:00'+make_interval(secs=>grid_seconds)) AS timestamp,
 price,grid_seconds-last_tick_seconds AS price_age_seconds,
 CASE WHEN grid_seconds-last_tick_seconds>60 THEN 1 ELSE 0 END AS stale_over_1min,
 (n=0 AND coalesce((SELECT ts_seconds>:open_seconds FROM first_tick),FALSE)) AS opening_approximation
 FROM grid15 WHERE mod(n,4)=0)
SELECT 'daily' AS record_kind,row_to_json(d)::text AS payload FROM daily d
UNION ALL SELECT 'bar',row_to_json(b)::text FROM bars b'''


def independent_measures(raw_frame, session, conditions):
    """Different implementation: pandas median + numpy searchsorted; never calls SQL."""
    f=raw_frame.copy()
    f=f[(f.ts_seconds>=session['open_seconds'])&(f.ts_seconds<=session['close_seconds'])]
    f=f[(f.price>0)&(f['size']>0)&np.isfinite(f.price)&np.isfinite(f['size'])]
    f=f[f.correction_raw.fillna('').astype(str).str.strip().isin(['00','0'])]
    f=f[f.sale_condition_raw.fillna('').str.replace(r'\s','',regex=True).isin(conditions)]
    f=f[f.exchange.notna()&f.exchange.astype(str).str.strip().ne('')]
    if f.empty:
        raise RuntimeError('No retained trades in independent raw-slice check')
    counts=f.groupby('exchange').size().rename('count').reset_index().sort_values(['count','exchange'],ascending=[False,True])
    venue=str(counts.iloc[0].exchange)
    clean=f[f.exchange.eq(venue)].groupby('ts_seconds').price.median().sort_index()
    seconds=clean.index.to_numpy(float); prices=clean.to_numpy(float)
    out=[]
    for frequency in (15,30,60,300,900,1800):
        grid=np.arange(session['open_seconds'],session['close_seconds']+1,frequency,dtype=float)
        ix=np.searchsorted(seconds,grid,side='right')-1
        values=np.full(len(grid),np.nan); valid=ix>=0; values[valid]=prices[ix[valid]]
        if not valid[0]: values[0]=prices[0]
        r=np.diff(np.log(values)); m=len(grid)-1; observed=int(np.isfinite(r).sum())
        complete=observed==m
        out.append({'frequency_seconds':frequency,'M_expected':m,'M_observed':observed,
                    'selected_exchange':venue,'RV':float(np.dot(r,r)) if complete else None,
                    'RQ':float(m/3*np.sum(r**4)) if complete else None,
                    'BV':float(np.pi/2*m/(m-1)*np.dot(np.abs(r[1:]),np.abs(r[:-1]))) if complete else None})
    return out


def write_records(store, relative, records, source, query_hash, fieldnames=None, metadata=None):
    records=list(records)
    if store.cached(relative,query_hash):
        if metadata:
            store.manifest['files'][relative].update(metadata)
            dump_json(store.manifest_path,store.manifest)
        return
    if fieldnames is None:
        if not records:
            raise ValueError('Specify headers for an empty output')
        fieldnames=list(records[0])
    path=store.path(relative); pending=path.with_name(path.name+'.partial')
    with pending.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fieldnames,extrasaction='raise')
        writer.writeheader(); writer.writerows(records)
    os.replace(pending,path)
    store.record(relative,len(records),source,query_hash,**(metadata or {}))


def cached_daily_paths(split,symbol,day):
    return (f'{split}/taq/daily/{symbol}_{day}.csv',f'{split}/taq/minute/{symbol}_{day}.csv')


def acquire_day(client, schemas, calendar, symbol, day, split):
    guard_date(day)
    if day not in calendar:
        raise ValueError('Requested day is not in the frozen session calendar')
    session=calendar[day]
    params={'day':dt.date.fromisoformat(day),'symbol':symbol,'open_seconds':session['open_seconds'],
            'close_seconds':session['close_seconds'],'session_seconds':session['close_seconds']-session['open_seconds'],
            'm15':(session['close_seconds']-session['open_seconds'])//15,'early_close':session['early_close'],
            'conditions':client.config['accepted_sale_conditions']}
    daily_path,minute_path=cached_daily_paths(split,symbol,day)
    while True:
        source=trade_source(client,schemas,day)
        if source is None:
            client.store.event('missing_trade_source',date=day,symbol=symbol,split=split)
            return None
        sql=aggregate_sql(source['sql'])
        params['rule_tag']=VERSION+'_A07P1_ASSUMED_regular_only'+('_LEGACY_SECONDS_ASSUMED' if source['legacy_time_assumed'] else '')
        query_hash=hashlib.sha256((sql+json.dumps(params,sort_keys=True,default=str)).encode()).hexdigest()
        client.store.save_query(sql,params,source['schema']+'.'+source['table'],query_hash)
        if (client.store.cached(daily_path,query_hash) and client.store.cached(minute_path,query_hash)
            and (split!='training' or 'measurement_findings' in client.store.manifest['files'][daily_path])):
            return daily_path,minute_path
        try:
            frame=client.sql(sql,params)
            break
        except Exception as exc:
            if not is_permission_denied(exc): raise
            # Denied views are not missing days in every later year. Try another
            # eligible source, then continue the calendar with explicit gaps.
            client.deny_trade_source(source,day,exc)
    daily=[]; bars=[]
    for record in frame.itertuples(index=False):
        payload=json.loads(record.payload) if isinstance(record.payload,str) else record.payload
        if record.record_kind=='daily': daily.append(payload)
        elif record.record_kind=='bar': bars.append(payload)
        else: raise RuntimeError('Unrecognized aggregate result type')
    daily.sort(key=lambda r:r['frequency_seconds']); bars.sort(key=lambda r:r['timestamp'])
    if len(daily)!=6 or len(bars)!=params['session_seconds']//60+1:
        raise RuntimeError('Aggregate result shape does not match the frozen calendar')
    # Do not inspect validation values: serialize blind, without previews or measurement summaries.
    measurement_findings=None
    if split=='training':
        measurement_findings=[]
        for r in daily:
            if r['invalid_nano_records']:
                raise RuntimeError('Nanosecond remainder outside mapped range; source mapping must be checked')
            bad=[]
            if r['M_observed']!=r['M_expected']: bad.append('missing_return_intervals')
            for field in ['RV','RQ','BV']:
                value=r[field]
                if value is None or not isinstance(value,(int,float)) or not np.isfinite(value) or value<=0:
                    bad.append('invalid_or_missing_'+field)
            if bad: measurement_findings.append({'frequency_seconds':r['frequency_seconds'],'findings':bad})
        if measurement_findings:
            client.store.event('measurement_findings',date=day,symbol=symbol,split=split,findings=measurement_findings)
    src=source['schema']+'.'+source['table']
    write_records(client.store,daily_path,daily,src,query_hash,
        metadata={'measurement_findings':measurement_findings,'measurement_QC':'training checks' if split=='training' else 'not inspected; blind export'})
    write_records(client.store,minute_path,bars,src,query_hash)
    return daily_path,minute_path


def export_raw_slice(client, schemas, day):
    if day not in client.config['raw_slice_dates']:
        raise ValueError('Raw tick export attempted outside the fixed six dates')
    source=trade_source(client,schemas,day)
    if source is None:
        client.store.event('missing_raw_slice',date=day)
        return None
    sql='SELECT :symbol AS symbol,raw.* FROM ('+source['sql']+') raw ORDER BY ts_seconds,sequence_raw'
    relative=f'training/taq/slices/SPY_{day}.csv.gz'
    client.export(sql,{'symbol':'SPY','day':dt.date.fromisoformat(day)},relative,source['schema']+'.'+source['table'])
    return relative


def check_raw_pilot(client, calendar, raw_path, daily_path):
    rows=client.store.manifest['files'][raw_path]['rows']
    if rows>client.config['independent_check_max_rows']:
        raise RuntimeError('Raw-slice independent check exceeds its bounded memory plan; aggregation stays at pilot stage')
    cols=['ts_seconds','price','size','exchange','sale_condition_raw','correction_raw']
    path=client.store.path(raw_path)
    pd.read_csv(path,usecols=cols,nrows=5,dtype={'correction_raw':'string','sale_condition_raw':'string'})
    frame=pd.read_csv(path,usecols=cols,dtype={'correction_raw':'string','sale_condition_raw':'string'})
    day=Path(raw_path).name.split('_',1)[1].split('.csv')[0]
    expected=independent_measures(frame,calendar[day],client.config['accepted_sale_conditions'])
    with client.store.path(daily_path).open(newline='') as stream:
        actual={int(r['frequency_seconds']):r for r in csv.DictReader(stream)}
    findings=[]
    for e in expected:
        a=actual[e['frequency_seconds']]
        for key in ['M_expected','M_observed']:
            if int(a[key])!=e[key]: findings.append({'frequency':e['frequency_seconds'],'field':key})
        if a['selected_exchange']!=e['selected_exchange']:
            findings.append({'frequency':e['frequency_seconds'],'field':'selected_exchange'})
        for key in ['RV','RQ','BV']:
            if e[key] is None:
                matches=a[key] in ('','None')
            else:
                matches=a[key] not in ('','None') and np.isclose(float(a[key]),e[key],
                    rtol=client.config['independent_relative_tolerance'],
                    atol=client.config['independent_'+key+'_absolute_tolerance'])
            if not matches: findings.append({'frequency':e['frequency_seconds'],'field':key})
    result={'status':'passed_checks' if not findings else 'failed','day':day,'method':'Independent pandas medians and numpy searchsorted; SQL uses CTEs/bins/windows','findings':findings,
            'not_claimed':'This does not resolve SPYRM reference units or certify empirical reconciliation.'}
    dump_json(client.store.path('diagnostics/raw_pilot_check.json'),result)
    if findings: raise RuntimeError('Independent raw-slice calculation disagrees with server aggregates; full TAQ acquisition stopped')
    return result


def ids_cte(idmap):
    values=[]; params={}
    for n,(symbol,permno) in enumerate(idmap.items()):
        values.append(f'(:symbol_{n},:permno_{n})')
        params['symbol_'+str(n)]=symbol; params['permno_'+str(n)]=int(permno)
    return 'WITH ids(symbol,permno) AS (VALUES '+','.join(values)+') ',params


def resolve_ids(client, schemas):
    names=choose_source(client,schemas,'stocknames',['permno','ticker','namedt','nameenddt'],['crsp','crsp_a_stock','crspa','crspm'])
    # Point-in-time anchor is in training; later data never select the panel.
    f=client.sql(f'''SELECT DISTINCT ticker,permno FROM {relation(*names)}
WHERE ticker=ANY(:symbols) AND namedt<=:anchor AND nameenddt>=:anchor''',
        {'symbols':client.config['etfs'],'anchor':dt.date(2016,12,30)})
    idmap={}
    for symbol in client.config['etfs']:
        candidates=f.loc[f.ticker.eq(symbol),'permno'].drop_duplicates().tolist()
        if len(candidates)!=1:
            raise RuntimeError('Ambiguous/missing CRSP security identity for '+symbol+'; refusing an arbitrary match')
        idmap[symbol]=int(candidates[0])
    dump_json(client.store.path('private/security_ids.json'),idmap)
    return names,idmap


def acquire_support(client, schemas, split, start, end, names, idmap, folder='support'):
    start,end=guard_date(start),guard_date(end)
    dsf=choose_source(client,schemas,'dsf',['date','permno','prc','ret','retx','vol','shrout','cfacpr','cfacshr'],['crsp','crsp_a_stock','crspa','crspm'])
    dist=choose_source(client,schemas,'dsedist',['permno','exdt','distcd','divamt','facpr','facshr','dclrdt','rcrddt','paydt'],['crsp','crsp_a_stock','crspa','crspm'])
    ff=choose_source(client,schemas,'factors_daily',['date','mktrf','rf'],['ff','ff_all'])
    cte,params=ids_cte(idmap)
    params.update(start=dt.date.fromisoformat(start),end=dt.date.fromisoformat(end))
    suffix='pilot' if folder=='support_pilot' else ('train' if split=='training' else 'validation')
    sql=cte+f'''SELECT i.symbol,n.permno,n.ticker,n.cusip,n.ncusip,n.comnam,n.shrcd,n.exchcd,
 greatest(n.namedt,:start) AS namedt,least(n.nameenddt,:end) AS nameenddt
FROM {relation(*names)} n JOIN ids i USING(permno)
WHERE n.namedt<=:end AND n.nameenddt>=:start ORDER BY i.symbol,n.namedt'''
    client.export(sql,params,f'{split}/{folder}/crsp_names_{suffix}.csv', '.'.join(names))
    sql=cte+f'''SELECT i.symbol,d.permno,d.date,d.prc,d.ret,d.retx,d.vol,d.shrout,d.cfacpr,d.cfacshr
FROM {relation(*dsf)} d JOIN ids i USING(permno)
WHERE d.date BETWEEN :start AND :end ORDER BY i.symbol,d.date'''
    client.export(sql,params,f'{split}/{folder}/crsp_dsf_etf_{suffix}.csv','.'.join(dsf))
    sql=cte+f'''SELECT i.symbol,d.permno,d.exdt,d.distcd,d.divamt,d.facpr,d.facshr,
 CASE WHEN d.dclrdt<=:end THEN d.dclrdt END AS dclrdt,
 CASE WHEN d.rcrddt<=:end THEN d.rcrddt END AS rcrddt,
 CASE WHEN d.paydt<=:end THEN d.paydt END AS paydt
FROM {relation(*dist)} d JOIN ids i USING(permno)
WHERE d.exdt BETWEEN :start AND :end ORDER BY i.symbol,d.exdt,d.distcd'''
    client.export(sql,params,f'{split}/{folder}/crsp_dist_etf_{suffix}.csv','.'.join(dist))
    client.export(f'SELECT date,mktrf,rf FROM {relation(*ff)} WHERE date BETWEEN :start AND :end ORDER BY date',
        {'start':params['start'],'end':params['end']},f'{split}/{folder}/ff_daily_{suffix}.csv','.'.join(ff))
    return {'names':'.'.join(names),'daily':'.'.join(dsf),'distributions':'.'.join(dist),'ff':'.'.join(ff),
            'FF_units':'vendor_native_unconverted','CRSP_returns_prices':'vendor_native_unconverted'}


def master_projection(columns):
    def pick(options):
        present=[identifier(c)+'::text' for c in options if c in columns]
        return ('coalesce('+','.join(present)+')' if len(present)>1 else present[0]) if present else 'NULL::text'
    root=pick(['sym_root','symbol_root'])
    full_symbol_only=root=='NULL::text' and 'symbol_15' in columns
    if full_symbol_only:
        # Catalog-confirmed 2018/2019 layout: exact unsuffixed ETF symbol only.
        # Do not infer/split arbitrary full stock symbols into root and suffix.
        root='trim('+identifier('symbol_15')+'::text)'
    if root=='NULL::text': return None
    fields={'symbol_root':root,'symbol_suffix':pick(['sym_suffix','symbol_suffix']),
            'cusip':pick(['cusip']),'security_description':pick(['sec_desc']),
            'listed_exchange':pick(['listed_exchange','listed_market'])}
    return fields


def acquire_masters(client, schemas, calendar, split, start, end, symbols=None):
    paths=[]; missing=[]; mappings={}
    for year in range(int(start[:4]),int(end[:4])+1):
        schema='taqm_'+str(year)
        if schema not in schemas:
            missing.append(year); continue
        tables=client.tables(schema)
        # Actual catalog layouts vary by year. Prefer one annual table; otherwise
        # use only master daily tables whose date is in the registered window.
        annual=next((t for t in ('mastm_'+str(year),'mast_'+str(year),'master_'+str(year)) if t in tables),None)
        candidates=[annual] if annual else sorted(t for t in tables if re.fullmatch(r'(mastm?|master)_\d{8}',t) and start<=t[-8:-4]+'-'+t[-4:-2]+'-'+t[-2:]<=end)
        if not candidates:
            missing.append(year); continue
        for table in candidates:
            columns=client.columns(schema,table)
            projection=master_projection(columns)
            if not projection or 'date' not in columns:
                missing.append(year); continue
            mappings[schema+'.'+table]=('symbol_15 exact requested unsuffixed symbol; suffix not inferred'
                if not {'sym_root','symbol_root'}&set(columns) else 'explicit root/suffix columns')
            fields=','.join(expr+' AS '+identifier(alias) for alias,expr in projection.items())
            a=max(start,f'{year}-01-01'); b=min(end,f'{year}-12-31')
            sql=f'SELECT date,{fields} FROM {relation(schema,table)} WHERE date BETWEEN :start AND :end AND '+projection['symbol_root']+'=ANY(:symbols) ORDER BY date,symbol_root,symbol_suffix'
            relative=f'{split}/metadata/{table}.csv.gz'
            client.export(sql,{'start':dt.date.fromisoformat(a),'end':dt.date.fromisoformat(b),'symbols':symbols or client.config['etfs']},relative,schema+'.'+table)
            paths.append(relative)
    return {'files':paths,'missing_years':sorted(set(missing)),'symbol_mapping_by_table':mappings}


def historical_aliases(store, fallback):
    relative='training/support/crsp_names_train.csv'
    if relative not in store.manifest['files']: return list(fallback)
    path=store.path(relative)
    pd.read_csv(path,usecols=['ticker'],nrows=5,dtype='string')
    frame=pd.read_csv(path,usecols=['ticker'],dtype='string')
    return sorted(set(fallback)|set(frame.ticker.dropna().str.strip()))


def construct_cusip_links(store, split, masters):
    """Deterministic identifier join, not the proprietary WRDS CRSP/TAQ link algorithm."""
    suffix='train' if split=='training' else 'validation'
    names_path=store.path(f'{split}/support/crsp_names_{suffix}.csv')
    if not names_path.exists() or not masters['files']:
        return {'status':'not_available','reason':'Names/master inputs missing'}
    columns=['symbol','permno','ncusip','namedt','nameenddt']
    pd.read_csv(names_path,usecols=columns,nrows=5,dtype='string')
    names=pd.read_csv(names_path,usecols=columns,dtype='string').fillna('')
    names['key']=names.ncusip.str.strip().str[:8]
    records=[]
    for relative in masters['files']:
        cols=['date','symbol_root','symbol_suffix','cusip','listed_exchange']
        pd.read_csv(store.path(relative),usecols=cols,nrows=5,dtype='string')
        frame=pd.read_csv(store.path(relative),usecols=cols,dtype='string').fillna('')
        for row in frame.itertuples(index=False):
            key=row.cusip.strip()[:8]
            matches=names[(names.key.eq(key))&(names.namedt<=row.date)&(names.nameenddt>=row.date)] if len(key)==8 else names.iloc[:0]
            unique=matches[['symbol','permno']].drop_duplicates()
            one=len(unique)==1
            records.append({'date':row.date,'symbol_root':row.symbol_root,'symbol_suffix':row.symbol_suffix,
                'cusip':row.cusip,'listed_exchange':row.listed_exchange,
                'canonical_symbol':unique.iloc[0]['symbol'] if one else None,
                'permno':unique.iloc[0]['permno'] if one else None,
                'match_status':'exact_cusip_date_unique' if one else ('ambiguous' if len(unique)>1 else 'unmatched'),
                'method':'Own exact 8-character historical NCUSIP/date join; not official WRDS linking algorithm'})
    signature=hashlib.sha256(json.dumps([(p,store.manifest['files'][p]['sha256']) for p in masters['files']]+[(str(names_path),digest_file(names_path))]).encode()).hexdigest()
    output=f'{split}/metadata/taq_crsp_link_computed_{suffix}.csv'
    write_records(store,output,records,'TAQ masters + CRSP historical names',signature,
        fieldnames=['date','symbol_root','symbol_suffix','cusip','listed_exchange','canonical_symbol','permno','match_status','method'])
    return {'status':'saved','file':output,'official_WRDS_link':False}


def combine_csv(store, relatives, output, source):
    relatives=sorted(set(relatives))
    if not relatives: return None
    signature=hashlib.sha256(json.dumps([(p,store.manifest['files'][p]['sha256']) for p in relatives]).encode()).hexdigest()
    if store.cached(output,signature): return output
    path=store.path(output); pending=path.with_name(path.name+'.partial')
    rows=0; header=None
    with pending.open('w',encoding='utf-8',newline='') as destination:
        writer=csv.writer(destination)
        for relative in relatives:
            file=store.path(relative); opener=gzip.open if str(file).endswith('.gz') else open
            with opener(file,'rt',encoding='utf-8',newline='') as incoming:
                reader=csv.reader(incoming); current=next(reader)
                if header is None: header=current; writer.writerow(header)
                if current!=header: raise RuntimeError('Cannot combine mismatched export schemas')
                for row in reader: writer.writerow(row); rows+=1
    os.replace(pending,path)
    store.record(output,rows,source,signature)
    return output


def minute_to_parquet(store, csv_relative):
    import pyarrow as pa
    import pyarrow.csv as pc
    import pyarrow.parquet as pq
    output=csv_relative.removesuffix('.csv')+'.parquet'
    signature=store.manifest['files'][csv_relative]['sha256']
    if store.cached(output,signature): return output
    path=store.path(output); pending=path.with_name(path.name+'.partial')
    types={'symbol':pa.string(),'date':pa.date32(),'timestamp':pa.timestamp('us'),'price':pa.float64(),
           'price_age_seconds':pa.float64(),'stale_over_1min':pa.int64(),'opening_approximation':pa.bool_()}
    reader=pc.open_csv(store.path(csv_relative),convert_options=pc.ConvertOptions(column_types=types,
        true_values=['True','true','1'],false_values=['False','false','0']))
    writer=None; rows=0
    try:
        for batch in reader:
            if writer is None: writer=pq.ParquetWriter(pending,batch.schema,compression='zstd')
            writer.write_batch(batch); rows+=batch.num_rows
    finally:
        if writer is not None: writer.close()
    if writer is None: raise RuntimeError('No minute export data to convert')
    os.replace(pending,path); store.record(output,rows,'Conversion of '+csv_relative,signature,
        time_zone_note='Naive wall timestamps in America/New_York, same as source session clock')
    return output


def raw_slices_to_parquet(store, paths):
    import pyarrow as pa
    import pyarrow.csv as pc
    import pyarrow.parquet as pq
    paths=sorted(p for p in paths if p)
    if len(paths)!=6: raise RuntimeError('All six fixed raw slices are required before writing the combined slice file')
    output='training/spy_trades_slice.parquet'
    signature=hashlib.sha256(json.dumps([store.manifest['files'][p]['sha256'] for p in paths]).encode()).hexdigest()
    if store.cached(output,signature): return output
    target=store.path(output); pending=target.with_name(target.name+'.partial')
    types={'symbol':pa.string(),'date':pa.date32(),'ts_seconds':pa.float64(),'price':pa.float64(),
           'size':pa.float64(),'exchange':pa.string(),'sale_condition_raw':pa.string(),
           'correction_raw':pa.string(),'sequence_raw':pa.string(),'time_nano_raw':pa.int32()}
    writer=None; rows=0
    try:
        for relative in paths:
            reader=pc.open_csv(store.path(relative),convert_options=pc.ConvertOptions(column_types=types))
            for batch in reader:
                if writer is None: writer=pq.ParquetWriter(pending,batch.schema,compression='zstd')
                writer.write_batch(batch); rows+=batch.num_rows
    finally:
        if writer is not None: writer.close()
    if writer is None: raise RuntimeError('No raw slice records to convert')
    os.replace(pending,target); store.record(output,rows,'Fixed six raw SPY slices',signature)
    return output


def export_volare_if_local(store, config):
    """User-run mechanical export. Never executed on market data by the authoring agent.

    A byte-prefix predicate is applied before CSV parsing; later-period rows are not
    decoded, converted, summarised, placed in frames or displayed. Archive traversal
    is opaque container processing. No network/authentication to VOLARE occurs.
    """
    candidates=[Path(config['volare_archive_path']),Path.cwd()/'realized_variance_stocks.zip']
    archive=next((p for p in candidates if p.is_file()),None)
    if archive is None:
        return {'status':'local_archive_not_visible','action':'WRDS servers cannot see Windows Downloads. Run this same notebook locally, or use the included local VOLARE-only command. No new bulk download is required.'}
    output='training/volare_stocks_train.csv'
    signature=digest_file(archive)
    if store.cached(output,signature): return {'status':'saved','file':output}
    columns=['date','symbol','rv1','rv5','rq1','rq5']; targets={'MSFT','JPM','XOM'}
    pending=store.path(output).with_name('volare_stocks_train.csv.partial'); rows=0
    with zipfile.ZipFile(archive) as package:
        member='realized_variance_stocks.csv'
        if member not in package.namelist(): raise RuntimeError('Unexpected VOLARE archive member name')
        with package.open(member) as incoming,pending.open('w',encoding='utf-8',newline='') as destination:
            header=next(csv.reader([incoming.readline().decode('utf-8-sig')]))
            positions={name:header.index(name) for name in columns}
            if positions['date']!=0 or positions['symbol']!=1:
                raise RuntimeError('VOLARE layout changed; byte-prefix filter cannot be applied safely')
            writer=csv.writer(destination); writer.writerow(columns)
            for opaque_line in incoming:
                if not opaque_line.startswith((b'2015-',b'2016-')): continue
                # Only approved training records are decoded at this point.
                row=next(csv.reader([opaque_line.decode('utf-8')]))
                if row[1] in targets and '2015-01-02'<=row[0]<='2016-12-30':
                    writer.writerow([row[positions[c]] for c in columns]); rows+=1
    if rows==0: raise RuntimeError('No requested VOLARE training records found')
    os.replace(pending,store.path(output)); store.record(output,rows,'User-local VOLARE archive',signature,
        selection='Only 2015/2016 row prefixes decoded; MSFT/JPM/XOM, selected columns')
    return {'status':'saved','file':output}


def clean_error(exc):
    message=str(exc).split('[SQL:')[0].split('[parameters:')[0][:1500]
    message=re.sub(r'postgres(?:ql)?://\S+','[connection URL removed]',message)
    message=re.sub(r'(?i)(password\s*[=:]\s*)\S+',r'\1[removed]',message)
    return {'exception_type':type(exc).__name__,'message':message.strip()}


def run_downloads(config, encoded_calendar, connection_factory=None):
    """Run only when the user executes this function; no browser automation/login by agent."""
    config=dict(DEFAULT_CONFIG,**config); validate_config(config)
    calendar=decode_calendar(encoded_calendar)
    rules={k:v for k,v in config.items() if k not in ['output_directory','profile','volare_archive_path']}
    rule_hash=hashlib.sha256((VERSION+json.dumps(rules,sort_keys=True)+encoded_calendar).encode()).hexdigest()
    store=Store(config['output_directory'],rule_hash)
    report={'engine':VERSION,'acquisition_revision':ACQUISITION_REVISION,'profile':config['profile'],'rule_hash':rule_hash,'stages':{},'gaps':{},
            'boundaries':{'training_end':'2016-12-31','validation_export_only_end':'2019-12-31','later_market_data_requested':False},
            'scientific_status':'Candidate acquisition only. SPYRM RQ/session provenance and empirical R1 remain unresolved. No production/model contest or gate promotion.'}
    def stage(name, action):
        try:
            value=action()
            shown=({'source':'.'.join(value[0]),'resolved_security_count':len(value[1])}
                   if name=='CRSP_security_identity' and value is not None else value)
            report['stages'][name]={'status':'completed','result':shown}
            dump_json(store.path('diagnostics/status.json'),report)
            print(name+': complete')
            return value
        except Exception as exc:
            error=clean_error(exc); report['stages'][name]={'status':'failed',**error}
            store.event('stage_failed',stage=name,**error)
            dump_json(store.path('diagnostics/status.json'),report)
            print(name+': '+error['exception_type']+' — '+error['message'][:250])
            return None
    stage('VOLARE_local_training_export',lambda:export_volare_if_local(store,config))
    db=None; client=None
    try:
        if connection_factory is None:
            import wrds
            connection_factory=wrds.Connection
        print('Connecting to WRDS. Complete your own interactive login and Duo prompt if asked; choose n for .pgpass creation.')
        db=connection_factory()
        client=Client(db,store,config)
        client.sql("SELECT set_config('statement_timeout',:value,false), set_config('DateStyle','ISO, YMD',false), set_config('TimeZone','America/New_York',false)",{'value':str(config['query_timeout_seconds']*1000)})
        backend=client.sql('SELECT pg_backend_pid() AS job_backend_pid, current_setting(\'server_version_num\') AS version')
        if int(backend.iloc[0]['version'])<120000:
            raise RuntimeError('This SELECT-only CTE implementation requires PostgreSQL 12+; no privilege change is needed')
        store.manifest['backend_job_id']=int(backend.iloc[0]['job_backend_pid'])
        schemas=client.schemas()
        taq_schemas=[s for s in schemas if re.fullmatch(r'taqm_(200[7-9]|201[0-9])',s) or s in ('taq','taqmsec') or re.fullmatch(r'taq_?20(0[7-9]|1[0-9])',s)]
        client.preload_trade_columns(taq_schemas)
        inventory={'TAQ_schemas':taq_schemas,'CRSP_schemas':[s for s in schemas if s.startswith('crsp')],
                   'FF_schemas':[s for s in schemas if s in ('ff','ff_all')],'notes':'Catalog identifiers only; no market observations'}
        dump_json(store.path('diagnostics/source_inventory.json'),inventory)

        identity=stage('CRSP_security_identity',lambda:resolve_ids(client,schemas))
        if identity:
            names,idmap=identity
            support_pilot=stage('support_pilot',lambda:acquire_support(client,schemas,'training','2014-01-01','2014-01-31',names,idmap,'support_pilot'))
            if config['profile']=='all' and support_pilot:
                stage('support_training',lambda:acquire_support(client,schemas,'training',config['support_start'],config['training_end'],names,idmap))
                if config['export_validation_blind']:
                    stage('support_validation_blind_export',lambda:acquire_support(client,schemas,'sealed/validation',config['validation_start'],config['validation_end'],names,idmap))

        aliases=historical_aliases(store,config['etfs'])
        masters=stage('TAQ_master_training',lambda:acquire_masters(client,schemas,calendar,'training',config['training_start'],config['training_end'],aliases))
        if masters: stage('TAQ_CRSP_computed_training_link',lambda:construct_cusip_links(store,'training',masters))
        if config['profile']=='all' and config['export_validation_blind']:
            val_masters=stage('TAQ_master_validation_blind_export',lambda:acquire_masters(client,schemas,calendar,'sealed/validation',config['validation_start'],config['validation_end'],aliases))
            if val_masters: stage('TAQ_CRSP_computed_validation_link',lambda:construct_cusip_links(store,'sealed/validation',val_masters))

        raw_paths=[]
        first_raw=stage('raw_early_close_pilot',lambda:export_raw_slice(client,schemas,'2014-11-28'))
        first_daily=stage('aggregate_early_close_pilot',lambda:acquire_day(client,schemas,calendar,'SPY','2014-11-28','training'))
        pilot_check=None
        if first_raw and first_daily:
            raw_paths.append(first_raw)
            pilot_check=stage('independent_raw_slice_check',lambda:check_raw_pilot(client,calendar,first_raw,first_daily[0]))
        if pilot_check:
            def one_month():
                completed=[]
                for day in sorted(d for d in calendar if '2014-01-01'<=d<='2014-01-31'):
                    result=acquire_day(client,schemas,calendar,'SPY',day,'training')
                    if result is None: raise RuntimeError('Pilot-month source missing: '+day)
                    completed.append(result)
                combine_csv(store,[x[0] for x in completed],'training/spy_daily_pilot.csv','Fixed January 2014 pilot')
                minute=combine_csv(store,[x[1] for x in completed],'training/spy_1min_pilot.csv','Fixed January 2014 pilot')
                minute_to_parquet(store,minute)
                return {'status':'saved','days':len(completed),'SPYRM_reconciliation':'not certified; reference RQ units unresolved'}
            month=stage('aggregate_one_month_pilot',one_month)
            for day in config['raw_slice_dates']:
                if day=='2014-11-28': continue
                p=stage('raw_slice_'+day,lambda day=day:export_raw_slice(client,schemas,day))
                if p: raw_paths.append(p)
            stage('raw_slices_Parquet',lambda:raw_slices_to_parquet(store,raw_paths))

            if config['profile']=='all' and month:
                def period(symbol,split,start,end):
                    expected=sorted(d for d in calendar if start<=d<=end)
                    paths=[]; missing=[]; failures=[]
                    for day in expected:
                        value=None
                        try:
                            value=acquire_day(client,schemas,calendar,symbol,day,split)
                            if value: paths.append(value)
                            else: missing.append(day)
                        except Exception as exc:
                            failures.append({'date':day,**clean_error(exc)})
                            # Permissions are handled per source/year in acquire_day.
                            # Repeated non-permission failures still stop a broken query.
                            if len(failures)>=3: break
                        if value and split=='training' and len(paths)%25==0:
                            print(symbol+': '+str(len(paths))+' training session files ready (no market values displayed)')
                    source_complete=len(paths)==len(expected) and not missing and not failures
                    issue_dates=sorted(Path(p[0]).stem.split('_',1)[1] for p in paths
                        if store.manifest['files'][p[0]].get('measurement_findings'))
                    complete=source_complete and not issue_dates
                    suffix='train' if split=='training' else 'validation'
                    tag='' if complete else '_PARTIAL'
                    stem='spy' if symbol=='SPY' else symbol.lower()
                    daily=combine_csv(store,[p[0] for p in paths],f'{split}/{stem}_daily_{suffix}{tag}.csv','Source-bounded TAQ daily aggregates')
                    minute=combine_csv(store,[p[1] for p in paths],f'{split}/{stem}_1min_{suffix}{tag}.csv','Source-bounded TAQ one-minute endpoints')
                    if minute: minute_to_parquet(store,minute)
                    coverage={'complete':complete,'source_coverage_complete':source_complete,
                              'measurement_QC':'training findings reported' if split=='training' else 'not inspected; blind export',
                              'training_measurement_issue_dates':issue_dates,
                              'expected_session_jobs':len(expected),'completed_session_jobs':len(paths),
                              'missing_source_dates':missing,'errors':failures,
                              'unattempted_dates':expected[len(paths)+len(missing)+len(failures):],
                              'daily_file':daily,'minute_csv':minute}
                    dump_json(store.path('diagnostics/'+symbol+'_'+suffix+'_coverage.json'),coverage)
                    report['gaps'][symbol+'_'+suffix]=coverage
                    return {'complete':complete,'partial_filenames_used':not complete}
                stage('SPY_training_all_available',lambda:period('SPY','training',config['training_start'],config['training_end']))
                if config['export_validation_blind']:
                    stage('SPY_validation_blind_export',lambda:period('SPY','sealed/validation',config['validation_start'],config['validation_end']))
                if config['optional_etf_aggregates'] or config['optional_stock_comparison']:
                    report['stages']['optional_expansion']={'status':'not_run','reason':'Expansion awaits empirical SPY reconciliation; unknown reference RQ units cannot be self-certified by this downloader.'}
        else:
            report['stages']['TAQ_full_history']={'status':'not_run','reason':'The independent one-day check must pass before the month/full acquisition. Existing support files are retained.'}
    except Exception as exc:
        report['stages']['connection_or_setup']={'status':'failed',**clean_error(exc)}
        print('WRDS setup stopped: '+type(exc).__name__+'. Redacted details are in diagnostics/status.json.')
    finally:
        if client is not None:
            report['trade_source_access_gaps']=getattr(client,'access_gaps',[])
        if db is not None:
            try: db.close()
            except Exception: pass
    failed=any(s.get('status') in ('failed','not_run') for s in report['stages'].values())
    partial=any(not x.get('complete',False) for x in report['gaps'].values())
    external=[]
    for name,item in report['stages'].items():
        result=item.get('result')
        if isinstance(result,dict) and result.get('status')=='local_archive_not_visible': external.append('Existing VOLARE archive not visible from this kernel')
        if isinstance(result,dict) and result.get('missing_years'): external.append(name+' missing master years: '+','.join(map(str,result['missing_years'])))
    report['external_dependencies']=external
    report['overall_status']='incomplete_access_or_checks' if failed or partial else ('pilot_complete' if config['profile']=='pilot' else 'available_exports_saved')
    if external and report['overall_status']=='available_exports_saved': report['overall_status']='WRDS_exports_saved_external_items_missing'
    report['remaining_scientific_blocks']=['SPYRM RQ/session/source reconciliation','Vendor definitions/rights review','No human ownership is inferred','No held-out analysis or production contest']
    dump_json(store.path('diagnostics/status.json'),report)
    dump_json(store.manifest_path,store.manifest)
    package_outputs(store)
    print('Finished: '+report['overall_status']+'. Completed files are resumable; inspect the diagnostics status, not market previews.')
    return {'status':report['overall_status'],'output_directory':str(store.root),
            'training_zip':str(store.root/'RJN_TRAINING.zip'),'sealed_zip':str(store.root/'RJN_VALIDATION_SEALED.zip'),
            'diagnostics_zip':str(store.root/'RJN_DIAGNOSTICS.zip')}


def package_outputs(store):
    """Explicit output allowlists; never zip cwd/home/notebook/credential files."""
    for filename,prefixes in [('RJN_TRAINING.zip',('training/','private/')),
                              ('RJN_VALIDATION_SEALED.zip',('sealed/validation/',)),
                              ('RJN_DIAGNOSTICS.zip',('diagnostics/',))]:
        destination=store.root/filename
        with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
            if filename!='RJN_DIAGNOSTICS.zip': z.write(store.manifest_path,arcname='acquisition_manifest.json')
            if filename=='RJN_DIAGNOSTICS.zip':
                # Only program/admin diagnostics, never acquisition data files or security ID values.
                for file in (store.root/'diagnostics').iterdir():
                    if file.is_file() and file.suffix=='.json': z.write(file,arcname=file.name)
            else:
                for relative in sorted(store.manifest['files']):
                    if relative.startswith(prefixes): z.write(store.path(relative),arcname=relative)
                private=store.root/'private/security_ids.json'
                if filename=='RJN_TRAINING.zip' and private.exists(): z.write(private,arcname='private/security_ids.json')
                if filename=='RJN_TRAINING.zip':
                    for relative in store.manifest['query_specs']:
                        z.write(store.path(relative),arcname=relative)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calendar',type=Path,help='Frozen calendar JSON payload from the starter bundle')
    parser.add_argument('--config',type=Path)
    parser.add_argument('--volare-only',action='store_true')
    args=parser.parse_args()
    cfg=dict(DEFAULT_CONFIG)
    if args.config: cfg.update(json.loads(args.config.read_text()))
    if os.name=='nt' and cfg['output_directory']==DEFAULT_CONFIG['output_directory']:
        cfg['output_directory']=r'D:\AICorner\WRDS_Private_Downloads\automatic'
    if args.volare_only:
        store=Store(cfg['output_directory']+'_VOLARE',hashlib.sha256((VERSION+'volare_only').encode()).hexdigest())
        print(json.dumps(export_volare_if_local(store,cfg)))
    else:
        if not args.calendar: parser.error('--calendar required; easiest route is the self-contained notebook')
        payload=json.loads(args.calendar.read_text())['encoded_calendar']
        print(json.dumps(run_downloads(cfg,payload)))
