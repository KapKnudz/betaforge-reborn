# Move exact research between Macs

Git preserves code, tests, decisions, policy and compact reports. Exact source evidence and saved runs travel in a separate private archive. Each Mac keeps its own Börsdata credential and Codex authentication; neither belongs in an archive or Git.

## Create an archive

First stop acquisition and analysis writes. The archive command refuses to overwrite an existing version:

```sh
.venv/bin/python scripts/archive_research.py \
  --output data/backups/research-2026-11-03.tar.gz
```

It includes the existing Gränges frozen packet and completed Codex run, the original pi reports/preparation/runs/QA and compact research metadata, Börsdata captures, and a consistent snapshot of the canonical evidence database plus its source blobs. The live database is copied through the existing SQLite backup/freeze implementation. Research symlinks are rejected. Environment/configuration directories and credential filenames are excluded from the fixed selection.

The command writes three files:

- `research-2026-11-03.tar.gz`: exact selected research bytes, with a consistent canonical-store copy.
- `research-2026-11-03.tar.gz.sha256`: checksum covering the whole archive, including saved answers and traces.
- `research-2026-11-03.tar.gz.manifest.json`: source Git commit/worktree status, relative file inventory, sizes and archive checksum.

Keep all three privately. The archive is not encrypted by this command. It contains financial research and model traces, so use authenticated private storage. The source Git commit is the HEAD at capture; the manifest also flags local tracked/untracked work. A dirty checkpoint must not be presented as fully reproducible from that commit alone.

The fixed paths deliberately cover the existing research, not an arbitrary filesystem backup. Add an explicit reviewed path when another company/run needs preservation. Do not point this workflow at home directories, authentication stores or live research running on both Macs.

## Restore on the second Mac

Clone the recorded source checkpoint, install its Python/PDF prerequisites and authenticate Codex separately. Download the archive and sidecars from the selected private storage. In the download directory, verify before extracting:

```sh
shasum -a 256 -c research-2026-11-03.tar.gz.sha256
tar -tzf research-2026-11-03.tar.gz
```

Extract into a clean clone or a separate clean restore directory, never over a database or result directory currently in use:

```sh
tar -xzf research-2026-11-03.tar.gz -C /absolute/path/to/clean/betaforge-reborn
```

The archive uses repository-relative paths, so existing packet/report paths resolve after restoration. Render the saved analysis without reacquiring data or running the model:

```sh
.venv/bin/python scripts/render_codex_walkthrough.py
```

The original frozen packets stay unchanged. The canonical `data/evidence` restored from this archive is a consistent backup, with the freeze manifest alongside it. Preserve its database and blobs together.

Moving completed evidence/results is separate from continuing an active Codex conversation: same-thread resume on a second Mac is not yet verified. Do not copy authentication files to make it work. See the [portability review](research/version-control-portability-review.md) and [Codex integration](codex-integration.md).
