"use strict";

const $ = (id) => document.getElementById(id);
const labels = { pending: "Pending", in_progress: "In progress", blocked: "Blocked", done: "Done" };
const publicDocs = new Set([
  "AGENTS.md", "CONTRIBUTING.md", "README.md", "DESIGN.md", "docs/analysis-process.md", "docs/architecture.md", "work/README.md",
  "docs/analysis-policy.md", "docs/calculations.md", "docs/company-workflow.md", "docs/research/system-readiness-review.md",
  "docs/research/borsdata-retrieval-storage.md", "docs/codex-integration.md", "docs/saved-analysis-view.md", "docs/material-inputs.md", "docs/analysis-workflow.md",
]);
let currentPlan = null;
let loading = false;
let lastSuccess = null;
let lastPlanText = null;
let runsLoaded = false;
let indexRequest = 0;
let indexedRuns = [];
let indexedCompanies = new Map();
const selectedVersions = new Map();
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
function rounded(value, minimumFractionDigits = 0) {
  const numeric = number(value);
  return numeric === null ? "Unavailable" : numeric.toLocaleString("en-GB", { minimumFractionDigits, maximumFractionDigits: 2 });
}
function savedValue(value, unit, minimumFractionDigits = 0) {
  const displayUnit = unit === "percent" ? "%" : unit === "dimensionless" ? "×" : unit;
  const missing = number(value) === null;
  const node = element("span", missing ? "unavailable" : "", missing ? "Unavailable" : rounded(value, minimumFractionDigits) + (displayUnit ? (["%", "×"].includes(displayUnit) ? "" : " ") + displayUnit : ""));
  node.title = "Exact saved value: " + text(value) + (unit ? " " + unit : "");
  return node;
}
function headlinePrice(record, value) {
  const node = savedValue(value, record.currency || record.unit, 2);
  node.title = "Exact saved value: " + text(record.value) + " · unit " + text(record.unit) + " · scale " + text(record.scale) + " · currency " + text(record.currency);
  return node;
}
function sourceRefs(input, sources, originLabel) {
  const refs = element("div");
  const evidence = Array.isArray(input.evidence) ? input.evidence : input.evidence ? [input.evidence] : [];
  const ids = new Set([input.source_id, input.report_id, input.pointer && input.pointer.report_id, ...evidence.map((e) => typeof e === "string" ? e : e.report_id || e.source_id)].filter(Boolean));
  for (const id of ids) {
    const source = sources.find((s) => s.id === id);
    if (!source) { refs.append(element("span", "source-ref", (originLabel || (String(id).startsWith("src_") ? "Frozen API source ID" : "Saved source ID")) + ": " + id)); continue; }
    refs.append(savedLink("source-" + id, "Source: " + source.title));
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
  const explicitUnits = [price.currency + "/share today", price.currency + "/share", price.currency + "/shares"];
  const priceUnitMatches = price.unit === "currency/share" || explicitUnits.includes(price.unit);
  return scenarios.every((scenario) => priceUnitMatches && (explicitUnits.includes(scenario.unit) ||
    (scenario.unit === "currency/share" && scenario.currency === price.currency)));
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
  if ($("panel-company") && $("panel-company").contains(target) && $("panel-company").hidden) selectTab("company");
  if (target.tagName === "DETAILS") target.open = true;
  for (let parent = target.parentElement; parent; parent = parent.parentElement) {
    if (parent.tagName === "DETAILS") parent.open = true;
  }
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
function shortScenarioName(scenario) {
  return {bear: "Bear", base: "Base", bull: "Bull"}[scenario.id] || "Case";
}
function endpointChart(run, quote = null) {
  const scenarios = scenarioEndpoints(run);
  const wrapper = element("div", "endpoint-charts");
  for (const [key, heading, dateKey] of [["present_value", "Present value", "present_value_date"], ["future_target", "Future target", "target_date"]]) {
    const panel = element("div", "endpoint-panel");
    const present = key === "present_value";
    const dates = [...new Set(scenarios.map((scenario) => datedEndpoint(scenario[dateKey])))];
    panel.append(element("h4", "", heading), element("p", "endpoint-date", dates.join(" / ")));
    const values = scenarios.map((item) => number(item[key] && item[key].value));
    const units = new Set(scenarios.map((item) => item[key] && item[key].unit));
    const comparable = units.size === 1 && !units.has(undefined) && values.every((value) => value !== null && value >= 0);
    if (!comparable) {
      panel.append(element("p", "callout", "Comparable nonnegative saved endpoints are unavailable. Read the exact scenario records below."));
    } else {
      const priceMatches = quote && matchingPrice({...quote, value: quote.normalized_value, scale: "1"}, scenarios.map((item) => item[key]));
      const maximum = Math.max(1, ...values, priceMatches ? quote.normalized_value : 0);
      const svg = svgElement("svg", { viewBox: "0 0 500 250", class: "chart endpoint-chart " + (present ? "present-chart" : "future-chart"), role: "img", "aria-label": heading + (present ? " horizontal dot plot: " : " vertical columns: ") + scenarios.map((item) => item.name + ", " + text(item[key].value) + " " + item[key].unit + ", " + datedEndpoint(item[dateKey])).join("; ") });
      svg.append(svgElement("text", { x: 16, y: 20, class: "axis-text" }, [...units][0]));
      if (present) {
        svg.append(svgElement("line", { x1: 130, x2: 430, y1: 213, y2: 213, class: "chart-axis" }), svgElement("text", { x: 130, y: 237, class: "axis-text" }, "0"), svgElement("text", { x: 430, y: 237, class: "axis-text", "text-anchor": "end" }, rounded(maximum)));
        if (priceMatches) {
          const x = 130 + quote.normalized_value / maximum * 300;
          svg.append(svgElement("line", { x1: x, x2: x, y1: 35, y2: 213, class: "price-line" }));
        }
      } else {
        svg.append(svgElement("line", { x1: 25, x2: 475, y1: 188, y2: 188, class: "chart-axis" }));
        if (priceMatches) {
          const y = 188 - quote.normalized_value / maximum * 135;
          svg.append(svgElement("line", {x1: 25, x2: 475, y1: y, y2: y, class: "price-line"}));
        }
      }
      scenarios.forEach((scenario, index) => {
        const label = shortScenarioName(scenario);
        const link = svgElement("a", { href: "#scenario-" + scenario.id, "aria-label": scenario.name + ": rationale and assumptions" });
        link.addEventListener("click", (event) => openSavedTarget("scenario-" + scenario.id, event));
        if (present) {
          const y = 55 + index * 145 / Math.max(1, scenarios.length - 1);
          const x = 130 + values[index] / maximum * 300;
          link.append(svgElement("rect", { x: 0, y: y - 27, width: 500, height: Math.min(60, 145 / Math.max(1, scenarios.length - 1)), fill: "transparent", "pointer-events": "all", class: "chart-hit-area" }));
          link.append(svgElement("text", { x: 16, y: y + 5 }, label), svgElement("circle", { cx: x, cy: y, r: 7, class: "scenario-dot " + scenario.id }), svgElement("text", { x, y: y - 13, "text-anchor": "middle" }, rounded(scenario[key].value)));
        } else {
          const slot = 440 / scenarios.length;
          const x = 30 + index * slot + slot / 2;
          const height = values[index] / maximum * 135;
          link.append(svgElement("rect", { x: 30 + index * slot, y: 28, width: slot, height: 212, fill: "transparent", "pointer-events": "all", class: "chart-hit-area" }));
          link.append(svgElement("rect", { x: x - Math.min(38, slot * .3), y: 188 - height, width: Math.min(76, slot * .6), height, class: "scenario-bar " + scenario.id }), svgElement("text", { x, y: 177 - height, "text-anchor": "middle" }, rounded(scenario[key].value)), svgElement("text", { x, y: 217, "text-anchor": "middle" }, label));
        }
        svg.append(link);
      });
      panel.append(svg);
      if (priceMatches) panel.append(element("p", "chart-caption market-reference-label", "Latest stored market price · " + quote.date + " · " + rounded(quote.normalized_value) + " " + quote.currency + "/share. " + (present ? "Dated comparison price." : "Present-day comparison, not a forecast.")));
    }
    panel.append(element("p", "chart-caption", present ? "Discounted share target plus discounted dividends. Saved required return; see valuation assumptions." : "Share target at the saved horizon. Separately paid dividends are excluded. Each chart has its own scale."));
    wrapper.append(panel);
  }
  return wrapper;
}
function displayName(name) { return text(name).replace(/\s*\(publ\)\s*$/i, "").trim(); }
function normalizedPrice(price) {
  const value = number(price && price.value), scale = number(price && price.scale);
  return value === null || scale === null || scale <= 0 || !Number.isFinite(value * scale) ? null : value * scale;
}
function tableCells(line) {
  const source = String(line).trim(), cells = [];
  let cell = "", trailingSeparator = false;
  for (let index = 0; index < source.length; index++) {
    const char = source[index], next = source[index + 1];
    if (char === "\\" && (next === "\\" || next === "|")) { cell += next; index++; trailingSeparator = false; }
    else if (char === "|") { cells.push(cell.trim()); cell = ""; trailingSeparator = true; }
    else { cell += char; trailingSeparator = false; }
  }
  cells.push(cell.trim());
  if (source.startsWith("|")) cells.shift();
  if (trailingSeparator) cells.pop();
  return cells;
}
function shortPeriod(value) {
  return String(value).replace(/\b(January|February|March|April|May|June|July|August|September|October|November|December)\b/g, month => month.slice(0, 3));
}
function scalarCell(cell) {
  const value = String(cell).trim();
  return /^[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/.test(value) ? number(value.replace(/,/g, "")) : null;
}
function driverForecasts(run) {
  const scenarios = scenarioEndpoints(run);
  const year = scenarios[0]?.target_date?.value;
  if (!/^\d{4}$/.test(year) || scenarios.length < 2 || scenarios.some(item =>
    item.target_date?.value !== year || item.target_date.precision !== "year")) return null;
  const originals = run.original_calculations || [];
  const forecast = scenarios.map(scenario => {
    const valuation = originals.find(calc => calc.id === scenario.valuation_calculation_id && calc.formula === "valuation_case");
    const ebit = valuation && formulaInput(valuation, "forecast_ebit");
    const operating = ebit && originals.find(calc => [calc.id, calc.id + "#ebit"].includes(ebit.id) && calc.formula === "revenue_ebit");
    if (!operating || operating.outputs?.ebit?.value !== ebit.calculation_value || operating.outputs.ebit.unit !== ebit.unit) return null;
    const sales = formulaInput(operating, "revenue"), margin = formulaInput(operating, "ebit_margin");
    const currency = sales?.unit === "currency" ? sales.currency : sales?.unit;
    const salesValue = number(sales?.calculation_value), marginValue = number(margin?.calculation_value);
    if (!/^[A-Z]{3}$/.test(currency) || salesValue === null || margin?.unit !== "dimensionless" || marginValue === null) return null;
    return {scenario, currency, sales: salesValue / 1e6, margin: marginValue * 100, calculation: operating.id};
  });
  if (forecast.some(item => !item || item.currency !== forecast[0].currency)) return null;
  // The saved operating table declares the accounting basis of the formula inputs.
  const operatingTables = (run.analysis?.sections || []).filter(section => section.id === "valuation")
    .flatMap(section => section.paragraphs.flatMap(paragraph => paragraph.text.split(/\r?\n/).flatMap((line, index, lines) => {
      const headers = tableCells(line);
      if (headers.length !== scenarios.length + 1 || !headers[0].startsWith(year + " ") ||
          !scenarios.every((scenario, i) => headers[i + 1] === scenario.name) || !isTableDivider(lines[index + 1])) return [];
      return [readTableRows(lines, index + 2)];
    })));
  const comparable = operatingTables.some(rows => {
    const sales = rows.find(row => row[0] === "Net sales, " + forecast[0].currency + " m");
    const margin = rows.find(row => row[0] === "Reported EBIT margin");
    return forecast.every((item, i) => {
      const marginValue = margin?.[i + 1]?.endsWith("%") ? scalarCell(margin[i + 1].slice(0, -1)) : null;
      return scalarCell(sales?.[i + 1]) === item.sales && marginValue !== null && Math.abs(marginValue - item.margin) < 1e-9;
    });
  });
  return comparable ? {year, forecast} : null;
}
function driverHistory(headers, rows, context) {
  const saved = context?.drivers;
  if (!saved) return null;
  const {forecast, year} = saved, currency = forecast[0].currency;
  const sales = headers.indexOf("Net sales (" + currency + " m)"), margin = headers.indexOf("EBIT margin (%)");
  if (sales < 1 || margin < 1 || !/^\s*Reported group (?:history|actuals) uses? net sales\b/i.test(context.paragraph.text)) return null;
  const references = new Set(context.paragraph.references);
  const actuals = (context.run.original_calculations || []).filter(calc =>
    calc.formula === "ebit_margin" && references.has(calc.id + "#margin_percent"));
  const periods = rows.map(row => {
    const label = row[0], annual = /^\d{4}$/.test(label), trailing = /^R12\b/.test(label);
    const salesValue = scalarCell(row[sales]), marginValue = scalarCell(row[margin]);
    const marginPrecision = row[margin].split(".")[1]?.length || 0;
    const record = actuals.find(calc => {
      const ebit = formulaInput(calc, "ebit"), revenue = formulaInput(calc, "revenue");
      const date = ebit?.period_end, output = calc.outputs?.margin_percent;
      if (ebit?.kind !== "flow" || !/^\d{4}-\d{2}-\d{2}$/.test(date) || date > context.run.analysis_date || date.slice(0, 4) >= year ||
          !/^\d{4}-\d{2}-\d{2}$/.test(ebit.period_start) ||
          !revenue || (revenue.unit === "currency" ? revenue.currency : revenue.unit) !== currency ||
          output?.unit !== "percent" || number(output.value) === null || marginValue === null || marginPrecision > 12 ||
          salesValue === null || number(revenue.calculation_value) === null || Number(revenue.calculation_value) / 1e6 !== salesValue ||
          Number(Number(output.value).toFixed(marginPrecision)) !== marginValue) return false;
      const days = (Date.parse(date) - Date.parse(ebit.period_start)) / 86400000 + 1;
      if (!(days >= 360 && days <= 372)) return false;
      const report = (context.run.sources || []).find(source => source.id === revenue.report_id);
      const datedFlow = revenue.kind === "flow" && revenue.report_type === ebit.report_type &&
        revenue.period_start === ebit.period_start && revenue.period_end === date;
      // Some cited report inputs record the exact flow dates in the saved label.
      const citedFlow = revenue.kind === "report" && report?.period?.end === date && report.published_at &&
        report.published_at <= context.run.analysis_date && revenue.quote && references.has(report.id + ":p" + revenue.page) &&
        (revenue.label || "").includes(ebit.period_start + " to " + date);
      if (!datedFlow && !citedFlow) return false;
      if (annual) return ebit.report_type === "year" && label === date.slice(0, 4);
      const month = new Date(date + "T00:00:00Z").toLocaleString("en-GB", {month: "long", timeZone: "UTC"});
      return trailing && ebit.report_type === "r12" && label === "R12 " + month + " " + date.slice(0, 4);
    });
    return {label, annual, trailing, date: record && formulaInput(record, "ebit").period_end};
  });
  if (periods.filter(item => item.annual).length < 2 || periods.filter(item => item.trailing).length > 1 ||
      periods.some((item, i) => !item.date || (i > 0 && (!periods[i - 1].annual || periods[i - 1].date >= item.date))) ||
      new Set(periods.map(item => item.label)).size !== rows.length) return null;
  const section = element("div", "driver-history");
  for (const [index, key, unit] of [[sales, "sales", ""], [margin, "margin", "%"]]) {
    const values = rows.map(row => scalarCell(row[index])), targets = forecast.map(item => item[key]);
    const minimum = Math.min(...values, ...targets), maximum = Math.max(...values, ...targets);
    const y = (value) => 133 - (value - minimum) / (maximum - minimum || 1) * 89;
    const actualX = (i) => 67 + 184 * i / Math.max(1, rows.length - 1);
    const caseX = (i) => 289 + 120 * i / (forecast.length - 1);
    const svg = svgElement("svg", {viewBox: "0 0 438 172", class: "chart driver-chart", role: "img",
      "aria-label": headers[index] + ". History on the memo's stated basis: " + rows.map(row => row[0] + " " + row[index] + unit).join(", ") +
        ". Separate " + year + " assumptions: " + forecast.map(item => item.scenario.name + " " + rounded(item[key]) + unit).join(", ")});
    for (const value of new Set([minimum, maximum])) {
      svg.append(svgElement("line", {x1: 61, x2: 430, y1: y(value), y2: y(value), class: "chart-axis"}),
        svgElement("text", {x: 57, y: y(value) + 4, "text-anchor": "end", class: "axis-text"}, rounded(value) + unit));
    }
    svg.append(svgElement("line", {x1: 270, x2: 270, y1: 22, y2: 138, class: "chart-axis"}),
      svgElement("text", {x: 349, y: 14, "text-anchor": "middle", class: "axis-text"}, year + " assumptions"));
    periods.forEach((period, i) => {
      if (period.annual && i > 0 && Number(period.label) - Number(periods[i - 1].label) === 1) {
        svg.append(svgElement("line", {x1: actualX(i - 1), x2: actualX(i), y1: y(values[i - 1]), y2: y(values[i]), class: "driver-actual-line"}));
      }
      const point = svgElement("circle", {cx: actualX(i), cy: y(values[i]), r: 4, class: period.annual ? "driver-actual" : "driver-trailing"});
      point.append(svgElement("title", {}, period.label + " · " + rows[i][index] + unit));
      svg.append(point);
      if (i === 0 || i === periods.length - 1 || (period.annual && periods[i + 1]?.trailing)) {
        svg.append(svgElement("text", {x: actualX(i), y: 157, "text-anchor": "middle", class: "axis-text"}, period.annual ? period.label : "R12"));
      }
    });
    forecast.forEach(({scenario}, i) => {
      const point = svgElement("circle", {cx: caseX(i), cy: y(targets[i]), r: 5, class: "scenario-dot " + scenario.id});
      point.append(svgElement("title", {}, scenario.name + " · " + rounded(targets[i]) + unit));
      svg.append(point, svgElement("text", {x: caseX(i), y: y(targets[i]) - 9, "text-anchor": "middle", class: "axis-text"}, rounded(targets[i]) + unit),
        svgElement("text", {x: caseX(i), y: 157, "text-anchor": "middle", class: "axis-text"}, shortScenarioName(scenario)));
    });
    const panel = element("div");
    panel.append(element("h4", "", headers[index]), svg);
    section.append(panel);
  }
  const trailing = periods.find(item => item.trailing);
  const wrap = element("div", "driver-comparison");
  wrap.append(section, element("p", "chart-caption", "Saved history" + (trailing ? " · open dot " + trailing.label : "") +
    ". The separate " + year + " markers are terminal assumptions. Accounting labels follow the memo's stated basis. Check the linked records for the underlying definitions."), detail("Source table and forecast calculations", [
    table(headers, rows), referenceList([...new Set([...context.paragraph.references, ...forecast.map(item => item.calculation)])], context.run),
  ]));
  return wrap;
}
let periodTableId = 0;
function periodTable(headers, rows, context) {
  const saved = table(headers, rows);
  if (headers.includes("What changes from base") && headers.includes("Annual IRR")) saved.className += " sensitivity-table";
  if (headers[0] !== "Period" || rows.length < 2 || rows.some(row => row.length !== headers.length || !row[0])) return saved;
  const drivers = driverHistory(headers, rows, context);
  if (drivers) return drivers;
  const measures = headers.flatMap((label, index) => index && rows.every(row => scalarCell(row[index]) !== null) ? [{label, index, values: rows.map(row => scalarCell(row[index]))}] : []);
  if (!measures.length) return saved;
  const wrapper = element("div", "period-history"), label = element("label", "", "Measure"), select = element("select"), chart = element("div", "period-chart");
  select.id = "period-measure-" + periodTableId++;
  label.htmlFor = select.id;
  select.setAttribute("aria-label", "Measure · saved period values");
  measures.forEach((measure, index) => { const option = element("option", "", measure.label); option.value = String(index); select.append(option); });
  function draw() {
    const measure = measures[Number(select.value) || 0], minimum = Math.min(0, ...measure.values), maximum = Math.max(0, ...measure.values), range = maximum - minimum || 1;
    const svg = svgElement("svg", {viewBox: "0 0 600 220", class: "chart period-chart-svg", role: "img", "aria-label": measure.label + " · exact saved period values"});
    svg.append(svgElement("text", {x: 15, y: 18, class: "axis-text"}, measure.label));
    const zero = 170 - (0 - minimum) / range * 120;
    svg.append(svgElement("line", {x1: 15, x2: 585, y1: zero, y2: zero, class: "chart-axis"}));
    measure.values.forEach((value, index) => {
      const slot = 570 / rows.length, x = 15 + slot * (index + .5), y = 170 - (value - minimum) / range * 120;
      svg.append(svgElement("rect", {x: x - Math.min(35, slot * .3), y: Math.min(y, zero), width: Math.min(70, slot * .6), height: Math.abs(y - zero), class: "scenario-bar"}), svgElement("text", {x, y: value < 0 ? y + 17 : y - 8, "text-anchor": "middle"}, rows[index][measure.index]), svgElement("text", {x, y: 207, "text-anchor": "middle", class: "axis-text", "aria-label": rows[index][0]}, shortPeriod(rows[index][0])));
    });
    chart.replaceChildren(svg);
  }
  select.addEventListener("change", draw);
  draw();
  wrapper.append(label, select, chart, element("p", "chart-caption", "Exact saved values and period labels. Source references and saved qualifications below retain period length, units and basis."), detail("Source table", [saved]));
  return wrapper;
}
function isTableDivider(line) {
  const cells = tableCells(line ?? "");
  return cells.length > 0 && cells.every(cell => /^:?-{3,}:?$/.test(cell));
}
function readTableRows(lines, index) {
  const rows = [];
  while (index < lines.length && lines[index].includes("|")) {
    const row = tableCells(lines[index]);
    if (!row.length) break;
    rows.push(row);
    index++;
  }
  return rows;
}
function readableReport(markdown, context) {
  const node = element("div", "report-body");
  const lines = String(markdown || "").split(/\r?\n/);
  let paragraph = [];
  const flush = () => { if (paragraph.length) { node.append(element("p", "saved-text", paragraph.join("\n"))); paragraph = []; } };
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*$/);
    const headers = line.includes("|") ? tableCells(line) : [];
    if (heading) { flush(); node.append(element("h4", "", heading[2])); }
    else if (headers.length && isTableDivider(lines[index + 1])) {
      flush();
      const rows = readTableRows(lines, index + 2);
      index += rows.length + 1;
      node.append(periodTable(headers, rows, context));
    } else if (!line.trim()) flush();
    else paragraph.push(line);
  }
  flush();
  if (!node.children.length) node.append(element("p", "unavailable", "No saved narrative is available."));
  return node;
}
function companySections(view) {
  const overview = element("section", "company-overview");
  overview.id = "company-panel-overview";
  const panels = {overview};
  view.append(overview);
  for (const [name, title, description] of [
    ["business", "Investment case", "Business, opportunity and principal risks"],
    ["valuation", "Valuation assumptions", "Scenario inputs, weights and reasoning"],
    ["financials", "Financials and management", "Dated results, calculation basis and management outlook"],
    ["evidence", "Evidence", "Original analysis, sources, definitions and calculation records"],
  ]) {
    const chapter = detail("", []);
    chapter.className = "company-chapter";
    chapter.id = "company-panel-" + name;
    chapter.firstElementChild.append(element("strong", "", title), element("span", "", description));
    const body = element("div", "chapter-body");
    chapter.append(body);
    view.append(chapter);
    panels[name] = body;
  }
  return panels;
}
function readerSection(section, run, drivers) {
  const block = element("article", "reader-section");
  block.id = "reader-" + section.id;
  for (const [index, paragraph] of (section.paragraphs || []).entries()) {
    const heading = String(paragraph.text || "").match(/^###\s+([^\n]+)\n+/);
    const content = readableReport(heading ? paragraph.text.slice(heading[0].length) : paragraph.text, {paragraph, run, drivers});
    content.append(detail((paragraph.kind || "Saved text") + " · sources & calculations", [referenceList(paragraph.references, run)]));
    if (heading) {
      const subsection = detail(heading[1], [content], section.id === "drivers" && index === 0);
      subsection.className = "memo-subsection";
      block.append(subsection);
    } else block.append(content);
  }
  return block;
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
  const relationship = { direct: "Direct management " + item.statement_type, related: "Related management statement · " + item.statement_type, not_stated: "No direct guidance stated for this measure." }[item.relationship];
  block.append(element("p", "detail-label", relationship));
  if (item.relationship !== "not_stated") block.append(element("p", "saved-text", item.statement));
  const evidenceContent = [element("h5", "", item.metric_label)];
  if (item.relationship === "not_stated") evidenceContent.push(element("p", "saved-text", item.statement));
  if (item.statement_date || item.target_period) evidenceContent.push(element("p", "meta", "Statement date: " + text(item.statement_date) + " · Horizon: " + text(item.target_period)));
  evidenceContent.push(element("p", "basis", "Issuer basis: " + item.basis));
  if (item.actual) evidenceContent.push(element("p", "basis", "Saved comparison: " + item.actual));
  evidenceContent.push(referenceList([...(item.references || []), ...(item.actual_references || [])], run));
  if (item.evidence) {
    const evidence = item.evidence;
    evidenceContent.push(element("p", "meta", "Report " + evidence.report_id + " · physical page " + evidence.page), element("blockquote", "saved-text", evidence.quote), referenceList([evidence.report_id + ":p" + evidence.page], run));
  }
  block.append(detail("Definition & source", evidenceContent));
  return block;
}
function scenarioAssumptions(run) {
  const scenarios = scenarioEndpoints(run);
  const inputs = [["forecast_ebit", "Forecast EBIT"], ["exit_multiple", "Exit EV / EBIT"], ["years", "Years"], ["annual_dividend_per_share", "Annual dividend / share"], ["required_return", "Saved required return"]];
  const section = element("section", "company-section scenario-assumptions");
  section.append(element("h3", "", "The saved valuation inputs"), element("p", "basis", "The required return belongs to this saved report. A later policy or market quote does not replace it. Missing inputs and incomplete mappings remain visible in calculation details."));
  section.append(table(["Scenario", ...inputs.map(([, label]) => label)], scenarios.map((scenario) => {
    const calc = (run.calculations || []).find((item) => item.id === scenario.valuation_calculation_id);
    return [savedLink("scenario-" + scenario.id, scenario.name, ""), ...inputs.map(([key]) => {
      const input = ((calc || {}).inputs || {})[key] || {};
      // Only the saved normalized input carries the scale used by the formula.
      const normalized = input.calculation_value;
      const rate = key === "required_return" && number(normalized) !== null;
      const unit = rate ? "percent" : key === "exit_multiple" ? "×" : key === "years" ? "" : String(input.unit || "").replace("currency", input.currency || "currency");
      const millions = key === "forecast_ebit" && /^[A-Z]{3}$/.test(unit) && number(normalized) !== null;
      const value = savedValue(rate ? Number(normalized) * 100 : millions ? Number(normalized) / 1000000 : normalized, millions ? unit + " million" : unit);
      value.title = "Original saved input: " + text(input.value) + " " + text(input.unit) + " · scale " + text(input.scale) + ". Saved normalized input: " + text(normalized);
      return value;
    })];
  })));
  return section;
}
function scenarioRationale(run, useMemo = true) {
  const section = element("section", "company-section scenario-reasoning");
  section.append(element("h3", "", "What each scenario assumes"));
  for (const scenario of scenarioEndpoints(run)) {
    const editorial = useMemo && run.reader_memo && run.reader_memo.schema_version === 1 && (run.reader_memo.scenarios || []).find((item) => item.id === scenario.id);
    const prose = editorial || scenario;
    const item = detail(scenario.name, [], scenario.id === "base");
    item.className = "scenario-case";
    item.id = (useMemo ? "scenario-" : "canonical-scenario-") + scenario.id;
    item.append(element("h4", "", "Business outcome"), element("p", "saved-text", prose.rationale));
    const valuation = element("p", "basis");
    valuation.append(document.createTextNode("Present value · " + datedEndpoint(scenario.present_value_date) + ": "), savedValue(scenario.present_value.value, scenario.present_value.unit), document.createTextNode(". Future target · " + datedEndpoint(scenario.target_date) + ": "), savedValue(scenario.future_target.value, scenario.future_target.unit));
    item.append(valuation);
    const weight = (run.probability || {}).weights && run.probability.weights[scenario.id];
    if (number(weight) !== null) item.append(element("h4", "", "Why this weight"), element("p", "basis", "Saved weight: " + rounded(Number(weight) * 100) + "%. " + (prose.probability_rationale || "No separate weight rationale saved.")));
    const assumptions = [element("h4", "", "Valuation assumptions"), element("p", "saved-text", text(prose.assumption_rationale)), referenceList([scenario.valuation_calculation_id, scenario.weight_ref, ...(scenario.probability_references || []), ...(prose.references || [])].filter(Boolean), run)];
    item.append(detail("Assumptions, sources & calculation", assumptions));
    section.append(item);
  }
  return section;
}
function renderAnalysisReview(run) {
  const section = element("section", "company-section analysis-review");
  section.id = "company-review";
  section.append(element("h3", "", "Independent challenge of the canonical analysis"));
  const review = run.analysis_review;
  if (!review) { section.append(element("p", "callout", "No independent structured review is saved for this analysis.")); return section; }
  section.append(element("p", "meta", "Reviewer: " + text(review.reviewer) + " · Verdict: " + text(review.verdict)), element("p", "saved-text", review.summary));
  for (const finding of review.findings || []) section.append(detail(finding.id + " · " + finding.verdict, [element("p", "saved-text", finding.reasoning), element("p", "basis", "Missing evidence: " + text(finding.missing_evidence)), referenceList(finding.references, run)]));
  if ((review.disagreements || []).length) section.append(detail("Disagreements retained", [recordList(review.disagreements)]));
  return section;
}
function returnCalculation(run) {
  const returns = (run.original_calculations || []).filter((calc) => calc.operation === "financial_formula" && calc.formula === "expected_cashflow_irr");
  const selected = (run.benchmark || {}).return_calculation_id;
  const candidates = selected === undefined ? returns : returns.filter((calc) => calc.id === selected);
  return candidates.length === 1 ? candidates[0] : null;
}
function formulaInput(calculation, field) {
  const inputs = (calculation.inputs || []).filter((input) => input.field === field);
  return inputs.length === 1 && inputs[0].id && inputs[0].id === (calculation.input_ids || {})[field] ? inputs[0] : null;
}
function usesReportPrice(calculation, price) {
  const input = calculation && formulaInput(calculation, "price");
  return input && price && price.id && price.source_id && price.date && input.id === price.id &&
    ["value", "unit", "scale", "currency", "source_id"].every((key) => input[key] === price[key]) &&
    (input.date || input.period_end) === price.date;
}
function returnUsesReportPrice(run) {
  const calculation = returnCalculation(run);
  const output = ((calculation || {}).outputs || {}).irr_percent || {};
  return Boolean(usesReportPrice(calculation, run.price) && number(output.value) !== null &&
    output.value === (run.benchmark || {}).candidate_annualized_return_percent);
}
function matchedScenarioReturns(run) {
  const scenarios = scenarioEndpoints(run), price = run.price;
  if (!run.analysis || scenarios.length < 2 || !(normalizedPrice(price) > 0)) return null;
  const calculations = (run.original_calculations || []).filter(calc => calc.operation === "financial_formula");
  const matches = [];
  for (const scenario of scenarios) {
    const valuation = calculations.find(calc => calc.id === scenario.valuation_calculation_id && calc.formula === "valuation_case");
    if (!valuation || (Object.hasOwn(valuation.input_ids || {}, "price") || (valuation.inputs || []).some(input => input.field === "price")) &&
        !usesReportPrice(valuation, price)) return null;
    const years = formulaInput(valuation, "years"), dividend = formulaInput(valuation, "annual_dividend_per_share");
    const hurdle = formulaInput(valuation, "required_return");
    const terminal = (valuation.outputs || {}).future_target;
    if (!years || !dividend || !hurdle || !terminal || !scenario.target_date?.value ||
        terminal.value !== scenario.future_target.value || terminal.unit !== scenario.future_target.unit ||
        !matchingPrice({...price, scale: "1", value: normalizedPrice(price)}, [terminal, dividend])) return null;
    const horizon = number(years.calculation_value), rate = number(hurdle.calculation_value);
    if (years.unit !== "dimensionless" || !Number.isInteger(horizon) || horizon < 1 || horizon > 10 ||
        hurdle.unit !== "dimensionless" || rate === null || rate < 0 || !Number.isFinite(rate * 100)) return null;
    const sameInput = (saved, reference) => saved && ["id", "value", "unit", "scale", "currency", "calculation_value"].every(key => saved[key] === reference[key]);
    const candidates = calculations.filter(calc => {
      if (calc.formula !== "expected_cashflow_irr" || !usesReportPrice(calc, price)) return false;
      const target = formulaInput(calc, "expected_future_target");
      return target && target.id === valuation.id + "#future_target" && target.unit === terminal.unit &&
        target.calculation_value === terminal.value && sameInput(formulaInput(calc, "years"), years) &&
        sameInput(formulaInput(calc, "expected_annual_dividend_per_share"), dividend);
    });
    if (candidates.length !== 1) return null;
    const result = (candidates[0].outputs || {}).irr_percent || {};
    if (result.unit !== "percent" || number(result.value) === null) return null;
    matches.push({scenario, horizon, rate, calculation: candidates[0], valuation, value: result.value});
  }
  const first = matches[0];
  return matches.every(item => item.horizon === first.horizon && item.rate === first.rate &&
    datedEndpoint(item.scenario.target_date) === datedEndpoint(first.scenario.target_date)) ? matches : null;
}
function scenarioReturnChart(run, matches) {
  const section = element("section", "scenario-returns");
  section.append(element("h4", "", "Annual scenario returns"));
  const hurdle = matches[0].rate * 100, zero = 0;
  const values = matches.map(item => number(item.value));
  const minimum = Math.min(zero, ...values), maximum = Math.max(hurdle, zero, ...values);
  const span = maximum - minimum || 1;
  const x = (value) => 82 + (value - minimum) / span * 240;
  const bottom = 30 + matches.length * 32;
  const svg = svgElement("svg", {viewBox: "0 0 420 " + (bottom + 19), class: "chart return-chart", role: "img",
    "aria-label": "Annual cash-flow returns at the " + run.price.date + " report price. " + matches.map(({scenario, value}) => scenario.name + " " + value + "%").join(", ") + ". Saved hurdle " + rounded(hurdle) + "%."});
  for (const [value, css] of [[zero, "chart-axis"], [hurdle, "price-line"]]) {
    svg.append(svgElement("line", {x1: x(value), x2: x(value), y1: 26, y2: bottom, class: css}));
  }
  svg.append(svgElement("text", {x: x(zero), y: bottom + 16, "text-anchor": "middle", class: "axis-text"}, "0%"),
    svgElement("text", {x: x(hurdle), y: 16, "text-anchor": "middle", class: "axis-text"}, rounded(hurdle) + "% hurdle"));
  matches.forEach(({scenario, value, calculation}, index) => {
    const y = 41 + index * 32;
    const target = "scenario-" + scenario.id;
    const link = svgElement("a", {href: "#" + target, "aria-label": scenario.name + " " + value + "%. Read assumptions."});
    link.addEventListener("click", event => openSavedTarget(target, event));
    link.append(svgElement("rect", {x: 0, y: y - 14, width: 420, height: 30, fill: "transparent", "pointer-events": "all", class: "chart-hit-area"}),
      svgElement("text", {x: 5, y: y + 5}, shortScenarioName(scenario)),
      svgElement("circle", {cx: x(number(value)), cy: y, r: 6, class: "scenario-dot " + scenario.id}),
      svgElement("text", {x: 410, y: y + 5, "text-anchor": "end"}, rounded(value) + "%"),
      svgElement("title", {}, "Saved return " + value + "% · " + calculation.id));
    svg.append(link);
  });
  section.append(svg, element("p", "chart-caption", "Includes model year-end dividends over " + matches[0].horizon + " years at the report price of " +
    rounded(normalizedPrice(run.price), 2) + " " + run.price.currency + "/share on " + run.price.date + "."),
    savedLink("company-scenarios", "See present values and share targets", ""));
  return section;
}
function returnExplanation(run) {
  const calc = returnCalculation(run);
  const rows = [["Report purchase price", rounded(normalizedPrice(run.price)) + " " + (run.price.currency || "") + " · " + run.price.date]];
  for (const [field, label] of [["expected_annual_dividend_per_share", "Expected annual dividend / share"], ["expected_future_target", "Expected terminal share target"], ["years", "Years"]]) {
    const input = (calc.inputs || []).find(item => item.field === field) || {};
    rows.push([label, savedValue(input.calculation_value, input.unit === "dimensionless" ? "" : input.unit)]);
  }
  rows.push(["Final receipt · dividend plus share target", savedValue(((calc.outputs || {}).terminal_cash_flow || {}).value, ((calc.outputs || {}).terminal_cash_flow || {}).unit)], ["Saved annual return", savedValue(((calc.outputs || {}).irr_percent || {}).value, "percent")]);
  const node = detail("How the conditional annual return is calculated", [element("p", "", "The saved model weights each scenario’s dividend and terminal share target at each payment date, then solves the annual rate that equates those cash flows with the report price. It does not average scenario returns. The formula uses constant model-year-end dividends and a common integer horizon, rather than actual dividend dates. A latest quote does not recalculate this result."), table(["Saved cash-flow input / output", "Value"], rows), referenceList([calc.id], run), savedLink("company-return", "Saved return and historical benchmark context")]);
  node.id = "return-explanation";
  return node;
}
function renderCompany(run) {
  savedReferenceIds.clear();
  const view = $("company-view");
  const sameRun = loadedRunId === run.id;
  const detailStates = new Map(Array.from(view.querySelectorAll("details")).map((item, index) => [item.id || index, item.open]));
  view.replaceChildren();
  const sources = run.sources || [];
  const header = element("div", "company-header");
  const memo = run.reader_memo && run.reader_memo.schema_version === 1 ? run.reader_memo : run.analysis;
  header.append(element("h2", "", displayName(run.company.name) + (run.company.ticker ? " · " + run.company.ticker : "")), element("p", "meta", "Analysis date: " + text(run.analysis_date)));
  view.append(header);
  const panels = companySections(view);
  const conclusion = element("div", "memo-conclusion");
  conclusion.append(element("h3", "", "Investment conclusion"), element("p", "memo-lead", text(memo ? memo.summary : run.conclusion)), savedLink("company-panel-business", "Read the investment case →", ""));
  const figures = element("aside", "company-facts");
  const fact = (label, value, note) => {
    const row = element("div", "company-fact");
    row.append(element("span", "fact-label", label), value, element("small", "", note));
    figures.append(row);
    return row;
  };
  const price = run.price || {};
  const marketPrice = element("div", "market-price", "Loading…");
  marketPrice.id = "latest-market-price";
  marketPrice.setAttribute("role", "status");
  const marketRow = fact("Latest market price", marketPrice, "Quote date unavailable");
  marketRow.children[2].id = "latest-market-price-date";
  const reportPrice = element("div", "report-price");
  reportPrice.append(headlinePrice(price, normalizedPrice(price)));
  fact("Report price", reportPrice, text(price.date || price.period_end));
  const boundReturn = returnUsesReportPrice(run);
  const scenarioReturns = matchedScenarioReturns(run);
  if (scenarioReturns) conclusion.append(scenarioReturnChart(run, scenarioReturns));
  const base = scenarioEndpoints(run).find(scenario => scenario.id === "base") || scenarioEndpoints(run)[0] || {};
  const baseCalculation = (run.calculations || []).find(calc => calc.id === base.valuation_calculation_id) || {};
  const required = number(((baseCalculation.inputs || {}).required_return || {}).calculation_value);
  fact("Required return", savedValue(required === null ? null : required * 100, "percent"), "Report assumption");
  panels.overview.append(conclusion, figures);
  const marketEvidence = element("div");
  marketEvidence.id = "latest-market-price-evidence";
  panels.evidence.append(element("p", "meta", (run.analysis ? "Analysis completed: " : "Financial review: ") + text(run.reviewed_at).slice(0, 10) + " · Method: " + text(run.method)), detail("Report conclusion", [element("p", "saved-text", text(run.analysis ? run.analysis.summary : run.conclusion))]), detail("Price evidence", [element("p", "detail-label", "Report price"), element("p", "basis", text(price.basis)), sourceRefs(price, sources), element("pre", "", text(price)), marketEvidence]));
  if (run.reader_memo && memo === run.reader_memo) {
    panels.evidence.append(element("p", "basis", "Reader edition edited " + text(memo.edited_at) + ". The independent challenge applies to the canonical analysis, not this editorial rewrite."), detail("Reader edition provenance", [element("pre", "", text({schema_version: memo.schema_version, analysis_sha256: memo.analysis_sha256, edited_at: memo.edited_at}))]));
  }
  if (boundReturn) panels.valuation.append(returnExplanation(run));
  if (scenarioReturns) panels.valuation.append(detail("Saved annual return calculations", [
    table(["Scenario", "Saved annual return", "Records"], scenarioReturns.map(({scenario, value, calculation, valuation}) => [
      scenario.name, savedValue(value, "percent"), referenceList([calculation.id, valuation.id], run),
    ])),
  ]));
  if (scenarioEndpoints(run).length) panels.valuation.append(scenarioAssumptions(run));
  const drivers = driverForecasts(run);
  for (const section of (memo || {}).sections || []) {
    const chapter = element("section", "memo-section");
    chapter.append(element("h3", "", section.title || section.id), readerSection(section, run, drivers));
    (["valuation", "risks"].includes(section.id) ? panels.valuation : panels.business).append(chapter);
  }
  if (!memo) panels.business.append(element("p", "basis", "This saved run has no structured business sections. Read the original report in Evidence."), savedLink("legacy-report", "Read the original report", ""));
  const scenarioSection = element("section", "company-section");
  scenarioSection.id = "company-scenarios";
  const endpoints = scenarioEndpoints(run);
  scenarioSection.append(element("h3", "", "Valuation scenarios"), element("p", "basis", endpoints.length ? "Saved scenario endpoints. Select a mark to read its rationale and assumptions." : "Present values as of " + text(run.analysis_date) + ". Future targets and assumptions remain in the report."));
  const scenarioGrid = element("div", "scenario-grid");
  scenarioGrid.id = "company-valuation-charts";
  scenarioGrid.append(endpoints.length ? endpointChart(run) : scenarioChart(run));
  const savedScenarios = run.scenarios || [];
  const hasWeights = savedScenarios.some(item => number(item.weight) !== null);
  const scenarioTable = table(["Scenario", "Present value", ...(hasWeights ? ["Weight"] : []), "Saved basis"], savedScenarios.map((s) => {
    const basis = element("div");
    basis.append(element("p", "basis", s.basis), referenceList(s.calculation_ids, run), detail("Exact value & calculation IDs", [element("p", "exact", text(s.value) + " " + s.unit + (s.weight !== undefined ? " · exact weight " + text(s.weight) : "")), element("p", "exact", (s.calculation_ids || []).join(", "))]));
    return [s.name, savedValue(s.value, String(s.unit || "").replace(/ today$/, "")),
      ...(hasWeights ? [number(s.weight) === null ? "Unavailable" : rounded(Number(s.weight) * 100) + "%"] : []), basis];
  }));
  panels.valuation.append(detail("Saved scenario values & exact records", [scenarioTable]));
  if (endpoints.length) {
    scenarioGrid.classList.add("with-endpoints");
    const links = element("div", "scenario-links");
    for (const item of endpoints) links.append(savedLink("scenario-" + item.id, item.name + " · rationale & assumptions", ""));
    panels.valuation.append(links);
  }
  scenarioSection.append(scenarioGrid);
  const probability = run.probability || {};
  if (!scenarioReturns) scenarioSection.append(savedLink("company-panel-valuation", "Read assumptions, risks & saved hurdle →", "memo-next"));
  panels.valuation.append(detail(probability.status === "missing" ? "Probability basis" : "Weight qualifications & exact saved weights",
    [element("p", "basis", probabilityDescription(probability)), probability.status === "missing" ? null : element("pre", "", text(probability.weights))].filter(Boolean)));
  if (scenarioReturns) panels.valuation.append(scenarioSection);
  else panels.overview.append(scenarioSection);
  panels.evidence.append(detail("Original analysis", [renderAnalysis(run)]));
  if (run.reader_memo && memo === run.reader_memo) panels.evidence.append(detail("Canonical scenario reasoning", [scenarioRationale(run, false)]));
  if (endpoints.length) panels.valuation.append(scenarioRationale(run));
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
    metric.append(value, element("span", "meta", periodLabel));
    const current = currentCalculation(calc);
    const explanation = run.analysis && calculationPeriod(calc) ? "Dated saved inputs; the calculation basis states periods and adjustments." : current ? (number(output.value) === null ? "Latest period selected; final ratio unavailable." : "Latest matched " + calc.report_type.toUpperCase() + " inputs.") : "Historical or undated result; a matched current-period result is not available.";
    if (number(output.value) === null) metric.append(element("p", "basis unavailable", "See missing inputs in calculation details."));
    const basis = Object.entries(calc.inputs || {}).map(([name, input]) => name + " · " + economicPeriod(input) + ". " + text(input && input.basis));
    metric.append(detail("Calculation basis & periods", [element("p", "meta", calc.label || calc.id), element("p", "basis", explanation + (calc.current_period_reason ? " " + calc.current_period_reason : "")), element("p", "basis", text(calc.basis)), recordList(basis), referenceList([calc.id], run)]));
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
    for (const item of additional) guidance.append(detail(item.metric_label, [managementComparison(item, run)]));
    metricSection.append(guidance);
  }
  if (!metrics.children.length && !comparisons.length) metricSection.append(element("p", "basis", "No separate saved metrics or structured management comparisons are included."));
  panels.financials.append(metricSection);
  if (run.analysis) panels.evidence.append(detail("Independent analysis review", [renderAnalysisReview(run)]));
  const reportingDates = sources.map((source) => source.period && source.period.end).filter(Boolean).sort();
  const recency = element("section", "company-section current-data");
  recency.append(element("p", "basis", "Latest reporting period in saved sources: " + (reportingDates.pop() || "Unavailable") + ". Frozen analysis date: " + run.analysis_date + (run.analysis ? ". Saved run completed: " : ". Financial review: ") + text(run.reviewed_at).slice(0, 10) + ". This timestamp does not refresh the underlying data."));
  if ((run.current_data_limits || []).length) recency.append(detail("Current data limits", [recordList(run.current_data_limits)]));
  panels.evidence.append(recency);
  if ((run.material_inputs || []).length) panels.evidence.append(renderMaterialInputs(run.material_inputs, sources));
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
  if (boundReturn) benchmarkContent.push(savedLink("return-explanation", "How the conditional return was calculated"));
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
  panels.evidence.append(working);
  if (sameRun) for (const [index, details] of Array.from(view.querySelectorAll("details")).entries()) {
    const key = details.id || index;
    if (detailStates.has(key)) details.open = detailStates.get(key);
  }
  loadedRunId = run.id;
  view.hidden = false;
  if (!sameRun && typeof location !== "undefined" && location.hash) revealSavedHash();
}
function revealSavedHash() {
  let id;
  try { id = decodeURIComponent(location.hash.slice(1)); } catch (error) { return; }
  const target = $(id);
  if (target && $("company-view").contains(target)) openSavedTarget(id);
  else if ($("panel-company") && /^(company-|analysis-|reader-|scenario-|source-|calculation-|input-|record-|legacy-report)/.test(id)) selectTab("company");
}
function normalizeQuote(candidate, run) {
  const reportCurrency = (run.price || {}).currency;
  const date = candidate && typeof candidate.date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(candidate.date) ? new Date(candidate.date + "T00:00:00Z") : null;
  const value = normalizedPrice(candidate);
  if (!candidate || candidate.instrument_id !== run.company.instrument_id || !/^[A-Z]{3}$/.test(candidate.currency) || (reportCurrency && candidate.currency !== reportCurrency) || candidate.unit !== "currency/share" || candidate.kind !== "daily_close" || value === null || value <= 0 || !date || !Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== candidate.date) return null;
  return {...candidate, normalized_value: value};
}
async function loadMarketPrice(run, request) {
  let quote = null;
  if (Number.isInteger(run.company.instrument_id) && run.company.instrument_id > 0) {
    try {
      const response = await getJSON("/api/market-price/" + encodeURIComponent(run.company.instrument_id));
      quote = normalizeQuote(response.quote, run);
    } catch (error) { /* The report remains available without a separate market quote. */ }
  }
  if (request !== runRequest || loadedRunId !== run.id) return;
  const price = $("latest-market-price");
  price.replaceChildren();
  $("latest-market-price-date").textContent = quote ? "Close · " + quote.date : "No compatible stored quote";
  if (!quote) { price.append(document.createTextNode("Unavailable")); return; }
  price.append(headlinePrice(quote, quote.normalized_value));
  $("latest-market-price-evidence").replaceChildren(element("p", "detail-label", "Latest market price"), element("p", "basis", "Daily close from the configured evidence store. Adjustment basis is unverified."), element("pre", "", text(quote)));
  if (scenarioEndpoints(run).length) $("company-valuation-charts").replaceChildren(endpointChart(run, quote));
}
async function loadRun(id) {
  const request = ++runRequest;
  $("company-error").hidden = true;
  $("company-view").hidden = true;
  if (!id) {
    loadedRunId = null;
    $("company-status").hidden = true;
    return;
  }
  const indexed = indexedRuns.find(run => run.id === id);
  if (indexed) selectedVersions.set(String(indexed.company.instrument_id), id);
  $("company-status").hidden = false;
  $("company-status").textContent = "Loading saved analysis…";
  try {
    const run = await getJSON("/api/runs/" + encodeURIComponent(id));
    if (request !== runRequest) return;
    if (run.id !== id || (indexed && run.company.instrument_id !== indexed.company.instrument_id)) throw new Error("Saved identity does not match selection");
    renderCompany(run);
    $("company-status").classList.remove("stale");
    $("company-status").textContent = "";
    $("company-status").hidden = true;
    await loadMarketPrice(run, request);
  } catch (error) {
    if (request !== runRequest) return;
    $("company-view").hidden = true;
    $("company-error").hidden = false;
    $("company-error").textContent = "Could not load this saved analysis. Check the configured saved-view file and refresh.";
    $("company-status").classList.add("stale");
    $("company-status").hidden = false;
    $("company-status").textContent = "Saved analysis unavailable";
  }
}
function savedRunLabel(run, runs = []) {
  const label = (run.analysis_kind === "structured" ? "Structured · completed " : "Financial review · ") + text(run.reviewed_at).slice(0, 10);
  const matches = runs.filter(other => other.company.instrument_id === run.company.instrument_id && savedRunLabel(other) === label);
  if (matches.length < 2) return label;
  const asOf = " · Cutoff " + text(run.analysis_date);
  return label + asOf + (matches.some(other => other.id !== run.id && other.analysis_date === run.analysis_date) ? " · " + run.id : "");
}
function newestMemo(a, b) {
  const completion = run => Number.isFinite(Date.parse(run.reviewed_at)) ? Date.parse(run.reviewed_at) : 0;
  return String(b.analysis_date || "").localeCompare(String(a.analysis_date || "")) || completion(b) - completion(a) || a.id.localeCompare(b.id);
}
function showCompanyEmpty(company = null) {
  const empty = $("company-empty");
  empty.replaceChildren(element("h2", "", company ? displayName(company.name) : "No companies configured"),
    element("p", "", company ? "No saved analysis yet." : "Add a captured company catalogue or saved memo to the workbench."));
  if (company && company.captured_at) empty.append(element("p", "basis", "Börsdata snapshot · " + company.captured_at.slice(0, 10)));
  empty.hidden = false;
}
function showCompany(id) {
  const versions = indexedRuns.filter(run => String(run.company.instrument_id) === id).sort(newestMemo);
  $("run-select").replaceChildren();
  for (const run of versions) {
    const option = element("option", "", savedRunLabel(run, versions));
    option.value = run.id;
    option.title = "Analysis cutoff: " + text(run.analysis_date) + (run.analysis_kind === "structured" ? " · Analysis completed: " : " · Financial review: ") + text(run.reviewed_at);
    $("run-select").append(option);
  }
  const previous = selectedVersions.get(id);
  const selected = versions.some(run => run.id === previous) ? previous : (versions[0] || {}).id || "";
  $("run-select").value = selected;
  $("run-select").disabled = !versions.length;
  $("company-empty").hidden = versions.length > 0;
  if (!versions.length) {
    $("run-select").append(element("option", "", "No saved memo"));
    showCompanyEmpty(indexedCompanies.get(String(id)));
  }
  return loadRun(selected);
}
async function loadRuns(force = false) {
  if (runsLoaded && !force) return;
  const request = ++indexRequest;
  ++runRequest;
  $("company-view").hidden = true;
  $("company-error").hidden = true;
  $("company-empty").hidden = true;
  $("company-select").disabled = true;
  $("run-select").disabled = true;
  $("company-status").hidden = false;
  $("company-status").textContent = "Loading companies and memo versions…";
  try {
    const data = await getJSON("/api/runs");
    if (request !== indexRequest) return;
    if (!Array.isArray(data.runs)) throw new Error("Invalid saved index");
    if (data.companies !== undefined && !Array.isArray(data.companies)) throw new Error("Invalid company catalogue");
    const selected = $("company-select").value;
    indexedRuns = data.runs.filter(run => run.company && Number.isInteger(run.company.instrument_id) && run.company.instrument_id > 0);
    const companies = new Map();
    for (const company of data.companies || []) {
      if (!company || !Number.isInteger(company.instrument_id) || company.instrument_id <= 0 || typeof company.name !== "string" || !company.name.trim()) throw new Error("Invalid captured company");
      companies.set(String(company.instrument_id), company);
    }
    for (const run of [...indexedRuns].sort(newestMemo)) {
      const id = String(run.company.instrument_id);
      if (!companies.has(id)) companies.set(id, run.company);
    }
    indexedCompanies = companies;
    $("company-select").replaceChildren();
    for (const [id, company] of [...companies].sort((a, b) => displayName(a[1].name).localeCompare(displayName(b[1].name)) || Number(a[0]) - Number(b[0]))) {
      const hasMemo = indexedRuns.some(run => String(run.company.instrument_id) === id);
      const option = element("option", "", displayName(company.name) + (company.ticker ? " · " + company.ticker : "") + " · #" + id + (hasMemo ? "" : " · No memo"));
      option.value = id;
      $("company-select").append(option);
    }
    runsLoaded = true;
    $("company-status").classList.remove("stale");
    $("company-empty").hidden = companies.size > 0;
    $("company-select").disabled = !companies.size;
    if (!companies.size) {
      $("company-select").append(element("option", "", "No companies configured"));
      $("run-select").replaceChildren(element("option", "", "No saved memos"));
      $("company-status").hidden = true;
      showCompanyEmpty();
    } else {
      const newest = [...indexedRuns].sort(newestMemo)[0];
      $("company-select").value = companies.has(selected) ? selected : newest ? String(newest.company.instrument_id) : companies.keys().next().value;
      await showCompany($("company-select").value);
    }
  } catch (error) {
    if (request !== indexRequest) return;
    runsLoaded = false;
    $("company-error").hidden = false;
    $("company-error").textContent = "Could not read the saved-analysis index. Check the local server and refresh.";
    $("company-status").classList.add("stale");
    $("company-status").hidden = false;
    $("company-status").textContent = "Saved-analysis index unavailable";
  }
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
window.addEventListener("hashchange", () => {
  revealTaskHash();
  revealSavedHash();
});
$("company-select").addEventListener("change", () => showCompany($("company-select").value));
$("run-select").addEventListener("change", () => loadRun($("run-select").value));
$("refresh").addEventListener("click", () => { refresh(); if (runsLoaded || !$("panel-company").hidden) loadRuns(true); });
refresh();
revealSavedHash();
setInterval(refresh, 10000);
