# Rough or Just Noisy?

An undergraduate working-paper study of historical trade-source information, realized-volatility measurements and exposure-cap masking. The analysis combines a known-truth synthetic diagnostic with a controlled historical source comparison. It does not claim a new estimator, latent-market roughness identification or a profitable trading strategy.

## Read the study

Read [the paper](paper/main.pdf), its [editable source](paper/main.tex), or the [explained university lecture](presentation/Rough_or_Just_Noisy_Lecture_Explained.pptx). The lecture defines terms before using them and includes worked examples. The paper explains the research question, construction, assumptions, results, mathematical derivations, verification and limitations.

The current empirical case covers398 SPY sessions in2013-2014 and a one-month four-fund panel. The fixed A13 extension is acquired and independently checked: [read its report and six figures](docs/A13/A13_BREADTH_REPORT.md). It covers1,592 paired ETF-days and qualifies the SPY-only practical conclusion. The integrated paper/lecture revision is still in progress; the linked PDF/PPTX remain the clearly labeled pre-A13 draft. The original longer forecasting contest remains deferred.

## Run without licensed data

Use Python3.12 or later. Create a virtual environment, install with `python -m pip install -e ".[test]"`, then run `python -m pytest -q`. The synthetic examples are `python scripts/source_audit_demo.py` and `python scripts/run_study.py --pilot`. The notebook demos also need the optional demo dependencies.

The paper compiles from paper/main.tex and its included generated tables/facts and vector figures. Licensed empirical observations are not needed to compile it. Recreating its empirical findings does require the separately licensed source inputs and matching metadata. Empirical analysis/check scripts are provided, but the input observations and private provenance are excluded.

## Data and authorship

This checkout includes original code, synthetic records, manuscript text and aggregate research figures/tables. It excludes licensed market observations, sealed archives, downloaded research PDFs, credentials and the later private local Git history. The existing remote history is preserved. The separate local research checkpoint has additional private records and must not be pushed wholesale.

Martin Valachy directed the project. Codex implemented and drafted the computational work. Automated independent checks are not independent human peer review. Martin's comprehension/code review remains open. See AI_USE.md and the paper disclosure.

The MIT license covers original software and synthetic artifacts. It does not grant rights to vendor observations or third-party material. See NOTICE.md. Repository access/visibility does not imply journal acceptance or validated investment performance.
