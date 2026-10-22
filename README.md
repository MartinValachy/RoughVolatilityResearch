# Rough or Just Noisy?

An undergraduate working-paper study of historical trade-source information, realized-volatility measurements and exposure-cap masking. The analysis combines a known-truth synthetic diagnostic with a controlled historical source comparison. It does not claim a new estimator, latent-market roughness identification or a profitable trading strategy.

## Read the study

Read [the integrated version 1.2 paper](paper/main.pdf), its [editable source](paper/main.tex), or the [university lecture](presentation/Rough_or_Just_Noisy_Lecture_v1_2.pptx). The 27-page paper explains the research question, construction, assumptions, results, mathematical derivations, verification and limitations. The 49-slide lecture defines terms before using them and includes worked examples, with ten editable charts and ten editable tables.

The study covers 398 sessions in 2013-2014 for SPY, QQQ, IWM, EFA and TLT: 1,990 distinct fund-days. The fixed exploratory follow-up qualifies the SPY result: the original five-minute rule has 50/272 QQQ origins with a source-dependent position gap of at least five percentage points, against zero for SPY. EFA illustrates cap masking; incomplete TLT histories are withheld. See the [full follow-up report and six figures](docs/A13/A13_BREADTH_REPORT.md) and [verification record](paper/VERIFICATION.md). These are historical risk-input comparisons. No trading returns or untouched-regime validation are claimed. The original longer forecasting contest remains deferred.

## Run without licensed data

Use Python3.12 or later. Create a virtual environment, install with `python -m pip install -e ".[test]"`, then run `python -m pytest -q`. The synthetic examples are `python scripts/source_audit_demo.py` and `python scripts/run_study.py --pilot`. The notebook demos also need the optional demo dependencies.

The paper compiles from paper/main.tex and its included generated tables/facts and vector figures. To audit its supplied aggregate claims, run `python scripts/check_undergraduate_paper.py`, `python scripts/check_breadth_paper.py` and `python scripts/check_paper_derivations.py`. The slide audit is `python scripts/check_lecture_presentation.py --presentation presentation/Rough_or_Just_Noisy_Lecture_v1_2.pptx`. Licensed observations are unnecessary for compilation and these supplied-output checks. Recreating the empirical findings requires separately licensed source inputs; those observations and private provenance are excluded. Lecture authoring targets ArtifactSession/Artifact Tool; the exported PPTX is independently editable and its content checker uses the Python standard library.

## Data and authorship

This checkout includes original code, synthetic records, manuscript text and aggregate research figures/tables. It excludes licensed market observations, sealed archives, downloaded research PDFs, credentials and the later private local Git history. The existing remote history is preserved. The separate local research checkpoint has additional private records and must not be pushed wholesale.

Martin Valachy directed the project. Codex implemented and drafted the computational work. Automated independent checks are not independent human peer review. Martin's comprehension/code review remains open. See AI_USE.md and the paper disclosure.

The MIT license covers original software and synthetic artifacts. It does not grant rights to vendor observations or third-party material. See NOTICE.md. Repository access/visibility does not imply journal acceptance or validated investment performance.
