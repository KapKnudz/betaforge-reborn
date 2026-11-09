from copy import deepcopy
import json
import unittest

import test_tools
from betaforge.analysis_report import SECTIONS, render_markdown, validate_report, validate_saved_report, validate_review
from betaforge.financials import FORMULAS
from betaforge.tools import digest


class AnalysisReportTests(unittest.TestCase):
    setUp = test_tools.ToolsTests.setUp
    tearDown = test_tools.ToolsTests.tearDown

    def report(self, weighted=True, version=2):
        self.tools.structured = True
        self.tools.packet['analysis_date'] = '2026-11-04'
        self.tools.read_report('example', 1)
        self.tools.report_publication_dates = {'example': '2026-01-01'}
        ids = {}
        for field, unit in FORMULAS['valuation_case']['required_fields'].items():
            value = {'forecast_ebit':'100', 'exit_multiple':'10', 'forecast_shares':'100', 'years':'3', 'required_return':'0.1'}.get(field, '0')
            ids[field] = self.tools.record_input(value, field, unit, 'assumption')['id']
        calc = self.tools.calculate_financial('valuation_case', ids, 'Test bridge', 'Test basis')
        cases = []
        for identifier, weight in [('bear', '.2'), ('base', '.5'), ('bull', '.3')]:
            case = dict(id=identifier, name=identifier, valuation_calculation_id=calc['id'], present_value_date={'value':'2026-11-04','precision':'day'}, target_date={'value':'2029','precision':'year'}, rationale='Mechanism evidence', assumption_rationale='Explicit model assumptions', references=['example:p1', calc['id']+'#present_value'])
            if weighted:
                ref = self.tools.record_input(weight, identifier + ' probability', 'dimensionless', 'assumption')['id']
                case.update(weight_ref=ref, probability_rationale='Conditional point probability')
                if version == 2:
                    case['probability_references'] = ['example:p1']
            cases.append(case)
        return dict(schema_version=version, analysis_date='2026-11-04', summary='Conditional case.', sections=[dict(id=key,title=key,paragraphs=[dict(kind='interpretation',text='Evidence and interpretation.',references=['example:p1'])]) for key in SECTIONS], management_comparisons=[dict(id='operating-margin',metric_key='ebit_margin',metric_label='Margin',relationship='related',statement_type='driver',statement='Source statement',statement_date='2026-01-01',target_period=None,basis='Group, reported',actual=None,actual_references=[],references=['example:p1'],evidence={'report_id':'example','page':1,'quote':'Net revenue was 10.25 million SEK.'})], scenarios=cases, probability_limits='Representative outcomes omit tails.' if weighted else 'Comparable outcome frequencies are unavailable.')

    def test_canonical_values_are_copied_and_generated_report_retains_evidence(self):
        report = self.report()
        response = self.tools.submit_analysis(report)
        saved = json.loads((self.root/'run/analysis.json').read_text())
        self.assertEqual(response['analysis_sha256'], digest(self.root/'run/analysis.json'))
        self.assertEqual(saved['review_status'], 'unreviewed')
        self.assertEqual(saved['scenarios'][0]['future_target']['value'], '10')
        validate_saved_report(saved, self.tools)
        saved['scenarios'][0]['future_target']['value'] = '999'
        with self.assertRaisesRegex(ValueError, 'differs'):validate_saved_report(saved, self.tools)
        answer = (self.root/'run/answer.md').read_text()
        self.assertIn('year precision', answer)
        self.assertIn('example:p1', answer)
        self.assertIn('Net revenue was', answer)
        self.assertIn('Probability sources: example:p1', answer)

    def test_new_report_can_omit_probabilities_without_losing_scenario_values(self):
        report = self.report(weighted=False)
        self.tools.submit_analysis(report)
        saved = json.loads((self.root/'run/analysis.json').read_text())
        validate_saved_report(saved, self.tools)
        self.assertEqual(saved['schema_version'], 2)
        self.assertEqual(saved['scenarios'][0]['future_target']['value'], '10')
        self.assertNotIn('weight_ref', saved['scenarios'][0])
        answer = (self.root/'run/answer.md').read_text()
        self.assertNotIn('Probability:', answer)
        self.assertIn(report['probability_limits'], answer)

    def test_weights_require_complete_source_backed_rationales_and_exact_total(self):
        original = self.report()
        mutations = [
            lambda s: s.pop('probability_references'),
            lambda s: s.update(probability_rationale=' '),
            lambda s: s.update(probability_references=[]),
            lambda s: s.update(probability_references=['example:p3']),
            lambda s: s.update(probability_references=[s['weight_ref']]),
            lambda s: s.update(weight_ref=original['scenarios'][1]['weight_ref']),
            lambda s: s.update(weight_ref=self.tools.record_input(
                '0.20000000000000000000000000000000000001', 'Nearly valid', 'dimensionless', 'assumption')['id']),
            lambda s: [s.pop(key) for key in ('weight_ref', 'probability_rationale', 'probability_references')],
        ]
        for mutate in mutations:
            report = deepcopy(original)
            mutate(report['scenarios'][0])
            with self.subTest(case=report['scenarios'][0]), self.assertRaises(ValueError):
                self.tools.submit_analysis(report)

    def test_legacy_schema_remains_readable_with_original_markdown(self):
        legacy = self.report(version=1)
        legacy['scenarios'][0]['weight_ref'] = self.tools.record_input(
            '0.20000000000000000000000000000000000001', 'Archived probability', 'dimensionless', 'assumption')['id']
        with self.assertRaisesRegex(ValueError, 'schema version'):
            self.tools.submit_analysis(legacy)
        saved = validate_report(legacy, self.tools, saved=True)
        self.assertEqual(validate_saved_report(saved, self.tools), saved)
        case = legacy['scenarios'][0]
        self.assertIn(
            f"Explicit model assumptions\nProbability: {case['weight_ref']}. Conditional point probability\n"
            f"Calculation: {case['valuation_calculation_id']}\n",
            render_markdown(saved),
        )
        self.assertNotIn('Probability sources:', render_markdown(saved))

    def test_fabricated_references_dates_and_quotes_are_rejected(self):
        original = self.report()
        mutations = [
            lambda r: r['sections'][0]['paragraphs'][0].update(references=['fiction']),
            lambda r: r['sections'][0]['paragraphs'][0].update(references=['example:p3']),
            lambda r: r.update(analysis_date='2026-11-05'),
            lambda r: r['management_comparisons'][0].update(statement_date='2026-01-02'),
            lambda r: r['management_comparisons'][0]['evidence'].update(quote='A fabricated promise'),
            lambda r: r['scenarios'][0].update(present_value='999'),
            lambda r: r['scenarios'][0].update(target_date={'value':'2029-12-31','precision':'day'}),
            lambda r: r['scenarios'][0].update(target_date={'value':'2028','precision':'year'}),
        ]
        for mutate in mutations:
            changed = deepcopy(original);mutate(changed)
            with self.subTest(report=changed), self.assertRaises(ValueError):validate_report(changed,self.tools)

    def test_no_guidance_claim_requires_searched_reports(self):
        report=self.report();item=report['management_comparisons'][0]
        item.update(relationship='not_stated',statement_type='not_stated',evidence=None,statement_date=None)
        with self.assertRaisesRegex(ValueError,'actually searched'):validate_report(report,self.tools)
        self.tools.search_reports('guidance','example')
        validate_report(report,self.tools)

    def test_quote_whitespace_normalization_and_required_reading(self):
        report=self.report();report['management_comparisons'][0]['evidence']['quote']='Net revenue\nwas 10.25 million SEK.'
        validate_report(report,self.tools)
        self.tools.state['coverage']={}
        with self.assertRaisesRegex(ValueError,'reading'):self.tools.submit_analysis(report)

    def test_constructor_failure_closes_opened_store(self):
        from unittest.mock import Mock, patch
        from betaforge.tools import EvidenceTools
        store=Mock()
        index=self.root/'reports/prepared/index.json'
        index.write_text('{invalid')
        with patch('betaforge.storage.EvidenceStore',return_value=store):
            with self.assertRaises(ValueError):
                EvidenceTools(self.packet,self.root/'invalid-init',structured=True)
        store.close.assert_called_once()

    def test_unknown_publication_date_cannot_be_invented(self):
        report=self.report()
        self.assertEqual(self.tools.catalogue()['reports'][0]['publication_date'],'2026-01-01')
        self.tools.report_publication_dates={}
        with self.assertRaisesRegex(ValueError,'publication date'):
            validate_report(report,self.tools)
        report['management_comparisons'][0]['statement_date']=None
        validate_report(report,self.tools)

    def test_saved_observation_read_can_support_research_round(self):
        self.tools.structured=True
        self.tools.read_report('example',1)
        observation=self.tools.store.query_financials(self.tools.instrument,fields=['revenues'],limit=1)[0]
        response=self.tools.call('get_saved_record',{'identifier':observation['id']},'saved-record')
        self.assertTrue(response['success'])
        self.assertIn(observation['id'],self.tools.state['seen_evidence'])
        result=self.tools.finish_research_round('Inspected saved observation',[observation['id']],False)
        self.assertIn(observation['id'],result['new_evidence_ids'])

    def test_revision_reopens_only_two_rounds_and_only_once(self):
        self.report();self.tools.state['research_closed']=True
        self.tools.state['rounds']=[{} for _ in range(10)]
        self.tools.reopen_revision_research()
        self.assertFalse(self.tools.state['research_closed'])
        self.assertFalse(self.tools.finish_research_round('Targeted source check',['example:p1'],False)['stop'])
        self.assertTrue(self.tools.finish_research_round('Second source check',['example:p2'],False)['stop'])
        with self.assertRaisesRegex(ValueError,'one revision'):self.tools.reopen_revision_research()

    def test_feedback_identity_is_bound_to_packet_and_analysis(self):
        review=dict(schema_version=1,packet_sha256='packet',analysis_sha256='analysis',reviewer='Independent reviewer',verdict='revise',summary='Test assumptions.',findings=[dict(id='one',verdict='bounded concern',reasoning='Source does not support estimate.',references=['example:p1'],missing_evidence='Comparable outcomes')],disagreements=[])
        validate_review(review,'packet','analysis')
        with self.assertRaisesRegex(ValueError,'disagreement'):
            validate_review(dict(review,disagreements=[{'unvalidated':'object'}]),'packet','analysis')
        for packet, analysis in [('other','analysis'),('packet','other')]:
            with self.assertRaisesRegex(ValueError,'hash'):validate_review(review,packet,analysis)


if __name__ == '__main__':unittest.main()
