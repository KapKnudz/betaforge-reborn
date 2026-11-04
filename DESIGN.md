# Betaforge design brief

Agreed direction, 4 November 2026. A classic financial research workspace: clear figures, concise explanations and detail that opens when needed. The first deliverable is a separate Company-page prototype for visual review. Adoption into the working interface follows the user's review.

## References and purpose

| Reference | Apply to Betaforge |
| --- | --- |
| [NBIM investments](https://www.nbim.no/en/investments/) | Clean sans-serif type, restrained colour, strong grouping, short summaries and clear navigation. Its page is spacious overall; use its hierarchy within a compact research screen. |
| [ABG Kinnevik memo, 4 February 2025](https://abgprivatebanking.se/wp-content/uploads/2025/02/Momentum-builds-for-2025e.pdf) | Page 1: concise thesis beside an aligned facts panel and chart. Pages 2–4: labelled charts, grouped numerical columns, visible totals and source notes. Adapt print density to readable screen sizes. |

These are presentation references. The [investment policy](docs/analysis-policy.md) and [calculation catalogue](docs/calculations.md) own financial meaning. ABG's NAV approach and ratings are specific to its report. Reference originals and exact company evidence stay in private storage.

The reader should quickly understand the business case, what the price requires, the main uncertain assumption and where to inspect its evidence.

## Company layout

1. **Quiet header:** company and ticker; small labelled report selector at the upper right. Keep the project navigation subordinate to the company research.
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

## Prototype and review

Terra/medium leads this user-approved visual prototype. Sol retains financial judgment and independent code review. This is a bounded design trial, not a claim that one model has superior design performance. Production implementation keeps the existing project roles.

Build one local HTML/CSS/JavaScript prototype using the existing validated saved-view format. Keep it separate from `web/progress/`. Its preview command takes an explicit saved view and optionally a read-only quote store; opening it performs no provider or model call. Shared files contain no issuer-specific figures or prose.

Review the actual browser at 1280 × 720 and 390 × 844:

- The desktop opening shows the company, conclusion, dated key figures and a meaningful part of the valuation graphic without a large decorative header.
- Overview and sections feel like one coherent research page. Small labels and repeated explanations do not dominate.
- Both chart forms are readable and visibly different. Scenario and source links reveal the right details; keyboard navigation and focus work.
- Financial values, units, dates, definitions and qualifications match their saved records. Missing values remain explicit.
- Narrow layouts have no page-wide horizontal overflow; wide tables scroll within their own containers.
- Compare with the selected references for hierarchy, density and clarity. Code checks and model review support correctness; the user decides whether the visual direction is right.

Record user feedback here when it changes a design rule. [The plan](work/plan.json) owns delivery status, and [the architecture](docs/architecture.md) owns module boundaries.
