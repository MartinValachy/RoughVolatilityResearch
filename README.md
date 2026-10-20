# Rough or Just Noisy?

Independent research on measurement error, apparent roughness, volatility forecasts and risk decisions. This repository contains a **completed preparation/pilot checkpoint**, not a production empirical study or a publication-ready paper.

Start with [STATUS.md](STATUS.md), the [executed pilot report](manuscript/PILOT_REPORT.md), and the [positioning memo](manuscript/POSITIONING_AND_FEASIBILITY.md). The [formula notebook](notebooks/formula_audit.ipynb), [evidence cards](literature/cards/), [novelty matrix](literature/novelty_matrix.csv), [SPY data card](data/DATA_CARD.md), [decisions](DECISIONS.md) and [protocol amendments](protocol/AMENDMENTS.md) record assumptions and limitations. `checkpoint.json` is the exact continuation state.

The user reclassified the original thesis proposal as independent research on 20 October 2026. No supervisor, registration or academic deadline is implied. The supplied v1.0 files remain unchanged under `protocol/inputs/`; UZH rules are retained as reference only. See [AI_USE.md](AI_USE.md) for assistance and review status.

## Local environment and commands

Verified on Windows 11 with Python 3.12.14. Project directory: `D:\AICorner\Rough_or_Just_Noisy`. Commands below use PowerShell. The first block recreates the isolated environment using the bundled interpreter available on this machine. On another machine, substitute its Python 3.12 executable.

```powershell
Set-Location 'D:\AICorner\Rough_or_Just_Noisy'
$researchPython = 'C:\Users\valac\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $researchPython -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.lock.txt
```

The existing `.venv` is already installed. Run the checkpoint check and scientific tests:

```powershell
& '.\.venv\Scripts\python.exe' scripts/validate_checkpoint.py
& '.\.venv\Scripts\python.exe' -m pytest -q
```

Reproduce the bounded experiments (each writes a new run directory and updates its `results/latest_*.json` pointer):

```powershell
& '.\.venv\Scripts\python.exe' scripts/execute_notebook.py
& '.\.venv\Scripts\python.exe' scripts/pilot.py
& '.\.venv\Scripts\python.exe' scripts/efficient_price.py
& '.\.venv\Scripts\python.exe' scripts/covariance_control.py
& '.\.venv\Scripts\python.exe' scripts/baseline_pilot.py
& '.\.venv\Scripts\python.exe' scripts/inference_mock.py
& '.\.venv\Scripts\python.exe' scripts/replicate_patton.py
& '.\.venv\Scripts\python.exe' scripts/audit_mouti.py
& '.\.venv\Scripts\python.exe' scripts/audit_data.py
& '.\.venv\Scripts\python.exe' scripts/report.py
& '.\.venv\Scripts\python.exe' scripts/finalize_checkpoint.py
& '.\.venv\Scripts\python.exe' scripts/polish_markdown.py
& '.\.venv\Scripts\python.exe' scripts/validate_checkpoint.py
```

Synthetic seeds/configurations are fixed; timestamps, runtime and run IDs naturally differ. The pilot is capped at 100 paths per cell and refuses a production setting. No market test-period data are read by these commands. The inference mock intentionally reports unresolved coverage instead of silently certifying it.

## Inputs and acquisition

Downloaded papers, third-party code, the small SPY RDA and row-level data derivatives remain local and are excluded from Git. On a fresh checkout, restore the accessible, hash-pinned inputs before source-dependent table replication or the data audit:

```powershell
& '.\.venv\Scripts\python.exe' scripts/acquire_frozen.py --kind all
```

This verifies existing bytes or restores only the exact recorded versions; it refuses hash changes. It does not attempt blocked sources or create accounts. Public availability can change: failures are logged, while synthetic work can proceed independently. `scripts/acquire.py` and the exploratory acquisition helpers document discovery; the frozen acquisition command is the reproduction interface.

The original Notion backup/proposal were read, never modified. Their URLs are recorded in `manifests/context_sources.json`. VOLARE requires an account; no entitlement was verified. An author-linked official replication archive returned 403 locally. No restrictions were bypassed and no restricted credentials were used.

The local SPY example covers 2014-2019. Development is restricted to 2014-2016; later validation rows are quarantined. The final 2020-2025 test remains unopened and no observations from it were acquired. RQ units, session M, return/overnight conventions and upstream data rights remain unresolved. No empirical noise-calibrated model contest or net trading result is claimed.

## Reading results correctly

- **Illustration:** daily Gaussian log IV and Brownian efficient-price experiments. These are not market identification results.
- **Oracle diagnostic:** known-law covariance matching, Gaussian power bound and projection/exposure comparisons. These are not fitted feasible-model rankings or equivalence tests.
- **Published replication:** Patton 2011 Table 1, 25/27 cells within a tolerance specified before execution; two approximate source entries differ.
- **Secondary preprint audit:** Mouti 2026 Table 2, 35/48 cells within the registered tolerance; unresolved differences retained.
- **Readiness:**15 scientific tests pass. G0/G2/G3 remain partial; G4 has not passed. Do not launch production or open final-test data.

Large reproducible synthetic forecast panels remain local; aggregate tables, figures, run metadata, configuration hashes and a claim ledger are versioned. Source PDFs and market-data rows are not redistributed. No public release license has been selected for our own code at this checkpoint; third-party rights remain with their owners. The repository is private.
