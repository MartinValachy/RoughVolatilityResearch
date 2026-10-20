# SPY pilot data card

Instrument: SPDR S&P500 ETFTrust (SPY). Source: highfrequency::SPYRM, repository commit `eb0e84898ce1c44142726412529bbcf9e296a066`, package 1.0.2. Original RDA134520 bytes; SHA256`93601d2712c8317d9528491e6c182debca5c060f0504da3a023340c414f6e013`. Official maintainer documentation and JSS article are preserved locally; download URLs/hashes are in `manifests/data_acquisition.json`.

The complete small container spans 2014-01-02 through 2019-12-31. Development pilot:750 rows, 2014-01-02 through 2016-12-30. Later 745 rows are quarantined in `data/sealed/`. No 2020-2025 observations were acquired. Initial schema inspection viewed the first 3 rows and last 2019 row, disclosed in the amendment.

## Definitions and fields

RV1/RV5: unannualized realized variance at 1/5 minute sampling. Decimal-return variance is supported by JSSp 24 multiplyingRVby 10000 for percent-return-squared examples. BPV, medianRV andRK fields are available at the same named frequencies; exact provider bandwidth/boundaries remain unresolved. RQ1/RQ5, medianRQ are quarantined because their raw scale is not verified againstRV. No 15/30 minute observed series is available. No actual per-day countM is supplied.

CLOSE is the last recorded trade price, explicitly not the official closing price. Split/distribution/total-return handling and overnight treatment are unverified. No economic return series is constructed. Dates are exchange dates without intraday timestamps; source availability time is unknown and must not be invented.

## Quality

No duplicate dates; dates sorted. The audit reports all missing/nonpositive values by field. Of 756 expectedNYSEsessions, six are absent:2014-07-03, 2014-11-28, 2014-12-24, 2015-11-27, 2015-12-24, 2016-11-25. All are early closes according to exchange_calendars 4.13.2. Do not infer the exclusion's exact source rationale solely from this pattern. No rows are filled and no unexplained outliers removed.

Daily precomputed data cannot validate price filters, stale quotes, trade conditions or independent recomputation. The separate sampleOneMinuteData example concerns an unnamed stock/market proxy and is not used to validateSPY.

## License and admissible use

The package declaresGPL>=2. The upstream market-data provenance and dataset-specific redistribution terms are not separately documented in the inspected files. Keep raw files and row-level derivatives local. The private repository stores acquisition instructions, hashes and aggregate quality reports. This is a useful public-data pilot with a **partial** data gate, not a fully validated empirical contest sample.

Noise calibration, HARQ and risk returns remain blocked by RQ/session/return-interval definitions. The 750 development observations cannot support the original 1250-day empirical fitting window without a documented future amendment and additional data.
