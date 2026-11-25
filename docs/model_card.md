# Research charter and model card

**Question:** how do curve construction and key-rate exposures alter hypothetical cash-bond valuation, hedge and carry/roll-down? **Extension:** does a curve-factor forecast improve rate prediction and a constrained allocation illustration relative to no-change?

**Evidence clock:** 499 source observations, 2 January 2024–31 December 2025; retrieved 25 November 2026. This is a retrospective study, without historical provider vintages or a prospective holdout. The market receipt has its own source date and retrieval clock.

## Instrument contract

| Item | Choice | Practical consequence |
| --- | --- | --- |
| Instrument | Regular nominal hypothetical cash bond | No actual CUSIP claim |
| Frequency | Two coupons per year | No odd stub support |
| Dates | Backwards from maturity, EOM-aware, unadjusted | No holiday/payment adjustment |
| Valuation moment | After same-date coupon payment | Settlement-date cash flows excluded; accrued resets to zero |
| Accrual | Actual/Actual ICMA regular coupon periods | Actual days divided by actual coupon-period days |
| Yield | Annual nominal, semiannual compounding | Fractional first coupon exponent |
| Curve time | Actual/365 Fixed | Leap years can push a 30-calendar-year cash flow outside 30 curve years |
| Price | Per 100 face, dirty = clean + accrued | Coupon cash and accrued cannot be credited twice |
| Support | No extrapolation beyond 30 curve years | Interactive schedule practical maximum 29 calendar years |

## Curve contract

Core par tenors are 0.5, 1, 2, 3, 5, 7, 10, 20 and 30 years. Linear interpolation supplies hypothetical par coupons at each half year. Sequential bootstrap solves unit-par idealised instruments. The baseline interpolates log discount factors. The linear-discount challenger shares nodes. Nelson-Siegel fits four continuous-zero parameters to nine par residuals with equal bp weights and three fixed initial taus.

The source's production method is Treasury's monotone-convex curve [official methodology](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/treasury-yield-curve-methodology). This lab is an alternative educational approximation. Continuous forward-rate jumps at grid boundaries, especially across sparse long tenors, are model diagnostics. A smoothly fitted challenger is compared rather than passed off as an observed curve.

## Risk and decision contract

Continuous-zero shocks are applied at cash-flow times. Key hats at 0.5/2/5/10/20/30 years partition unity and remain flat beyond their outer knots. One-bp central bumps define DV01. Full repricing is the large-shock reference. Yield and curve duration have different perturbation conventions.

Equal-capital bullet/barbell are parallel-duration matched; the ladder is equal capital but shorter duration. The main hedge minimises six-bucket squared USD/bp residual using 2/10-year instruments with ±20,000 unit bounds. A 10-year-only parallel-neutral hedge is a counterexample, and a same-instrument hedge is a mathematical control. Residual risk is retained. Short locate, repo, futures CTD and funding limits are absent.

The carry bridge order is carry at constant YTM → roll on initial tenor curve → curve move → financing → costs. Coupon cash earns zero. Financing at 4% and costs at 2 bp/side are assumptions. A same-bond holding is distinct from a rebuilt constant-maturity basket.

## Forecast protocol

Five source observations ahead, 49 target windows in 2025, next origin at the previous target. All training observations and targets mature by origin. Three PCA factors are fitted on training levels and predicted via a five-step factor regression. Ridge predicts changes from three lagged five-observation changes, with train-only standardisation and alpha 100. No-change is the reference. No evaluation-driven parameter search or model promotion.

The allocation illustration permits 0–50% in a 10-year sleeve, remainder in a 2-year sleeve, maximum six years of starting duration, no leverage and explicit entry/exit costs. It rebuilds maturities each interval. It is a model-implied comparison; no annualised trading track record is claimed.
