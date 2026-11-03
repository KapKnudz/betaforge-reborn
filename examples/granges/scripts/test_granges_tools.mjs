// Usage: node examples/granges/scripts/test_granges_tools.mjs /path/to/pi-coding-agent [corpus-root]
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const { loadExtensions } = await import(pathToFileURL(join(process.argv[2], "dist/core/extensions/loader.js")));
const root = mkdtempSync(join(tmpdir(), "granges-tools-test-"));
const extension = fileURLToPath(new URL("./granges_tools.ts", import.meta.url));
const report_id = "granges-annual-2021";
let call = 0;
async function load(data, output) {
  process.env.BF_DATA_DIR = data;
  process.env.BF_RUN_DIR = output;
  const loaded = await loadExtensions([extension], process.cwd());
  assert.deepEqual(loaded.errors, []);
  const tools = loaded.extensions[0].tools;
  assert.deepEqual([...tools.keys()], ["read_report", "search_reports", "view_report_page", "calculate"]);
  return (name, params) => tools.get(name).definition.execute(`test-${++call}`, params);
}
try {
  mkdirSync(join(root, "prepared"));
  const pages = Array.from({ length: 34 }, (_, i) => ({ page: i + 1, text: i === 33 ? "x".repeat(45_001) : `Needle page ${i + 1}\n${"x".repeat(22_000)}` }));
  writeFileSync(join(root, "prepared/index.json"), JSON.stringify({ reports: [{ report_id, pages: pages.length }] }));
  writeFileSync(join(root, `prepared/${report_id}.json`), JSON.stringify(pages));
  const invoke = await load(root, join(root, "run"));
  const first = (await invoke("read_report", { report_id, start_page: 1 })).details;
  assert.deepEqual(first.delivered_pages, [1, 2]);
  assert.equal(first.next_page, 3);
  assert.ok(first.text.length <= 45_000);
  assert.ok(first.text.includes(pages[1].text));
  assert.ok(first.text.endsWith(`PDF PAGE 2 END ===\n`));
  await assert.rejects(invoke("read_report", { report_id, start_page: 34 }), /exceeds/);
  await assert.rejects(invoke("read_report", { report_id, start_page: 0 }), /integer/);
  await assert.rejects(invoke("read_report", { report_id: "../../other", start_page: 1 }), /Unknown/);
  const search = (await invoke("search_reports", { query: "nEEdLe" })).details;
  assert.equal(search.total_hits, 33);
  assert.equal(search.hits.length, 30);
  assert.equal(search.full_page_read, false);
  assert.ok(search.hits.every(hit => hit.snippet.length <= 328));
  assert.equal((await invoke("search_reports", { query: ".*" })).details.total_hits, 0);
  await assert.rejects(invoke("search_reports", { query: " " }), /whitespace/);
  const sources = ["fixture: page 1"];
  for (const [operation, values, expected] of [["add", [2, 3, 4], 9], ["subtract", [9, 3], 6], ["multiply", [2, 3], 6], ["divide", [9, 3], 3], ["growth_percent", [100, 125], 25]]) {
    assert.equal((await invoke("calculate", { operation, values, sources })).details.result, expected);
  }
  for (const [operation, values] of [["divide", [1, 0]], ["growth_percent", [0, 1]], ["subtract", [1, 2, 3]], ["add", [Infinity, 1]], ["multiply", [1e308, 1e308]]]) {
    await assert.rejects(invoke("calculate", { operation, values, sources }));
  }
  const audit = readFileSync(join(root, "run/tool-audit.jsonl"), "utf8").trim().split("\n").map(JSON.parse);
  assert.ok(audit.some(row => row.event === "error"));
  assert.deepEqual(audit.find(row => row.event === "result" && row.tool === "read_report").delivered_pages, [1, 2]);
  assert.ok(audit.every(row => !Object.hasOwn(row, "text")));
  if (process.argv[3]) {
    const real = await load(resolve(process.argv[3]), join(root, "real-run"));
    const rendered = await real("view_report_page", { report_id: "granges-q3-2026", page: 20 });
    assert.equal(rendered.details.dpi, 110);
    const bytes = Buffer.from(rendered.content[1].data, "base64");
    assert.equal(bytes.subarray(1, 4).toString(), "PNG");
  }
  console.log("PASS: module loading, complete-page bounds, cursors, search limits, literal matching, arithmetic, errors, audit" + (process.argv[3] ? ", real PDF rendering" : ""));
} finally {
  rmSync(root, { recursive: true, force: true });
}
