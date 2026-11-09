# Continue in Codex Cloud

Git carries code, project Codex configuration, draft skills and the current plan. Exact provider data, PDFs, transcripts and saved memos remain in private research archives. A public clone alone does not restore company analyses.

## Prepare the environment

1. Select `KapKnudz/betaforge-reborn` on `main`; PR #18 is merged. Keep `KapKnudz/betaforge-research-private` available for release assets. Preserve existing checkout edits when fetching newer code.
2. Use Python, Node.js for the JavaScript checks, and Poppler (`poppler-utils` on Debian/Ubuntu). Python 3.14.7, Node 24 and Poppler have been exercised in Cloud. Reuse a valid project virtual environment. To create one, select the intended interpreter explicitly; `BETAFORGE_PYTHON` can contain its absolute path:

   ```sh
   if [ ! -x .venv/bin/python ]; then
     "${BETAFORGE_PYTHON:-python3.14}" -m venv .venv
   fi
   .venv/bin/python --version
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python -m pip check
   node --version
   pdftoppm -v
   .venv/bin/python -m unittest discover -s tests -v
   git diff --check
   ```

   Do not recreate an existing virtual environment with a different Python version. No additional service, container or provider credential is needed for offline development.
3. Authenticate GitHub separately and restore selected private releases using [the archive instructions](research-handoff.md#restore). Verify checksums and member paths before extracting into clean staging. Copy into ignored research paths only when absent or byte-identical. Preserve a conflicting database, packet or run as a complete separate version; do not overlay different immutable bundles.
4. For a reusable environment, use **Edit**, test the setup, **Save** and **Publish** when those controls are available. Preserve both repository entries and private access. Updating one task checkout does not update or republish the reusable environment; verify a fresh task after publication. See [OpenAI's Cloud environment guide](https://learn.chatgpt.com/docs/environments/cloud-environments).

## Match the project Codex settings

Read `AGENTS.md`, `work/plan.json` and the affected source files. The committed `.codex/config.toml` selects Sol/xhigh, and `.codex/agents/` defines the existing model roles. Follow [model routing](model-routing.md); do not replace these roles with an available alternative model.

Codex can ignore project-local configuration until the checkout is trusted. Check effective settings and disabled configuration layers in the current client. Trust only the intended inspected repository through the supported trust flow; do not change global model, provider, approval or sandbox defaults to compensate. Strict configuration validation checks syntax and supported fields; it does not prove that a project layer loaded or that live model access works. For an individual plain CLI invocation, the documented model settings can be explicit:

```sh
codex -m gpt-6.1-sol -c 'model_reasoning_effort="xhigh"'
```

The valuation runner already passes Sol/xhigh explicitly. Its evidence-tool restrictions remain separate from ordinary project development. Local personal skills and wrappers are not portable dependencies. The analysis guides remain drafts under `docs/skill-drafts/`; follow [the analysis workflow](analysis-workflow.md) to freeze the selected guides explicitly rather than activating historical packets or installing drafts automatically.

Never copy Mac `.env`, Codex authentication or account configuration into Cloud or Git. Authenticate the Cloud executable separately. `codex login status` can report a saved login whose token no longer refreshes; a successful bounded live check is separate evidence.

## Open the workbench

Start the existing read-only viewer:

```sh
.venv/bin/python scripts/serve_progress.py
```

A Cloud `127.0.0.1` address belongs to the Cloud machine. In a supported Cloud chat, open the right side panel, then **New tab (+) → Desktop**, and open `http://127.0.0.1:8765` in Cloud Chrome. Shared Cloud Desktop viewing has been exercised; the same address in the Mac browser reaches a different machine. If browser DOM control is unavailable, native Cloud desktop control can still work.

Refresh Cloud Chrome after frontend edits; restart the Python server after server-code changes or to adopt different saved exports. The plan refreshes automatically. The viewer has no user authentication and binds only to loopback. Do not tunnel or publicly forward private exports. If an authenticated private desktop or preview is unavailable, report HTTP/file verification separately from visual verification. See [viewer boundaries](saved-analysis-view.md).

After restoring the corresponding private files, both latest Lime versions can be selected explicitly:

```sh
.venv/bin/python scripts/serve_progress.py \
  --analysis data/saved-views/lime-updated-skills-20261109.json \
  --analysis data/saved-views/lime-business-brief-20261109.json
```

Add an explicitly restored corpus manifest and read-only market database only when needed, following [saved-result viewing](saved-analysis-view.md). A stored quote is dated context; opening the viewer never refreshes provider data or reruns a valuation.

## Restore earlier research when needed

The [9 November checkpoint](https://github.com/KapKnudz/betaforge-research-private/releases/tag/cloud-research-2026-11-09) contains recent AQ/Lime pilots, saved views, audit notes, investor-writing originals and benchmarks. Its manifest records application commit `d29d4ad`; later source changes do not rewrite saved runs. It supplements earlier releases.

| Needed evidence | Earlier private release |
|---|---|
| Original Gränges packet/run and quality facts | `research-quality-2026-11-03` |
| Current-period Gränges facts | `material-review-2026-11-04` |
| Structured Gränges policy analysis | `policy-analysis-2026-11-04`, version 3 archive |
| Thirty-company API corpus and catalogue | `development-corpus-30-2026-11-03` |
| Nine companies' original reports and packets | `nine-company-packets-2026-11-05` |
| Their completed results and reviews | `nine-company-results-2026-11-05`, after the packets release |

Use the [example restore guidance](../examples/granges/README.md) for legacy fact paths. Missing earlier evidence can skip a private test class even when all public tests pass. Keep those skips explicit.

Twenty-five of the 26 exports in the 9 November checkpoint validate with the current viewer. Preserve historical `granges-20261101.json` unchanged and exclude it: its older provenance shape is incompatible. Both latest Lime exports are compatible. Check other restored exports before configuring them; do not overwrite or migrate originals merely to populate the viewer.

## Verify before a new valuation

- Resolve and inspect the Cloud Codex executable. The runner now discovers `codex` on PATH; `--codex` can select a verified installation explicitly. Cloud agent access does not establish nested-runner authentication.
- Confirm actual Sol/xhigh access, following [model routing](model-routing.md). A model catalogue is a capability description, not a successful model run.
- Confirm `pdftoppm` is on PATH, or use `BETAFORGE_PDFTOPPM`, and verify frozen database, source, report and contract hashes.
- Run a separately identified bounded tool smoke using the [existing runner](codex-integration.md). Preserve original packets and saved results. Relocating or preparing a runnable packet is separate from restoring an export; changed implementation hashes require a new run.

If authentication or the required model is unavailable, finish offline/data/viewer checks and record the exact remaining limitation. Do not substitute a model or describe saved-result validation as a successful Cloud valuation run.
