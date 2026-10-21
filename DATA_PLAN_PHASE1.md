# DATA_PLAN_PHASE1.md — read only during the data stage (S3)

First results (milestone R), training data only: R1 own SPY RV/RQ reconciled with SPYRM (closes G2); R2 descriptive naive finite-band H and q-hat at 1/5/15/30-min, explicit lag bands, no latent-H claims; R3 baselines M0-M3, paired QLIKE at h=1/5/22.
Split at download: training (<= 2016-12-31) in `data/raw/wrds/`; validation (2017-2019) straight into `data/sealed/`, unopened. Nothing dated 2020+ is pulled, not even for summary statistics.

| Step | Task | Output |
|---|---|---|
| 0 | Draft amendment A07 (panel, windows, split rule, fields, reconciliation tolerances, units, session count M, overnight rule, BNHLS 2009 trade filters); Martin approves before any pull | A07 text |
| 1 | Martin checks WRDS entitlement: TAQ millisecond, CRSP daily, Fama-French; table names, first dates, any intraday-indicator product | ENTITLEMENT_NOTES.md |
| 2 | Metadata for SPY, QQQ, IWM, EFA, TLT: TAQ master, CRSP names (ticker, CUSIP, permno, ticker changes) | symbol_history.csv, crsp_names.csv |
| 3 | CRSP daily (prc, ret, retx, vol, shrout, cfacpr, cfacshr) 2006-12-29..2019-12-31, distributions, Fama-French daily (mkt-rf, rf) | crsp_dsf_etf.csv, crsp_dist_etf.csv, ff_daily.csv |
| 4 | Raw SPY trades, 6 training days: 2014-11-28, 2015-12-24 (early closes), 2015-08-24, 2016-01-20, 2016-06-24, one ordinary day. Trade fields only, no NBBO ticks | spy_trades_slice.parquet |
| 5 | SPY aggregated server-side, regular session, 2007-01-03..2019-12-31: daily panel (early-close flag, grid counts, RV/RQ/bipower at 15s,30s,1m,5m,15m,30m, subsampled 5-min RV, tick lag-1 autocovariance, first/last price, trades removed) + 1-min bars. Test on Step 4 days and one month, compare with SPYRM and a hand calculation, then full run | spy_daily_train.csv, spy_1min_train.parquet (+ sealed validation parts) |
| 6 | Optional: same job for MSFT, JPM, XOM, 2016-01-04..2016-06-30, compare with VOLARE rv1, rv5, rq1, rq5 | 3 small CSVs |
| 7 | Only after Step 5 reconciles: QQQ, IWM, EFA, TLT | 4 daily CSVs |
| 8 | After each pull: SHA-256, WRDS table/job ID, date, row count in manifests/data_acquisition.json; confirm .gitignore | manifest entries |

Not in Phase 1: 2020+ data, NBBO ticks, OptionMetrics, VIX, Bloomberg, other ETFs, validation analysis. Mismatches in reconciliation are findings, never tuned away. Early closes have fewer grid points; do not treat them as ordinary days.
