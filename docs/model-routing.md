# Project model policy

Researched on 3 November 2026 against official OpenAI documentation. Betaforge uses `gpt-6.1-sol`/`xhigh` for its coordinating thinker and valuation runner. The user excludes Astra. The role assignments below are project decisions based on documented strengths; they are not benchmark results for this repository.

## Roles

| Role | Model / effort | Scope and escalation |
| --- | --- | --- |
| Thinker | `gpt-6.1-sol` / `xhigh` | Coordinate work, resolve architecture and accounting meaning, make financial judgments and integrate evidence. |
| Built-in `worker` | `gpt-6.1-sol` / `high` | Implement bounded changes and run appropriate checks. Return ambiguous design and financial definitions to the thinker. |
| `explorer` | `gpt-6-luna` / `high` | Narrow read-only file/source scans with a clear question and cited findings. Return ambiguity rather than making architectural or financial decisions. |
| `visual_evidence` | `gpt-6.1-terra` / `medium` | Inspect screenshots, UI states, PDF tables and layout. Cite the image or physical page; return financial interpretation to the thinker. |
| `reviewer` | `gpt-6.1-sol` / `high` | Fresh independent read-only review under the root review rules. Make no edits, start no code, test or model runs, grant no waivers and perform no merges. |
| Valuation runner | `gpt-6.1-sol` / `xhigh` | Analyze the frozen packet through the existing evidence tools and security restrictions. |

OpenAI describes [Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) as suited to complex coding and professional work, [Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra) to visual reasoning, computer use and writing, and [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) to focused, high-volume tasks. Their model pages support the chosen effort levels. The [model guide](https://developers.openai.com/api/docs/guides/latest-model) recommends starting Terra at `medium`; the [subagent guide](https://learn.chatgpt.com/docs/agent-configuration/subagents#choosing-models-and-reasoning) recommends Luna for narrow tasks and `high` for logic, assumptions and review. Betaforge therefore keeps implementation on Sol and uses Terra for visual evidence.

## Configuration and dispatch

The project `.codex/config.toml` sets `model = "gpt-6.1-sol"` and `model_reasoning_effort = "xhigh"`. Its `[agents]` section sets `default_subagent_model = "gpt-6.1-sol"` and `default_subagent_reasoning_effort = "high"`. The built-in worker uses those defaults. Three standalone files under `.codex/agents/` define `explorer`, `visual_evidence` and `reviewer`, each with an explicit model and effort. Concurrency, provider and approval settings remain governed by the existing session.

Official [custom-agent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents) resolves each setting from an explicit spawn value, then `[agents]` defaults, then the parent. A custom agent file overrides that resolved value. Our custom `explorer` overrides the built-in role of that name. The configured reviewer pins `high`; a spawn override cannot increase its effort. When review needs `xhigh`, use a fresh generic Sol/`xhigh` agent with the same independent read-only brief. Custom agents inherit the parent's permissions; read-only instructions do not create a separate sandbox.

When a harness does not expose these custom roles, explicitly select the table's model and effort in its spawn tool. Give a worker changing models a fresh brief containing the bounded task, relevant paths, constraints and required evidence. Use a full-history fork only when its inherited model and effort match the assigned role. The coordinating thinker remains responsible for integrating results and updating the plan.

If Luna or Terra is unavailable, explicitly select Sol at the assigned role's effort and report the substitution. If required Sol/`xhigh` is unavailable, stop and report the missing capability. Never silently fall back or select Astra.

## Effective settings and verification

[Configuration precedence](https://learn.chatgpt.com/docs/config-file/config-basic#configuration-precedence) places CLI flags and `--config` above trusted project defaults, and project defaults above user configuration. Untrusted projects skip project `.codex/` layers. Check the effective model and effort in a fresh run; the UI's selected model or an explicit invocation override may take precedence over defaults. Files written during an existing turn cannot retroactively change its executing model.

The valuation controller explicitly requests Sol/`xhigh` for thread configuration and each turn, records it in `run.json`, disables provider fallback and rejects a different returned model. Its offline fake-server regression checks those requests and saved metadata. This establishes request wiring; a live check is separate evidence of installed-client and account support. See [the runner contract](codex-integration.md) for its tools and execution limits.

Existing frozen packets, saved results and dated Sol/`high` smoke receipts retain their original meaning. The runner's existing implementation-hash check requires a separately identified run after this change; it does not rewrite or silently resume earlier runs with changed code.

On 3 November 2026, the installed `codex-cli 0.166.0-alpha.5.1` accepted strict configuration validation. Its effective project configuration reported Sol/`xhigh` and Sol/`high` subagent defaults; its model catalogue included all three assigned models and effort levels. A live Sol/`xhigh` smoke then completed financial queries, original-page image delivery and four calculations with no tool errors or unexpected native tools. This verifies the current client/account and runner path, not automatic task-routing quality or a full valuation. The first smoke exposed a missing PDF renderer on PATH; the successful separate run used the documented `BETAFORGE_PDFTOPPM` override. Private receipts are under `data/corpora-work/20261103-expansion30/` and `data/runs/model-routing-sol-xhigh-image-smoke-20261103/`.
