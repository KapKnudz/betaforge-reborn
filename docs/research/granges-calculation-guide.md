# What the 326 Gränges calculations do

Guide prepared 3 November 2026 for the frozen 1 November walkthrough. This guide classifies existing records; it does not rerun or revise the valuation. The source of every appendix row is the [saved calculations](../../data/granges-codex/runs/20261101-full/calculations.json), and the original values/assumptions are in [saved inputs](../../data/granges-codex/runs/20261101-full/inputs.json).

## Why the count is large

The report contains one principal three-scenario EV/EBIT model, an EBITDA cross-check, a reverse market-expectations check, source reconciliations and sensitivity tests. The 326 entries count individual arithmetic operations. A division, discount factor, debt subtraction or display conversion each becomes a saved record. They are not 326 independent valuation models. [Final answer, sections 2–10](../../data/granges-codex/runs/20261101-full/answer.md).

Of the 326 records, **82 only convert SEK into a count of million-SEK units** for presentation, and **one is a valid unit-check multiplication** duplicating bear EBIT. The conversion does not change a valuation assumption. For example, dividing SEK 22,656,000,000 by the saved one-million-SEK display unit produces 22,656 displayed million-SEK units. [Answer, Technical appendix: Unit audit example](../../data/granges-codex/runs/20261101-full/answer.md), calculations `calc:09fe2a5a5d6705162621` and `calc:cf7aef916766119133b5`.

Individual results are in base units. The report’s MSEK table displays and percentage formatting should not be read as extra forecasts. The separate arithmetic check reproduced all 326 records and checked 919 operands, but that establishes arithmetic/source-value consistency rather than economic forecast accuracy. [Verification result](../../data/granges-codex/runs/20261101-full/calculation-verification.json).

## Groups and their uses

| Group | Count | Why it exists | Final-report location |
|---|---:|---|---|
| Historical growth and sales drivers | 9 | Tests what changed in physical sales, earnings and revenue, including the FX/component bridge. It informs the operating narrative rather than mechanically producing a target price. | [Answer sections 2–3](../../data/granges-codex/runs/20261101-full/answer.md) |
| Accounting, cash-flow, debt and EPS reconciliation | 31 | Checks definitions and source consistency before selecting valuation inputs: statutory versus company cash flow, reported versus adjusted earnings, debt boundaries and share denominators. | [Answer sections 2,6–7](../../data/granges-codex/runs/20261101-full/answer.md) |
| Recycling denominator | 1 | Checks that 300 ktonnes of recycled aluminium divided by 665 ktonnes of total inputs is consistent with the disclosed recycling percentage. It supports the ESG narrative. | [Answer section 5](../../data/granges-codex/runs/20261101-full/answer.md) |
| Current market valuation and provider conventions | 24 | Establishes current market capitalization and multiples; checks daily-price averages and the provider EV/share conventions. It prevents mixing dates, definitions and EV claim boundaries. | [Answer sections 7–8](../../data/granges-codex/runs/20261101-full/answer.md) |
| Shared discount, dividends and proxy setup | 11 | Builds reusable discount factors, the interim-dividend present value, dividend cash cost, NCI book proxy and annualization exponent. These are shared steps, not separate company valuations. | [Answer section 9](../../data/granges-codex/runs/20261101-full/answer.md) |
| Operating forecasts, cash retention and leverage | 36 | Turns scenario volume and profit per tonne into EBIT, tests growth/utilization, rolls retained cash into financial debt and checks forecast leverage. Cash retention itself remains an explicit assumption. | [Answer section 9, Assumptions and Cash conversion](../../data/granges-codex/runs/20261101-full/answer.md) |
| EV/EBIT valuation and equity bridge | 50 | Applies the EV/EBIT multiple, subtracts debt-like and minority claims, divides by shares, discounts future equity and adds interim dividends. It includes an earlier bridge and its pension-adjusted replacement. | [Answer section 9, Full bridge and Future targets](../../data/granges-codex/runs/20261101-full/answer.md) |
| EBITDA valuation cross-check | 30 | Adds assumed D&A to forecast EBIT, applies EV/EBITDA and uses the same equity/dividend bridge. This checks consistency but shares the main model’s operating and cash assumptions. | [Answer section 9, EBITDA cross-check](../../data/granges-codex/runs/20261101-full/answer.md) |
| Sensitivity tests | 44 | Tests how the result responds to the multiple, EBIT, net debt, NCI, leases, pensions, dilution and an 8%/12% required return. Earlier price-sensitive outputs are replaced after the pension addition. | [Answer section 10](../../data/granges-codex/runs/20261101-full/answer.md) |
| Reverse market-expectations test | 7 | Works backward from the observed price to the future EBIT required under the chosen multiple, debt bridge, dividends and equity-return hurdle. The final answer is about 2,572 MSEK of 2029 EBIT. | [Answer section 10, What the market price requires](../../data/granges-codex/runs/20261101-full/answer.md) |
| Units and presentation | 83 | Contains 82 divisions by a saved one-million-SEK presentation unit and one valid multiplication probe duplicating bear EBIT. These are audit/presentation steps rather than 83 new economic assumptions. | [Answer section 1 and Technical appendix, Unit audit example](../../data/granges-codex/runs/20261101-full/answer.md) |
| **Total** | **326** | Each record appears in one group. | |

## The main valuation chain

For each bear/base/bull case, the chain is:

1. Forecast volume × EBIT per tonne → future EBIT.
2. Future EBIT × selected EV/EBIT → operating enterprise value.
3. Starting financial net debt − three years of retained cash → future financial net debt. Retained cash is assumed after common dividends, tax, interest, minority distributions, capex and working capital.
4. Enterprise value − future financial net debt − leases − pension proxy − NCI proxy + separately valued non-operating assets → parent common equity.
5. Parent common equity ÷ selected share count → November 2029 target per share.
6. Discount that target at the 10% assumed equity required return and add separately discounted interim dividends → value today.

The final base case is 700 ktonnes × 3,600 SEK/tonne = 2,520 MSEK EBIT; 11× gives 27,720 MSEK EV. After 5,064 MSEK of claims, common equity is 22,656 MSEK. The future target is 212.54 SEK/share; its discounted equity component is 159.69, plus 8.46 dividend PV, giving 168.14 today using the unrounded amounts. Displayed rounded components can sum to a different last decimal. These numbers come from the saved model; the cash, multiple and operating assumptions remain judgments. [Answer section 9](../../data/granges-codex/runs/20261101-full/answer.md), calculations `calc:c1d73916d19848baa375`, `calc:09fe2a5a5d6705162621`, `calc:ec089d26955fb8159230`, `calc:791e2ac113fabdd105dc`.

The EBITDA cross-check changes the earnings metric and multiple but shares the main model’s business forecasts, debt, ownership proxies and dividends. It is a cross-check, not independent confirmation. [Answer section 9, EBITDA cross-check](../../data/granges-codex/runs/20261101-full/answer.md).

The reverse test starts at the saved 172.20 SEK price and solves backward for the 2029 EBIT needed under those assumptions: about 2,572 MSEK at 11×. It is a reverse operating-expectations test, not a cash-flow DCF with a full FCFF forecast, WACC and terminal growth model. [Answer section 10](../../data/granges-codex/runs/20261101-full/answer.md); the [frozen prompt, Valuation deliverable](../../data/granges-codex/packet-20261101/prompt.md) requested EV/EBIT scenarios.

## Which calculations support the final answer?

Every ID in the final answer was matched exactly, and the saved calculation-to-calculation inputs were followed backward. The graph gives:

- **77 directly cited** calculations.
- **81 additional upstream dependencies** needed to produce those cited calculations.
- **168 other saved calculations**, outside that literal final-citation graph.

The last group includes additional supporting checks, display conversions, duplicate diagnostic work and superseded outputs. It must not be equated with 168 wrong or unused calculations. A table can use a rounded display without mentioning its own conversion ID. Conversely, a cited result can rely on several uncited intermediate calculations. The graph measures explicit traceability, not everything the analyst considered. [Final answer](../../data/granges-codex/runs/20261101-full/answer.md), exact IDs and saved `inputs` arrays in [calculations](../../data/granges-codex/runs/20261101-full/calculations.json).

Two preserved working-history examples matter:

- **Misleading early gross-income label:** record 4 subtracts provider gross income of 8,354 MSEK from sales of 28,362 MSEK and returns 20,008 MSEK, which is materials. Its label calls this gross income. The selected final result is record 17, `calc:cab3205c8b46e1e4204b`, correctly 8,354 MSEK. The early record is outside the final citation graph. [Answer section 2](../../data/granges-codex/runs/20261101-full/answer.md).
- **First-pass pension omission:** the initial scenario bridge included financial debt, leases and NCI. A later source read added the separately disclosed pension proxy. Updated records 205–258 produce the selected final targets/current ratios; earlier per-share values remain in the audit. Some first-pass operations, such as EBIT, EV and debt forecasts, remain valid upstream steps because pensions do not change them. [Answer sections 7,9–10](../../data/granges-codex/runs/20261101-full/answer.md).

## What the calculations leave to judgment

The count does not make the scenario probabilities, future operating assumptions or exit multiples statistically established. The run assumed 620/700/760 ktonnes, 2,700/3,600/4,200 SEK EBIT per tonne, 8×/11×/12× EV/EBIT and annual retained cash of −350/+350/+650 MSEK after common dividends. It did not derive a calibrated probability distribution. The answer explicitly describes the outputs as conditional and not probability weighted. [Answer, Executive assessment and section 9](../../data/granges-codex/runs/20261101-full/answer.md).

The 44 sensitivity steps show how values respond when inputs change. Sensitivity is not probability: a severe bear outcome can have a large impact without the model establishing its likelihood. Selecting probabilities is a separate decision requiring defined scenario meanings and evidence.

## Complete calculation catalogue

Rows retain the original saved labels so every entry can be found in the existing explorer. **Cited** means an exact ID is present in the answer; **Upstream** means an uncited ancestor of a cited ID; **Other working/support** means outside that literal graph. “Superseded” identifies particular earlier valuations replaced by the pension-inclusive bridge, rather than declaring every uncited result obsolete. All purposes below are interpretations of the recorded operations and input references, not new valuations.

### Historical growth and sales drivers — 9

Tests what changed in physical sales, earnings and revenue, including the FX/component bridge. It informs the operating narrative rather than mechanically producing a target price.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 1 | `calc:d7bfee43f83bffe2d195` | Cumulative volume growth 2021–2025 | Measures cumulative physical-volume growth over 2021–2025. | Cited |
| 2 | `calc:e60a3123d4d5fd94a912` | Cumulative adjusted EBIT growth 2021–2025 | Measures cumulative adjusted-EBIT growth over 2021–2025. | Cited |
| 3 | `calc:194e6b0b91e429630f81` | 2022 sales increase | Measures the change in 2022 reported net sales. | Cited |
| 5 | `calc:54ca709da14f20003f80` | 2022 sales growth excluding disclosed FX, unallocated remainder | Removes disclosed FX from the sales change; the remainder is deliberately unallocated. | Cited |
| 281 | `calc:0d92d7b8029f03d091d0` | 2022 minus 2021 fabrication revenue component | Measures the change in fabrication revenue. | Cited |
| 282 | `calc:860a6e77a66474725268` | 2022 minus 2021 raw revenue component | Measures the change in raw-material/other revenue. | Cited |
| 283 | `calc:30257162852a50d55274` | 2022 minus 2021 other revenue component | Measures the change in other revenue. | Cited |
| 284 | `calc:1682a6303df18531b18f` | Sum of displayed 2022 revenue component changes | Adds the displayed revenue-component changes. | Upstream |
| 285 | `calc:84d5ab89bc804a377623` | Revenue component bridge residual versus total sales change | Measures their residual against the total sales change. | Cited |

### Accounting, cash-flow, debt and EPS reconciliation — 31

Checks definitions and source consistency before selecting valuation inputs: statutory versus company cash flow, reported versus adjusted earnings, debt boundaries and share denominators.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 4 | `calc:a8600d09170d56ab1671` | 2025 gross-income subtotal: sales less materials | Computes sales less the provider gross-income subtotal; the saved label is misleading. This returns materials of 20,008 MSEK, not final gross income. | Other working/support |
| 6 | `calc:d8eb85458e299583d45f` | q1_line_ocf | Reconstructs Q1 company operating cash flow from operating lines. | Other working/support |
| 7 | `calc:378128d33538aeda48b8` | q1_cfo_to_apm | Reconstructs Q1 company cash flow from statutory CFO, tax and capex. | Cited |
| 8 | `calc:102f307391b62221a750` | q1_provider_fcf | Checks provider Q1 FCF as statutory CFO plus investing cash flow. | Cited |
| 9 | `calc:6068f857628f8e18a3dc` | q3_reported_plus_adjustment | Adds Q3 reported EBIT and the displayed adjustment. | Cited |
| 10 | `calc:cee05c92877f046634f9` | ytd_reported_plus_adjustment | Adds year-to-date reported EBIT and its adjustment. | Cited |
| 11 | `calc:cf16049539a4006127af` | r12_reported_plus_adjustment | Adds R12 reported EBIT and its adjustment. | Cited |
| 12 | `calc:74c7040559e3662b5c58` | q3_adj_ebit_plus_da | Checks Q3 adjusted EBIT plus displayed D&A against adjusted EBITDA. | Cited |
| 13 | `calc:16aad27c82982a9ccea8` | r12_adj_ebit_plus_da | Checks the R12 adjusted-EBITDA bridge. | Cited |
| 14 | `calc:0ce2d9376fd0bb279a6a` | r12_da_difference | Measures the 8 MSEK difference between the two D&A/impairment measures. | Cited |
| 15 | `calc:a1000d02e40b2d9cf8d7` | r12_quarter_cfo_sum | Sums four quarter CFO values to compare with provider R12 CFO. | Cited |
| 17 | `calc:cab3205c8b46e1e4204b` | materials_reconciliation25 | Computes the final gross-income subtotal: sales less materials, 8,354 MSEK. | Cited |
| 18 | `calc:dedace3b7e1148540252` | q1_apm_residual | Measures the Q1 reconstructed/published cash-flow residual. | Cited |
| 19 | `calc:5880adede4f35e4d025a` | q3_ebit_residual | Measures the Q3 displayed adjusted-EBIT residual. | Other working/support |
| 20 | `calc:a5bb2ab0cae5834d96dd` | r12_ebit_residual | Measures the R12 displayed adjusted-EBIT residual. | Other working/support |
| 21 | `calc:ae48b7c4e626ba5b7196` | debt_gross_less_cash | Subtracts cash from gross interest-bearing debt before lease removal. | Upstream |
| 22 | `calc:caf111a2026b85ba88d4` | cfo_annual_plus_ytd | Adds annual CFO and current year-to-date CFO before rolling out the prior year-to-date. | Upstream |
| 23 | `calc:7350ccac46d9a8198b95` | q3_cfo_reverse_tax | Reverses Q3 cash taxes from statutory CFO before capex deduction. | Upstream |
| 24 | `calc:a19aff96647aa07c7815` | 2025_provider_fcf_check | Checks FY2025 provider FCF as CFO plus investing cash flow. | Cited |
| 25 | `calc:290d5346a09c007272d1` | q3_provider_fcf_check | Checks Q3 provider FCF as CFO plus investing cash flow. | Cited |
| 26 | `calc:209db6c2c37959313b02` | debt_bridge_excluding_leases | Removes cash and leases from gross debt; preserves the 1 MSEK difference to the issuer APM. | Cited |
| 27 | `calc:ad96c63b0f6febaf4705` | cfo_annual_roll | Builds an alternative R12 CFO roll from annual/cumulative figures; retains its rounding difference. | Cited |
| 28 | `calc:ef06103ad0af09a1a2ca` | q3_cfo_to_company_ocf | Reconciles Q3 statutory CFO to company operating cash flow. | Cited |
| 276 | `calc:991963a2c1273cf478c9` | Historical financial debt plus leases and pensions 2021 | Adds financial net debt, leases and pensions for the 2021 provider-basis check. | Cited |
| 277 | `calc:583b26ceee9eea1081a9` | Historical financial debt plus leases and pensions 2022 | Repeats that provider-basis check for 2022. | Cited |
| 278 | `calc:1826c934d6e307a3667b` | Historical financial debt plus leases and pensions 2023 | Repeats that provider-basis check for 2023. | Cited |
| 279 | `calc:ee90c372dadf7a9474ef` | Historical financial debt plus leases and pensions 2024 | Repeats that provider-basis check for 2024; retains the 1 MSEK residual. | Cited |
| 280 | `calc:b4dd320220036268f60c` | Provider EBITDA identity: R12 reported EBIT plus APM D&A | Checks provider EBITDA as reported EBIT plus the issuer’s APM D&A. | Cited |
| 286 | `calc:b505e3f939321910c324` | API versus issued share count difference percent | Quantifies the provider-versus-issued share-count difference. | Cited |
| 287 | `calc:6157c58e92d3b9e2d0bf` | Q3 profit divided by provider shares | Tests EPS using the provider share count and rounded parent profit. | Cited |
| 288 | `calc:8fc34f62e714bb7648a5` | Q3 profit divided by basic weighted shares | Tests EPS using basic weighted shares and the same rounded profit. | Cited |

### Recycling denominator — 1

Checks that 300 ktonnes of recycled aluminium divided by 665 ktonnes of total inputs is consistent with the disclosed recycling percentage. It supports the ESG narrative.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 16 | `calc:8be4048b7f05f6ea50fa` | recycled_input_ratio25 | Checks recycled inputs divided by total metal inputs. | Cited |

### Current market valuation and provider conventions — 24

Establishes current market capitalization and multiples; checks daily-price averages and the provider EV/share conventions. It prevents mixing dates, definitions and EV claim boundaries.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 29 | `calc:4fd134f4e9b7cd5fdb21` | current_market_cap | Multiplies the dated price by selected issued shares. | Cited |
| 30 | `calc:69f2c42d9bf3bd60510b` | current_reported_pe | Divides price by issuer diluted R12 EPS. | Cited |
| 31 | `calc:16ddefb0c7d1e2e9a887` | current_EV_lease_NCI_excluded | Adds financial net debt to market capitalization on the observed provider convention. | Upstream |
| 32 | `calc:5c373d87543af927f16d` | current_EV_including_leases_and_NCI_book_proxy | Adds leases and NCI to the initial EV bridge, before the later pension addition. | Upstream |
| 33 | `calc:e5241672e14f6f37a7ff` | current_provider_convention_EV_reported_EBIT | Divides provider-convention EV by reported EBIT. | Other working/support |
| 34 | `calc:6607667073e8fdedddff` | current_provider_convention_EV_adjusted_EBIT | Divides provider-convention EV by adjusted EBIT. | Other working/support |
| 35 | `calc:541d55b4f995ea21983d` | current_full_EV_reported_EBIT | Divides the initial EV including leases/NCI by reported EBIT; later updated for pensions. | Other working/support |
| 36 | `calc:1f2d446a1f233fa534e3` | current_full_EV_adjusted_EBIT | Divides the initial EV including leases/NCI by adjusted EBIT; later updated for pensions. | Other working/support |
| 37 | `calc:bbaf11509c97abe5b8b3` | current_full_EV_adjusted_EBITDA | Divides the initial EV including leases/NCI by adjusted EBITDA; later updated for pensions. | Other working/support |
| 38 | `calc:ca592cf1af4a9dd9c66f` | Sum of 2025 daily closes part 0 | Adds the first batch of 2025 daily closes. | Upstream |
| 39 | `calc:eac4792d0de7a1c8d158` | Sum of 2025 daily closes part 100 | Adds the second batch of 2025 daily closes. | Upstream |
| 40 | `calc:1eda3e25d590a4a911ca` | Sum of 2025 daily closes part 200 | Adds the final batch of 2025 daily closes. | Upstream |
| 41 | `calc:712881657f5c5e2443b3` | Sum of all 2025 daily closes | Combines the three daily-close subtotals. | Upstream |
| 42 | `calc:8a1c46fd0caf460d4a6b` | Arithmetic mean of 2025 daily closes | Divides the close sum by 249 observations to test the annual-average label. | Cited |
| 255 | `calc:ed644041ef6fd7c0bf52` | Current full EV including pension proxy | Adds pensions to the final current EV convention. | Cited |
| 256 | `calc:c1005fed82ddbe84e7f5` | Current full EV including pension to reported EBIT | Divides pension-inclusive current EV by reported EBIT. | Cited |
| 257 | `calc:1be3ab63a0f0cfc8faea` | Current full EV including pension to adjusted EBIT | Divides pension-inclusive current EV by adjusted EBIT. | Cited |
| 258 | `calc:eeb90a1b9f6af2791c0c` | Current full EV including pension to adjusted EBITDA | Divides pension-inclusive current EV by adjusted EBITDA. | Cited |
| 321 | `calc:c8cfdbfec79efbf91d63` | Provider latest EV divided by reported EBIT | Checks the latest provider EV/reported-EBIT ratio against the saved ratio series. | Cited |
| 322 | `calc:0f658d0d6b2a8b2771b2` | Provider latest EV less market cap under explicit SEK proxies | Subtracts latest provider market cap from provider EV under explicit SEK unit proxies. | Cited |
| 323 | `calc:34b78a53446e812ef206` | Provider annual2025 EV less market cap under explicit SEK proxies | Repeats that EV-minus-market-cap convention test for FY2025. | Cited |
| 324 | `calc:08d3bf8f3c9fa5c101da` | Provider latest market cap implied shares under explicit currency proxy | Infers shares from latest provider market cap divided by price. | Other working/support |
| 325 | `calc:390acc0bad355804c651` | Provider annual2025 market cap implied report-date shares | Infers FY2025 report-date shares from market cap divided by its dated price. | Other working/support |
| 326 | `calc:90212df77c4bddf9f48a` | Provider annual2025 EV divided by reported EBIT | Checks FY2025 provider EV divided by reported EBIT. | Other working/support |

### Shared discount, dividends and proxy setup — 11

Builds reusable discount factors, the interim-dividend present value, dividend cash cost, NCI book proxy and annualization exponent. These are shared steps, not separate company valuations.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 43 | `calc:3a25b339288352bd6798` | Annual discount factor | Forms one plus the 10% required return. | Upstream |
| 44 | `calc:77382694d8cd8079abfe` | Discount factor year 1 | Raises the discount factor to year one. | Upstream |
| 45 | `calc:d91aa664af3039b04705` | PV dividend year 1 | Discounts the first modeled dividend. | Upstream |
| 46 | `calc:5c21868c194a4f61c7e0` | Discount factor year 2 | Raises the discount factor to year two. | Upstream |
| 47 | `calc:7dbc4e90a7973f7f51a5` | PV dividend year 2 | Discounts the second modeled dividend. | Upstream |
| 48 | `calc:5b5e8771db42c61bec26` | Discount factor year 3 | Raises the discount factor to year three. | Upstream |
| 49 | `calc:ba48c634cb4d3eeb0a76` | PV dividend year 3 | Discounts the third modeled dividend. | Upstream |
| 50 | `calc:9594afb64913fcb82adf` | PV all interim dividends | Sums the three discounted interim dividends. | Cited |
| 51 | `calc:1838cb7dc2d3bc270b97` | Assumed minority fair value at book proxy | Applies the selected 1× book-value proxy to NCI equity. | Upstream |
| 52 | `calc:9d52c7236522b8477c0e` | Annual common dividends in cash | Converts the 3.40 SEK dividend per share into total annual common-dividend cash. | Cited |
| 53 | `calc:95a6812dc2bf77bd812a` | CAGR exponent for three years | Builds the one-third exponent for three-year CAGR. | Other working/support |

### Operating forecasts, cash retention and leverage — 36

Turns scenario volume and profit per tonne into EBIT, tests growth/utilization, rolls retained cash into financial debt and checks forecast leverage. Cash retention itself remains an explicit assumption.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 56 | `calc:28c7df5807db01f39b34` | bear EBIT | Bear: multiplies forecast physical volume by EBIT per tonne. | Upstream |
| 58 | `calc:496194d5192d805f1a3d` | bear cumulative debt reduction | Bear: totals three years of assumed cash retained after dividends. | Upstream |
| 59 | `calc:36b881d5bdf7df2fc432` | bear future financial net debt | Bear: subtracts retained cash from starting financial net debt. | Cited |
| 67 | `calc:e11c16b113e600b7274e` | bear utilization | Bear: compares forecast volume with the 800-ktonne capacity reference. | Other working/support |
| 68 | `calc:14848da2bf355b6247fc` | bear EBIT future current ratio | Bear: divides forecast EBIT by current adjusted R12 EBIT. | Other working/support |
| 69 | `calc:959ed209668acc013146` | bear EBIT CAGR factor | Bear: takes the cube root of that earnings ratio. | Other working/support |
| 70 | `calc:173ce0a5c57cecdc2658` | bear EBIT CAGR | Bear: subtracts one to obtain annualized EBIT growth. | Other working/support |
| 71 | `calc:869e9d6a684a1824a5ec` | bear volume future current ratio | Bear: divides forecast volume by current volume. | Other working/support |
| 72 | `calc:9337db1321cfc95c3012` | bear volume CAGR factor | Bear: takes the cube root of that volume ratio. | Other working/support |
| 73 | `calc:50fd9a2c8fc0e56c9efc` | bear volume CAGR | Bear: subtracts one to obtain annualized volume growth. | Other working/support |
| 74 | `calc:3957bd0841e630d6a7ee` | bear annual equity cash before common dividend | Bear: adds common dividends back to retained cash to expose assumed pre-common-dividend cash generation. | Cited |
| 81 | `calc:4ee9d7a33bcab41b8716` | base EBIT | Base: multiplies forecast physical volume by EBIT per tonne. | Upstream |
| 83 | `calc:6a1ded8fd9fe956f70a4` | base cumulative debt reduction | Base: totals three years of assumed cash retained after dividends. | Upstream |
| 84 | `calc:4b5dac7ddf9ecb6cf3a8` | base future financial net debt | Base: subtracts retained cash from starting financial net debt. | Cited |
| 92 | `calc:d19985603a72bab53347` | base utilization | Base: compares forecast volume with the 800-ktonne capacity reference. | Other working/support |
| 93 | `calc:0c83e5a779a1b2c3c20e` | base EBIT future current ratio | Base: divides forecast EBIT by current adjusted R12 EBIT. | Other working/support |
| 94 | `calc:2ed26c69d659a7814f47` | base EBIT CAGR factor | Base: takes the cube root of that earnings ratio. | Other working/support |
| 95 | `calc:01eb6e6d191edea2b441` | base EBIT CAGR | Base: subtracts one to obtain annualized EBIT growth. | Other working/support |
| 96 | `calc:d17d384064a64d8a3780` | base volume future current ratio | Base: divides forecast volume by current volume. | Other working/support |
| 97 | `calc:4e1b3d05402b0a943462` | base volume CAGR factor | Base: takes the cube root of that volume ratio. | Other working/support |
| 98 | `calc:14a269bf1b171e8491ff` | base volume CAGR | Base: subtracts one to obtain annualized volume growth. | Other working/support |
| 99 | `calc:cb47d38619329373c72a` | base annual equity cash before common dividend | Base: adds common dividends back to retained cash to expose assumed pre-common-dividend cash generation. | Cited |
| 106 | `calc:8a8725b9e33339889549` | bull EBIT | Bull: multiplies forecast physical volume by EBIT per tonne. | Upstream |
| 108 | `calc:41f501af492761a00a54` | bull cumulative debt reduction | Bull: totals three years of assumed cash retained after dividends. | Upstream |
| 109 | `calc:b1922f11caa9e12c20e3` | bull future financial net debt | Bull: subtracts retained cash from starting financial net debt. | Cited |
| 117 | `calc:300efbeb6dc399a8d829` | bull utilization | Bull: compares forecast volume with the 800-ktonne capacity reference. | Other working/support |
| 118 | `calc:7f4b8e2900c7d5382ea5` | bull EBIT future current ratio | Bull: divides forecast EBIT by current adjusted R12 EBIT. | Other working/support |
| 119 | `calc:0cf896f5cad7f5aa60fb` | bull EBIT CAGR factor | Bull: takes the cube root of that earnings ratio. | Other working/support |
| 120 | `calc:7b1fa9c48c7c617ef274` | bull EBIT CAGR | Bull: subtracts one to obtain annualized EBIT growth. | Other working/support |
| 121 | `calc:b8fa5eb66e48aaf0f430` | bull volume future current ratio | Bull: divides forecast volume by current volume. | Other working/support |
| 122 | `calc:ca39ef3177c4200f2e5f` | bull volume CAGR factor | Bull: takes the cube root of that volume ratio. | Other working/support |
| 123 | `calc:84a42406b1bd953f75d2` | bull volume CAGR | Bull: subtracts one to obtain annualized volume growth. | Other working/support |
| 124 | `calc:31a18ba6d11fe17c8f96` | bull annual equity cash before common dividend | Bull: adds common dividends back to retained cash to expose assumed pre-common-dividend cash generation. | Cited |
| 213 | `calc:a454e37fe54ffc6ee490` | bear forecast issuer leverage | Bear: divides future financial debt by forecast EBITDA to test issuer leverage. | Other working/support |
| 226 | `calc:88634fe4053012480bdb` | base forecast issuer leverage | Base: divides future financial debt by forecast EBITDA to test issuer leverage. | Other working/support |
| 239 | `calc:f98da26d0ecc4f6665f5` | bull forecast issuer leverage | Bull: divides future financial debt by forecast EBITDA to test issuer leverage. | Other working/support |

### EV/EBIT valuation and equity bridge — 50

Applies the EV/EBIT multiple, subtracts debt-like and minority claims, divides by shares, discounts future equity and adds interim dividends. It includes an earlier bridge and its pension-adjusted replacement.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 57 | `calc:062d981365426b89e1f3` | bear operating EV | Bear: multiplies forecast EBIT by the selected EV/EBIT. | Cited |
| 60 | `calc:8a77bd6bf719ad500d24` | bear equity bridge deductions | Bear: adds initial future financial debt, leases and the NCI proxy; pension omitted in this first pass. | Other working/support |
| 61 | `calc:324eb3b9b0ce9c415a2d` | bear parent common equity | Bear: subtracts initial claims from EV; superseded by the pension-inclusive bridge. | Other working/support |
| 62 | `calc:a81ee9367d16759ff087` | bear future value per share | Bear: divides initial common equity by shares; superseded. | Other working/support |
| 63 | `calc:4e4bfa4b7b60215ba995` | bear PV terminal equity per share | Bear: discounts the initial target; superseded. | Other working/support |
| 64 | `calc:8d78cd7c0799f096dc0b` | bear present value including dividends | Bear: adds dividend PV to the initial discounted target; superseded. | Other working/support |
| 65 | `calc:aee384ab080a5bda2856` | bear present valuation gap percent | Bear: compares the initial PV with the observed price; superseded. | Other working/support |
| 66 | `calc:47aa66518b40834ca01d` | bear future target price change percent | Bear: compares the initial future target with price; superseded. | Other working/support |
| 82 | `calc:c1d73916d19848baa375` | base operating EV | Base: multiplies forecast EBIT by the selected EV/EBIT. | Cited |
| 85 | `calc:b93ad9d9f77443dd8f51` | base equity bridge deductions | Base: adds initial future financial debt, leases and the NCI proxy; pension omitted in this first pass. | Other working/support |
| 86 | `calc:bb72bbb8dd03106dbfea` | base parent common equity | Base: subtracts initial claims from EV; superseded by the pension-inclusive bridge. | Other working/support |
| 87 | `calc:c2cd75c2b856c15fa9dd` | base future value per share | Base: divides initial common equity by shares; superseded. | Other working/support |
| 88 | `calc:d1aeb025c58784eb2de4` | base PV terminal equity per share | Base: discounts the initial target; superseded. | Other working/support |
| 89 | `calc:4150523f4a0cdee8b57b` | base present value including dividends | Base: adds dividend PV to the initial discounted target; superseded. | Other working/support |
| 90 | `calc:f7e71cf595accbd25093` | base present valuation gap percent | Base: compares the initial PV with the observed price; superseded. | Other working/support |
| 91 | `calc:09828714c5aecc2d5416` | base future target price change percent | Base: compares the initial future target with price; superseded. | Other working/support |
| 107 | `calc:5b6dab576fcf28d490ec` | bull operating EV | Bull: multiplies forecast EBIT by the selected EV/EBIT. | Cited |
| 110 | `calc:fac4c1fb9b1476c412d9` | bull equity bridge deductions | Bull: adds initial future financial debt, leases and the NCI proxy; pension omitted in this first pass. | Other working/support |
| 111 | `calc:862282afdac6773619ec` | bull parent common equity | Bull: subtracts initial claims from EV; superseded by the pension-inclusive bridge. | Other working/support |
| 112 | `calc:583fd174cb431c781806` | bull future value per share | Bull: divides initial common equity by shares; superseded. | Other working/support |
| 113 | `calc:a4755471801fb02d942a` | bull PV terminal equity per share | Bull: discounts the initial target; superseded. | Other working/support |
| 114 | `calc:36c1cd8e2613f05b68b6` | bull present value including dividends | Bull: adds dividend PV to the initial discounted target; superseded. | Other working/support |
| 115 | `calc:b654e93f7a066f46e62d` | bull present valuation gap percent | Bull: compares the initial PV with the observed price; superseded. | Other working/support |
| 116 | `calc:8ef4ec62788eef5121a1` | bull future target price change percent | Bull: compares the initial future target with price; superseded. | Other working/support |
| 203 | `calc:2b21810326e757e9a44b` | Forecast pension debt-like proxy | Holds the separately identified pension proxy at 229 MSEK through the horizon. | Upstream |
| 204 | `calc:e43354e7d9ad0d4c2aca` | Forecast lease liability proxy | Holds lease liabilities at 247 MSEK through the horizon. | Upstream |
| 205 | `calc:936ade4d34036442c3f4` | bear final bridge deductions | Bear: sums future financial net debt, leases, pension proxy and NCI proxy. | Upstream |
| 206 | `calc:21d1a73cef304ed1c193` | bear final equity before other assets | Bear: subtracts those claims from EBIT-based EV. | Upstream |
| 207 | `calc:9bfc82253aa56dda7729` | bear final common equity | Bear: adds the explicitly zero separately valued non-operating assets. | Cited |
| 208 | `calc:58483a4265ad1711632e` | bear final future target per share | Bear: divides final common equity by selected shares. | Cited |
| 209 | `calc:2b170d16ddca9c353ff7` | bear final terminal PV | Bear: discounts the final future target at 10%. | Upstream |
| 210 | `calc:44251337e56efb345589` | bear final present value | Bear: adds the modeled interim-dividend PV for value today. | Cited |
| 211 | `calc:61d800669b94d6fef036` | bear final present gap | Bear: compares final present value with the observed price. | Other working/support |
| 212 | `calc:f4e9ea92013f40ec2bdd` | bear final future price change | Bear: compares final future target with the observed price. | Other working/support |
| 218 | `calc:d15460b7fa5b9a88cc46` | base final bridge deductions | Base: sums future financial net debt, leases, pension proxy and NCI proxy. | Upstream |
| 219 | `calc:efad5b53c5db7a6f7ec9` | base final equity before other assets | Base: subtracts those claims from EBIT-based EV. | Upstream |
| 220 | `calc:09fe2a5a5d6705162621` | base final common equity | Base: adds the explicitly zero separately valued non-operating assets. | Cited |
| 221 | `calc:ec089d26955fb8159230` | base final future target per share | Base: divides final common equity by selected shares. | Cited |
| 222 | `calc:82409fe9ee34dcd844bf` | base final terminal PV | Base: discounts the final future target at 10%. | Upstream |
| 223 | `calc:791e2ac113fabdd105dc` | base final present value | Base: adds the modeled interim-dividend PV for value today. | Cited |
| 224 | `calc:4b540ccab7aedab897ee` | base final present gap | Base: compares final present value with the observed price. | Other working/support |
| 225 | `calc:4f58cc1f796d6f87ac4a` | base final future price change | Base: compares final future target with the observed price. | Other working/support |
| 231 | `calc:a54a195cf1bcd41a2971` | bull final bridge deductions | Bull: sums future financial net debt, leases, pension proxy and NCI proxy. | Upstream |
| 232 | `calc:28e418e0a1b2d859c564` | bull final equity before other assets | Bull: subtracts those claims from EBIT-based EV. | Upstream |
| 233 | `calc:7d8ba596400d170dfc53` | bull final common equity | Bull: adds the explicitly zero separately valued non-operating assets. | Cited |
| 234 | `calc:8bb04786888b2fb17641` | bull final future target per share | Bull: divides final common equity by selected shares. | Cited |
| 235 | `calc:de5304cc10f4f7f3f8c5` | bull final terminal PV | Bull: discounts the final future target at 10%. | Upstream |
| 236 | `calc:9e9577bc76984e4d0163` | bull final present value | Bull: adds the modeled interim-dividend PV for value today. | Cited |
| 237 | `calc:0655aaa4c9c7d75bc015` | bull final present gap | Bull: compares final present value with the observed price. | Other working/support |
| 238 | `calc:f03a09d8f75196a28bd8` | bull final future price change | Bull: compares final future target with the observed price. | Other working/support |

### EBITDA valuation cross-check — 30

Adds assumed D&A to forecast EBIT, applies EV/EBITDA and uses the same equity/dividend bridge. This checks consistency but shares the main model’s operating and cash assumptions.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 75 | `calc:17211e306d2150f3cb1d` | bear normalized EBITDA | Bear: adds assumed D&A to forecast EBIT. | Upstream |
| 76 | `calc:b94c21530a558583fc02` | bear EBITDA crosscheck EV | Bear: applies the chosen EV/EBITDA cross-check multiple. | Upstream |
| 77 | `calc:c9410f04f287db55abec` | bear EBITDA crosscheck equity | Bear: subtracts the initial claim bridge from EBITDA-based EV; superseded. | Other working/support |
| 78 | `calc:e910523a31aea7501b1c` | bear EBITDA crosscheck future per share | Bear: divides initial EBITDA-based equity by shares; superseded. | Other working/support |
| 79 | `calc:ddfb7c88ba45e2c95146` | bear EBITDA crosscheck PV terminal | Bear: discounts the initial EBITDA-based target; superseded. | Other working/support |
| 80 | `calc:de3225b086c210313dd5` | bear EBITDA crosscheck present including dividends | Bear: adds dividends to the initial EBITDA cross-check; superseded. | Other working/support |
| 100 | `calc:76b63cb90fab9d1e0261` | base normalized EBITDA | Base: adds assumed D&A to forecast EBIT. | Upstream |
| 101 | `calc:45b4117816af8b3d442b` | base EBITDA crosscheck EV | Base: applies the chosen EV/EBITDA cross-check multiple. | Upstream |
| 102 | `calc:779165a2e4258e0cb975` | base EBITDA crosscheck equity | Base: subtracts the initial claim bridge from EBITDA-based EV; superseded. | Other working/support |
| 103 | `calc:eb83546b0171a8c31ea3` | base EBITDA crosscheck future per share | Base: divides initial EBITDA-based equity by shares; superseded. | Other working/support |
| 104 | `calc:115d97d4eb5315613296` | base EBITDA crosscheck PV terminal | Base: discounts the initial EBITDA-based target; superseded. | Other working/support |
| 105 | `calc:9b43f32ad12b2d7fe765` | base EBITDA crosscheck present including dividends | Base: adds dividends to the initial EBITDA cross-check; superseded. | Other working/support |
| 125 | `calc:cac1a86c8316a969b580` | bull normalized EBITDA | Bull: adds assumed D&A to forecast EBIT. | Upstream |
| 126 | `calc:0f5a5800a460ae9151b7` | bull EBITDA crosscheck EV | Bull: applies the chosen EV/EBITDA cross-check multiple. | Upstream |
| 127 | `calc:1572f043512991f09432` | bull EBITDA crosscheck equity | Bull: subtracts the initial claim bridge from EBITDA-based EV; superseded. | Other working/support |
| 128 | `calc:2a5677f0f67b9378bc51` | bull EBITDA crosscheck future per share | Bull: divides initial EBITDA-based equity by shares; superseded. | Other working/support |
| 129 | `calc:63da79d3a0e078ae727f` | bull EBITDA crosscheck PV terminal | Bull: discounts the initial EBITDA-based target; superseded. | Other working/support |
| 130 | `calc:c8df364c9a59373e6028` | bull EBITDA crosscheck present including dividends | Bull: adds dividends to the initial EBITDA cross-check; superseded. | Other working/support |
| 214 | `calc:b77eb71c134e6c46f87f` | bear final EBITDA crosscheck equity | Bear: subtracts final claims from EBITDA-based EV. | Upstream |
| 215 | `calc:3200ffce68bd016d5b58` | bear final EBITDA crosscheck target | Bear: divides final EBITDA-based common equity by shares. | Upstream |
| 216 | `calc:51560b498b530d9e0c73` | bear final EBITDA crosscheck terminal PV | Bear: discounts the final EBITDA-based target. | Upstream |
| 217 | `calc:c1a3d016a4f5fbcbc6f3` | bear final EBITDA crosscheck present | Bear: adds interim-dividend PV to complete the EBITDA cross-check. | Cited |
| 227 | `calc:007956ea6074328c3ff0` | base final EBITDA crosscheck equity | Base: subtracts final claims from EBITDA-based EV. | Upstream |
| 228 | `calc:57c4cdef8f0c1c2b5ec0` | base final EBITDA crosscheck target | Base: divides final EBITDA-based common equity by shares. | Upstream |
| 229 | `calc:2e020b9643afe3978faf` | base final EBITDA crosscheck terminal PV | Base: discounts the final EBITDA-based target. | Upstream |
| 230 | `calc:991d31b75b29a50ff639` | base final EBITDA crosscheck present | Base: adds interim-dividend PV to complete the EBITDA cross-check. | Cited |
| 240 | `calc:7f1fae09bb13b556837d` | bull final EBITDA crosscheck equity | Bull: subtracts final claims from EBITDA-based EV. | Upstream |
| 241 | `calc:7c9408da73f293985bea` | bull final EBITDA crosscheck target | Bull: divides final EBITDA-based common equity by shares. | Upstream |
| 242 | `calc:20e47b86bfb75911cd0f` | bull final EBITDA crosscheck terminal PV | Bull: discounts the final EBITDA-based target. | Upstream |
| 243 | `calc:96f99d1ad8a24e371aeb` | bull final EBITDA crosscheck present | Bull: adds interim-dividend PV to complete the EBITDA cross-check. | Cited |

### Sensitivity tests — 44

Tests how the result responds to the multiple, EBIT, net debt, NCI, leases, pensions, dilution and an 8%/12% required return. Earlier price-sensitive outputs are replaced after the pension addition.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 131 | `calc:2cecd1055ef8edf1ae0a` | One turn of base EBIT multiple future per share | Calculates the future per-share effect of one extra turn of base EV/EBIT. | Upstream |
| 132 | `calc:d3a921ab295f76962c06` | One turn of base EBIT multiple present per share | Discounts that one-turn multiple effect. | Cited |
| 133 | `calc:56c183d2c79b4b687129` | NCI book-value proxy increment future per share | Calculates the future per-share effect of another 651 MSEK NCI claim. | Upstream |
| 134 | `calc:a082c9d53c75c7ea6d9f` | NCI book-value proxy increment present per share | Discounts that NCI-value effect. | Cited |
| 135 | `calc:b3e4975d6fa94b671b34` | Lease amount future per share | Calculates the future per-share effect of lease liabilities. | Other working/support |
| 136 | `calc:7ee1266937a931272070` | Lease amount present per share | Discounts that lease-liability effect. | Other working/support |
| 137 | `calc:2aa324c42daccbb54659` | 500 MSEK debt change future per share | Calculates the future per-share effect of 500 MSEK more financial debt. | Upstream |
| 138 | `calc:37f48ab13f02aaba18c4` | 500 MSEK debt change present per share | Discounts that debt effect. | Cited |
| 139 | `calc:beb65fba1d205cb46244` | 100 MSEK EBIT times base multiple | Converts a 100 MSEK EBIT change into EV at the base multiple. | Upstream |
| 140 | `calc:e371ad2781b6ef05226f` | 100 MSEK EBIT future per share | Converts that EBIT/EV sensitivity into future per-share value. | Upstream |
| 141 | `calc:75d7114e5bf8b76aca15` | 100 MSEK EBIT present per share | Discounts that EBIT sensitivity. | Cited |
| 142 | `calc:d087a16647bfb02ae006` | Shares with 2 percent dilution | Increases the share denominator by 2%. | Upstream |
| 143 | `calc:9eb76bd293ec9ac20952` | Base future value at 2 percent dilution | Computes the initial base future target with 2% more shares; later updated for pensions. | Other working/support |
| 144 | `calc:ab421ebfb9d5073f400c` | Base PV terminal at 2 percent dilution | Discounts that initial diluted future target; later updated. | Other working/support |
| 145 | `calc:48ce565b6b92d81b04be` | Base present value at 2 percent dilution | Adds dividends to the initial diluted terminal PV; later updated. | Other working/support |
| 146 | `calc:74bae03a8f8ccb27cc3d` | 8 percent factor | Forms one plus the 8% required return. | Upstream |
| 147 | `calc:1567e9d7f1f02b4f60e0` | 8 percent factor 1 | Builds its year-one discount factor. | Upstream |
| 148 | `calc:e653a67c43af925e9cd5` | 8 percent dividend PV 1 | Discounts year-one dividend at 8%. | Upstream |
| 149 | `calc:f6ce13013d01df61fc07` | 8 percent factor 2 | Builds its year-two discount factor. | Upstream |
| 150 | `calc:a49e588f1aea841f9b16` | 8 percent dividend PV 2 | Discounts year-two dividend at 8%. | Upstream |
| 151 | `calc:7b4c80542a473f1e373c` | 8 percent factor 3 | Builds its year-three discount factor. | Upstream |
| 152 | `calc:127e4fe477e82cbcbcd7` | 8 percent dividend PV 3 | Discounts year-three dividend at 8%. | Upstream |
| 153 | `calc:c7a7fe1a76dbdd3bdc91` | 8 percent dividend total PV | Adds the three 8% dividend present values. | Upstream |
| 154 | `calc:8ec39c4b137da888b38e` | 8 percent base terminal PV | Discounts the initial base target at 8%; later updated for pensions. | Other working/support |
| 155 | `calc:b1fc0548be7906ef711f` | 8 percent base present value | Adds dividend PV to the initial 8% base result; later updated. | Other working/support |
| 156 | `calc:92d7ae1ec6c391db9982` | 12 percent factor | Forms one plus the 12% required return. | Upstream |
| 157 | `calc:312b978ee2b1e643435b` | 12 percent factor 1 | Builds its year-one discount factor. | Upstream |
| 158 | `calc:8a1d8f76c8818c077b82` | 12 percent dividend PV 1 | Discounts year-one dividend at 12%. | Upstream |
| 159 | `calc:1d148e46ffe978a37b5a` | 12 percent factor 2 | Builds its year-two discount factor. | Upstream |
| 160 | `calc:7a67052eac494983511d` | 12 percent dividend PV 2 | Discounts year-two dividend at 12%. | Upstream |
| 161 | `calc:a39389f12b5b026f7d26` | 12 percent factor 3 | Builds its year-three discount factor. | Upstream |
| 162 | `calc:d650f3e520bdf01ae282` | 12 percent dividend PV 3 | Discounts year-three dividend at 12%. | Upstream |
| 163 | `calc:c4882e5cb80edaf3ef01` | 12 percent dividend total PV | Adds the three 12% dividend present values. | Upstream |
| 164 | `calc:0da22aa4c30eee7f5d30` | 12 percent base terminal PV | Discounts the initial base target at 12%; later updated for pensions. | Other working/support |
| 165 | `calc:da1d057dde63a1b0942b` | 12 percent base present value | Adds dividend PV to the initial 12% base result; later updated. | Other working/support |
| 244 | `calc:14b494bc916ff174c2d4` | Pension proxy future value effect per share | Calculates the future per-share effect of the supplementary pension deduction. | Upstream |
| 245 | `calc:7dd4b4390b5c7118aefe` | Pension proxy present effect per share | Discounts that pension effect to today. | Cited |
| 246 | `calc:5679b7a7edb3eceb839d` | 8 percent final base terminal PV | Discounts the pension-adjusted base target at 8%. | Upstream |
| 247 | `calc:2321492b4c43d1bb64e3` | 8 percent final base present | Adds the 8% dividend PV to the updated base terminal PV. | Cited |
| 248 | `calc:00da4221f58976c6a4da` | 12 percent final base terminal PV | Discounts the pension-adjusted base target at 12%. | Upstream |
| 249 | `calc:da82018809cb099a9aa8` | 12 percent final base present | Adds the 12% dividend PV to the updated base terminal PV. | Cited |
| 250 | `calc:9db400a41263ca54feba` | Final base diluted future target | Computes the pension-adjusted future target with 2% more shares. | Upstream |
| 251 | `calc:6c8c37586dc8b20301e9` | Final base diluted terminal PV | Discounts that updated diluted target. | Upstream |
| 252 | `calc:3d0a9811e9aa8a335589` | Final base diluted present | Adds dividends to the updated diluted terminal PV. | Cited |

### Reverse market-expectations test — 7

Works backward from the observed price to the future EBIT required under the chosen multiple, debt bridge, dividends and equity-return hurdle. The final answer is about 2,572 MSEK of 2029 EBIT.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 166 | `calc:9efbed4642ac29ca69bc` | Market price excluding dividend PV | Removes the modeled dividend PV from the observed price. | Upstream |
| 167 | `calc:ef7ef24dd9305da53733` | Required future equity per share at 10 percent | Compounds the remaining equity price to the future date at 10%. | Upstream |
| 168 | `calc:296b22307d8557de3ac9` | Required future parent equity | Converts required future per-share equity into total parent equity. | Upstream |
| 169 | `calc:c7b5f0506c4da398fa34` | Required future EV with base bridge | Adds the initial future debt/claim bridge to required equity; later updated for pensions. | Other working/support |
| 170 | `calc:99366742acdf6c745028` | Required 2029 EBIT at 11 times EV EBIT | Divides that initial required EV by 11×; later updated for pensions. | Other working/support |
| 253 | `calc:5d363ae72bc769458d0c` | Required future EV including pension proxy | Adds the pension-inclusive future claim bridge to required market-implied equity. | Upstream |
| 254 | `calc:ab7bcbbd657092293c3e` | Required EBIT to justify latest price | Divides required EV by 11× to obtain the final market-implied 2029 EBIT. | Cited |

### Units and presentation — 83

Contains 82 divisions by a saved one-million-SEK presentation unit and one valid multiplication probe duplicating bear EBIT. These are audit/presentation steps rather than 83 new economic assumptions.

| Record | Calculation ID | Saved label | Purpose | Role |
|---:|---|---|---|---|
| 54 | `calc:0290610f4f34ed1244f2` | Unit test: bear volume times SEK per metric tonne | Validates volume multiplied by profit per tonne; duplicates the later bear EBIT calculation. | Other working/support |
| 55 | `calc:73a47ad1df1a43ba8430` | Current market cap expressed as count of million-SEK units | Displays “current_market_cap” in million-SEK units; no change to economics. | Other working/support |
| 171 | `calc:3f36a22db73fc0e6bb6f` | Assumed minority fair value at book proxy expressed as count of million-SEK units | Displays “Assumed minority fair value at book proxy” in million-SEK units; no change to economics. | Other working/support |
| 172 | `calc:0bf675521e7234180bbb` | Annual common dividends in cash expressed as count of million-SEK units | Displays “Annual common dividends in cash” in million-SEK units; no change to economics. | Other working/support |
| 173 | `calc:e7b50805fd75ec7b4822` | bear EBIT expressed as count of million-SEK units | Displays “bear EBIT” in million-SEK units; no change to economics. | Other working/support |
| 174 | `calc:1755c187c3926622a066` | bear operating EV expressed as count of million-SEK units | Displays “bear operating EV” in million-SEK units; no change to economics. | Other working/support |
| 175 | `calc:b2198349b23aba0c76e0` | bear cumulative debt reduction expressed as count of million-SEK units | Displays “bear cumulative debt reduction” in million-SEK units; no change to economics. | Other working/support |
| 176 | `calc:f0b277dfcb008085b20c` | bear future financial net debt expressed as count of million-SEK units | Displays “bear future financial net debt” in million-SEK units; no change to economics. | Other working/support |
| 177 | `calc:b19260d60bb059ee3df3` | bear equity bridge deductions expressed as count of million-SEK units | Displays “bear equity bridge deductions” in million-SEK units; no change to economics. | Other working/support |
| 178 | `calc:dce91e2e2cf6c5d1a40b` | bear parent common equity expressed as count of million-SEK units | Displays “bear parent common equity” in million-SEK units; no change to economics. | Other working/support |
| 179 | `calc:aedfeee8022663f941bf` | bear annual equity cash before common dividend expressed as count of million-SEK units | Displays “bear annual equity cash before common dividend” in million-SEK units; no change to economics. | Other working/support |
| 180 | `calc:5c33d1ebfc7813addc30` | bear normalized EBITDA expressed as count of million-SEK units | Displays “bear normalized EBITDA” in million-SEK units; no change to economics. | Other working/support |
| 181 | `calc:27a616c0c451c06dd17e` | bear EBITDA crosscheck EV expressed as count of million-SEK units | Displays “bear EBITDA crosscheck EV” in million-SEK units; no change to economics. | Other working/support |
| 182 | `calc:dd09aa91d8c6a114d7fa` | bear EBITDA crosscheck equity expressed as count of million-SEK units | Displays “bear EBITDA crosscheck equity” in million-SEK units; no change to economics. | Other working/support |
| 183 | `calc:a341132973a3f429e4a0` | base EBIT expressed as count of million-SEK units | Displays “base EBIT” in million-SEK units; no change to economics. | Other working/support |
| 184 | `calc:433b8d489f6f6c941c4d` | base operating EV expressed as count of million-SEK units | Displays “base operating EV” in million-SEK units; no change to economics. | Other working/support |
| 185 | `calc:8089c6b21e9e4649c048` | base cumulative debt reduction expressed as count of million-SEK units | Displays “base cumulative debt reduction” in million-SEK units; no change to economics. | Other working/support |
| 186 | `calc:35b99543e4a7cf4c6631` | base future financial net debt expressed as count of million-SEK units | Displays “base future financial net debt” in million-SEK units; no change to economics. | Other working/support |
| 187 | `calc:f7a45698a147c238b96b` | base equity bridge deductions expressed as count of million-SEK units | Displays “base equity bridge deductions” in million-SEK units; no change to economics. | Other working/support |
| 188 | `calc:a5fc9e89798c2379b3a7` | base parent common equity expressed as count of million-SEK units | Displays “base parent common equity” in million-SEK units; no change to economics. | Other working/support |
| 189 | `calc:52150772636a1ea4db31` | base annual equity cash before common dividend expressed as count of million-SEK units | Displays “base annual equity cash before common dividend” in million-SEK units; no change to economics. | Other working/support |
| 190 | `calc:ce4a2189d11c164ae22b` | base normalized EBITDA expressed as count of million-SEK units | Displays “base normalized EBITDA” in million-SEK units; no change to economics. | Other working/support |
| 191 | `calc:35269dc7d6dd5b076c09` | base EBITDA crosscheck EV expressed as count of million-SEK units | Displays “base EBITDA crosscheck EV” in million-SEK units; no change to economics. | Other working/support |
| 192 | `calc:9e95b9a75e151b5f269d` | base EBITDA crosscheck equity expressed as count of million-SEK units | Displays “base EBITDA crosscheck equity” in million-SEK units; no change to economics. | Other working/support |
| 193 | `calc:a997478034d48159596c` | bull EBIT expressed as count of million-SEK units | Displays “bull EBIT” in million-SEK units; no change to economics. | Other working/support |
| 194 | `calc:c0bf75199cc3feb4a002` | bull operating EV expressed as count of million-SEK units | Displays “bull operating EV” in million-SEK units; no change to economics. | Other working/support |
| 195 | `calc:df3e277dbf16d6f7057d` | bull cumulative debt reduction expressed as count of million-SEK units | Displays “bull cumulative debt reduction” in million-SEK units; no change to economics. | Other working/support |
| 196 | `calc:b4bd04a476af7dea177f` | bull future financial net debt expressed as count of million-SEK units | Displays “bull future financial net debt” in million-SEK units; no change to economics. | Other working/support |
| 197 | `calc:9d7f225a9513fe3fca8e` | bull equity bridge deductions expressed as count of million-SEK units | Displays “bull equity bridge deductions” in million-SEK units; no change to economics. | Other working/support |
| 198 | `calc:55b80a394144f855859b` | bull parent common equity expressed as count of million-SEK units | Displays “bull parent common equity” in million-SEK units; no change to economics. | Other working/support |
| 199 | `calc:63b94cbf09602bf58136` | bull annual equity cash before common dividend expressed as count of million-SEK units | Displays “bull annual equity cash before common dividend” in million-SEK units; no change to economics. | Other working/support |
| 200 | `calc:f0208a96f7f3b21eea53` | bull normalized EBITDA expressed as count of million-SEK units | Displays “bull normalized EBITDA” in million-SEK units; no change to economics. | Other working/support |
| 201 | `calc:50d31c5fa342a4a02048` | bull EBITDA crosscheck EV expressed as count of million-SEK units | Displays “bull EBITDA crosscheck EV” in million-SEK units; no change to economics. | Other working/support |
| 202 | `calc:396d3531f256efe7623c` | bull EBITDA crosscheck equity expressed as count of million-SEK units | Displays “bull EBITDA crosscheck equity” in million-SEK units; no change to economics. | Other working/support |
| 259 | `calc:dc9050abb631dbf74596` | Forecast pension debt-like proxy expressed as count of million-SEK units | Displays “Forecast pension debt-like proxy” in million-SEK units; no change to economics. | Other working/support |
| 260 | `calc:a1e0e4460b798c06d54d` | Forecast lease liability proxy expressed as count of million-SEK units | Displays “Forecast lease liability proxy” in million-SEK units; no change to economics. | Other working/support |
| 261 | `calc:975ff508220c831c0921` | bear final bridge deductions expressed as count of million-SEK units | Displays “bear final bridge deductions” in million-SEK units; no change to economics. | Other working/support |
| 262 | `calc:f83677f980ecdf3e4efb` | bear final equity before other assets expressed as count of million-SEK units | Displays “bear final equity before other assets” in million-SEK units; no change to economics. | Other working/support |
| 263 | `calc:f4b0e76f3de963d9f8c1` | bear final common equity expressed as count of million-SEK units | Displays “bear final common equity” in million-SEK units; no change to economics. | Other working/support |
| 264 | `calc:c524c572cd5fb78805ab` | bear final EBITDA crosscheck equity expressed as count of million-SEK units | Displays “bear final EBITDA crosscheck equity” in million-SEK units; no change to economics. | Other working/support |
| 265 | `calc:06d9c7c2dd4298fc4f1d` | base final bridge deductions expressed as count of million-SEK units | Displays “base final bridge deductions” in million-SEK units; no change to economics. | Other working/support |
| 266 | `calc:9de021a2cebfd5b0fcdd` | base final equity before other assets expressed as count of million-SEK units | Displays “base final equity before other assets” in million-SEK units; no change to economics. | Other working/support |
| 267 | `calc:cf7aef916766119133b5` | base final common equity expressed as count of million-SEK units | Displays “base final common equity” in million-SEK units; no change to economics. | Cited |
| 268 | `calc:474107bd8ea1296391e2` | base final EBITDA crosscheck equity expressed as count of million-SEK units | Displays “base final EBITDA crosscheck equity” in million-SEK units; no change to economics. | Other working/support |
| 269 | `calc:08cc78193223f8a81151` | bull final bridge deductions expressed as count of million-SEK units | Displays “bull final bridge deductions” in million-SEK units; no change to economics. | Other working/support |
| 270 | `calc:583471853d61b445a288` | bull final equity before other assets expressed as count of million-SEK units | Displays “bull final equity before other assets” in million-SEK units; no change to economics. | Other working/support |
| 271 | `calc:934b6e532225525f30ad` | bull final common equity expressed as count of million-SEK units | Displays “bull final common equity” in million-SEK units; no change to economics. | Other working/support |
| 272 | `calc:175cc9ccdb8e4bdcef28` | bull final EBITDA crosscheck equity expressed as count of million-SEK units | Displays “bull final EBITDA crosscheck equity” in million-SEK units; no change to economics. | Other working/support |
| 273 | `calc:f53dad2e656a7e751dbb` | Required future EV including pension proxy expressed as count of million-SEK units | Displays “Required future EV including pension proxy” in million-SEK units; no change to economics. | Other working/support |
| 274 | `calc:782f3a070fb538eb6f62` | Required EBIT to justify latest price expressed as count of million-SEK units | Displays “Required EBIT to justify latest price” in million-SEK units; no change to economics. | Cited |
| 275 | `calc:52f5cd4607367470c709` | Current full EV including pension proxy expressed as count of million-SEK units | Displays “Current full EV including pension proxy” in million-SEK units; no change to economics. | Other working/support |
| 289 | `calc:3278ff3351634abb931b` | 2022 minus 2021 fabrication revenue component expressed in million-SEK units | Displays “2022 minus 2021 fabrication revenue component” in million-SEK units; no change to economics. | Other working/support |
| 290 | `calc:aa1c7b7ec68ca6355d01` | 2022 minus 2021 raw revenue component expressed in million-SEK units | Displays “2022 minus 2021 raw revenue component” in million-SEK units; no change to economics. | Other working/support |
| 291 | `calc:46b02975fe9ab489bde1` | 2022 minus 2021 other revenue component expressed in million-SEK units | Displays “2022 minus 2021 other revenue component” in million-SEK units; no change to economics. | Other working/support |
| 292 | `calc:661b0a34e01476d78e48` | Sum of displayed 2022 revenue component changes expressed in million-SEK units | Displays “Sum of displayed 2022 revenue component changes” in million-SEK units; no change to economics. | Other working/support |
| 293 | `calc:dcbc7daf316cb5eda85e` | Revenue component bridge residual versus total sales change expressed in million-SEK units | Displays “Revenue component bridge residual versus total sales change” in million-SEK units; no change to economics. | Other working/support |
| 294 | `calc:61e10c96231e1b46a3f9` | Historical financial debt plus leases and pensions 2021 expressed in million-SEK units | Displays “Historical financial debt plus leases and pensions 2021” in million-SEK units; no change to economics. | Other working/support |
| 295 | `calc:5bf235693f9c47b7386e` | Historical financial debt plus leases and pensions 2022 expressed in million-SEK units | Displays “Historical financial debt plus leases and pensions 2022” in million-SEK units; no change to economics. | Other working/support |
| 296 | `calc:6ac1c21bc950447bfabc` | Historical financial debt plus leases and pensions 2023 expressed in million-SEK units | Displays “Historical financial debt plus leases and pensions 2023” in million-SEK units; no change to economics. | Other working/support |
| 297 | `calc:bd4ae24ed111630ebf6b` | Historical financial debt plus leases and pensions 2024 expressed in million-SEK units | Displays “Historical financial debt plus leases and pensions 2024” in million-SEK units; no change to economics. | Other working/support |
| 298 | `calc:36e5185f23e1cac4309b` | q1_line_ocf expressed in million-SEK units | Displays “q1_line_ocf” in million-SEK units; no change to economics. | Other working/support |
| 299 | `calc:ccc48b318b00ef1f9dab` | q1_cfo_to_apm expressed in million-SEK units | Displays “q1_cfo_to_apm” in million-SEK units; no change to economics. | Other working/support |
| 300 | `calc:c038202f34cf8971902d` | q1_provider_fcf expressed in million-SEK units | Displays “q1_provider_fcf” in million-SEK units; no change to economics. | Other working/support |
| 301 | `calc:899d571148a5a75bf211` | q3_reported_plus_adjustment expressed in million-SEK units | Displays “q3_reported_plus_adjustment” in million-SEK units; no change to economics. | Other working/support |
| 302 | `calc:83502423f40cbfeb7daa` | ytd_reported_plus_adjustment expressed in million-SEK units | Displays “ytd_reported_plus_adjustment” in million-SEK units; no change to economics. | Other working/support |
| 303 | `calc:e7a60c1075e5256a6d7a` | r12_reported_plus_adjustment expressed in million-SEK units | Displays “r12_reported_plus_adjustment” in million-SEK units; no change to economics. | Other working/support |
| 304 | `calc:49731677abfa34d5b155` | q3_adj_ebit_plus_da expressed in million-SEK units | Displays “q3_adj_ebit_plus_da” in million-SEK units; no change to economics. | Other working/support |
| 305 | `calc:b437d46de706a19b47e6` | r12_adj_ebit_plus_da expressed in million-SEK units | Displays “r12_adj_ebit_plus_da” in million-SEK units; no change to economics. | Other working/support |
| 306 | `calc:e75370f8923885dc9886` | r12_da_difference expressed in million-SEK units | Displays “r12_da_difference” in million-SEK units; no change to economics. | Other working/support |
| 307 | `calc:6f3ec44f3a9da81f3edd` | r12_quarter_cfo_sum expressed in million-SEK units | Displays “r12_quarter_cfo_sum” in million-SEK units; no change to economics. | Other working/support |
| 308 | `calc:0a153aae4a41acbae08f` | materials_reconciliation25 expressed in million-SEK units | Displays “materials_reconciliation25” in million-SEK units; no change to economics. | Other working/support |
| 309 | `calc:a605e54127a852b16717` | q1_apm_residual expressed in million-SEK units | Displays “q1_apm_residual” in million-SEK units; no change to economics. | Other working/support |
| 310 | `calc:3cb6ab49d7d3115f4903` | q3_ebit_residual expressed in million-SEK units | Displays “q3_ebit_residual” in million-SEK units; no change to economics. | Other working/support |
| 311 | `calc:b1c03b03220af4c2c912` | r12_ebit_residual expressed in million-SEK units | Displays “r12_ebit_residual” in million-SEK units; no change to economics. | Other working/support |
| 312 | `calc:7d2aad64e8a8ad703892` | debt_gross_less_cash expressed in million-SEK units | Displays “debt_gross_less_cash” in million-SEK units; no change to economics. | Other working/support |
| 313 | `calc:bd6437e37d8d987b1c11` | cfo_annual_plus_ytd expressed in million-SEK units | Displays “cfo_annual_plus_ytd” in million-SEK units; no change to economics. | Other working/support |
| 314 | `calc:75b2d2e4851d7e835073` | q3_cfo_reverse_tax expressed in million-SEK units | Displays “q3_cfo_reverse_tax” in million-SEK units; no change to economics. | Other working/support |
| 315 | `calc:5dfb657a0879e041d079` | 2025_provider_fcf_check expressed in million-SEK units | Displays “2025_provider_fcf_check” in million-SEK units; no change to economics. | Other working/support |
| 316 | `calc:cf3c9d76e437e0a6f13c` | q3_provider_fcf_check expressed in million-SEK units | Displays “q3_provider_fcf_check” in million-SEK units; no change to economics. | Other working/support |
| 317 | `calc:ea4ac73b9acd68947f02` | debt_bridge_excluding_leases expressed in million-SEK units | Displays “debt_bridge_excluding_leases” in million-SEK units; no change to economics. | Other working/support |
| 318 | `calc:aec85ebe808749802312` | cfo_annual_roll expressed in million-SEK units | Displays “cfo_annual_roll” in million-SEK units; no change to economics. | Other working/support |
| 319 | `calc:d31d5f360eaec6941919` | q3_cfo_to_company_ocf expressed in million-SEK units | Displays “q3_cfo_to_company_ocf” in million-SEK units; no change to economics. | Other working/support |
| 320 | `calc:4f402c96d4598a5c5794` | current_market_cap expressed in million-SEK units | Displays “current_market_cap” in million-SEK units; no change to economics. | Other working/support |
