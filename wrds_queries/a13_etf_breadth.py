# A13 fixed training-only ETF source comparison. No queries run on import.
# Run inside WRDS Jupyter, in RJN_WRDS_DATA beside A10_source_replication_v2.
# Owned A10 measurement/acquisition definitions below are embedded, not imported
# from or executed through an older notebook. No credentials are requested.
from pathlib import Path
import base64,csv,datetime as dt,hashlib,json,os,re,sys,time,zlib
import numpy as np
import pandas as pd

A13_CONFIG = {'version': 'A13-training-breadth-1', 'start': '2013-01-02', 'end': '2014-07-31', 'panel': ['QQQ', 'IWM', 'EFA', 'TLT'], 'already_observed_month': '2014-01', 'pilot_day': '2013-02-01', 'pilot_month': '2013-02', 'discovery_dates': ['2014-01-02', '2014-07-03'], 'frequencies_seconds': [15, 30, 60, 300, 900, 1800], 'RV_material_factor': 1.1, 'RQ_material_factor': 2.0, 'EWMA_lambda': 0.94, 'EWMA_warmup': 126, 'target_annual_volatility': 0.1, 'weight_cap': 1.0, 'annual_sessions': 252, 'bootstrap_draws': 3999, 'date_blocks': [22, 11, 44], 'bootstrap_seed': 20261024, 'production_allowed': False, 'classification': 'Fixed follow-up exploratory breadth study; no latent-H, independent-fund, profitability or untouched-validation claim'}
A13_CALENDAR = json.loads(zlib.decompress(base64.b64decode('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actlK8QWckKSbKDSlutWpInICUmygUpbrluxc6UTE4kttly3IpVdji2SDVTact2KbXadmF6NLV61MrbF45cvW65bsXIrRiTJBiptuW7FzpVOTMEafhgNP1jDD6PhB2v4YTT8YA0/jIYfrOGH0fCDNfwwGn6whh9Gww/W8MNo+MEafhgNP1jDD6PhBwsTwggTgrFFGGwRjC3CYAsyUGnLdSt2rnS2CMYWYbAFGai05boVq+w6W5CBSluuW7Fz5bAFyi3CyC0SfJ+65boVaSJp3PQkg7M04CwZnKUBZ8kwJg2MSXbTk8ZNT7KbnjRuesjspi3Xrdi50uEsGcakgTFkdtOW61akicizm5LNbtpy2QqxRRpsQQYqbbluxcqtftNDBiptuW7FNrtOTMnYIg22IAOVtly2Qjc98kClZAOVtly3IudKHqh0rSU7sBlpDBmotOW6FSm38kClZAOVtly3IudKHqh0X4vSmGakMWSg0pbrVqSyywOVkg1U2nLdip0rHWMaS2OakcaQgUpbrluxyq4TExmotOW6FTtXOjE1FpE0IyIhA5W2XLdim13HGDJQactFq87YohtsQQYqbbluRSq7PFAp2UClLdetSGWXBypda8lm7wZbkIFKW65bkcouD1RKNlBpy3Urdq50YuqMLbrBFmSg0pbrVqSJyAOVkg1U2nLZChGTPFDpWst2oM4WZKDSlutWrLLraQwZqLTluhU7VzqcdYYx3cAYMlBpy3UrUtnlgUrJBipt+X+s/v//r11Lya4YRkJCBiptuW5Fqq08UCnZQKUt163YXtcpZrCEZBgJCRmotOW6Fam28kClZAOVtly3YudKp5jBEpJhJCRkoNKW61aEYuSBSskGKm25bsXOlU4xg4UxwwhjyEClLZetEMXIA5WSDVTacmb1618L1I2X')))
A13_COMPONENT_HASHES = {'original_engine_file_sha256': '1f0adbfdad39df7d53bc7f760bcf9b19eb55da9754e1c4730814ce62a522ad21', 'selected_measurement_definitions_sha256': 'cccede362ea56341f294cc250e582cfa106e56d3dec8be099db02faffc492858', 'original_source_replication_file_sha256': 'ec2666a2f43a745501a76849014c7b6a2b0b8ee8d5b645c6ab74763359e0c369', 'frozen_acquisition_class_sha256': '30888218f5d14dc298f697df2379fda553b2101d23a2dd2093e1961f58b02e0b', 'controller_sha256': 'e0638f036611fc1bcf7cf971611cc14a968f84310805aee0e0662e6c5f1d7a59', 'protocol_file_sha256': '6496aa621ef01ce62a53ab0377406c8ff2f88f63c9747912247d18e330b974cf', 'config_file_sha256': 'c46836e956ec8a6ec459812dd747b4ac9627000222b34fe209b3e8063625a402', 'config_canonical_sha256': 'b3eb40015c40054e9f632ea977ff81df8bfa416a54d01854e4c1117a94dc98e6', 'calendar_canonical_sha256': 'cdf3066d032552ece013a39b4155251462fdf02778911a75d2e07f1782438ffe'}
A13_CODE_HASH = 'e4521a82ba0b03fceec99167999216a80c76146b871680010e4c4c30c02a1288'


VERSION = 'rjn-wrds-download-1.0'


SOURCES = {
    'wrds_python': 'https://github.com/wharton/wrds',
    'nyse_2014': 'https://people.stern.nyu.edu/jhasbrou/Teaching/POST%202015%20Spring/TAQ/Daily_TAQ_Client_Spec_v2%200.pdf',
    'nyse_later': 'https://wrds-www.wharton.upenn.edu/documents/1967/Daily_TAQ_Client_Spec_v4.0.pdf',
    'policy': 'https://wrds-www.wharton.upenn.edu/pages/about/ai-policy-on-chatgpt-and-other-generative-ai-tools/',
}


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


class A10FrozenSourceReplication:
    def source_frame(self,day,symbols,kind):
        self.allowed(day,symbols);stamp=day.replace('-','');sasday=dt.date.fromisoformat(day).strftime('%d%b%Y').upper()
        names=','.join('"'+s+'"' for s in symbols)
        if kind=='legacy':
            directory='/wrds/nyse/sasdata/taqs';table='ct_'+stamp
            where=f'SYMBOL in ({names}) and DATE="{sasday}"d'
            keep='SYMBOL DATE TIME PRICE SIZE CORR COND EX';formats='TIME best32. DATE yymmdd10.'
        else:
            directory='/wrds/nyse/taq_msec'+stamp[:4]+'/m'+stamp[:6];table='ctm_'+stamp
            where=f'SYM_ROOT in ({names}) and SYM_SUFFIX=" " and DATE="{sasday}"d'
            keep='SYM_ROOT SYM_SUFFIX DATE TIME_M PRICE SIZE TR_CORR TR_SCOND EX';formats='TIME_M best32. DATE yymmdd10.'
        source=Path(directory)/(table+'.sas7bdat')
        stat=source.stat();frozen={'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}
        snapshots=self.store.manifest.setdefault('source_file_metadata',{})
        if str(source) in snapshots and snapshots[str(source)]!=frozen: raise ValueError('Provider source metadata changed since first acquisition')
        snapshots[str(source)]=frozen
        program=f'''libname rjnaudit "{directory}" access=readonly;
data work.rjn_audit;
 set rjnaudit.{table}(where=({where}) keep={keep});
 format {formats};
run;
proc sql; create table work.rjn_audit_count as select count(*) as n from work.rjn_audit; quit;'''
        qh=hashlib.sha256((program+self.store.rule_hash).encode()).hexdigest()
        self.store.save_query(program,{'day':day,'symbols':symbols,'kind':kind},str(source),qh)
        log=self.sas.submit(program,results='TEXT').get('LOG','')
        if re.search(r'(?m)^\s*ERROR(?:\s+\d+-\d+)?:',log):
            self.store.path('diagnostics/error_'+day+'_'+kind+'.log').write_text(log)
            raise RuntimeError('SAS source read failed')
        n=int(self.sas.sasdata2dataframe('rjn_audit_count',libref='work',method='MEMORY').iloc[0,0])
        if not 0<n<=2500000: raise ValueError('Source-day subset outside fixed memory bound')
        raw=self.sas.sasdata2dataframe('rjn_audit',libref='work',method='MEMORY');raw.columns=raw.columns.str.lower()
        if len(raw)!=n or not pd.to_datetime(raw.date).dt.date.eq(dt.date.fromisoformat(day)).all(): raise ValueError('Source subset date/count mismatch')
        if kind=='legacy':
            symbol=raw.symbol.astype('string').str.strip();seconds=pd.to_numeric(raw.time)
            corr=pd.to_numeric(raw['corr'],errors='coerce').map(lambda v:str(int(v)) if pd.notna(v) and v==int(v) else '')
            condition=raw.cond
        else:
            symbol=raw.sym_root.astype('string').str.strip();seconds=pd.to_numeric(raw.time_m)
            if not raw.sym_suffix.fillna('').str.strip().eq('').all(): raise ValueError('Suffix escaped filter')
            corr=raw.tr_corr.astype('string').fillna('').str.strip();condition=raw.tr_scond
        if not symbol.isin(symbols).all(): raise ValueError('Symbol escaped filter')
        result=pd.DataFrame({'symbol':symbol.to_numpy(),'date':dt.date.fromisoformat(day),
            'ts_seconds':seconds.to_numpy(float),'price':pd.to_numeric(raw.price).to_numpy(float),
            'size':pd.to_numeric(raw['size']).to_numpy(float),'exchange':raw.ex.astype('string').fillna('').str.strip().to_numpy(),
            'sale_condition_raw':condition.astype('string').fillna('').to_numpy(),'correction_raw':corr.to_numpy(),
            'sequence_raw':None,'time_nano_raw':None})
        digest=hashlib.sha256(pd.util.hash_pandas_object(result,index=False).to_numpy().tobytes()).hexdigest()
        return result,{'source':str(source),'source_file_metadata':frozen,'subset_sha256':digest,'rows':n}

    def compute(self,frame,day,symbol,case):
        session=self.calendar[day];seconds=session['close_seconds']-session['open_seconds']
        source='SELECT date,ts_seconds,price,size,exchange,sale_condition_raw,correction_raw,sequence_raw,time_nano_raw FROM audit_source WHERE date=:day'
        sql=self.engine.aggregate_sql(source)
        params={'day':dt.date.fromisoformat(day),'symbol':symbol,'open_seconds':session['open_seconds'],
            'close_seconds':session['close_seconds'],'session_seconds':seconds,'m15':seconds//15,
            'early_close':session['early_close'],'conditions':['','@'],'rule_tag':'A10_diagnostic_'+case}
        sql=re.sub(r'(?<!:):([A-Za-z_][A-Za-z_0-9]*)',lambda m:'$'+m[1],sql)
        sql=sql.replace('make_interval(secs=>grid_seconds)',"grid_seconds * INTERVAL '1 second'")
        with duckdb.connect() as con:
            con.execute("SET memory_limit='1GB'");con.execute('SET threads=2');con.register('audit_source',frame)
            out=con.execute(sql,params).fetchdf()
        daily=sorted([json.loads(p) for p in out.loc[out.record_kind.eq('daily'),'payload']],key=lambda r:r['frequency_seconds'])
        independent=self.engine.independent_measures(frame,session,['','@'])
        if len(daily)!=6 or len(independent)!=6: raise ValueError('Frequency grid incomplete')
        for a,b in zip(daily,independent):
            for field in ['frequency_seconds','M_expected','M_observed','selected_exchange']:
                if a[field]!=b[field]: raise ValueError('Independent structural check failed: '+field)
            for field in ['RV','RQ','BV']:
                if b[field] is None:
                    if a[field] is not None: raise ValueError('Missing-grid moment was not preserved')
                    continue
                if a[field] is None or a[field]<=0 or not np.isclose(a[field],b[field],rtol=1e-7,atol={'RV':1e-12,'RQ':1e-16,'BV':1e-12}[field]):
                    raise ValueError('Independent moment check failed: '+field)
            a['case']=case
        return daily

    def acquire(self,day,symbols):
        self.allowed(day,symbols)
        todo=[]
        for symbol in symbols:
            rel='paired/'+symbol+'_'+day+'.csv';sig=hashlib.sha256((self.store.rule_hash+symbol+day).encode()).hexdigest()
            if not self.store.cached(rel,sig): todo.append(symbol)
        if not todo: return {'date':day,'status':'cached','symbols':symbols}
        started=time.perf_counter();legacy,lmeta=self.source_frame(day,todo,'legacy');modern,mmeta=self.source_frame(day,todo,'millisecond')
        alignments=[]
        for symbol in todo:
            old=legacy[legacy.symbol.eq(symbol)].reset_index(drop=True);new=modern[modern.symbol.eq(symbol)].reset_index(drop=True)
            aligned=len(old)>0 and len(old)==len(new) and all((old[c].to_numpy()==new[c].to_numpy()).all() for c in ['price','size','exchange'])
            if not aligned:
                self.engine.dump_json(self.store.path('diagnostics/alignment_'+symbol+'_'+day+'.json'),{'legacy_rows':len(old),'modern_rows':len(new),'aligned':False})
                raise ValueError('Exact trade identity failed: '+symbol+' '+day)
            rows=[]
            for times in ['millisecond','legacy']:
                for flags in ['millisecond','legacy']:
                    t=new if times=='millisecond' else old;c=new if flags=='millisecond' else old
                    f=new.copy();f['ts_seconds']=t.ts_seconds.to_numpy();f['sale_condition_raw']=c.sale_condition_raw.to_numpy();f['correction_raw']=c.correction_raw.to_numpy()
                    rows.extend(self.compute(f,day,symbol,times+'_time__'+flags+'_flags'))
            f=old.copy();mask=new.sale_condition_raw.astype('string').fillna('').str.contains('B',regex=False).to_numpy()
            replacement=f.sale_condition_raw.to_numpy(copy=True);replacement[mask]=new.sale_condition_raw.to_numpy()[mask]
            f.loc[:,'sale_condition_raw']=replacement
            rows.extend(self.compute(f,day,symbol,'legacy_restore_modern_category_B'))
            if len(rows)!=30: raise ValueError('Case grid incomplete')
            rel='paired/'+symbol+'_'+day+'.csv';sig=hashlib.sha256((self.store.rule_hash+symbol+day).encode()).hexdigest()
            findings=[{'case':r['case'],'frequency_seconds':r['frequency_seconds'],'M_expected':r['M_expected'],'M_observed':r['M_observed']}
                      for r in rows if r['M_observed']!=r['M_expected']]
            self.engine.write_records(self.store,rel,rows,lmeta['source']+' || '+mmeta['source'],sig,
                metadata={'independent_check_passed':True,'exact_record_alignment':True,'measurement_findings':findings,
                          'legacy_source':lmeta,'millisecond_source':mmeta})
            alignments.append({'symbol':symbol,'source_rows':len(old),'timestamp_max_difference':float(np.max(np.abs(old.ts_seconds-new.ts_seconds))),
                'category_B_records_full_day':int(mask.sum()),'independent_checks_passed':True,'measurement_findings':findings})
        self.sas.submit('proc datasets lib=work nolist; delete rjn_audit rjn_audit_count; quit;',results='TEXT')
        result={'date':day,'status':'saved','symbols':todo,'checks':alignments,'seconds':time.perf_counter()-started}
        self.engine.dump_json(self.store.path('diagnostics/day_'+day+'.json'),result)
        return result


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


if __name__ == '__main__':
    A13_RESULT = run_a13_notebook()
