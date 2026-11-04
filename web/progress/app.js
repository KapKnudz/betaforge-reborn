"use strict";

const $ = (id) => document.getElementById(id);
const labels = { pending: "Pending", in_progress: "In progress", blocked: "Blocked", done: "Done" };
const publicDocs = new Set([
  "AGENTS.md", "CONTRIBUTING.md", "README.md", "docs/architecture.md", "work/README.md",
  "docs/analysis-policy.md", "docs/calculations.md", "docs/company-workflow.md", "docs/research/system-readiness-review.md",
  "docs/research/borsdata-retrieval-storage.md", "docs/codex-integration.md", "docs/saved-analysis-view.md",
]);
let currentPlan = null;
let loading = false;
let lastSuccess = null;
let lastPlanText = null;
let runsLoaded = false;
let runsLoading = false;
let runRequest = 0;
let loadedRunId = null;
const openTasks = new Set();

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function text(value) {
  if (value === undefined || value === null || value === "") return "Unavailable";
  return typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
}
function status(value) { return element("span", "status " + value, labels[value] || value); }
function documentReference(path, label) {
  if (!publicDocs.has(path)) return element("span", "unlinked", label);
  const link = element("a", "", label);
  link.href = "/docs/" + path;
  link.target = "_blank";
  link.rel = "noopener";
  return link;
}
function svgElement(tag, attrs, label) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
  if (label !== undefined) node.textContent = label;
  return node;
}
function progress(done, total, large = false) {
  const group = element("div");
  const percent = total ? Math.round(100 * done / total) : 0;
  if (large) {
    const figure = element("div", "progress-figure");
    figure.append(element("span", "progress-value", percent + "%"), element("span", "progress-caption", done + " of " + total + " tasks complete"));
    group.append(figure);
  }
  const bar = svgElement("svg", { viewBox: "0 0 100 7", preserveAspectRatio: "none", class: "progress-bar", role: "img", "aria-label": done + " of " + total + " tasks complete" });
  bar.append(svgElement("rect", { x: 0, y: 0, width: 100, height: 7, class: "progress-track" }), svgElement("rect", { x: 0, y: 0, width: total ? 100 * done / total : 0, height: 7, class: "progress-done" }));
  group.append(bar);
  if (!large) group.append(element("p", "progress-caption", done + " / " + total + " tasks complete"));
  return group;
}
function renderTasks(plan) {
  const list = $("task-list");
  for (const details of list.querySelectorAll("details[data-task]")) {
    if (details.open) openTasks.add(details.dataset.task);
    else openTasks.delete(details.dataset.task);
  }
  list.replaceChildren();
  const filter = $("filter").value;
  const tasks = plan.tasks.filter((task) => filter === "all" || (filter === "done" ? task.status === "done" : task.status !== "done"));
  for (const task of tasks) {
    const card = element("article", "task");
    card.id = "task-" + task.id;
    const side = element("div", "task-side");
    side.append(element("p", "task-id", task.id), status(task.status));
    side.append(element("p", "task-milestone", plan.milestones.find((item) => item.id === task.milestone).title));
    const body = element("div", "task-body");
    body.append(element("h3", "", task.title));
    if (task.summary) body.append(element("p", "note", task.summary));
    if (task.purpose) body.append(element("p", "purpose", "Why: " + task.purpose));
    if (task.blocker) body.append(element("p", "blocker", "Blocked: " + task.blocker));
    const details = element("details");
    details.dataset.task = task.id;
    details.open = openTasks.has(task.id);
    details.append(element("summary", "", "Completion criteria, notes & evidence"));
    if (task.note) details.append(element("p", "note", task.note));
    const criteria = element("ul");
    for (const criterion of task.acceptance) criteria.append(element("li", "", criterion));
    details.append(element("p", "detail-label", "Completion criteria"), criteria, element("p", "detail-label", "Evidence"));
    const evidence = element("div", "evidence");
    for (const path of task.evidence) evidence.append(documentReference(path, path));
    if (!task.evidence.length) evidence.append(element("span", "", "No evidence recorded yet."));
    details.append(evidence);
    body.append(details);
    card.append(side, body);
    list.append(card);
  }
  if (!tasks.length) list.append(element("p", "empty", "No tasks in this view."));
}
function render(plan) {
  $("goal").textContent = plan.goal;
  $("scope").textContent = plan.scope;
  $("overall-progress").replaceChildren(progress(plan.tasks.filter((t) => t.status === "done").length, plan.tasks.length, true));
  const counts = $("counts");
  counts.replaceChildren();
  for (const value of ["done", "in_progress", "pending", "blocked"]) {
    const count = element("div", "count");
    count.append(element("strong", "", String(plan.tasks.filter((task) => task.status === value).length)), element("span", "", labels[value]));
    counts.append(count);
  }
  const next = plan.tasks.find((task) => task.id === plan.next_task);
  $("next-title").textContent = next ? next.title : "Plan complete";
  $("next-note").textContent = next ? (next.blocker || next.summary || next.title) : "All recorded tasks are done. Agree the next goal before adding more work.";
  $("next-purpose").textContent = next && next.purpose ? "Why: " + next.purpose : "";
  $("next-link").hidden = !next;
  if (next) $("next-link").href = "#task-" + next.id;
  const roadmap = $("milestones");
  roadmap.replaceChildren();
  plan.milestones.forEach((milestone, index) => {
    const tasks = plan.tasks.filter((task) => task.milestone === milestone.id);
    const card = element("article", "milestone " + milestone.status);
    card.append(element("div", "milestone-number", String(index + 1).padStart(2, "0")), element("h3", "", milestone.title), element("p", "", milestone.summary), progress(tasks.filter((t) => t.status === "done").length, tasks.length), status(milestone.status));
    roadmap.append(card);
  });
  renderTasks(plan);
  $("session-summary").textContent = plan.session.summary;
  $("session-next").textContent = plan.session.next_step;
  $("references").replaceChildren(...plan.references.map((ref) => documentReference(ref.path, ref.label)));
  $("updated").textContent = "Plan updated: " + plan.updated_at;
  $("dashboard").hidden = false;
}
async function getJSON(url) {
  const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(8000) });
  if (!response.ok) throw new Error("Saved record unavailable");
  return response.json();
}
async function refresh() {
  if (loading) return;
  loading = true;
  $("refresh").disabled = true;
  try {
    const plan = await getJSON("/api/plan");
    const planText = JSON.stringify(plan);
    if (planText !== lastPlanText) {
      const firstPlan = currentPlan === null;
      render(plan);
      currentPlan = plan;
      lastPlanText = planText;
      revealTaskHash(firstPlan);
    }
    lastSuccess = new Date();
    $("error").hidden = true;
    $("connection").classList.remove("stale");
    $("connection").textContent = "Live plan · checked " + lastSuccess.toLocaleTimeString() + " · refreshes every 10 seconds";
  } catch (error) {
    $("error").hidden = false;
    $("error").textContent = lastSuccess ? "Could not refresh. Showing the last successful plan from " + lastSuccess.toLocaleTimeString() + ". Check work/plan.json and the local server." : "Could not load the plan. Check work/plan.json and the local server, then refresh.";
    $("connection").classList.add("stale");
    $("connection").textContent = lastSuccess ? "Disconnected · displayed plan may be stale" : "Plan unavailable";
  } finally {
    loading = false;
    $("refresh").disabled = false;
  }
}
function selectTab(name, focus = false) {
  for (const item of ["project", "architecture", "company"]) {
    const selected = item === name;
    $("tab-" + item).setAttribute("aria-selected", String(selected));
    $("tab-" + item).tabIndex = selected ? 0 : -1;
    $("panel-" + item).hidden = !selected;
  }
  if (focus) $("tab-" + name).focus();
  if (name === "company" && !runsLoaded) loadRuns();
}
function revealTaskHash(scroll = true) {
  const hash = location.hash;
  if (!hash.startsWith("#task-") || !currentPlan) return;
  const id = hash.slice(6);
  if (!currentPlan.tasks.some((task) => task.id === id)) return;
  selectTab("project");
  $("filter").value = "all";
  renderTasks(currentPlan);
  const card = document.getElementById("task-" + id);
  card.querySelector("details").open = true;
  openTasks.add(id);
  if (scroll) card.scrollIntoView({ block: "start" });
}
function detail(title, children, open = false) {
  const node = element("details");
  node.open = open;
  node.append(element("summary", "", title), ...children);
  return node;
}
function recordList(items) {
  const list = element("ul", "record-list");
  for (const item of items || []) list.append(element("li", "", text(item && typeof item === "object" && typeof item.text === "string" ? item.text : item)));
  return list;
}
function table(headers, rows) {
  const wrapper = element("div", "table-wrap");
  const node = element("table");
  const head = element("thead");
  const heading = element("tr");
  headers.forEach((title) => heading.append(element("th", "", title)));
  head.append(heading);
  const body = element("tbody");
  for (const row of rows) {
    const tr = element("tr");
    for (const value of row) {
      const td = element("td");
      td.append(value instanceof Node ? value : document.createTextNode(text(value)));
      tr.append(td);
    }
    body.append(tr);
  }
  node.append(head, body);
  wrapper.append(node);
  return wrapper;
}
function number(value) {
  if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) return null;
  return Number(value);
}
function rounded(value) {
  const numeric = number(value);
  return numeric === null ? "Unavailable" : numeric.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
function savedValue(value, unit) {
  const displayUnit = unit === "percent" ? "%" : unit === "dimensionless" ? "×" : unit;
  const missing = number(value) === null;
  const node = element("span", missing ? "unavailable" : "", missing ? "Unavailable" : rounded(value) + (displayUnit ? (["%", "×"].includes(displayUnit) ? "" : " ") + displayUnit : ""));
  node.title = "Exact saved value: " + text(value) + (unit ? " " + unit : "");
  return node;
}
function sourceRefs(input, sources, originLabel) {
  const refs = element("div");
  const evidence = Array.isArray(input.evidence) ? input.evidence : input.evidence ? [input.evidence] : [];
  const ids = new Set([input.source_id, input.report_id, input.pointer && input.pointer.report_id, ...evidence.map((e) => typeof e === "string" ? e : e.report_id || e.source_id)].filter(Boolean));
  for (const id of ids) {
    const source = sources.find((s) => s.id === id);
    if (!source) { refs.append(element("span", "source-ref", (originLabel || (String(id).startsWith("src_") ? "Frozen API source ID" : "Saved source ID")) + ": " + id)); continue; }
    const link = element("a", "source-ref", "Source: " + source.title);
    link.href = "#source-" + id;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const target = document.getElementById("source-" + id);
      for (let parent = target.parentElement; parent; parent = parent.parentElement) if (parent.tagName === "DETAILS") parent.open = true;
      target.scrollIntoView({ block: "start" });
    });
    refs.append(link);
  }
  return refs;
}
function inputEvidence(input, sources) {
  const entries = Array.isArray(input.evidence) ? input.evidence : input.evidence ? [input.evidence] : [];
  const records = [];
  for (const evidence of entries) {
    if (!evidence || typeof evidence !== "object") { records.push(element("p", "exact", text(evidence))); continue; }
    const block = element("div");
    const location = [evidence.report_id ? "Report " + evidence.report_id : null, evidence.page !== undefined ? "physical page " + text(evidence.page) : null, evidence.row ? "row " + evidence.row : null, evidence.column ? "column " + evidence.column : null].filter(Boolean).join(" · ");
    block.append(element("p", "basis", location || "Saved evidence"));
    if (evidence.quote) block.append(element("blockquote", "saved-text", text(evidence.quote)));
    if (evidence.status) block.append(element("p", "meta", "Evidence status: " + text(evidence.status)));
    if (evidence.source_pointer) block.append(element("p", "exact", "Source pointer: " + text(evidence.source_pointer)));
    block.append(sourceRefs(evidence, sources));
    const source = sources.find((item) => item.id === evidence.report_id);
    if (source && source.url && Number.isInteger(evidence.page) && evidence.page > 0) {
      try {
        const url = new URL(source.url);
        if (["https:", "http:"].includes(url.protocol) && !url.username && !url.password) {
          url.hash = "page=" + evidence.page;
          const link = element("a", "source-ref", "Open original · page " + evidence.page + " ↗");
          link.href = url.href;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          block.append(link);
        }
      } catch (error) { /* Preserve the saved evidence when its link is invalid. */ }
    }
    block.append(detail("Exact evidence metadata", [element("pre", "", text(evidence))]));
    records.push(block);
  }
  return records.length ? detail("Report evidence (" + records.length + ")", records) : null;
}
function renderCalculation(calc, sources) {
  const children = [];
  children.push(element("p", "meta", "Saved record " + calc.id + " · " + text(calc.formula) + " · version " + text(calc.version)));
  children.push(element("p", "formula", text(calc.formula_text)));
  const outputs = Object.entries(calc.outputs || {}).map(([key, output]) => [key, savedValue(output.value, output.unit), text(output.value)]);
  children.push(element("p", "detail-label", "Saved outputs"), table(["Output", "Display", "Exact value"], outputs));
  if (calc.warnings && calc.warnings.length) { const warnings = recordList(calc.warnings); warnings.classList.add("warning"); children.push(element("p", "detail-label", "Warnings"), warnings); }
  if (calc.missing_inputs && calc.missing_inputs.length) { const missing = recordList(calc.missing_inputs); missing.classList.add("unavailable"); children.push(element("p", "detail-label", "Missing inputs"), missing); }
  const inputs = [];
  for (const [name, input] of Object.entries(calc.inputs || {})) {
    const info = typeof input === "object" && input !== null ? input : { value: input };
    const context = element("div");
    context.append(element("p", "basis", [info.basis, info.period_end || info.year || (info.period ? text(info.period) : null), info.report_type, info.status].filter(Boolean).join(" · ")));
    if (info.id || info.metric) context.append(element("p", "exact", [info.id, info.metric].filter(Boolean).join(" · ")));
    if (info.pointer || info.source_pointer) context.append(element("p", "exact", "Source pointer: " + text(info.pointer || info.source_pointer)));
    context.append(sourceRefs(info, sources));
    const evidence = inputEvidence(info, sources);
    if (evidence) context.append(evidence);
    inputs.push([name, text(info.value), [info.unit, info.scale !== undefined ? "scale " + info.scale : null, info.currency].filter(Boolean).join(" · "), context]);
  }
  children.push(element("p", "detail-label", "Inputs & source trail"), table(["Input", "Exact value", "Unit / scale", "Basis / provenance"], inputs));
  if (calc.options && Object.keys(calc.options).length) children.push(detail("Saved options", [element("pre", "", text(calc.options))]));
  if (calc.preserved_assumptions) children.push(detail("Preserved assumptions", [element("pre", "", text(calc.preserved_assumptions))]));
  const node = detail(calc.label || calc.id, children);
  node.id = "calculation-" + calc.id;
  return node;
}
function matchingPrice(price, scenarios) {
  if (!price || number(price.value) === null || number(price.value) < 0 || !price.date || String(price.scale) !== "1" || !price.currency) return false;
  return scenarios.every((scenario) => scenario.unit === price.unit ||
    (price.unit === "currency/share" && [price.currency + "/share today", price.currency + "/share"].includes(scenario.unit)));
}
function scenarioChart(run) {
  const scenarios = run.scenarios || [];
  const values = scenarios.map((s) => number(s.value));
  const wrapper = element("div");
  const unit = scenarios.length ? scenarios[0].unit : null;
  if (!scenarios.length || values.some((v) => v === null || v < 0) || !unit || scenarios.some((s) => s.unit !== unit)) {
    wrapper.append(element("p", "callout", "Scenario chart unavailable: comparable nonnegative saved values and units are required. Exact records remain in the table."));
    return wrapper;
  }
  const price = run.price || {};
  const priceValue = number(price.value);
  // Normalize the typed currency/share label only; values stay at their saved scale.
  const comparablePrice = matchingPrice(price, scenarios);
  const max = Math.max(1, ...values, comparablePrice ? priceValue : 0);
  const width = 500;
  const height = 70 + scenarios.length * 66;
  const left = 110;
  const plotWidth = 290;
  const svg = svgElement("svg", { viewBox: "0 0 " + width + " " + height, class: "chart", role: "img", "aria-label": "Saved scenario present values in " + unit + (comparablePrice ? ", with dated saved price reference" : "") });
  svg.append(svgElement("text", { x: left, y: 25, class: "axis-text" }, "PRESENT VALUE TODAY · " + unit));
  scenarios.forEach((scenario, index) => {
    const y = 46 + index * 66;
    svg.append(svgElement("text", { x: 15, y: y + 18 }, scenario.name), svgElement("rect", { x: left, y, width: values[index] / max * plotWidth, height: 27, class: "scenario-bar" }), svgElement("text", { x: left + values[index] / max * plotWidth + 8, y: y + 18 }, rounded(scenario.value)));
  });
  if (comparablePrice) {
    const x = left + priceValue / max * plotWidth;
    svg.append(svgElement("line", { x1: x, x2: x, y1: 37, y2: height - 28, class: "price-line" }));
  }
  wrapper.append(svg);
  wrapper.append(element("p", "chart-caption", comparablePrice ? "Dashed reference: saved price " + rounded(price.value) + " " + (price.unit === "currency/share" ? price.currency + "/share" : price.unit) + " · " + text(price.date || price.period_end) + ". This is a frozen observation, not a live quote." : "Saved present values only. No compatible dated price reference is available."));
  return wrapper;
}
function probabilityDescription(probability) {
  const basis = probability.basis ? " " + probability.basis : "";
  if (probability.status === "proposed") return "Proposed analyst weights, not adopted or calibrated probabilities." + basis;
  if (probability.status === "missing") return "No saved probabilities are available." + basis;
  return "Saved probabilities." + basis;
}
function calculationPeriod(calc) {
  return Object.values(calc.inputs || {}).map((input) => {
    if (!input || typeof input !== "object") return "";
    if (typeof input.period_end === "string" && /^\d{4}-\d{2}-\d{2}$/.test(input.period_end)) return input.period_end;
    if (/^\d{4}$/.test(String(input.year))) return String(input.year);
    return "";
  }).sort().pop() || "";
}
function renderCompany(run) {
  const view = $("company-view");
  const opened = new Set(Array.from(view.querySelectorAll("details[open] > summary")).map((summary) => summary.textContent));
  view.replaceChildren();
  const sources = run.sources || [];
  const header = element("div", "company-header");
  header.append(element("p", "eyebrow", "SAVED ANALYSIS · READ ONLY"), element("h2", "", text(run.company.name) + (run.company.ticker ? " · " + run.company.ticker : "")), element("p", "meta", "Analysis date: " + text(run.analysis_date) + " · Saved review: " + text(run.reviewed_at)), element("p", "meta", "Method: " + text(run.method)));
  header.append(element("p", "conclusion", text(run.conclusion)));
  view.append(header);
  const scenarioSection = element("section", "company-section");
  scenarioSection.append(element("h3", "", "Valuation scenarios"), element("p", "basis", "Saved present values at the analysis date. Future targets and horizon assumptions remain in each saved basis; the workbench performs no valuation calculations."));
  const scenarioGrid = element("div", "scenario-grid");
  scenarioGrid.append(scenarioChart(run));
  scenarioGrid.append(table(["Scenario", "Present value", "Weight", "Saved basis"], (run.scenarios || []).map((s) => {
    const basis = element("div");
    basis.append(element("p", "basis", s.basis), detail("Exact value & calculation IDs", [element("p", "exact", text(s.value) + " " + s.unit + (s.weight !== undefined ? " · exact weight " + text(s.weight) : "")), element("p", "exact", (s.calculation_ids || []).join(", "))]));
    return [s.name, savedValue(s.value, s.unit), s.weight === undefined || s.weight === null ? "Unavailable" : rounded(Number(s.weight) * 100) + "%", basis];
  })));
  scenarioSection.append(scenarioGrid);
  const price = run.price || {};
  const priceNote = element("p", "basis");
  priceNote.append(document.createTextNode("Frozen price observation: "), savedValue(price.value, price.unit === "currency/share" ? price.currency + "/share" : price.unit), document.createTextNode(" · date " + text(price.date || price.period_end) + " · " + text(price.basis)), sourceRefs(price, sources, "Frozen API observation"));
  scenarioSection.append(priceNote);
  const probability = run.probability || {};
  scenarioSection.append(element("p", "callout", probabilityDescription(probability)));
  if (probability.weights) scenarioSection.append(detail("Exact saved weights", [element("pre", "", text(probability.weights))]));
  view.append(scenarioSection);
  const calculations = run.calculations || [];
  const metrics = element("div", "metrics");
  const metricDefinitions = [
    ["ebit_margin", "EBIT margin", "margin_percent"],
    ["incremental_ebit_margin", "Incremental EBIT margin", "incremental_margin_percent"],
    ["operating_roic", "Operating ROIC", "roic_percent"],
    ["group_cash_conversion", "Group cash conversion", "conversion_percent"],
    ["ev_ebit", "EV / EBIT", "multiple"],
    ["pe", "Diluted P/E", "multiple"],
  ];
  for (const [formula, label, primary] of metricDefinitions) {
    const candidates = calculations.filter((calc) => calc.formula === formula);
    if (!candidates.length) continue;
    // Only explicit saved period metadata orders results; no dates are inferred from prose.
    candidates.sort((a, b) => calculationPeriod(b).localeCompare(calculationPeriod(a)));
    const calc = candidates[0];
    const output = (calc.outputs || {})[calc.primary_output || primary] || {};
    const metric = element("div", "metric");
    metric.append(element("span", "meta", label));
    const value = savedValue(output.value, ["ev_ebit", "pe"].includes(formula) && output.unit === "fraction" ? "×" : output.unit);
    value.classList.add("metric-value");
    metric.append(value, element("span", "meta", (calculationPeriod(calc) || "Period not recorded") + " · " + (calc.label || calc.id)));
    if (number(output.value) === null) metric.append(element("p", "basis unavailable", "See missing inputs in calculation details."));
    metrics.append(metric);
  }
  if (metrics.children.length) view.append(metrics);
  const working = element("section", "company-section");
  working.append(detail("Calculations & inputs (" + calculations.length + ")", calculations.length ? calculations.map((calc) => renderCalculation(calc, sources)) : [element("p", "unavailable", "No named calculations saved.")]));
  working.append(detail("Analysis & interpretation", (run.interpretation || []).length ? [recordList(run.interpretation)] : [element("p", "unavailable", "No separate interpretation saved.")]));
  working.append(detail("Saved research narrative", [element("p", "saved-text", text(run.narrative))]));
  working.append(detail("Notes & limitations", (run.notes || []).length ? [recordList(run.notes)] : [element("p", "unavailable", "No separate notes saved.")]));
  const benchmark = run.benchmark || {};
  const benchmarkContent = [table(["Saved statistic", "Percent / percentage points"], [["Candidate annualized return (%)", savedValue(benchmark.candidate_annualized_return_percent)], ["Benchmark annualized return (%)", savedValue(benchmark.benchmark_annualized_return_percent)], ["Difference (percentage points)", savedValue(benchmark.difference_percentage_points)]]), element("p", "basis", text(benchmark.interpretation)), element("p", "basis", text(benchmark.limits)), element("p", "basis", text(benchmark.context))];
  working.append(detail("Return & benchmark", benchmarkContent));
  const sourceContent = [];
  for (const source of sources) {
    const item = element("article", "source-item");
    item.id = "source-" + source.id;
    const title = element("h4", "", source.title || source.id);
    item.append(title, element("p", "meta", "Report ID: " + source.id + " · period " + (source.period ? [source.period.start, source.period.end].filter(Boolean).join(" to ") || "Unavailable" : "Unavailable") + " · published " + text(source.published_at)));
    if (source.url) {
      try {
        const url = new URL(source.url);
        if (["https:", "http:"].includes(url.protocol) && !url.username && !url.password) {
          const link = element("a", "", "Original source ↗");
          link.href = url.href;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          item.append(link);
        }
      } catch (error) { /* Invalid saved URLs remain plain evidence records. */ }
    }
    item.append(detail("Pages & integrity · " + source.id, [element("p", "meta", "Pages: " + text(source.pages)), element("p", "meta", "Original SHA-256: " + text(source.sha256)), element("p", "meta", "Prepared SHA-256: " + text(source.prepared_sha256))]));
    sourceContent.push(item);
  }
  working.append(detail("Sources & report pages (" + sources.length + ")", sourceContent.length ? sourceContent : [element("p", "unavailable", "No sources included in this saved view.")]));
  working.append(detail("Run provenance", [element("pre", "", text(run.provenance))]));
  if (run.original_calculations) working.append(detail("Original scalar calculation trace", [element("p", "basis", "Original saved operations, preserved as recorded. These are separate from the named calculation records above."), element("pre", "trace", text(run.original_calculations))]));
  view.append(working);
  if (loadedRunId === run.id) for (const details of view.querySelectorAll("details")) if (opened.has(details.firstElementChild.textContent)) details.open = true;
  loadedRunId = run.id;
  view.hidden = false;
}
async function loadRun(id) {
  const request = ++runRequest;
  $("company-error").hidden = true;
  if (!id) { $("company-view").hidden = true; return; }
  $("company-status").textContent = "Loading saved analysis…";
  // Hide the previous company while loading so a failed selection cannot mislabel it.
  $("company-view").hidden = true;
  try {
    const run = await getJSON("/api/runs/" + encodeURIComponent(id));
    if (request !== runRequest) return;
    renderCompany(run);
    $("company-status").classList.remove("stale");
    $("company-status").textContent = "Saved record loaded · " + text(run.analysis_date) + " · no live quote or analysis refresh";
  } catch (error) {
    if (request !== runRequest) return;
    $("company-error").hidden = false;
    $("company-error").textContent = "Could not load this saved analysis. Check the configured saved-view file and refresh.";
    $("company-status").classList.add("stale");
    $("company-status").textContent = "Saved analysis unavailable";
  }
}
async function loadRuns(force = false) {
  if (runsLoading || (runsLoaded && !force)) return;
  runsLoading = true;
  $("company-error").hidden = true;
  try {
    const data = await getJSON("/api/runs");
    const selected = $("run-select").value;
    $("run-select").replaceChildren();
    for (const run of data.runs) {
      const option = element("option", "", run.company.name + (run.company.ticker ? " · " + run.company.ticker : "") + " · " + text(run.analysis_date));
      option.value = run.id;
      $("run-select").append(option);
    }
    runsLoaded = true;
    $("company-status").classList.remove("stale");
    $("company-empty").hidden = data.runs.length > 0;
    $("run-select").disabled = !data.runs.length;
    if (!data.runs.length) {
      $("run-select").append(element("option", "", "No saved analyses"));
      $("company-view").hidden = true;
      $("company-status").textContent = "No local saved analysis has been explicitly configured.";
    } else {
      if (data.runs.some((run) => run.id === selected)) $("run-select").value = selected;
      await loadRun($("run-select").value);
    }
  } catch (error) {
    $("company-error").hidden = false;
    $("company-error").textContent = "Could not read the saved-analysis index. Check the local server and refresh.";
    $("company-status").classList.add("stale");
    $("company-status").textContent = "Saved-analysis index unavailable";
  } finally { runsLoading = false; }
}
for (const name of ["project", "architecture", "company"]) {
  $("tab-" + name).addEventListener("click", () => selectTab(name));
  $("tab-" + name).addEventListener("keydown", (event) => {
    const names = ["project", "architecture", "company"];
    let index = names.indexOf(name);
    if (event.key === "ArrowRight") index = (index + 1) % names.length;
    else if (event.key === "ArrowLeft") index = (index + names.length - 1) % names.length;
    else if (event.key === "Home") index = 0;
    else if (event.key === "End") index = names.length - 1;
    else return;
    event.preventDefault();
    selectTab(names[index], true);
  });
}
$("architecture-link").addEventListener("click", () => { selectTab("architecture", true); $("tab-architecture").scrollIntoView({ block: "start" }); });
$("filter").addEventListener("change", () => { if (currentPlan) renderTasks(currentPlan); });
$("next-link").addEventListener("click", (event) => {
  if (!currentPlan || currentPlan.next_task === null) { event.preventDefault(); return; }
  $("filter").value = "all";
  renderTasks(currentPlan);
  document.getElementById("task-" + currentPlan.next_task).querySelector("details").open = true;
  openTasks.add(currentPlan.next_task);
});
window.addEventListener("hashchange", () => revealTaskHash());
$("run-select").addEventListener("change", () => loadRun($("run-select").value));
$("refresh").addEventListener("click", () => { refresh(); if (runsLoaded || !$("panel-company").hidden) loadRuns(true); });
refresh();
setInterval(refresh, 10000);
