"""Exercise saved UI semantics without a server; browser layout has separate QA."""
from pathlib import Path
import shutil
import subprocess
import unittest


class ProgressUITests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required for the buildless UI check")
    def test_structured_and_legacy_saved_rendering(self):
        script = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
class SavedNode {
  constructor(tag = "#text") { this.tagName = tag.toUpperCase(); this.children = []; this.attributes = {}; this.listeners = {}; this.className = ""; this.dataset = {}; this.classList = { add: (...names) => { this.className += " " + names.join(" "); }, remove: () => {} }; }
  set textContent(value) { this.content = String(value); this.children = []; }
  get textContent() { return (this.content || "") + this.children.map(node => node.textContent).join(""); }
  get firstElementChild() { return this.children[0]; }
  append(...nodes) { for (const node of nodes) { node.parentElement = this; this.children.push(node); } }
  replaceChildren(...nodes) { this.children = []; this.content = ""; this.append(...nodes); }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  querySelectorAll(selector) { return all(this).filter(node => selector === "details" ? node.tagName === "DETAILS" : selector === "details[open] > summary" ? node.tagName === "SUMMARY" && node.parentElement.tagName === "DETAILS" && node.parentElement.open : false); }
  scrollIntoView() { this.scrolled = true; }
  focus() { this.focused = true; }
}
const all = node => node.children.flatMap(child => [child, ...all(child)]);
const root = new SavedNode("main");
const view = new SavedNode("div"); view.id = "company-view"; root.append(view);
const document = { getElementById: id => [root, ...all(root)].find(node => node.id === id), createElement: tag => new SavedNode(tag), createElementNS: (_, tag) => new SavedNode(tag), createTextNode: text => { const node = new SavedNode(); node.textContent = text; return node; } };
const sandbox = { document, Node: SavedNode, URL, console };
vm.createContext(sandbox);
let source = fs.readFileSync("web/progress/app.js", "utf8");
source = source.slice(0, source.indexOf('for (const name of ["project", "architecture", "company"])'));
vm.runInContext(source, sandbox);
const calculation = { id: "calc:value", label: "Saved valuation", formula: "valuation_case", version: "1", formula_text: "Saved formula", inputs: { ebit: { id: "input:ebit", value: "4", unit: "SEK", basis: "Reported EBIT" } }, outputs: { present_value: { value: "120", unit: "SEK/share" } }, options: {} };
const sectionIds = ["thesis", "drivers", "quality", "management", "valuation", "risks"];
const references = ["annual:p26", "calc:value#present_value", "input:ebit", "input:standalone", "unavailable:reference"];
const scenario = { id: "base", name: "Base", present_value: {value: "120", unit: "SEK/share"}, future_target: {value: "180", unit: "SEK/share"}, present_value_date: { value: "2026-11-01", precision: "day" }, target_date: { value: "2029", precision: "year" }, rationale: "Base rationale", assumption_rationale: "Saved EBIT assumption", valuation_calculation_id: "calc:value", weight_ref: "input:ebit", references, probability_rationale: "Conditional analyst judgment" };
const run = { id: "structured", company: {name: "Sample"}, analysis_date: "2026-11-01", reviewed_at: "2026-11-04", method: "Saved", conclusion: "Legacy summary", scenarios: [{name: "Base",value: "120",unit: "SEK/share",basis: "Saved basis",calculation_ids: ["calc:value"]}], probability: {status: "proposed",weights: {base: "0.6"}}, calculations: [calculation], original_calculations: [{id: "calc:old",label: "Old calculation", inputs: []}], sources: [{id: "annual",title: "Annual report",url: "https://example.com/report.pdf",period: {}, pages: 40}], saved_records: [{id: "input:standalone", value: "2", scale: "1", unit: "percent", kind: "assumption", basis: "Saved standalone assumption"}], narrative: "# Full saved report\n\nOriginal narrative.", analysis: {summary: "Structured lead",validation_status: "syntax_and_identity_valid",review_status: "unreviewed",sections: sectionIds.map(id => ({id,title: id,paragraphs: [{kind: "fact",text: "<script>must remain text</script>" + (id === "thesis" ? "\n\n| Period | Reported EBIT |\n| --- | --- |\n| 2025 | 4 |\n| 2026 R12 | 5 |" : ""),references: id === "risks" ? references.slice(0, 3) : references}]})), scenarios: [scenario], management_comparisons: [{id: "utilization",metric_key: "utilization",metric_label: "Plant utilization",relationship: "related",statement_type: "driver",statement: "Utilization supports the operation",statement_date: "2026-10-01",target_period: "2027",basis: "Issuer utilization; not EBIT margin",actual: "Related metric",references: ["annual:p26"],actual_references: [],evidence: {report_id: "annual",page: 26,quote: "Original saved words"}}],probability_limits: "Weights are not calibrated"}};
run.calculations.push({id: "calc:margin",label: "Reported EBIT margin",basis: "Consolidated R12 reported earnings and matched revenue",formula: "ebit_margin",version: "1",formula_text: "EBIT / revenue",inputs: {ebit: {id: "input:dated-ebit", value: "10",unit: "SEK",kind: "flow",report_type: "r12",period_start: "2025-10-01",period_end: "2026-09-30",basis: "Reported EBIT; no adjustment"}},outputs: {margin_percent: {value: "10",unit: "percent"}}});
run.analysis.management_comparisons.push({id: "margin-guidance",metric_key: "ebit_margin",metric_label: "Reported EBIT margin",relationship: "not_stated",statement_type: "not_stated",statement: "No direct EBIT margin guidance was found in the saved reading",statement_date: null,target_period: null,basis: "Issuer statement review",actual: "Reported EBIT margin",references: [],actual_references: [],evidence: null});
run.analysis.management_comparisons.push({id: "roce-target",metric_key: "operating_roic",metric_label: "Issuer ROCE target",relationship: "related",statement_type: "target",statement: "Issuer targets ROCE above its hurdle",statement_date: "2026-10-01",target_period: "2027",basis: "ROCE uses the issuer capital definition; this is not operating ROIC",actual: "Related capital measure",references: [],actual_references: [],evidence: null});
sandbox.run = run;
assert(vm.runInContext('savedRunLabel({...run, analysis_kind: "structured"})', sandbox).includes("analysis completed 2026-11-04"));
assert(!vm.runInContext('savedRunLabel({...run, analysis_kind: "structured"})', sandbox).includes("review"));
assert(vm.runInContext('savedRunLabel({...run, analysis_kind: "legacy"})', sandbox).includes("saved financial review 2026-11-04"));
vm.runInContext("renderCompany(run)", sandbox);
assert(view.textContent.includes("Structured lead"));
const header = () => all(view).find(node => node.className === "company-header");
assert(header().textContent.includes("Independent challenge: pending"));
assert(!header().textContent.includes("unreviewed"));
assert(all(view).some(node => node.tagName === "TEXT" && node.textContent === "Base · 60%"));
assert(all(view).filter(node => node.tagName === "SVG" && node.attributes.class === "chart endpoint-chart").every(node => node.attributes["aria-label"].includes("saved weight 60%")));
assert(view.textContent.includes("Analysis completed: 2026-11-04"));
assert(view.textContent.includes("Saved run completed: 2026-11-04"));
assert(!view.textContent.includes("Saved financial review:"));
assert(!view.textContent.includes("Review recorded:"));
assert(document.getElementById("metric-ebit_margin").textContent.includes("No direct guidance stated"));
assert(!document.getElementById("metric-ebit_margin").textContent.includes("Plant utilization"));
assert(view.textContent.includes("2029 · year precision"));
assert(!view.textContent.includes("2029-01-01"));
assert(view.textContent.includes("Saved weight: 60%"));
assert(view.textContent.includes("Related management statement · target"));
assert(document.getElementById("management-roce-target").textContent.includes("ROCE uses the issuer capital definition"));
assert(!document.getElementById("management-roce-target").textContent.includes("Related management driver"));
const managementSource = all(document.getElementById("management-utilization")).find(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "Sources & management quotation");
assert(managementSource && !managementSource.open);
assert(managementSource.textContent.includes("Original saved words"));
const datedMetric = document.getElementById("metric-ebit_margin");
assert(datedMetric.textContent.includes("Dated saved inputs; the calculation basis states periods and adjustments."));
assert(datedMetric.textContent.includes("Consolidated R12 reported earnings and matched revenue"));
assert(datedMetric.textContent.includes("2026-09-30"));
assert(datedMetric.textContent.includes("Reported EBIT; no adjustment"));
assert(!datedMetric.textContent.includes("Historical or undated result"));
assert(!datedMetric.textContent.includes("Latest matched"));
assert(view.textContent.includes("No independent structured review is saved"));
assert(view.textContent.includes("reference retained; detail unavailable"));
assert(!all(view).some(node => node.tagName === "SCRIPT"));
for (const id of sectionIds) {
  const section = document.getElementById("analysis-" + id);
  assert(section && section.textContent.includes("<script>must remain text</script>"));
  for (let parent = section.parentElement; parent; parent = parent.parentElement) assert.notEqual(parent.tagName, "DETAILS");
}
const thesis = document.getElementById("analysis-thesis");
const structuredTable = all(thesis).find(node => node.tagName === "TABLE");
assert(structuredTable && structuredTable.textContent.includes("2026 R12"));
assert(!all(thesis).some(node => node.tagName === "P" && node.textContent.includes("| Period |")));
for (let parent = structuredTable.parentElement; parent; parent = parent.parentElement) assert.notEqual(parent.tagName, "DETAILS");
const referenceDisclosure = all(thesis).find(node => node.tagName === "DETAILS");
assert(referenceDisclosure && referenceDisclosure.firstElementChild.textContent === "Sources & calculations (5)");
assert(!referenceDisclosure.open);
assert(!all(document.getElementById("analysis-risks")).some(node => node.tagName === "DETAILS"));
const links = all(view).filter(node => node.tagName === "A");
for (const target of ["scenario-base", "source-annual", "calculation-calc:value", "input-input:ebit", "record-input:standalone"]) {
  const link = links.find(node => node.href === "#" + target);
  assert(link, target);
  let prevented = false;
  link.listeners.click({preventDefault: () => { prevented = true; }});
  assert(prevented && document.getElementById(target).focused, target);
  for (let parent = document.getElementById(target).parentElement; parent; parent = parent.parentElement) if (parent.tagName === "DETAILS") assert(parent.open);
}
assert(links.some(node => node.href === "https://example.com/report.pdf#page=26"));
assert(document.getElementById("calculation-calc:old"));
const chartBars = all(view).filter(node => node.tagName === "RECT" && node.attributes.class && node.attributes.class.includes("scenario-bar"));
assert.equal(chartBars.length, 2);
assert.equal(Number(chartBars[0].attributes.width), 312);
assert.equal(Number(chartBars[1].attributes.width), 468);
run.analysis_review = {reviewer: "Independent reviewer", verdict: "revise", summary: "Challenge summary", findings: [{id: "finding-1", verdict: "revise",reasoning: "Missing issuer definition",missing_evidence: "Report definition",references: ["annual:p26"]}],disagreements: []};
vm.runInContext("renderCompany(run)", sandbox);
assert(header().textContent.includes("Independent challenge: changes requested"));
assert(!header().textContent.includes("unreviewed"));
const originalStatus = all(view).find(node => node.tagName === "P" && node.textContent === "Original submission review status: unreviewed");
assert(originalStatus && originalStatus.parentElement.tagName === "DETAILS");
assert(document.getElementById("company-review").textContent.includes("Missing issuer definition"));
run.analysis_review.verdict = "accept";
run.analysis.scenarios[0].name = "A very long base scenario name retained without crowding the endpoint label";
vm.runInContext("renderCompany(run)", sandbox);
assert(header().textContent.includes("Independent challenge: accepted"));
assert(document.getElementById("scenario-base").textContent.includes(run.analysis.scenarios[0].name));
assert(all(view).filter(node => node.tagName === "SVG" && node.attributes.class === "chart endpoint-chart").every(node => node.attributes["aria-label"].includes(run.analysis.scenarios[0].name)));
assert(!all(view).some(node => node.tagName === "TEXT" && node.textContent.includes("A very long base scenario")));
assert.equal(run.analysis.review_status, "unreviewed");
const missingWeights = vm.runInContext("endpointChart({...run, probability: {weights: {}}})", sandbox);
assert(missingWeights.textContent.includes("Base · weight unavailable"));
const zeroWeight = vm.runInContext("endpointChart({...run, probability: {weights: {base: '0'}}})", sandbox);
assert(zeroWeight.textContent.includes("Base · 0%"));
const ids = all(view).map(node => node.id).filter(Boolean);
assert.equal(ids.length, new Set(ids).size);
delete run.analysis;
run.id = "legacy";
run.narrative = "# Full report\n\nA preserved paragraph.\n\n| Metric | Value |\n| --- | --- |\n| EBIT | 4 |\n\n<script>still text</script>";
vm.runInContext("renderCompany(run)", sandbox);
const legacy = document.getElementById("legacy-report");
assert(legacy.textContent.includes("A preserved paragraph."));
assert(all(legacy).some(node => node.tagName === "H4" && node.textContent === "Full report"));
assert(all(legacy).some(node => node.tagName === "TABLE"));
assert(!all(legacy).some(node => node.tagName === "SCRIPT"));
assert(view.textContent.includes("Saved present values only"));
assert(document.getElementById("metric-ebit_margin").textContent.includes("Historical or undated result; a matched current-period result is not available."));
assert(view.textContent.includes("Saved financial review: 2026-11-04"));
assert(!view.textContent.includes("Analysis completed:"));
assert(!view.textContent.includes("Saved run completed:"));
assert(!view.textContent.includes("Base rationale"));
'''
        result = subprocess.run([shutil.which("node"), "-e", script], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
