# Rough or Just Noisy? - full undergraduate working paper

The reviewed version 1.2 PDF integrates the checked four-fund A13 follow-up. It has 27 pages, eight figures, nine tables and a mathematical derivation appendix. Editable sources include main.tex, theory.tex, breadth.tex and breadth_appendix.tex. The companion university lecture has 49 slides with essential definitions and worked examples. See VERIFICATION.md for the exact review and numerical checks. Independent human review remains open.

## Research question
How does changing historical source time/condition information affect realized measures and a fixed risk input, and how can an exposure cap hide that disagreement?

## Evidence
The paper combines the A08 known-truth baseline, A10 controlled SPY source comparison, A11 explicitly post-result policy sensitivity and A13 fixed exploratory follow-up. The union covers 1,990 distinct fund-days over the same historical calendar. QQQ qualifies the reassuring SPY five-minute result; EFA illustrates strong cap masking. Incomplete TLT comparisons are withheld. The original longer forecast contest remains deferred; no option observations were needed.

## Reproduction
To compile the supplied manuscript, run LaTeX twice on main.tex from this folder; no vendor observations are required. To check the supplied aggregate claims, run `python scripts/check_undergraduate_paper.py`, `python scripts/check_breadth_paper.py` and `python scripts/check_paper_derivations.py` from the repository root. The project also opens in Codex's built-in LaTeX editor. Local compilation used `--disable-installer --interaction=nonstopmode --halt-on-error` without system package installation.

Full empirical regeneration requires separately licensed inputs. The original `prepare_undergraduate_paper.py` also uses the private A10 derivative to regenerate displayed weight paths. `prepare_breadth_paper.py` rebuilds A13 facts/tables from supplied aggregate summaries and checked report figures, with optional `--report-directory` (default docs/A13). Independent checkers use csv/json/math, verify every numerical macro/selector and reject planted changes. A data-free checkout audits the supplied outputs and compiles the paper; it cannot recreate the empirical extraction.

## Claim boundaries
Source agreement is not true integrated variance; finite-band H-tilde is not latent H; weights are inputs, not an economic backtest. A11 is after the original results, not untouched validation. Numerical verification is not independent human peer review. Martin's comprehension/code review remains open and the AI contribution is disclosed in the paper.

## For an undergraduate portfolio
The defensible output is a complete reproducible case-study working paper with a practical source/state/constraint audit, not a claim to journal acceptance or a new estimator. The separate synthetic candidate remains the basis for an eventual authorized data-free release. Restricted observations, private manifests and this repository's historical Git objects are not a public-release package.

## Analytical treatment
The full derivation appendix develops RV/RQ moments and units, q-hat finite-sample interpretation, price versus daily log-proxy noise, OU/finite-band slopes, crossed-source interactions, initialized EWMA persistence, cap masking and paired block resampling. The mathematics explains the empirical design; it does not turn illustrative assumptions into fitted market facts.
