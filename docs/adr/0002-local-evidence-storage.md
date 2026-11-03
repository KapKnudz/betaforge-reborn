---
status: accepted
---

# Keep immutable source files and query financial observations through SQLite

Accepted by the user on 2026-11-01 as the starting specification for storage and the Codex Gränges walkthrough. The [research specification](../research/borsdata-retrieval-storage.md) defines dataset coverage, retention and reconciliation; [ADR 0001](0001-persist-company-evidence.md) establishes that acquisition is independent of analysis.

Preserve original JSON and PDF evidence with content hashes. SQLite stores source-linked financial observations, definitions, dated identities and revisions. Freeze the database and required evidence versions for each analysis so later provider changes do not alter saved results. Keep provider values, report-derived figures and explicitly chosen calculation inputs distinct.

This favors simple local operation and replay over maintaining a server database or rebuilding evidence on every run. The tradeoff is that the application owns snapshot integrity, backup and a single-writer ingestion path. A server database can replace SQLite if concurrent users or writers require it; the source and observation identities must survive that migration.

Preserve all returned statement fields, the agreed available histories, metadata and contextual datasets. Deduplicate unchanged payloads and retain changed versions. Record unresolved definitions and source disagreements at the affected input, without blocking unrelated useful analysis. Historical context from a current revised API response is not a point-in-time backtest.
