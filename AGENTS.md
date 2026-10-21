# AGENTS.md — Rough or Just Noisy? (autonomous research agent for Martin Valachy)

You run autonomously: pick tasks from `ROADMAP.md`, do them, verify, log, continue. Do not ask permission for anything inside the rules below. Be terse; no narration or flattery. English.

## Autonomy loop
1. Take the first `[ ]` task in ROADMAP.md whose dependencies are done and which is not blocked. Mark `[~]`.
2. Locate what you need (see "Finding things"), do the work, run the task's acceptance check, mark `[x]` with run ID / file path.
3. Append one line to `LOG.md`: `date | task | result | run_id`. Update `checkpoint.json` only for changed fields.
4. Go to 1. Stop only when: ROADMAP has no runnable task; a hard stop below applies to every remaining task; or you have finished 6 tasks (or ~90 min). Then write the handoff (below) and stop.
5. Questions and decisions: never wait. Append to `QUEUE_FOR_MARTIN.md` (question, your default, reversible? y/n). If reversible, proceed on the default and tag outputs ASSUMED. If irreversible or a gate, mark the task `[B]` and move to the next task.
6. You may add tasks to ROADMAP.md only if they serve the current phase's stated goal; everything else goes to `IDEAS_PARKING.md` (one line).

## Hard stops (never self-authorise; mark `[B]`, queue for Martin, continue elsewhere)
- Opening validation data (2017-2019, `data/sealed/`): needs "UNLOCK VALIDATION" from Martin. Final test 2020-2025: needs "UNSEAL". Public release: needs "RELEASE". Never pull or read data dated 2020+.
- WRDS/Bloomberg/any login, credentials, paywalled or access-controlled sources: never log in, never request, store or print credentials; on 401/403 stop that task. Martin runs WRDS queries that you write.
- Changes to scope, panel, windows, horizons, model list, margins or primary endpoints: only via an amendment Martin has approved BEFORE the run or data pull. You may draft amendments as PROPOSED.
- Contacting anyone, posting, purchasing, creating accounts, installing system-wide software, deleting files outside this repo.
- Runs estimated > 10 min or > 4 GB memory: write the pilot-size result first, queue the big run for Martin's approval.

## Finding things (cheap and targeted)
- Locate first: `rg -n -i "keyword" INDEX.md` gives file and line. Then read only that range: `sed -n 120,170p FILE`. Never open INDEX.md whole.
- Not in the index: `rg -n -i "keyword" <dir> --max-count 5 -g "!*.pdf" -g "!.venv" -g "!runs" -g "!results" -g "!tmp"`. Code: `rg -n "def name" src scripts`, then read that function only.
- Rebuild the index (seconds) only after you add files: `python scripts/build_index.py .` (or `.\.venv\Scripts\python.exe scripts/build_index.py .`).
- Facts about Martin, project state, protocol and data live in `CONTEXT_PACK.md`: `rg -n` a keyword there instead of reading it whole. Data stage: `DATA_PLAN_PHASE1.md`.
- Before computing, check whether it already exists: `rg -n "<config or task keyword>" manifests/run_index.json` and `data/derived`. Reuse, do not recompute.
- Never read a file twice in a session; keep notes in your own working summary. Never glob or list `.venv`, `runs/`, `results/`, `tmp/`, `literature/*.pdf`.

## Reading data (sample first, never whole)
- CSV: header + `head -n 5` + `wc -l`. In pandas always `usecols=` and `nrows=` first; compute on needed columns only; print `shape` and a few summary lines, never a dataframe.
- Parquet: read schema/metadata, then selected columns and row groups. DuckDB aggregates are better than loading: `SELECT ... GROUP BY ... LIMIT`.
- JSON: list keys, then the one key you need. Logs and test output: `| tail -n 30`; pytest with `-q --tb=line`.
- Truncate every command output (`| head -40`). Never print large arrays, JSON blobs or manifests.
- Exploration order: one symbol, one month, then widen only after the small result is correct. Server-side aggregation for WRDS pulls (see the data plan); never request raw ticks except the six slice days.
- Papers: open only the page or section you need; record page in the evidence card.

## Working rules
- Batch independent commands in one call. One deliverable at a time. Tests: only those touching changed code during work; the full suite and `scripts/validate_checkpoint.py` once at handoff, only if code changed.
- Protocol (`protocol/PROTOCOL_v1.1.md`, `AMENDMENTS.md`) wins on scientific points. Every number you report has a run ID in `manifests/run_index.json`; only numbers that will be cited go into `manifests/claim_ledger.json`. Label claims VERIFIED / INFERRED / UNVERIFIED.
- Never cite a paper you have not opened. Never write "first/novel/new" in public files without approved wording. Insignificance is not equivalence. Do not clip negative corrected moments. Never tune to held-out data. Mismatches in reconciliation are findings, not bugs to tune away.
- Raw market/vendor data and downloaded papers are never committed. Log SHA-256, source, date, row count in `manifests/data_acquisition.json`.
- Verification, proportional to risk. Tier A (simulators, estimators, RV/RQ computation, forecast loop, evaluation, inference): one independent check before reporting (closed form, published number with preset tolerance, second method, limiting case, or planted-bug test). Report "passed these checks", never "correct". Tier B (plots, formatting, boilerplate): just run it.

## Ownership (asynchronous, never blocks engineering)
After each finished Tier A component, append to `QUEUE_FOR_MARTIN.md` three viva questions (what it computes; what breaks it; predict one modified run). Martin answers in `COMPREHENSION_LOG.md`; you never edit that file. A component is OWNED only after he answers correctly. Public release stays blocked until the core components are OWNED. His central derivations (noisy variogram, OU finite-lag slope, quarticity scaling) are queued for him to do by hand; you check them afterwards.

## Handoff (once, at stop)
`HANDOFF.md`, <= 15 lines: done (run IDs) / verified / failed or open / blocked and why / top 3 items in QUEUE_FOR_MARTIN. Update ROADMAP statuses. Then stop.
