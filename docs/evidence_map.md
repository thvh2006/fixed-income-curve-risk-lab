# Claim–evidence map

| Claim | Evidence | Challenge | Status |
| --- | --- | --- | --- |
| 499 complete core curves | Raw annual CSVs; `coverage`, `source_receipts`, source manifest | Duplicate dates, year mismatch, missing/nonfinite tenor rejection | Supported for retrieved files; historical vintages absent |
| Bootstrap reprices idealised par instruments | `history[].repricing_bp`; notebook 03; Excel Bootstrap | Every curve × nine core tenors; negative-rate fixture; no extrapolation | Supported internal identity; no traded security validation |
| Dated bond pricing/YTM reconcile | `bond`, 36 `golden_cases`; notebook 02; independent workbook and browser pricer | Coupon dates, mid-period AI, EOM/leap dates, analytical zero/par and round trips | Supported within regular hypothetical conventions |
| Key rates describe nonparallel exposure | `bond.curve_risk`, `portfolios`; notebook 04 | Partition of unity, finite-difference aggregation, +200 bp full repricing | Qualified by chosen zero bump basis |
| Equal duration does not equal equal stress | Bullet/barbell durations and stress; notebook 05 | Equal capital and matched parallel DV01, twists and butterfly | Supported model illustration |
| 2/10-year hedge leaves material 5-year residual | `hedge.before`, `after`, bounds, full stress | Independently re-solved bounded objective, parallel-neutral and same-instrument controls | Supported; not an execution recommendation |
| Carry bridge matches cash ledger | `carry`; notebook 06; workbook Carry and Roll | Separate coupon/dirty identity, higher finance/cost scenarios | Supported ordered accounting identity |
| No-change has lowest aggregate forecast RMSE | `forecast.metrics`, 49 origin receipts; notebook 07 | Train-only PCA/scaling; matured targets; whole-evaluator future mutation | Supported retrospective comparison; no general superiority claim |
| Forecast allocation provides investment alpha | `forecast.allocation` contains all four policies | Costs, duration cap, common dates, observed-vs-hypothetical distinction | Not established; model-implied decision illustration only |
| Failed refresh preserves last good data | `refresh_market.py`; operations tests | Invalid CSV and date regression leave identical last-good bytes | Supported in failure tests; deployed run receipt recorded separately |
| Report/Excel/web agree | Canonical artifacts, Excel receipt, browser golden cases, manifest | Baseline and changed inputs, native recalculation and visual QA | Supported within recorded test coverage |
