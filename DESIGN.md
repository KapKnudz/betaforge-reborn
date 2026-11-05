# Betaforge design brief

Direction approved on 4 November 2026. A classic financial research workspace: clear figures, concise explanations and detail that opens when needed. The approved Company trial is now being integrated into the main workbench, with company/memo navigation and a visual explanation of the system and analysis process.

## References and purpose

| Reference | Apply to Betaforge |
| --- | --- |
| [NBIM investments](https://www.nbim.no/en/investments/) | Clean sans-serif type, restrained colour, strong grouping, short summaries and clear navigation. Its page is spacious overall; use its hierarchy within a compact research screen. |
| [ABG Kinnevik memo, 4 February 2025](https://abgprivatebanking.se/wp-content/uploads/2025/02/Momentum-builds-for-2025e.pdf) | Page 1: concise thesis beside an aligned facts panel and chart. Pages 2–4: labelled charts, grouped numerical columns, visible totals and source notes. Adapt print density to readable screen sizes. |

These are presentation references. The [investment policy](docs/analysis-policy.md) and [calculation catalogue](docs/calculations.md) own financial meaning. ABG's NAV approach and ratings are specific to its report. Reference originals and exact company evidence stay in private storage.

The reader should quickly understand the business case, what the price requires, the main uncertain assumption and where to inspect its evidence.

## Company layout

1. **Quiet header:** company and ticker; separate labelled company and memo-version selectors. Keep the memo selector at the upper right and project navigation subordinate to the company research.
   Captured companies remain selectable before their first memo. Show a concise empty state with the snapshot date; keep data availability distinct from completed analysis.
2. **Overview:** a short investment conclusion alongside a compact facts panel. Distinguish the latest stored market quote from the dated report price. Label conditional annual return and the report's required return accurately.
3. **Valuation graphic:** show the three scenarios with legible values, units, probabilities and dates. Use different chart forms for present values and future share targets. Selecting a scenario opens its assumptions.
4. **Full-width expandable sections:** Investment case; Valuation assumptions; Financials and management; Evidence. Each has a short useful summary. Details are closed initially; links open the relevant section and focus their target.

Use one overview and expandable sections rather than the current five Company subtabs. On narrow screens, stack the memo, facts and charts while retaining the reading order.

## Visual rules

- White background, dark navy text, quiet grey separators and one restrained accent. Reserve positive/negative colours for financial meaning.
- Use a system sans-serif font, tabular figures and right-aligned numeric columns. Body text around 16 px; secondary labels remain readable. Use a clear scale of company title, section heading, body and annotation.
- Start with an 8 px spacing rhythm. Group related figures closely and leave stronger separation between sections. Use thin rules and background bands sparingly; hierarchy comes from alignment, type and grouping.
- Keep the conclusion near 80–90 words. Put a useful claim beside its supporting figure; move extraction history, raw identifiers and long quotations into Evidence.
- Show units and periods with figures. Display monetary totals in clearly labelled millions where helpful. Preserve exact saved values in supporting details.
- Charts have clear dates, minimal gridlines and short legends. Explain dividend treatment beside valuation charts. Historical performance comparisons require compatible return series; forecast paths require actual saved forecasts.
- Controls look actionable, have visible keyboard focus and work without hover. Use native disclosures where possible. Keep source and calculation links available through the detail layers.
- Use descriptive subheadings within business and valuation sections. Keep long qualifications folded; show the business model, operating record and material assumptions first.
- Put dated actuals beside scenario assumptions. State differences in accounting basis and leave unavailable comparisons explicit. Explain briefly why the main drivers affect value.
- Add the latest stored market price as a dated reference in both valuation charts when currency and per-share units match. The line on a future-target chart is today's comparison price, not a forecast.
- Make the saved annual-return calculation inspectable beside the headline figure. Keep its purchase-price date distinct from the latest quote. Use compatible saved tables for trend charts, with their units, periods, qualifications and source links.

## Prototype and review

Terra/medium led the approved visual trial; production implementation follows the existing project roles. Sol retains financial judgment and independent code review. The trial does not establish superior design performance by one model.

The working interface lives in `web/progress/`; `web/prototypes/company/` preserves the design trial. Reuse the existing validated saved-view format and read-only routes. Opening either view performs no provider or model call. Shared files contain no issuer-specific figures or prose.

The Architecture view shows a concise technical map and expandable analysis stages. Distinguish code-enforced checks, agent judgment and coordinator actions with consistent labels. Describe saved reasoning and evidence, rather than presenting internal model deliberation as observable. These diagrams explain the system; they do not claim a run is in progress.

Review the actual browser at 1280 × 720 and 390 × 844:

- The desktop opening shows the company, conclusion, dated key figures and a meaningful part of the valuation graphic without a large decorative header.
- Overview and sections feel like one coherent research page. Small labels and repeated explanations do not dominate.
- Both chart forms are readable and visibly different. Scenario and source links reveal the right details; keyboard navigation and focus work.
- Financial values, units, dates, definitions and qualifications match their saved records. Missing values remain explicit.
- Narrow layouts have no page-wide horizontal overflow; wide tables scroll within their own containers.
- Compare with the selected references for hierarchy, density and clarity. Code checks and model review support correctness; the user decides whether the visual direction is right.

Record user feedback here when it changes a design rule. [The plan](work/plan.json) owns delivery status, and [the architecture](docs/architecture.md) owns module boundaries.
