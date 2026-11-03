# Version control and workstation portability review

Reviewed 3 November 2026. This was a read-only inspection of Git metadata, source, documentation and file metadata. No files were staged, committed or pushed; no tests, acquisition, model or valuation runs were started. Only this findings note was written. Credential values were not read or printed.

## Recommendation

Create a reviewed source checkpoint before adding more functionality. The current remote `main` preserves only the initial planning foundation. Keep source and decisions in Git, and preserve exact company evidence and completed analysis records as separate private bundles. This reuses the existing frozen-packet design; a new storage architecture is unnecessary. [Git inventory](#git-inventory), [accepted storage decision](../adr/0002-local-evidence-storage.md), [packet preparation](../../scripts/prepare_codex_packet.py#L45).

This is a plan, not authorization to publish or a claim that another workstation has already been tested.

## Findings

| Bounded claim | Verdict and reasoning | Missing evidence or next check |
|---|---|---|
| The important local work is already preserved on GitHub | **Unsupported.** Only `docs/planning/decisions.md` and `docs/planning/investment-philosophy-draft.md` are tracked. The first is locally modified. README, glossary, ignore rules, source, tests and later research notes are untracked. Remote `main` and `HEAD` remain at the initial commit. [Git inventory](#git-inventory). | A reviewed commit and push have not occurred. This review did not inspect every possible remote branch; the named working branch is absent remotely. |
| The repository is suitable for a private source checkpoint | **Supported with a file review.** GitHub metadata identifies `KapKnudz/betaforge-reborn` as private, with default branch `main`. The candidate source/doc files are small; the largest inspected untracked candidate is the public Swagger schema at about 116 KB. [Git inventory](#git-inventory), [candidate inventory](#recommended-first-checkpoint). | No full content-level secret audit or dependency license audit was performed. `.env.example` is a candidate template, not an exemption from checking the staged content. |
| A clone alone can restore the existing research | **Unsupported.** Original/prepared reports, provider captures, SQLite evidence and Codex runs are ignored. The README links to those local artifacts and explicitly says they are excluded. [`.gitignore`](../../.gitignore#L6), [README, Preserve the original report comparison](../../README.md#L84). | Select a private artifact handoff/backup location and exercise a restore. Reacquiring current source data cannot promise identical historical bytes or provider revisions. |
| Frozen company inputs can be moved without a database redesign | **Supported by design, not yet cross-machine verified.** Preparation copies PDFs and prepared text, uses relative `snapshot_dir`/`reports_dir`, and freezes the database with source blobs. Tool initialization resolves those paths relative to the packet and checks hashes. [Preparation](../../scripts/prepare_codex_packet.py#L54), [freeze](../../betaforge/storage.py#L578), [packet resolution and integrity](../../betaforge/tools.py#L117). | A restore on a second workstation has not been performed. Retain the packet byte-for-byte and its original source/normalizer identities. |
| Setup is fully reproducible on another workstation | **Partial.** Most project paths derive from the repository root. However, the only dependency file pins Requests; PDF extraction separately imports `pypdf`, and image reading requires `pdftoppm`. The current Codex default is a macOS application path, with an existing `--codex` override. The protocol was tested against a specific alpha build. [Requirements](../../scripts/requirements-borsdata.txt#L1), [PDF preparation](../../scripts/prepare_granges.py#L7), [README setup](../../README.md#L24), [runner default](../../betaforge/codex_runner.py#L19), [CLI override](../../betaforge/codex_runner.py#L281), [protocol evidence](../codex-integration.md#L61). | A complete setup manifest and same-build second-machine check are missing. Do not require Node/pi unless reproducing the older comparison. [README, original comparison](../../README.md#L76). |
| A saved result can be displayed on another workstation | **Supported by design if its artifacts are transferred.** The renderer reads the frozen SQLite database, packet and saved answer/calculations. Its packet paths are relative; it does not initiate analysis. [Renderer](../../scripts/render_codex_walkthrough.py#L81), [integration records](../codex-integration.md#L52). | Confirm a clean restore and renderer invocation. Git alone omits the required bundle. |
| An active Codex analysis can resume on any workstation from the bundle | **Unproved.** Local tool state and evidence identity are saved, but the runner calls `thread/resume` with the prior Codex thread ID. The project has no conversation import step. Evidence identity is content-based; `run.json` also records the original absolute packet path. [Tool identity](../../betaforge/tools.py#L149), [run setup](../../betaforge/codex_runner.py#L159), [resume request](../../betaforge/codex_runner.py#L230). | Cross-workstation availability of the Codex thread was not tested. Treat completed-result handoff and live-thread migration as separate capabilities. Do not copy authentication files into the repository to compensate. |
| The current builder is a general watchlist runner | **Unsupported beyond the walkthrough.** Acquisition accepts an instrument ID, but packet preparation still queries ID 426 and fixes the analysis date to 1 November 2026. [Acquisition CLI](../../scripts/fetch_borsdata_context.py#L114), [initial context](../../scripts/prepare_codex_packet.py#L20), [packet metadata](../../scripts/prepare_codex_packet.py#L83). | Parameterize company, date and required reports when generalizing; this is not needed merely to preserve the existing Gränges analysis. |

## Git inventory

The following read-only commands were inspected on 3 November 2026:

```text
git branch --show-current
feat/granges-walkthrough

git ls-files
docs/planning/decisions.md
docs/planning/investment-philosophy-draft.md

git log -1 --oneline
42993b1 docs: record initial planning foundation

git ls-remote origin HEAD refs/heads/main refs/heads/feat/granges-walkthrough
42993b1c30805ee1f7d0e2c7f0a28b5069267240 HEAD
42993b1c30805ee1f7d0e2c7f0a28b5069267240 refs/heads/main
```

The working branch has no returned remote ref. `gh-axi repo view KapKnudz/betaforge-reborn` reported visibility `private` and default branch `main`. The remote is [KapKnudz/betaforge-reborn](https://github.com/KapKnudz/betaforge-reborn). These results establish the local tracked inventory and the queried remote refs; they do not claim an audit of all remote history.

## Recommended first checkpoint

Review this explicit inventory before staging, rather than adding the entire workspace:

1. **Project rules and navigation:** `.gitignore`, placeholder-only `.env.example`, `README.md`, `GLOSSARY.md`.
2. **Decisions and philosophy:** the existing `docs/planning/` files, accepted `docs/adr/`, retrieval and Codex integration documentation.
3. **Current implementation:** `betaforge/`, `scripts/`, `tests/`, and dependency declarations. Preserve the older pi experiment as a clearly separate reproduction path.
4. **Research and compact provenance:** `docs/research/`, walkthrough questions/protocol/rubric, selected report facts, source manifest, comparison review, probability illustration records and public Swagger schema/source metadata. Review the selected extracted report excerpts before including them; the first checkpoint does not require every QA extract.
5. **A small handoff index:** identify the code commit, analysis date, packet identity and the separately stored completed-result bundle. Existing hashes and manifests should be reused rather than copied into a second bespoke tracking system.

Keep `.env.local`, authentication files, `.venv`, caches, IDE configuration, raw provider/PDF bodies, databases, traces and generated review pages outside the source checkpoint. Current `.gitignore` covers the main data/secret/cache paths but does not exclude the entire `.idea/` directory, which appears among untracked candidates. Some individual IDE files are ignored by other local rules; a portable repository rule is preferable. [Ignore rules](../../.gitignore), [README credentials](../../README.md#L24), [Git inventory](#git-inventory).

File metadata showed approximately 81 KB of current package source, 92 KB of scripts, 30 KB of tests and 227 KB of untracked documentation at inspection time. New review notes can change the counts. No individual source/doc candidate examined by metadata approaches the large local packet/run sizes. These are file-size observations, not a content-level secret review.

## Minimal workstation workflow

1. **Source:** commit and push the reviewed code/docs checkpoint to the existing private repository after the user approves the plan. On another workstation, clone the same commit/branch.
2. **Environment:** install the documented Python/PDF prerequisites and a verified Codex build, supply the executable through the existing override if needed, create local `.env.local`, and authenticate Codex separately. Preserve no credential values in Git. [README setup](../../README.md#L24), [Codex entry point](../codex-integration.md#L5).
3. **Exact completed analysis:** first inventory and privately preserve the selected frozen packet, completed Codex run and earlier pi comparison outputs. Record a digest of the exact archive: existing packet/evidence identities do not cover every saved answer, review or trace. Then restore the bundle into its documented locations on the second Mac, verify the archive and existing evidence identities, and open or render the saved result. The current packet is about **99.7 MB** and the current run about **79.3 MB** in logical file sizes. A private bundle is manageable for this example and avoids expanding ordinary Git history with raw research artifacts. [Packet preparation](../../scripts/prepare_codex_packet.py#L45), [renderer](../../scripts/render_codex_walkthrough.py#L81).
4. **Ongoing research state:** back up the canonical `data/evidence` database together with its blobs, not just the SQLite file, if the goal includes maintaining the whole watchlist across machines. Individual frozen packets preserve a particular analysis but are not a substitute for the current watchlist store. [Freeze implementation](../../betaforge/storage.py#L578), [ingestion CLI](../../scripts/ingest_evidence.py#L15).
5. **Resume:** initially support viewing completed work or starting a new explicitly identified analysis on either workstation. Keep same-thread live resume as an additional capability until a second-machine transfer is verified. [Resume contract](../codex-integration.md#L44).

Several retained documentation links contain the current workstation's absolute `/Users/kasperknudas/...` path. Convert navigational links to repository-relative links when preparing the source checkpoint; keep original provenance inside frozen records intact. Inspected examples are the [philosophy application note](granges-philosophy-application.md) and [retrieval design](../retrieval-design.md). This separates convenient document navigation from evidence identity.

## Open decision

The user subsequently confirmed **Macs first** and **exact evidence plus saved analyses**. Private Git for source and decisions, plus a private byte-preserving archive for completed research, is therefore the proposed handoff approach. Exact historical evidence and active Codex conversation state need different handoff checks. The archive destination and live-thread migration remain open; no storage transfer was implemented by this review.
