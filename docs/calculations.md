# Financial calculation catalogue

Formula version 1, 3 November 2026; return-comparison guidance updated 4 November 2026. This defines the calculations permitted by the [analysis policy](analysis-policy.md). The live named registry is [`betaforge/financials.py`](../betaforge/financials.py), `VERSION = "1"`; the analyst can inspect its formula text, fields, units, limits and outputs.

## Common conventions

- Monetary registry inputs/outputs currently use **SEK**, shares use actual shares, and volume uses actual tonnes. A verified currency conversion is required before using other monetary currencies in this registry.
- Rates, probabilities, margins used in forecasts and multiples use fractions/dimensionless values: `0.10` means 10%. Ratio outputs ending in `_percent` multiply by 100. Valuation multiples are not percentages.
- Preserve source value/scale, date/period, company, reporting/adjustment basis and group/parent ownership. Apply scale once before arithmetic. Missing is not zero; an explicit zero claim needs a source or assumption.
- Use Decimal arithmetic. Display rounding never changes the saved result. A denominator can be mathematically nonzero yet economically unsuitable; expose the limitation.
- Each result identifies formula/version, source or assumption IDs, normalized inputs, output units and warnings/missing inputs. New financial definitions need an explicit named formula; no generic expression language or hidden scoring weights are used.
- The tool wrapper rejects known quarter/YTD denominators in ordinary P/E and EV/EBIT. Capital diagnostics use an annual/R12 flow, its matching closing balance and an opening balance dated the day before the flow starts when dates are known. Undated analyst inputs still require an explicit basis; numerical checks do not independently verify scope or accounting interpretation.
- Current diagnostics prefer the latest compatible quarter/R12 evidence. Annual history and annual-only disclosures remain labelled separately; the [period and input-selection rules](material-inputs.md) define the presentation and evidence requirements.

## Implemented named formulas

| Registry ID | Formula and output | Input meaning and non-use conditions |
|---|---|---|
| `ebit_margin` | `margin_percent = 100 × ebit / revenue` | Positive revenue; reported and adjusted EBIT remain separate. Pass-through revenue can change the percentage without changing fabrication economics. |
| `incremental_ebit_margin` | `ebit_change = ebit_current − ebit_previous`; `revenue_change = revenue_current − revenue_previous`; `incremental_margin_percent = 100 × ebit_change / revenue_change` | Requires `comparable_periods=true`. Zero revenue change is undefined. Revenue contraction and changes below 1% of prior revenue are warnings, not automatic evidence of improving economics. `revenue_passthrough` adds a qualification. Acquisitions, FX and one-offs require interpretation. |
| `working_capital_to_sales` | `selected_balance = (balance_start + balance_end)/2` when `balance_basis=average`; otherwise the explicit closing balance. `ratio_percent = 100 × selected_balance / revenue` | Name the actual operating balance. Average is the default and requires both observations; closing is an explicit alternative. Positive annual/R12 revenue and consistent period/seasonality. These are not inventory/payable days; total liabilities are not trade payables. |
| `invested_capital` | `group_equity + gross_debt_including_leases + net_pension_liability − cash − non_operating_assets` | A book-capital proxy. Group equity already includes goodwill and NCI, and gross debt already includes leases; none is added twice. Pensions are additional only when outside gross debt. Cash and identified non-operating assets are the explicitly selected deductions. |
| `operating_roic` | `nopat = ebit × (1 − operating_tax_rate)`; `average_invested_capital = (invested_capital_start + invested_capital_end)/2`; `roic_percent = 100 × nopat / average_invested_capital` | Operating tax is an explicit fraction in `[0,1]`, from a source or labeled assumption. Positive average capital is required. A loss may imply a tax benefit not immediately usable. Keep this two-point-average measure separate from issuer ROCE and provider ROIC. |
| `group_cash_conversion` | `cash_after_capex = cfo − cash_capex`; `cash_after_capex_and_interest = cash_after_capex − interest_paid_outside_cfo`; `cash_after_debt_like_service = cash_after_capex_and_interest − lease_principal_outside_cfo`; `conversion_percent = 100 × cash_after_debt_like_service / group_net_income` | CFO is statutory group CFO; group net income includes NCI and is after interest/tax. Capex, outside-CFO cash interest and outside-CFO principal are positive outflow magnitudes. CFO already includes working capital/taxes. Interest inside CFO is not deducted again. Missing interest/principal leaves dependent outputs missing; show the known bridge. Conversion needs positive group net income. Before all dividends, not parent-common FCFE. |
| `fcf_yield` | `yield_percent = 100 × free_cash_flow / valuation_denominator` | Explicit options must pair `cash_flow_scope=parent_common` with `denominator_scope=market_cap`, or `firm` with `enterprise_value`. The numerator must already match that scope; this function does not derive FCF. Positive denominator; negative cash retains its sign. Do not substitute unverified provider FCF or group cash after debt service for parent-owner FCF. |
| `ev_ebit` | `multiple = enterprise_value / ebit` | Positive EBIT. Match dates, adjusted/reported earnings and the EV claims convention. Negative EV needs a cash/claim explanation. |
| `pe` | `multiple = price / diluted_eps` | Dated nonnegative price and matching parent diluted EPS, each SEK/share. Positive EPS; a loss does not yield a meaningful ordinary P/E. Keep a basic-EPS choice separately labeled. |
| `volume_ebit` | `ebit = sales_volume × ebit_per_tonne` | Tonnes × SEK/tonne, not ktonnes × kSEK. Nonnegative physical sales; profit per tonne is a stated forecast. Capacity is not sales. |
| `revenue_ebit` | `ebit = revenue × ebit_margin` | Revenue in SEK; forecast margin is a fraction in `[-1,1]`. State the operating mechanism; do not add this EBIT to another volume-derived estimate of the same operations. |
| `valuation_case` | The fixed scenario bridge below, returning `present_value` plus each intermediate economic result. | Positive forecast EBIT, multiple and shares. Integer `years` from 1–10, nonnegative required return and explicit claim/dividend assumptions. Negative common equity is retained as an equity shortfall; no negative share-price/PV quote is fabricated. |
| `scenario_weighted_values` | `expected_present_value = Σ weight_s × present_value_s`; likewise `expected_future_target` and `expected_annual_dividend_per_share`. | Inputs use `bear_`, `base_` and `bull_` prefixes for each `weight`, `present_value`, `future_target` and `annual_dividend_per_share`, plus common `years`. Nonnegative fractions sum exactly to one; all values are nonnegative SEK/share on the same date, ownership basis and integer 1–10-year horizon. Define whether cases cover the distribution or give a conditional approximation. |
| `expected_cashflow_irr` | Solve `0 = −price + Σ expected_annual_dividend_per_share/(1+IRR)^t + expected_future_target/(1+IRR)^years`, `t=1..years`; return `irr_percent = 100 × IRR`. | Positive SEK/share `price`, nonnegative expected dividend and target, integer `years` from 1–10. Constant year-end dividends; final cash is that year's dividend plus the target once. Outputs also expose the initial, interim and terminal cash flows. With no positive future receipts, no finite IRR is reported. This is not an average of scenario IRRs or a promised realized return. |

The cash formula can also show `cash_after_capex_and_net_interest = cash_after_capex + net_interest_cash_outside_cfo`, where net interest is signed. This is a disclosed intermediate, not a substitute for gross outside-CFO interest in the primary conversion. Interest received and paid must not be silently equated. `noncash_sbc_addback` is disclosed separately and not automatically deducted a second time; reported EBIT/net income retain compensation expense, and ownership analysis must address awards and dilution.

Lease principal means principal only. If a source bundles lease interest and principal and the split is not verified, keep principal missing. A missing observation must not become zero to complete the cash-conversion ratio.

## Primary scenario bridge: `valuation_case`

```text
future_financial_net_debt = current_financial_net_debt − annual_retained_cash × years
enterprise_value         = forecast_ebit × exit_multiple
total_claims             = future_financial_net_debt + additional_leases + pensions + nci_value
common_equity            = enterprise_value − total_claims + non_operating_assets
future_target            = common_equity / forecast_shares
terminal_pv              = future_target / (1 + required_return)^years
dividend_pv              = Σ annual_dividend_per_share / (1 + required_return)^t, t=1..years
present_value            = terminal_pv + dividend_pv
price_gap_percent        = 100 × (present_value / price − 1), when a positive price is supplied
```

`annual_retained_cash` is after common dividends, tax, financing cash costs, minority distributions, reinvestment and working-capital needs. It can be negative. If a chosen bridge excludes a cash use, separately disclose how the debt forecast accounts for it, without charging it twice. The first implementation assumes a constant annual amount and annual year-end dividends; it does not imply quarterly forecast precision.

Additional leases, pensions and minority claims are deducted only if the selected financial net debt excludes them and the multiple/earnings convention includes them. Cash already netted in debt is not added again. NCI book value may be an explicit proxy, not a verified fair value. Non-operating assets receive value only if excluded from operating EV and supported separately; a balance-sheet financial-assets total is not automatically surplus value.

Forecast shares refer to the target date. State treasury, incentive and future issuance assumptions. Historical weighted-average EPS shares do not automatically describe that date. Existing awards and recurring future compensation costs are related but different claims; avoid counting the same award twice.

## Other explicit arithmetic and analytical checks

These equations may use the existing saved-ID arithmetic tool. They are transparent supporting calculations, not additional forecasting models or hidden registry functions:

| Calculation | Formula | Required qualification |
|---|---|---|
| Current market cap | `dated share price × selected current shares` | Same class, date and currency; issued shares without a treasury adjustment are a proxy. |
| Current operating EV | `market cap + financial net debt + additional claims − separately valued surplus assets` | Same claims convention as the EBIT multiple; no double cash/lease/pension/NCI deduction. |
| Historical change | `current − previous`; ordinary growth `100 × (current/previous − 1)` | Comparable scope and a meaningful positive baseline for ordinary growth. Otherwise show the absolute change and explain the sign. |
| CAGR | `100 × ((end/start)^(1/elapsed_years) − 1)` | Positive comparable endpoints and elapsed years. Not valid for sign-changing earnings. |
| Market-implied future EBIT | `(((price − dividend_pv) × (1+r)^T × forecast_shares) + total_claims − non_operating_assets) / exit_multiple` | Same fixed assumptions as the scenario bridge; positive multiple. A conditional operating requirement, not a reverse DCF or unique market forecast. |
| Optional EBITDA check | `EBITDA = selected EBIT + selected D&A`; apply an explicit EV/EBITDA and the same equity bridge | A specific diagnostic use only. Shared EBIT and balance-sheet assumptions do not independently validate the main model; capex and working capital remain economically relevant. |
| Sensitivity | `selected formula(changed assumption) − selected formula(base assumption)` | One or two informative modest changes or a coherent joint disappointment. Sensitivity is not outcome probability. |
| Return attribution | An ordered bridge changing operating growth, unit margin, multiple, claims and shares, one stage at a time | State the order and treatment of interactions. An additive explanation of the selected scenario, not a new valuation model. |

## Expected return, personal hurdle and historical comparison

The personal investment hurdle starts at **10%**, with **9% present-value sensitivity** and explained company-specific overrides, as defined in the [policy](analysis-policy.md#probabilities-and-returns). Hold cash flows, operating assumptions and probabilities fixed for that rate-only sensitivity. The selected personal rate is also the starting discount rate for shareholder cash flows; it is not an estimated WACC.

The historical comparison is **SIX Return Index (SIXRX)**: `100 × ((reinvested_dividend_total_return_index_end / index_start)^(1/elapsed_years) − 1)` over the agreed trailing ten years in SEK. Verify the exact series, dates, trading-day alignment, positive index values and source treatment of distributions/corporate actions. Price CAGR without reinvested dividends, another SIX price index or a different total-return index is not an automatic substitute. This historical return is neither the personal hurdle nor a forecast of future index returns.

The adopted candidate statistic is IRR of expected cash flows, using `scenario_weighted_values` followed by `expected_cashflow_irr`. For a starting price `P0`, calculate the probability-weighted cash at each future date, `E(CF_t) = sum(probability_s × cash_flow_s,t)`, including the scenario's terminal share value once at the horizon. Solve `0 = −P0 + sum(E(CF_t)/(1+IRR)^t)`. The present implementation supports constant annual dividends and one common horizon. Decimal bisection solves the unique root for one initial outflow and nonnegative future receipts. Do not average scenario IRRs or apply CAGR only to the expected exit price. If the modeled cases are conditional, the result is conditional too. Compare the result with the selected personal hurdle; changing the discount rate alone does not change this IRR. Missing SIXRX data leaves a historical comparison gap, not a barrier to that personal-hurdle comparison. Earlier packets retain their original conventions.

No full DCF/reverse DCF formula is implemented here. Such a model would need explicit future cash flows, reinvestment, tax and terminal assumptions rather than relabeling the implied-EBIT calculation.
