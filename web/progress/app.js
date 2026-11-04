"use strict";

const $ = (id) => document.getElementById(id);
const labels = { pending: "Pending", in_progress: "In progress", blocked: "Blocked", done: "Done" };
const publicDocs = new Set([
  "AGENTS.md", "CONTRIBUTING.md", "README.md", "docs/architecture.md", "work/README.md",
  "docs/analysis-policy.md", "docs/calculations.md", "docs/company-workflow.md", "docs/research/system-readiness-review.md",
  "docs/research/borsdata-retrieval-storage.md", "docs/codex-integration.md", "docs/saved-analysis-view.md", "docs/material-inputs.md", "docs/analysis-workflow.md",
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
const savedReferenceIds = new Set();

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
    const location = [evidence.report_id ? "Report " + evidence.report_id : null, evidence.section ? "Saved analysis · " + evidence.section : null, evidence.page !== undefined ? "physical page " + text(evidence.page) : null, evidence.row ? "row " + evidence.row : null, evidence.column ? "column " + evidence.column : null].filter(Boolean).join(" · ");
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
  return records.length ? detail((entries.every((item) => item && item.report_id) ? "Report evidence (" : "Source evidence (") + records.length + ")", records) : null;
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
    if (info.id && !savedReferenceIds.has("input-" + info.id)) { context.id = "input-" + info.id; savedReferenceIds.add(context.id); }
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
  const displayUnit = unit.replace(/ today$/, "");
  const svg = svgElement("svg", { viewBox: "0 0 " + width + " " + height, class: "chart", role: "img", "aria-label": "Scenario present values as of " + text(run.analysis_date) + " in " + displayUnit + (comparablePrice ? ", with report price reference dated " + price.date : "") });
  svg.append(svgElement("text", { x: left, y: 25, class: "axis-text" }, "Present value · " + text(run.analysis_date) + " · " + displayUnit));
  scenarios.forEach((scenario, index) => {
    const y = 46 + index * 66;
    svg.append(svgElement("text", { x: 15, y: y + 18 }, scenario.name), svgElement("rect", { x: left, y, width: values[index] / max * plotWidth, height: 27, class: "scenario-bar" }), svgElement("text", { x: left + values[index] / max * plotWidth + 8, y: y + 18 }, rounded(scenario.value)));
  });
  if (comparablePrice) {
    const x = left + priceValue / max * plotWidth;
    svg.append(svgElement("line", { x1: x, x2: x, y1: 37, y2: height - 28, class: "price-line" }));
  }
  wrapper.append(svg);
  wrapper.append(element("p", "chart-caption", comparablePrice ? "Dashed reference: report price " + rounded(price.value) + " " + (price.unit === "currency/share" ? price.currency + "/share" : price.unit) + " · " + text(price.date) + "." : "Saved present values only. No compatible dated price reference is available."));
  return wrapper;
}
function probabilityDescription(probability) {
  const basis = probability.basis ? " " + probability.basis : "";
  if (probability.status === "proposed") return "Proposed analyst weights, not adopted or calibrated probabilities." + basis;
  if (probability.status === "missing") return "No saved probabilities are available." + basis;
  return "Saved probabilities." + basis;
}
function calculationPeriod(calc) {
  if (calc.period_end) return calc.period_end;
  return Object.values(calc.inputs || {}).map((input) => {
    if (!input || typeof input !== "object") return "";
    if (typeof input.period_end === "string" && /^\d{4}-\d{2}-\d{2}$/.test(input.period_end)) return input.period_end;
    if (/^\d{4}$/.test(String(input.year))) return String(input.year);
    return "";
  }).sort().pop() || "";
}
function economicPeriod(record) {
  if (!record) return "Unavailable";
  if (record.kind === "assumption") return "Scenario assumption";
  if (record.kind === "stock") return record.period_end ? "Closing " + record.period_end : "Closing date not recorded";
  const dates = [record.period_start, record.period_end].filter(Boolean).join(" to ");
  return [record.report_type ? record.report_type.toUpperCase() : null, dates || record.year].filter(Boolean).join(" · ") || "Period not recorded";
}
function materialValue(record) {
  const currency = record.unit === "currency" ? record.currency : record.unit === "SEK" ? "SEK" : null;
  const raw = number(record.value);
  let value = raw;
  let unit = record.unit;
  if (currency && raw !== null) {
    // Scale conversion is presentation only; the saved record remains unchanged.
    value = raw * Number(record.scale) / 1000000;
    unit = "M" + currency;
  } else if (record.unit === "currency/share") unit = (record.currency || "currency") + "/share";
  else if (record.unit === "shares" && String(record.scale) === "1000000") unit = "million shares";
  else if (record.unit === "multiple" || (record.kind === "calculation" && String(record.id).endsWith("#multiple"))) unit = "×";
  else if (record.unit === "percent") unit = "%";
  else if (String(record.scale) !== "1") unit += " · scale " + record.scale;
  const node = element("span", value === null ? "unavailable" : "", value === null ? "Unavailable" : rounded(value) + (["%", "×"].includes(unit) ? "" : " ") + unit);
  node.title = "Exact saved value: " + text(record.value) + " · unit " + record.unit + " · scale " + record.scale + (record.currency ? " · currency " + record.currency : "");
  return node;
}
function currentCalculation(calc) {
  const field = { ebit_margin: "revenue", incremental_ebit_margin: "revenue_current", operating_roic: "ebit", group_cash_conversion: "cfo", ev_ebit: "ebit", pe: "diluted_eps" }[calc.formula];
  const input = (calc.inputs || {})[field];
  return calc.display_role === "current" && ["r12", "quarter"].includes(calc.report_type) && calc.period_start && calc.period_end && input &&
    input.report_type === calc.report_type && input.period_start === calc.period_start && input.period_end === calc.period_end;
}
function sourceRecord(record, sources) {
  const block = element("div");
  if (record.id && !savedReferenceIds.has("record-" + record.id)) { block.id = "record-" + record.id; savedReferenceIds.add(block.id); }
  block.append(element("p", "basis", [record.kind, record.basis, record.status].filter(Boolean).join(" · ")), sourceRefs(record, sources));
  const evidence = inputEvidence(record.evidence ? record : record.report_id && record.quote ? { evidence: record } : record, sources);
  if (evidence) block.append(evidence);
  block.append(detail("Exact saved source record", [element("pre", "", text(record))]));
  return block;
}
function renderMaterialInputs(rows, sources) {
  const section = element("section", "company-section material-inputs");
  section.append(element("h3", "", "Material values: meaning & selection"), element("p", "basis", "Definitions and selection reasons are saved analyst decisions. A numeric match alone does not verify a provider definition. Forecasts and assumptions retain their saved kind."));
  section.append(documentReference("docs/material-inputs.md", "Period and definition-status rules ↗"));
  const records = rows.map((row) => {
    const selected = row.selected;
    const label = element("div");
    label.append(element("p", "", row.label), element("p", "meta", "Selected definition: " + row.definition_status + " · Source check: " + row.reconciliation_status));
    const selectedValue = element("div");
    if (selected) {
      selectedValue.append(materialValue(selected), element("p", "meta", "Kind: " + selected.kind));
    } else selectedValue.append(element("span", "unavailable", "Unavailable · no selected value"));
    const reason = element("div");
    reason.append(element("p", "basis", row.selection_reason));
    if (row.valuation_uses.length) reason.append(recordList(row.valuation_uses));
    const trail = [];
    if (selected) trail.push(element("p", "detail-label", "Selected record"), sourceRecord(selected, sources));
    for (const candidate of row.candidates) {
      const record = candidate.record;
      const content = [element("p", "basis", candidate.comparison_basis), element("p", "meta", "Candidate definition: " + candidate.definition_status + " · Numeric comparison: " + candidate.reconciliation_status), sourceRecord(record, sources)];
      if (candidate.residual) content.push(element("p", "exact", "Saved residual: " + text(candidate.residual.value) + " " + candidate.residual.unit + " · " + candidate.residual.formula));
      trail.push(detail("Candidate · " + (record.metric || record.id) + " · " + materialValue(record).textContent + " · " + economicPeriod(record), content));
    }
    if (row.limitations.length) trail.push(element("p", "detail-label", "Limitations"), recordList(row.limitations));
    const evidence = inputEvidence(row, sources);
    if (evidence) trail.push(evidence);
    reason.append(detail("Sources, comparisons & limitations", trail));
    return [label, selectedValue, economicPeriod(selected), row.definition, reason];
  });
  section.append(detail("Inspect material decisions (" + rows.length + ")", [table(["Material value", "Selected value / unit", "Economic period", "What it means", "Why use it"], records)]));
  return section;
}
function openSavedTarget(id, event) {
  const target = document.getElementById(id);
  if (!target) return;
  if (event) event.preventDefault();
  for (let parent = target.parentElement; parent; parent = parent.parentElement) if (parent.tagName === "DETAILS") parent.open = true;
  target.scrollIntoView({ block: "start" });
  target.tabIndex = -1;
  target.focus({ preventScroll: true });
}
function savedLink(id, label, className = "source-ref") {
  const link = element("a", className, label);
  link.href = "#" + id;
  link.addEventListener("click", (event) => openSavedTarget(id, event));
  return link;
}
function referenceList(references, run) {
  const node = element("div", "analysis-references");
  for (const reference of references || []) {
    const ref = String(reference);
    const base = ref.split("#")[0];
    const page = ref.match(/^(.*):p([1-9][0-9]*)$/);
    const source = (run.sources || []).find((item) => item.id === (page ? page[1] : ref));
    const calculation = [...(run.calculations || []), ...(run.original_calculations || [])].find((item) => item.id === base);
    if (source) {
      node.append(savedLink("source-" + source.id, source.title + (page ? " · physical page " + page[2] : "")));
      if (page && source.url) {
        try {
          const url = new URL(source.url);
          if (["https:", "http:"].includes(url.protocol) && !url.username && !url.password) {
            url.hash = "page=" + page[2];
            const link = element("a", "source-ref", "Open page " + page[2] + " ↗");
            link.href = url.href;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            node.append(link);
          }
        } catch (error) { /* Saved reference remains readable. */ }
      }
    } else if (calculation) node.append(savedLink("calculation-" + base, ref));
    else if ((run.calculations || []).some((calc) => Object.values(calc.inputs || {}).some((input) => input && input.id === ref))) node.append(savedLink("input-" + ref, ref));
    else if ((run.saved_records || []).some((record) => record.id === ref)) node.append(savedLink("record-" + ref, ref));
    else if ((run.material_inputs || []).some((row) => [row.selected, ...(row.candidates || []).map((item) => item.record)].some((record) => record && record.id === ref))) node.append(savedLink("record-" + ref, ref));
    else node.append(element("span", "source-ref unlinked", ref + " · reference retained; detail unavailable in this export"));
  }
  return node;
}
function datedEndpoint(date) {
  if (!date || !date.value) return "Date not recorded";
  return date.value + (date.precision === "year" ? " · year precision" : date.precision === "month" ? " · month precision" : "");
}
function scenarioEndpoints(run) {
  return run.analysis ? run.analysis.scenarios : (run.scenarios || []).filter((item) => item.present_value && item.future_target);
}
function endpointChart(run) {
  const scenarios = scenarioEndpoints(run);
  const wrapper = element("div", "endpoint-charts");
  const endpoints = scenarios.flatMap((scenario) => [scenario.present_value, scenario.future_target]);
  const units = new Set(endpoints.map((item) => item && item.unit));
  const comparable = units.size === 1 && !units.has(undefined) && endpoints.every((item) => number(item && item.value) !== null && number(item.value) >= 0);
  const maximum = comparable ? Math.max(1, ...endpoints.map((item) => number(item.value))) : 1;
  const weightLabel = (scenario) => {
    const weight = (run.probability || {}).weights && run.probability.weights[scenario.id];
    return number(weight) === null ? "weight unavailable" : rounded(Number(weight) * 100) + "%";
  };
  for (const [key, heading, dateKey] of [["present_value", "Present value", "present_value_date"], ["future_target", "Future target", "target_date"]]) {
    const panel = element("div", "endpoint-panel");
    panel.append(element("h4", "", heading));
    const values = scenarios.map((item) => number(item[key] && item[key].value));
    if (!comparable) {
      panel.append(element("p", "callout", "Comparable nonnegative saved endpoints are unavailable. Read the exact scenario records below."));
    } else {
      const svg = svgElement("svg", { viewBox: "0 0 500 " + (scenarios.length * 90 + 12), class: "chart endpoint-chart", role: "img", "aria-label": heading + ": " + scenarios.map((item) => item.name + ", saved weight " + weightLabel(item) + ", " + text(item[key].value) + " " + item[key].unit + ", " + datedEndpoint(item[dateKey])).join("; ") });
      scenarios.forEach((scenario, index) => {
        const y = 24 + index * 90;
        const label = { bear: "Bear", base: "Base", bull: "Bull" }[scenario.id] || "Scenario";
        svg.append(svgElement("text", { x: 16, y }, label + " · " + weightLabel(scenario)), svgElement("text", { x: 484, y, "text-anchor": "end" }, rounded(scenario[key].value) + " " + scenario[key].unit));
        svg.append(svgElement("rect", { x: 16, y: y + 12, width: values[index] / maximum * 468, height: 13, class: "scenario-bar " + scenario.id }));
        svg.append(svgElement("text", { x: 16, y: y + 49, class: "axis-text" }, datedEndpoint(scenario[dateKey])));
      });
      panel.append(svg);
    }
    wrapper.append(panel);
  }
  return wrapper;
}
function readableReport(markdown) {
  const node = element("div", "report-body");
  const lines = String(markdown || "").split(/\r?\n/);
  let paragraph = [];
  const flush = () => { if (paragraph.length) { node.append(element("p", "saved-text", paragraph.join("\n"))); paragraph = []; } };
  const cells = (line) => line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*$/);
    if (heading) { flush(); node.append(element("h" + Math.min(6, heading[1].length + 3), "", heading[2])); }
    else if (line.includes("|") && index + 1 < lines.length && /^\s*\|?\s*:?-{3,}/.test(lines[index + 1])) {
      flush();
      const headers = cells(line);
      const rows = [];
      index += 2;
      while (index < lines.length && lines[index].includes("|") && lines[index].trim()) { rows.push(cells(lines[index])); index++; }
      index--;
      node.append(table(headers, rows));
    } else if (!line.trim()) flush();
    else paragraph.push(line);
  }
  flush();
  if (!node.children.length) node.append(element("p", "unavailable", "No saved narrative is available."));
  return node;
}
function analysisNavigation(run) {
  const nav = element("nav", "analysis-nav");
  nav.setAttribute("aria-label", "Company analysis sections");
  const sections = run.analysis ? run.analysis.sections.map((section) => ["analysis-" + section.id, section.id.charAt(0).toUpperCase() + section.id.slice(1)]) : [["legacy-report", "Full saved report"]];
  for (const [id, label] of [["company-scenarios", "Scenarios"], ...sections, ["company-metrics", "Metrics & management"], ...(run.analysis ? [["company-review", "Independent challenge"]] : []), ["company-working", "Sources & calculations"]]) nav.append(savedLink(id, label, ""));
  return nav;
}
function renderAnalysis(run) {
  const section = element("section", "company-section analysis-body");
  if (!run.analysis) {
    section.id = "legacy-report";
    section.append(element("p", "eyebrow", "ORIGINAL SAVED ANALYSIS"), element("h3", "", "Read the full report"), element("p", "basis", "This legacy record has no structured analysis or independent structured review. Its original narrative is shown as saved; headings and tables are presented for reading."), readableReport(run.narrative));
    return section;
  }
  section.append(element("p", "eyebrow", "THE INVESTMENT CASE"), element("h3", "", "Analysis & reasoning"));
  for (const saved of run.analysis.sections) {
    const block = element("article", "analysis-section");
    block.id = "analysis-" + saved.id;
    block.append(element("h4", "", saved.title));
    for (const paragraph of saved.paragraphs) {
      const entry = element("div", "analysis-paragraph");
      const references = referenceList(paragraph.references, run);
      entry.append(element("span", "paragraph-kind", paragraph.kind), readableReport(paragraph.text), paragraph.references.length > 3 ? detail("Sources & calculations (" + paragraph.references.length + ")", [references]) : references);
      block.append(entry);
    }
    section.append(block);
  }
  return section;
}
function managementComparison(item, run) {
  const block = element("article", "management-comparison");
  block.id = "management-" + item.id;
  const relationship = { direct: "Direct management " + item.statement_type, related: "Related management statement · " + item.statement_type, not_stated: "No direct guidance stated" }[item.relationship];
  block.append(element("p", "detail-label", relationship), element("h5", "", item.metric_label), element("p", "saved-text", item.statement));
  if (item.statement_date || item.target_period) block.append(element("p", "meta", "Statement date: " + text(item.statement_date) + " · Horizon: " + text(item.target_period)));
  block.append(element("p", "basis", "Issuer basis: " + item.basis));
  if (item.actual) block.append(element("p", "basis", "Saved comparison: " + item.actual));
  const evidenceContent = [referenceList([...(item.references || []), ...(item.actual_references || [])], run)];
  if (item.evidence) {
    const evidence = item.evidence;
    evidenceContent.push(element("p", "meta", "Report " + evidence.report_id + " · physical page " + evidence.page), element("blockquote", "saved-text", evidence.quote), referenceList([evidence.report_id + ":p" + evidence.page], run));
  }
  block.append(detail(item.evidence ? "Sources & management quotation" : "Sources checked", evidenceContent));
  return block;
}
function scenarioRationale(run) {
  const section = element("section", "company-section scenario-reasoning");
  section.append(element("h3", "", "What each scenario assumes"));
  for (const scenario of scenarioEndpoints(run)) {
    const item = element("article", "scenario-case");
    item.id = "scenario-" + scenario.id;
    item.append(element("h4", "", scenario.name), element("p", "saved-text", scenario.rationale));
    const valuation = element("p", "basis");
    valuation.append(document.createTextNode("Present value · " + datedEndpoint(scenario.present_value_date) + ": "), savedValue(scenario.present_value.value, scenario.present_value.unit), document.createTextNode(". Future target · " + datedEndpoint(scenario.target_date) + ": "), savedValue(scenario.future_target.value, scenario.future_target.unit));
    item.append(valuation);
    const weight = (run.probability || {}).weights && run.probability.weights[scenario.id];
    item.append(element("p", "basis", "Saved weight: " + (number(weight) === null ? "Unavailable" : rounded(Number(weight) * 100) + "%") + ". " + (scenario.probability_rationale || "No separate weight rationale saved.")));
    const assumptions = [element("p", "saved-text", text(scenario.assumption_rationale)), referenceList([scenario.valuation_calculation_id, scenario.weight_ref, ...(scenario.references || [])].filter(Boolean), run)];
    item.append(detail("Assumptions, sources & calculation", assumptions));
    section.append(item);
  }
  return section;
}
function renderAnalysisReview(run) {
  const section = element("section", "company-section analysis-review");
  section.id = "company-review";
  section.append(element("h3", "", "Independent challenge"));
  const review = run.analysis_review;
  if (!review) { section.append(element("p", "callout", "No independent structured review is saved for this analysis.")); return section; }
  section.append(element("p", "meta", "Reviewer: " + text(review.reviewer) + " · Verdict: " + text(review.verdict)), element("p", "saved-text", review.summary));
  for (const finding of review.findings || []) section.append(detail(finding.id + " · " + finding.verdict, [element("p", "saved-text", finding.reasoning), element("p", "basis", "Missing evidence: " + text(finding.missing_evidence)), referenceList(finding.references, run)]));
  if ((review.disagreements || []).length) section.append(detail("Disagreements retained", [recordList(review.disagreements)]));
  return section;
}
function returnUsesReportPrice(run) {
  const price = run.price;
  const returns = (run.original_calculations || []).filter((calc) => calc.operation === "financial_formula" && calc.formula === "expected_cashflow_irr");
  if (!price || !price.id || !price.source_id || returns.length !== 1) return false;
  const calculation = returns[0];
  const inputs = (calculation.inputs || []).filter((input) => input.field === "price");
  if (inputs.length !== 1 || (calculation.input_ids || {}).price !== price.id || inputs[0].id !== price.id) return false;
  return ["value", "unit", "scale", "currency", "source_id"].every((key) => inputs[0][key] === price[key]) &&
    (inputs[0].date || inputs[0].period_end) === price.date &&
    (((calculation.outputs || {}).irr_percent || {}).value === (run.benchmark || {}).candidate_annualized_return_percent);
}
function renderCompany(run) {
  savedReferenceIds.clear();
  const view = $("company-view");
  const opened = new Set(Array.from(view.querySelectorAll("details[open] > summary")).map((summary) => summary.textContent));
  view.replaceChildren();
  const sources = run.sources || [];
  const header = element("div", "company-header");
  header.append(element("h2", "", text(run.company.name) + (run.company.ticker ? " · " + run.company.ticker : "")), element("p", "meta", "Analysis date: " + text(run.analysis_date) + (run.analysis ? " · Analysis completed: " : " · Financial review: ") + text(run.reviewed_at).slice(0, 10) + " · Method: " + text(run.method)));
  const estimatedReturn = (run.benchmark || {}).candidate_annualized_return_percent;
  if (number(estimatedReturn) !== null) {
    const overview = element("p", "return-overview");
    overview.append(document.createTextNode("Estimated annual return" + (returnUsesReportPrice(run) ? " · at report price" : "") + ": "), savedValue(estimatedReturn, "percent"), document.createTextNode(" · conditional on the report's scenarios. "), savedLink("company-return", "Assumptions & limitations", ""));
    header.append(overview);
  }
  const price = run.price || {};
  const reportPrice = element("p", "basis market-price");
  reportPrice.append(document.createTextNode("Report price: "), savedValue(price.value, price.unit === "currency/share" ? price.currency + "/share" : price.unit), document.createTextNode(" · " + text(price.date || price.period_end)));
  const marketPrice = element("p", "basis market-price", "Latest market price: " + (Number.isInteger(run.company.instrument_id) && run.company.instrument_id > 0 ? "loading…" : "unavailable"));
  marketPrice.id = "latest-market-price";
  marketPrice.setAttribute("role", "status");
  const marketEvidence = element("div");
  marketEvidence.id = "latest-market-price-evidence";
  header.append(marketPrice, reportPrice, detail("Price evidence", [element("p", "detail-label", "Report price"), element("p", "basis", text(price.basis)), sourceRefs(price, sources), element("pre", "", text(price)), marketEvidence]));
  header.append(detail("Report conclusion", [element("p", "saved-text", text(run.analysis ? run.analysis.summary : run.conclusion))]));
  if (run.analysis) header.append(savedLink("company-review", "Independent challenge: " + ({ accept: "accepted", revise: "changes requested" }[(run.analysis_review || {}).verdict] || "pending"), "challenge-status"));
  view.append(header, analysisNavigation(run));
  const scenarioSection = element("section", "company-section");
  scenarioSection.id = "company-scenarios";
  const endpoints = scenarioEndpoints(run);
  scenarioSection.append(element("h3", "", "Valuation scenarios"), element("p", "basis", endpoints.length ? "Conditional scenario values at two dates; both panels share a scale. Dividend assumptions are shown below." : "Present values as of " + text(run.analysis_date) + ". Future targets and assumptions remain in the report."));
  const scenarioGrid = element("div", "scenario-grid");
  scenarioGrid.append(endpoints.length ? endpointChart(run) : scenarioChart(run));
  const scenarioTable = table(["Scenario", "Present value", "Weight", "Saved basis"], (run.scenarios || []).map((s) => {
    const basis = element("div");
    basis.append(element("p", "basis", s.basis), referenceList(s.calculation_ids, run), detail("Exact value & calculation IDs", [element("p", "exact", text(s.value) + " " + s.unit + (s.weight !== undefined ? " · exact weight " + text(s.weight) : "")), element("p", "exact", (s.calculation_ids || []).join(", "))]));
    return [s.name, savedValue(s.value, String(s.unit || "").replace(/ today$/, "")), s.weight === undefined || s.weight === null ? "Unavailable" : rounded(Number(s.weight) * 100) + "%", basis];
  }));
  scenarioGrid.append(endpoints.length ? detail("Saved scenario values & exact records", [scenarioTable]) : scenarioTable);
  if (endpoints.length) {
    scenarioGrid.classList.add("with-endpoints");
    const links = element("div", "scenario-links");
    for (const item of endpoints) links.append(savedLink("scenario-" + item.id, item.name + " · rationale & assumptions", ""));
    scenarioSection.append(links);
  }
  scenarioSection.append(scenarioGrid);
  const probability = run.probability || {};
  scenarioSection.append(element("p", "callout", probabilityDescription(probability)));
  if (probability.weights) scenarioSection.append(detail("Exact saved weights", [element("pre", "", text(probability.weights))]));
  if (run.analysis && run.analysis.probability_limits && run.analysis.probability_limits !== probability.basis) scenarioSection.append(element("p", "basis", run.analysis.probability_limits));
  view.append(scenarioSection, renderAnalysis(run));
  if (endpoints.length) view.append(scenarioRationale(run));
  const calculations = run.calculations || [];
  const metricSection = element("section", "company-section");
  metricSection.id = "company-metrics";
  metricSection.append(element("h3", "", "Metrics & management statements"));
  const metrics = element("div", "metrics");
  const comparisons = run.analysis ? run.analysis.management_comparisons || [] : [];
  const displayedComparisons = new Set();
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
    const priority = (calc) => currentCalculation(calc) ? (calc.report_type === "r12" ? 2 : 1) : 0;
    candidates.sort((a, b) => priority(b) - priority(a) || calculationPeriod(b).localeCompare(calculationPeriod(a)));
    const calc = candidates[0];
    const output = (calc.outputs || {})[calc.primary_output || primary] || {};
    const metric = element("div", "metric");
    metric.id = "metric-" + formula;
    metric.append(element("span", "meta", label));
    const value = savedValue(output.value, ["ev_ebit", "pe"].includes(formula) && output.unit === "fraction" ? "×" : output.unit);
    value.classList.add("metric-value");
    const periodLabel = calc.period_end || calc.year ? economicPeriod(calc) : calculationPeriod(calc) || "Period not recorded";
    metric.append(value, element("span", "meta", periodLabel + " · " + (calc.label || calc.id)));
    const current = currentCalculation(calc);
    const explanation = run.analysis && calculationPeriod(calc) ? "Dated saved inputs; the calculation basis states periods and adjustments." : current ? (number(output.value) === null ? "Latest period selected; final ratio unavailable." : "Latest matched " + calc.report_type.toUpperCase() + " inputs.") : "Historical or undated result; a matched current-period result is not available.";
    metric.append(element("p", "basis", explanation + (calc.current_period_reason ? " " + calc.current_period_reason : "")));
    if (number(output.value) === null) metric.append(element("p", "basis unavailable", "See missing inputs in calculation details."));
    if (run.analysis) {
      const basis = Object.entries(calc.inputs || {}).map(([name, input]) => name + " · " + economicPeriod(input) + ". " + text(input && input.basis));
      metric.append(detail("Calculation basis & periods", [element("p", "basis", text(calc.basis)), recordList(basis), referenceList([calc.id], run)]));
    }
    for (const item of comparisons.filter((item) => item.metric_key === formula || item.metric_key === primary)) {
      metric.append(managementComparison(item, run));
      displayedComparisons.add(item.id);
    }
    metrics.append(metric);
  }
  if (metrics.children.length) metricSection.append(metrics);
  const additional = comparisons.filter((item) => !displayedComparisons.has(item.id));
  if (additional.length) {
    const guidance = element("div", "management-grid");
    for (const item of additional) guidance.append(managementComparison(item, run));
    metricSection.append(guidance);
  }
  if (!metrics.children.length && !comparisons.length) metricSection.append(element("p", "basis", "No separate saved metrics or structured management comparisons are included."));
  view.append(metricSection);
  if (run.analysis) view.append(renderAnalysisReview(run));
  const reportingDates = sources.map((source) => source.period && source.period.end).filter(Boolean).sort();
  const recency = element("section", "company-section current-data");
  recency.append(element("p", "basis", "Latest reporting period in saved sources: " + (reportingDates.pop() || "Unavailable") + ". Frozen analysis date: " + run.analysis_date + (run.analysis ? ". Saved run completed: " : ". Financial review: ") + text(run.reviewed_at).slice(0, 10) + ". This timestamp does not refresh the underlying data."));
  if ((run.current_data_limits || []).length) recency.append(detail("Current data limits", [recordList(run.current_data_limits)]));
  view.append(recency);
  if ((run.material_inputs || []).length) view.append(renderMaterialInputs(run.material_inputs, sources));
  const working = element("section", "company-section");
  working.id = "company-working";
  working.append(element("h3", "", "Sources & working"));
  if ((run.saved_records || []).length) {
    const records = run.saved_records.map((record) => {
      const item = detail(record.label || record.metric || record.id, [materialValue(record), element("p", "basis", economicPeriod(record)), sourceRecord(record, sources)]);
      return item;
    });
    working.append(detail("Referenced evidence & assumptions (" + records.length + ")", records));
  }
  working.append(detail("Calculations & inputs (" + calculations.length + ")", calculations.length ? calculations.map((calc) => renderCalculation(calc, sources)) : [element("p", "unavailable", "No named calculations saved.")]));
  working.append(detail("Analysis & interpretation", (run.interpretation || []).length ? [recordList(run.interpretation)] : [element("p", "unavailable", "No separate interpretation saved.")]));
  if (run.analysis) working.append(detail("Original full report", [readableReport(run.narrative)]));
  working.append(detail("Notes & limitations", (run.notes || []).length ? [recordList(run.notes)] : [element("p", "unavailable", "No separate notes saved.")]));
  const benchmark = run.benchmark || {};
  const benchmarkContent = [table(["Saved statistic", "Percent / percentage points"], [["Candidate annualized return (%)", savedValue(benchmark.candidate_annualized_return_percent)], ["Benchmark annualized return (%)", savedValue(benchmark.benchmark_annualized_return_percent)], ["Difference (percentage points)", savedValue(benchmark.difference_percentage_points)]]), element("p", "basis", text(benchmark.interpretation)), element("p", "basis", text(benchmark.limits)), element("p", "basis", text(benchmark.context))];
  benchmarkContent[0].id = "company-return";
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
  const provenance = [element("pre", "", text(run.provenance))];
  if (run.analysis) provenance.unshift(element("p", "meta", "Original submission review status: " + text(run.analysis.review_status)));
  working.append(detail("Run provenance", provenance));
  if ((run.original_calculations || []).length) {
    const trace = [];
    for (const calc of run.original_calculations) {
      const item = detail(calc.label || calc.id, [element("pre", "trace", text(calc))]);
      if (!calculations.some((record) => record.id === calc.id)) item.id = "calculation-" + calc.id;
      trace.push(item);
    }
    working.append(detail("Original calculation trace", [element("p", "basis", "Original saved operations and named formulas, preserved as recorded."), ...trace]));
  }
  view.append(working);
  if (loadedRunId === run.id) for (const details of view.querySelectorAll("details")) if (opened.has(details.firstElementChild.textContent)) details.open = true;
  loadedRunId = run.id;
  view.hidden = false;
}
async function loadMarketPrice(run, request) {
  if (!Number.isInteger(run.company.instrument_id) || run.company.instrument_id <= 0) return;
  let quote = null;
  try {
    const response = await getJSON("/api/market-price/" + encodeURIComponent(run.company.instrument_id));
    const candidate = response.quote;
    const reportCurrency = (run.price || {}).currency;
    const date = candidate && typeof candidate.date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(candidate.date) ? new Date(candidate.date + "T00:00:00Z") : null;
    if (candidate && candidate.instrument_id === run.company.instrument_id && /^[A-Z]{3}$/.test(candidate.currency) && (!reportCurrency || candidate.currency === reportCurrency) && candidate.unit === "currency/share" && String(candidate.scale) === "1" && candidate.kind === "daily_close" && number(candidate.value) !== null && number(candidate.value) > 0 && date && Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === candidate.date) quote = candidate;
  } catch (error) { /* The report remains available without a separate market quote. */ }
  if (request !== runRequest || loadedRunId !== run.id) return;
  const price = $("latest-market-price");
  price.replaceChildren(document.createTextNode("Latest market price: "));
  if (!quote) { price.append(document.createTextNode("unavailable")); return; }
  price.append(savedValue(quote.value, quote.currency + "/share"), document.createTextNode(" · Close · " + quote.date));
  $("latest-market-price-evidence").replaceChildren(element("p", "detail-label", "Latest market price"), element("p", "basis", "Daily close from the configured evidence store. Adjustment basis is unverified."), element("pre", "", text(quote)));
}
async function loadRun(id) {
  const request = ++runRequest;
  $("company-error").hidden = true;
  if (!id) { $("company-view").hidden = true; return; }
  $("company-status").hidden = false;
  $("company-status").textContent = "Loading saved analysis…";
  // Hide the previous company while loading so a failed selection cannot mislabel it.
  $("company-view").hidden = true;
  try {
    const run = await getJSON("/api/runs/" + encodeURIComponent(id));
    if (request !== runRequest) return;
    renderCompany(run);
    $("company-status").classList.remove("stale");
    $("company-status").textContent = "";
    $("company-status").hidden = true;
    await loadMarketPrice(run, request);
  } catch (error) {
    if (request !== runRequest) return;
    $("company-error").hidden = false;
    $("company-error").textContent = "Could not load this saved analysis. Check the configured saved-view file and refresh.";
    $("company-status").classList.add("stale");
    $("company-status").hidden = false;
    $("company-status").textContent = "Saved analysis unavailable";
  }
}
function savedRunLabel(run, runs = []) {
  const label = run.company.name + " · " + (run.analysis_kind === "structured" ? "Structured" : "Financial review") + " · " + text(run.reviewed_at).slice(0, 10);
  const matches = runs.filter(other => savedRunLabel(other) === label);
  if (matches.length < 2) return label;
  const asOf = " · As of " + text(run.analysis_date);
  return label + asOf + (matches.some(other => other.id !== run.id && other.analysis_date === run.analysis_date) ? " · " + run.id : "");
}
async function loadRuns(force = false) {
  if (runsLoading || (runsLoaded && !force)) return;
  runsLoading = true;
  $("company-error").hidden = true;
  $("company-status").hidden = false;
  $("company-status").textContent = "Loading report versions…";
  try {
    const data = await getJSON("/api/runs");
    const selected = $("run-select").value;
    $("run-select").replaceChildren();
    for (const run of data.runs) {
      const option = element("option", "", savedRunLabel(run, data.runs));
      option.value = run.id;
      option.title = "Analysis date: " + text(run.analysis_date) + (run.analysis_kind === "structured" ? " · Analysis completed: " : " · Financial review: ") + text(run.reviewed_at).slice(0, 10);
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
    $("company-status").hidden = false;
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
