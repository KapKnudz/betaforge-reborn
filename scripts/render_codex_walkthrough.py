"""Render saved Gränges records as a portable HTML review; never runs analysis."""
import argparse
import base64
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def esc(value):
    return html.escape(str(value), quote=True)


def display_number(value):
    """Readable base-unit display; the complete saved decimal remains in details."""
    try:
        with localcontext() as context:
            context.prec = 150
            number = Decimal(str(value))
            if not number.is_finite():
                return str(value)
            shown = format(number.quantize(Decimal('0.000001')), ',f').rstrip('0').rstrip('.')
            return '0' if shown == '-0' else shown
    except (InvalidOperation, ValueError):
        return str(value)


def read_json(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def download(label, name, content, mime='application/json'):
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(content.encode()).decode()
    return f'<a class="btn" download="{esc(name)}" href="data:{mime};base64,{encoded}">{esc(label)}</a>'


def details(label, value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    return f'<details><summary>{esc(label)}</summary><pre>{esc(text)}</pre></details>'


def rows_list(value):
    return list(value.values()) if isinstance(value, dict) else value or []


def report_html(text):
    # No Markdown renderer is installed in the project or default Python.
    # Preserve readable source safely; the reviewed summary leads the page.
    return '<pre class="report">' + esc(text) + '</pre>'


def reviewed_summary(summary):
    if not summary:
        return ''
    conclusion = '<p class="notice">' + esc(summary.get('conclusion', '')) + '</p>'
    rows = []
    for scenario in summary.get('scenarios', []):
        refs = ', '.join(scenario.get('calculation_ids', []))
        rows.append('<tr><td>' + esc(scenario.get('name', '')) + '</td><td class="num">' +
                    esc(scenario.get('value', '')) + ' ' + esc(scenario.get('unit', '')) +
                    '</td><td>' + esc(scenario.get('basis', '')) + '<br><code>' + esc(refs) + '</code></td></tr>')
    table = ('<div class="tablewrap"><table><thead><tr><th scope="col">Reviewed scenario</th>'
             '<th scope="col">Value</th><th scope="col">Basis / saved calculations</th></tr></thead><tbody>' +
             ''.join(rows) + '</tbody></table></div>') if rows else ''
    notes = ''.join('<li>' + esc(note) + '</li>' for note in summary.get('notes', []))
    return conclusion + table + ('<ul class="review-notes">' + notes + '</ul>' if notes else '')


STYLE = '''
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#10100f;color:#e8e5dc;font:16px/1.65 system-ui,sans-serif}main{max-width:1320px;margin:auto;padding:40px 24px}section{margin:48px 0}h1{font:clamp(2.4rem,6vw,4.7rem)/1.06 Georgia,serif;max-width:1000px;margin:22px 0}h2{font:2rem/1.2 Georgia,serif;margin:0 0 20px}h3{font-size:1.1rem}p{max-width:960px}.muted{color:#b7b3a6}.eyebrow{color:#c4a865;letter-spacing:.12em;text-transform:uppercase;font-size:12px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}.panel{min-width:0;padding:24px;border:1px solid #38362e;border-radius:12px;background:#191916}.number{color:#dac184;font:2.5rem Georgia,serif}.tablewrap{max-width:100%;overflow:auto;border:1px solid #38362e;border-radius:12px}table{width:100%;border-collapse:collapse}th,td{text-align:left;vertical-align:top;padding:16px;border-bottom:1px solid #333129;overflow-wrap:anywhere}th{color:#dac184;background:#1e1d17;font-size:13px}td{font-size:14px}code{color:#e0cda2;font-size:.9em;overflow-wrap:anywhere}a{color:#d8bd7c}nav{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0}.btn{display:inline-block;padding:8px 13px;border:1px solid #786a46;border-radius:6px;text-decoration:none;font-size:13px;height:auto;min-height:0}.notice{border-left:3px solid #c4a865;padding:14px 22px;background:#1c1b16}.filters{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:16px}input{max-width:100%;background:#1b1b17;color:#e8e5dc;padding:10px;border:1px solid #5c574a;border-radius:6px}details{margin-top:12px}summary{cursor:pointer;color:#d8bd7c}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.65 ui-monospace,monospace;max-width:100%;margin:14px 0}.report{font:15px/1.8 system-ui,sans-serif;max-width:1050px}.review-notes{padding-left:24px;list-style:revert}.num{font-variant-numeric:tabular-nums}.status{color:#dac184;font-weight:650}.citation-badge{display:inline-block;font-size:11px;line-height:1.5;margin-top:8px;padding:3px 7px;border:1px solid #575144;border-radius:5px}.citation-badge.cited{color:#dac184;border-color:#786a46}.citation-badge.intermediate{color:#b7b3a6}.formula{min-width:180px;max-width:340px}.calc-label{min-width:220px}.provenance{min-width:220px;max-width:400px}progress{accent-color:#c4a865;width:100%;height:8px}.small{font-size:13px}footer{border-top:1px solid #38362e;padding-top:24px;margin-top:48px}tbody tr[hidden]{display:none}@media(max-width:800px){.grid{grid-template-columns:minmax(0,1fr)}main{padding:28px 16px}th,td{padding:12px}.number{font-size:2rem}}@media print{body{background:white;color:#222}.panel,th,.notice{background:white;border-color:#aaa}.muted{color:#555}a,code,summary,.number,.status{color:#514421}.filters,nav{display:none}details{break-inside:avoid}pre{color:#222}}
'''


def render(run_dir, packet_file, output, allow_incomplete=False):
    run_dir, packet_file, output = map(lambda p: Path(p).resolve(), (run_dir, packet_file, output))
    run = read_json(run_dir / 'run.json', {'status': 'not_started'})
    final = run.get('status') == 'completed' and not run.get('smoke', False)
    if not final and not allow_incomplete:
        raise ValueError('Full walkthrough is not completed; use --allow-incomplete for a clearly marked progress artifact')
    packet = read_json(packet_file)
    packet_dir = packet_file.parent
    snapshot = (packet_dir / packet['snapshot_dir']).resolve()
    reports_dir = (packet_dir / packet['reports_dir']).resolve()
    index = read_json(reports_dir / 'prepared/index.json')
    state = read_json(run_dir / 'tool-state.json', {})
    calculations = rows_list(read_json(run_dir / 'calculations.json', state.get('calculations', {})))
    inputs = rows_list(read_json(run_dir / 'inputs.json', state.get('inputs', {})))
    answer_file = run_dir / 'answer.md'
    # A partial model message is never promoted to a final valuation report.
    answer = answer_file.read_text() if final and answer_file.exists() else ''
    review = read_json(run_dir / 'review-summary.json', {}) if final else {}
    mapping = (packet_dir / 'mapping-resolution.md').read_text()
    database = snapshot / 'evidence.sqlite3'
    with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
        connection.row_factory = sqlite3.Row
        sources = [dict(r) for r in connection.execute('SELECT id,provider,endpoint,parameters,sha256,observed_at FROM sources ORDER BY provider,endpoint,id')]
        for source in sources:
            source['parameters'] = json.loads(source['parameters'])
        counts = {table: connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                  for table in ('observations', 'current_observations', 'acquisitions')}
        datasets = [dict(r) for r in connection.execute('SELECT dataset,count(*) AS records FROM datasets GROUP BY dataset ORDER BY dataset')]
    source_by_id = {source['id']: source for source in sources}
    required = set(packet.get('required_reports', [r['report_id'] for r in index['reports']]))
    coverage_rows, delivered, total = [], 0, 0
    for report in index['reports']:
        rid = report['report_id']
        if rid not in required:
            continue
        pages = int(report['pages'])
        valid = {page for page in state.get('coverage', {}).get(rid, []) if type(page) is int and 1 <= page <= pages}
        read = len(valid)
        delivered += read
        total += pages
        coverage_rows.append(f'<tr><td>{esc(rid)}</td><td class="num">{read} / {pages}</td><td>{"Delivered" if read == pages else "Incomplete"}<progress value="{read}" max="{pages}" aria-label="{esc(rid)} page delivery"></progress></td><td>{details("PDF and text hashes", {k: report[k] for k in ("source_sha256", "prepared_sha256")})}</td></tr>')
    cited_ids = set(re.findall(r'\bcalc:[0-9a-f]{20}\b', answer))
    calc_rows = []
    for position, calc in enumerate(calculations, 1):
        cited = calc.get('id') in cited_ids
        citation_status = 'Cited in final report' if cited else 'Intermediate / not cited'
        badge_class = 'cited' if cited else 'intermediate'
        evidence = []
        for item in calc.get('inputs', []):
            record = dict(item)
            if item.get('source_id') in source_by_id:
                record['source_provenance'] = source_by_id[item['source_id']]
            evidence.append(record)
        identifiers = [item.get('id', 'unspecified') for item in calc.get('inputs', [])]
        formula = calc.get('formula_text') or (str(calc.get('operation', 'unknown')) + '(' + ', '.join(identifiers) + ')')
        result = 'Unavailable' if calc.get('result') is None else display_number(calc.get('result', ''))
        outputs = details('Named outputs and limits', {key:calc[key] for key in ('outputs','warnings','missing_inputs','basis','version') if key in calc}) if calc.get('outputs') else ''
        calc_rows.append(f'<tr id="calculation-{position}"><td class="calc-label"><strong>{esc(calc.get("label", "Untitled"))}</strong><br><code>{esc(calc.get("id", ""))}</code><br><span class="citation-badge {badge_class}">{citation_status}</span></td><td class="num">{esc(result)}<br><span class="muted">{esc(calc.get("unit", ""))}</span>{outputs}</td><td class="formula"><code>{esc(formula)}</code></td><td class="provenance">{details("Inputs and source provenance", evidence)}{details("Saved calculation", calc)}</td></tr>')
    status = str(run.get('status', 'unknown'))
    headline = 'Gränges, from evidence to valuation.' if final else 'Gränges analysis is still in progress.'
    description = ('The saved full walkthrough is complete. Review its report, required-page delivery and calculation inputs below. Completion is a run status, not an independent endorsement of the valuation.' if final else f'This is a progress snapshot. Saved run status: {status}. No final valuation is presented; regenerate from saved records after completion.')
    source_rows = ''.join(f'<tr><td>{esc(s["provider"])}</td><td><code>{esc(s["endpoint"])}</code></td><td>{esc(s["observed_at"])}{details("Source ID, parameters and hash", s)}</td></tr>' for s in sources)
    dataset_rows = ''.join(f'<tr><td><code>{esc(d["dataset"])}</code></td><td class="num">{d["records"]:,}</td></tr>' for d in datasets)
    # Extract source-authored sections, never infer scenario values from labels or calculations.
    mapping_summary = mapping.split('## Bounded verdict', 1)[-1].strip() if '## Bounded verdict' in mapping else 'See the full saved mapping decisions.'
    downloads = [download('Run metadata', 'run.json', run), download('Calculations JSON', 'calculations.json', calculations), download('Inputs JSON', 'inputs.json', inputs), download('Sources JSON', 'sources.json', sources), download('Mapping decisions', 'mapping-resolution.md', mapping, 'text/markdown')]
    if answer:
        downloads.insert(0, download('Full report Markdown', 'answer.md', answer, 'text/markdown'))
    if review:
        downloads.append(download('Reviewed summary', 'review-summary.json', review))
    contract_text = ''
    for role, entry in packet.get('analysis_contract', {}).items():
        path = (packet_dir / entry['path']).resolve()
        if not path.is_relative_to(packet_dir):
            raise ValueError('Analysis contract path outside packet')
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Analysis contract hash mismatch')
        body = path.read_text()
        downloads.append(download('Analysis '+role, role+'.md', body, 'text/markdown'))
        contract_text += details('Adopted '+role, body)
    answer_block = ('<details><summary>Read the full saved report</summary>' + report_html(answer) + '</details>') if answer else '<p class="notice">The final answer is not available in this artifact. No scenario figures have been inferred from intermediate calculations.</p>'
    generated = datetime.now(timezone.utc).isoformat(timespec='seconds')
    document = f'''<!doctype html>
<html lang="en" data-theme="luxury"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Gränges • Codex walkthrough review</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/daisyui@5.5.19/daisyui.css"><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/daisyui@5.5.19/themes.css"><style>{STYLE}</style></head><body><main>
<header><div class="eyebrow">Betaforge / saved walkthrough / {esc(packet.get('analysis_date', 'undated'))}</div><h1>{headline}</h1><p>{esc(description)}</p><p class="muted small">Generated {esc(generated)}. This page reads saved files only. It never refreshes data or starts an analysis.</p><nav><a class="btn" href="#report">Report</a><a class="btn" href="#calculations">Calculations</a><a class="btn" href="#coverage">Reading coverage</a><a class="btn" href="#sources">Sources</a></nav></header>
<section class="grid" aria-label="Run summary"><div class="panel"><div class="eyebrow">Saved run status</div><div class="number">{esc(status.replace('_', ' '))}</div><p class="muted">{esc(run.get('model', 'Unknown model'))} / {esc(run.get('reasoning_effort', 'unknown'))} reasoning</p></div><div class="panel"><div class="eyebrow">Required text pages delivered</div><div class="number">{delivered:,} / {total:,}</div><p class="muted">{len(coverage_rows)} required reports. Delivery does not prove comprehension.</p></div><div class="panel"><div class="eyebrow">Audited calculations</div><div class="number">{len(calculations):,}</div><p class="muted">{len(inputs):,} saved analyst inputs and assumptions. Original observation scales are applied once.</p></div></section>
<section id="report"><h2>The saved analysis</h2>{reviewed_summary(review)}{answer_block}{contract_text}</section>
<section id="calculations"><h2>Trace each calculation</h2><p class="muted">Values below use base units, rounded to at most six decimal places for display. Exact saved decimals remain in the details. Expand a row to inspect original values, scales, selected sources and assumptions. Badges mark exact calculation IDs cited in the final report. Uncited does not mean wrong: intermediate work can include abandoned interpretations, so use the final report for endorsed conclusions.</p><div class="filters"><label for="calc-search">Find a calculation</label><input id="calc-search" type="search" placeholder="Label, value, unit or input ID"><span id="calc-count" class="muted" aria-live="polite"></span></div><div class="tablewrap"><table><thead><tr><th scope="col">Calculation</th><th scope="col">Result / unit</th><th scope="col">Operation and input IDs</th><th scope="col">Evidence</th></tr></thead><tbody id="calc-rows">{''.join(calc_rows)}</tbody></table></div><p id="no-calculations" class="muted" hidden>No matching calculations.</p></section>
<section id="coverage"><h2>Required reports and reading coverage</h2><p class="muted">Five annual reports and the three 2026 interim reports. Search snippets and page images do not substitute for complete text delivery.</p><div class="tablewrap"><table><thead><tr><th scope="col">Report</th><th scope="col">Pages delivered / total</th><th scope="col">Status</th><th scope="col">Frozen source identity</th></tr></thead><tbody>{''.join(coverage_rows)}</tbody></table></div></section>
<section id="mapping" class="panel"><h2>How conflicting figures were handled</h2><pre class="report">{esc(mapping_summary)}</pre>{details('Read all saved mapping decisions', mapping)}</section>
<section id="sources"><h2>The frozen evidence foundation</h2><p>{len(sources):,} saved source versions; {counts['acquisitions']:,} acquisition records; {counts['current_observations']:,} current financial observations within this snapshot ({counts['observations']:,} saved observation versions).</p><p class="muted">Counts include global lookup/context responses and repeated historical series. They do not represent distinct Gränges reports or independent financial facts. All source identities refer to the frozen packet.</p><details><summary>Dataset inventory</summary><div class="tablewrap"><table><thead><tr><th scope="col">Dataset</th><th scope="col">Saved rows</th></tr></thead><tbody>{dataset_rows}</tbody></table></div></details><details><summary>Source endpoints, acquisition dates and hashes</summary><div class="tablewrap"><table><thead><tr><th scope="col">Provider</th><th scope="col">Endpoint</th><th scope="col">Acquired / provenance</th></tr></thead><tbody>{source_rows}</tbody></table></div></details>{details('Run identity and lifecycle metadata', run)}</section>
<section><h2>Keep the review with its records</h2><p class="muted">Downloads are embedded in this HTML and work without a server. PDFs and raw source bodies remain in the frozen packet; raw model events and image payloads are intentionally omitted from this review.</p><nav>{''.join(downloads)}</nav><p class="small muted">Run directory: <code>{esc(run_dir.relative_to(ROOT) if run_dir.is_relative_to(ROOT) else run_dir)}</code><br>Packet: <code>{esc(packet_file.relative_to(ROOT) if packet_file.is_relative_to(ROOT) else packet_file)}</code></p></section>
<footer class="muted small">Design adapted from <a href="borsdata-research.html">.lavish/borsdata-research.html</a>: DaisyUI luxury palette and the existing Tailwind review layout. Structure follows Lavish explanation and table playbooks. Inline styles preserve readability offline; optional DaisyUI theme styles use a CDN. This is a portable review artifact, not the planned production website.</footer>
</main><script>
const rows = Array.from(document.querySelectorAll('#calc-rows tr'));
const search = document.getElementById('calc-search');
function filter() {{ const q = search.value.toLocaleLowerCase(); let visible = 0;
 for (const row of rows) {{ row.hidden = !row.textContent.toLocaleLowerCase().includes(q); if (!row.hidden) visible++; }}
 document.getElementById('calc-count').textContent = visible + ' of ' + rows.length + ' calculations';
 document.getElementById('no-calculations').hidden = visible !== 0;
}}
search.addEventListener('input', filter); filter();
</script></body></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document)
    return {'output': str(output), 'run_status': status, 'final_report_included': bool(answer), 'calculations': len(calculations), 'delivered_pages': delivered, 'required_pages': total}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=ROOT / 'data/granges-codex/runs/20261101-full')
    parser.add_argument('--packet', type=Path, default=ROOT / 'data/granges-codex/packet-20261101/packet.json')
    parser.add_argument('--output', type=Path, default=ROOT / '.lavish/granges-codex-walkthrough.html')
    parser.add_argument('--allow-incomplete', action='store_true', help='Render a clearly marked progress snapshot without a final answer')
    args = parser.parse_args()
    print(json.dumps(render(args.run, args.packet, args.output, args.allow_incomplete)))


if __name__ == '__main__':
    main()
