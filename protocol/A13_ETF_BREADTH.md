# A13 - Prespecified training-only breadth extension

Status: FROZEN before new observations are acquired. User explicitly questioned limited acquisition and requested deeper evidence, 22 October 2026. Standing user scope/approval override applies. A10/A11 outputs and the original forecast protocol remain unchanged.

Question: Does the controlled source-information discrepancy extend beyond SPY and the previously inspected January-2014 ETF panel? This is a follow-up exploratory replication in the same historical regime, not untouched chronological validation or a search for significance.

Fixed panel: QQQ, IWM, EFA, TLT. Fixed window: every XNYS session from 2013-01-02 through 2014-07-31, matching A10's mounted common overlap. January 2014 ETF observations already acquired in A10 are reused and visibly labeled, not downloaded again. New acquisition covers the other months. No additional symbols/windows will be chosen based on outcomes.

Constructions, fields, condition/correction rules, venue selection, same-time medians, opening convention, missing-grid handling and six intervals (15,30,60,300,900,1800 seconds) are identical to A10. Restore-B remains diagnostic, not a new production filter. Ordered price/size/venue correspondence is checked before comparison; failures are reported, never repaired with invented joins. The stronger two-day A09 time/correction identity is not silently extended.

Primary descriptive outcome: per-fund incidence of fixed RV/RQ materiality thresholds outside January 2014 and outside the two explicitly known discovery dates 2014-01-02/2014-07-03. Thresholds remain absolute log ratios > log(1.1) for RV and > log(2) for RQ. Every fund, construction and grid is reported, including zero effects and missing denominators. No pooled independent-fund significance claim.

Secondary summaries: full-calendar finite-band slopes at 1-5/1-10/1-22 lags and initialized EWMA inputs with lambda .94, warmup126,target .10,cap1,annual252. Combining the already observed January panel preserves calendar spacing/history; those full-window outcomes are explicitly not unseen-data tests. Report original-policy capped/uncapped gaps and state ratios without choosing a best policy. Retain the A11 setting grid only as a labeled post-result secondary sensitivity if computed.

Uncertainty: retain paired calendar indices, missing/eligible indicators and mean-date-block22 with11/44 sensitivities and3999 draws. Funds share dates and market exposures; do not treat their rows as independent replications. No latent-H interval, equivalence or profitability claim.

Acquisition: separate A13 output directory/signature, one-day pilot 2013-02-01, then February2013 pilot, then the fixed remaining window. Positive bounded per-day source subsets stay on WRDS. Persist daily measures, correspondence/measurement checks, query/source hashes and progress only. Do not overwrite A10 directories, silently enlarge memory limits, retrieve raw ticks to the local machine, or acquire closed periods. Stop and record exact permission/schema/bound failures.

Acceptance: fixed calendar coverage and source/member hashes checked; SQL moments agree with independent construction; full summaries independently recalculated, including planted-error checks. Findings may strengthen, qualify or contradict the current case study. Revise the paper and lecture accordingly; do not label this extension successful merely because the effect looks larger.

Validation2017-2019/final2020+ remain closed. The original 1,250-day forecast contest still requires source/history reconciliation and is not completed by A13. Any public distribution excludes proprietary observations and private history. Existing GitHub visibility is private and must remain unchanged unless separately requested.
