# Undergraduate working paper

Read main.pdf; compile main.tex with the included theory.tex,references.tex,generated facts/tables and six vector figures. No licensed observations are needed to compile. The PDF is the qualified A08/A10/A11 case-study draft. The running A13 broader-fund extension has no analyzed result in this version; it will produce a separately checked revision.

To audit printed numbers from the included aggregate summary tables: python scripts/check_undergraduate_paper.py. To check selected derivations: python scripts/check_paper_derivations.py. Empirical reconstruction requires separately licensed inputs; scripts/prepare_undergraduate_paper.py additionally expects the checked private A10 ratio file at its documented local path. This repository does not supply those observations. The generated source/figures allow independent compilation without that path.

The complete derivations treat RV/RQ moments/units,q-hat,price versus log-proxy noise,finite-band OU behavior,crossed-source interactions,initialized EWMA,cap masking and paired block resampling. Measurement assumptions are explicit; no latent-H identification,trading edge,priority or independent human review is claimed.
