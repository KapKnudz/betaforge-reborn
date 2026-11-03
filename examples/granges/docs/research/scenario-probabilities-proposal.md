# Scenario probabilities: proposed next step

Prepared 3 November 2026. **Probability ownership is agreed; numerical Gränges weights are still a proposal.** The original 1 November analysis remains frozen. This note separates its conditional valuations from a proposed probability-based decision process.

## What is missing today

The saved report supplies bear/base/bull assumptions and values, and expressly says they are not probability-weighted forecasts. Consequently, its 168.14 SEK base present value is not an expected value across possible outcomes. Its roughly-fair-value conclusion is conditional on that base case. [Saved answer, Executive assessment and section 9](../../../../data/granges-codex/runs/20261101-full/answer.md).

The three present values are 52.35241848 / 168.14270678 / 249.08595434 SEK per share. They discount the corresponding November 2029 targets and assumed dividends at 10%. Future targets of 58.42706900 / 212.54394273 / 320.27940522 belong to a different date and must not be mixed with present values. [Answer section 9](../../../../data/granges-codex/runs/20261101-full/answer.md); final present-value calculations `calc:44251337e56efb345589`, `calc:791e2ac113fabdd105dc`, `calc:9e9577bc76984e4d0163`.

## Proposed meaning and process

1. **Define the outcomes first.** Describe weak, central and strong business outcomes over the three-year horizon. For an unconditional expectation, use mutually exclusive buckets covering the relevant distribution, with a conditional-mean value or cash-flow path within each bucket. If representative points approximate those means, label the approximation. Assign probability to a business-outcome range, not to an exact share price. The current cases are conditional point assumptions; their values are not yet established as those bucket averages.
2. **Keep each case coherent.** Volume, profit per tonne, debt, dividend capacity and the valuation multiple must fit together. Financial distress or dilution should have its own branch when material, or be explicitly incorporated into the weak case. Do not mechanically combine every favorable or unfavorable assumption.
3. **Estimate company-specific weights.** Start from relevant historical frequencies and comparable operating outcomes where evidence exists, then adjust for the company's current position, management execution, capacity, repair milestones, cash conversion, leverage and market conditions. Identify judgment separately from measured frequencies. Do not multiply event probabilities while silently assuming that correlated events are independent.
4. **Expose uncertainty.** The analyst should propose rounded weights and a plausible range, explain what moves each weight, and allow human overrides. A probability is distinct from confidence in the underlying evidence. Avoid a universal 25/50/25 default.
5. **Calculate and retain the distribution.** Weights must be nonnegative and total 100% across an exhaustive set of modeled outcomes. If a material tail is omitted, disclose the omitted mass and label a normalized average conditional on the covered outcomes. Show the probability-weighted present value and future payoff separately, alongside downside severity, the scenario returns and the uncertainty in the weights.
6. **Update on evidence.** Record which repair, earnings, working-capital, debt or management observations would change the probabilities. Preserve the prior version and rationale.

These are recommendations, not a claim that the existing three values define a calibrated distribution. Damodaran's primary treatment distinguishes stress cases from probability-based scenario analysis and emphasizes covering the relevant range of outcomes before constructing an expected value. [Probabilistic Valuation, chapter 3, pp 2–4](https://pages.stern.nyu.edu/~adamodar/pdfiles/DSV2/Ch3.pdf).

## The calculation

For comparable present values, the proposed calculation is:

```text
Weighted present value
  = p_bear × bear present value
  + p_base × base present value
  + p_bull × bull present value
```

The [illustration records](../../data/probability-examples.json) use the original full-precision results. Holding bull probability at 20% and transferring weight between bear and base gives:

| Illustrative bear/base/bull weights | Weighted present value, SEK/share | Weighted November 2029 target, SEK/share |
|---|---:|---:|
| 1% / 79% / 20% | 183.17 | 232.55 |
| 50% / 30% / 20% | 126.44 | 157.03 |

These demonstrate sensitivity only. Neither set is an estimate of Gränges' actual probabilities. Averaging scenario values is preferable to first averaging assumptions and then valuing that averaged case: value can depend nonlinearly on combinations such as EBIT multiplied by an exit multiple.

## Provisional analyst weights for Gränges

Using the saved 1 November evidence, the working proposal is **25% bear / 55% base / 20% bull**. These are subjective company-specific judgments, editable by the user, not measured frequencies or a fixed default.

| Case | Draft weight | Evidence behind the judgment |
|---|---:|---|
| Bear | 25% | R12 statutory CFO of 293 MSEK and Börsdata-defined FCF of −346 MSEK (CFO plus investing cash flow), ROCE below the target, working-capital absorption, Asian pricing and repair/insurance uncertainty justify meaningful downside weight. The existing bear also combines weaker operating performance, cash burn and a lower multiple, so it is more severe than a mild volume setback. |
| Base | 55% | Completed expansion, 800 ktonnes capacity, improving recent profit per tonne and observed execution support a central recovery path. The 700-ktonne case is 87.5% of stated nameplate capacity, an analytical proxy rather than the issuer's plant-level utilization measure; management targets more than 90% utilization. Cash conversion must still improve. |
| Bull | 20% | Higher utilization, better mix and Asian profitability offer a path, but 760 ktonnes, 4,200 SEK EBIT per tonne and 650 MSEK retained cash require several favorable developments together. |

Evidence: [saved report sections 4,6,9–11](../../../../data/granges-codex/runs/20261101-full/answer.md). The weights are judgments about the combined narratives; the evidence does not statistically identify those percentages.

The resulting **indicative three-case weighted present value is 155.38 SEK/share**, at the original illustrative 10% discount rate. The weighted November 2029 target is 195.56 SEK/share; it excludes interim dividends from the target itself, while the present value includes their discounted payments. [Exact inputs and Decimal calculations](../../data/probability-examples.json), `working_draft`.

This is conditional on the three modeled **going-concern** cases. Their point values are judgmental representatives rather than established conditional means. An explicit default or severe-dilution tail remains unquantified; the weighted value is not an exhaustive, calibrated expectation. Current profitability and net-debt/adjusted-EBITDA of 1.7 times do not indicate imminent distress in the saved report, while weak cash conversion prevents establishing that tail risk as zero. [Saved report sections 6,9,11](../../../../data/granges-codex/runs/20261101-full/answer.md).

Test joint alternative judgments of **35/50/15** for greater cash-conversion skepticism and **15/60/25** after convincing repair/cash recovery evidence. These produce approximately **139.76** and **171.01 SEK/share** respectively. They are sensitivity cases, not statistical confidence bounds. Updating the weights should follow new evidence rather than whichever value makes the investment attractive. [Illustration records, `weight_uncertainty_examples`](../../data/probability-examples.json).

## Return, risk and the agreed benchmark

A probability-weighted average of outcomes does not remove the need for an appropriate required return. Ordinary real-world probability weights represent an expectation, not a certainty equivalent. Keep the reasons for probability choices, the discount rate and any investment margin of safety separately visible. [Damodaran, Valuation Approaches and Metrics, Misunderstanding Risk Adjustment, p31](https://people.stern.nyu.edu/adamodar/pdfiles/papers/valuesurvey.pdf).

Three useful measures should be named precisely:

- Probability of losing nominal money over the horizon, including distributions.
- Probability of failing the investment return hurdle.
- Probability that the analyst's present value is below the market price.

For example, the base future target exceeds the starting price, while its present value at the illustrative 10% rate is below that price. It therefore describes a positive nominal modeled outcome that misses 10%. Under this model's initial purchase followed by positive dividends and terminal equity proceeds, a present value below the purchase price at 10% is equivalent to a scenario IRR below 10%. Those two modeled probabilities are not independent risk measures. The actual future market price can also diverge from the scenario target. [Answer section 9, Future targets versus today's value](../../../../data/granges-codex/runs/20261101-full/answer.md).

The agreed benchmark is Investor AB B's trailing ten-year annualized total return with dividends reinvested, as of the analysis date. Its data and calculation conventions remain to be verified. The walkthrough's 10% assumption did not implement that benchmark. [Planning foundation, Return hurdle](../../../../docs/planning/decisions.md#return-hurdle).

Missing the Investor B hurdle can differ from missing 10% if the measured benchmark or return convention differs. The opportunity-cost comparison and the valuation discount rate serve different purposes; this proposal does not require automatically setting both to the same number.

The annual return statistic also needs an explicit convention: the weighted mean of scenario IRRs, the IRR of expected cash flows and the annualized return on expected terminal wealth can differ. The next specification should name the chosen statistic and use consistent dividend/reinvestment treatment for the candidate and benchmark.

## Decision frontier

**Q1 — Probability ownership: settled.** The user confirmed that the analyst proposes company-specific weights with evidence and uncertainty, editable by the user. The policy is recorded in [the planning foundation](../../../../docs/planning/decisions.md#scenario-probability-ownership). No particular numerical split was adopted by that reply.

Outcome definitions, numerical probability estimates, return-statistic conventions and probability-update rules remain to be made explicit. The Investor B benchmark identity is already agreed and does not need to be chosen again. No new ADR is necessary for the present explanatory proposal.
