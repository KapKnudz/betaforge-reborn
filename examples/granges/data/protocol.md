# Gränges report-exposure experiment

Frozen before candidate answers on 2026-11-01. One run per arm; this is a feasibility and evidence-handling probe, not a general benchmark or complete valuation.

## Fixed evidence and task

Eight original English PDFs: annuals 2021–2025 and Q1, H1 and Q3 2026. The source manifest preserves original URLs and hashes. The shared prepared corpus contains all 921 physical pages, 3,146,886 characters and 484,068 whitespace-delimited words, including page markers. Native text extraction has known table spacing and reading-order limitations. Original page images remain available in both arms. Extraction is not a guarantee of semantic fidelity.

The eight questions in `questions.json` were prepared independently from the sources before candidate answers. The answer key is withheld from the model. No Börsdata values, web search, outside documents or other agents are available in either arm. All numeric work must use the same calculation tool with source references.

## Model and harness

Both arms use GPT-6.1 Sol with high reasoning through the installed pi harness. The exact model succeeded in a tool-free preflight. The installed Codex CLI rejected the model through its ChatGPT route, so the harness is held constant at pi for this experiment. Native tools, MCP, other extensions, skills, prompt templates and context files are disabled. Only the four corpus-bound tools are enabled: `read_report`, `search_reports`, `view_report_page`, `calculate`.

## Arms

- **Upfront:** the entire prepared corpus is appended to the initial prompt, along with the same index and questions. Automatic compaction is disabled so a context overflow cannot silently become a summary experiment. The same verification and calculation tools remain available. A rejected initial request is a feasibility result, not a scored answer and not permission to shorten the corpus.
- **Tools:** only the index and questions are supplied initially. The model is instructed to read every report page using bounded complete-page reads, then use targeted search, images and calculations. Automatic compaction is enabled to allow a long sequential reading workflow; compactions are recorded. This is an explicit difference between the chosen configurations and may lose earlier details.

The common system prompt and per-arm prompts are saved in the runner and run directories. Source files cannot be selected arbitrarily through the tool API. A tool audit records exact delivered page ranges, searches, viewed images and calculations. A search hit does not count as a full read. Delivered pages demonstrate exposure, not comprehension.

## Execution controls

Each arm has a two-hour outer deadline. The controller waits for `agent_settled`, not `agent_end`; it clears the queue, aborts and uses bounded process termination if needed. Automatic provider retries are disabled. At most ten additional prompts can recover incomplete mandatory reading. Two consecutive recovery rounds with no new pages or newly viewed page images stop the run. This progress measure is a narrow mechanical proxy; it is not a semantic judgment that all research questions are resolved.

If all mandatory pages have been exposed and the initial answer is complete, no additional research prompts are needed. The controller does not inject reference-answer corrections. Raw events, the final answer, tool audit, timing, usage and errors are retained. Pi-reported dollar estimates are provider rate estimates, not a statement about charges to the user's subscription.

## Evaluation

An independent reviewer scores source-supported answers, periods and units, calculations, citations, contradictions and missing evidence against eight questions totaling 40 points. Record coverage separately from answer quality. If the upfront arm cannot fit, report that the quality comparison was not completed; a successful tools answer cannot demonstrate that it is inherently more accurate than a feasible upfront answer.

The company is Large Cap and the actual source acquisition used issuer-IR PDFs. This run does not validate a small-company population, MFN scraping, Börsdata ingestion, the future website or a production valuation process.

## Observed execution facts

Both runs completed on GPT-6.1 Sol with the same questions and unchanged prepared-source hashes. The upfront request was accepted with 763,408 reported input tokens despite the pi model listing describing a 500K context. This observation establishes acceptance of this request on this route; it does not establish a maximum supported context size.

Upfront completed in 361.502 seconds with no compaction. Tools completed in 413.068 seconds with all 921 pages delivered and one threshold-triggered compaction. The compaction observer recorded start at 2026-11-01T14:55:10.656893Z and end at 2026-11-01T14:55:59.941556Z; these are local observation times, not exact provider timestamps. Compaction reported 26,569 input and 1,775 output tokens, separately from assistant-message usage.

These are two actual workflow configurations, not a controlled estimate of exposure method alone: compaction differs, the number and grouping of tool calls differ, and there is one run per arm. Model-run times exclude shared acquisition and PDF preparation. The derived `runs/comparison-summary.json` preserves assistant usage, compaction usage and combined totals separately. Cached processing counts are not unique document-token counts or a statement of subscription charges. No provider-reported dollar estimate is presented as actual billing.
