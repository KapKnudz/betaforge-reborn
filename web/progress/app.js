"use strict";

const $ = (id) => document.getElementById(id);
const labels = { pending: "Pending", in_progress: "In progress", blocked: "Blocked", done: "Done" };
const publicDocs = new Set([
  "AGENTS.md", "CONTRIBUTING.md", "README.md", "docs/architecture.md", "work/README.md",
  "docs/analysis-policy.md", "docs/calculations.md", "docs/company-workflow.md", "docs/research/system-readiness-review.md",
  "docs/research/borsdata-retrieval-storage.md", "docs/codex-integration.md",
]);
let currentPlan = null;
let loading = false;
let lastSuccess = null;
let lastPlanText = null;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function status(value) {
  return element("span", "status " + value, labels[value]);
}

function documentReference(path, label) {
  if (!publicDocs.has(path)) return element("span", "unlinked", label);
  const link = element("a", "", label);
  link.href = "/docs/" + path;
  link.target = "_blank";
  link.rel = "noopener";
  return link;
}

function renderTasks(plan) {
  const list = $("task-list");
  const opened = new Set(Array.from(list.querySelectorAll("details[open]")).map((d) => d.dataset.task));
  list.replaceChildren();
  const filter = $("filter").value;
  const tasks = plan.tasks.filter((task) => filter === "all" || (filter === "done" ? task.status === "done" : task.status !== "done"));
  for (const task of tasks) {
    const card = element("article", "task");
    card.id = "task-" + task.id;
    const side = element("div", "task-side");
    side.append(element("p", "task-id", task.id), status(task.status));
    const milestone = plan.milestones.find((item) => item.id === task.milestone);
    side.append(element("p", "task-milestone", milestone.title));
    const body = element("div", "task-body");
    body.append(element("h3", "", task.title), element("p", "note", task.note));
    if (task.blocker) body.append(element("p", "blocker", "Blocked: " + task.blocker));
    const details = element("details");
    details.dataset.task = task.id;
    details.open = opened.has(task.id);
    details.append(element("summary", "", "Completion criteria and evidence"));
    const criteria = element("ul");
    for (const criterion of task.acceptance) criteria.append(element("li", "", criterion));
    details.append(criteria, element("p", "detail-label", "Evidence"));
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
  const counts = $("counts");
  counts.replaceChildren();
  for (const value of ["done", "in_progress", "pending", "blocked"]) {
    const count = element("div", "count");
    count.append(element("strong", "", String(plan.tasks.filter((task) => task.status === value).length)), element("span", "", labels[value]));
    counts.append(count);
  }
  const next = plan.tasks.find((task) => task.id === plan.next_task);
  $("next-title").textContent = next ? next.title : "Plan complete";
  $("next-note").textContent = next ? (next.blocker || next.note) : "All recorded tasks are done. Agree the next goal before adding more work.";
  $("next-link").hidden = !next;
  if (next) $("next-link").href = "#task-" + next.id;
  const roadmap = $("milestones");
  roadmap.replaceChildren();
  plan.milestones.forEach((milestone, index) => {
    const card = element("article", "milestone " + milestone.status);
    card.append(element("div", "milestone-number", String(index + 1).padStart(2, "0")), element("h3", "", milestone.title), element("p", "", milestone.summary), status(milestone.status));
    roadmap.append(card);
  });
  renderTasks(plan);
  $("session-summary").textContent = plan.session.summary;
  $("session-next").textContent = plan.session.next_step;
  const references = $("references");
  references.replaceChildren();
  for (const reference of plan.references) references.append(documentReference(reference.path, reference.label));
  $("updated").textContent = "Plan updated: " + plan.updated_at;
  $("dashboard").hidden = false;
}

async function refresh() {
  if (loading) return;
  loading = true;
  $("refresh").disabled = true;
  try {
    const response = await fetch("/api/plan", { cache: "no-store", signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error("Plan unavailable");
    const plan = await response.json();
    const planText = JSON.stringify(plan);
    if (planText !== lastPlanText) {
      render(plan);
      currentPlan = plan;
      lastPlanText = planText;
    }
    lastSuccess = new Date();
    $("error").hidden = true;
    $("connection").classList.remove("stale");
    $("connection").textContent = "Connected · last checked " + lastSuccess.toLocaleTimeString();
  } catch (error) {
    $("error").hidden = false;
    $("error").textContent = lastSuccess
      ? "Could not refresh. Showing the last successful plan from " + lastSuccess.toLocaleTimeString() + ". Check work/plan.json and the local server."
      : "Could not load the plan. Check work/plan.json and the local server, then refresh.";
    $("connection").classList.add("stale");
    $("connection").textContent = lastSuccess ? "Disconnected · displayed plan may be stale" : "Plan unavailable";
  } finally {
    loading = false;
    $("refresh").disabled = false;
  }
}

$("filter").addEventListener("change", () => { if (currentPlan) renderTasks(currentPlan); });
$("next-link").addEventListener("click", (event) => {
  if (!currentPlan || currentPlan.next_task === null) {
    event.preventDefault();
    return;
  }
  $("filter").value = "all";
  renderTasks(currentPlan);
  document.getElementById("task-" + currentPlan.next_task).querySelector("details").open = true;
});
$("refresh").addEventListener("click", refresh);
refresh();
setInterval(refresh, 10000);
