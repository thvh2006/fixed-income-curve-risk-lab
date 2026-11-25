# Workbook review guide

Open `deliverables/P4_Curve_Risk_Workbook.xlsx` and start at **Start Here**. Blue cells with pale amber fill are editable, green formulas link other sheets, black formulas calculate locally. Values in historical review regions are imported Python snapshots.

| Area | What recalculates | What stays a snapshot |
| --- | --- | --- |
| Inputs / Bootstrap | Nine par inputs, interpolated semiannual coupons, sequential DFs, repriced par | Raw Treasury source table |
| Bond Schedule | Maturity-anchored regular coupons, future flags, ACT/365 time, cash flows, discount/PV and yield exponents | None in the selected-bond calculation |
| Price and Risk | Accrued, clean/dirty, solved Excel YIELD, yield duration/DV01 and convexity | Python baseline audit targets |
| Key Rate Risk | Each cash flow's contribution to six zero-rate bumps | Key tenor definitions |
| Inputs G34:J37 | Native coupon × parallel-zero-bp sensitivity, linked to the actual coupon/shock inputs | None in the sensitivity grid |
| Curves and Fit / Portfolios / Stress | Differences and presentation | Full Python method, allocation and scenario results |
| Hedge | Before + two saved instrument sensitivities × editable hedge units; L2 residual | Instrument sensitivities, saved optimiser solution, parallel-neutral counterexample |
| Carry and Roll | Bridge components, financing and per-side cost assumptions, net return and identity | Initial/aged/final revaluation inputs for the fixed historical holding |
| Forecast | Presented outcomes and date-level audit trail | PCA/ridge fits, errors and allocation histories |
| Audit | Independent differences and tolerances | Canonical baseline expected values |

## Meaningful checks

1. Default settlement 2025-12-31, maturity 2030-12-31, coupon 4%, zero shock. Dirty price should be 101.215533 per 100 face. The solved YTM is approximately 3.7313%.
2. Change coupon and zero shock. Compare the live selected-bond result with the native sensitivity table. Full repricing is used, not a duration-only estimate.
3. Move settlement within a coupon period. Accrued becomes positive and YTM fractional periods update. On a coupon date accrued is zero and that date's payment is excluded after payment.
4. Change the hedge's two position units. Residual key-rate exposures and L2 norm update. The saved least-squares solution need not neutralise parallel DV01.
5. Increase financing and transaction costs. The carry bridge net return declines and the ledger reconciliation stays zero.

Restore baseline controls before expecting baseline Audit comparisons to pass. Restore par rates from Sources for 31 December 2025. The workbook intentionally does not claim to retrain forecasts or recompute all historical scenarios when a selected-bond control changes.

Supported selected-bond scope is regular semiannual coupons, face 100 and a practical maximum 29-calendar-year horizon. No business-day payment adjustment, stub schedule or actual Treasury quote is implied. Invalid inputs are flagged; unexpected numerical errors remain visible.
