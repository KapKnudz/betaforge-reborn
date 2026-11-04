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
  contains(target) { return this === target || all(this).includes(target); }
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
sandbox.run = run;
assert.equal(vm.runInContext('savedRunLabel({...run, analysis_kind: "structured"})', sandbox), "Sample · Structured · 2026-11-04");
assert.equal(vm.runInContext('savedRunLabel({...run, analysis_kind: "legacy"})', sandbox), "Sample · Financial review · 2026-11-04");
sandbox.versions = [run, {...run, id: "older", analysis_date: "2026-10-01"}];
assert.equal(vm.runInContext('savedRunLabel(versions[0], versions)', sandbox), "Sample · Financial review · 2026-11-04 · As of 2026-11-01");
assert.equal(vm.runInContext('savedRunLabel(versions[1], versions)', sandbox), "Sample · Financial review · 2026-11-04 · As of 2026-10-01");
sandbox.versions = [run, {...run, id: "revised"}];
assert.equal(vm.runInContext('savedRunLabel(versions[0], versions)', sandbox), "Sample · Financial review · 2026-11-04 · As of 2026-11-01 · structured");
assert.equal(vm.runInContext('savedRunLabel(versions[1], versions)', sandbox), "Sample · Financial review · 2026-11-04 · As of 2026-11-01 · revised");
vm.runInContext("renderCompany(run)", sandbox);
assert(view.textContent.includes("Structured lead"));
const header = () => all(view).find(node => node.className === "company-header");
const conclusion = all(view).find(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "Report conclusion");
assert(conclusion && !conclusion.open && conclusion.textContent.includes("Structured lead"));
assert(!header().children.some(node => node.tagName === "P" && node.textContent.includes("Structured lead")));
assert(header().textContent.includes("Estimated annual return · at report price: 12.5% Conditional · return assumptions"));
assert(!header().textContent.includes("Original analysis challenge"));
assert(!header().textContent.includes("unreviewed"));
assert(!view.textContent.includes("READ ONLY"));
const marketPrice = all(view).find(node => node.className === "basis market-price" && node.textContent.startsWith("Report price:"));
assert.equal(marketPrice.textContent, "Report price: 100 SEK/share · 2026-10-30");
assert(!marketPrice.textContent.includes(run.price.basis));
const priceEvidence = all(view).find(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "Price evidence");
assert(priceEvidence && !priceEvidence.open);
assert(priceEvidence.textContent.includes(run.price.basis));
assert(priceEvidence.textContent.includes("src_price"));
assert(priceEvidence.textContent.includes('"scale": "1"'));
assert(header().textContent.includes("Analysis date: 2026-11-01"));
const panel = name => document.getElementById("company-panel-" + name);
const tab = name => document.getElementById("company-tab-" + name);
assert.equal(panel("overview").hidden, false);
for (const name of ["business", "valuation", "financials", "evidence"]) assert.equal(panel(name).hidden, true);
assert.equal(tab("overview").attributes["aria-selected"], "true");
assert.equal(tab("overview").attributes["aria-controls"], panel("overview").id);
assert.equal(panel("overview").attributes["aria-labelledby"], tab("overview").id);
assert(panel("overview").textContent.includes("Structured lead"));
assert(panel("overview").textContent.includes("Analyst-proposed weights"));
assert(!panel("overview").textContent.includes("Original narrative."));
assert(panel("business").textContent.includes("Business quality"));
assert.equal(document.getElementById("reader-drivers").parentElement.open, true);
assert.equal(document.getElementById("reader-quality").parentElement.open, false);
assert.equal(document.getElementById("reader-management").parentElement.open, false);
assert.equal(document.getElementById("scenario-base").open, true);
assert.equal(document.getElementById("reader-risks").parentElement.open, false);
document.getElementById("reader-drivers").parentElement.open = false;
const repeatedDisclosures = () => all(view).filter(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "fact · sources & calculations");
assert(repeatedDisclosures().length > 1);
repeatedDisclosures()[0].open = true;
repeatedDisclosures()[1].open = false;
vm.runInContext("renderCompany(run)", sandbox);
assert.equal(document.getElementById("reader-drivers").parentElement.open, false);
assert.equal(repeatedDisclosures()[0].open, true);
assert.equal(repeatedDisclosures()[1].open, false);
vm.runInContext("openSavedTarget('reader-quality')", sandbox);
assert.equal(panel("business").hidden, false);
assert.equal(document.getElementById("reader-quality").parentElement.open, true);
vm.runInContext("selectCompanyPanel('overview')", sandbox);
assert(panel("valuation").textContent.includes("12%"));
assert(!panel("valuation").textContent.includes("3×"));
const scaledCalculation = {...calculation,inputs: {forecast_ebit: {value: "2400",scale: "1000000",calculation_value: "2400000000",unit: "currency",currency: "SEK"},required_return: {value: "12",scale: "0.01",calculation_value: "0.12",unit: "dimensionless"},years: {value: "3",scale: "1",calculation_value: "3",unit: "dimensionless"}}};
sandbox.scaledRun = {...run,calculations: [scaledCalculation]};
const scaledAssumptions = vm.runInContext("scenarioAssumptions(scaledRun)", sandbox);
assert(scaledAssumptions.textContent.includes("2,400 SEK million"));
assert(all(scaledAssumptions).some(node => node.title && node.title.includes("2400000000")));
assert(scaledAssumptions.textContent.includes("12%"));
assert(!scaledAssumptions.textContent.includes("1,200%"));
delete scaledCalculation.inputs.required_return.calculation_value;
delete scaledCalculation.inputs.forecast_ebit.calculation_value;
const missingNormalized = vm.runInContext("scenarioAssumptions(scaledRun)", sandbox);
assert(!missingNormalized.textContent.includes("12%"));
assert(!missingNormalized.textContent.includes("2,400 currency"));
assert(missingNormalized.textContent.includes("Unavailable"));
tab("overview").listeners.keydown({key: "ArrowRight",preventDefault() {}});
assert.equal(panel("business").hidden, false);
assert.equal(panel("business").scrolled, true);
assert.equal(panel("overview").hidden, true);
assert.equal(tab("business").tabIndex, 0);
assert.equal(tab("overview").tabIndex, -1);
tab("business").listeners.keydown({key: "End",preventDefault() {}});
assert.equal(panel("evidence").hidden, false);
tab("evidence").listeners.keydown({key: "Home",preventDefault() {}});
assert.equal(panel("overview").hidden, false);
vm.runInContext("selectCompanyPanel('financials'); renderCompany(run)", sandbox);
assert.equal(panel("financials").hidden, false);
assert.equal(panel("financials").scrolled, undefined);
assert.equal(panel("overview").hidden, true);
vm.runInContext("selectCompanyPanel('overview')", sandbox);
run.reader_memo = {schema_version: 1,edited_at: "2026-11-04",analysis_sha256: "hash",summary: "A short editorial conclusion.",sections: sectionIds.map(id => ({id,title: id,paragraphs: [{kind: "interpretation",text: "Reader " + id,references: ["annual:p26"]}]})), scenarios: [{id: "base",rationale: "Reader base rationale",assumption_rationale: "Reader assumption",probability_rationale: "Reader weight caveat",references: ["annual:p26"]}]};
vm.runInContext("renderCompany(run)", sandbox);
assert(panel("overview").textContent.includes("A short editorial conclusion."));
assert(!panel("overview").textContent.includes("Structured lead"));
assert(panel("business").textContent.includes("Reader drivers"));
assert(document.getElementById("scenario-base").textContent.includes("Reader base rationale"));
assert(document.getElementById("canonical-scenario-base").textContent.includes("Base rationale"));
assert(panel("evidence").textContent.includes("not this editorial rewrite"));
assert(panel("evidence").textContent.includes("Structured lead"));
assert(panel("evidence").textContent.includes("Original narrative."));
delete run.reader_memo;
vm.runInContext("renderCompany(run)", sandbox);
assert(panel("overview").textContent.includes("Structured lead"));
assert(!panel("business").textContent.includes("Reader drivers"));
run.reader_memo = {schema_version: 2,summary: "Unsupported reader format",scenarios: [{id: "base",rationale: "Unsupported rationale"}]};
vm.runInContext("renderCompany(run)", sandbox);
assert(panel("overview").textContent.includes("Structured lead"));
assert(!document.getElementById("scenario-base").textContent.includes("Unsupported rationale"));
delete run.reader_memo;
for (const price of [null, {...run.price, value: "90"}, {...run.price, id: "obs:other-price"}, {...run.price, source_id: "src_other"}]) {
  sandbox.variant = {...run, price};
  vm.runInContext("renderCompany(variant)", sandbox);
  assert(header().textContent.includes("Estimated annual return: 12.5%"));
  assert(!header().textContent.includes("at report price"));
}
sandbox.variant = {...run, original_calculations: []};
vm.runInContext("renderCompany(variant)", sandbox);
assert(!header().textContent.includes("at report price"));
sandbox.variant = {...run, original_calculations: [...run.original_calculations, {...run.original_calculations[1], id: "calc:other-irr"}]};
vm.runInContext("renderCompany(variant)", sandbox);
assert(!header().textContent.includes("at report price"));
vm.runInContext("renderCompany(run)", sandbox);
assert(all(view).some(node => node.tagName === "TEXT" && node.textContent === "Base · 60%"));
assert(all(view).filter(node => node.tagName === "SVG" && (node.attributes.class || "").includes("endpoint-chart")).every(node => node.attributes["aria-label"].includes("saved weight 60%")));
assert(view.textContent.includes("Analysis completed: 2026-11-04"));
assert(view.textContent.includes("Saved run completed: 2026-11-04"));
assert(!view.textContent.includes("Saved financial review:"));
assert(!view.textContent.includes("Review recorded:"));
assert(document.getElementById("metric-ebit_margin").textContent.includes("No direct guidance stated for this measure."));
assert(!document.getElementById("metric-ebit_margin").textContent.includes("Plant utilization"));
assert(view.textContent.includes("2029 · year precision"));
assert(!view.textContent.includes("2029-01-01"));
assert(view.textContent.includes("Saved weight: 60%"));
assert(view.textContent.includes("Related management statement · target"));
assert(document.getElementById("management-roce-target").textContent.includes("ROCE uses the issuer capital definition"));
assert(!document.getElementById("management-roce-target").textContent.includes("Related management driver"));
const managementSource = all(document.getElementById("management-utilization")).find(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "Definition & source");
assert(managementSource && !managementSource.open);
assert(managementSource.textContent.includes("Original saved words"));
assert(managementSource.textContent.includes("Issuer utilization; not EBIT margin"));
assert.equal(document.getElementById("management-utilization").parentElement.open, false);
const absentGuidance = document.getElementById("management-margin-guidance");
const guidanceDefinition = all(absentGuidance).find(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "Definition & source");
assert(guidanceDefinition && !guidanceDefinition.open);
assert(guidanceDefinition.textContent.includes("No direct EBIT margin guidance was found"));
assert(!absentGuidance.children.filter(node => node.tagName === "P").some(node => node.textContent.includes("No direct EBIT margin guidance was found")));
const datedMetric = document.getElementById("metric-ebit_margin");
assert(!datedMetric.children.filter(node => node.tagName === "SPAN" || node.tagName === "P").some(node => node.textContent.includes("Consolidated R12") || node.textContent.includes("Dated saved inputs")));
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
  assert(all(panel("evidence")).some(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "Original analysis" && all(node).includes(section)));
}
const originalAnalysis = all(panel("evidence")).find(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "Original analysis");
assert.equal(originalAnalysis.open, false);
const originalReview = all(panel("evidence")).find(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "Independent analysis review");
assert.equal(originalReview.open, false);
const thesis = document.getElementById("analysis-thesis");
const structuredTable = all(thesis).find(node => node.tagName === "TABLE");
assert(structuredTable && structuredTable.textContent.includes("2026 R12"));
assert(!all(thesis).some(node => node.tagName === "P" && node.textContent.includes("| Period |")));
assert(all(originalAnalysis).includes(structuredTable));
const referenceDisclosure = all(thesis).find(node => node.tagName === "DETAILS");
assert(referenceDisclosure && referenceDisclosure.firstElementChild.textContent === "Sources & calculations (5)");
assert(!referenceDisclosure.open);
assert(!all(document.getElementById("analysis-risks")).some(node => node.tagName === "DETAILS"));
vm.runInContext("openSavedTarget('analysis-thesis')", sandbox);
assert.equal(panel("evidence").hidden, false);
assert.equal(originalAnalysis.open, true);
vm.runInContext("openSavedTarget('company-review')", sandbox);
assert.equal(originalReview.open, true);
const links = all(view).filter(node => node.tagName === "A");
for (const target of ["scenario-base", "source-annual", "calculation-calc:value", "input-input:ebit", "record-input:standalone", "company-return"]) {
  const link = links.find(node => node.href === "#" + target);
  assert(link, target);
  let prevented = false;
  link.listeners.click({preventDefault: () => { prevented = true; }});
  assert(prevented && document.getElementById(target).focused, target);
  assert.equal(panel(target === "scenario-base" ? "valuation" : "evidence").hidden, false);
  for (let parent = document.getElementById(target).parentElement; parent; parent = parent.parentElement) if (parent.tagName === "DETAILS") assert(parent.open);
}
assert(links.some(node => node.href === "https://example.com/report.pdf#page=26"));
assert(document.getElementById("calculation-calc:old"));
const chartBars = all(view).filter(node => node.tagName === "RECT" && node.attributes.class && node.attributes.class.includes("scenario-bar"));
assert.equal(chartBars.length, 1);
assert.equal(Number(chartBars[0].attributes.height), 135);
const dots = all(view).filter(node => node.tagName === "CIRCLE" && (node.attributes.class || "").includes("scenario-dot"));
assert.equal(dots.length, 1);
assert.equal(Number(dots[0].attributes.cx), 430);
const charts = all(view).filter(node => node.tagName === "SVG" && (node.attributes.class || "").includes("endpoint-chart"));
assert(charts[0].attributes["aria-label"].includes("horizontal dot plot"));
assert(charts[1].attributes["aria-label"].includes("vertical columns"));
for (const chart of charts) for (const link of all(chart).filter(node => node.tagName === "A")) {
  const hitArea = link.firstElementChild;
  assert.equal(hitArea.tagName, "RECT");
  assert.equal(hitArea.attributes.class, "chart-hit-area");
  assert.equal(hitArea.attributes.fill, "transparent");
  assert.equal(hitArea.attributes["pointer-events"], "all");
  assert(Number(hitArea.attributes.width) > 0 && Number(hitArea.attributes.height) > 0);
  assert(link.children.length > 1);
}
assert(panel("overview").textContent.includes("Discounted share target plus discounted dividends"));
assert(panel("overview").textContent.includes("Separately paid dividends are excluded"));
assert.equal(all(charts[0]).filter(node => node.tagName === "LINE" && node.attributes.class === "price-line").length, 1);
assert.equal(all(charts[1]).filter(node => node.tagName === "LINE" && node.attributes.class === "price-line").length, 0);
const foreignCurrency = vm.runInContext("endpointChart({...run, price: {...run.price,currency: 'USD'}})", sandbox);
assert(!all(foreignCurrency).some(node => node.attributes.class === "price-line"));
const ambiguousUnit = vm.runInContext("matchingPrice(run.price, [{unit: 'currency/share'}])", sandbox);
assert.equal(ambiguousUnit, false);
assert.equal(vm.runInContext("matchingPrice({...run.price,unit: 'SEK/shares'}, [{unit: 'SEK/shares'}])", sandbox), true);
assert.equal(vm.runInContext("matchingPrice({...run.price,unit: 'SEK/shares'}, [{unit: 'USD/shares'}])", sandbox), false);
const sourceLinks = vm.runInContext("sourceRefs({report_id: 'annual'}, run.sources)", sandbox);
vm.runInContext("selectCompanyPanel('financials')", sandbox);
all(sourceLinks).find(node => node.tagName === "A").listeners.click({preventDefault() {}});
assert.equal(panel("evidence").hidden, false);
assert.equal(panel("financials").hidden, true);
assert(document.getElementById("source-annual").focused);
sandbox.location = {hash: "#source-annual"};
vm.runInContext("selectCompanyPanel('overview'); revealSavedHash()", sandbox);
assert.equal(panel("evidence").hidden, false);
assert(document.getElementById("source-annual").focused);
vm.runInContext("selectCompanyPanel('business'); renderCompany(run)", sandbox);
assert.equal(panel("business").hidden, false);
sandbox.location.hash = "#%invalid";
vm.runInContext("revealSavedHash()", sandbox);
sandbox.location.hash = "";
run.analysis_review = {reviewer: "Independent reviewer", verdict: "revise", summary: "Challenge summary", findings: [{id: "finding-1", verdict: "revise",reasoning: "Missing issuer definition",missing_evidence: "Report definition",references: ["annual:p26"]}],disagreements: []};
vm.runInContext("renderCompany(run)", sandbox);
assert(document.getElementById("company-review").textContent.includes("revise"));
assert(!header().textContent.includes("unreviewed"));
const originalStatus = all(view).find(node => node.tagName === "P" && node.textContent === "Original submission review status: unreviewed");
assert(originalStatus && originalStatus.parentElement.tagName === "DETAILS");
assert(document.getElementById("company-review").textContent.includes("Missing issuer definition"));
run.analysis_review.verdict = "accept";
run.analysis.scenarios[0].name = "A very long base scenario name retained without crowding the endpoint label";
vm.runInContext("renderCompany(run)", sandbox);
assert(document.getElementById("company-review").textContent.includes("accept"));
assert(document.getElementById("scenario-base").textContent.includes(run.analysis.scenarios[0].name));
assert(all(view).filter(node => node.tagName === "SVG" && (node.attributes.class || "").includes("endpoint-chart")).every(node => node.attributes["aria-label"].includes(run.analysis.scenarios[0].name)));
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
run.scenarios[0].unit = "SEK/share today";
run.narrative = "# Full report\n\nA preserved paragraph.\n\n| Metric | Value |\n| --- | --- |\n| EBIT | 4 |\n\n<script>still text</script>";
vm.runInContext("renderCompany(run)", sandbox);
const legacy = document.getElementById("legacy-report");
assert(legacy.textContent.includes("A preserved paragraph."));
assert(all(legacy).some(node => node.tagName === "H4" && node.textContent === "Full report"));
assert(all(legacy).some(node => node.tagName === "TABLE"));
assert(!all(legacy).some(node => node.tagName === "SCRIPT"));
assert(view.textContent.includes("Present values as of 2026-11-01. Future targets and assumptions remain in the report."));
const legacyChart = all(view).find(node => node.tagName === "SVG" && node.attributes.class === "chart");
assert(legacyChart.textContent.includes("Present value · 2026-11-01 · SEK/share"));
assert(!/today/i.test(legacyChart.textContent + legacyChart.attributes["aria-label"]));
assert.equal(run.scenarios[0].unit, "SEK/share today");
assert(view.textContent.includes("120 SEK/share today"));
assert(document.getElementById("metric-ebit_margin").textContent.includes("Historical or undated result; a matched current-period result is not available."));
assert(panel("evidence").textContent.includes("Financial review: 2026-11-04"));
assert(!view.textContent.includes("Saved financial review:"));
assert(!view.textContent.includes("Analysis completed:"));
assert(!view.textContent.includes("Saved run completed:"));
assert(!view.textContent.includes("Base rationale"));
assert(all(view).some(node => node.className === "chart-caption" && node.textContent === "Dashed reference: report price 100 SEK/share · 2026-10-30."));
delete run.benchmark;
vm.runInContext("renderCompany(run)", sandbox);
assert(!all(header()).some(node => node.className === "return-overview"));
assert(all(panel("evidence")).some(node => node.tagName === "DETAILS" && node.firstElementChild.textContent === "Report conclusion" && node.textContent.includes("Legacy summary")));
for (const id of ["company-status", "company-error"]) { const node = new SavedNode("p"); node.id = id; root.append(node); }
(async () => {
  vm.runInContext("getJSON = async () => run", sandbox);
  const pending = vm.runInContext('loadRun("legacy")', sandbox);
  assert.equal(document.getElementById("company-status").hidden, false);
  assert.equal(document.getElementById("company-status").textContent, "Loading saved analysis…");
  await pending;
  assert.equal(document.getElementById("company-status").hidden, true);
  assert.equal(document.getElementById("company-status").textContent, "");
  const quote = {instrument_id: 1, value: "125", scale: "1", unit: "currency/share", currency: "SEK", date: "2026-11-04", source_id: "src_latest", provider: "Börsdata", kind: "daily_close", retrieved_at: "2026-11-04T12:00:00+00:00", checked_at: "2026-11-04T12:30:00+00:00"};
  run.benchmark = {candidate_annualized_return_percent: "12.5"};
  sandbox.getJSON = async url => url.startsWith("/api/market-price/") ? {quote} : run;
  await vm.runInContext('loadRun("legacy")', sandbox);
  assert.equal(document.getElementById("latest-market-price").textContent, "Latest market price: 125 SEK/share · Close · 2026-11-04");
  assert(header().textContent.includes("Report price: 100 SEK/share · 2026-10-30"));
  assert(header().textContent.includes("Estimated annual return · at report price: 12.5%"));
  assert(!document.getElementById("latest-market-price").textContent.includes("src_latest"));
  assert(document.getElementById("latest-market-price-evidence").textContent.includes(quote.checked_at));
  assert(document.getElementById("latest-market-price-evidence").textContent.includes("src_latest"));
  assert.equal(run.price.value, "100");
  assert.equal(run.price.date, "2026-10-30");
  const reportPrice = run.price;
  run.price = null;
  await vm.runInContext('loadRun("legacy")', sandbox);
  assert.equal(document.getElementById("latest-market-price").textContent, "Latest market price: 125 SEK/share · Close · 2026-11-04");
  assert(header().textContent.includes("Report price: Unavailable"));
  assert(header().textContent.includes("Estimated annual return: 12.5%"));
  assert(!header().textContent.includes("at report price"));
  run.price = reportPrice;
  for (const invalid of [null, {...quote, instrument_id: 2}, {...quote, currency: "USD"}, {...quote, currency: ""}, {...quote, date: "2026-02-30"}, {...quote, scale: "100"}]) {
    sandbox.getJSON = async url => url.startsWith("/api/market-price/") ? {quote: invalid} : run;
    await vm.runInContext('loadRun("legacy")', sandbox);
    assert.equal(document.getElementById("latest-market-price").textContent, "Latest market price: unavailable");
    assert(header().textContent.includes("Report price: 100 SEK/share · 2026-10-30"));
    assert.equal(view.hidden, false);
  }
  sandbox.getJSON = async url => { if (url.startsWith("/api/market-price/")) throw new Error("Store unavailable"); return run; };
  await vm.runInContext('loadRun("legacy")', sandbox);
  assert.equal(document.getElementById("latest-market-price").textContent, "Latest market price: unavailable");
  assert.equal(document.getElementById("company-error").hidden, true);
  assert.equal(view.hidden, false);
  const quotes = [];
  sandbox.getJSON = url => url.startsWith("/api/market-price/") ? new Promise(resolve => quotes.push(resolve)) : Promise.resolve({...run, id: url.endsWith("first") ? "first" : "second", company: {name: url.endsWith("first") ? "First" : "Second", instrument_id: url.endsWith("first") ? 1 : 2}});
  const first = vm.runInContext('loadRun("first")', sandbox);
  await new Promise(setImmediate);
  const second = vm.runInContext('loadRun("second")', sandbox);
  await new Promise(setImmediate);
  assert.equal(quotes.length, 2);
  quotes[1]({quote: {...quote, instrument_id: 2, value: "150"}});
  await second;
  quotes[0]({quote});
  await first;
  assert(header().textContent.includes("Second"));
  assert.equal(document.getElementById("latest-market-price").textContent, "Latest market price: 150 SEK/share · Close · 2026-11-04");
  vm.runInContext('getJSON = async () => { throw new Error("Unavailable"); }', sandbox);
  await vm.runInContext('loadRun("missing")', sandbox);
  assert.equal(document.getElementById("company-status").hidden, false);
  assert.equal(document.getElementById("company-status").textContent, "Saved analysis unavailable");
  assert.equal(document.getElementById("company-error").hidden, false);
  assert.equal(view.hidden, true);
})().catch(error => { console.error(error); process.exitCode = 1; });
'''
        result = subprocess.run([shutil.which("node"), "-e", script], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
