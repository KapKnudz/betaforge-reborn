import { appendFileSync, mkdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

type Page = { page: number; text: string };
const runFile = promisify(execFile);
const READ_LIMIT = 45_000;

export default function (pi: ExtensionAPI) {
  if (!process.env.BF_DATA_DIR || !process.env.BF_RUN_DIR) {
    throw new Error("BF_DATA_DIR and BF_RUN_DIR are required");
  }
  const dataDir = resolve(process.env.BF_DATA_DIR);
  const runDir = resolve(process.env.BF_RUN_DIR);
  const index = JSON.parse(readFileSync(join(dataDir, "prepared/index.json"), "utf8"));
  const reports = new Map<string, Page[]>();
  for (const report of index.reports) {
    if (!/^granges-(annual-20\d\d|q[13]-2026|h1-2026)$/.test(report.report_id)) {
      throw new Error("Invalid report identifier in index");
    }
    const pages: Page[] = JSON.parse(readFileSync(join(dataDir, "prepared", `${report.report_id}.json`), "utf8"));
    if (pages.length !== report.pages || !pages.every((p, i) => p.page === i + 1 && typeof p.text === "string")) {
      throw new Error(`Invalid prepared pages: ${report.report_id}`);
    }
    reports.set(report.report_id, pages);
  }
  mkdirSync(runDir, { recursive: true });
  const audit = (record: object) => appendFileSync(join(runDir, "tool-audit.jsonl"), JSON.stringify({ at: new Date().toISOString(), ...record }) + "\n");
  const getReport = (id: string) => {
    const pages = reports.get(id);
    if (!pages) throw new Error("Unknown report_id; use a report from the fixed catalogue");
    return pages;
  };
  const checkPage = (pages: Page[], page: number) => {
    if (!Number.isInteger(page) || page < 1 || page > pages.length) throw new Error(`page must be an integer from 1 to ${pages.length}`);
  };
  const result = (details: object) => ({ content: [{ type: "text" as const, text: JSON.stringify(details) }], details });
  const perform = async (tool: string, call_id: string, input: object, action: () => Promise<any> | any) => {
    audit({ event: "call", tool, call_id, input });
    try {
      return await action();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      audit({ event: "error", tool, call_id, error: message });
      throw error;
    }
  };
  const reportId = Type.String({ description: "Exact report_id from the fixed report catalogue" });

  pi.registerTool(defineTool({
    name: "read_report", label: "Read report pages",
    description: "Read consecutive complete PDF pages, up to 45,000 characters including markers. Follow next_page until null. Pages are physical PDF page numbers. This is a full-page read; search snippets are not. An individually oversized page returns an explicit error.",
    parameters: Type.Object({ report_id: reportId, start_page: Type.Integer({ minimum: 1 }) }),
    async execute(callId, params) {
      return perform("read_report", callId, params, () => {
        const pages = getReport(params.report_id);
        checkPage(pages, params.start_page);
        let text = "";
        const delivered_pages: number[] = [];
        for (const page of pages.slice(params.start_page - 1)) {
          const block = `\n=== ${params.report_id} | PDF PAGE ${page.page} START ===\n${page.text}\n=== ${params.report_id} | PDF PAGE ${page.page} END ===\n`;
          if (text.length + block.length > READ_LIMIT) {
            if (!text) throw new Error(`PDF page ${page.page} exceeds the complete-page read limit; use view_report_page`);
            break;
          }
          text += block;
          delivered_pages.push(page.page);
        }
        const end_page = delivered_pages[delivered_pages.length - 1];
        const metadata = { report_id: params.report_id, start_page: params.start_page, end_page, delivered_pages, next_page: end_page < pages.length ? end_page + 1 : null, characters: text.length };
        audit({ event: "result", tool: "read_report", call_id: callId, ...metadata });
        return result({ ...metadata, text });
      });
    },
  }));

  pi.registerTool(defineTool({
    name: "search_reports", label: "Search report text",
    description: "Case-insensitive literal search. Returns at most 30 matching pages, one bounded snippet per page, and total matching page count. Search snippets never count as full-page reads.",
    parameters: Type.Object({ query: Type.String({ minLength: 1, maxLength: 500 }), report_id: Type.Optional(reportId) }),
    async execute(callId, params) {
      return perform("search_reports", callId, params, () => {
        if (typeof params.query !== "string" || !params.query.trim() || params.query.length > 500) throw new Error("query must contain 1–500 characters and cannot be whitespace only");
        const selected = params.report_id === undefined ? [...reports] : [[params.report_id, getReport(params.report_id)]] as [string, Page[]][];
        const query = params.query.toLowerCase();
        const hits: { report_id: string; page: number; snippet: string }[] = [];
        let total_hits = 0;
        for (const [id, pages] of selected) {
          for (const page of pages) {
            const position = page.text.toLowerCase().indexOf(query);
            if (position < 0) continue;
            total_hits++;
            if (hits.length < 30) {
              const start = Math.max(0, position - 160);
              const end = Math.min(page.text.length, position + query.length + 160);
              hits.push({ report_id: id, page: page.page, snippet: `${start ? "…" : ""}${page.text.slice(start, end)}${end < page.text.length ? "…" : ""}` });
            }
          }
        }
        const metadata = { query: params.query, report_id: params.report_id ?? null, total_hits, returned_hits: hits.length, full_page_read: false };
        audit({ event: "result", tool: "search_reports", call_id: callId, ...metadata, pages: hits.map(({ report_id, page }) => ({ report_id, page })) });
        return result({ ...metadata, hits });
      });
    },
  }));

  pi.registerTool(defineTool({
    name: "view_report_page", label: "View original PDF page",
    description: "Render one physical PDF page at 110 dpi to inspect tables, charts, units or extraction errors. Returns the original page image.",
    parameters: Type.Object({ report_id: reportId, page: Type.Integer({ minimum: 1 }) }),
    async execute(callId, params, signal) {
      return perform("view_report_page", callId, params, async () => {
        checkPage(getReport(params.report_id), params.page);
        const imageDir = join(runDir, "images");
        mkdirSync(imageDir, { recursive: true });
        const prefix = join(imageDir, `${params.report_id}-p${params.page}`);
        await runFile("pdftoppm", ["-f", String(params.page), "-l", String(params.page), "-singlefile", "-r", "110", "-png", join(dataDir, "sources", `${params.report_id}.pdf`), prefix], { signal, timeout: 60_000, maxBuffer: 1_000_000 });
        const image_path = `${prefix}.png`;
        const image = readFileSync(image_path);
        const details = { report_id: params.report_id, page: params.page, dpi: 110, image_path };
        audit({ event: "result", tool: "view_report_page", call_id: callId, ...details, bytes: image.length });
        return { content: [{ type: "text" as const, text: JSON.stringify(details) }, { type: "image" as const, data: image.toString("base64"), mimeType: "image/png" }], details };
      });
    },
  }));

  pi.registerTool(defineTool({
    name: "calculate", label: "Calculate from cited inputs",
    description: "Arithmetic using supplied finite numbers. add/multiply require at least two values; subtract/divide use [left,right]; growth_percent uses [old,new] and computes (new-old)/old*100. sources records the provenance of supplied inputs; it does not verify them.",
    parameters: Type.Object({ operation: Type.Union(["add", "subtract", "multiply", "divide", "growth_percent"].map(value => Type.Literal(value))), values: Type.Array(Type.Number(), { minItems: 2, maxItems: 100 }), sources: Type.Array(Type.String({ minLength: 1, maxLength: 500 }), { minItems: 1, maxItems: 100 }) }),
    async execute(callId, params) {
      return perform("calculate", callId, params, () => {
        const { operation, values, sources } = params;
        if (!Array.isArray(values) || values.length < 2 || values.length > 100 || !values.every(Number.isFinite)) throw new Error("Provide 2–100 finite values");
        if (!Array.isArray(sources) || !sources.length || sources.length > 100 || !sources.every(s => typeof s === "string" && s.trim().length > 0 && s.length <= 500)) throw new Error("Provide 1–100 source references, each 1–500 characters");
        if (["subtract", "divide", "growth_percent"].includes(operation) && values.length !== 2) throw new Error(`${operation} requires exactly two values`);
        let value: number;
        switch (operation) {
          case "add": value = values.reduce((a, b) => a + b, 0); break;
          case "multiply": value = values.reduce((a, b) => a * b, 1); break;
          case "subtract": value = values[0] - values[1]; break;
          case "divide": if (values[1] === 0) throw new Error("Division by zero"); value = values[0] / values[1]; break;
          case "growth_percent": if (values[0] === 0) throw new Error("Growth baseline is zero"); value = (values[1] - values[0]) / values[0] * 100; break;
          default: throw new Error("Unsupported operation");
        }
        if (!Number.isFinite(value)) throw new Error("Result is not finite");
        const details = { operation, values, sources, result: value };
        audit({ event: "result", tool: "calculate", call_id: callId, ...details });
        return result(details);
      });
    },
  }));
}
