"""Check the prototype's financial display and navigation contract with synthetic data."""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PrototypeTests(unittest.TestCase):
    def test_browser_helpers(self):
        script = r"""
const assert = require('node:assert/strict');
const p = require('./web/prototypes/company/app.js');
assert.equal(p.priceValue({value:'123',scale:'0.01'}),1.23);
assert.equal(p.fixed(p.priceValue({value:'123',scale:'0.01'})),'1.23');
assert.equal(p.priceValue({value:'123'}),null);
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
class Node { constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.parentElement=null;this.style={};this.textContent='';} append(...items){for(const item of items){this.children.push(item);if(item instanceof Node)item.parentElement=this;}} replaceChildren(){this.children=[];} setAttribute(){} addEventListener(name,fn){this[name]=fn;} scrollIntoView(){} focus(){} }
global.Node=Node;
const roots={content:new Node('div'),status:new Node('p'),'report-version':new Node('span')};
global.document={createElement:t=>new Node(t),createTextNode:t=>{const n=new Node('#text');n.textContent=t;return n;},getElementById:id=>{function find(n){if(n.id===id)return n;for(const c of n.children){const r=find(c);if(r)return r;}return null;}return roots[id] || find(roots.content);}};
const p=require('./web/prototypes/company/app.js');
const input={report_type:'r12',period_start:'2025-10-01',period_end:'2026-09-30'};
const calc={id:'calc:one',formula:'ebit_margin',label:'Current ratio',basis:'Saved basis',report_type:'r12',display_role:'current',...input,inputs:{revenue:input},outputs:{margin_percent:{value:'14.2',unit:'percent'}}};
const run={company:{name:'Synthetic',ticker:'SYN'},analysis_date:'2026-11-01',price:{value:'123',scale:'0.01',currency:'USD'},reader_memo:{summary:'Test',sections:[{title:'Case',paragraphs:[{kind:'interpretation',text:'Saved text',references:['calc:one#margin_percent']}]}],scenarios:[]},probability:{status:'proposed',weights:{base:'1'}},analysis:{scenarios:[{id:'base',name:'Base',present_value:{value:'1.23456789',unit:'USD/shares'},future_target:{value:'2.3456789',unit:'USD/shares'}}],management_comparisons:[{metric_label:'ROCE',relationship:'related',statement:'Outlook',basis:'Issuer definition',statement_date:'2026-01-01',target_period:'2027',references:['calc:one'],actual_references:[]}]},calculations:[calc,{id:'calc:two',formula:'ev_ebit',outputs:{multiple:{value:'12.345',unit:'dimensionless'}}},{id:'calc:missing',formula:'pe',outputs:{multiple:{value:null,unit:'dimensionless'}}}],notes:['Legacy note']};
p.render({run,quote:{value:'234',scale:'0.01',currency:'USD',date:'2026-10-30'}});
function all(n){return [n,...n.children.flatMap(all)];} const nodes=all(roots.content), text=nodes.map(n=>n.textContent).join('|');
for(const expected of ['1.23 USD','2.34 USD','Classification: interpretation','14.2 %','R12 · 2025-10-01 to 2026-09-30','Related management statement','2027','Complete source record','Legacy note','12.3 ×','Present value: 1.23 USD/shares · Future target: 2.35 USD/shares','Proposed weights · select a scenario for assumptions'])assert.ok(text.includes(expected),expected);
assert.ok(!text.includes('Unavailable ×'));
const reference=nodes.find(n=>n.textContent==='calc:one#margin_percent' && n.tagName==='A');assert.ok(reference);reference.click({preventDefault(){}});const target=document.getElementById('reference-0');assert.ok(target.open);assert.ok(document.getElementById('evidence').open);
assert.equal(p.periodLabel({report_type:'quarter',period_start:'2026-07-01',period_end:'2026-09-30'}),'QUARTER · 2026-07-01 to 2026-09-30');
assert.equal(p.periodLabel({formula:'operating_roic',inputs:{ebit:input}}),'R12 · 2025-10-01 to 2026-09-30');
assert.notEqual(p.periodLabel(calc),p.periodLabel({report_type:'quarter',period_start:'2026-07-01',period_end:'2026-09-30'}));
"""
        subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
