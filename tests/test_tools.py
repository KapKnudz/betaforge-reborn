import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from decimal import Decimal

from betaforge.storage import EvidenceStore
from betaforge.tools import EvidenceTools


class ToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        source=self.root/'source';source.mkdir()
        payload={'instrument':426,'reports':[{'year':2025,'period':5,'report_Start_Date':'2025-01-01','report_End_Date':'2025-12-31','currency':'SEK','currency_Ratio':1,'revenues':10.25}]}
        body=json.dumps(payload).encode();(source/'year.json').write_bytes(body)
        (source/'manifest.json').write_text(json.dumps({'retrieved_at':'2026-01-01T00:00:00Z','requests':[{'endpoint':'/v1/instruments/426/reports/year','parameters':{'original':1},'file':'year.json','http_status':200,'sha256':hashlib.sha256(body).hexdigest()}]}))
        with EvidenceStore(self.root/'live/evidence.sqlite3') as store:
            store.ingest_snapshot(source);store.freeze(self.root/'snapshot')
        reports=self.root/'reports';(reports/'prepared').mkdir(parents=True);(reports/'sources').mkdir()
        pages=[{'page':1,'text':'Net revenue was 10.25 million SEK.'},{'page':2,'text':'A second complete page.'}]
        p=reports/'prepared/example.json';p.write_text(json.dumps(pages))
        pdf=reports/'sources/example.pdf';pdf.write_bytes(b'%PDF-test-fixture')
        (reports/'prepared/index.json').write_text(json.dumps({'reports':[{'report_id':'example','pages':2,'source_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'prepared_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}))
        self.packet=self.root/'packet.json';self.packet.write_text(json.dumps({'snapshot_dir':'snapshot','reports_dir':'reports','instrument_id':426}))
        self.tools=EvidenceTools(self.packet,self.root/'run')

    def tearDown(self):
        self.tools.store.close();self.temp.cleanup()

    def test_packet_cannot_silently_select_a_company(self):
        packet=json.loads(self.packet.read_text())
        for value in (None,True,'426',0,-1):
            with self.subTest(value=value):
                changed=dict(packet)
                if value is None:
                    del changed['instrument_id']
                else:
                    changed['instrument_id']=value
                self.packet.write_text(json.dumps(changed))
                directory=self.root/'invalid-identity'
                with self.assertRaisesRegex(ValueError,'explicit positive integer instrument_id'):
                    EvidenceTools(self.packet,directory)
                self.assertFalse(directory.exists())
        self.packet.write_text(json.dumps(packet))

    def test_search_does_not_satisfy_reading_and_full_pages_do(self):
        self.tools.search_reports('revenue')
        self.assertFalse(self.tools.coverage()['complete'])
        result=self.tools.read_report('example',1)
        self.assertEqual(result['delivered_pages'],[1,2]);self.assertTrue(self.tools.coverage()['complete'])
        with self.assertRaises(ValueError):self.tools.read_report('../secret',1)
        with self.assertRaises(ValueError):self.tools.read_report('example',3)

    def test_calculations_load_saved_exact_values_and_reject_fabricated_ids(self):
        observation=self.tools.get_financials(fields=['revenues'])['observations'][0]
        assumption=self.tools.record_input('0.1','Explicit test margin','ratio','assumption')
        result=self.tools.calculate('multiply',[observation['id'],assumption['id']],'Test EBIT','SEK')
        self.assertEqual(result['result'],'1025000.000')
        self.assertEqual(result['inputs'][0]['source_id'],observation['source_id'])
        shares=self.tools.record_input('2000000','Actual shares','shares','assumption')
        per_share=self.tools.calculate('divide',[observation['id'],shares['id']],'Revenue per share','SEK/share')
        self.assertEqual(per_share['result'],'5.125')
        self.assertEqual(per_share['unit'],'SEK/shares')
        dollars=self.tools.record_input('1','USD input','USD','assumption')
        with self.assertRaisesRegex(ValueError,'Incompatible'):
            self.tools.calculate('add',[observation['id'],dollars['id']],'Mixed currency','SEK')
        with self.assertRaises(ValueError):
            self.tools.calculate('multiply',[observation['id'],assumption['id']],'Mislabelled millions','MSEK')
        with self.assertRaises(ValueError):self.tools.calculate('add',['fiction',assumption['id']],'bad','MSEK')
        with self.assertRaises(ValueError):self.tools.record_input('NaN','bad','ratio','assumption')
        zero=self.tools.record_input('0','zero','ratio','assumption')
        with self.assertRaises(ValueError):self.tools.calculate('divide',[assumption['id'],zero['id']],'bad','ratio')

    def test_report_quote_required_and_audited(self):
        with self.assertRaises(ValueError):self.tools.record_input('9','fake revenue','MSEK','report','example',1,'The report never said this')
        value=self.tools.record_input('10.25','Revenue','MSEK','report','example',1,'Net revenue was 10.25 million SEK.')
        self.assertEqual(value['status'],'analyst_extracted_not_independently_reconciled')

    def test_named_formula_scales_once_and_reuses_intermediate_without_new_arithmetic(self):
        revenue = self.tools.get_financials(fields=['revenues'])['observations'][0]
        margin = self.tools.record_input('0.10','Forecast operating margin','fraction','assumption')
        result = self.tools.calculate_financial('revenue_ebit', {'revenue':revenue['id'],'ebit_margin':margin['id']},
                                                'Forecast EBIT','FY2025 source revenue; explicit forecast margin')
        self.assertEqual(Decimal(result['result']), Decimal('1025000'))
        named = self.tools.resolve_input(result['id']+'#ebit')
        self.assertEqual(named['value'], result['result'])
        self.assertEqual(named['scale'],'1')
        self.assertEqual(len(self.tools.state['calculations']),1)
        wrong = self.tools.record_input('10','Percent is not a fraction','percent','assumption')
        with self.assertRaisesRegex(ValueError,'fraction/percent'):
            self.tools.calculate_financial('revenue_ebit', {'revenue':revenue['id'],'ebit_margin':wrong['id']},'Bad margin','Explicit basis')
        usd = self.tools.record_input('10','USD revenue','USD','assumption')
        with self.assertRaisesRegex(ValueError,'currency'):
            self.tools.calculate_financial('revenue_ebit', {'revenue':usd['id'],'ebit_margin':margin['id']},'Bad currency','Explicit basis')

    def test_missing_cash_input_keeps_known_intermediate_but_cannot_reuse_missing_primary(self):
        cfo = self.tools.record_input('10','CFO','SEK','assumption')
        capex = self.tools.record_input('3','Cash capex magnitude','SEK','assumption')
        result = self.tools.calculate_financial('group_cash_conversion', {'cfo':cfo['id'],'cash_capex':capex['id']},
                                                'Group cash conversion','Test group flow; interest and lease principal unresolved')
        self.assertIsNone(result['result'])
        self.assertEqual(self.tools.resolve_input(result['id']+'#cash_after_capex')['value'],'7')
        with self.assertRaisesRegex(ValueError,'primary output is unavailable'):
            self.tools.resolve_input(result['id'])
        with self.assertRaisesRegex(ValueError,'unavailable named'):
            self.tools.resolve_input(result['id']+'#conversion_percent')

    def test_known_period_mismatch_rejected_before_financial_formula(self):
        first={'field':'ebit','period_start':'2025-01-01','period_end':'2025-12-31'}
        second={'field':'revenue','period_start':'2026-01-01','period_end':'2026-12-31'}
        with self.assertRaisesRegex(ValueError,'incompatible period'):
            self.tools._financial_periods('ebit_margin',[first,second])
        for formula,field in [('pe','diluted_eps'),('ev_ebit','ebit')]:
            with self.subTest(formula=formula), self.assertRaisesRegex(ValueError,'annual or R12'):
                self.tools._financial_periods(formula,[{'field':field,'report_type':'quarter'}])
        annual={'field':'ebit','report_type':'year','period_start':'2025-01-01','period_end':'2025-12-31'}
        closing={'field':'invested_capital_end','period_end':'2025-12-31'}
        opening={'field':'invested_capital_start','period_end':'2021-12-31'}
        with self.assertRaisesRegex(ValueError,'Opening capital date'):
            self.tools._financial_periods('operating_roic',[annual,closing,opening])
        opening['period_end']='2024-12-31'
        self.tools._financial_periods('operating_roic',[annual,closing,opening])

    def test_policy_contract_is_verified_and_available_to_analyst(self):
        self.tools.store.close()
        policy=self.root/'policy.md';policy.write_text('Adopted policy v1')
        calculations=self.root/'calculations.md';calculations.write_text('Named formulas v1')
        packet=json.loads(self.packet.read_text())
        packet['analysis_contract']={name:{'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                                     for name,path in [('policy',policy),('calculations',calculations)]}
        self.packet.write_text(json.dumps(packet))
        self.tools=EvidenceTools(self.packet,self.root/'policy-run')
        self.assertEqual(self.tools.get_calculation_definitions()['analysis_contract']['policy'],'Adopted policy v1')
        self.assertIn('analysis_contract', self.tools.identity)
        policy.write_text('Changed policy')
        with self.assertRaisesRegex(ValueError,'contract hash'):
            EvidenceTools(self.packet,self.root/'tampered-policy-run')

    def test_market_context_is_verified_before_use_or_resume(self):
        self.tools.store.close()
        market=self.root/'market.json'; market.write_text('{"series":"SIXRX"}')
        packet=json.loads(self.packet.read_text())
        packet['market_benchmark_context']={'context_path':'market.json','files':[
            {'path':'market.json','sha256':hashlib.sha256(market.read_bytes()).hexdigest()}]}
        self.packet.write_text(json.dumps(packet))
        self.tools=EvidenceTools(self.packet,self.root/'market-run')
        self.assertIn('market_benchmark_context',self.tools.identity)
        market.write_text('{"series":"other"}')
        with self.assertRaisesRegex(ValueError,'Benchmark context hash'):
            EvidenceTools(self.packet,self.root/'bad-market-run')

    def test_fractional_power_supports_annualized_return_with_unit_guards(self):
        one=self.tools.record_input('1','One','ratio','assumption')
        three=self.tools.record_input('3','Years','ratio','assumption')
        exponent=self.tools.calculate('divide',[one['id'],three['id']],'Annualization exponent','ratio')
        growth=self.tools.record_input('1.728','Three-year total return factor','ratio','assumption')
        result=self.tools.calculate('power',[growth['id'],exponent['id']],'Annual return factor','ratio')
        self.assertLess(abs(Decimal(result['result'])-Decimal('1.2')),Decimal('1e-35'))
        cash=self.tools.record_input('8','Cash','SEK','assumption')
        negative=self.tools.record_input('-8','Negative factor','ratio','assumption')
        for invalid in (cash,negative):
            with self.assertRaisesRegex(ValueError,'positive dimensionless'):
                self.tools.calculate('power',[invalid['id'],exponent['id']],'Invalid root','ratio')

    def test_resume_checks_identity_and_preserves_coverage(self):
        self.tools.call('read_report',{'report_id':'example','start_page':1},'call-1')
        resumed=EvidenceTools(self.packet,self.root/'run',resume=True)
        self.assertTrue(resumed.coverage()['complete']);resumed.store.close()
        self.packet.write_text(self.packet.read_text()+' ')
        with self.assertRaises(ValueError):EvidenceTools(self.packet,self.root/'run',resume=True)

    def test_frozen_database_tamper_rejected(self):
        with (self.root/'snapshot/evidence.sqlite3').open('ab') as file:file.write(b'corrupt')
        with self.assertRaises(ValueError):EvidenceTools(self.packet,self.root/'newrun')

    def test_research_round_limits_and_evidence_validation(self):
        with self.assertRaises(ValueError):self.tools.finish_research_round('too early',[],False)
        self.tools.read_report('example',1)
        with self.assertRaises(ValueError):self.tools.finish_research_round('invented',['unknown'],False)
        first=self.tools.finish_research_round('reviewed page',['example:p1'],False)
        self.assertFalse(first['stop'])
        self.assertFalse(self.tools.finish_research_round('no new evidence',[],False)['stop'])
        self.assertTrue(self.tools.finish_research_round('still no new evidence',[],False)['stop'])
        self.tools.save()
        denied=self.tools.call('read_report',{'report_id':'example','start_page':1},'closed')
        self.assertFalse(denied['success'])
        self.assertTrue(self.tools.state['research_closed'])
        resumed=EvidenceTools(self.packet,self.root/'run',resume=True)
        self.assertTrue(resumed.state['research_closed']);resumed.store.close()


if __name__=='__main__':unittest.main()
