"""Small saved-report contract. Validation checks identity and syntax, not economics."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal
import re

from betaforge.financials import FORMULAS

SECTIONS = ('thesis', 'drivers', 'quality', 'management', 'valuation', 'risks')


def text(value, label, maximum=12000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'{label} requires bounded nonempty text')
    return value


def fields(value, required, optional=()):
    if not isinstance(value, dict) or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ValueError('Invalid report fields: ' + ', '.join(required))


def iso_date(value):
    text(value, 'date', 10)
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Date must use YYYY-MM-DD')
    date.fromisoformat(value)
    return value


def dated_endpoint(value):
    fields(value, ('value', 'precision'))
    precision = value['precision']
    patterns = {'year': r'\d{4}', 'month': r'\d{4}-\d{2}', 'day': r'\d{4}-\d{2}-\d{2}'}
    if precision not in patterns or not isinstance(value['value'], str) or not re.fullmatch(patterns[precision], value['value']):
        raise ValueError('Endpoint value must match its explicit year/month/day precision')
    iso_date(value['value'] + {'year': '-01-01', 'month': '-01', 'day': ''}[precision])
    return value['value']


def references(values, tools, required=False):
    if not isinstance(values, list) or len(values) > 100 or (required and not values):
        raise ValueError('Provide a bounded list of saved references')
    for identifier in values:
        text(identifier, 'reference', 200)
        report = re.fullmatch(r'([A-Za-z0-9_-]+):p([1-9]\d*)', identifier)
        if report:
            tools.page(report[1], int(report[2]))
        elif identifier not in tools.state['calculations']:
            tools.resolve_input(identifier)
    return values


def validate_report(report, tools):
    fields(report, ('schema_version', 'analysis_date', 'summary', 'sections', 'management_comparisons', 'scenarios', 'probability_limits'))
    if type(report['schema_version']) is not int or report['schema_version'] != 1:
        raise ValueError('Unsupported report schema version')
    iso_date(report['analysis_date'])
    if report['analysis_date'] != tools.packet.get('analysis_date'):
        raise ValueError('Analysis date must match frozen packet')
    text(report['summary'], 'summary')
    text(report['probability_limits'], 'probability limits')
    sections = report['sections']
    if not isinstance(sections, list) or len(sections) != len(SECTIONS) or {s.get('id') for s in sections if isinstance(s, dict)} != set(SECTIONS):
        raise ValueError('Require the six stable analysis sections')
    for section in sections:
        fields(section, ('id', 'title', 'paragraphs'))
        text(section['title'], 'section title', 300)
        if not isinstance(section['paragraphs'], list) or not 1 <= len(section['paragraphs']) <= 50:
            raise ValueError('Section requires 1-50 paragraphs')
        for paragraph in section['paragraphs']:
            fields(paragraph, ('kind', 'text', 'references'))
            if paragraph['kind'] not in ('fact', 'interpretation', 'assumption'):
                raise ValueError('Paragraph kind must distinguish fact, interpretation and assumption')
            text(paragraph['text'], 'paragraph')
            references(paragraph['references'], tools, required=True)
    comparisons = report['management_comparisons']
    if not isinstance(comparisons, list) or len(comparisons) > 100:
        raise ValueError('Management comparisons must be bounded')
    identifiers = set()
    for item in comparisons:
        fields(item, ('id', 'metric_key', 'metric_label', 'relationship', 'statement_type', 'statement', 'statement_date', 'target_period', 'basis', 'actual', 'actual_references', 'references', 'evidence'))
        if not re.fullmatch(r'[a-z0-9_-]+', text(item['id'], 'management ID', 100)) or item['id'] in identifiers:
            raise ValueError('Management comparison IDs must be unique and stable')
        identifiers.add(item['id'])
        if item['metric_key'] not in FORMULAS:
            raise ValueError('Management metric_key must name an existing financial formula')
        for key in ('metric_label', 'statement', 'basis'):
            text(item[key], key)
        if item['relationship'] not in ('direct', 'related', 'not_stated') or item['statement_type'] not in ('target', 'guidance', 'driver', 'not_stated'):
            raise ValueError('Invalid management relationship or statement type')
        for key in ('actual', 'target_period'):
            if item[key] is not None:
                text(item[key], key)
        references(item['references'], tools, required=True)
        references(item['actual_references'], tools, required=item['actual'] is not None)
        if item['statement_date'] is not None:
            iso_date(item['statement_date'])
            if item['statement_date'] > report['analysis_date']:
                raise ValueError('Statement date follows the analysis date')
        evidence = item['evidence']
        if item['statement_type'] == 'not_stated' or item['relationship'] == 'not_stated':
            if item['statement_type'] != 'not_stated' or item['relationship'] != 'not_stated' or evidence is not None or item['statement_date'] is not None:
                raise ValueError('Explicit not_stated needs null evidence/date and both classifications')
            report_ids = {ref.split(':p')[0] for ref in item['references'] if ':p' in ref}
            if not report_ids or not report_ids <= set(tools.state.get('searched_reports', [])):
                raise ValueError('No-guidance claim requires references to reports actually searched')
        else:
            fields(evidence, ('report_id', 'page', 'quote'))
            page = tools.page(evidence['report_id'], evidence['page'])
            quote = text(evidence['quote'], 'source quote', 4000)
            normalize = lambda s: re.sub(r'\s+', ' ', s).strip()
            if normalize(quote) not in normalize(page['text']):
                raise ValueError('Management quote not found on physical report page')
            source_ref = f"{evidence['report_id']}:p{evidence['page']}"
            if source_ref not in item['references']:
                raise ValueError('Management evidence page must appear in references')
            published = tools.report_publication_dates.get(evidence['report_id'])
            if item['statement_date'] != published:
                raise ValueError('Statement date must match known source publication date or remain null when unknown')
    scenarios = report['scenarios']
    if not isinstance(scenarios, list) or len(scenarios) != 3 or {s.get('id') for s in scenarios if isinstance(s, dict)} != {'bear', 'base', 'bull'}:
        raise ValueError('Require bear, base and bull scenarios')
    saved = deepcopy(report)
    weights = Decimal(0)
    targets = set()
    from betaforge.tools import decimal, unit_dimensions
    for item in saved['scenarios']:
        fields(item, ('id', 'name', 'valuation_calculation_id', 'present_value_date', 'target_date', 'rationale', 'assumption_rationale', 'references', 'weight_ref', 'probability_rationale'))
        for key in ('name', 'rationale', 'assumption_rationale', 'probability_rationale'):
            text(item[key], key)
        references(item['references'], tools, required=True)
        pv_date = dated_endpoint(item['present_value_date'])
        target = dated_endpoint(item['target_date'])
        if item['present_value_date'] != {'value': report['analysis_date'], 'precision': 'day'}:
            raise ValueError('Present value date must equal the frozen analysis date')
        if target[:4] <= pv_date[:4]:
            raise ValueError('Target must follow the analysis year')
        if len(target)>4 and target[5:] != pv_date[5:len(target)]:
            raise ValueError('Target month/day must match the saved whole-year horizon')
        targets.add((target, item['target_date']['precision']))
        calculation = tools.state['calculations'].get(item['valuation_calculation_id'], {})
        if calculation.get('formula') != 'valuation_case':
            raise ValueError('Scenario must reference a saved named valuation_case')
        for output in ('present_value', 'future_target'):
            value = tools.resolve_input(item['valuation_calculation_id'] + '#' + output)
            if unit_dimensions(value) != {'SEK': 1, 'shares': -1} or decimal(value['value']) < 0:
                raise ValueError('Valuation output must be available nonnegative SEK per share')
            item[output] = {'value': value['value'], 'unit': value['unit']}
        years = next((r['calculation_value'] for r in calculation['inputs'] if r['field'] == 'years'), None)
        if years is None or int(target[:4]) - int(pv_date[:4]) != decimal(years):
            raise ValueError('Target year must match the saved valuation horizon')
        weight = tools.state['inputs'].get(item['weight_ref'], {})
        if weight.get('kind') != 'assumption' or unit_dimensions(weight) or not 0 <= decimal(weight['value']) * decimal(weight.get('scale', '1')) <= 1:
            raise ValueError('Scenario weight must reference a saved dimensionless probability assumption')
        weights += decimal(weight['value']) * decimal(weight.get('scale', '1'))
    if weights != 1 or len(targets) != 1:
        raise ValueError('Probabilities must sum to one and scenario endpoints must match')
    saved.update(identity=deepcopy(tools.identity), validation_status='syntax_and_identity_valid', review_status='unreviewed')
    return saved


def render_markdown(report):
    lines = ['# Company analysis', '', report['summary'], '', f"Analysis date: {report['analysis_date']}", '', 'Validation: syntax and evidence identity only. Economic review: ' + report['review_status'] + '.', '']
    for section in report['sections']:
        lines += ['## ' + section['title'], '']
        for paragraph in section['paragraphs']:
            lines += [f"**{paragraph['kind'].capitalize()}:** {paragraph['text']}", 'References: ' + ', '.join(paragraph['references']), '']
    lines += ['## Scenario endpoints', '']
    for item in report['scenarios']:
        lines += [f"### {item['name']}", '', f"Present value ({item['present_value_date']['value']}): {item['present_value']['value']} {item['present_value']['unit']}. Target ({item['target_date']['value']}, {item['target_date']['precision']} precision): {item['future_target']['value']} {item['future_target']['unit']}.", item['rationale'], item['assumption_rationale'], 'Probability: ' + item['weight_ref'] + '. ' + item['probability_rationale'], 'Calculation: ' + item['valuation_calculation_id'], 'References: ' + ', '.join(item['references']), '']
    lines += [report['probability_limits'], '', '## Management comparisons', '']
    for item in report['management_comparisons']:
        lines += [f"### {item['metric_label']} ({item['relationship']})", '', item['statement'], 'Date: ' + str(item['statement_date']) + '; target period: ' + str(item['target_period']), 'Basis: ' + item['basis'], 'Actual: ' + str(item['actual']), 'References: ' + ', '.join(item['references'] + item['actual_references']), '']
        if item['evidence']:
            lines += ['> ' + item['evidence']['quote'], '']
    lines += ['## Source and calculation appendix', '', 'Report references use physical PDF pages. Saved input and calculation IDs retain exact values, units, bases and dependencies in inputs.json and calculations.json.', '']
    return '\n'.join(lines)


def validate_feedback(feedback, identity, analysis_sha256):
    fields(feedback, ('schema_version', 'packet_sha256', 'analysis_sha256', 'reviewer', 'verdict', 'summary', 'findings', 'disagreements'))
    if type(feedback['schema_version']) is not int or feedback['schema_version'] != 1 or feedback['packet_sha256'] != identity['packet_sha256'] or feedback['analysis_sha256'] != analysis_sha256:
        raise ValueError('Feedback must match the frozen packet and submitted analysis hash')
    if feedback['verdict'] not in ('accept', 'revise'):
        raise ValueError('Feedback verdict must be accept or revise')
    text(feedback['reviewer'], 'reviewer', 500)
    text(feedback['summary'], 'review summary')
    if not isinstance(feedback['findings'], list) or len(feedback['findings']) > 100 or not isinstance(feedback['disagreements'], list) or len(feedback['disagreements']) > 100:
        raise ValueError('Review findings and disagreements must be bounded lists')
    for disagreement in feedback['disagreements']:
        text(disagreement, 'review disagreement')
    for finding in feedback['findings']:
        fields(finding, ('id', 'verdict', 'reasoning', 'references', 'missing_evidence'))
        for key in ('id', 'verdict', 'reasoning'):
            text(finding[key], key)
        if not isinstance(finding['references'], list) or not all(isinstance(v, str) for v in finding['references']) or not isinstance(finding['missing_evidence'], str):
            raise ValueError('Finding requires references and explicit missing evidence')
    return feedback


def validate_review(feedback, packet_sha256, analysis_sha256):
    return validate_feedback(feedback, {'packet_sha256': packet_sha256}, analysis_sha256)


REPORT_CONTRACT = '''Call submit_analysis with {report:{schema_version:1,analysis_date,summary,
sections:[{id,title,paragraphs:[{kind,text,references:[saved_reference]}]}],
management_comparisons:[{id,metric_key,metric_label,relationship,statement_type,statement,
statement_date,target_period,basis,actual,actual_references:[],references:[],evidence}],
scenarios:[{id,name,valuation_calculation_id,present_value_date,target_date,rationale,
assumption_rationale,references:[],weight_ref,probability_rationale}],probability_limits}}.
Six sections exactly: thesis, drivers, quality, management, valuation, risks. Paragraph kinds:
fact, interpretation, assumption; each needs saved references. Sources: REPORT:pN physical
pages, saved observation/input IDs, calc:ID#output. Management metric_key must be a named
financial formula. Relationship direct|related|not_stated; statement_type target|guidance|driver|not_stated.
Evidence is {report_id,page,quote} with an exact whitespace-normalized page quote. statement_date
is known publication date YYYY-MM-DD, otherwise null. target_period/actual may be null.
An explicit no-guidance entry requires both not_stated labels, null evidence/date, and page
references to reports actually searched with search_reports. Keep issuer ROCE separate from
operating_roic; related drivers are not direct operating targets. Scenarios exactly bear/base/bull.
Dates are {value:'YYYY' or 'YYYY-MM' or 'YYYY-MM-DD',precision:'year'|'month'|'day'}; present
value date is the analysis date at day precision. Preserve honest target precision; don't invent
days from an annual horizon. All cases share the endpoint and saved integer years. Each case
references a saved complete valuation_case; do not supply present_value/future_target numbers:
the client copies these outputs. weight_ref is a saved dimensionless assumption; weights sum
exactly to one. Provide company-specific probability evidence and omitted-tail limitations.
Write the summary as a short investment conclusion for a financial reader, following the
supplied policy's writing rules. Explain the business mechanism, selected forecast magnitude
and shareholder return implication. Name concrete cash uses and operating risks; support
qualitative judgments with evidence. Price references need their date. Keep execution,
extraction and revision bookkeeping out of the investment summary and in audit details.
Aim for an opening conclusion of about 90 words and short, readable sections. Use compact
tables for comparisons. Explain business economics, required improvement, capital needs
and shareholder results; keep detailed reconciliations and revision history in evidence
details. Keep material uncertainty beside the conclusion it limits when shortening prose.
Select one operating equation. Explain 3-5 drivers and the company's own 5-10-year history
where available; save one or two modest disappointment checks and two or three disconfirmers.
Use saved named calculations. Required reading plus validated submission permits execution
completion only; economic review is separate. Submission generates answer.md automatically.'''


def validate_saved_report(report, tools):
    """Revalidate persisted canonical values against their original evidence context."""
    candidate = deepcopy(report)
    for key in ('identity', 'validation_status', 'review_status'):
        candidate.pop(key, None)
    for scenario in candidate.get('scenarios', []):
        scenario.pop('present_value', None)
        scenario.pop('future_target', None)
    expected = validate_report(candidate, tools)
    if expected != report:
        raise ValueError('Saved report differs from validated evidence and calculation outputs')
    return expected
