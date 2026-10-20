# Research protocol v1.1 - preparation checkpoint

Working title: **Rough or Just Noisy? Measurement Error, Apparent Roughness, and the Decision Value of Volatility Forecasts.**

This is independent research. It is not a registered or supervised thesis. The original v1.0 draft is in `inputs/Thesis_Execution_Plan.md`; `AMENDMENTS.md` resolves changes and ambiguities. v1.1 authorizes the bounded pilot only. `production_allowed=false` remains enforced.

## Questions and estimands

- Identification: distinguish prespecified observation laws at available spacing; report size/power or an explicit inconclusive result. Naive finite-band H is descriptive.
- Prediction: paired QLIKE differences for average future daily variance at 1/5/22 trading days. Positive predictions, identical cutoffs and matured labels are mandatory.
- Decision sensitivity: exposure disagreement and aligned risk tracking; eventual net economic outcomes require complete execution accounting.

The initial numerical study treats daily Gaussian log IV as a reduced-form model. The continuous-time Brownian OU efficient-price construction is separate. We have not validated the mapping from rough log spot variance to daily log IV.

## Pilot locks

Configuration files record the complete bounded grids and independent random-stream keys. The current runs do not choose a primary empirical rough/nonrough pair or tune equivalence margins. Current source versions and exact input hashes are recorded in manifests. The primary empirical dates from the draft remain unchanged; see A04 for fallback coverage limitations.

Keep simple baseline checks separate from known-covariance projection/power diagnostics. All structural families in the future contest must have comparable estimation opportunity, information, noise treatment and history; a fixed flexible persistence control is mandatory. No true parameters are handed to one feasible competitor alone.

## Readiness gates as of this checkpoint

| Gate | Assessment | Evidence / missing work |
|---|---|---|
| G0 positioning | Partial, sufficient for pilot |18 targeted evidence cards and novelty matrix; closest overlaps identified. Publication novelty is not established; inspect remaining gaps and exact journal/supplement versions before a novelty claim. |
| G1 formula implementation | Technical checks passed; independent review open | Executed formula notebook, analytical/numerical tests, source-equation visual checks. Source sign/approximation issues recorded. Human verification remains explicit in AI_USE.md. |
| G2 data | Partial | SPY 750-row development pilot, date/calendar audit, pinned inputs and hashes. RQ units/session M/overnight/return adjustments/upstream licensing unresolved; live VOLARE and official author archive not accessible. |
| G3 simulation | Partial | Exact OU, rough Cauchy covariance, noise stresses, numerical price integration, independent covariance checks and Monte Carlo uncertainty. Continuous-time rough integration, source-faithful inferential H coverage and practical estimated structural forecasts remain open. |
| G4 frozen final contest/report | Not passed | Baseline and inference mocks ran, but 30-series bootstrap coverage was 0.80 at nominal 0.90 (MCSE 0.073); block sensitivities/refitting/long-memory calibration, numerical margins and execution accounting remain open. |

A completed preparation checkpoint does not imply these gates all passed. **Do not launch the production grid or open the final empirical test.** No task automation or recurring monitor was created.

## Next executable work

First resolve SPY RQ provenance and sampling counts from the maintainer/JSS source construction or another lawfully accessible documented archive. Run `python scripts/validate_checkpoint.py` before continuing. Extend Level B to the selected rough spot model with explicit integration and covariance checks; then validate an inferential estimator under the actual observation layer. Freeze estimated-model fitting, numerical equivalence margins and return/execution conventions on development/validation data before any final test.
