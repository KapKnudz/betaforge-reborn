"""Exercise Company navigation and saved financial/source semantics without a server."""
from pathlib import Path
import shutil
import subprocess
import unittest


HARNESS = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
class SavedNode {
  constructor(tag = "#text") { this.tagName = tag.toUpperCase(); this.children = []; this.attributes = {}; this.listeners = {}; this.className = ""; this.dataset = {}; this.classList = { add: (...names) => { this.className += " " + names.join(" "); }, remove: () => {} }; }
  set textContent(value) { this.content = String(value); this.children = []; }
  get textContent() { return (this.content || "") + this.children.map(node => node.textContent).join(""); }
  set value(value) { this.selectedValue = String(value); }
  get value() { return this.tagName === "SELECT" ? this.selectedValue ?? (this.children[0] || {}).value ?? "" : this.selectedValue ?? ""; }
  get firstElementChild() { return this.children[0]; }
  append(...nodes) { for (const node of nodes) { node.parentElement = this; this.children.push(node); } }
  insertBefore(node, before) { node.parentElement = this; this.children.splice(this.children.indexOf(before), 0, node); }
  replaceChildren(...nodes) { this.children = []; this.content = ""; this.selectedValue = undefined; this.append(...nodes); }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  querySelectorAll(selector) { return all(this).filter(node => selector === "details" ? node.tagName === "DETAILS" : false); }
  contains(target) { return this === target || all(this).includes(target); }
  scrollIntoView() { this.scrolled = true; }
  focus() { this.focused = true; }
}
const all = node => node.children.flatMap(child => [child, ...all(child)]);
const root = new SavedNode("main");
for (const id of ["panel-project", "panel-architecture", "panel-company", "tab-project", "tab-architecture", "tab-company", "company-status", "company-error", "company-empty", "company-select", "run-select"]) { const node = new SavedNode(id.endsWith("select") ? "select" : "div"); node.id = id; root.append(node); }
const view = new SavedNode("div"); view.id = "company-view";
const document = { getElementById: id => [root, ...all(root)].find(node => node.id === id), createElement: tag => new SavedNode(tag), createElementNS: (_, tag) => new SavedNode(tag), createTextNode: text => { const node = new SavedNode(); node.textContent = text; return node; } };
document.getElementById("panel-company").append(view);
const sandbox = { document, Node: SavedNode, URL, console };
vm.createContext(sandbox);
let source = fs.readFileSync("web/progress/app.js", "utf8");
source = source.slice(0, source.indexOf('for (const name of ["project", "architecture", "company"])'));
vm.runInContext(source, sandbox);
const $ = id => document.getElementById(id);
const panel = name => $("company-panel-" + name);
const disclosure = (name, from = view) => all(from).find(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === name);
const evaluate = code => vm.runInContext(code, sandbox);
'''

FIXTURE = r'''
const calculation = { id: "calc:value", label: "Saved valuation", formula: "valuation_case", version: "1", formula_text: "Saved formula", inputs: { ebit: { id: "input:ebit", value: "4", unit: "SEK", basis: "Reported EBIT" }, required_return: {value: "0.12", calculation_value: "0.12", unit: "dimensionless"}, years: {value: "3",calculation_value: "3",unit: "dimensionless"} }, outputs: { present_value: { value: "120", unit: "SEK/share" } }, options: {} };
const sectionIds = ["thesis", "drivers", "quality", "management", "valuation", "risks"];
const references = ["annual:p26", "calc:value#present_value", "input:ebit", "input:standalone", "unavailable:reference"];
const scenario = { id: "base", name: "Base", present_value: {value: "120", unit: "SEK/share"}, future_target: {value: "180", unit: "SEK/share"}, present_value_date: { value: "2026-11-01", precision: "day" }, target_date: { value: "2029", precision: "year" }, rationale: "Base rationale", assumption_rationale: "Saved EBIT assumption", valuation_calculation_id: "calc:value", weight_ref: "input:ebit", references, probability_rationale: "Conditional analyst judgment" };
const run = { id: "structured", company: {name: "Sample"}, analysis_date: "2026-11-01", reviewed_at: "2026-11-04", method: "Saved", conclusion: "Legacy summary", scenarios: [{name: "Base",value: "120",unit: "SEK/share",basis: "Saved basis",calculation_ids: ["calc:value"]}], probability: {status: "proposed",weights: {base: "0.6"}}, calculations: [calculation], original_calculations: [{id: "calc:old",label: "Old calculation", inputs: []}], sources: [{id: "annual",title: "Annual report",url: "https://example.com/report.pdf",period: {}, pages: 40}], saved_records: [{id: "input:standalone", value: "2", scale: "1", unit: "percent", kind: "assumption", basis: "Saved standalone assumption"}], narrative: "# Full saved report\n\nOriginal narrative.", analysis: {summary: "Structured lead",validation_status: "syntax_and_identity_valid",review_status: "unreviewed",sections: sectionIds.map(id => ({id,title: id,paragraphs: [{kind: "fact",text: "<script>must remain text</script>" + (id === "thesis" ? "\n\n| Period | Reported EBIT |\n| --- | --- |\n| 2025 | 4 |\n| 2026 R12 | 5 |" : ""),references: id === "risks" ? references.slice(0, 3) : references}]})), scenarios: [scenario], management_comparisons: [{id: "utilization",metric_key: "utilization",metric_label: "Plant utilization",relationship: "related",statement_type: "driver",statement: "Utilization supports the operation",statement_date: "2026-10-01",target_period: "2027",basis: "Issuer utilization; not EBIT margin",actual: "Related metric",references: ["annual:p26"],actual_references: [],evidence: {report_id: "annual",page: 26,quote: "Original saved words"}}],probability_limits: "Weights are not calibrated"}};
run.calculations.push({id: "calc:margin",label: "Reported EBIT margin",basis: "Consolidated R12 reported earnings and matched revenue",formula: "ebit_margin",version: "1",formula_text: "EBIT / revenue",inputs: {ebit: {id: "input:dated-ebit", value: "10",unit: "SEK",kind: "flow",report_type: "r12",period_start: "2025-10-01",period_end: "2026-09-30",basis: "Reported EBIT; no adjustment"}},outputs: {margin_percent: {value: "10",unit: "percent"}}});
run.analysis.management_comparisons.push({id: "margin-guidance",metric_key: "ebit_margin",metric_label: "Reported EBIT margin",relationship: "not_stated",statement_type: "not_stated",statement: "No direct EBIT margin guidance was found in the saved reading",statement_date: null,target_period: null,basis: "Issuer statement review",actual: "Reported EBIT margin",references: [],actual_references: [],evidence: null});
run.analysis.management_comparisons.push({id: "roce-target",metric_key: "operating_roic",metric_label: "Issuer ROCE target",relationship: "related",statement_type: "target",statement: "Issuer targets ROCE above its hurdle",statement_date: "2026-10-01",target_period: "2027",basis: "ROCE uses the issuer capital definition; this is not operating ROIC",actual: "Related capital measure",references: [],actual_references: [],evidence: null});
run.price = {id: "obs:price", value: "100", unit: "currency/share", currency: "SEK", scale: "1", date: "2026-10-30", basis: "Closing price from preserved API evidence", source_id: "src_price"};
run.company.instrument_id = 1;
run.benchmark = {candidate_annualized_return_percent: "12.5", interpretation: "Conditional return estimate", limits: ["Scenario assumptions may fail"]};
run.original_calculations.push({id: "calc:irr", operation: "financial_formula", formula: "expected_cashflow_irr", input_ids: {price: "obs:price"}, inputs: [{...run.price, field: "price"}], outputs: {irr_percent: {value: "12.5", unit: "percent"}}});
run.current_data_limits = ["Synthetic R12 cash conversion remains incomplete"];
run.material_inputs = [{label: "Working capital",selected: {id: "input:working",value: "20",scale: "1000000",unit: "currency",currency: "SEK",kind: "stock",period_end: "2026-09-30",basis: "Operating working capital; cash and financing excluded",report_id: "annual",evidence: [{report_id: "annual",page: 26,quote: "Preserved synthetic working capital definition"}]},definition_status: "verified",reconciliation_status: "matched",definition: "Operating receivables plus inventories less operating payables",selection_reason: "Retain the saved operating definition",valuation_uses: ["Inspect reinvestment support"],candidates: [],limitations: ["Quarterly composition remains incomplete"]}];
sandbox.run = run;
'''


class ProgressUITests(unittest.TestCase):
    def run_ui(self, script):
        result = subprocess.run([shutil.which("node"), "-e", HARNESS + FIXTURE + script], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is required for the buildless UI check")
    def test_explicit_return_selection_preserves_price_binding_and_explanation(self):
        self.run_ui(r'''
const original = run.original_calculations.find(calc => calc.id === "calc:irr");
const selected = {...original,id: "calc:adopted",outputs: {irr_percent: {value: "8.4",unit: "percent"}}};
run.original_calculations.push(selected);
run.benchmark.candidate_annualized_return_percent = "8.4";
evaluate("renderCompany(run)");
assert(panel("overview").textContent.includes("Report-price binding unavailable"));
run.benchmark.return_calculation_id = selected.id;
evaluate("renderCompany(run)");
assert(panel("overview").textContent.includes("Conditional annual return8.4%At report price"));
assert($("return-explanation").textContent.includes("Saved annual return8.4%"));
assert(all($("return-explanation")).some(node => node.href === "#calculation-calc:adopted"));
for (const id of [null, "calc:missing", "calc:old", original.id]) {
  run.benchmark.return_calculation_id = id;
  assert.equal(evaluate("returnUsesReportPrice(run)"), false);
}
run.benchmark.return_calculation_id = selected.id;
for (const [key,value] of [["id","obs:other"],["value","101"],["unit","currency"],["scale","10"],["currency","USD"],["source_id","src_other"],["date","2026-10-29"]]) {
  sandbox.changed = {...run,price: {...run.price,[key]:value}};
  assert.equal(evaluate("returnUsesReportPrice(changed)"), false, key);
}
''')

    @unittest.skipUnless(shutil.which("node"), "Node is required for the buildless UI check")
    def test_structured_and_legacy_saved_rendering(self):
        self.run_ui(r'''

evaluate("renderCompany(run)");
assert.equal(all(view).filter(node => node.className === "company-chapter").length, 4);
for (const name of ["business", "valuation", "financials", "evidence"]) assert(!panel(name).open);
assert(!all(view).some(node => node.attributes.role === "tab"));
assert(panel("overview").textContent.includes("Investment conclusionStructured lead"));
assert(panel("overview").textContent.includes("Conditional annual return12.5%At report price · 2026-10-30"));
assert(panel("overview").textContent.includes("Required return12%Report assumption"));
assert.equal(all(panel("overview")).find(node => node.className === "report-price").textContent, "100.00 SEK");
assert.equal(evaluate("rounded('172.2')"), "172.2");
assert.equal(evaluate("headlinePrice({value: '172.2',scale: '1',unit: 'currency/share',currency: 'SEK'}, 172.2)").textContent, "172.20 SEK");
assert(evaluate("headlinePrice({value: '12.5',scale: '10',unit: 'currency/share',currency: 'SEK'}, 125)").title.includes("12.5 · unit currency/share · scale 10"));
assert(!$("return-explanation").open);
assert($("return-explanation").textContent.includes("does not average scenario returns"));
assert($("return-explanation").textContent.includes("2026-10-30"));
assert(!disclosure("Report conclusion").open);
assert(disclosure("Price evidence").textContent.includes("src_price"));
assert($("company-scenarios").textContent.includes("Analyst-proposed weights"));
assert.equal($("company-scenarios").parentElement, panel("overview"));
for (const name of ["business", "valuation", "financials", "evidence"]) assert.equal(panel(name).parentElement, view);
assert(panel("business").textContent.includes("<script>must remain text</script>"));
assert(!all(view).some(node => node.tagName === "SCRIPT"));
assert.equal(evaluate("displayName('Sample (publ)')"), "Sample");
assert(panel("evidence").textContent.includes("Analysis completed: 2026-11-04"));
assert(panel("evidence").textContent.includes("Saved run completed: 2026-11-04"));
assert(!view.textContent.includes("Review recorded:"));
assert($("metric-ebit_margin").textContent.includes("No direct guidance stated for this measure."));
assert($("metric-ebit_margin").textContent.includes("Consolidated R12 reported earnings and matched revenue"));
assert($("metric-ebit_margin").textContent.includes("2026-09-30"));
assert($("management-roce-target").textContent.includes("Related management statement · target"));
assert($("management-roce-target").textContent.includes("this is not operating ROIC"));
assert(disclosure("Definition & source", $("management-utilization")).textContent.includes("Original saved words"));
assert(view.textContent.includes("2029 · year precision"));
assert(!view.textContent.includes("2029-01-01"));
assert(view.textContent.includes("No independent structured review is saved"));
assert(view.textContent.includes("Material values: meaning & selection"));
assert(view.textContent.includes("Operating receivables plus inventories less operating payables"));
assert(view.textContent.includes("20 MSEK"));
assert(view.textContent.includes("Preserved synthetic working capital definition"));
assert(disclosure("Current data limits").textContent.includes("Synthetic R12 cash conversion remains incomplete"));
assert(disclosure("Return & benchmark"));
assert(view.textContent.includes("reference retained; detail unavailable"));
assert(!disclosure("Original analysis").open);
const history = all($("reader-thesis")).find(node => node.className === "period-history");
assert(history && all(history).some(node => node.tagName === "SELECT"));
assert(history.textContent.includes("Exact saved values and period labels"));
assert(!history.textContent.includes("Historical"));
assert.deepEqual(Array.from(evaluate("tableCells('| Period | EBIT \\\\| adjusted | Revenue |')")), ["Period", "EBIT | adjusted", "Revenue"]);
const multiple = evaluate("readableReport('| Period | EBIT (SEK million) | Margin (%) |\\n| --- | --- | --- |\\n| 2025 | -2 | 3 |\\n| 2026 R12 | 5 | 4 |')");
const measureSelect = all(multiple).find(node => node.tagName === "SELECT");
assert.equal(measureSelect.children.length, 2);
measureSelect.value = "1"; measureSelect.listeners.change();
assert(all(multiple).find(node => node.tagName === "SVG").attributes["aria-label"].includes("Margin (%)"));
assert(!evaluate("readableReport('| Period | EBIT |\\n| --- | --- |\\n| 2025 | unavailable |\\n| 2026 | 5 |')").textContent.includes("Measure"));
for (const target of ["scenario-base", "source-annual", "calculation-calc:value", "input-input:ebit", "record-input:standalone", "company-return", "return-explanation"]) {
  const link = all(view).find(node => node.href === "#" + target);
  assert(link, target); let prevented = false;
  link.listeners.click({preventDefault() { prevented = true; }});
  assert(prevented && $(target).focused, target);
  for (let parent = $(target); parent; parent = parent.parentElement) if (parent.tagName === "DETAILS") assert(parent.open);
}
assert(all(view).some(node => node.href === "https://example.com/report.pdf#page=26"));
assert($("calculation-calc:old"));
assert(panel("evidence").open);
panel("evidence").open = false;
evaluate("renderCompany(run)");
assert.equal(panel("evidence").open, false);
const scaledCalculation = {...calculation,inputs: {forecast_ebit: {value: "2400",scale: "1000000",calculation_value: "2400000000",unit: "currency",currency: "SEK"},required_return: {value: "12",scale: "0.01",calculation_value: "0.12",unit: "dimensionless"},years: {value: "3",scale: "1",calculation_value: "3",unit: "dimensionless"}}};
sandbox.scaledRun = {...run,calculations: [scaledCalculation]};
assert(evaluate("scenarioAssumptions(scaledRun)").textContent.includes("2,400 SEK million"));
assert(evaluate("scenarioAssumptions(scaledRun)").textContent.includes("12%"));
assert(!evaluate("scenarioAssumptions(scaledRun)").textContent.includes("3×"));
delete scaledCalculation.inputs.required_return.calculation_value;
assert(!evaluate("scenarioAssumptions(scaledRun)").textContent.includes("12%"));
run.reader_memo = {schema_version: 1,edited_at: "2026-11-04",analysis_sha256: "hash",summary: "A short editorial conclusion.",sections: sectionIds.map(id => ({id,title: id,paragraphs: [{kind: "interpretation",text: "### Saved descriptive heading\n\nReader " + id,references: ["annual:p26"]}]})), scenarios: [{id: "base",rationale: "Reader base rationale",assumption_rationale: "Reader assumption",probability_rationale: "Reader weight caveat",references: ["annual:p26"]}]};
evaluate("renderCompany(run)");
assert(panel("overview").textContent.includes("A short editorial conclusion."));
assert(!panel("overview").textContent.includes("Reader edition · original analysis & review"));
assert(panel("business").textContent.includes("Reader drivers"));
assert(panel("business").textContent.includes("Saved descriptive heading"));
assert($("scenario-base").textContent.includes("Reader base rationale"));
for (const heading of ["Business outcome", "Valuation assumptions", "Why this weight"]) assert($("scenario-base").textContent.includes(heading));
assert($("canonical-scenario-base").textContent.includes("Base rationale"));
assert(panel("evidence").textContent.includes("not this editorial rewrite"));
assert(panel("evidence").textContent.includes("Original narrative."));
run.reader_memo.schema_version = 2;
evaluate("renderCompany(run)");
assert(panel("overview").textContent.includes("Structured lead"));
assert(!$("scenario-base").textContent.includes("Reader base rationale"));
delete run.reader_memo;
for (const price of [null, {...run.price, value: "90"}, {...run.price, id: "obs:other-price"}, {...run.price, source_id: "src_other"}]) {
  sandbox.variant = {...run, price}; evaluate("renderCompany(variant)");
  assert(panel("overview").textContent.includes("Report-price binding unavailable"));
  assert(!$("return-explanation"));
}
evaluate("renderCompany(run)");
run.analysis_review = {reviewer: "Independent reviewer", verdict: "revise", summary: "Challenge summary", findings: [{id: "finding-1", verdict: "revise",reasoning: "Missing issuer definition",missing_evidence: "Report definition",references: ["annual:p26"]}],disagreements: []};
evaluate("renderCompany(run)");
assert($("company-review").textContent.includes("Missing issuer definition"));
assert(disclosure("Run provenance").textContent.includes("Original submission review status: unreviewed"));
const ids = all(view).map(node => node.id).filter(Boolean);
assert.equal(ids.length, new Set(ids).size);
const charts = () => all($("company-valuation-charts")).filter(node => node.tagName === "SVG");
assert(charts()[0].attributes["aria-label"].includes("horizontal dot plot"));
assert(charts()[1].attributes["aria-label"].includes("vertical columns"));
assert(charts().every(node => node.attributes["aria-label"].includes("saved weight 60%")));
for (const chart of charts()) for (const link of all(chart).filter(node => node.tagName === "A")) {
  assert.equal(link.firstElementChild.attributes.class, "chart-hit-area");
  assert.equal(link.firstElementChild.attributes["pointer-events"], "all");
}
assert($("company-scenarios").textContent.includes("Separately paid dividends are excluded"));
assert(!all(charts()[0]).some(node => node.attributes.class === "price-line"));
const quote = {instrument_id: 1, value: "125", scale: "1", unit: "currency/share", currency: "SEK", date: "2026-11-04", source_id: "src_latest", kind: "daily_close", checked_at: "2026-11-04T12:30:00+00:00"};
(async () => {
  sandbox.getJSON = async url => url.startsWith("/api/market-price/") ? {quote} : run;
  await evaluate('loadRun("structured")');
  assert.equal($("latest-market-price").textContent, "125.00 SEK");
  assert.equal($("latest-market-price-date").textContent, "Close · 2026-11-04");
  assert($("latest-market-price-evidence").textContent.includes(quote.checked_at));
  assert(charts().every(chart => all(chart).some(node => node.attributes.class === "price-line")));
  assert.equal(all(charts()[0]).find(node => node.attributes.class === "price-line").attributes.x1, "430");
  assert.equal(all(charts()[1]).find(node => node.attributes.class === "price-line").attributes.y1, String(188 - 125 / 180 * 135));
  assert.equal(run.price.value, "100");
  assert(panel("overview").textContent.includes("Conditional annual return12.5%"));
  sandbox.getJSON = async url => url.startsWith("/api/market-price/") ? {quote: {...quote,value: "12.5",scale: "10"}} : run;
  await evaluate('loadRun("structured")');
  assert.equal($("latest-market-price").textContent, "125.00 SEK");
  for (const invalid of [null, {...quote, instrument_id: 2}, {...quote, currency: "USD"}, {...quote, currency: ""}, {...quote, date: "2026-02-30"}, {...quote, scale: "0"}, {...quote, scale: "-1"}, {...quote, scale: "Infinity"}]) {
    sandbox.getJSON = async url => url.startsWith("/api/market-price/") ? {quote: invalid} : run;
    await evaluate('loadRun("structured")');
    assert.equal($("latest-market-price").textContent, "Unavailable");
    assert(charts().every(chart => !all(chart).some(node => node.attributes.class === "price-line")));
    assert.equal(view.hidden, false);
  }
  sandbox.getJSON = async url => { if (url.startsWith("/api/market-price/")) throw Error("No quote store"); return run; };
  await evaluate('loadRun("structured")');
  assert.equal(view.hidden, false);
  assert.equal($("company-error").hidden, true);
  delete run.analysis; run.id = "legacy";
  run.scenarios[0].unit = "SEK/share today";
  run.narrative = "# Full report\n\nA preserved paragraph.\n\n| Metric | Value |\n| --- | --- |\n| EBIT | 4 |\n\n<script>still text</script>";
  evaluate("renderCompany(run)");
  assert($("legacy-report").textContent.includes("A preserved paragraph."));
  assert(all($("legacy-report")).some(node => node.tagName === "TABLE"));
  assert(!all($("legacy-report")).some(node => node.tagName === "SCRIPT"));
  assert(view.textContent.includes("Financial review: 2026-11-04"));
  assert(!view.textContent.includes("Analysis completed:"));
  assert(view.textContent.includes("120 SEK/share today"));
  assert(view.textContent.includes("Present values as of 2026-11-01"));
  assert.equal(run.scenarios[0].unit, "SEK/share today");
})().catch(error => { console.error(error); process.exitCode = 1; });
''')

    @unittest.skipUnless(shutil.which("node"), "Node is required for the buildless UI check")
    def test_captured_companies_without_memos_and_pending_requests(self):
        self.run_ui(r'''
const indexRun = (id, instrument) => ({id,company: {name: "Memo issuer " + instrument,instrument_id: instrument},analysis_kind: "structured",analysis_date: "2026-11-01",reviewed_at: "2026-11-04"});
const versions = [indexRun("a-only", 1), indexRun("outside-corpus", 3)];
const companies = [{instrument_id: 1,name: "Captured issuer A",ticker: "A",captured_at: "2026-11-03T17:00:00Z"}, {instrument_id: 2,name: "Captured issuer B (publ)",ticker: "B",captured_at: "2026-11-03T18:00:00Z"}];
const detail = item => ({...run,...item,analysis: {...run.analysis},price: {...run.price}});
const calls = [];
const server = async url => {
  calls.push(url);
  if (url === "/api/runs") return {runs: versions,companies};
  if (url.startsWith("/api/market-price/")) return {quote: null};
  return detail(versions.find(item => item.id === url.split("/").pop()));
};
const selectCompany = async id => { $("company-select").value = id; await evaluate('showCompany("' + id + '")'); };
(async () => {
  sandbox.getJSON = server;
  await evaluate("loadRuns()");
  assert.equal($("company-select").children.length, 3, "catalogue and saved companies form one instrument-based list");
  assert.equal($("company-select").value, "1", "default to available research");
  assert.equal($("company-select").children[0].textContent.includes("Captured issuer A"), true);
  assert($("company-select").children[1].textContent.includes("No memo"));
  const requestsBefore = calls.length;
  await selectCompany("2");
  assert.equal(calls.length, requestsBefore, "selecting an unanalyzed company requests no memo or quote");
  assert.equal(view.hidden, true);
  assert.equal($("company-empty").hidden, false);
  assert($("company-empty").textContent.includes("Captured issuer B"));
  assert(!$("company-empty").textContent.includes("(publ)"));
  assert($("company-empty").textContent.includes("No saved analysis yet."));
  assert($("company-empty").textContent.includes("2026-11-03"));
  assert.equal($("run-select").disabled, true);
  assert.equal($("company-status").hidden, true);
  assert.equal(evaluate("loadedRunId"), null);
  await evaluate("loadRuns(true)");
  assert.equal($("company-select").value, "2", "refresh preserves a company without a memo");
  await selectCompany("1");
  assert.equal(view.hidden, false);
  assert.equal($("company-empty").hidden, true);
  const pending = [];
  sandbox.getJSON = url => url.startsWith("/api/runs/") ? new Promise(resolve => pending.push(resolve)) : server(url);
  const oldMemo = evaluate('loadRun("a-only")');
  await selectCompany("2");
  pending[0](detail(versions[0])); await oldMemo;
  assert.equal(view.hidden, true, "an in-flight memo cannot replace the empty company");
  assert.equal(evaluate("loadedRunId"), null);
  const quotes = [];
  sandbox.getJSON = url => url.startsWith("/api/market-price/") ? new Promise(resolve => quotes.push(resolve)) : server(url);
  const oldQuote = selectCompany("1"); await new Promise(setImmediate);
  await selectCompany("2"); quotes[0]({quote: null}); await oldQuote;
  assert.equal(view.hidden, true, "an in-flight quote cannot reveal old company research");
  sandbox.getJSON = async () => ({runs: [],companies});
  await evaluate("loadRuns(true)");
  assert.equal($("company-select").disabled, false, "catalogue-only browsing works without any saved analysis");
  assert.equal($("company-select").children.length, 2);
  sandbox.getJSON = async () => ({runs: [],companies: []});
  await evaluate("loadRuns(true)");
  assert($("company-empty").textContent.includes("No companies configured"), "an empty index must clear the prior company identity");
})().catch(error => { console.error(error); process.exitCode = 1; });
''')

    @unittest.skipUnless(shutil.which("node"), "Node is required for the buildless UI check")
    def test_company_versions_and_request_races(self):
        self.run_ui(r'''
const indexRun = (id, instrument, cutoff, completed) => ({id,company: {name: "Synthetic Same Name (publ)",instrument_id: instrument},analysis_kind: "structured",analysis_date: cutoff,reviewed_at: completed});
const versions = [indexRun("a-old", 1, "2026-10-01", "2026-11-04T23:00:00Z"), indexRun("a-new", 1, "2026-11-01", "2026-11-04T20:00:00Z"), indexRun("a-revised", 1, "2026-11-01", "2026-11-04T21:00:00Z"), indexRun("b-only", 2, "2026-10-15", "2026-11-04T20:00:00Z")];
versions[1].company.name = "Synthetic Same Name";
const detailRun = item => ({...run,...item,analysis: {...run.analysis},price: {...run.price}});
const quote = instrument_id => ({instrument_id, value: instrument_id === 1 ? "111" : "222", scale: "1",unit: "currency/share", currency: "SEK", date: "2026-11-04",kind: "daily_close"});
const server = async url => {
  if (url === "/api/runs") return {runs: [...versions,indexRun("invalid", 0, "2026-11-01", "2026-11-04")]};
  if (url.startsWith("/api/market-price/")) return {quote: quote(Number(url.split("/").pop()))};
  return detailRun(versions.find(item => item.id === url.split("/").pop()));
};
sandbox.versions = versions;
assert(evaluate("savedRunLabel(versions[1], versions)").endsWith(" · Cutoff 2026-11-01 · a-new"));
assert(evaluate("savedRunLabel(versions[2], versions)").endsWith(" · Cutoff 2026-11-01 · a-revised"));
assert.equal(evaluate("savedRunLabel(versions[0], versions)"), "Structured · completed 2026-11-04 · Cutoff 2026-10-01", "name drift still disambiguates different cutoffs without an unnecessary ID");
assert.equal(evaluate("savedRunLabel(versions[3], versions)"), "Structured · completed 2026-11-04", "another instrument does not create a collision");
(async () => {
  sandbox.getJSON = server;
  await evaluate("loadRuns()");
  assert.equal($("company-select").children.length, 2, "same names must remain separate instruments");
  assert.equal($("company-select").value, "1");
  assert.equal($("run-select").children.length, 3);
  const labels = $("run-select").children.map(node => node.textContent);
  assert.equal(new Set(labels).size, 3, "final visible labels remain distinct despite company-name drift");
  assert(labels.every(label => !label.includes("Synthetic Same Name")));
  assert.equal($("run-select").value, "a-revised", "cutoff precedes completion, then latest completion wins");
  assert($("run-select").children.some(node => node.title.includes("Analysis cutoff:") && node.title.includes("Analysis completed:")));
  assert($("company-select").children[1].textContent.includes("#2"));
  assert(!$("company-select").children[1].textContent.includes("(publ)"));
  $("run-select").value = "a-old"; await evaluate('loadRun("a-old")');
  $("company-select").value = "2"; await evaluate('showCompany("2")');
  assert.equal($("run-select").children.length, 1);
  assert.equal($("run-select").value, "b-only");
  assert.equal($("latest-market-price").textContent, "222.00 SEK");
  $("company-select").value = "1"; await evaluate('showCompany("1")');
  assert.equal($("run-select").value, "a-old", "switch back retains an explicit choice");
  await evaluate("loadRuns(true)");
  assert.equal($("run-select").value, "a-old", "refresh retains a valid choice");
  const pendingIndexes = [];
  sandbox.getJSON = url => url === "/api/runs" ? new Promise(resolve => pendingIndexes.push(resolve)) : server(url);
  const oldIndex = evaluate("loadRuns(true)"), newIndex = evaluate("loadRuns(true)");
  assert.equal(view.hidden, true);
  pendingIndexes[1]({runs: [versions[3]]}); await newIndex;
  assert.equal($("company-select").value, "2");
  pendingIndexes[0]({runs: [versions[0]]}); await oldIndex;
  assert.equal($("company-select").value, "2", "stale index cannot replace a newer index");
  assert.equal($("run-select").value, "b-only");
  const pendingDetails = [];
  sandbox.getJSON = url => url.startsWith("/api/runs/") ? new Promise(resolve => pendingDetails.push(resolve)) : server(url);
  const oldDetail = evaluate('loadRun("a-new")'), newDetail = evaluate('loadRun("b-only")');
  assert.equal(view.hidden, true);
  pendingDetails[1](detailRun(versions[3])); await newDetail;
  pendingDetails[0](detailRun(versions[1])); await oldDetail;
  assert.equal(evaluate("loadedRunId"), "b-only", "stale detail cannot replace the selected memo");
  assert.equal($("latest-market-price").textContent, "222.00 SEK");
  const pendingQuotes = [];
  sandbox.getJSON = url => url.startsWith("/api/market-price/") ? new Promise(resolve => pendingQuotes.push(resolve)) : server(url);
  const oldQuote = evaluate('loadRun("a-new")'); await new Promise(setImmediate);
  const newQuote = evaluate('loadRun("b-only")'); await new Promise(setImmediate);
  pendingQuotes[1]({quote: quote(2)}); await newQuote;
  pendingQuotes[0]({quote: quote(1)}); await oldQuote;
  assert.equal($("latest-market-price").textContent, "222.00 SEK", "stale quote cannot mislabel another company");
  sandbox.getJSON = async url => url.startsWith("/api/runs/") ? detailRun(versions[0]) : server(url);
  await evaluate('loadRun("b-only")');
  assert.equal(view.hidden, true, "mismatched detail identity fails closed");
  assert.equal($("company-error").hidden, false);
  sandbox.getJSON = async () => { throw Error("Index unavailable"); };
  await evaluate("loadRuns(true)");
  assert.equal(view.hidden, true);
  assert.equal($("company-status").textContent, "Saved-analysis index unavailable");
  assert.equal($("company-select").disabled, true);
  sandbox.getJSON = async () => ({runs: []});
  await evaluate("loadRuns(true)");
  assert.equal(view.hidden, true);
  assert.equal($("company-empty").hidden, false);
  assert.equal($("company-select").disabled, true);
  assert.equal($("run-select").disabled, true);
  assert.equal($("company-error").hidden, true);
})().catch(error => { console.error(error); process.exitCode = 1; });
''')
