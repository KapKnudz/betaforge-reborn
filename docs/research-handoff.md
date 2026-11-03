# Move exact research between Macs

Git preserves code, tests, decisions, policy and compact reports. Exact source evidence and saved runs travel in a separate private archive. Each Mac keeps its own Börsdata credential and Codex authentication; neither belongs in an archive or Git.

## Verified private checkpoint

The [private GitHub release `research-baseline-2026-11-03`](https://github.com/KapKnudz/betaforge-reborn/releases/tag/research-baseline-2026-11-03) targets source commit `5678dd1de282b7b5569ff6acc7c68ff72f7cc194`. Its `research-2026-11-03-foundation.tar.gz` contains 432 files, 456,847,456 source bytes and 226,352,173 compressed bytes. SHA256:

```text
9d77f82a592c184153e0f2e01e441276e0818ddf10f5228eaaae291579bb47d3
```

The GitHub digest and a fresh download matched that checksum. A clean clone restored all 432 files, verified both database manifests and their 87 blobs each, then rendered the completed 921-page/326-calculation walkthrough without fetching data or calling a model. This was a clean-directory test on the current Mac; a second physical Mac and live conversation migration were not tested. The outside Downloads watchlist is not included. The archive manifest inventories paths and sizes; its whole-archive digest covers the exact bytes, including saved outputs.

## Mac prerequisites

The [current implementation release `research-quality-2026-11-03`](https://github.com/KapKnudz/betaforge-reborn/releases/tag/research-quality-2026-11-03) additionally preserves the new frozen policy packet, completed integration smoke, final quality review and benchmark source snapshots. Its archive is `research-2026-11-03-quality.tar.gz`; use its own checksum and manifest. The release tag identifies the corresponding source commit. The earlier baseline release remains the unchanged historical checkpoint.

The current bundle also includes the exact user-supplied watchlist at `data/watchlists/20261103-original/Knudz_Watchlist.csv`, with a local manifest. It is 3,592 bytes, SHA256 `b84d9cdf998765a7cd2bdb8219d717daa5c034e9f5e152120df775602c761c6e`. The CSV stays outside Git history. Its original Downloads location is not required after restore; the historical baseline bundle did not include it.

Python 3.14.7 is the tested version. Install Python and Poppler, create a local environment and install the complete pinned dependencies:

```sh
brew install python@3.14 poppler
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

Use the desktop Codex login on each Mac. The controller's default binary is `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`; use `--codex` if that Mac has a different verified installation. Do not transfer login files. Put only that Mac's Börsdata key in ignored `.env.local`; no key is needed to render saved evidence.

`pdftoppm` must be on PATH for original-page images. Alternatively set `BETAFORGE_PDFTOPPM` to a local Poppler executable. In the current managed environment, Homebrew's fontconfig post-install step failed, so the verified desktop runtime's Poppler 26.05.0 was used through that override. The renderer path is workstation setup, not research evidence.

Download the private release with an authenticated GitHub CLI:

```sh
gh release download research-quality-2026-11-03 \
  --repo KapKnudz/betaforge-reborn --dir /absolute/path/private-download
```

Choose the source commit for historical reproduction, or the current implementation branch `feat/granges-walkthrough` for the new policy and tools. The original evidence packet and saved result remain separate from newer runs.

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
