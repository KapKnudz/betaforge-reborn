'use strict';
const number = value => value === null || value === undefined || value === '' || !Number.isFinite(Number(value)) ? null : Number(value);
const priceValue = record => { const value=number(record && record.value), scale=number(record && record.scale); return value===null || scale===null ? null : value*scale; };
const displayName = name => String(name || 'Company unavailable').replace(/\s*\(publ\)\s*$/i, '').trim();
const shortPeriod = value => String(value).replace(/\b(January|February|March|April|May|June|July|August|September|October|November|December)\b/g, month => month.slice(0,3));
function quoteReference(quote, units) {
  if (!quote || !/^[A-Z]{3}$/.test(quote.currency || '') || number(quote.scale) === null || number(quote.scale) <= 0 || number(quote.value) === null || number(quote.value) <= 0 || !units.length || !units.every(unit => unit === quote.currency+'/share' || unit === quote.currency+'/shares')) return null;
  const value=priceValue(quote);
  return Number.isFinite(value) ? {value, label:'Market price · '+dateLabel(quote.date)+' · '+fixed(value)+' '+quote.currency} : null;
}
function scalarCell(cell) {
  const text=String(cell).trim();
  if (!/^[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/.test(text)) return null;
  return number(text.replace(/,/g,''));
}
function tableCells(line) {
  const source=String(line).trim(), cells=[]; let cell='', trailingSeparator=false;
  for(let index=0;index<source.length;index++) {
    const char=source[index], next=source[index+1];
    if(char==='\\' && (next==='\\' || next==='|')) { cell+=next; index++; trailingSeparator=false; }
    else if(char==='|') { cells.push(cell.trim()); cell=''; trailingSeparator=true; }
    else { cell+=char; trailingSeparator=false; }
  }
  cells.push(cell.trim());
  if(source.startsWith('|'))cells.shift();
  if(trailingSeparator)cells.pop();
  return cells;
}
function periodMeasures(headers, rows) {
  if (headers[0] !== 'Period' || rows.length < 2 || rows.some(row=>row.length!==headers.length || !row[0])) return [];
  return headers.flatMap((label,index)=>index && rows.every(row=>scalarCell(row[index])!==null) ? [{label,index,values:rows.map(row=>scalarCell(row[index]))}] : []);
}
const fixed = value => number(value) === null ? 'Unavailable' : new Intl.NumberFormat('en-GB', {minimumFractionDigits: 2, maximumFractionDigits: 2}).format(number(value));
const display = value => number(value) === null ? 'Unavailable' : new Intl.NumberFormat('en-GB', {maximumFractionDigits: 1}).format(number(value));
const dateLabel = value => {
  const raw = typeof value === 'object' && value ? value.value : value;
  if (!raw) return 'Date unavailable';
  const match = String(raw).match(/^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/);
  if (!match) return String(raw);
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return match[3] ? `${Number(match[3])} ${months[Number(match[2])-1] || match[2]} ${match[1]}` : match[2] ? `${months[Number(match[2])-1] || match[2]} ${match[1]}` : match[1];
};
function safeUrl(value) { try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password ? url.href : null; } catch (_) { return null; } }
function returnCalculation(run) {
  const returns = (run.original_calculations || []).filter(c => c.operation === 'financial_formula' && c.formula === 'expected_cashflow_irr');
  const selected = (run.benchmark || {}).return_calculation_id;
  const candidates = selected === undefined ? returns : returns.filter(c => c.id === selected);
  return candidates.length === 1 ? candidates[0] : null;
}
function returnUsesReportPrice(run) {
  const price = run.price, calc = returnCalculation(run);
  if (!price || !price.id || !price.source_id || !calc) return false;
  const inputs = (calc.inputs || []).filter(i => i.field === 'price');
  return number(((calc.outputs || {}).irr_percent || {}).value) !== null && inputs.length === 1 && (calc.input_ids || {}).price === price.id && inputs[0].id === price.id && ['value','unit','scale','currency','source_id'].every(k => inputs[0][k] === price[k]) && (inputs[0].date || inputs[0].period_end) === price.date && (((calc.outputs || {}).irr_percent || {}).value === (run.benchmark || {}).candidate_annualized_return_percent);
}
function inputDisplay(input, key) {
  const value = number(input && input.calculation_value);
  if (value === null) return 'Unavailable';
  if (key === 'required_return') return display(value * 100) + '%';
  if (key === 'forecast_ebit') return display(value / 1000000) + ' ' + (input.currency || input.unit || 'currency') + ' million';
  if (key === 'exit_multiple') return display(value) + '×';
  return display(value) + (input.unit && input.unit !== 'dimensionless' ? ' ' + input.unit : '');
}
const metricDefinitions=[['ebit_margin','EBIT margin','margin_percent'],['incremental_ebit_margin','Incremental EBIT margin','incremental_margin_percent'],['operating_roic','Operating ROIC','roic_percent'],['group_cash_conversion','Group cash conversion','conversion_percent'],['ev_ebit','EV / EBIT','multiple'],['pe','Diluted P/E','multiple']];
function calculationPeriod(calc) { return calc.period_end || Object.values(calc.inputs || {}).map(input=>input && typeof input==='object' ? (/^\d{4}-\d{2}-\d{2}$/.test(input.period_end || '') ? input.period_end : /^\d{4}$/.test(String(input.year)) ? String(input.year) : '') : '').sort().pop() || ''; }
const periodFields={ebit_margin:'revenue',incremental_ebit_margin:'revenue_current',operating_roic:'ebit',group_cash_conversion:'cfo',ev_ebit:'ebit',pe:'diluted_eps'};
function currentCalculation(calc) { const input=(calc.inputs || {})[periodFields[calc.formula]]; return calc.display_role==='current' && ['r12','quarter'].includes(calc.report_type) && calc.period_start && calc.period_end && input && input.report_type===calc.report_type && input.period_start===calc.period_start && input.period_end===calc.period_end; }
function periodLabel(calc) { const input=(calc.inputs || {})[periodFields[calc.formula]] || {}, type=calc.report_type || input.report_type, start=calc.period_start || input.period_start, end=calc.period_end || input.period_end; return [type ? type.toUpperCase() : null,[start,end].filter(Boolean).join(' to ') || calc.year || calculationPeriod(calc)].filter(Boolean).join(' · ') || 'Period not recorded'; }
function selectedMetrics(calculations) { return metricDefinitions.flatMap(([formula,label,primary])=>{const candidates=calculations.filter(c=>c.formula===formula);const priority=c=>currentCalculation(c) ? (c.report_type==='r12'?2:1):0;candidates.sort((a,b)=>priority(b)-priority(a) || calculationPeriod(b).localeCompare(calculationPeriod(a)));return candidates.length ? [{calc:candidates[0],label,primary}] : [];}); }
function findReference(run, reference) {
  const sourceMatch=String(reference).match(/^(.*):p(\d+)$/);
  if(sourceMatch) { const source=(run.sources||[]).find(s=>s.id===sourceMatch[1]); return source ? {kind:'source', record:source, page:sourceMatch[2]} : null; }
  const [id, field]=String(reference).split('#');
  function find(value) { if(!value || typeof value!=='object') return null; if(value.id===id) return value; for(const item of Object.values(value)) { const found=find(item); if(found) return found; } return null; }
  const record=find({calculations:run.calculations, original_calculations:run.original_calculations, saved_records:run.saved_records, price:run.price, sources:run.sources});
  return record ? {kind:'record',record,field:field || null} : null;
}
function revealTarget(node) { if (!node) return; let parent=node; while(parent) { if(parent.tagName==='DETAILS') parent.open=true; parent=parent.parentElement; } node.tabIndex=-1; node.scrollIntoView({block:'start'}); node.focus({preventScroll:true}); }
if (typeof module !== 'undefined') module.exports = {tableCells, displayName, quoteReference, scalarCell, periodMeasures, number, display, fixed, priceValue, dateLabel, safeUrl, returnUsesReportPrice, inputDisplay, findReference, revealTarget, calculationPeriod, currentCalculation, periodLabel, selectedMetrics};
if (typeof document !== 'undefined') {
const el = (tag, cls, text) => { const node = document.createElement(tag); if (cls) node.className = cls; if (text !== undefined && text !== null) node.textContent = text; return node; };
const append = (parent, ...children) => { parent.append(...children); return parent; };
const raw = value => el('pre','raw',JSON.stringify(value, null, 2));
function detail(title, child, id) { const d=el('details'); if(id) d.id=id; append(d,el('summary','',title),child); return d; }
function linkTarget(id, label) { const a=el('a','',label); a.href='#'+id; a.addEventListener('click', e => {e.preventDefault(); openTarget(id);}); return a; }
function openTarget(id) { revealTarget(document.getElementById(id)); }
function fact(label, value, note, record) { const row=el('div','fact'); const figure=el('strong','',value); if(record) figure.title='Raw value: '+String(record.value ?? 'Unavailable')+' · scale: '+String(record.scale ?? 'Unavailable'); append(row,el('span','',label),figure,el('small','',note)); return row; }
function chapter(id, title, description) { const d=el('details','chapter'); d.id=id; const s=el('summary'); append(s,el('strong','',title),el('span','',description)); const body=el('div','chapter-body'); append(d,s,body); return [d,body]; }
function table(headers, rows) { const wrap=el('div','table-wrap'), t=el('table'), head=el('thead'), tr=el('tr'), body=el('tbody'); headers.forEach(h=>tr.append(el('th','',h))); head.append(tr); rows.forEach(row=>{const r=el('tr');row.forEach(cell=>{const td=el('td'); if(cell instanceof Node)td.append(cell);else td.textContent=cell; r.append(td);});body.append(r);});append(t,head,body);wrap.append(t);return wrap; }
function periodTable(headers, rows, id) {
 const measures=periodMeasures(headers,rows), saved=table(headers,rows);
 if (!measures.length) return saved;
 const wrapper=el('div','history'), label=el('label','trend-label','Measure'), select=el('select'), chart=el('div','trend-chart');
 select.id=id; label.htmlFor=id; select.setAttribute('aria-label','Measure');
 measures.forEach((measure,i)=>{const option=el('option','',measure.label);option.value=String(i);select.append(option);});
 function draw() {
  const measure=measures[Number(select.value) || 0], min=Math.min(0,...measure.values), max=Math.max(0,...measure.values), range=max-min || 1;
  chart.replaceChildren(); chart.setAttribute('aria-label',measure.label+' · exact saved period values');
  chart.append(el('p','trend-unit',measure.label));
  const columns=el('div','trend-columns');
  measure.values.forEach((value,i)=>{const column=el('div','trend-column'), plot=el('div','trend-plot'), bar=el('span','trend-bar'+(value<0?' negative':'')), zero=el('span','trend-zero');
   zero.style.bottom=(-min/range*100)+'%'; bar.style.bottom=((Math.min(0,value)-min)/range*100)+'%';bar.style.height=(Math.abs(value)/range*100)+'%';
   const period=el('span','trend-period',shortPeriod(rows[i][0]));period.title=rows[i][0];append(plot,zero,bar); append(column,el('span','trend-value',rows[i][measure.index]),plot,period);columns.append(column);
  }); chart.append(columns);
 }
 select.addEventListener('change',draw); draw(); append(wrapper,label,select,chart,el('p','caption','Exact saved values and period labels. See the source table and saved qualifications for period length and basis.'),detail('Source table',saved));return wrapper;
}
function readableReport(markdown, id) {
 const node=el('div','report-body'), lines=String(markdown || '').split(/\r?\n/); let paragraph=[], tableIndex=0;
 const flush=()=>{if(paragraph.length){node.append(el('p','saved-text',paragraph.join('\n')));paragraph=[];}};
 for(let index=0;index<lines.length;index++) {
  const line=lines[index], heading=line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*$/);
  if(heading){flush();node.append(el('h4','',heading[2]));}
  else if(line.includes('|') && index+1<lines.length && tableCells(lines[index+1]).length && tableCells(lines[index+1]).every(cell=>/^:?-{3,}:?$/.test(cell))) {
   flush(); const headers=tableCells(line), rows=[];index+=2;
   while(index<lines.length && lines[index].includes('|') && lines[index].trim()){rows.push(tableCells(lines[index]));index++;}index--;
   node.append(periodTable(headers,rows,id+'-measure-'+tableIndex++));
  } else if(!line.trim())flush(); else paragraph.push(line);
 }
 flush();return node;
}
function render(data) {
 const run=data.run || {}, quote=data.quote, market=quoteReference(quote,quote ? [quote.currency+'/shares'] : []), company=run.company || {}, memo=run.reader_memo || run.analysis || {}, legacy=!run.analysis, scenarios=((run.analysis && run.analysis.scenarios) || run.scenarios || []).map((s,i)=>({...s,id:s.id || 'legacy-'+i})), calculations=run.calculations || [];
 const root=document.getElementById('content'); root.replaceChildren(); document.getElementById('report-version').textContent=dateLabel(run.analysis_date); document.getElementById('status').textContent='';
 const title=el('div','title-row'), name=el('h1','',displayName(company.name)); name.append(el('span','ticker',company.ticker || '')); append(title,append(el('div'),el('div','eyebrow','Company research'),name),el('div','date','Analysis · '+dateLabel(run.analysis_date))); root.append(title);
 const overview=el('div','overview'), memoBlock=el('section','memo'), facts=el('aside','facts'); append(memoBlock,el('h2','','Investment conclusion'),el('p','',memo.summary || run.conclusion || 'No conclusion saved.'),linkTarget('investment-case','Read the investment case →'));
 const price=run.price || {}; facts.append(fact('Latest market price',market ? fixed(market.value)+' '+quote.currency : 'Unavailable',market ? 'Daily close · '+dateLabel(quote.date) : 'No valid stored quote supplied',quote));
 facts.append(fact('Report price',fixed(priceValue(price))+' '+(price.currency || price.unit || ''),dateLabel(price.date),price));
 const returnBound=returnUsesReportPrice(run), ret=(run.benchmark || {}).candidate_annualized_return_percent; const returnFact=fact('Conditional annual return',returnBound ? fixed(ret)+'%' : 'Unavailable',returnBound ? 'At report price · '+dateLabel(price.date) : 'Report-price binding unavailable'); if(returnBound)returnFact.append(linkTarget('return-explanation','How this return is calculated'));facts.append(returnFact);
 const base=scenarios.find(s=>s.id==='base') || scenarios[0] || {}, calc=calculations.find(c=>c.id===base.valuation_calculation_id) || {}; facts.append(fact('Required return',inputDisplay((calc.inputs || {}).required_return,'required_return'),'Report assumption'));
 append(overview,memoBlock,facts); root.append(overview);
 const charts=el('section','charts'), head=el('div','chart-head'); append(head,el('h2','','Valuation scenarios'),el('span','',run.probability && run.probability.status==='proposed' ? 'Proposed weights · select a scenario for assumptions' : 'Select a scenario to inspect its assumptions')); charts.append(head); const grid=el('div','chart-grid');
 for(const [key,label,dateKey] of [['present_value','Present value','present_value_date'],['future_target','Future share target','target_date']]) {
  const endpoint=s=>legacy && key==='present_value' ? s : s[key] || {};
  const panel=el('div','chart'), vals=scenarios.map(s=>number(endpoint(s).value)), unitList=scenarios.map(s=>endpoint(s).unit), units=new Set(unitList), comparable=scenarios.length && vals.every(v=>v!==null && v>=0) && units.size===1 && !units.has(undefined), reference=comparable && !legacy && market && unitList.every(unit=>unit===quote.currency+'/share' || unit===quote.currency+'/shares') ? market : null, max=Math.max(1,...vals.filter(v=>v!==null),reference ? reference.value : 0), position=value=>value/max*100;
  const dates=legacy && key==='present_value' ? 'See saved valuation basis' : [...new Set(scenarios.map(s=>dateLabel(s[dateKey])))].join(' / '); append(panel,el('h3','',legacy && key==='present_value' ? 'Saved scenario value' : label),el('p','sub',dates+' · '+([...units][0] || 'unit unavailable')));
  if(!comparable) panel.append(el('p','muted','Comparable saved endpoints are unavailable.'));
  else if(key==='present_value') {
   const plot=el('div','dot-plot');
   scenarios.forEach((s,i)=>{const button=el('button','dot-row');button.type='button';button.title=String(endpoint(s).value)+' '+endpoint(s).unit;button.setAttribute('aria-label',s.name+' · '+display(vals[i])+' '+endpoint(s).unit+' · open assumptions');const n=el('span','scenario-name',s.name), w=number(((run.probability || {}).weights || {})[legacy?s.name.toLowerCase():s.id]);n.append(el('small','',w===null?'Weight unavailable':display(w*100)+'% weight'));const track=el('span','dot-track'), dot=el('span','dot');dot.style.left=position(vals[i])+'%';track.append(dot);append(button,n,track,el('span','value',display(vals[i])));button.addEventListener('click',()=>openTarget('scenario-'+s.id));plot.append(button);});
   if(reference){const layer=el('div','dot-reference-layer'), line=el('span','market-reference vertical');line.style.left=position(reference.value)+'%';line.title=reference.label;line.setAttribute('aria-label',reference.label);layer.append(line);plot.append(layer);}panel.append(plot);
   const axis=el('div','dot-axis');append(axis,el('span','','0'),el('span','',display(max)));panel.append(axis);
  } else {const bars=el('div','bars'), labels=el('div','bar-labels');scenarios.forEach((s,i)=>{const b=el('button','bar-button');b.type='button';b.title=String(s[key].value)+' '+s[key].unit;b.setAttribute('aria-label',s.name+' · '+display(vals[i])+' '+s[key].unit+' · open assumptions');const bar=el('span','bar');bar.style.height=(position(vals[i])/100*96)+'px';append(b,el('span','bar-value',display(vals[i])),bar);b.addEventListener('click',()=>openTarget('scenario-'+s.id));bars.append(b);labels.append(el('span','',s.name));});
   if(reference){const line=el('span','market-reference horizontal');line.style.bottom=(position(reference.value)/100*96)+'px';line.title=reference.label;line.setAttribute('aria-label',reference.label);bars.append(line);}append(panel,bars,labels);panel.append(el('p','chart-axis','Scale: 0–'+display(max)+' '+unitList[0]));}
  if(reference)panel.append(el('p','market-label',reference.label));
  panel.append(el('p','caption',legacy ? 'Only saved values are shown; see the recorded valuation basis.' : key==='present_value'?'Includes discounted dividends and the discounted share target.':'Excludes separately paid dividends. The market price is a present-day comparison, not a forecast. Each chart uses its own scale.'));grid.append(panel);
 } charts.append(grid);root.append(charts);
 const disclosures=el('div','disclosures'); const [investment,investmentBody]=chapter('investment-case','Investment case','Business, opportunity and principal risks'); const [valuation,valuationBody]=chapter('valuation-assumptions','Valuation assumptions','Scenario inputs, weights and reasoning'); const [financials,financialBody]=chapter('financials','Financials and management','Key ratios and management outlook'); const [evidence,evidenceBody]=chapter('evidence','Evidence','Original analysis, sources and calculation records'); append(disclosures,investment,valuation,financials,evidence);root.append(disclosures);
 const referenceIds=new Map(); function provenance(kind, refs) { const content=el('div'); content.append(el('p','muted','Classification: '+(kind || 'Not stated'))); const list=el('ul','source-list'); (refs || []).forEach(ref=>{if(!referenceIds.has(ref)) referenceIds.set(ref,'reference-'+referenceIds.size);const li=el('li');li.append(linkTarget(referenceIds.get(ref),ref));list.append(li);}); if(!list.children.length)content.append(el('p','muted','No references saved.')); else content.append(list);return detail('Sources & calculations',content); }
 if(returnBound) {
  const calculation=returnCalculation(run), content=el('div'), inputs=calculation.inputs || [], outputs=calculation.outputs || {};
  const savedInput=field=>inputs.find(input=>input.field===field) || {}, savedValue=(record,integer=false)=>number(record.calculation_value ?? record.value)===null ? 'Unavailable' : (integer ? String(number(record.calculation_value ?? record.value)) : fixed(record.calculation_value ?? record.value))+(record.unit && record.unit!=='dimensionless'?' '+record.unit:'')+(record.calculation_value===undefined && record.scale && record.scale!=='1'?' · scale '+record.scale:'');
  append(content,el('p','','The saved model weights each scenario’s dividend and terminal share target at each payment date, then solves the annual rate that equates those cash flows with the report price. It does not average scenario returns. The saved formula uses constant model-year-end dividends and a common integer horizon, rather than actual dividend dates.'),el('p','','Report-price basis: '+fixed(priceValue(price))+' '+(price.currency || '')+' · '+dateLabel(price.date)+'. The latest quote does not recalculate this result.'),table(['Saved cash-flow input / output','Value'],[['Initial report price',savedValue(savedInput('price'))],['Expected annual dividend / share',savedValue(savedInput('expected_annual_dividend_per_share'))],['Expected terminal share target',savedValue(savedInput('expected_future_target'))],['Years',savedValue(savedInput('years'),true)],['Final receipt · dividend plus share target',savedValue(outputs.terminal_cash_flow || {})],['Saved annual return',fixed(outputs.irr_percent.value)+'%']]),provenance('Saved expected cash-flow IRR',[calculation.id].filter(Boolean)),detail('Exact return calculation',raw(calculation)));
  valuationBody.append(detail('How the conditional annual return is calculated',content,'return-explanation'));
 }
 const sections=memo.sections || []; let businessOpened=false; sections.forEach((s,sectionIndex)=>{const article=el('article','memo-section'), isValuation=s.id==='valuation'; article.append(el('h3','',s.title || s.id || 'Saved research')); (s.paragraphs || []).forEach((p,paragraphIndex)=>{const text=typeof p==='string'?p:p.text || '', heading=text.match(/^###\s+([^\n]+)\n+/), body=readableReport(heading ? text.slice(heading[0].length) : text,'memo-'+sectionIndex+'-'+paragraphIndex); if(typeof p==='object' && p)body.append(provenance(p.kind,p.references)); if(isValuation && paragraphIndex===0){if(heading)article.append(el('h4','',heading[1]));article.append(body);}else {const d=detail(heading ? heading[1] : (s.title || s.id || 'Saved research')+(s.paragraphs.length>1?' · '+(paragraphIndex+1):''),body); d.className='memo-subsection';if(!isValuation && (!businessOpened || Array.from(body.children).some(child=>child.className==='history'))){d.open=true;businessOpened=true;}article.append(d);}}); (isValuation?valuationBody:investmentBody).append(article);}); if(!sections.length)investmentBody.append(el('p','','No structured investment case saved.'));
 const keys=[['forecast_ebit','Forecast EBIT'],['exit_multiple','Exit multiple'],['years','Years'],['annual_dividend_per_share','Annual dividend / share'],['required_return','Required return']]; valuationBody.append(detail('Exact calculation inputs',legacy ? table(['Scenario','Saved value','Saved basis'],scenarios.map(s=>[linkTarget('scenario-'+s.id,s.name),String(s.value)+' '+s.unit,s.basis])) : table(['Scenario',...keys.map(x=>x[1])],scenarios.map(s=>{const c=calculations.find(x=>x.id===s.valuation_calculation_id)||{};return [linkTarget('scenario-'+s.id,s.name),...keys.map(([key])=>{const input=(c.inputs||{})[key]||{}, span=el('span','',inputDisplay(input,key));span.title='Saved input: '+JSON.stringify(input);return span;})];}))));
 scenarios.forEach(s=>{const prose=(memo.scenarios||[]).find(x=>x.id===s.id)||s, content=el('div'); if(legacy) append(content,el('p','','Saved value: '+String(s.value)+' '+s.unit),el('p','','Saved basis: '+s.basis),provenance('Scenario calculations',s.calculation_ids)); else {[['rationale','Business outcome'],['assumption_rationale','Valuation assumptions'],['probability_rationale','Why this weight']].forEach(([k,label])=>append(content,el('h4','',label),el('p','',prose[k] || 'Not stated.')));const endpoints=el('p','muted','Present value: '+fixed((s.present_value||{}).value)+' '+String((s.present_value||{}).unit || '')+' · Future target: '+fixed((s.future_target||{}).value)+' '+String((s.future_target||{}).unit || '')); endpoints.title='Exact saved endpoints: '+JSON.stringify({present_value:s.present_value,future_target:s.future_target}); content.append(endpoints);content.append(provenance('Scenario rationale',prose.references));} const d=detail(s.name,content,'scenario-'+s.id);d.className='scenario-detail';valuationBody.append(d);});
 financialBody.append(el('h3','','Saved financial calculations')); const metrics=selectedMetrics(calculations); financialBody.append(table(['Measure','Period','Saved result'],metrics.map(({calc:c,label,primary})=>{const out=(c.outputs||{})[c.primary_output || primary]||{}, unit=out.unit==='percent'?'%':['fraction','dimensionless'].includes(out.unit) && ['ev_ebit','pe'].includes(c.formula)?'×':out.unit||'';const cell=el('span','',display(out.value)+(number(out.value)!==null && unit ? ' '+unit : ''));cell.title=JSON.stringify(out);return [label,periodLabel(c),cell];}))); if(!metrics.length)financialBody.append(el('p','muted','No saved financial metrics available.')); metrics.forEach(({calc:c,label})=>{const content=el('div');append(content,el('p','',c.label || c.id),el('p','',c.basis || 'Basis not stated.'),provenance('Calculation',[c.id].filter(Boolean)));financialBody.append(detail(label+' · calculation basis',content));});
 financialBody.append(el('h3','','Management comparisons')); ((run.analysis||{}).management_comparisons||[]).forEach(m=>{const article=el('article');append(article,el('h3','',m.metric_label),el('p','muted','Statement type: '+(({target:'Target',guidance:'Guidance',driver:'Driver',not_stated:'Not stated'})[m.statement_type] || 'Not stated')),el('p','muted','Relationship: '+(({direct:'Direct',related:'Related',not_stated:'Not stated'})[m.relationship] || 'Not stated')),el('p','',m.statement),el('p','','Definition: '+(m.basis || 'Not stated')),el('p','','Saved actual: '+(m.actual || 'Not stated')),el('p','muted','Statement date: '+dateLabel(m.statement_date)+' · Horizon: '+(m.target_period || 'Not stated')),provenance('Management comparison',[...(m.references || []),...(m.actual_references || [])])); financialBody.append(article);});
 evidenceBody.append(el('p','muted','The independent economic review applies to the canonical analysis. The reader edition is an editorial rewrite.')); const references=el('div'); referenceIds.forEach((target,ref)=>{const found=findReference(run,ref), item=el('details');item.id=target;item.append(el('summary','',ref));if(found && found.kind==='source'){const url=safeUrl(found.record.url);if(url){const a=el('a','','Open source · page '+found.page);const pageUrl=new URL(url);pageUrl.hash='page='+found.page;a.href=pageUrl.href;a.target='_blank';a.rel='noopener noreferrer';item.append(a);}item.append(raw(found.record));}else item.append(raw(found ? found.record : 'Reference record unavailable'));references.append(item);});evidenceBody.append(detail('Referenced sources and records',references));
 evidenceBody.append(detail('Canonical report',raw(run.analysis || run.narrative || 'Unavailable')),detail('Independent review',raw(run.analysis_review || 'Unavailable')));
 const sources=el('ul','source-list');(run.sources||[]).forEach(s=>{const li=el('li'), url=safeUrl(s.url);if(url){const a=el('a','',s.title||s.id);a.href=url;a.target='_blank';a.rel='noopener noreferrer';li.append(a);}else li.append(el('span','',s.title||s.id));li.append(document.createTextNode(' · '+(s.id||'')+' · '+(s.pages ? s.pages+' pages' : 'page count unavailable')));sources.append(li);});evidenceBody.append(detail('Sources and page references',append(el('div'),sources,raw((run.analysis||{}).sections || []))),detail('Calculations and raw records',raw({calculations:run.calculations,original_calculations:run.original_calculations,saved_records:run.saved_records,price:run.price,quote})),detail('Report provenance',raw(run.provenance || {})),detail('Complete source record',raw(run))); if(quote) evidenceBody.append(detail('Complete quote record',raw(quote)));
}
if (typeof module !== 'undefined') module.exports.render=render;
if (typeof module === 'undefined' || !module.exports) fetch('/data.json').then(r=>{if(!r.ok)throw Error('Report unavailable');return r.json();}).then(render).catch(()=>{document.getElementById('status').textContent='The saved report could not be loaded.';});
}
