"""Bounded tools over a frozen company evidence packet; no provider credentials."""
from __future__ import annotations

import base64
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone

from betaforge.financials import FORMULAS, evaluate

READ_LIMIT = 45000


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_analysis_guides(base, entries):
    """Validate supplied frozen guides without consulting their live source paths."""
    if not isinstance(entries, list) or not entries:
        raise ValueError('Analysis guides must be a nonempty list')
    texts, sources = {}, set()
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) != {'role', 'source_path', 'path', 'sha256'} or
                entry['role'] not in ('analyst', 'reviewer')):
            raise ValueError('Invalid analysis guide role or metadata')
        for key in ('path', 'source_path'):
            value = entry[key]
            if (not isinstance(value, str) or not value or '\\' in value or
                    Path(value).is_absolute() or '..' in Path(value).parts or
                    Path(value).as_posix() != value or value == '.'):
                raise ValueError('Invalid analysis guide path')
        path = (base / entry['path']).resolve()
        if not path.is_relative_to(base):
            raise ValueError('Analysis guide path escapes packet')
        if entry['path'] in texts or entry['source_path'] in sources:
            raise ValueError('Duplicate analysis guide path or source')
        if not isinstance(entry['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', entry['sha256']):
            raise ValueError('Invalid analysis guide hash')
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != entry['sha256']:
            raise ValueError('Analysis guide hash mismatch')
        texts[entry['path']] = body.decode('utf-8')
        sources.add(entry['source_path'])
    return texts


def write_json(path, value):
    temporary = Path(str(path) + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False))
    temporary.replace(path)


def decimal(value):
    if isinstance(value, bool):
        raise ValueError('Boolean is not a financial number')
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError('Invalid decimal') from error
    if not result.is_finite() or len(str(value)) > 200:
        raise ValueError('Provide a finite bounded decimal')
    return result


def unit_dimensions(record):
    unit=str(record.get('unit','unknown')).strip()
    currency=record.get('currency')
    if unit in ('currency','currency/share'):
        if not currency:raise ValueError('Currency is unresolved; cannot calculate this observation')
        unit=unit.replace('currency',currency)
    aliases={'ratio':'','dimensionless':'','fraction':'','multiple':'','x':'','number':'','%':'percent','share':'shares'}
    unit=aliases.get(unit.lower(),unit)
    if unit.lower() in ('unknown','provider_defined') or re.search(r'(?i)^(msek|million|sek million)',unit):
        raise ValueError('Use a defined base unit; currency values in millions require scale=1000000')
    if not unit:return {}
    result={}
    for side,part in enumerate(unit.split('/')):
        if side>1:raise ValueError('Unsupported unit expression')
        for token in part.split('*'):
            token=token.strip();token=aliases.get(token.lower(),token)
            if not token:continue
            match=re.fullmatch(r'([A-Za-z_]+)(?:\^(-?\d+))?',token)
            if not match:raise ValueError('Unsupported unit; use base units such as SEK, shares or dimensionless')
            name,power=match.groups();power=int(power or 1)*(1 if side==0 else -1)
            result[name]=result.get(name,0)+power
    return {k:v for k,v in result.items() if v}


def unit_label(dimensions):
    def terms(positive):
        return '*'.join(k+(f'^{abs(v)}' if abs(v)!=1 else '') for k,v in sorted(dimensions.items()) if (v>0)==positive)
    numerator,denominator=terms(True),terms(False)
    return (numerator or 'dimensionless')+('/'+denominator if denominator else '')


def schema(name, description, properties, required=()):
    return {'type': 'function', 'name': name, 'description': description,
            'inputSchema': {'type': 'object', 'properties': properties,
                            'required': list(required), 'additionalProperties': False}}


STRING = {'type': 'string'}
INT = {'type': 'integer', 'minimum': 1}
TOOL_SCHEMAS = [
    schema('read_report', 'Read consecutive complete physical PDF pages, maximum 45000 characters. Follow next_page until null for each required report. Search snippets do not satisfy required reading.',
           {'report_id': STRING, 'start_page': INT}, ['report_id', 'start_page']),
    schema('search_reports', 'Literal text search across saved reports. At most 30 snippets; these do not count as page reads.',
           {'query': STRING, 'report_id': STRING}, ['query']),
    schema('view_report_page', 'View the original physical PDF page as an image to verify tables, figures and extraction problems.',
           {'report_id': STRING, 'page': INT}, ['report_id', 'page']),
    schema('get_financials', 'Query frozen dated financial observations. Values retain original unit/scale and provider basis; calculate automatically multiplies observation value by scale to use base units. Paginate with offset.',
           {'report_type': STRING, 'fields': {'type': 'array', 'items': STRING},
            'limit': {'type': 'integer', 'minimum': 1, 'maximum': 200},
            'offset': {'type': 'integer', 'minimum': 0}}),
    schema('get_dataset', 'Inspect bounded frozen context records such as prices, KPI histories, metadata and events. Use get_catalogue for dataset names. Paginate with offset.',
           {'dataset': STRING, 'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100},
            'offset': {'type': 'integer', 'minimum': 0}}, ['dataset']),
    schema('get_source', 'Resolve a frozen source ID to provenance, endpoint, nonsecret parameters and original file hash.',
           {'source_id': STRING}, ['source_id']),
    schema('get_catalogue', 'Return report catalogue, frozen dataset catalogue, reading coverage, and saved calculation/input IDs.', {}),
    schema('get_calculation_definitions', 'Show the fixed financial formulas, required base units, options, outputs and limitations. Use these grouped formulas for valuation and diagnostics.', {}),
    schema('record_input', 'Save a numeric input before calculation. Specify base unit and scale (1000000 for a value stated in millions); calculation multiplies value by scale. Assumptions require a clear label. Report inputs require physical page and a verbatim quote present in saved text; label remains an analyst extraction, not independently verified. Prefer saved observation IDs when available.',
           {'value': STRING, 'label': STRING, 'unit': STRING, 'scale': STRING,
            'kind': {'type': 'string', 'enum': ['assumption', 'report']},
            'report_id': STRING, 'page': INT, 'quote': STRING}, ['value', 'label', 'unit', 'kind']),
    schema('calculate_financial', 'Evaluate one named financial formula using saved IDs. Each source scale is applied once. One record contains the full formula, named inputs, all intermediate outputs and gaps. Cite calc:ID#output_name to reuse a named output. Money currently requires SEK. State period, ownership scope and reported/adjusted basis explicitly.',
           {'formula': {'type':'string','enum':list(FORMULAS)},
            'input_ids': {'type':'object','additionalProperties':STRING,'maxProperties':24},
            'options': {'type':'object','properties': {
                'comparable_periods':{'type':'boolean'}, 'revenue_passthrough':{'type':'boolean'},
                'balance_basis':{'type':'string','enum':['average','closing']},
                'cash_flow_scope':{'type':'string','enum':['parent_common','firm']},
                'denominator_scope':{'type':'string','enum':['market_cap','enterprise_value']}}, 'additionalProperties':False},
            'label':STRING,'basis':STRING}, ['formula','input_ids','label','basis']),
    schema('calculate', 'Calculate using saved observation/input/calculation IDs, not prose numbers. Observation values are AUTOMATICALLY multiplied by stored scale; saved calculations are already in base units (SEK, actual shares). Do not apply scale again. Operations add/multiply accept 2-100 IDs; subtract/divide/growth_percent/power exactly two. Output unit is explicit and audited; reconcile units before calling.',
           {'operation': {'type': 'string', 'enum': ['add', 'subtract', 'multiply', 'divide', 'growth_percent', 'power']},
            'input_ids': {'type': 'array', 'items': STRING, 'minItems': 2, 'maxItems': 100},
            'label': STRING, 'unit': STRING}, ['operation', 'input_ids', 'label', 'unit']),
    schema('finish_research_round', 'After required reading, mark one follow-up investigation complete. Cite newly used evidence IDs and summarize what changed; at most 10 rounds or two consecutive rounds with no new evidence. This is an investigation boundary, not a count of individual tool calls.',
           {'summary': STRING, 'evidence_ids': {'type': 'array', 'items': STRING},
            'ready_to_finalize': {'type': 'boolean'}}, ['summary', 'evidence_ids', 'ready_to_finalize']),
]


STRUCTURED_TOOL_SCHEMAS = [
    schema('get_saved_record', 'Inspect one saved input, calculation (including all named outputs), or selected-company observation by exact ID.',
           {'identifier': STRING}, ['identifier']),
    schema('submit_analysis', 'Submit the complete structured report after required reading. Values are copied from saved valuation_case outputs. Syntax and source identity validity are separate from economic review. See supplied STRUCTURED REPORT CONTRACT.',
           {'report': {'type': 'object'}}, ['report']),
]


class EvidenceTools:
    def __init__(self, packet_path, run_dir, resume=False, structured=False):
        from betaforge.storage import EvidenceStore
        self.packet_path = Path(packet_path).resolve()
        self.packet = json.loads(self.packet_path.read_text())
        if not isinstance(self.packet, dict) or type(self.packet.get('instrument_id')) is not int or self.packet['instrument_id'] <= 0:
            raise ValueError('Packet requires an explicit positive integer instrument_id')
        self.instrument = self.packet['instrument_id']
        self.structured = structured
        self.run_dir = Path(run_dir).resolve()
        self.run_dir.mkdir(parents=True, exist_ok=True)
        def resolve(value):
            path = Path(value)
            return path.resolve() if path.is_absolute() else (self.packet_path.parent / path).resolve()
        self.snapshot = resolve(self.packet['snapshot_dir'])
        self.report_dir = resolve(self.packet['reports_dir'])
        manifest = json.loads((self.snapshot / 'manifest.json').read_text())
        if digest(self.snapshot / 'evidence.sqlite3') != manifest['database_sha256']:
            raise ValueError('Frozen database hash mismatch')
        for blob in manifest['blobs']:
            path = (self.snapshot / blob['path']).resolve()
            if not path.is_relative_to(self.snapshot) or digest(path) != blob['sha256']:
                raise ValueError('Frozen source hash mismatch')
        self.store = EvidenceStore(self.snapshot / 'evidence.sqlite3', readonly=True)
        try:
            self.index = json.loads((self.report_dir / 'prepared/index.json').read_text())
            self.reports = {}
            for item in self.index['reports']:
                rid = item['report_id']
                if not re.fullmatch(r'[a-zA-Z0-9_-]+', rid):
                    raise ValueError('Unsafe report identifier')
                prepared = self.report_dir / 'prepared' / (rid + '.json')
                pdf = self.report_dir / 'sources' / (rid + '.pdf')
                if digest(prepared) != item['prepared_sha256'] or digest(pdf) != item['source_sha256']:
                    raise ValueError('Report does not match frozen preparation hashes: ' + rid)
                pages = json.loads(prepared.read_text())
                if len(pages) != item['pages'] or any(p['page'] != i + 1 or not isinstance(p['text'], str) for i, p in enumerate(pages)):
                    raise ValueError('Invalid report pages')
                self.reports[rid] = pages
            self.report_publication_dates = {}
            source_manifest = self.report_dir / 'source-manifest.json'
            if source_manifest.exists():
                entries = json.loads(source_manifest.read_text()).get('documents', [])
                self.report_publication_dates = {r['report_id']: r['publication_date'] for r in entries if r.get('publication_date')}
            self.required = self.packet.get('required_reports', list(self.reports))
            if not set(self.required) <= set(self.reports):
                raise ValueError('Required report missing')
            self.store.validate_report_links({r['report_id']:{'source_sha256':r['source_sha256'],'pages':r['pages']} for r in self.index['reports']}, instrument_id=self.instrument)
            self.identity = {'packet_sha256': digest(self.packet_path), 'database_sha256': digest(self.snapshot / 'evidence.sqlite3'),
                             'reports': {r['report_id']: [r['source_sha256'], r['prepared_sha256']] for r in self.index['reports']}}
            if structured and source_manifest.exists():
                self.identity['source_manifest_sha256'] = digest(source_manifest)
            self.analysis_contract = {}
            for name, entry in self.packet.get('analysis_contract', {}).items():
                if name not in {'policy','calculations'}:
                    raise ValueError('Unknown analysis contract document')
                path = (self.packet_path.parent / entry['path']).resolve()
                if Path(entry['path']).is_absolute() or not path.is_relative_to(self.packet_path.parent) or digest(path) != entry['sha256']:
                    raise ValueError('Analysis contract hash or path mismatch')
                self.analysis_contract[name] = path.read_text()
            if self.analysis_contract:
                if set(self.analysis_contract) != {'policy','calculations'}:
                    raise ValueError('Analysis contract requires policy and calculations')
                self.identity['analysis_contract'] = self.packet['analysis_contract']
            self.analysis_guide_texts = {}
            if 'analysis_guides' in self.packet:
                self.analysis_guide_texts = read_analysis_guides(self.packet_path.parent, self.packet['analysis_guides'])
                self.identity['analysis_guides'] = self.packet['analysis_guides']
            for benchmark_name in ('benchmark_context','market_benchmark_context'):
                benchmark = self.packet.get(benchmark_name)
                if not benchmark:
                    continue
                verified = set()
                for entry in benchmark['files']:
                    path = (self.packet_path.parent / entry['path']).resolve()
                    if Path(entry['path']).is_absolute() or not path.is_relative_to(self.packet_path.parent) or digest(path) != entry['sha256']:
                        raise ValueError('Benchmark context hash or path mismatch')
                    verified.add(entry['path'])
                if benchmark['context_path'] not in verified:
                    raise ValueError('Benchmark context file is not verified')
                self.identity[benchmark_name] = benchmark
            self.state_path = self.run_dir / 'tool-state.json'
            self.lock = threading.RLock()
            if resume:
                self.state = json.loads(self.state_path.read_text())
                if self.state['identity'] != self.identity:
                    raise ValueError('Resume evidence identity changed')
            else:
                if self.state_path.exists():
                    raise ValueError('Existing tool state; use resume')
                self.state = {'identity': self.identity, 'coverage': {}, 'inputs': {}, 'calculations': {},
                              'rounds': [], 'round_evidence': [], 'consecutive_unproductive': 0, 'seen_evidence': [], 'research_closed': False, 'finalization_calls': 0}
                self.save()
        except BaseException:
            self.store.close()
            raise

    def save(self):
        write_json(self.state_path, self.state)

    def audit(self, event):
        with (self.run_dir / 'tool-audit.jsonl').open('a') as file:
            file.write(json.dumps({'at': datetime.now(timezone.utc).isoformat(), **event}, ensure_ascii=False) + '\n')

    def page(self, rid, page):
        if rid not in self.reports:
            raise ValueError('Unknown report ID')
        if isinstance(page, bool) or not isinstance(page, int) or not 1 <= page <= len(self.reports[rid]):
            raise ValueError('Page outside report')
        return self.reports[rid][page - 1]

    def coverage(self):
        result = {}
        for rid in self.required:
            read = set(self.state['coverage'].get(rid, []))
            missing = [i for i in range(1, len(self.reports[rid]) + 1) if i not in read]
            result[rid] = {'total_pages': len(self.reports[rid]), 'delivered_pages': len(read), 'next_unread_page': missing[0] if missing else None}
        return {'reports': result, 'complete': all(r['next_unread_page'] is None for r in result.values()),
                'delivered_pages': sum(r['delivered_pages'] for r in result.values()),
                'total_pages': sum(r['total_pages'] for r in result.values())}

    def catalogue(self):
        return {'instrument_id': self.instrument, 'reports': [{'report_id': rid, 'pages': len(p), **({'publication_date': self.report_publication_dates.get(rid)} if self.structured else {})} for rid, p in self.reports.items()],
                'datasets': self.packet.get('datasets', [d['dataset'] for d in self.store.list_datasets()]), 'context': self.packet.get('context', ''), 'initial_context':self.packet.get('initial_context',{}),
                'coverage': self.coverage(), 'saved_input_ids': list(self.state['inputs']),
                'calculation_ids': list(self.state['calculations']), 'research_rounds': self.state['rounds'],
                **({'analysis_guides': self.packet['analysis_guides']} if 'analysis_guides' in self.packet else {})}

    def get_calculation_definitions(self):
        return {'formulas': FORMULAS, 'analysis_contract': self.analysis_contract,
                'contract_status': 'versioned' if self.analysis_contract else 'legacy_packet_without_adopted_policy'}

    def read_report(self, report_id, start_page):
        self.page(report_id, start_page)
        text, delivered = '', []
        for page in self.reports[report_id][start_page-1:]:
            block = f"\n=== {report_id} | PDF PAGE {page['page']} ===\n{page['text']}\n"
            if len(text) + len(block) > READ_LIMIT:
                if not delivered:
                    raise ValueError('Page exceeds text limit; inspect original image')
                break
            text += block
            delivered.append(page['page'])
        self.state['coverage'][report_id] = sorted(set(self.state['coverage'].get(report_id, [])) | set(delivered))
        self.state['seen_evidence'] = sorted(set(self.state['seen_evidence']) | {f'{report_id}:p{p}' for p in delivered})
        return {'report_id': report_id, 'delivered_pages': delivered, 'next_page': delivered[-1]+1 if delivered[-1] < len(self.reports[report_id]) else None, 'text': text}

    def search_reports(self, query, report_id=None):
        if not isinstance(query, str) or not query.strip() or len(query) > 500:
            raise ValueError('Query must contain 1-500 characters')
        ids = [report_id] if report_id else list(self.reports)
        hits, count = [], 0
        for rid in ids:
            if rid not in self.reports:
                raise ValueError('Unknown report')
            for p in self.reports[rid]:
                start = p['text'].lower().find(query.lower())
                if start >= 0:
                    count += 1
                    if len(hits) < 30:
                        hits.append({'report_id': rid, 'page': p['page'], 'snippet': p['text'][max(0,start-160):start+len(query)+160]})
        self.state['searched_reports'] = sorted(set(self.state.get('searched_reports', [])) | set(ids))
        return {'hits': hits, 'total_hits': count, 'full_page_read': False}

    def view_report_page(self, report_id, page):
        self.page(report_id, page)
        entry = next(r for r in self.index['reports'] if r['report_id'] == report_id)
        if digest(self.report_dir/'sources'/(report_id+'.pdf')) != entry['source_sha256']:
            raise ValueError('Original report changed after packet initialization')
        directory = self.run_dir / 'images'; directory.mkdir(exist_ok=True)
        prefix = directory / f'{report_id}-p{page}'
        image = prefix.with_suffix('.png')
        if not image.exists():
            renderer = os.environ.get('BETAFORGE_PDFTOPPM') or shutil.which('pdftoppm')
            if not renderer or not Path(renderer).is_file():
                raise ValueError('PDF renderer unavailable: install Poppler or set BETAFORGE_PDFTOPPM to its pdftoppm executable')
            subprocess.run([renderer, '-f', str(page), '-l', str(page), '-singlefile', '-r', '110', '-png',
                            str(self.report_dir/'sources'/(report_id+'.pdf')), str(prefix)],
                           check=True, timeout=max(0.1,min(60,getattr(self,'deadline',float('inf'))-time.monotonic())), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Original image is evidence; image inspection alone does not satisfy full text reading.
        self.state['seen_evidence'] = sorted(set(self.state['seen_evidence']) | {f'{report_id}:p{page}'})
        return {'report_id': report_id, 'page': page, 'image_path': str(image), 'sha256': digest(image)}

    def get_financials(self, report_type=None, fields=None, limit=100, offset=0):
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 200 or not isinstance(offset,int) or offset < 0:
            raise ValueError('Invalid pagination')
        if fields is not None and (not isinstance(fields, list) or not 1 <= len(fields) <= 50 or not all(isinstance(f,str) for f in fields)):
            raise ValueError('Fields must be a bounded list of metric names')
        rows = self.store.query_financials(self.instrument, report_type=report_type, fields=fields, limit=limit, offset=offset)
        self.state['seen_evidence'] = sorted(set(self.state['seen_evidence']) | {str(r['id']) for r in rows})
        return {'observations': rows, 'offset': offset, 'next_offset': offset+len(rows) if len(rows)==limit else None}

    def get_dataset(self, dataset, limit=50, offset=0):
        if dataset not in self.packet.get('datasets', [d['dataset'] for d in self.store.list_datasets()]):
            raise ValueError('Dataset not in frozen packet catalogue')
        if not isinstance(limit,int) or isinstance(limit,bool) or not 1 <= limit <= 100 or not isinstance(offset,int) or offset < 0:
            raise ValueError('Invalid pagination')
        rows = self.store.query_dataset(dataset, instrument_id=self.instrument, limit=limit, offset=offset)
        self.state['seen_evidence'] = sorted(set(self.state['seen_evidence']) | {str(r['id']) for r in rows})
        return {'dataset': dataset, 'records': rows, 'next_offset': offset+len(rows) if len(rows)==limit else None}

    def get_source(self, source_id):
        return self.store.get_source(source_id)

    def record_input(self, value, label, unit, kind, report_id=None, page=None, quote=None, scale='1'):
        val = decimal(value)
        if not isinstance(label,str) or not label.strip() or len(label)>500 or not isinstance(unit,str) or not unit.strip() or len(unit)>100:
            raise ValueError('Input needs bounded label and unit')
        factor=decimal(scale)
        if factor<=0:raise ValueError('Scale must be positive')
        record = {'value': str(val), 'label': label, 'unit': unit, 'scale': str(factor), 'kind': kind}
        if kind == 'report':
            text = self.page(report_id,page)['text']
            if not isinstance(quote,str) or len(quote.strip()) < 10 or len(quote) > 2000:
                raise ValueError('Report input requires 10-2000 character source quote')
            normalized = lambda s: re.sub(r'\s+', ' ', s).strip()
            if normalized(quote) not in normalized(text):
                raise ValueError('Quote not found on saved source page; inspect page and use exact extracted quote')
            record.update(report_id=report_id,page=page,quote=quote,status='analyst_extracted_not_independently_reconciled')
        elif kind == 'assumption':
            record['status'] = 'explicit_assumption'
        else:
            raise ValueError('Unknown input kind')
        identifier = 'input:' + hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()[:20]
        self.state['inputs'][identifier] = {'id':identifier, **record}
        return self.state['inputs'][identifier]

    def resolve_input(self, identifier):
        if identifier in self.state['inputs']:
            return self.state['inputs'][identifier]
        if identifier in self.state['calculations']:
            r = self.state['calculations'][identifier]
            if r['result'] is None:
                raise ValueError('Calculation primary output is unavailable; inspect missing inputs')
            return {'id':identifier,'value':r['result'],'unit':r['unit'],'kind':'calculation','scale':'1',
                    **{key:r[key] for key in ('period_start','period_end','report_type') if key in r}}
        if '#' in identifier:
            calculation, output = identifier.split('#', 1)
            r = self.state['calculations'].get(calculation, {})
            if output not in r.get('outputs', {}) or r['outputs'][output]['value'] is None:
                raise ValueError('Unknown or unavailable named calculation output')
            return {'id':identifier, **r['outputs'][output], 'kind':'calculation','scale':'1',
                    **{key:r[key] for key in ('period_start','period_end','report_type') if key in r}}
        try:
            record = self.store.get_observation(identifier)
        except (KeyError, ValueError, TypeError):
            raise ValueError('Unknown input ID') from None
        if not record:
            raise ValueError('Unknown input ID')
        if int(record['instrument_id']) != self.instrument:
            raise ValueError('Observation outside selected instrument')
        return record

    def calculate_financial(self, formula, input_ids, label, basis, options=None):
        if formula not in FORMULAS or not isinstance(input_ids, dict) or len(input_ids) > 24:
            raise ValueError('Use a named formula and a bounded mapping of input fields to saved IDs')
        if not all(isinstance(k,str) and isinstance(v,str) for k,v in input_ids.items()):
            raise ValueError('Formula inputs must be saved IDs')
        if not isinstance(label,str) or not label.strip() or len(label)>500 or not isinstance(basis,str) or not basis.strip() or len(basis)>2000:
            raise ValueError('Provide a concise label and explicit period, scope and earnings basis')
        definition = FORMULAS[formula]
        fields = {**definition['required_fields'], **definition['optional_fields']}
        if set(input_ids) - set(fields):
            raise ValueError('Unknown financial formula input fields')
        inputs, values = [], {}
        for field, identifier in input_ids.items():
            item = dict(self.resolve_input(identifier))
            if unit_dimensions(item) != unit_dimensions({'unit':fields[field]}):
                raise ValueError(f'Input {field} requires base unit {fields[field]}; currency and fraction/percent must match')
            factor = decimal(item.get('scale','1'))
            if factor <= 0:
                raise ValueError('Input scale must be positive')
            if item['value'] is not None:
                with localcontext() as context:
                    context.prec = 40
                    values[field] = decimal(item['value']) * factor
                item['calculation_value'] = str(values[field])
            item['field'] = field
            inputs.append(item)
        period_warnings, period = self._financial_periods(formula, inputs)
        result = evaluate(formula, values, options)
        primary = result['outputs'].get(result['primary_output'])
        record = {**result, 'operation':'financial_formula', 'label':label, 'basis':basis,
                  'inputs':inputs, 'input_ids':dict(input_ids), 'options':options or {},
                  'result':primary['value'] if primary else None,
                  'unit':definition['output_units'][result['primary_output']], 'scale':'1', **period}
        record['warnings'].extend(period_warnings)
        identifier = 'calc:' + hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()[:20]
        record['id'] = identifier
        self.state['calculations'][identifier] = record
        return record

    @staticmethod
    def _financial_periods(formula, inputs):
        """Reject known mismatches; do not invent dates for analyst assumptions."""
        records = {item['field']:item for item in inputs}
        warnings = []
        def matching(fields):
            selected = [records[k] for k in fields if k in records]
            for key in ('period_start','period_end'):
                known = {r[key] for r in selected if r.get(key)}
                if len(known)>1:
                    raise ValueError('Financial formula inputs have incompatible '+key)
            if any(not r.get('period_end') for r in selected):
                warnings.append('Some input periods are analyst-declared in basis; dates are not independently verified')
        if formula in {'ebit_margin','group_cash_conversion','invested_capital'}:
            matching(records)
        elif formula == 'incremental_ebit_margin':
            matching(('ebit_current','revenue_current'))
            matching(('ebit_previous','revenue_previous'))
            current, prior = records.get('revenue_current',{}), records.get('revenue_previous',{})
            if current.get('period_end') and prior.get('period_end') and current['period_end'] <= prior['period_end']:
                raise ValueError('Incremental-margin current period must follow the prior period')
            if all(r.get('period_start') and r.get('period_end') for r in (current,prior)):
                durations = [(datetime.fromisoformat(r['period_end'])-datetime.fromisoformat(r['period_start'])).days for r in (current,prior)]
                if abs(durations[0]-durations[1])>14:
                    raise ValueError('Incremental-margin periods have incompatible durations')
        elif formula in {'working_capital_to_sales','operating_roic'}:
            flow = records.get('revenue' if formula=='working_capital_to_sales' else 'ebit',{})
            if flow.get('report_type') and flow['report_type'] not in {'year','r12'}:
                raise ValueError('Use annual or R12 flow for the capital diagnostic')
            closing = records.get('balance_end' if formula=='working_capital_to_sales' else 'invested_capital_end',{})
            if closing.get('period_end') and flow.get('period_end') and closing['period_end']!=flow['period_end']:
                raise ValueError('Closing capital date must match the flow period end')
            opening = records.get('balance_start' if formula=='working_capital_to_sales' else 'invested_capital_start',{})
            if opening.get('period_end') and flow.get('period_start'):
                gap = (datetime.fromisoformat(flow['period_start'])-datetime.fromisoformat(opening['period_end'])).days
                if gap != 1:
                    raise ValueError('Opening capital date must be the day before the flow period starts')
            warnings.append('Opening/closing capital, group scope and tax basis require the stated source reconciliation')
        elif formula in {'pe','ev_ebit'}:
            earnings = records.get('diluted_eps' if formula=='pe' else 'ebit',{})
            if earnings.get('report_type') and earnings['report_type'] not in {'year','r12'}:
                raise ValueError('Ordinary P/E and EV/EBIT require annual or R12 earnings; do not use an unannualized quarter/YTD')
            if not earnings.get('report_type'):
                warnings.append('Annual earnings period is analyst-declared in basis, not independently verified')
            if formula=='pe' and earnings.get('metric')=='earnings_Per_Share' and 'unresolved' in earnings.get('basis','').lower():
                raise ValueError('Provider EPS basic/diluted basis is unresolved; select a verified diluted EPS input')
        ends = {r.get('period_end') for r in inputs if r.get('period_end')}
        starts = {r.get('period_start') for r in inputs if r.get('period_start')}
        period = {}
        if formula in {'ebit_margin','group_cash_conversion','invested_capital'}:
            if len(ends)==1: period['period_end']=next(iter(ends))
            if len(starts)==1 and formula!='invested_capital': period['period_start']=next(iter(starts))
        return list(dict.fromkeys(warnings)), period

    def calculate(self, operation, input_ids, label, unit):
        if not isinstance(input_ids,list) or not 2 <= len(input_ids) <= 100 or not all(isinstance(i,str) for i in input_ids):
            raise ValueError('Use 2-100 saved input IDs')
        inputs = [dict(self.resolve_input(i)) for i in input_ids]
        values=[]
        for item in inputs:
            factor=decimal(item.get('scale','1'))
            if factor<=0:raise ValueError('Input scale must be positive')
            with localcontext() as context:
                context.prec=40
                normalized=decimal(item['value'])*factor
            item['calculation_value']=str(normalized)
            values.append(normalized)
        if operation in ('subtract','divide','growth_percent','power') and len(values)!=2:
            raise ValueError('Operation needs exactly two inputs')
        if not isinstance(label,str) or not label.strip() or len(label)>500 or not isinstance(unit,str) or not unit.strip() or len(unit)>100:
            raise ValueError('Provide calculation label and output unit')
        dimensions=[unit_dimensions(item) for item in inputs]
        if operation in ('add','subtract','growth_percent') and any(d!=dimensions[0] for d in dimensions):
            raise ValueError('Incompatible base units or currencies')
        expected=dict(dimensions[0])
        if operation=='growth_percent':expected={'percent':1}
        elif operation in ('multiply','divide'):
            for i,d in enumerate(dimensions[1:]):
                for k,v in d.items():expected[k]=expected.get(k,0)+(v if operation=='multiply' else -v)
            expected={k:v for k,v in expected.items() if v}
        elif operation=='power':
            if dimensions[1]:raise ValueError('Exponent must be dimensionless')
            if abs(values[1])>100:raise ValueError('Exponent must be between -100 and 100')
            if values[1]!=values[1].to_integral_value():
                if dimensions[0] or values[0]<=0:
                    raise ValueError('Fractional powers require a positive dimensionless base')
                expected={}
            else:
                expected={k:v*int(values[1]) for k,v in expected.items() if v*int(values[1])}
        if unit_dimensions({'unit':unit})!=expected:
            raise ValueError('Output unit must match base-unit arithmetic: '+unit_label(expected))
        with localcontext() as context:
            context.prec = 40
            if operation == 'add': result = sum(values)
            elif operation == 'multiply':
                result = Decimal(1)
                for v in values: result *= v
            elif operation == 'subtract': result = values[0]-values[1]
            elif operation == 'divide':
                if values[1]==0: raise ValueError('Division by zero')
                result = values[0]/values[1]
            elif operation == 'growth_percent':
                if values[0]==0: raise ValueError('Growth baseline is zero')
                result = (values[1]-values[0])/values[0]*100
            elif operation == 'power':
                if values[0]==0 and values[1]<=0: raise ValueError('Undefined power')
                result = values[0] ** values[1]
            else: raise ValueError('Unknown operation')
        if not result.is_finite() or abs(result)>Decimal('1e100'):
            raise ValueError('Nonfinite or excessive result')
        record={'operation':operation,'inputs':inputs,'result':str(result),'label':label,'unit':unit_label(expected),'scale':'1','basis':'base units; each source value multiplied by stored scale exactly once'}
        identifier='calc:'+hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()[:20]
        record['id']=identifier
        self.state['calculations'][identifier]=record
        return record

    def get_saved_record(self, identifier):
        if identifier in self.state['calculations']:
            return self.state['calculations'][identifier]
        record = self.resolve_input(identifier)
        if identifier not in self.state['inputs'] and not identifier.startswith('calc:'):
            self.state['seen_evidence'] = sorted(set(self.state['seen_evidence']) | {identifier})
        return record

    def submit_analysis(self, report):
        if not self.structured:
            raise ValueError('Structured submission is not enabled')
        from betaforge.analysis_report import validate_report, render_markdown
        if not self.coverage()['complete']:
            raise ValueError('Required report reading is incomplete')
        validated = validate_report(report, self)
        write_json(self.run_dir / 'analysis.json', validated)
        (self.run_dir / 'answer.md').write_text(render_markdown(validated))
        self.state['analysis_sha256'] = digest(self.run_dir / 'analysis.json')
        return {'analysis_sha256': self.state['analysis_sha256'], 'validation_status': validated['validation_status'],
                'review_status': 'unreviewed', 'economic_quality_verified': False}

    def reopen_revision_research(self):
        """Called by the controller only after a verified, saved review request."""
        if self.state.get('revision_count', 0):
            raise ValueError('At most one revision is allowed')
        self.state.update(revision_count=1, revision_round_start=len(self.state['rounds']),
                          research_closed=False, consecutive_unproductive=0, finalization_calls=0)
        self.state.pop('analysis_sha256', None)
        self.save()

    def finish_research_round(self, summary, evidence_ids, ready_to_finalize):
        if not self.coverage()['complete']:
            raise ValueError('Required report reading is incomplete')
        limit = self.state.get('revision_round_start', 0) + 2 if self.state.get('revision_count') else 10
        if self.state.get('research_closed') or len(self.state['rounds'])>=limit or self.state['consecutive_unproductive']>=2:
            return {'stop':True,'reason':'research_limit','rounds':len(self.state['rounds'])}
        if not isinstance(summary,str) or not summary.strip() or len(summary)>5000 or not isinstance(evidence_ids,list) or len(evidence_ids)>100:
            raise ValueError('Bounded round summary and evidence IDs required')
        if not all(isinstance(i,str) and i in self.state['seen_evidence'] for i in evidence_ids):
            raise ValueError('Round evidence must have been retrieved')
        new=set(evidence_ids)-set(self.state['round_evidence'])
        self.state['round_evidence']=sorted(set(self.state['round_evidence'])|new)
        self.state['consecutive_unproductive']=0 if new else self.state['consecutive_unproductive']+1
        result={'round':len(self.state['rounds'])+1,'summary':summary,'new_evidence_ids':sorted(new),'ready_to_finalize':bool(ready_to_finalize)}
        self.state['rounds'].append(result)
        result['stop']=bool(ready_to_finalize) or len(self.state['rounds'])>=limit or self.state['consecutive_unproductive']>=2
        if result['stop']:self.state['research_closed']=True
        return result

    def call(self, name, arguments, call_id):
        with self.lock:
            self.audit({'event':'call','tool':name,'call_id':call_id,'arguments':arguments})
            try:
                allowed={s['name'] for s in TOOL_SCHEMAS + (STRUCTURED_TOOL_SCHEMAS if self.structured else [])}
                if name not in allowed: raise ValueError('Unknown tool')
                if not isinstance(arguments,dict): raise ValueError('Tool arguments must be an object')
                if self.state.get('research_closed'):
                    if name not in {'calculate','calculate_financial','get_calculation_definitions','record_input','get_catalogue','get_source','finish_research_round','submit_analysis','get_saved_record'}:
                        raise ValueError('Research is closed by the round limit or finalization decision; use saved evidence and finalize')
                    self.state['finalization_calls']=self.state.get('finalization_calls',0)+1
                    if self.state['finalization_calls']>200:
                        raise ValueError('Finalization tool limit reached; return the saved partial answer')
                result=self.catalogue() if name=='get_catalogue' else getattr(self,name)(**arguments)
                self.save()
                audit_result={k:v for k,v in result.items() if k!='text'} if isinstance(result,dict) else result
                self.audit({'event':'result','tool':name,'call_id':call_id,'result':audit_result})
                content=[{'type':'inputText','text':json.dumps(result,ensure_ascii=False)}]
                if name=='view_report_page':
                    content.append({'type':'inputImage','imageUrl':'data:image/png;base64,'+base64.b64encode(Path(result['image_path']).read_bytes()).decode()})
                return {'contentItems':content,'success':True}
            except (ValueError,KeyError,TypeError,OSError,InvalidOperation,subprocess.SubprocessError) as error:
                self.save()
                self.audit({'event':'error','tool':name,'call_id':call_id,'error':str(error)})
                return {'contentItems':[{'type':'inputText','text':str(error)}],'success':False}
