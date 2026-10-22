# Rough or Just Noisy? - undergraduate working paper v1.3

The 35-page paper is rewritten for second-year students. It starts with a reader's guide and glossary, then explains the question, data, calculations and findings in plain language. Worked examples show RV/RQ, the variance update, the investment rule, percentage points and cap masking. Each advanced derivation has a purpose statement; Appendix D is optional for a first reading. The empirical results, all eight figures and nine tables, generated facts and formal derivation equations are preserved. The lecture remains at version 1.2 and was not edited.

## Reading order

Start with the abstract and reader's guide (pages 1-3), then Sections 1-3 for the question, data and calculation steps. Sections 4-6 explain the findings. Sections 7-9 discuss limits, checks and conclusions. Appendices A-C/F retain full audit tables; Appendix D supplies advanced derivations and Appendix E explains reproduction. See REVIEW_GUIDE.md for questions to test your understanding.

## Evidence and limits

The paper combines the A08 known-truth baseline, A10 controlled SPY source comparison, A11 explicitly post-result policy sensitivity and A13 fixed exploratory follow-up. These labels identify research stages, not concepts the reader must already know. The union covers 1,990 distinct fund-days in one historical window. QQQ qualifies the reassuring SPY five-minute result; EFA illustrates cap masking; incomplete TLT comparisons are withheld. This is a reproducible historical case study, not a forecast winner or a trading-profit claim. Source agreement is not true integrated variance; the finite-band statistic is not latent H. Independent human review remains open and AI assistance is disclosed.

## Reproduction

Compile main.tex twice from this folder. Editable content is in main.tex, reader_guide.tex, study.tex, breadth.tex, breadth_appendix.tex and theory.tex. Supplied vector figures and generated facts/tables require no vendor observations for compilation.

From the repository root, run `python scripts/check_undergraduate_paper.py`, `python scripts/check_breadth_paper.py`, `python scripts/check_student_examples.py` and `python scripts/check_paper_derivations.py`. These check supplied aggregate claims and selected mathematical/teaching calculations; they do not recreate the empirical extraction. See VERIFICATION.md for exact run IDs, scope and artifact hashes. Full empirical regeneration requires separately licensed source inputs. Validation 2017-2019 and final 2020+ remain closed; the original longer forecasting contest is deferred.
