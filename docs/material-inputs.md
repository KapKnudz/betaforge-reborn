# Material inputs and financial periods

Every material selection should answer five questions: **what is it, which period does it describe, where is the evidence, why choose it, and how does valuation use it?** Keep provider observations, report facts and assumptions distinct.

## The decision record

A saved review can contain `material_inputs`. Each row records a selected source record, its definition, selection reason, valuation uses, limitations and compared candidates. Source records retain exact values, scale/currency, observation IDs, report pages and hashes.

Two independent statuses prevent a numeric match from becoming an accounting claim:

| Status | Meaning |
|---|---|
| Selected `definition_status` | `documented` or `unresolved` for the stated selected concept and scope. An explicit assumption can have a documented meaning without becoming an observed fact; its `kind` remains `assumption`. |
| Candidate `definition_status` | Whether the compared source's accounting convention is documented. For a provider field, a matching amount alone cannot resolve it. Report-derived candidates can have documented formulas while the provider's general formula remains unresolved. |
| `reconciliation_status` | `unreviewed`, `matched`, `derived_match`, `disagrees` or `not_comparable`. The row's source check concerns its selected evidence; each candidate has its own numeric-comparison status and residual. A verified report total can still differ from a provider candidate. |

An EPS disagreement may justify selecting report diluted EPS. Group profit and parent profit can both be correct and non-comparable. A book minority balance can be a sourced fact while its use as a future fair-value claim remains an assumption.

The API documentation establishes field identities and period/currency conventions. The [definition audit](research/borsdata-definition-audit.md) records the limits of those definitions; issuer reports establish the scoped accounting evidence.

## Use the latest compatible period

| Value | Preferred current evidence | Keep visible |
|---|---|---|
| EBIT margin | Latest quarter for recent trading; latest R12 for an annual earnings base | Reported/adjusted basis and matching revenue duration |
| Incremental EBIT margin | Same quarter or R12 against its prior-year equivalent | Both deltas, acquisitions, FX, pass-through and one-offs; this is not isolated organic operating leverage |
| Operating ROIC | R12 operating earnings and capital at both R12 endpoints | Tax assumption, capital convention and two-point-average limitation |
| Inventory/trade balances relative to sales | Actual operating components at matching R12 endpoints and R12 sales | Annual fallback when the interim supplies only aggregates; never relabel aggregate receivables/payables as trade components |
| Cash conversion | R12 statutory CFO, actual cash capex and separately verified cash interest/lease principal | Known intermediate cash amounts; missing components prevent only the dependent ratio |
| Debt, cash, leases, minority claims | Latest available closing balance before the analysis cutoff | Additional claim conventions and any stale/fair-value proxy |
| P/E and EV/EBIT | Dated price/EV with an annual or R12 earnings denominator | Ownership, dilution, units and the EV claims convention |

A date such as December 2025 is appropriate for historical analysis, an explicitly annual-only disclosure or an assumption's evidence. It should not appear as an unqualified current diagnostic when a matching newer period is supportable. For R12 capital measures, the opening date is the day before the R12 flow starts; the latest December balance is not automatically the correct opening balance.

Keep four clocks distinct: financial period, issuer publication date, acquisition/check date and analysis cutoff. A later review can improve mappings using an already-published report without refreshing the frozen price or changing the original valuation.

## Current implementation

The [Gränges example](../examples/granges/README.md) extends its existing deterministic review with an explicit private current-facts file and a scoped material ledger. The original review and model run remain preserved. The [local viewer](saved-analysis-view.md) displays the saved ledger and current-period diagnostics; shared code contains no issuer assumptions and no database migration is needed.

For a future analyst packet, pass the generated private `material-inputs.md` through the existing `--mapping-resolution` option. The packet already freezes that document, hashes it and includes its content in the evidence context. Do not silently replace the original packet or resume a run under changed evidence.
