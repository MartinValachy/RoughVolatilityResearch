"""A10 bounded paired-source acquisition, executed on authenticated WRDS host.

Requires engine, sas, calendar, A10_CONFIG and A10_CODE_HASH in notebook globals.
No tick files outside SAS WORK; persist aggregate cases and metadata only.
Instantiation does not pull data. Run day, then month, then full explicitly.
"""
import datetime as dt
import hashlib,json,re,time
from pathlib import Path
import numpy as np
import pandas as pd
import duckdb


class SourceReplication:
    def __init__(self,config,code_hash,engine,sas,calendar):
        self.config=config;self.code_hash=code_hash;self.engine=engine;self.sas=sas;self.calendar=calendar
        signature=hashlib.sha256((code_hash+json.dumps(config,sort_keys=True)+engine.aggregate_sql('audit_source')).encode()).hexdigest()
        self.store=engine.Store('A10_source_replication_v2',signature)
        self.store.path('measurement_template.sql').write_text(engine.aggregate_sql('SELECT * FROM audit_source WHERE date=:day'))

    def allowed(self,day,symbols):
        dt.date.fromisoformat(day)
        if not self.config['start']<=day<=self.config['end'] or day not in self.calendar:
            raise ValueError('Unregistered source-audit day')
        if not symbols or not set(symbols)<=set(self.config['panel']): raise ValueError('Unregistered symbol')

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

    def run(self,phase):
        if phase not in ['day','month','full']: raise ValueError('Unknown bounded phase')
        jobs=[]
        if phase=='day': jobs=[('2014-01-02',['QQQ'])]
        elif phase=='month': jobs=[(d,self.config['panel']) for d in sorted(self.calendar) if d.startswith(self.config['panel_month'])]
        else:
            jobs=[(d,self.config['panel'] if d.startswith(self.config['panel_month']) else [self.config['main_symbol']])
                  for d in sorted(self.calendar) if self.config['start']<=d<=self.config['end']]
        if len(jobs)>500: raise ValueError('Bounded audit job limit exceeded')
        start=time.perf_counter();done=[]
        for day,symbols in jobs:
            try: result=self.acquire(day,symbols)
            except Exception as exc:
                self.engine.dump_json(self.store.path('progress.json'),{'phase':phase,'status':'stopped_on_error','date':day,'completed_dates':len(done),
                    'planned_dates':len(jobs),'error_type':type(exc).__name__,'message':str(exc)[:300]})
                raise
            done.append(result)
            if len(done)%5==0 or len(done)==len(jobs):
                status={'phase':phase,'status':'running' if len(done)<len(jobs) else 'passed_checks','completed_dates':len(done),
                    'planned_dates':len(jobs),'seconds':time.perf_counter()-start,'last_date':day,'code_sha256':self.code_hash}
                self.engine.dump_json(self.store.path('progress.json'),status)
                print(json.dumps(status),flush=True)
        self.engine.dump_json(self.store.path('diagnostics/phase_'+phase+'.json'),{'status':'passed_checks','dates':len(done),
            'seconds':time.perf_counter()-start,'summary':done,'rule_hash':self.store.rule_hash})
        return {'phase':phase,'status':'passed_checks','dates':len(done),'seconds':time.perf_counter()-start}


if all(name in globals() for name in ['A10_CONFIG','A10_CODE_HASH','engine','sas','calendar']):
    A10_AUDIT=SourceReplication(A10_CONFIG,A10_CODE_HASH,engine,sas,calendar)
