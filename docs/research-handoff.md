# Private research and workstation handoff

The public code repository holds reusable code, policy, tests and reference examples. Exact PDFs, provider captures, frozen databases, watchlists and saved analyses belong in [the private research repository](https://github.com/KapKnudz/betaforge-research-private/releases), which must remain private. Credentials and Codex authentication stay local to each Mac and are excluded from both Git and bundles.

The two original research releases were copied unchanged to private storage after the code repository became public. All nine archive/verification files matched their original sizes and SHA256 hashes; public attachments were removed. The [worked-example handoff record](../examples/granges/docs/granges-research-handoff.md) preserves exact checksums, source commits and restore results. Removing public attachments cannot recall prior downloads.

## Mac prerequisites

Python 3.14.7 is the tested version. Install Python and Poppler, create the local environment and install the pinned dependencies:

```sh
brew install python@3.14 poppler
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

The default Codex binary is `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`. Supply `--codex` for another verified local installation and authenticate separately on each workstation. Put the acquisition key in ignored `.env.local`. Saved-result viewing and deterministic replay need no provider credential.

`pdftoppm` must be on PATH for original-page images, or set `BETAFORGE_PDFTOPPM` to its executable. The desktop runtime's Poppler 26.05.0 has also been exercised through that override. The executable path is workstation setup, not source evidence.

## Create a versioned private bundle

Stop acquisition and analysis writes first. Explicitly select the saved company evidence and results to preserve; no company or dated run is included automatically:

```sh
.venv/bin/python scripts/archive_research.py \
  --include data/packets/company-snapshot \
  --include data/runs/company-analysis \
  --db data/evidence/evidence.sqlite3 \
  --output data/backups/research-version.tar.gz
```

Repeat `--include` for captured sources, benchmarks, watchlists or `examples/<case>/data` as needed. Includes must be reviewed repository-relative research subpaths under `data/` or `examples/<case>/data`; the repository root, home directories, configuration paths, symlinks and backup output are rejected. Overlapping includes are deduplicated. The output must sit outside its selected inputs.

Pass the live store through `--db`, rather than including its directory. The existing SQLite freeze implementation creates a consistent database backup with verified source blobs, archived under the store's repository-relative parent. The default is `data/evidence/evidence.sqlite3`; a different company's store can be supplied explicitly. Do not place the archive inside that live store.

The command refuses an existing archive or sidecar and writes:

- `.tar.gz`: selected exact files plus the consistent store freeze.
- `.tar.gz.sha256`: SHA256 covering the whole archive, including saved outputs.
- `.tar.gz.manifest.json`: application Git identity/worktree status, source paths/database, member paths/sizes and archive checksum.

The bundle is not encrypted by the command. Upload it only to private storage. A source checkpoint with local changes is recorded honestly and cannot be presented as reproducible from its HEAD commit alone. This is a selected research archive, not a filesystem backup.

## Restore

Authenticate GitHub on the receiving Mac and download a selected release:

```sh
gh release download "$RESEARCH_TAG" \
  --repo KapKnudz/betaforge-research-private --dir /absolute/path/private-download
```

Use the application source commit from the archive manifest to check out code in the public code repository. Tags in the separate storage repository identify its README history, not application code. Verify the checksum before extraction:

```sh
shasum -a 256 -c research-version.tar.gz.sha256
tar -tzf research-version.tar.gz
tar -xzf research-version.tar.gz -C /absolute/path/to/clean/betaforge-reborn
```

Extract into a clean clone or separate clean restore directory, never over a store or analysis currently in use. Paths inside the archive remain repository-relative. Preserve the database, manifest and blobs together. Legacy bundles retain their original private data paths; use the corresponding [example replay commands](../examples/granges/README.md) with current code, or the recorded code checkpoint for historical reproduction.

Completed-result restoration and active Codex conversation migration are separate. A clean-clone restore/render/replay has passed on the current Mac. A physical second Mac and same-thread live resume there remain unverified. Do not transfer authentication files. See [Codex integration](codex-integration.md).
