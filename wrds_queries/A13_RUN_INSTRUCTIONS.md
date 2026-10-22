# A13: what to do

1. In WRDS Jupyter, open `rough_noisy_setup`, then `RJN_WRDS_DATA`. You should see the folder `A10_source_replication_v2` from the previous successful download. Do not open any sealed folder.
2. Upload `RJN_A13_ETF_BREADTH.ipynb` into that same `RJN_WRDS_DATA` folder and open the uploaded notebook. You may use the normal Python 3 kernel. It does not require the older notebook's kernel or variables.
3. Choose **Run > Run All Cells** in this new notebook. No need to paste code into the old notebook, change dates or fill in table names. The readable `a13_etf_breadth.py` is an alternative: paste its whole contents into one new Python cell and run it.
4. Leave the kernel running. The notebook first verifies/reuses January2014, runs one QQQ/day, then February2013, then all fixed remaining dates. Full acquisition can take hours. Progress updates show completed dates, not a guaranteed ETA.
5. When the last cell prints `passed_checks` and shows `RJN_A13_ETF_BREADTH_FULL.zip`, click the ZIP link to download it. Give that ZIP back in this chat for independent analysis/checking. It contains restricted training derivatives and is for this private analysis, not GitHub.
6. If it prints `STOPPED`, download the PARTIAL ZIP link and return the printed error/status. Do not alter filters, dates, row limits or source paths. The notebook does not keep going into other phases after a failure. An interrupted run can be resumed by Run All; accepted members must match their stored hashes/check records.

No passwords or Duo codes belong in the notebook or chat. Setup runs only on the already authenticated WRDS host and starts local SAS without reading credential files. If SAS is not on that host's PATH, return the explicit error; do not rerun older acquisition cells as a workaround.

The code is self-contained and offline checked, but no new live WRDS run is claimed. It deliberately stops for missing source access, mismatched recorded-row correspondence, changed files, incomplete independent checks or exceeded existing memory bounds. Those are findings to diagnose, not tolerances to loosen.

Scientific scope: four fixed ETFs, the original historical overlap, and no new data-selected windows. Previously seen January2014 remains labeled. Broader findings may strengthen or weaken the current paper. Closed validation/final periods are untouched. The original forecast/history-reconciliation task remains separate.

Implementation reference for local STDIO SAS and cfgfile: https://sassoftware.github.io/saspy/configuration.html (official SASpy documentation, inspected 22 October 2026).
