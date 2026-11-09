(() => {
  function renderProcess() {
    const host = document.getElementById("process-view");
    if (!host || host.dataset.processRendered) return;
    host.dataset.processRendered = "true";
    host.classList.add("process-view");
    host.innerHTML = `
      <header class="process-heading">
        <p class="process-kicker">HOW BETAFORGE WORKS</p>
        <h2>System architecture and analysis</h2>
        <p>Preserve the sources. Explain a few earnings drivers. Calculate openly and challenge the conclusion.</p>
        <a href="/docs/docs/analysis-process.md" target="_blank" rel="noopener">Read the full process guide ↗</a>
      </header>

      <section class="process-section" aria-labelledby="process-architecture-title">
        <div class="process-section-heading"><span class="process-section-number">A</span><div><h3 id="process-architecture-title">The technical architecture</h3><p>Sources become a frozen input set, then saved results for the Company reader.</p></div></div>
        <ol class="process-map" aria-label="Technical data flow, in order">
          <li><span class="process-node-number">01</span><h4>Collect</h4><p>Börsdata API captures and selected reports from issuer sites or MFN.</p></li>
          <li><span class="process-node-number">02</span><h4>Preserve</h4><p>Raw captures, SQLite observations and original source files.</p></li>
          <li><span class="process-node-number">03</span><h4>Freeze</h4><p>One company packet: sources, cutoff, policy and formula catalogue.</p></li>
          <li class="process-analyst-node"><span class="process-node-number">04</span><h4>Analyze</h4><p>Codex analyst<br>↕ bounded evidence tools</p><div class="process-formula-node">↔ Named Decimal formulas</div></li>
          <li><span class="process-node-number">05</span><h4>Save &amp; export</h4><p>Report, inputs, calculations, audit records and review when obtained.</p></li>
          <li><span class="process-node-number">06</span><h4>Read</h4><p>Company viewer opens configured saved results.</p></li>
        </ol>
        <div class="process-storage"><p><strong>Public repository</strong>Code, policies, documentation and delivery status.</p><p><strong>Private research</strong>Raw evidence, frozen packets, analyses and reviews. Credentials stay local and separate from research archives.</p></div>
        <p class="process-note">Opening this workbench reads saved files. It does not fetch research, call a model or launch an analysis. The map describes the system, not live activity.</p>
      </section>

      <section class="process-section" aria-labelledby="process-skills-title">
        <div class="process-section-heading"><span class="process-section-number">B</span><div><h3 id="process-skills-title">Skills</h3><p>Draft guides for manual use. Full references are in the repository.</p></div></div>
        <ol class="process-skills">
          <li><h4><a href="/docs/docs/skill-drafts/betaforge-market-peer-research/SKILL.md" target="_blank" rel="noopener">Market and peer research ↗</a></h4><p><strong>Before freezing evidence.</strong> Compare peers or check up to three material questions left open by issuer reports.</p></li>
          <li><h4><a href="/docs/docs/skill-drafts/betaforge-company-analysis/SKILL.md" target="_blank" rel="noopener">Company analysis and valuation ↗</a></h4><p><strong>Before selecting forecasts.</strong> Write a short business brief from preserved evidence.</p></li>
          <li><h4><a href="/docs/docs/skill-drafts/betaforge-financial-report/SKILL.md" target="_blank" rel="noopener">Financial report writing ↗</a></h4><p><strong>While drafting the memo.</strong> The lead analyst writes the structured report and cites the evidence.</p></li>
          <li><h4><a href="/docs/docs/skill-drafts/betaforge-valuation-review/SKILL.md" target="_blank" rel="noopener">Independent valuation review ↗</a></h4><p><strong>After the draft.</strong> A separate reviewer challenges the draft against its evidence and calculations.</p></li>
        </ol>
      </section>

      <section class="process-section" aria-labelledby="process-analysis-title">
        <div class="process-section-heading"><span class="process-section-number">C</span><div><h3 id="process-analysis-title">From evidence to an investment case</h3><p>One lead analyst, a separate independent reviewer, and a coordinator who connects them.</p></div></div>
        <dl class="process-roles" aria-label="Responsibility legend">
          <div><dt><span class="process-badge process-code">Code-enforced</span></dt><dd>Identity, tool access, arithmetic and structural checks.</dd></div>
          <div><dt><span class="process-badge process-judgment">Agent judgment</span></dt><dd>Business meaning, forecasts, probabilities and challenge.</dd></div>
          <div><dt><span class="process-badge process-coordinator">Coordinator · session policy</span></dt><dd>Select the question, dispatch review and preserve its result.</dd></div>
        </dl>
        <h4 class="process-decisions-title">The analyst’s stated decisions</h4>
        <ol class="process-decisions" aria-label="How the analyst builds and tests the case">
          <li><h4>Business &amp; drivers</h4><p>Explain why customers buy and which developments could change earnings or cash needs. Choose three to five earnings and cash drivers.</p></li>
          <li><h4>Cash &amp; ownership</h4><p>Trace working capital, reinvestment and financing. Explain cash conversion, share compensation and dilution.</p></li>
          <li><h4>Operating assumptions</h4><p>Choose one earnings equation. Explain the evidence, business mechanism and magnitude behind each material forecast.</p></li>
          <li><h4>Scenarios &amp; value</h4><p>Support the multiple and any scenario weights. Bridge earnings through claims and future shares to value and shareholder return.</p></li>
          <li><h4>Disconfirm &amp; challenge</h4><p>Test modest disappointments and thesis-breaking evidence. A separate reviewer challenges the saved case.</p></li>
        </ol>
        <p class="process-note">Inspect saved facts, interpretations and assumptions, report-page citations, input IDs, forecast rationales and calculation records. Probability rationales and review findings are available when saved.</p>
        <p class="process-equation"><strong>Current primary method</strong><span>Operating earnings × selected EV/EBIT multiple → enterprise value → claims and shares → shareholder value</span></p>
        <p class="process-note">The analyst chooses and explains assumptions; named formulas perform the arithmetic outside the model. Material inputs and formulas remain inspectable. A full DCF or reverse DCF is not implemented.</p>

        <ol class="process-stages" aria-label="Analysis stages; open a stage for inputs, outputs, checks and limits">
          <li><details id="process-stage-freeze"><summary><span class="process-stage-number">1</span><span class="process-stage-title">Set the question &amp; freeze the evidence<small>A dated company, price and report corpus.</small></span><span class="process-badge process-coordinator">Coordinator</span><span class="process-badge process-code">Code</span></summary><div class="process-stage-body">
            <dl><div><dt>Inputs → outputs</dt><dd>Explicit company, cutoff, dated price, required reports and mapping decisions → frozen database, source files, report index, policy and packet hashes.</dd></div><div><dt>Code-enforced</dt><dd>Verify the selected instrument and database, source, report and contract identities. Reject missing selected required reports or changed files.</dd></div><div><dt>Coordinator · session policy</dt><dd>Choose a sufficient corpus: normally at least five annual reports where available, plus relevant interims. Identify missing context.</dd></div><div><dt>Limit</dt><dd>Hash agreement proves identity, not completeness, freshness or correct financial definitions.</dd></div></dl>
          </div></details></li>
          <li><details id="process-stage-read"><summary><span class="process-stage-number">2</span><span class="process-stage-title">Read, reconcile &amp; save inputs<small>Keep facts, interpretations and assumptions distinguishable.</small></span><span class="process-badge process-judgment">Agent</span><span class="process-badge process-code">Code</span></summary><div class="process-stage-body">
            <dl><div><dt>Inputs → outputs</dt><dd>Frozen reports and observations → delivered-page coverage, source references, saved report-derived inputs and explicit assumptions.</dd></div><div><dt>Agent judgment</dt><dd>Read the business, reconcile accounting differences, inspect ambiguous source pages and select comparable periods and definitions. The draft guides add a business brief for manual use.</dd></div><div><dt>Code-enforced</dt><dd>Bound queries and search snippets; track full-page delivery separately. Report inputs need a physical page and a quote matching saved text. Inputs receive content-based IDs.</dd></div><div><dt>Limit</dt><dd>Delivered pages do not prove comprehension. A matching quote does not verify numeric extraction or accounting meaning; report inputs remain analyst-extracted.</dd></div></dl>
          </div></details></li>
          <li><details id="process-stage-model"><summary><span class="process-stage-number">3</span><span class="process-stage-title">Explain drivers &amp; calculate scenarios<small>One operating equation, cash needs and a complete equity bridge.</small></span><span class="process-badge process-judgment">Agent</span><span class="process-badge process-code">Code</span></summary><div class="process-stage-body">
            <dl><div><dt>Inputs → outputs</dt><dd>Saved observations and assumptions → named calculation records, bear/base/bull values, cash-flow return and disclosed sensitivities.</dd></div><div><dt>Agent judgment</dt><dd>Explain how the evidence shapes assumptions and sensitivities, and which findings remain context. Test growth, margins and capital needs together. Avoid counting the same operating or cash benefit twice.</dd></div><div><dt>Code-enforced</dt><dd>Use saved input IDs and Decimal formulas, applying each source scale once. Check known incompatible units, currencies and periods; retain formulas, versions, inputs, missing values and warnings.</dd></div><div><dt>Limit</dt><dd>The registry currently uses SEK, actual tonnes and actual shares. The analyst still owns economic scope and undated assumptions. Probability checks do not calibrate the weights; expected cash-flow IRR supports constant year-end dividends and a common integer-year horizon.</dd></div></dl>
          </div></details></li>
          <li><details id="process-stage-report"><summary><span class="process-stage-number">4</span><span class="process-stage-title">Submit a traceable report<small>Save the rationale beside its assumptions and calculations.</small></span><span class="process-badge process-judgment">Agent</span><span class="process-badge process-code">Code</span></summary><div class="process-stage-body">
            <dl><div><dt>Inputs → outputs</dt><dd>Saved evidence, inputs and calculations → six sections: thesis, drivers, financial quality, management, valuation and risks; dated scenario outputs and report artifact hashes.</dd></div><div><dt>Code-enforced</dt><dd>Validate section structure, paragraph labels, saved references, three scenarios and compatible endpoint dates. Require a reason for omitted probabilities or three saved weights that sum to one, each with a rationale and evidence references. Copy scenario values from saved valuation_case outputs. Structured completion requires mandatory page delivery and accepted submission.</dd></div><div><dt>Agent judgment</dt><dd>Write a short causal investment case, disclose uncertainty and show modest disappointments and disconfirming evidence. Explain the outcomes the scenarios cover. Propose weights only with a defensible basis. The user can override them.</dd></div><div><dt>Limit</dt><dd>Acceptance checks structure and identity, not economic truth. Management comparisons can be empty; meaningful rationale and adequate scenario coverage are not semantically enforced. The saved explanation is inspectable rationale, not a complete record of internal model deliberation.</dd></div></dl>
          </div></details></li>
          <li><details id="process-stage-review"><summary><span class="process-stage-number">5</span><span class="process-stage-title">Challenge independently &amp; revise once<small>Execution completion and economic review are separate.</small></span><span class="process-badge process-coordinator">Coordinator</span><span class="process-badge process-judgment">Reviewer</span></summary><div class="process-stage-body">
            <dl><div><dt>Inputs → outputs</dt><dd>Exact draft, frozen evidence, policy, inputs and calculations → saved independent findings, bounded verdict and unresolved evidence gaps; one explicit revision if justified.</dd></div><div><dt>Coordinator · session policy</dt><dd>Dispatch a fresh read-only reviewer and save its challenge. The reviewer is separate from the lead analyst; it challenges business mechanics, financial definitions, cash, scenarios and the shareholder bridge. There is no autonomous review service.</dd></div><div><dt>Code-enforced</dt><dd>Bind feedback to the packet and draft hash. Permit one explicit revision with at most two targeted research rounds and a cumulative 7,200-second structured analyst limit.</dd></div><div><dt>Limit</dt><dd>Hash binding identifies the reviewed draft; it cannot prove reviewer independence or review quality. A revised report needs a focused independent check and a review bound to its new hash. Preserve disagreement and stop if material issues remain.</dd></div></dl>
          </div></details></li>
          <li><details id="process-stage-view"><summary><span class="process-stage-number">6</span><span class="process-stage-title">Preserve, export &amp; inspect<small>The viewer presents an existing saved result.</small></span><span class="process-badge process-coordinator">Coordinator</span><span class="process-badge process-code">Code</span></summary><div class="process-stage-body">
            <dl><div><dt>Inputs → outputs</dt><dd>Completed report and audit artifacts, plus current review when present → validated saved-view export and privately archived research.</dd></div><div><dt>Code-enforced</dt><dd>Export rechecks artifact identity, required reading and calculation references. A supplied current review must match the report. The workbench exposes explicitly configured saved exports.</dd></div><div><dt>Coordinator · session policy</dt><dd>Save the final challenge and preserve sources, draft, feedback, report and review. Keep delivery status separate from evidence and investment confidence.</dd></div><div><dt>Limit</dt><dd>A completed unreviewed report can be exported. The export’s reviewed_at field records run completion, not proof of economic review. Inspect the separately saved current review.</dd></div></dl>
          </div></details></li>
        </ol>

        <details class="process-guardrails"><summary>Execution boundaries &amp; where to inspect them</summary><div class="process-guardrail-body"><p>The analyst receives only the bounded client-owned evidence tools. Native shell, browser, apps, connectors and delegation are disabled; unexpected native tool activity fails the run. The coordinator dispatches the reviewer outside that analyst process.</p><p>Initial research closes at ten recorded rounds, two recorded rounds without a newly cited retrieved evidence ID, or explicit finalization. Further evidence reads then stop; up to 200 finalization calls remain under the active deadline. These are current implementation limits, not proof that the investigation made semantic progress.</p><p>Source references: <code>betaforge/tools.py</code> (EvidenceTools), <code>financials.py</code> (evaluate), <code>analysis_report.py</code> (validate_report), <code>codex_runner.py</code> (_run_with_tools), <code>saved_view.py</code> (build_structured_saved_view). The full guide links each claim to its owning code or policy section.</p></div></details>
        <nav class="process-reading" aria-label="Process reference documents"><a href="/docs/docs/analysis-policy.md" target="_blank" rel="noopener">Investment policy ↗</a><a href="/docs/docs/calculations.md" target="_blank" rel="noopener">Named formulas ↗</a><a href="/docs/docs/analysis-workflow.md" target="_blank" rel="noopener">Review workflow ↗</a><a href="/docs/docs/codex-integration.md" target="_blank" rel="noopener">Tool contract ↗</a></nav>
      </section>`;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderProcess, { once: true });
  } else {
    renderProcess();
  }
})();
