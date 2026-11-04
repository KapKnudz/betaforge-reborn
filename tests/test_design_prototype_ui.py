"""Check the prototype's financial display and navigation contract with synthetic data."""
import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node is required for the buildless UI check")
class PrototypeTests(unittest.TestCase):
    def test_browser_helpers(self):
        script = r"""
const assert = require('node:assert/strict');
const p = require('./web/prototypes/company/app.js');
assert.equal(p.priceValue({value:'123',scale:'0.01'}),1.23);
assert.equal(p.fixed(p.priceValue({value:'123',scale:'0.01'})),'1.23');
assert.equal(p.priceValue({value:'123'}),null);
assert.equal(p.displayName('Synthetic AB (PuBl)  '),'Synthetic AB');
assert.equal(p.displayName('Synthetic (publ) Holding'),'Synthetic (publ) Holding');
assert.equal(p.displayName('Synthetic public'),'Synthetic public');
assert.deepEqual(p.periodMeasures(['Period','Profit, USD million','Mixed'],[['2021','-1,234.5','1 / 2'],['R12 · Sep 2026','2','3 / 4']]).map(m=>m.label),['Profit, USD million']);
for(const invalid of ['', '12%','1 / 2','1,2','Infinity','<script>'])assert.equal(p.scalarCell(invalid),null);
assert.deepEqual(p.periodMeasures(['Year','Profit'],[['2021','1'],['2022','2']]),[]);
assert.deepEqual(p.periodMeasures(['Period','Profit'],[['2021','1'],['2022']]),[]);
const quote={value:'123',scale:'0.01',currency:'USD',date:'2026-10-30'};
assert.equal(p.quoteReference(quote,['USD/share','USD/shares']).value,1.23);
for(const invalid of [null,{...quote,scale:null},{...quote,scale:0},{...quote,scale:-1},{...quote,value:'Infinity'},{...quote,value:0},{...quote,currency:null}])assert.equal(p.quoteReference(invalid,['USD/shares']),null);
for(const unit of ['SEK/shares','currency/share','USD','USD million'])assert.equal(p.quoteReference(quote,[unit]),null);
assert.equal(p.dateLabel({value:'2029-11',precision:'month'}),'Nov 2029');
assert.equal(p.dateLabel('2026-10-30'),'30 Oct 2026');
assert.equal(p.inputDisplay({value:'12',scale:'1000000',calculation_value:'12000000',unit:'SEK'},'forecast_ebit'),'12 SEK million');
assert.equal(p.inputDisplay({value:'10',calculation_value:'0.1'},'required_return'),'10%');
assert.equal(p.inputDisplay({},'required_return'),'Unavailable');
assert.equal(p.safeUrl('javascript:alert(1)'),null);
assert.equal(p.safeUrl('https://user:pass@example.com/'),null);
assert.equal(p.safeUrl('https://example.com/a'),'https://example.com/a');
const price={id:'p',source_id:'s',value:'12',unit:'currency/share',scale:'1',currency:'USD',date:'2026-01-01'};
const calc={operation:'financial_formula',formula:'expected_cashflow_irr',input_ids:{price:'p'},inputs:[{...price,field:'price'}],outputs:{irr_percent:{value:'7'}}};
const run={price,original_calculations:[calc],benchmark:{candidate_annualized_return_percent:'7'}};
assert.equal(p.returnUsesReportPrice(run),true);
assert.equal(p.returnUsesReportPrice({...run,price:{...price,value:'13'}}),false);
assert.equal(p.returnUsesReportPrice({...run,original_calculations:[{...calc,outputs:{}}],benchmark:{}}),false);
const refs={sources:[{id:'report',url:'https://example.com/report.pdf'}],calculations:[{id:'calc:one',outputs:{pv:{value:'3'}},inputs:{rate:{id:'input:rate',value:'0.1'}}}]};
assert.equal(p.findReference(refs,'report:p17').page,'17');
assert.equal(p.findReference(refs,'calc:one#pv').field,'pv');
assert.equal(p.findReference(refs,'input:rate').record.value,'0.1');
assert.equal(p.findReference(refs,'missing'),null);
let scrolled=false,focused=false;
const outer={tagName:'DETAILS',open:false,parentElement:null};
const inner={tagName:'DETAILS',open:false,parentElement:outer,scrollIntoView(){scrolled=true},focus(){focused=true}};
p.revealTarget(inner);
assert.ok(outer.open && inner.open && scrolled && focused && inner.tabIndex===-1);
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)

    def test_render_saved_data(self):
        script = r"""
const assert=require('node:assert/strict');
class Node { constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.parentElement=null;this.style={};this.textContent='';} append(...items){for(const item of items){this.children.push(item);if(item instanceof Node)item.parentElement=this;}} replaceChildren(){this.children=[];} setAttribute(name,value){(this.attributes ||= {})[name]=value;} set innerHTML(value){throw Error('HTML rendering is forbidden');} addEventListener(name,fn){this[name]=fn;} scrollIntoView(){} focus(){} }
global.Node=Node;
const roots={content:new Node('div'),status:new Node('p'),'report-version':new Node('span')};
global.document={createElement:t=>new Node(t),createTextNode:t=>{const n=new Node('#text');n.textContent=t;return n;},getElementById:id=>{function find(n){if(n.id===id)return n;for(const c of n.children){const r=find(c);if(r)return r;}return null;}return roots[id] || find(roots.content);}};
const p=require('./web/prototypes/company/app.js');
const input={report_type:'r12',period_start:'2025-10-01',period_end:'2026-09-30'};
const calc={id:'calc:one',formula:'ebit_margin',label:'Current ratio',basis:'Saved basis',report_type:'r12',display_role:'current',...input,inputs:{revenue:input},outputs:{margin_percent:{value:'14.2',unit:'percent'}}};
const run={company:{name:'Synthetic',ticker:'SYN'},analysis_date:'2026-11-01',price:{value:'123',scale:'0.01',currency:'USD'},reader_memo:{summary:'Test',sections:[{title:'Case',paragraphs:[{kind:'interpretation',text:'Saved text',references:['calc:one#margin_percent']}]}],scenarios:[]},probability:{status:'proposed',weights:{base:'1'}},analysis:{scenarios:[{id:'base',name:'Base',present_value:{value:'1.23456789',unit:'USD/shares'},future_target:{value:'2.3456789',unit:'USD/shares'}}],management_comparisons:[{metric_label:'ROCE',relationship:'related',statement_type:'driver',statement:'Outlook',basis:'Issuer definition',statement_date:'2026-01-01',target_period:'2027',references:['calc:one'],actual_references:[]}]},calculations:[calc,{id:'calc:two',formula:'ev_ebit',outputs:{multiple:{value:'12.345',unit:'dimensionless'}}},{id:'calc:missing',formula:'pe',outputs:{multiple:{value:null,unit:'dimensionless'}}}],notes:['Legacy note']};
run.analysis.management_comparisons.push(...[
  ['Direct target','direct','target'],['Related guidance','related','guidance'],['Missing statement','not_stated','not_stated']
].map(([metric_label,relationship,statement_type])=>({metric_label,relationship,statement_type})));
p.render({run,quote:{value:'234',scale:'0.01',currency:'USD',date:'2026-10-30'}});
function all(n){return [n,...n.children.flatMap(all)];} const nodes=all(roots.content), text=nodes.map(n=>n.textContent).join('|');
for(const expected of ['1.23 USD','2.34 USD','Classification: interpretation','14.2 %','R12 · 2025-10-01 to 2026-09-30','2027','Complete source record','Legacy note','12.3 ×','Present value: 1.23 USD/shares · Future target: 2.35 USD/shares','Proposed weights · select a scenario for assumptions'])assert.ok(text.includes(expected),expected);
for(const [metric,type,relationship] of [['ROCE','Driver','Related'],['Direct target','Target','Direct'],['Related guidance','Guidance','Related'],['Missing statement','Not stated','Not stated']]) {
  const article=nodes.find(n=>n.tagName==='ARTICLE' && n.children.some(c=>c.tagName==='H3' && c.textContent===metric));
  assert.ok(article,metric);
  assert.ok(article.children.some(n=>n.textContent==='Statement type: '+type),metric+' statement type');
  assert.ok(article.children.some(n=>n.textContent==='Relationship: '+relationship),metric+' relationship');
}
assert.ok(!text.includes('Unavailable ×'));
const reference=nodes.find(n=>n.textContent==='calc:one#margin_percent' && n.tagName==='A');assert.ok(reference);reference.click({preventDefault(){}});const target=document.getElementById('reference-0');assert.ok(target.open);assert.ok(document.getElementById('evidence').open);
assert.equal(p.periodLabel({report_type:'quarter',period_start:'2026-07-01',period_end:'2026-09-30'}),'QUARTER · 2026-07-01 to 2026-09-30');
assert.equal(p.periodLabel({formula:'operating_roic',inputs:{ebit:input}}),'R12 · 2025-10-01 to 2026-09-30');
assert.notEqual(p.periodLabel(calc),p.periodLabel({report_type:'quarter',period_start:'2026-07-01',period_end:'2026-09-30'}));
const rich=JSON.parse(JSON.stringify(run));
rich.company.name='Synthetic AB (PuBl)';
rich.price={id:'report-price',source_id:'source:price',value:'123',scale:'0.01',currency:'USD',unit:'USD/shares',date:'2026-10-01'};
rich.original_calculations=[{id:'calc:return',operation:'financial_formula',formula:'expected_cashflow_irr',input_ids:{price:'report-price'},inputs:[
  {...rich.price,field:'price',calculation_value:'1.23'},
  {field:'expected_annual_dividend_per_share',value:'0.05',calculation_value:'0.05',unit:'USD/shares'},
  {field:'expected_future_target',value:'2.300000000000000000000000000000000000001',calculation_value:'2.300000000000000000000000000000000000001',unit:'USD/shares'},
  {field:'years',value:'3',calculation_value:'3',unit:'dimensionless'}
],outputs:{irr_percent:{value:'6.73',unit:'percent'},terminal_cash_flow:{value:'2.35',unit:'USD/shares'}}}];
rich.benchmark={candidate_annualized_return_percent:'6.73'};
rich.reader_memo.sections=[
 {id:'drivers',title:'Business drivers',paragraphs:[{text:'### Business mechanics\n\nSaved operating explanation.'},{kind:'fact',references:['calc:one'],text:'### Output and profitability\n\nSaved qualification <script>alert(1)</script>\n\n| Period | Volume, tonnes | Profit, USD million | Mixed basis |\n| --- | --- | --- | --- |\n| 2021 | 1,234 | -2 | 2 / 3 |\n| 2022 | 2,345 | 4 | 3 / 4 |\n| R12 · Sep 2026 | 2,678 | 5 | 4 / 5 |'},{text:'### Reinvestment\n\nSaved capital qualification.'}]},
 {id:'valuation',title:'Current and scenario comparison',paragraphs:[{kind:'interpretation',references:['calc:one'],text:'### What the cases require\n\nSaved valuation method.\n\n| Measure | Current actuals | Bear | Base | Bull |\n| --- | --- | --- | --- | --- |\n| Output | 20 | 21 | 22 | 23 |'},{text:'### Debt and cash details\n\nExact saved qualification.'}]}
];
const richOriginal=JSON.stringify(rich);
p.render({run:rich,quote:{value:'123400',scale:'0.01',currency:'USD',date:'2026-10-30'}});
let richNodes=all(roots.content), richText=richNodes.map(n=>n.textContent).join('|');
assert.equal(richNodes.find(n=>n.tagName==='H1').textContent,'Synthetic AB');
assert.ok(richText.includes('Synthetic AB (PuBl)'),'exact company name retained in evidence');
assert.ok(richText.includes('6.73%'));
assert.ok(richText.includes('At report price · 1 Oct 2026'));
const returnLink=richNodes.find(n=>n.tagName==='A' && n.href==='#return-explanation');assert.ok(returnLink);returnLink.click({preventDefault(){}});
assert.ok(document.getElementById('return-explanation').open);
const returnText=all(document.getElementById('return-explanation')).map(n=>n.textContent).join('|');
for(const expected of ['0.05 USD/shares','2.30 USD/shares','2.35 USD/shares','Initial report price','Years','3','It does not average scenario returns.','calc:return'])assert.ok(returnText.includes(expected),expected);
assert.ok(returnText.includes('Report-price basis: 1.23 USD · 1 Oct 2026'));
assert.ok(returnText.includes('constant model-year-end dividends and a common integer horizon, rather than actual dividend dates'));
const returnTable=all(document.getElementById('return-explanation')).find(n=>n.tagName==='TABLE');
assert.ok(!all(returnTable).some(n=>n.textContent.includes('2.300000000000000000000000000000000000001')));
assert.ok(all(document.getElementById('return-explanation')).some(n=>n.tagName==='PRE' && n.textContent.includes('2.300000000000000000000000000000000000001')));
const yearsRow=all(returnTable).find(n=>n.tagName==='TR' && n.children.some(c=>c.textContent==='Years'));assert.equal(yearsRow.children[1].textContent,'3');
const lines=richNodes.filter(n=>(n.className || '').startsWith('market-reference '));assert.equal(lines.length,2);
assert.equal(lines.find(n=>n.className.endsWith('vertical')).style.left,'100%');
assert.equal(lines.find(n=>n.className.endsWith('horizontal')).style.bottom,'96px');
assert.ok(richNodes.some(n=>n.className==='dot' && parseFloat(n.style.left)<1));
assert.equal(richNodes.filter(n=>n.className==='market-label' && n.textContent==='Market price · 30 Oct 2026 · 1,234.00 USD').length,2);
assert.ok(richText.includes('present-day comparison, not a forecast'));
const subsection=richNodes.filter(n=>n.className==='memo-subsection');assert.ok(subsection[0].open);assert.ok(subsection[1].open);assert.ok(!subsection[2].open);
assert.equal(subsection[1].children[0].textContent,'Output and profitability');
assert.ok(richNodes.some(n=>n.tagName==='H3' && n.textContent==='Business drivers'));
assert.ok(richNodes.some(n=>n.tagName==='P' && n.textContent==='Saved qualification <script>alert(1)</script>'));
assert.ok(!richNodes.some(n=>n.tagName==='SCRIPT'));
const selector=richNodes.find(n=>n.tagName==='SELECT');assert.ok(selector);assert.ok(selector.attributes['aria-label']);
assert.deepEqual(selector.children.map(n=>n.textContent),['Volume, tonnes','Profit, USD million']);
assert.ok(richText.includes('R12 · Sep 2026') && richText.includes('1,234'));
selector.value='1';selector.change();
richNodes=all(roots.content);
assert.ok(richNodes.some(n=>n.className==='trend-bar negative' && parseFloat(n.style.height)>0));
assert.ok(richNodes.some(n=>n.className==='trend-value' && n.textContent==='-2'));
const comparison=richNodes.find(n=>n.tagName==='TH' && n.textContent==='Current actuals');assert.ok(comparison);
let ancestor=comparison.parentElement;while(ancestor && ancestor.id!=='valuation-assumptions'){assert.notEqual(ancestor.tagName,'DETAILS','comparison table prominently visible');ancestor=ancestor.parentElement;}
const exact=richNodes.find(n=>n.tagName==='SUMMARY' && n.textContent==='Exact calculation inputs');assert.ok(exact && !exact.parentElement.open);
for(const heading of ['Business outcome','Valuation assumptions','Why this weight'])assert.ok(richNodes.some(n=>n.tagName==='H4' && n.textContent===heading));
assert.equal(JSON.stringify(rich),richOriginal);
for(const quote of [null,{value:'12',currency:'USD'},{value:'12',scale:'1',currency:'SEK'},{value:'12',scale:'0',currency:'USD'}]) {
 p.render({run:rich,quote});assert.equal(all(roots.content).filter(n=>(n.className || '').startsWith('market-reference ')).length,0);
}
p.render({run:rich,quote:{value:'123',scale:'0.01',currency:'USD',date:'2026-10-30'}});
const scaledNodes=all(roots.content);assert.equal(scaledNodes.filter(n=>n.className==='market-label' && n.textContent==='Market price · 30 Oct 2026 · 1.23 USD').length,2);
const scaledLine=scaledNodes.find(n=>n.className==='market-reference horizontal');assert.ok(parseFloat(scaledLine.style.bottom)>0 && parseFloat(scaledLine.style.bottom)<96);
const mismatch=JSON.parse(JSON.stringify(rich));mismatch.analysis.scenarios[0].future_target.unit='SEK/shares';
p.render({run:mismatch,quote:{value:'123',scale:'0.01',currency:'USD'}});
assert.equal(all(roots.content).filter(n=>(n.className || '').startsWith('market-reference ')).length,1);
const unbound=JSON.parse(JSON.stringify(rich));unbound.price.value='124';p.render({run:unbound});
assert.ok(!document.getElementById('return-explanation'));assert.ok(!all(roots.content).some(n=>n.textContent==='6.73%'));
const invalidHistory=JSON.parse(JSON.stringify(rich));invalidHistory.reader_memo.sections=[{id:'drivers',paragraphs:[{text:'| Period | Composite |\n| --- | --- |\n| 2021 | 1 / 2 |\n| 2022 | 2 / 3 |'}]}];
p.render({run:invalidHistory});assert.ok(!all(roots.content).some(n=>n.tagName==='SELECT'));assert.ok(all(roots.content).some(n=>n.tagName==='TD' && n.textContent==='1 / 2'));
const legacy={company:{name:'Legacy synthetic'},scenarios:[
  {name:'Saved case',value:'81.1234567890123456789',unit:'USD/share',basis:'Original discounted cash basis',calculation_ids:['calc:one#margin_percent']},
  {name:'Saved case',value:'102.34567890123456789',unit:'USD/share',basis:'Original target basis',calculation_ids:['calc:two#multiple']}
],calculations:run.calculations};
const original=JSON.stringify(legacy);
p.render({run:legacy});
const legacyNodes=all(roots.content), legacyText=legacyNodes.map(n=>n.textContent).join('|');
const details=legacyNodes.filter(n=>n.className==='scenario-detail');
assert.equal(details.length,2);
assert.equal(new Set(details.map(n=>n.id)).size,2);
assert.ok(!legacyNodes.some(n=>n.id==='scenario-undefined'));
for(const [i,scenario] of legacy.scenarios.entries()) {
  const row=legacyNodes.find(n=>n.tagName==='TR' && n.children.some(c=>c.children.some(a=>a.tagName==='A' && a.href==='#'+details[i].id)));
  assert.ok(row,'legacy value row '+i);
  assert.ok(all(row).some(n=>n.textContent===scenario.value+' '+scenario.unit));
  assert.ok(all(row).some(n=>n.textContent===scenario.basis));
  const link=all(row).find(n=>n.tagName==='A');link.click({preventDefault(){}});
  assert.ok(details[i].open && document.getElementById('valuation-assumptions').open);
  const detailText=all(details[i]).map(n=>n.textContent).join('|');
  assert.ok(detailText.includes('Saved value: '+scenario.value+' '+scenario.unit));
  assert.ok(detailText.includes('Saved basis: '+scenario.basis));
  const reference=all(details[i]).find(n=>n.tagName==='A' && n.textContent===scenario.calculation_ids[0]);
  assert.ok(reference);reference.click({preventDefault(){}});
  const record=document.getElementById(reference.href.slice(1));
  assert.ok(record.open && document.getElementById('evidence').open);
  assert.ok(all(record).some(n=>n.tagName==='PRE' && n.textContent.includes(scenario.calculation_ids[0].split('#')[0])));
}
assert.ok(legacyText.includes('Saved scenario value'));
assert.equal(legacyNodes.filter(n=>n.className==='dot-row').length,2);
assert.equal(legacyNodes.filter(n=>n.className==='bar-button').length,0);
assert.ok(legacyText.includes('Comparable saved endpoints are unavailable.'));
assert.ok(!legacyText.includes('Present value:') && !legacyText.includes('Future target:'));
assert.ok(!legacyText.includes('Includes discounted dividends') && !legacyText.includes('Excludes separately paid dividends'));
assert.ok(!/\d+% weight/.test(legacyText));
assert.equal(JSON.stringify(legacy),original);
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
