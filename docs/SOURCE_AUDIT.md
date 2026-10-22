# Daily source-compatibility audit

`roughnoisy.compatibility.compare_daily(reference, candidate)` compares already-aggregated daily measurements. It makes no network requests and requires no account. Pass two pandas DataFrames; neither is mutated.

| Column | Meaning |
|---|---|
| date | Same documented session identifier/type in both frames |
| symbol | Same security identifier and share class |
| frequency_seconds | Same sampling grid, origin and endpoint convention |
| RV | Sum of squared within-session log returns in documented units |
| RQ | Documented quarticity convention; for the standard convention, M/3 times the sum of fourth powers |
| M_expected | Positive integer number of expected within-session returns |
| M_observed | Actual integer number of returns, preserving incomplete grids |

Keys `(date, symbol, frequency_seconds)` must be unique and nonmissing. Calendar, security mapping, corporate actions, time zones and units are the caller's responsibility. Compare calendar-appropriate M: a shortened session must not silently use a full-session count. The tool can detect disagreement between counts; it cannot establish their calendar correctness if both inputs share a mistake.

The result is an outer join. Missing observations remain findings. Nonpositive/nonfinite moments are invalid; missing grids never count as non-material comparisons. RV and RQ have separate validity flags and nullable material-warning fields. Status prioritizes missing rows, invalid counts, differing expected counts, incomplete grids, invalid moments and material differences.

With defaults, RV warns when `abs(log(candidate/reference)) > log(1.1)`, and RQ when it exceeds `log(2)`. These are configurable engineering materiality settings, not significance tests or equivalence margins. Ratios slightly inside a threshold can still be unacceptable for a particular downstream use.

If log returns change from decimal to percent units, RV scales by 100² and standard RQ by 100⁴. A ratio warning does not diagnose that cause automatically. Verify definitions and provenance before attempting any correction. Missing M or inconsistent RQ conventions cannot be fixed by a guessed constant.

Run `python scripts/source_audit_demo.py`: synthetic unit, session, missing-day, incomplete-grid and large-measurement findings are planted and checked. The executed notebook shows the same workflow. No real security prices or observations are required.

For real inputs, investigate source documentation and controlled constructions. Timestamp/condition/venue interactions can be nonlinear. Neither source is necessarily ground truth. A successful audit is evidence of the checks performed, not permission to pool sources or evidence of better trading performance.
