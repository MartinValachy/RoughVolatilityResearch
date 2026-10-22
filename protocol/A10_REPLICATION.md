# A10 — Fixed source-semantics replication and downstream risk-input diagnostic

Frozen 22 October 2026 before the expanded pull. User requested a stronger, practically useful/interesting result beyond the established synthetic artifact. A09 is discovery: two fixed days establish exact trade-record identity but different timestamp/flag representations. Restoring modern category B alone nearly removes the January-2 discrepancy. No market-wide claim or provider-error allegation follows from those two observations.

## Question and fixed sample

Does the same literal regular-trade filter have information-equivalent meaning across legacy and millisecond TAQ, how often does the difference materially change RV/RQ, and how does it affect finite-band H and a fixed volatility-targeting input?

SPY common mounted overlap: all frozen XNYS sessions 2013-01-02 through 2014-07-31. Cross-asset replication: all January-2014 sessions for SPY/QQQ/IWM/EFA/TLT, the pre-existing registered ETF panel. No asset/day selected using unseen outcome measures. Primary new-day incidence excludes the two A09 discovery dates 2014-01-02 and 2014-07-03; report their outcomes separately. Full-window H/state-path diagnostics include them and must be labeled as such.

## Crossed construction

One exact source-day/panel subset per source is processed in SAS WORK and Python RAM on WRDS, then discarded. Raw ticks are not downloaded. Verify source row counts and exact rowwise price/size/venue identity separately per symbol. If identity fails, flag and do not invent joins or silently omit the day. No inference over a shortened or compressed calendar.

Five constructions, all six A07 grids: precise timestamps/modern flags; legacy timestamps/modern flags; precise timestamps/legacy flags; legacy timestamps/legacy flags; legacy timestamps/legacy flags with modern category-B flags restored on B-containing records. The last is an exploratory mechanism diagnostic, not a new production cleaning policy. Category overlap and median/venue choices may create interactions. Frozen session/positive/correction/blank-or-@/dominant-venue/median/previous-tick rules unchanged. All source-day moments checked against independent NumPy construction. A09 baseline corners must agree where already saved.

## Outcomes fixed before expanded acquisition

Primary: SPY new-day incidence of >10% absolute log-ratio RV discrepancy or >2-fold RQ discrepancy, by frequency, with exact denominator and missing-day accounting. Use |log(legacy/modern)| > log(1.1) for RV and >log(2) for RQ; no fitted threshold. Also continuous log-ratio distributions and residual differences after B restoration. Practical warning criterion: material discrepancies on at least 2% of new paired days at a grid, or at least 10 post-warmup origins with >=5 percentage-point weight differences. These are engineering relevance thresholds, not tests of latent H or equivalence.

Secondary: log-RV variogram slopes over fixed calendar lags 1–10 (sensitivity 1–5/1–22), source by source, with endpoint pairs preserved on gaps. They are finite-band descriptive values, not market local H estimates.

Downstream diagnostic: EWMA variance with fixed lambda=0.94, initialized at the first RV and evaluated after 126 observations. No parameter fit. Weight at each origin is min(1,0.10/sqrt(252*EWMA_variance)); weight disagreement, turnover and duration are diagnostics of different risk inputs, not actual strategy returns or net profitability. No overnight/corporate-action accounting claim. Any common-modern-RV QLIKE comparison is explicitly a reference-proxy diagnostic, not true-IV loss. The registered fitted forecast contest and its 1250-day window are unchanged and deferred.

Report SPY/date uncertainty with stationary date-block resampling, primary mean block 22, sensitivities 11/44; synchronize dates across ETF cross-sections, never treat correlated assets as independent replicates. Pilot one QQQ/day and then the fixed January panel before the full overlap. Save source hashes, code/query specs, counts and independent-check status; no pooling of legacy with millisecond history. No validation/final-period observations or public release.

Implementation correction during month pilot: an incomplete 15-second grid is a measurement finding, not grounds for discarding an entire symbol-day. Restore the existing A07 policy: save missing measures with exact expected/observed M, require independent agreement on missingness, preserve the calendar, report per-grid valid/missing denominators and withhold EWMA paths with gaps. Do not fill prices, shorten M or label a missing comparison as agreement. Adapter v2 starts a separate cache; the stopped v1 artifacts remain available. This changes error handling only, not filters, moments, thresholds or study outcomes.
