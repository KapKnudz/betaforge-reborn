# Simple calculations for an initial valuation

Use the [analysis policy](../../../analysis-policy.md), [calculation catalogue](../../../calculations.md) and [named registry](../../../../betaforge/financials.py) for canonical definitions, fields and limits. Select calculations that answer a specific business question.

Preserve source IDs, dates, periods, currency, scale, scope and adjustments. Normalize once into registry units: SEK, actual shares and tonnes; forecast rates are fractions. Use Decimal and round for display. Keep reported and adjusted EBIT separate. Missing inputs affect only dependent conclusions. Numerical reconciliation alone does not establish an accounting definition.

## Initial financial quality

Use compatible annual/R12 flows, dated balances and relevant history; explain acquisition, FX, seasonality and restatement effects. Select diagnostics that explain the company.

| Question and named calculation | Simple formula | Comparable basis and limit |
|---|---|---|
| Profitability: `ebit_margin` | `100 × EBIT / revenue` | Positive revenue and consistent EBIT basis. Pass-through prices can move revenue and margin without changing underlying unit economics. |
| Incremental profitability: `incremental_ebit_margin` | `ΔEBIT = EBIT_current − EBIT_previous`; `Δrevenue = revenue_current − revenue_previous`; margin = `100 × ΔEBIT / Δrevenue` | Confirm comparable periods and show both deltas. Zero revenue change is undefined; contraction, changes below 1% of prior revenue, acquisitions, FX and pass-through revenue require qualification. This alone does not prove operating leverage. |
| Capital efficiency: `invested_capital`, then `operating_roic` | `capital = group equity + gross debt including leases + net pension liability − cash − non-operating assets`; `NOPAT = EBIT × (1 − operating tax rate)`; ROIC = `100 × NOPAT / ((opening capital + closing capital) / 2)` | Explicit sourced or assumed tax rate and positive average capital. Opening/closing observations match the annual/R12 flow. Group equity already includes goodwill and NCI; leases already enter gross debt. Pensions are additional only outside debt. Keep provider ROIC and issuer ROCE separate. A loss's tax benefit may be unusable; this ratio does not establish value creation against the personal equity hurdle. |
| Working-capital demand: `working_capital_to_sales` | `100 × selected operating balance / annual or R12 sales`; average balance = `(opening + closing) / 2` | Name actual operating receivables, inventory or trade payables. Average requires both balances; closing is an explicit alternative. Explain seasonality. These are sales ratios, not inventory/payable days; total liabilities cannot substitute for trade payables. |

For earnings-to-cash quality, `group_cash_conversion` preserves this bridge:

```text
cash_after_capex = statutory group CFO − cash capex
cash_after_capex_and_interest = cash_after_capex − gross interest paid outside CFO
cash_after_debt_like_service = cash_after_capex_and_interest − lease principal outside CFO
conversion_percent = 100 × cash_after_debt_like_service / group net income
```

CFO already includes working-capital movements and cash taxes. Expose or reverse these before normalization; deduct each outflow once. Capex, outside-CFO interest and principal are positive outflow magnitudes. Group net income includes NCI and is after interest/tax; conversion requires positive income and is before dividends. It is a group diagnostic, not parent-common FCF. Missing gross interest or principal leaves conversion unavailable; show earlier known amounts. Bundled lease payments need a verified principal split. Keep SBC addbacks visible and address expense, awards and dilution without charging the same award twice.

## Primary valuation: operating earnings and the equity bridge

For each bear/base/bull case over the two-to-three-year horizon, choose one operating equation:

- `revenue_ebit`: `forecast EBIT = revenue × EBIT margin`.
- `volume_ebit`: `forecast EBIT = sales tonnes × EBIT per tonne`, when that better explains the business.

Use one estimate for the same operations. Anchor material drivers to annual/R12 results and history; explain their magnitude together. A central case combining record scale and strong profitability needs evidence. Select a defensible positive exit multiple on the same EBIT/claims basis.

`valuation_case` then applies:

```text
future_financial_net_debt = current_financial_net_debt − annual_retained_cash × years
enterprise_value = forecast_ebit × exit_multiple
total_claims = future_financial_net_debt + additional_leases + pensions + nci_value
common_equity = enterprise_value − total_claims + non_operating_assets
future_target = common_equity / forecast_shares
present_value = future_target / (1 + r)^years
              + Σ annual_dividend_per_share / (1 + r)^t, t = 1..years
```

Show every intermediate. Additional leases, pensions and NCI enter only when excluded from financial net debt and required by the selected EBIT/multiple convention. Identify supported surplus assets separately; cash already netted in debt is not added again. State target-date treasury shares, awards and issuance; historical EPS shares are not automatically forecast shares. Negative common equity is an equity shortfall, not a negative price quote.

Reconcile acquisition obligations: where each enters debt or cash uses, any declared aggregation/proxy and remaining gap. The registry has no acquisition-claim field. Do not silently relabel purchase obligations as actual NCI or remap historical cases. Keep targets conditional where the bridge leaves a material claim unresolved.

Support retained cash with an earnings path or horizon average: identify noncash adjustments, cash taxes, interest, working-capital needs, recurring investment and leases, then acquisitions, minority distributions and common dividends. Reuse saved named results and scalar reconciliation, separating generation from spending and exposing residual assumptions. `annual_retained_cash` is the constant annual amount after all those needs; it may be negative. Terminal EBIT alone does not establish horizon-average cash. Dividends are valued separately and cannot also reduce debt.

## Price checks and conditional complements

`ev_ebit = operating EV / positive EBIT` uses a dated EV with matching claims and annual/R12 earnings. Reconcile current EV from dated market cap, financial net debt, additional claims and separately valued surplus assets. `pe = dated price / positive parent diluted EPS` uses matching SEK/share and annual/R12 scope; label any basic-EPS alternative separately.

Use `fcf_yield = 100 × scoped FCF / matching value` only when supportable: parent-common cash pairs with market cap; unlevered firm cash pairs with EV. The function does not derive FCF. Group cash after debt service and unverified provider FCF do not establish parent-owner cash. Related multiples sharing forecasts provide context, not independent confirmation.

The conditional market-implied EBIT check is:

```text
(((price − dividend_pv) × (1 + r)^T × forecast_shares)
 + total_claims − non_operating_assets) / exit_multiple
```

Hold the stated multiple, claims, dividends and return fixed. This is the operating requirement under those assumptions, not a unique market forecast or reverse DCF. Test one or two useful modest changes or a coherent disappointment, including associated cash/reinvestment needs.

## Shareholder returns

Show each case's annual cash-flow IRR first. Reuse `expected_cashflow_irr`: set `expected_annual_dividend_per_share` to that case's dividend and `expected_future_target` to its target. Label the output as that case's IRR:

```text
0 = −starting_price + Σ dividend / (1 + IRR)^t + future_target / (1 + IRR)^years, t = 1..years
```

The implementation assumes constant year-end dividends and adds the target once to the final dividend. Inputs require positive price, nonnegative receipts and an integer 1–10-year horizon; no positive receipts gives no finite IRR.

When the [probability policy](../../../analysis-policy.md#probabilities-and-returns) supports weights, use `scenario_weighted_values` with explicit company-specific probabilities summing to one, then `expected_cashflow_irr` on the weighted cash flows. Label results from representative cases or omitted tails conditional. For unweighted cases, use individual returns and the price or operating conditions required to clear the hurdle.

Compare returns with the starting **10% personal annual equity hurdle**. Show **9% present-value sensitivity**, holding cash flows, operations and probabilities fixed; rate-only changes affect PV, not IRR. Explain any rate override. This is not WACC. Keep **SIXRX trailing ten-year annualized total return**, with reinvested dividends and verified dates/series, separate as historical context. Missing SIXRX leaves that comparison unavailable, not the hurdle verdict.

## Worked example: operating disappointment and the exit multiple

Use the [fictional manufacturer](business-evidence.md#fictional-example) at an illustrative SEK 100 share price. Assume three years, 10 million diluted shares, SEK 110 million of financial net debt and SEK 10 million of additional leases. Assume zero other claims and non-operating assets. The base case has SEK 30 million in annual cash after operating, reinvestment and financing needs, before common dividends. A SEK 2 dividend per share leaves SEK 10 million retained each year and SEK 80 million of financial net debt at exit.

| Check | Exit EBIT (SEK m) | Exit EV/EBIT | Annual dividend (SEK/share) | Future target (SEK/share) | Value today at 10% (SEK/share) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base | 120.75 | 12× | 2.00 | 135.90 | 107.08 |
| Multiple sensitivity | 120.75 | 10× | 2.00 | 111.75 | 88.93 |
| Operating disappointment | 66.50 | 12× | 0.00 | 67.80 | 50.94 |

In the base case, `valuation_case` multiplies EBIT by 12 to get SEK 1,449 million of EV. Subtracting SEK 80 million of net debt and SEK 10 million of leases leaves SEK 1,359 million for common shareholders. Divide by 10 million shares and discount the target and the three year-end dividends. In the operating disappointment, weaker orders, discounting and slower inventory clearance leave no cash to distribute or retain, so net debt stays at SEK 110 million. This checks the business and cash assumptions at the same multiple. The separate multiple sensitivity shows why the base result at SEK 100 needs evidence for the 12× assumption. Both multiples are illustrative.
