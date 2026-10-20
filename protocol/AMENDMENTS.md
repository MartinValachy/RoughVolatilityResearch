# Protocol amendments

The six original draft files in `protocol/inputs/` are preserved. This file records changes before any final-test evaluation.

## A01 - independent research, 20 October 2026

The user superseded the thesis framing with independent research intended for eventual publication. UZH registration, supervision, ECTS and thesis-specific approval are no longer project gates. The original `thesis/` directory is retained for compatibility; new writing belongs in `manuscript/`. No supervisor agreement, registration or public publication is claimed. The user separately authorized saving progress in the private `MartinValachy/RoughVolatilityResearch` repository.

## A02 - bounded rough covariance implementation

The first rough Gaussian implementation uses the generalized Cauchy covariance in Bennedsen, Lunde & Pakkanen, downloaded author version PDF p 6. It has an explicit positive definite covariance and separates local H from the long-lag tail. It is **not fOU**. H remains in {0.05, 0.10, 0.20, 0.35}, beta=0.5, stationary log dispersion=0.25, half-correlation time=22 days. Brownian OU half-lives remain {5, 22, 126}. This isolates simulator correctness before a continuous-time rough spot-volatility integration experiment.

The daily Level A model defines Gaussian log daily IV directly. It does not assert that log integrated variance inherits the local regularity of log spot variance. Level B currently validates Brownian OU spot variance and efficient-price construction only.

## A03 - pilot grid and calibration

Freeze 100 independent paths per family/sample-size cell, sample lengths 1250 and 5000, noise ratios q/m_X(1) in {0, 0.25, 1, 4}, lag bands 1-5/1-10/1-22. Here **q is the variance of the additive log error**, so its contribution to an iid noisy increment variance is 2q. This resolves an ambiguity in the draft's noise-ratio wording. Latent paths and standard noise draws are shared across paired noise treatments; different cells/replicates use separate SeedSequence streams. Targeted heteroskedastic, AR1-error and latent-correlated-error cells use the half-life 22 OU, ratio 1. No favorable-seed selection.

NLLS at lag 10 is a descriptive implementation of BLP's offset moment form, with explicit bounds and failure/boundary reporting. It is not their bandwidth-averaged estimator, and no fixed-day OU/Cauchy inference theorem is asserted. The frequency Hhat<0.2 is descriptive, not a size-controlled rejection rate.

## A04 - public SPY pilot and sealed periods

VOLARE downloads require an account; none was verified or created. The author-linked Shi-Yu-Zhang data archive was identified but returned 403 locally. Use the small maintainer-distributed `highfrequency::SPYRM` snapshot at commit `eb0e84898ce1c44142726412529bbcf9e296a066` as a development-only fallback. It spans 2014-2019; analyze 2014-2016 and quarantine 2017-2019. Initial schema inspection viewed the first three rows and the last 2019 row; this limited validation peeking is disclosed.

The planned final test **2020-2025 is unchanged and unopened**; no observations from it were acquired. The original 2007-2016 training period is not fully covered by this fallback. No 1250-day empirical rolling contest can be claimed from its 750 development observations. A future date/coverage amendment requires verified metadata before examining model comparisons. Do not silently move the final-test boundary to fit the fallback.

No quarticity rescaling is authorized by visual plausibility alone. The potential factor 1e-8 is a diagnostic hypothesis; empirical q calibration and HARQ fitting remain blocked pending source verification. Missing early-close days are left missing, not filled or treated as ordinary adjacent trading days in lag inference.

## A05 - registered replication targets

Before numerical execution, `configs/replication_patton.json` fixed the published Patton 2011 Table 1 target, all nine loss rows and t 6/t 10/normal columns, with absolute tolerance 0.015. This is a theoretical noisy-proxy-loss replication, not a roughness or empirical forecasting replication. All failures remain reported.

`configs/mouti_table2.json` separately fixed a 48-cell, tolerance 1e-4 numerical audit of a **preprint** finite-lag table. It does not replace the required published-result attempt. No correction to source claims is asserted without independent numerical checks.

## A06 - finite-grid oracle diagnostic

`configs/covariance_control.json` fixes a two-factor control and a ten-rate OU dictionary, nonnegative covariance weights, common Gaussian observation noise q=2/78, and equal stationary dispersion. The dictionary/rates were specified before running this diagnostic; no model-count search was performed. Matching uses known rough covariance moments, so this is an oracle/design experiment. It cannot be included in an estimated feasible-model ranking.

The 1250-point power exercise uses 1000 independent null paths for threshold calibration and separate 100-path samples under each simple DGP. Monte Carlo SEs for the evaluation samples exclude threshold-calibration uncertainty. The accompanying Gaussian KL/Pinsker calculation concerns the two fully specified **daily Gaussian laws**, not every possible rough and nonrough model.

## A07 - baseline/inference mocks

The first feasible baseline pipeline is a synthetic OU log-IV experiment with lastRV, EWMA(0.94), direct log-HAR, 1250-day fitting windows, refits every 22 origins, and 1/5/22-day average future variance labels. It does not use the empirical final test. HAR predictors require 21 pre-window warmup observations, disclosed in run metadata. Forecasts are persisted before attaching evaluation outcomes.

The 30-series stationary-bootstrap mock uses 4999 draws and mean block 44 at nominal 90% coverage. Its observed coverage is not accepted as final calibration; the small Monte Carlo sample and missing 22/66 sensitivity remain unresolved. Numerical equivalence margins for the primary study remain unregistered, so no equivalence claim is allowed.
