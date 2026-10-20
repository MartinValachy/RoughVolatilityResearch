from pathlib import Path
import json,hashlib,datetime,sys
R=Path(__file__).resolve().parents[1]
import pyreadr,numpy as np,pandas as pd,exchange_calendars as xc
def main():
 raw=R/'data/raw/SPYRM.rda';df=pyreadr.read_r(str(raw))['SPYRM'];df['date']=pd.to_datetime(df.DT)
 # Final test starts 2020; reject containers that overlap it in this pilot.
 if (df.date>=pd.Timestamp('2020-01-01')).any():raise ValueError('Raw container overlaps sealed final period; refusing pilot analysis')
 pilot=df.loc[df.date<=pd.Timestamp('2016-12-31')].copy();validation=df.loc[df.date>pd.Timestamp('2016-12-31')].copy()
 sealed=R/'data/sealed/SPY_validation_2017_2019.parquet';sealed_bytes=validation.to_parquet(index=False)
 if sealed.exists():
  if sealed.read_bytes()!=sealed_bytes:raise ValueError('Sealed validation bytes differ; refusing overwrite')
 else:sealed.write_bytes(sealed_bytes)
 pilot.to_csv(R/'data/derived/SPY_pilot_2014_2016.csv',index=False)
 cal=xc.get_calendar('XNYS',start='2014-01-01',end='2016-12-31');expected=cal.sessions_in_range(pilot.date.min(),pilot.date.max()).tz_localize(None)
 seen=pd.DatetimeIndex(pilot.date);missing=expected.difference(seen);off=seen.difference(expected)
 nums=pilot.select_dtypes(include='number')
 diagnostic={}
 for freq in [1,5]:
  ratio=pilot[f'RQ{freq}']/pilot[f'RV{freq}']**2
  diagnostic[str(freq)]={'median_raw_RQ_over_RV_squared':float(ratio.median()),'median_if_RQ_divided_by_1e8':float((ratio/1e8).median()),'status':'unit mismatch flagged; 1e-8 is a candidate conversion only, not applied; actual M unavailable'}
 report={'dataset':'highfrequency::SPYRM','instrument':'SPY ETF','provider_snapshot_commit':json.loads((R/'manifests/data_acquisition.json').read_text())[0]['commit'],'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'raw_rows':len(df),'raw_start':str(df.date.min().date()),'raw_end':str(df.date.max().date()),'pilot_rows':len(pilot),'pilot_start':str(pilot.date.min().date()),'pilot_end':str(pilot.date.max().date()),'sealed_validation_rows':len(validation),'final_test_rows_acquired':0,'date_duplicates':int(pilot.date.duplicated().sum()),'rows_sorted':bool(pilot.date.is_monotonic_increasing),'missing_cells':{k:int(v) for k,v in pilot.isna().sum().items()},'nonpositive_numeric_counts':{k:int(v) for k,v in (nums<=0).sum().items()},'calendar':'XNYS via exchange_calendars '+xc.__version__,'calendar_expected_sessions':len(expected),'calendar_missing_sessions':[str(d.date()) for d in missing],'off_calendar_dates':[str(d.date()) for d in off],'frequencies_minutes':[1,5],'fields':list(df.columns),'annualization':'RV fields used as unannualized decimal-return variance, supported by JSS p24 code multiplying RV by10000; dataset RQ units unresolved','quarticity_scaling_diagnostic':diagnostic,'session_and_time_zone':'US SPY date only; exact source session boundaries, early-close M and construction history unresolved','overnight':'Not documented; no return-interval or overnight trading claims permitted','raw_price_validation':'No matching same-asset/day raw prices supplied. sampleOneMinuteData is a different unnamed stock/market example, not a SPY replication input.','close_warning':'Maintainer explicitly says CLOSE is last recorded price, not official closing price; corporate-action/total-return treatment unresolved','license':'GPL>=2 for package; data-specific upstream rights not separately established. Keep raw and row-level derived data local.','prior_peeking':'Initial schema inspection viewed first3rows and last row(2019-12-31); all statistical audit and pilot modeling restricted to <=2016. No2020-2025 data present.','gate':'Partial data gate: useful frequency/positivity/calendar pilot; not a validated noise-calibrated empirical contest'}
 (R/'results/data_quality.json').write_text(json.dumps(report,indent=2))
 early=cal.early_closes.tz_localize(None)
 report['missing_sessions_that_are_early_closes']=[str(d.date()) for d in missing.intersection(early)]
 report['run_id']=datetime.datetime.now(datetime.timezone.utc).strftime('data_audit_%Y%m%dT%H%M%SZ')
 report['code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 (R/'results/data_quality.json').write_text(json.dumps(report,indent=2))
 run=R/'runs'/report['run_id'];run.mkdir();(run/'metadata.json').write_text(json.dumps(report,indent=2))
 pd.DataFrame([{'date':str(d.date()),'reason':'missing_expected_XNYS_session','action':'leave_missing_no_imputation'} for d in missing],columns=['date','reason','action']).to_csv(R/'results/data_exclusion_log.csv',index=False)
 mapping=[]
 for name in ['RV1','RV5','BPV1','BPV5','RK1','RK5','RQ1','RQ5','CLOSE']:
  mapping.append({'source_field':name,'role':'quarticity_quarantined' if name.startswith('RQ') else 'return_alignment_unresolved' if name=='CLOSE' else 'pilot_realized_measure','units':'unresolved' if name.startswith('RQ') else 'price' if name=='CLOSE' else 'squared_decimal_returns','sampling_minutes':None if name=='CLOSE' else int(name[-1]),'source':'SPYRM.Rd; JSS article; rQuar.Rd for formula only'})
 (R/'manifests/field_mapping.json').write_text(json.dumps(mapping,indent=2))
 print(json.dumps({k:report[k] for k in ['pilot_rows','pilot_start','pilot_end','date_duplicates','calendar_expected_sessions','calendar_missing_sessions','quarticity_scaling_diagnostic','final_test_rows_acquired']},indent=2))
if __name__=='__main__':main()
