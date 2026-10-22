# Reproduce version 1

Python 3.12 or later. The core study uses NumPy, SciPy, pandas and Matplotlib. All public demo inputs are synthetic. No WRDS login, network calls at analysis time, local market files or final-period observations are required.

## Install

From a fresh checkout, create an isolated virtual environment with `python -m venv .venv`. Activate it using `.venv\Scripts\Activate.ps1` on Windows or `source .venv/bin/activate` on macOS/Linux, then run:

```sh
python -m pip install -e ".[demo]"
python -m pytest tests/test_science.py tests/test_study.py -q
python scripts/run_study.py --pilot
```

The pilot is a four-path/model execution check, not a replacement for the full results.

## Complete synthetic analysis

```sh
python scripts/run_study.py
python scripts/check_study_refinement.py
python scripts/verify_study_tables.py
python scripts/build_side_project.py
python scripts/build_demo.py --execute
```

The fixed main config is `configs/side_project.json`. Seeds are split by model, path and latent/price/noise stream. Run metadata records config/source hashes, exact covariance controls, elapsed time and run IDs. Tables in `results/side_project/` are synthetic. Path metrics, not daily dependent observations, determine Monte Carlo SEs. Floating-point library differences can change last digits; compare scientific checks with their documented tolerances rather than file hashes across platforms.

The executed demo is `notebooks/side_project_demo.ipynb`. It checks covariance, runs a small fresh simulation and displays the frozen full-run summary. The checked full-run report is `manuscript/SYNTHETIC_STUDY.md`; figures are in `docs/figures/`. New run IDs and timings are expected on reproduction.

## Historical research workspace

The full local repository also retains acquisition code, source audits, earlier exploratory simulations and a larger registered forecast protocol. Those are provenance/archive material, not additional requirements for the synthetic version-1 claim. The old checkpoint validator checks unavailable private immutable inputs and is not the fresh-checkout reproduction interface. The original market forecasting contest remains deferred, not silently replaced by a shorter window. Historical market-data audit scripts may read mixed-period files: they are deliberately absent from this quickstart.

Empirical derivatives and market files stay in the private workspace. The synthetic release-candidate bundle is built from an explicit allowlist, without the historical repository, empirical annex, machine-specific manifests, paper PDFs or vendor records. That bundle can be reproduced separately.
