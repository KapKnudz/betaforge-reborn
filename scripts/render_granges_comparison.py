"""Render the completed experiment as a local, read-only review page."""
import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/granges-walkthrough"
OUT = ROOT / ".lavish"
esc = lambda value: html.escape(str(value))


def main():
    review = json.loads((DATA / "comparison-review.json").read_text())
    metrics = json.loads((DATA / "runs/comparison-summary.json").read_text())
    manifest = json.loads((DATA / "source-manifest.json").read_text())
    OUT.mkdir(exist_ok=True)
    assets = OUT / "granges-assets"
    assets.mkdir(exist_ok=True)
    image = DATA / "qa/granges-annual-2025-p141.png"
    shutil.copy2(image, assets / image.name)
    stats = []
    answer_blocks = []
    traces = []
    for arm, label in [("upfront", "Reports upfront"), ("tools", "Read through tools")]:
        directory = DATA / "runs" / arm
        meta = json.loads((directory / "metadata.json").read_text())
        audit = [json.loads(line) for line in (directory / "tool-audit.jsonl").read_text().splitlines()]
        results = [r for r in audit if r["event"] == "result"]
        usage = metrics["arms"][arm]["combined_usage_totals"]
        stats.append({"label": label, "score": review["scores"][arm], "minutes": round(meta["elapsed_seconds"] / 60, 1),
                      "responses": len(meta["usage"]), "uncached": usage["input"],
                      "cached": usage["cacheRead"],
                      "output": usage["output"],
                      "images": sum(r["tool"] == "view_report_page" for r in results),
                      "calculations": sum(r["tool"] == "calculate" for r in results),
                      "pages": meta["upfront_pages_in_request"] if arm == "upfront" else meta["coverage"]["pages_delivered"],
                      "compactions": sum(r.get("type") == "compaction_end" and not r.get("aborted") for r in meta["compactions"])})
        answer = (directory / "answer.md").read_text()
        answer_blocks.append(f'<details class="collapse collapse-arrow bg-base-200 border border-base-content/10"><summary class="collapse-title text-xl font-semibold">{label}: complete final answer</summary><div class="collapse-content"><pre class="answer">{esc(answer)}</pre></div></details>')
        for row in results:
            tool = row["tool"]
            if tool == "calculate":
                text = f"{row['operation']} {row['values']} → {row['result']} | Sources: {', '.join(row['sources'])}"
            elif tool == "read_report":
                text = f"{row['report_id']}, PDF pages {row['start_page']}–{row['end_page']}"
            elif tool == "view_report_page":
                text = f"{row['report_id']}, PDF page {row['page']}"
            else:
                text = f"{row['query']}: {row['total_hits']} matching pages"
            traces.append({"arm": label, "tool": tool, "text": text})
    cards = "".join(f'''<article class="card bg-base-200 border border-base-content/10"><div class="card-body">
      <p class="text-sm uppercase tracking-widest opacity-60">{s['label']}</p><div class="text-5xl font-semibold">{s['score']}<span class="text-xl opacity-50"> / 40</span></div>
      <p>{s['pages']} text pages supplied · {s['minutes']} minutes</p><p class="text-sm opacity-70">{s['images']} page-image checks · {s['calculations']} calculations · {s['compactions']} completed compactions</p>
      </div></article>''' for s in stats)
    score_rows = "".join(f"<tr><th>{esc(q['id'])}</th><td>{esc(q['topic'])}</td><td>{esc(q['upfront'])}/5</td><td>{esc(q['tools'])}/5</td><td>{esc(q['finding'])}</td></tr>" for q in review["questions"])
    source_rows = "".join(f'<tr><th>{esc(d["report_id"])}</th><td>{d["page_count"]}</td><td>{d["publication_date"]}</td><td><a class="link" href="{esc(d["source_url"])}" target="_blank" rel="noopener">Original issuer PDF ↗</a></td></tr>' for d in manifest["documents"])
    limit_items = "".join(f"<li>{esc(item)}</li>" for item in review["limitations"])
    metric_rows = "".join(f"<tr><th>{esc(label)}</th>" + "".join(f"<td>{s[key]:,}</td>" for s in stats) + "</tr>" for label,key in [("Model responses","responses"),("Uncached input tokens, accumulated","uncached"),("Cached input tokens, accumulated","cached"),("Output tokens, accumulated","output")])
    trace_json = json.dumps(traces, ensure_ascii=False).replace("<", "\\u003c")
    page = f'''<!doctype html><html lang="en" data-theme="luxury"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gränges · retrieval experiment</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/daisyui@5.5.19/daisyui.css"><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/daisyui@5.5.19/themes.css"><script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.2.4/dist/index.global.js"></script>
    <style>*{{box-sizing:border-box}}body{{margin:0;background:#09090b;color:#eee9df;font-family:system-ui,sans-serif}}.grid>*{{min-width:0}}p,td,th,li,a{{overflow-wrap:anywhere}}.answer{{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.7 ui-monospace,monospace;max-width:100%}}section{{margin-top:3rem}}.evidence-image{{max-width:100%;height:auto}}table{{width:100%}}li{{margin:.65rem 0}}.table-wrap{{overflow-x:auto}}summary{{cursor:pointer}}</style></head>
    <body><main class="max-w-6xl mx-auto p-6 md:p-12"><header><p class="text-sm uppercase tracking-[.2em] text-primary">Betaforge · fixed-corpus experiment · 1 November 2026</p><h1 class="text-4xl md:text-5xl font-semibold mt-5 mb-5">{esc(review['headline'])}</h1><p class="text-xl max-w-4xl opacity-80">{esc(review['recommendation'])}</p><p class="mt-5 text-sm opacity-60">One company · 8 original reports · 921 pages · GPT-6.1 Sol, high reasoning · pi 1.4.0</p></header>
    <section aria-label="Results" class="grid md:grid-cols-2 gap-5">{cards}</section>
    <p class="text-sm opacity-60 mt-4">Page supply measures exposure, not comprehension. Upfront pages were in the accepted request; tool pages were counted from complete-page tool deliveries.</p>
    <section><h2 class="text-2xl mb-5">Independent evidence review</h2><p class="mb-4 opacity-70">The reference rubric was prepared from the original PDFs before candidate answers were seen. Each question carries five points.</p><div class="table-wrap rounded-box border border-base-content/10"><table class="table"><thead><tr><th>Question</th><th>Evidence task</th><th>Upfront</th><th>Tools</th><th>Reviewer finding</th></tr></thead><tbody>{score_rows}</tbody></table></div></section>
    <section class="grid md:grid-cols-2 gap-8"><div><h2 class="text-2xl mb-5">A PDF is not a clean table</h2><p class="opacity-80">On annual 2025 PDF page 141, the extracted text splits 7,163 into “7,1 6 3”. Both approaches had access to original page images. Saved extracted text is useful context; important numeric inputs still need source verification.</p><p class="mt-4 text-sm opacity-60">Representative QA covered eight pages. It did not validate every table, chart or footnote.</p></div><details><summary class="mb-3 link">Inspect the original page sample</summary><img class="evidence-image rounded-box" src="granges-assets/{image.name}" alt="Gränges annual report 2025, physical PDF page 141, original financial table"></details></section>
    <section><h2 class="text-2xl mb-5">Acquisition provenance</h2><p class="mb-4">Originals were downloaded from Gränges’ IR archive. A separate MFN check found all eight releases and attachment links, but attachment downloads returned HTTP 403. MFN attachment byte identity remains unverified.</p><div class="table-wrap"><table class="table table-sm"><thead><tr><th>Report</th><th>PDF pages</th><th>Published</th><th>Source</th></tr></thead><tbody>{source_rows}</tbody></table></div></section>
    <section><h2 class="text-2xl mb-4">Measured processing</h2><div class="table-wrap"><table class="table"><thead><tr><th>Metric</th><th>Upfront</th><th>Tools</th></tr></thead><tbody>{metric_rows}</tbody></table></div><p class="mt-3 text-sm opacity-60">Token counts accumulate across model requests, including cached context. They are not unique document size or a subscription bill. Upfront compaction was disabled; tool-reading compaction was enabled. This compares those workflow configurations, not exposure method in isolation.</p></section>
    <section><h2 class="text-2xl mb-5">Inspect the tool record</h2><div class="flex flex-wrap gap-3 mb-4"><label>Approach <select id="arm" class="select select-sm"><option value="">Both</option><option>Reports upfront</option><option>Read through tools</option></select></label><label>Action <select id="tool" class="select select-sm"><option value="">All</option><option value="calculate">Calculations</option><option value="read_report">Full-page reads</option><option value="view_report_page">Page images</option><option value="search_reports">Searches</option></select></label></div><p id="count" class="text-sm opacity-60 mb-3"></p><div class="table-wrap max-h-[32rem] overflow-y-auto"><table class="table table-sm"><thead><tr><th>Approach</th><th>Action</th><th>Recorded result</th></tr></thead><tbody id="trace"></tbody></table></div></section>
    <section><h2 class="text-2xl mb-5">Complete candidate answers</h2><div class="space-y-4">{''.join(answer_blocks)}</div></section>
    <section class="card bg-base-200"><div class="card-body"><h2 class="text-2xl">What this establishes—and what remains open</h2><ul class="list-disc pl-5">{limit_items}</ul></div></section><footer class="mt-10 text-sm opacity-50">Read-only experiment review. No website backend or live Börsdata integration is represented here. Design: Lavish’s Tailwind/DaisyUI fallback; the repository has no existing UI design system.</footer></main>
    <script type="application/json" id="trace-data">{trace_json}</script><script>const data=JSON.parse(document.getElementById('trace-data').textContent);function draw(){{const a=document.getElementById('arm').value,t=document.getElementById('tool').value;const rows=data.filter(r=>(!a||r.arm===a)&&(!t||r.tool===t));const body=document.getElementById('trace');body.replaceChildren();for(const r of rows){{const tr=document.createElement('tr');for(const key of ['arm','tool','text']){{const td=document.createElement('td');td.textContent=r[key];tr.appendChild(td)}}body.appendChild(tr)}}document.getElementById('count').textContent=rows.length+' recorded tool results';}}document.getElementById('arm').addEventListener('change',draw);document.getElementById('tool').addEventListener('change',draw);draw();</script></body></html>'''
    target = OUT / "granges-retrieval.html"
    target.write_text(page)
    print(target)


if __name__ == "__main__":
    main()
