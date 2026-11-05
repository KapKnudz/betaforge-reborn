import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_codex_packet as packet
from betaforge.tools import EvidenceTools


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reports = self.root / "reports"
        (self.reports / "sources").mkdir(parents=True)
        (self.reports / "prepared").mkdir()
        pdf = self.reports / "sources/issuer-test.pdf"
        pdf.write_bytes(b"%PDF-test-evidence")
        pages = self.reports / "prepared/issuer-test.json"
        pages.write_text('[{"page":1,"text":"Revenue 10"}]')
        self.index = {"reports": [{"report_id": "issuer-test", "pages": 1,
                                  "source_sha256": packet.digest(pdf), "prepared_sha256": packet.digest(pages)}]}
        (self.reports / "prepared/index.json").write_text(json.dumps(self.index))
        (self.reports / "source-manifest.json").write_text('{"documents":[]}')
        (self.root / "docs").mkdir()
        (self.root / "docs/analysis-policy.md").write_text("Test adopted policy")
        (self.root / "docs/calculations.md").write_text("Test explicit formulas")
        self.prompt = self.root / "company-prompt.md"
        self.prompt.write_text("Test prompt")
        self.facts = self.root / "facts.json"
        self.facts.write_text(json.dumps({"instrument_id": 426, "mapping_version": "test",
                                         "observed_at": "2026-11-01T00:00:00Z", "facts": []}))
        self.input = self.root / "input"
        self.input.mkdir()
        requests = []
        for name, endpoint, payload in [
            ("instruments", "/v1/instruments", {"instruments": [{"insId": 426, "stockPriceCurrency": "SEK"}]}),
            ("prices", "/v1/instruments/426/stockprices", {"instrument": 426, "stockPricesList": [{"d": "2026-10-30", "c": 172.2}]})]:
            body = json.dumps(payload).encode()
            (self.input / (name + ".json")).write_bytes(body)
            requests.append({"endpoint": endpoint, "http_status": 200, "file": name + ".json",
                             "sha256": hashlib.sha256(body).hexdigest(), "parameters": {}})
        (self.input / "manifest.json").write_text(json.dumps({"retrieved_at": "2026-11-01T00:00:00Z", "requests": requests}))

    def build(self, **kwargs):
        with patch.object(packet, "ROOT", self.root):
            return packet.prepare([self.input], self.root / "published", self.root / "store/evidence.sqlite3", kwargs.pop("facts_path", self.facts), self.reports,
                                  analysis_date=kwargs.pop("analysis_date", "2026-11-01"),
                                  instrument_id=kwargs.pop("instrument_id", 426), prompt_path=kwargs.pop("prompt_path", self.prompt), **kwargs)

    def test_packet_preserves_independent_corpus_and_current_price(self):
        result = self.build()
        data = json.loads(result.read_text())
        self.assertIn('"metric": "price_close"', data["context"])
        copied = result.parent / "reports/sources/issuer-test.pdf"
        original = self.reports / "sources/issuer-test.pdf"
        self.assertEqual(packet.digest(copied), packet.digest(original))
        original.write_bytes(b"changed later")
        self.assertEqual(packet.digest(copied), self.index["reports"][0]["source_sha256"])
        self.assertIn("Test adopted policy", data["context"])
        self.assertIn("Test explicit formulas", data["context"])
        self.assertEqual(data["required_reports"], ["issuer-test"])
        for item in data["analysis_contract"].values():
            self.assertFalse(Path(item["path"]).is_absolute())
            self.assertEqual(packet.digest(result.parent / item["path"]), item["sha256"])
        (self.root / "docs/analysis-policy.md").write_text("New policy after the run")
        frozen_policy = result.parent / data["analysis_contract"]["policy"]["path"]
        self.assertEqual(frozen_policy.read_text(), "Test adopted policy")
        with self.assertRaises(FileExistsError):
            self.build()

    def test_corrupt_report_does_not_publish_partial_packet(self):
        (self.reports / "sources/issuer-test.pdf").write_bytes(b"not the frozen report")
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse((self.root / "published").exists())
        self.assertFalse(list(self.root.glob('.prepare-*')))

    def archive_fixture(self):
        annuals = [f"issuer-annual-{year}" for year in range(2021, 2026)]
        current = ["issuer-q1-2026", "issuer-q2-2026", "issuer-q3-2026"]
        for rid in annuals + current:
            for folder, suffix in (("sources", ".pdf"), ("prepared", ".json")):
                original = self.reports / folder / ("issuer-test" + suffix)
                (original.parent / (rid + suffix)).write_bytes(original.read_bytes())
            self.index["reports"].append({**self.index["reports"][0], "report_id": rid})
        (self.reports / "prepared/index.json").write_text(json.dumps(self.index))
        return annuals + current

    def test_required_subset_keeps_older_archive_reports_frozen_and_readable(self):
        required = self.archive_fixture()
        result = self.build(required_reports=required)
        data = json.loads(result.read_text())
        self.assertEqual(data["required_reports"], required)
        self.assertTrue((result.parent / "reports/sources/issuer-test.pdf").exists())
        tools = EvidenceTools(result, self.root / "subset-run")
        try:
            self.assertEqual(tools.required, required)
            self.assertEqual(len(tools.catalogue()["reports"]), 9)
            self.assertEqual(tools.read_report("issuer-test", 1)["delivered_pages"], [1])
        finally:
            tools.store.close()

    def test_invalid_required_selection_is_rejected_without_publication(self):
        for required in ([], ["unknown"], ["issuer-test", "issuer-test"], "issuer-test", [None]):
            with self.subTest(required=required), self.assertRaisesRegex(ValueError, "Required reports"):
                self.build(required_reports=required)
            self.assertFalse((self.root / "published").exists())
            self.assertFalse((self.root / "store").exists())
            self.assertFalse(list(self.root.glob('.prepare-*')))

    def test_invalid_or_post_cutoff_report_publication_is_rejected(self):
        for publication in ("2026-09-31", "20261101", "2026-11-02"):
            (self.reports / "source-manifest.json").write_text(json.dumps({"documents": [
                {"report_id": "issuer-test", "publication_date": publication}]}))
            with self.subTest(publication=publication), self.assertRaises(ValueError):
                self.build()
            self.assertFalse((self.root / "published").exists())
            self.assertFalse((self.root / "store").exists())
            self.assertFalse(list(self.root.glob('.prepare-*')))

    def test_known_cutoff_and_unknown_publication_dates_are_preserved_with_limit(self):
        required = self.archive_fixture()
        documents = [{"report_id": "issuer-test", "publication_date": None}]
        documents.extend({"report_id": rid, "publication_date": "2026-11-01"} for rid in required)
        documents[-1].pop("publication_date")
        manifest = json.dumps({"documents": documents}).encode()
        (self.reports / "source-manifest.json").write_bytes(manifest)
        result = self.build(required_reports=required)
        self.assertEqual((result.parent / "reports/source-manifest.json").read_bytes(), manifest)
        data = json.loads(result.read_text())
        self.assertEqual(data["required_reports"], required)
        self.assertIn("Missing or null report publication dates remain unknown", data["context"])
        self.assertIn("not an automatic backtest", data["context"])

    def test_nonrequired_archive_report_still_requires_matching_hashes(self):
        required = self.archive_fixture()
        (self.reports / "sources/issuer-test.pdf").write_bytes(b"changed archive")
        with self.assertRaisesRegex(ValueError, "fixed source hashes"):
            self.build(required_reports=required)
        self.assertFalse((self.root / "published").exists())
        self.assertFalse(list(self.root.glob('.prepare-*')))

    def test_financial_context_keeps_period_provider_and_source_dates_distinct(self):
        payload = {"instrument": 426, "reports": [{
            "year": 2025, "period": 5, "report_Start_Date": "2025-01-01",
            "report_End_Date": "2025-12-31", "report_Date": "2026-03-01",
            "currency": "SEK", "net_Sales": 10}]}
        body = json.dumps(payload).encode()
        (self.input / "reports.json").write_bytes(body)
        manifest = json.loads((self.input / "manifest.json").read_text())
        manifest["requests"].append({"endpoint": "/v1/instruments/426/reports/year",
                                     "parameters": {"original": 1}, "http_status": 200,
                                     "file": "reports.json", "sha256": hashlib.sha256(body).hexdigest()})
        (self.input / "manifest.json").write_text(json.dumps(manifest))
        data = json.loads(self.build().read_text())
        context = data["context"]
        foundation, _ = json.JSONDecoder().raw_decode(context[context.index('{'):])
        revenue = next(row for row in foundation["financials"] if row["metric"] == "net_Sales")
        self.assertEqual(revenue["period_start"], "2025-01-01")
        self.assertEqual(revenue["period_end"], "2025-12-31")
        self.assertEqual(revenue["provider_report_date"], "2026-03-01")
        self.assertEqual(revenue["source_first_captured_at"], "2026-11-01T00:00:00+00:00")
        self.assertEqual(revenue["source_last_successful_check_at"], "2026-11-01T00:00:00+00:00")
        self.assertIn("definition validation is separate", context)

    def test_instrument_date_prompt_and_additional_facts_are_explicit(self):
        manifest = json.loads((self.input / "manifest.json").read_text())
        for request in manifest["requests"]:
            path = self.input / request["file"]
            payload = json.loads(path.read_text())
            if "instruments" in payload:
                payload["instruments"][0]["insId"] = 777
            else:
                payload["instrument"] = 777
                payload["stockPricesList"].append({"d": "2026-11-04", "c": 999})
            body = json.dumps(payload).encode()
            path.write_bytes(body)
            request["sha256"] = hashlib.sha256(body).hexdigest()
            request["endpoint"] = request["endpoint"].replace("/426/", "/777/")
        (self.input / "manifest.json").write_text(json.dumps(manifest))
        base = json.loads(self.facts.read_text())
        base["instrument_id"] = 777
        self.facts.write_text(json.dumps(base))
        extra = self.root / "extra.json"
        extra.write_text(json.dumps({**base, "mapping_version": "extra", "facts": [{
            "metric": "cash_capex", "value": "2", "unit": "SEK", "scale": "1000000",
            "report_type": "year", "year": 2025, "period": 5, "kind": "flow", "basis": "cash outflow",
            "status": "matched", "period_start": "2025-01-01", "period_end": "2025-12-31",
            "evidence": {"report_id": "issuer-test", "page": 1,
                         "sha256": self.index["reports"][0]["source_sha256"]}}]}))
        result = self.build(instrument_id=777, analysis_date="2026-11-03", prompt_path=self.prompt, extra_facts=[extra])
        data = json.loads(result.read_text())
        self.assertEqual(data["instrument_id"], 777)
        self.assertEqual(data["analysis_date"], "2026-11-03")
        self.assertIn('"value": "172.2"', data["context"])
        self.assertNotIn('"value": "999"', data["context"])
        self.assertIn("No company-specific mapping note supplied", data["context"])
        saved_extra = result.parent / data["extra_report_facts"][0]["path"]
        self.assertEqual(saved_extra.read_bytes(), extra.read_bytes())
        self.assertEqual(packet.digest(saved_extra), data["extra_report_facts"][0]["sha256"])
        with packet.EvidenceStore(result.parent / "snapshot/evidence.sqlite3", readonly=True) as store:
            self.assertEqual(store.query_financials(777, fields=["cash_capex"])[0]["value"], "2")
        tools=EvidenceTools(result,self.root/'other-issuer-run')
        try:
            self.assertEqual(tools.catalogue()['instrument_id'],777)
            self.assertEqual(tools.read_report('issuer-test',1)['delivered_pages'],[1])
            rows=tools.get_financials(fields=['cash_capex'])['observations']
            self.assertEqual([row['instrument_id'] for row in rows],[777])
        finally:
            tools.store.close()

    def test_company_inputs_are_required_and_report_facts_can_be_absent(self):
        for value in (None,True,0,'426'):
            with self.subTest(instrument=value), self.assertRaisesRegex(ValueError,'Instrument ID'):
                self.build(instrument_id=value)
        with self.assertRaisesRegex(ValueError,'explicit company analysis prompt'):
            self.build(prompt_path=None)
        self.assertFalse((self.root/'published').exists())
        self.assertFalse((self.root/'store').exists())
        self.facts.unlink()
        result=self.build(facts_path=None)
        data=json.loads(result.read_text())
        self.assertFalse((result.parent/'reconciled-facts.json').exists())
        self.assertEqual(data['extra_report_facts'],[])
        self.assertIn('No company-specific mapping note supplied',data['context'])

    def test_bad_date_or_wrong_company_fact_is_rejected_before_publication(self):
        with self.assertRaises(ValueError):
            self.build(analysis_date="2026-02-30")
        extra = self.root / "wrong-company.json"
        extra.write_text(json.dumps({"instrument_id": 999}))
        with self.assertRaisesRegex(ValueError, "instrument"):
            self.build(extra_facts=[extra])
        self.assertFalse((self.root / "published").exists())
        self.assertFalse((self.root / "store").exists())

    def benchmark_fixture(self):
        base = self.root / "industry"
        (base / "raw").mkdir(parents=True)
        raw = base / "raw/marginGlobal.xls"
        raw.write_bytes(b"saved workbook bytes")
        manifest = {"schema_version": 1, "status": "complete", "sources": [{
            "id": "margins", "file": "raw/marginGlobal.xls", "sha256": packet.digest(raw)}]}
        (base / "manifest.json").write_text(json.dumps(manifest))
        context = {"schema_version": 1, "manifest": "manifest.json", "manifest_sha256": packet.digest(base / "manifest.json"),
                   "datasets": [{"id": "margins", "raw_file": "raw/marginGlobal.xls", "raw_sha256": packet.digest(raw),
                                 "selected_rows": [{"industry": "Metals & Mining", "cells": []}],
                                 "caveats": ["Internal source date differs; freshness is unresolved"]}]}
        path = base / "context.json"
        path.write_text(json.dumps(context))
        return path

    def test_benchmark_context_and_source_files_are_frozen_with_caveats(self):
        context = self.benchmark_fixture()
        result = self.build(benchmark_context=context)
        data = json.loads(result.read_text())
        self.assertIn("Metals & Mining", data["context"])
        self.assertIn("freshness is unresolved", data["context"])
        self.assertEqual(len(data["benchmark_context"]["files"]), 3)
        for item in data["benchmark_context"]["files"]:
            self.assertFalse(Path(item["path"]).is_absolute())
            self.assertEqual(packet.digest(result.parent / item["path"]), item["sha256"])
        original = context.parent / "raw/marginGlobal.xls"
        original.write_bytes(b"later replacement")
        self.assertEqual((result.parent / "benchmarks/raw/marginGlobal.xls").read_bytes(), b"saved workbook bytes")

    def test_corrupt_or_escaping_benchmark_sources_cannot_publish(self):
        context = self.benchmark_fixture()
        (context.parent / "raw/marginGlobal.xls").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "identity"):
            self.build(benchmark_context=context)
        self.assertFalse((self.root / "published").exists())
        self.assertFalse(list(self.root.glob('.prepare-*')))
        for value in ("../outside.json", "/absolute/path.json", "raw\\windows.xls"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                packet.relative_source(context.parent, value)

    def test_market_benchmark_raw_evidence_is_frozen_and_corruption_rejected(self):
        base=self.root/'market'; (base/'raw').mkdir(parents=True)
        raw=base/'raw/levels.html'; raw.write_text('Official total return levels')
        manifest=base/'manifest.json'
        manifest.write_text(json.dumps({'schema_version':1,'series':'SIXRX','analysis_date':'2026-11-01','sources':[
            {'id':'levels','file':'raw/levels.html','sha256':packet.digest(raw)}]}))
        context=base/'context.json'
        context.write_text(json.dumps({'schema_version':1,'manifest':'manifest.json','manifest_sha256':packet.digest(manifest),
                                       'benchmark':{'symbol':'SIXRX','currency':'SEK','return_type':'gross_total_return'},'analysis_date':'2026-11-01',
                                       'status':'verified_from_rounded_public_levels'}))
        result=self.build(market_benchmark_context=context)
        data=json.loads(result.read_text())
        self.assertIn('SIXRX',data['context'])
        self.assertEqual(len(data['market_benchmark_context']['files']),3)
        self.assertEqual((result.parent/'market-benchmark/raw/levels.html').read_bytes(),raw.read_bytes())
        with self.assertRaisesRegex(ValueError,'analysis date'):
            packet.copy_market_benchmark(context,self.root/'wrong-date-copy','2026-11-02')
        raw.write_text('Changed levels')
        with self.assertRaisesRegex(ValueError,'source identity'):
            packet.copy_market_benchmark(context,self.root/'bad-copy')


if __name__ == "__main__":
    unittest.main()
