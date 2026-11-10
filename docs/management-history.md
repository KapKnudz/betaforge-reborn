# Frozen management and ownership history

Use an optional, privately stored version-1 JSON sidecar to organize a requested five-year management/board history, ownership disclosures, responsibility links and every captured transaction row. Preserve older context where useful. This is a curated evidence index: its descriptions, dates and identity associations require source challenge. It supplies no score, valuation adjustment or inherited forecast judgment. A fresh analyst derives its own forecasts.

Pass `--management-history /absolute/path/history.json` to [packet preparation](../scripts/prepare_codex_packet.py). Preparation validates the structure and source links, copies the original UTF-8 bytes to `management-history.json`, records their hash and appends the complete parsed JSON with compact whitespace to the actual packet `prompt.md` before hashing that prompt. Inputs above 2 MiB fail rather than truncate. Use the packet prompt for the run. Loading/resuming never adds a sidecar or reads the original supplied path.

## Version 1 fields

All fields below are required, including empty lists and explicit nulls. Unknown fields and duplicate JSON keys are rejected. Local IDs are stable, unique within their collection and use letters, digits, colon, underscore or hyphen. Party IDs specifically use `<instrument_id>:<lowercase-slug>`; they are local evidence identities, never a universal person registry.

| Top-level field | Content |
| --- | --- |
| `schema_version` | Integer `1`. |
| `instrument_id`, `analysis_date` | Selected positive integer company ID and frozen `YYYY-MM-DD` cutoff. Both must match the packet. |
| `window` | `{start, end}` dates with `start < end` and `end = analysis_date`. The coordinator selects the requested five-year start; the validator does not infer or enforce a duration. |
| `source_scope` | `{report_ids, transaction_datasets, limitations}`. Lists of existing report IDs and explicitly selected transaction dataset names; at least one nonempty limitation states the bounded captured coverage. |
| `source_refs` | Source-reference objects below, addressed by local `id`. |
| `parties` | `{id, kind, name, source_refs, aliases}`. Kind is `individual`, `entity` or `unresolved`; `source_refs` is a nonempty list of source-reference IDs. Each alias is `{name, source_refs}` with its own nonempty evidence list. |
| `role_observations` | `{id, party_id, role, observed_date, source_refs, note}`. Role text includes its scope, such as group CEO or board chair. |
| `role_intervals` | `{id, party_id, role, start_date, end_date, source_refs, note}`. Either endpoint may be null; known endpoints cannot be reversed. |
| `ownership_observations` | `{id, party_id, observed_date, holding, basis, source_refs, note}`. Preserve `holding` and `basis` as sourced text, including units, direct/indirect scope and known definitions. No arithmetic or inferred current holding. |
| `commitment_links` | `{id, statement, party_ids, role_interval_ids, source_refs, responsibility_source_refs, note}`. An empty list is allowed. A link to a party or interval requires nonempty responsibility evidence; unresolved responsibility keeps both link lists empty and explains the gap in `note`. |
| `transaction_links` | One object per captured stored row in every selected dataset, using the fields below. |

Source references have exactly one of these shapes:

```json
{"id":"annual-role","kind":"report","report_id":"annual-2025","page":12,"quote":"Exact source wording"}
```

```json
{"id":"captured-row","kind":"dataset","dataset":"holdings_insider","row_id":"row_ID","source_id":"src_ID","pointer":"/list/0/values/0"}
```

Report references require a scoped report, physical page and whitespace-normalized matching quote. Dataset references must match an existing company-selected row's dataset, source and pointer. Source publication dates remain the report manifest's dates; capture/check dates remain source metadata accessible through `get_source`. Neither establishes a role-effective date or a holdings measurement date. `observed_date` is the actual observation/measurement date only when explicit, otherwise null; it cannot follow the cutoff. Interval endpoints are effective dates, and may include a future appointment announced in admitted source evidence. A note must preserve date precision and uncertainty: an employment year is not automatically a CEO start date.

## Transaction preservation and identity

Every transaction link has exactly these fields:

```json
{
  "row_id":"row_ID",
  "dataset":"holdings_insider",
  "source_id":"src_ID",
  "pointer":"/list/0/values/0",
  "payload":{},
  "reported_party_id":"777:owner-local-id",
  "party_id":null,
  "match_status":"unresolved",
  "match_source_refs":[],
  "date":null,
  "window_status":"unknown",
  "related_row_ids":[],
  "note":"Captured source owner; identity, date and transaction definition remain unresolved."
}
```

`payload` must equal the complete stored `get_dataset` row payload, with its JSON value types intact. Keep all row versions, correction candidates, non-management owners, entities, unmatched names and rows outside the window. The validator compares the exact row-ID set and payload/source/pointer identity against the frozen database for every selected dataset, using the same selected-company-or-unscoped-row rule as `get_dataset`. It never filters, deduplicates, sorts by assumed transaction chronology or nets transactions. `related_row_ids` may identify other retained correction/duplicate candidates; this does not assert that two rows are one event.

A captured row is not necessarily a trade: an empty/error carrier may also be a stored row. Preserve it with an explicit note and unresolved source-owner identity when the name is unavailable; do not count it as a transaction event merely because it appears in this list.

`reported_party_id` groups the exact source-owner label separately from a corroborated real issuer identity. Its party must cite that exact dataset row. Prefer separate company-scoped source-owner records, with `kind: unresolved` unless evidence establishes individual/entity status. Do not convert family labels, abbreviations or a missing owner-position value into a management identity. The validator does not infer the provider's owner-name field or prove that the chosen grouping is economically correct.

`party_id` stays null and `match_status` stays `unresolved` until corroborated full-name and compatible role or other identity evidence support the join. Candidate identities belong in `note`. A `matched` link requires an existing resolved party and nonempty `match_source_refs`, including evidence beyond the transaction's own row. Name similarity alone is insufficient; evidence presence does not prove its meaning. Aliases never trigger automatic joins.

`date` is an explicitly interpreted transaction date or null. `window_status` must be `inside`, `outside` or `unknown`, consistently with that date and the declared window. Preserve an after-cutoff row as outside; do not use it as information known by the cutoff. Keep transaction dates, verification dates, flags and unknown category codes distinct in the source challenge. Zero captured rows or a chosen scope establishes only that bounded capture, never no trading or complete public-register coverage.

## Analyst and reviewer use

The analyst reads the full frozen index, retrieves captured transactions through `get_dataset` to pagination exhaustion and checks the material source pages. Challenge scope omissions, source-owner versus real-person matches, dates/definitions, responsibility attribution and correction candidates. Explain what the evidence changes about delivery/alignment and confidence in material assumptions, including contrary evidence and gaps. Supporting supplements remain derived research, not issuer facts or forecast instructions.

The [structured report](codex-integration.md#structured-reports-and-independent-challenge) reference schema is unchanged. Sidecar local IDs and dataset row/source/pointer identities belong in readable prose or supporting notes; they are not new admissible saved-input/calculation reference IDs. Use existing valid report/observation/input/calculation references where applicable, and state dataset provenance explicitly rather than substituting an unrelated citation.

The coordinator manually supplies both the verified sidecar body and `tools.identity['management_history']` to the independent reviewer, together with the frozen guides and exact report. `EvidenceTools.management_history` caches the source-validated JSON; `get_catalogue` exposes its metadata. The reviewer checks prose claims against those captured rows and report pages. Dispatch remains manual. Saved views retain and validate the optional identity metadata without opening the sidecar or any live source; full source verification occurs during export. Old packets, reports and exports without this identity remain valid, subject to the existing runner implementation guard on resume.
