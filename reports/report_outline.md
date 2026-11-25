# Fixed Income Curve and Risk Lab

thvh2006<br/>Research release 1.0.0 | 25 November 2026<br/>Frozen observations: 2 January 2024 to 31 December 2025

<b>Abstract.</b> This study examines how transparent curve construction translates published Treasury par yields into hypothetical cash-bond valuation, key-rate exposures and hedging decisions. The evidence comprises 499 daily curves, an educational semiannual bootstrap, two interpolation methods, a Nelson-Siegel challenger, dated cash flows, equal-capital portfolios and an ordered return bridge. A retrospective five-observation forecast comparison evaluates no-change, train-only PCA/AR and ridge-change specifications on 49 non-overlapping target windows in 2025. All model and allocation candidates are retained.

The bootstrap reprices its idealised input instruments to floating-point precision. A hypothetical 4% bond due 31 December 2030 has a model dirty price of 101.215533 per 100 face on 31 December 2025. Equal parallel duration does not equal equal twist exposure. The bounded 2/10-year hedge reduces the six-bucket risk norm from 435.46 to 432.84 USD per basis point but leaves material residual risk. No-change produces lower aggregate forecast RMSE (9.40 bp) than PCA/AR (10.68 bp) or ridge (9.41 bp).

<b>Research boundary.</b> Treasury par/CMT observations are not a zero-coupon curve or an observed total-return series. All prices, portfolios, hedge trades and allocation returns in this paper are model-implied. The historical files were retrieved in 2026 and are not archived historical vintages. This release establishes numerical and accounting evidence within a stated educational model; it does not establish an executable investment edge.

<b>Reproducibility.</b> The public repository supplies original Python code, source CSV receipts, configuration, executed review notebooks, an independent Excel review workbook and an interactive dashboard. Canonical result artifacts carry a run identifier; the release manifest records exact file digests. Mathematical correctness and source semantics are tested separately.
# 1. Research question, design and evidence

The central question is whether differences in curve construction and key-rate exposure materially alter a fixed-income risk decision that might look satisfactory under a single duration number. The null for the forecasting extension is that added model structure does not improve a five-observation-ahead rate forecast beyond holding the current curve unchanged. Numerical fit, risk reduction and forecasting accuracy are evaluated as distinct outcomes.

The nominal Treasury scope excludes credit spreads, default recovery, inflation-linked principal, swaps, collateral conventions and futures delivery options. There is no CTD or conversion-factor model, and therefore no futures hedge. The hedge instruments are hypothetical cash bonds with explicit sensitivities and a cash-financed overlay. Instrument simplicity enables transparent reconciliation without implying coverage of the wider fixed-income market.

The design has three evidence levels. Published daily par rates are observed inputs. Discount, zero and forward curves are fitted objects. Dated bonds and portfolios are hypothetical instruments valued from those objects. Exact repricing of a constructed par instrument is a necessary calibration identity. It is not an independent validation against actual security prices, because those prices are not in the source data.

Source years and model settings are recorded in the research configuration. Calendar year 2024 supplies initial training history; 2025 supplies the retrospective forecast comparison. Forecast settings are fixed in code and configuration before the reported comparison is generated. This is not represented as an untouched historical holdout: the research was designed and run after the sample ended, and no prospective period has yet been collected.

The workflow freezes research outputs while allowing a separate EOD market receipt. Refreshing that receipt cannot alter the original study, the forecast comparison or the paper conclusion. Source access, rate validation, curve construction and file publication have distinct failure points. A failed source download retains the last-known-good market snapshot.
# 2. Source data and curve semantics

The source register contains official Treasury annual CSVs for 2024 and 2025 [S2, S3]. The intake sorts dates, rejects duplicate observations, requires nine complete core tenors and converts percentage quotes into decimal annual rates. The core grid is 6 months, 1, 2, 3, 5, 7, 10, 20 and 30 years. The 250 observations in 2024 and 249 in 2025 provide 4,491 core tenor cells without imputation.

The additional short maturities are retained in the original CSVs but are outside the educational coupon bootstrap. The 1.5-month series begins during 2025; its earlier absence is not filled or interpreted as zero. The study begins well after the documented December 2021 methodology change. These choices avoid a mixed-method historical sample and a changing short-tenor feature set, while limiting the span available for inference.

Treasury describes its production curve as a par curve derived with a monotone-convex method from indicative bid-side quotations [S1]. The lab does not reproduce that proprietary production implementation. It reads the published fixed-tenor par observations and constructs a disclosed approximation. A rate observed at a 10-year tenor does not imply that a particular traded instrument has exactly ten years remaining.

The local retrieval time is saved with SHA-256 hashes of the exact source bytes. Treasury generally targets publication by 18:00 America/New_York, subject to delays [S1]. The study has no vintage archive or security-specific execution timestamps. Same-day forecasting is therefore framed as an after-publication retrospective exercise rather than a certified historical trading simulation.

A fitted zero rate is a model output and depends on compounding and interpolation. Continuous zero and forward rates are labelled separately from semiannual YTM and par coupon rates. Negative-rate inputs are permitted by the engine; positive discount factors are required, while monotonic discount factors are not imposed as a universal condition.
# 3. Conventions, schedules and bond mathematics

The hypothetical instruments pay regular semiannual coupons with no odd first or last stub. Coupon dates are generated backwards from maturity using an end-of-month-aware anchor. Payment dates remain unadjusted. There is no claim that this schedule reproduces every Treasury legal payment convention. Settlement is explicit, and cash flows at or before settlement are excluded, corresponding to valuation after any same-date payment.

Accrued interest uses the elapsed fraction of the actual regular coupon period: AI = face × annual coupon / 2 × elapsed days / coupon-period days. Dirty price equals clean price plus accrued interest. Accrual is zero on a coupon date. Yield discount exponents use the remaining fraction to the next coupon plus the number of subsequent semiannual periods; the quoted YTM compounds semiannually.

Curve valuation uses Actual/365 Fixed time from settlement to each payment and the relevant discount factor. This time basis differs deliberately from the regular-period yield convention. As a result, calendar-dated cash flows may not fall precisely on the educational half-year bootstrap grid. Repricing that dated bond at a par coupon need not return exactly 100, even when the idealised par calibration identity holds.

The YTM solver brackets yields above -200% and uses bisection. Nonpositive dirty prices and unsupported maturities fail explicitly. Extrapolation beyond 30 curve years is prohibited; because Actual/365 includes leap days, the interactive bond schedule is restricted to a practical 29-year calendar horizon. A zero-coupon bond reduces to the analytical discounted-redemption case.

Macaulay duration is the PV-weighted cash-flow time under the yield convention. Modified duration divides it by one plus half the annual YTM. Convexity follows the second derivative with respect to that yield. These yield derivatives are checked against central finite differences, while parallel continuous-zero duration is computed by curve repricing and reported as a different measure.
# 4. Bootstrap, interpolation and model comparison

The educational bootstrap first linearly interpolates the sparse core par yields to each half-year maturity. Every interpolated coupon is an assumption, not an additional observed quote. With unit redemption, the next discount factor solves D(n) = [1 - c(n)/2 × sum of prior discount factors] / [1 + c(n)/2]. Sequential calibration produces a 60-node grid ending at 30 years.

Between nodes, the baseline linearly interpolates log discount factors. The linear-discount challenger shares exactly the same calibrated nodes and therefore reprices the same idealised semiannual instruments; it can differ for dated off-grid cash flows. No unsupported extrapolation is silently introduced. Shape diagnostics inspect positivity, forward levels and changes, rather than forcing an economically universal monotonicity rule.

The Nelson-Siegel challenger describes continuous zero rates using a level, slope, curvature and positive decay parameter. A damped Gauss-Newton routine minimises equally weighted par-yield residuals in basis points, using three fixed starting decay values and disclosed parameter bounds. The lowest residual solution is retained. Numerical finite-difference Jacobians and damping support stability without requiring a black-box pricing library.

The maximum absolute bootstrap repricing error across the full history is 3.12e-12 bp. The final-date Nelson-Siegel par RMSE is 3.6195 bp. The smooth model is a useful alternative representation; its lower dimensionality does not imply a more accurate price for an actual security. The actual-security validation gate remains open because security-specific quotes are absent.

The method comparison holds the same date, par observations and cash-flow instrument constant. It separates calibration error from interpolation choice. A model could fit the observed par grid closely yet produce different off-grid sensitivities. That distinction is central to hedge review: the exposure object, bump basis and cash-flow conventions matter alongside the RMSE.
# 5. Duration, convexity and key-rate sensitivities

Parallel curve DV01 is [P(zero - 1 bp) - P(zero + 1 bp)] / 2, in currency per basis point. Curve duration divides this central price difference by price and the 2 bp denominator. Curve convexity uses the corresponding central second difference. All shocks act on continuous zero rates; the par observations are not shifted and re-bootstrapped for these risk measures.

Key rates use triangular zero-rate hats at 0.5, 2, 5, 10, 20 and 30 years. The first and last hats remain flat outside the outer knots, so the hats partition unity over supported cash-flow times. The shock is evaluated directly at each payment time. A one-basis-point bump is repriced independently for each bucket; summing bucket DV01 approximates the parallel bump with a small finite-difference residual.

The selected five-year bond has yield modified duration 4.500237, curve duration 4.584934 and parallel curve DV01 0.04640665 per 100 face. The sum-of-keys residual is -4.38e-11 USD per basis point. The different duration measures are consistent with their different perturbation conventions; they are not interchangeable labels.

Large parallel shocks are fully repriced and compared with first-order duration and second-order duration-plus-convexity approximations. Convexity explains much of the second-order discrepancy but does not make a local approximation exact for a large move or a curve twist. Numerical correctness is assessed with small shocks; economic materiality is assessed with the larger stress set.

The Excel workbook independently generates the dated coupon schedule, bootstraps the default curve and calculates cash-flow-level key-rate contributions. Browser pricing independently implements the same conventions. Reconciliation tolerances reflect arithmetic precision and quoted units. A green-looking screen is not used as a substitute for checking the actual formula results.
# 6. Portfolio construction and stress design

Bullet, barbell and ladder portfolios each begin with USD 1 million of model market value. The bullet holds the five-year bond. The barbell allocates 58.46% to the two-year bond and 41.54% to the ten-year bond so its parallel curve duration equals the bullet at the starting date. The ladder allocates equally across one- through five-year maturities. All instruments use the disclosed hypothetical 4% coupon.

The ladder is an equal-capital comparison, not a duration-matched portfolio; its shorter exposure is displayed rather than hidden. Fractional face-100 units permit precise allocation in this risk study. No integer-lot implementation, dealer spread, short locate or security-specific liquidity is assumed. These simplifications make the comparison interpretable but limit execution claims.

The stress set includes parallel +100, -100 and +200 bp changes, a steepener, a flattener and a butterfly, with node shocks stored in the canonical artifact. A historical replay applies the change between the first and last 2025 model zero curves to the year-end book. That replay is a scenario on a fixed book, not a historical holding-period return.

Under the +100 bp parallel scenario the bullet loses USD 44,757.81, while the matched-duration barbell loses USD 44,179.21. Their local first-order exposures agree, while their convexity and full-repricing outcomes differ. Under the steepener the bullet P&amp;L is USD 1,157.56 and the barbell P&amp;L is USD -8,681.27.

The interpretation is structural. Matching one scalar does not match a vector of exposures. A portfolio can appear hedged under a parallel approximation and remain exposed to a local or nonparallel curve move. Stress is therefore evaluated after construction using the full payment schedule and the specified shock interpolation.
# 7. Bounded hedge and residual risk

The main hedge overlays two- and ten-year hypothetical cash bonds on the USD 1 million bullet. It minimises the squared Euclidean norm of six residual key-rate DV01 values, with each instrument bounded to plus or minus 20,000 face-100 units. Buckets receive equal weight in USD per basis point. A different bucket weighting would be a different hedge objective; no optimality across all market states is implied.

The unconstrained least-squares solution initializes a bounded coordinate-descent solver. Saved units, objective values, bounds and residual vectors are included in the release. Excel allows reviewers to change the saved units and observe the resulting risk vector without an add-in. A same-instrument five-year control is retained separately to show that an exact offset is numerically possible but economically uninformative for the cross-maturity question.

The main overlay uses -981.56 two-year units and -594.30 ten-year units. Its residual norm declines from 435.46 to 432.84 USD/bp. Initial cash of USD 157,692.95 offsets the hedge market value. The one-way transaction-cost illustration is USD 31.54 at 2 bp of gross consideration.

A separate 10-year-only hedge sets parallel DV01 to zero but leaves key-rate L2 risk of 565.48 USD/bp. The stress-after-hedge table reprices the overlay and the original book. Those instantaneous scenario figures exclude the displayed transaction cost and future cash financing. Short-bond borrowing, repo specialness, counterparty limits and changing hedge ratios are absent. The saved overlay is therefore a risk illustration rather than an executable hedge instruction.

Residual risk is expected: two instruments span at most two independent exposure directions, while six key-rate buckets describe the target. A lower L2 norm does not guarantee a smaller loss under every shock. The retained before/after vectors and large-shock results make this trade-off visible, instead of presenting a single hedge-effectiveness percentage as a universal outcome.
# 8. Carry, roll-down and the cash ledger

The holding study buys a hypothetical 4% bond due 2 January 2030 on 2 January 2025 and values it on 2 July 2025. The bond remains the same instrument. Coupon cash is recorded at payment and earns zero reinvestment return. All entry and exit values are dirty prices, so accrued interest is not added a second time.

The ordered bridge first ages the bond at its initial solved constant YTM. Coupon cash plus that aged price less opening dirty price is labelled carry. The difference between the aged initial-tenor-curve valuation and the constant-YTM valuation is roll-down. The difference between final-curve and initial-tenor-curve valuations is the curve move. This ordering is explicit and is not a unique causal decomposition.

Carry is 2.154094, roll-down 0.071257 and curve-move P&amp;L 2.086278 per 100 face. Financing at 4% annual on the opening dirty price contributes -1.949799. Assumed entry and exit costs of 2 bp contribute -0.039781. Net P&amp;L is 2.322049 and the net return is 2.3623%.

The independent ledger identity is coupons received plus final dirty value minus opening dirty value plus financing and transaction-cost entries. The sum of bridge components matches this identity to floating-point precision. Coupon-day, accrued-interest and leap-date tests challenge common timing errors. For a financed holding, the financing assumption is a driver, not an observed funding quote.

A constant-maturity allocation cannot be treated as the same holding. At each rebalance it sells aged instruments and buys replacement maturities, generating turnover and new cash flows. The forecast allocation illustration therefore rebuilds its hypothetical sleeves explicitly and charges costs at every entry and exit. It does not reuse this fixed-holding return as a frictionless total-return index.
# 9. Forecast protocol and negative comparative evidence

The forecast target is the nine-tenor par curve five source observations ahead. The 2025 origin sequence advances by five observations, so target windows do not overlap; an endpoint can also be the next origin. Training expands from 2024 and contains only observations through each origin. Every target used in training matures by that origin. Different calendar gaps between observations are retained.

No-change repeats the current curve. PCA/AR fits three principal components to the training level curves only, regresses future five-step factor scores on current scores and an intercept, and reconstructs the curve. The ridge-change model predicts five-observation curve differences from three lagged five-observation differences, with train-only centering/scaling and fixed alpha 100. No hyperparameter selection is performed on the reported evaluation.

Across 49 origins and nine tenors, no-change RMSE is 9.3973 bp, PCA/AR RMSE is 10.6826 bp and ridge RMSE is 9.4133 bp. Corresponding MAEs are 7.1429, 8.0114 and 7.1828 bp. All model results, including weaker challengers, remain in the published artifact.

The evidence does not support replacing no-change on aggregate error. The ridge gap is particularly small relative to the short sample. Errors across tenors are correlated and the forecast origins share expanding training history. No independence-based significance claim or extrapolation to all rate regimes is made. Future-data mutation checks test the software boundary but cannot turn later-retrieved history into a vintage dataset.

Dynamic Nelson-Siegel, macro vintages and additional machine-learning families remain separate extensions. They should be motivated by a measured deficiency and evaluated under a new protocol. Adding models until the 2025 ranking changes would consume the same retrospective comparison repeatedly and would weaken the interpretation.
# 10. Forecast decision value and model-implied allocation

The allocation illustration compares a fixed mix, no-change, PCA/AR and ridge forecasts. A fully funded portfolio holds two- and ten-year hypothetical sleeves, with no more than 50% in the ten-year sleeve and no more than six years of starting curve duration. At each five-observation origin it evaluates the expected aged price on the predicted curve, including coupon cash and assumed two-sided costs, then chooses either the permitted long-sleeve weight or the short sleeve alone.

Each interval liquidates the old position and rebuilds the target maturities. Both entry and exit cost 2 bp of dirty consideration. Fractional positions, no execution delay, zero interest on coupon cash and no taxes are assumed. The baseline fixed mix uses the same time-varying admissible maximum long weight. All policies share dates, costs and instrument conventions; the experiment does not use security-specific bid/ask quotes.

Terminal wealth from unit starting capital is fixed mix: 1.047779, no change: 1.047779, pca ar: 1.037010, ridge change: 1.047377. These are model-implied accounting outcomes across the 49 saved intervals, with no annualisation into a claimed market track record. The first-origin and last-target dates and each policy weight are retained in the artifact.

Forecast RMSE and economic decision value measure different things. A forecast can improve a long-tenor direction while worsening average error, or select a duration exposure that benefits from the realised regime. Such a payoff can coexist with weak predictive evidence. A single short retrospective period cannot distinguish skill from exposure and sample luck.

The appropriate decision is to retain the simple forecast as the reference and present the allocation figures as sensitivity evidence. No policy is promoted to live capital. A prospective collector, independent actual-security valuation and executable cost evidence would be needed before making a stronger implementation claim.
# 11. Validation, limitations and reproducibility

Validation has separate mathematical, temporal, reconciliation and failure layers. Analytical zero/par cases, price-yield round trips, accrual at coupon and leap dates, duration derivatives, convexity, key-hat aggregation, bounds and carry identities are tested. The release verifier rebuilds every observed curve, compares saved risk and forecast outcomes, checks source and release hashes and validates artifact semantics.

The workbook independently implements a subset suitable for manual review. Historical method comparisons, portfolio stress, hedge-input sensitivities and forecasting are imported Python snapshots and are labelled as such. Native coupon/zero-shock sensitivity uses actual model input cells. The browser pricer is an independent implementation with strict blank-input and date handling. Cross-platform agreement establishes consistent mathematics within the shared assumptions; it does not validate an absent market quote.

The notebook runner executes independent Python namespaces with captured HTML tables and PNG figures. Native Jupyter-kernel execution is a separate capability and is not claimed by that runner. The release provides readable executed outputs on GitHub and standard notebook cells that also support an IPython display environment. A manifest makes the exported state reviewable.

Important limits remain: two source years; later-retrieved history; educational par interpolation; regular hypothetical coupons; no odd stubs or adjusted payment calendar; no actual-security prices; no credit, liquidity or futures-delivery model; stylised borrowing and transaction costs; and no prospective investment evidence. The laboratory is complete within this nominal educational scope, with those boundaries retained in every output.

<b>References</b>

[S1] U.S. Department of the Treasury (2025). Treasury Yield Curve Methodology, revised 18 February 2025. <link href="https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology">Official source</link>.

[S2] U.S. Department of the Treasury. Daily Treasury Par Yield Curve Rates, calendar year 2024. Retrieved 25 November 2026. <link href="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&amp;field_tdr_date_value=2024">Official source</link>.

[S3] U.S. Department of the Treasury. Daily Treasury Par Yield Curve Rates, calendar year 2025. Retrieved 25 November 2026. <link href="https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&amp;field_tdr_date_value=2025">Official source</link>.

[S4] U.S. Department of the Treasury. Interest Rates: Frequently Asked Questions. <link href="https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rates-frequently-asked-questions">Official source</link>.

<b>Canonical run:</b> p4-662f58a64e8e. <b>Repository:</b> <link href="https://github.com/thvh2006/fixed-income-curve-risk-lab">github.com/thvh2006/fixed-income-curve-risk-lab</link>.