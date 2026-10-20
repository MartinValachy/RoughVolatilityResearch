# Status - preparation checkpoint

Updated 2026-10-20T21:14:07.373710+00:00. Workspace: `D:\AICorner\Rough_or_Just_Noisy`. Scope: **independent research intended for eventual publication**. No production study, public publication, registered thesis or supervision is claimed.

## Completed with evidence

- Read all six original specification files and inspected the two Notion source pages; originals unchanged under `protocol/inputs/`.
- Created isolated Python 3.12 environment and frozen dependencies, source/data manifests, decisions, amendments, claim ledger and machine-readable continuation state.
- Acquired 21 local PDFs; 27 source entries (24 original+3 targeted additions), 18 targeted evidence cards, novelty matrix and positioning memo. Author code pinned and not executed.
- Executed formula notebook and 15 scientific tests (0 failures, 0 errors).
- Ran 1400 independent daily latent paths/62 observation cells, 100 continuous-time Brownian price paths, 225000 baseline forecasts, 1000 known-law forecast histories and a bounded Gaussian classification-power experiment.
- Attempted published Patton Table 1 replication (25/27 cells within prespecified tolerance); independently audited Mouti preprint Table 2 (35/48 cells within tolerance), retaining discrepancies.
- Audited 750 public SPY development rows; 745 validation rows quarantined. All 6 missing NYSE sessions are early closes. RQ units and session M unresolved. No 2020-2025 data acquired.

## Material findings

Noise correction targets a finite-band OU slope, not automatically 0.5. A fixed flexible finite OU mixture closely approximates one rough daily Gaussian law; its 1250 point known-law power bound is about 7.68% at exact 5% size. This is an illustrative finite-grid result, not an empirical mechanism conclusion or practical-equivalence finding. Forecast/risk diagnostics remain separate.

## Gates and blockers

| Gate | Status |
|---|---|
| G0 | Partial: novelty not established; closest literature overlap narrowed |
| G1 | Technical pass; independent review open |
| G2 | Partial: RQ units, session M, upstream rights, full estimation history and return alignment unresolved |
| G3 | Partial: rough spot-to-IV mapping and valid inferential H coverage still open |
| G4 | Not passed: mock coverage 0.80 at nominal 0.90 (MCSE 0.073), margins/model fit/execution not frozen |

VOLARE requires a login; no existing entitlement verified. The official author-linked data archive returned 403 locally. Harvard realized-kernel PDF was readable in the web reader but returned 403 for local acquisition. Some Crossref lookups failed; those entries are not treated as authoritative matches. No credentials were entered, messages sent or access controls bypassed.

## Continue exactly here

1. Run `.\.venv\Scripts\python.exe scripts/validate_checkpoint.py`.
2. Read `checkpoint.json`, `protocol/PROTOCOL_v1.1.md` and `manuscript/PILOT_REPORT.md`.
3. Resolve source-supported SPYRM quarticity/session definitions; keep the final test sealed. Extend rough spot-to-IV numerical validation before empirical H interpretation.
4. Implement fair estimated structural fits and calibrate inference before freezing a final contest. Do not interpret bootstrap uncertainty or nonsignificance as equivalence.

Reproduction commands: `README.md`. Numerical claims: `manifests/claim_ledger.json`. Exact runs/configurations: `manifests/run_index.json`. No additional user input is needed to inspect/reproduce this checkpoint; further data access can be incorporated when available.
