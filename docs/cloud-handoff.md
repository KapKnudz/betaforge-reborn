# Continue in Codex Cloud

Git carries code, draft skills and the current plan. Exact provider data, PDFs, transcripts and saved memos remain in private research archives. Cloning this public repository alone does not restore the company analyses.

## Prepare the environment

1. Choose **Work in → Cloud → Create environment** and select `KapKnudz/betaforge-reborn`. Use the published working branch until its PR is merged; then use `main`.
2. Ask setup to install Python (3.14.7 is tested locally), Node.js for the JavaScript checks, and Poppler (`poppler-utils` on Debian/Ubuntu). Run from the repository root:

   ```sh
   python3 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python -m unittest discover -s tests -v
   git diff --check
   ```

3. For code development, no Börsdata credential is needed. To work with preserved analyses, restore the selected private release using [the archive instructions](research-handoff.md#restore). Authenticate separately; never copy local `.env` or Codex authentication files into Git.
4. Test the setup, save it and **Publish**. Keep an environment containing private research private. New tasks use the published setup; existing tasks retain their own working state. See [OpenAI's current Cloud environment guide](https://learn.chatgpt.com/docs/environments/cloud-environments).

## Start a working session

Read `AGENTS.md`, `work/plan.json` and the affected source files. Follow the plan and update its handoff. The analysis guides remain drafts under `docs/skill-drafts/`; their presence does not automatically load them into a valuation run. Follow [the analysis workflow](analysis-workflow.md) to freeze the selected guides explicitly.

Start the progress website with `.venv/bin/python scripts/serve_progress.py`. A cloud `127.0.0.1` address is not the local Mac's server. The viewer has no user authentication and requires loopback access. Do not tunnel or publicly forward a viewer containing private exports. Verify a private, authenticated cloud viewing path before loading research; otherwise use the public-only progress view or inspect saved files directly. See [the viewer boundaries](saved-analysis-view.md).

## Verify before a new valuation

- Resolve an available Codex executable and pass `--codex`; the default application path is Mac-specific. Cloud agent access does not itself establish that the nested analysis runner is authenticated or supported.
- Confirm Sol/xhigh is available, following [model routing](model-routing.md). Do not silently substitute a model.
- Confirm `pdftoppm` is on PATH (or set `BETAFORGE_PDFTOPPM`), and that restored packet files and hashes validate.
- Run a bounded tool smoke before a full analysis. Local saved-result validation is not evidence of a successful cloud model run.

Local tests and memo viewing have been exercised on the Mac. Linux/cloud setup, private-release access, preview access and the nested runner still require verification in the actual cloud environment. Local personal skills and command wrappers are not portable dependencies; use repository instructions and available equivalent tools.
