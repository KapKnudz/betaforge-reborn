from copy import deepcopy
from decimal import Decimal
import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from examples.granges.scripts.build_financial_review import build_review, load_market_benchmark, load_quality_facts, normalized, verify_packet, verify_quote
from examples.granges.scripts import fetch_granges, prepare_granges


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "data/granges-codex/packet-20261101"
FACTS = ROOT / "examples/granges/data/quality-facts-20261103.json"
RUN = ROOT / "data/granges-codex/runs/20261101-full"
BENCHMARK = ROOT / "data/benchmarks/sixrx/20261103T121617260724Z/context.json"


class ExamplePreparationTests(unittest.TestCase):
    def test_existing_prepared_evidence_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            prepared = base / "prepared"
            prepared.mkdir()
            saved = prepared / "index.json"
            saved.write_text('unchanged frozen evidence')
            with patch.object(prepare_granges, "BASE", base):
                with self.assertRaises(FileExistsError):
                    prepare_granges.prepare()
            self.assertEqual(saved.read_text(), 'unchanged frozen evidence')

    def test_case_manifest_populates_private_corpus_without_network_or_replacement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / "data/granges-walkthrough"
            case = root / "example-data"
            case.mkdir()
            pdf = base / "sources/report.pdf"
            pdf.parent.mkdir(parents=True)
            pdf.write_bytes(b"%PDF-saved-fixture")
            manifest = {"documents": [{"report_id": "granges-fixture", "local_path": "data/granges-walkthrough/sources/report.pdf",
                         "source_url": "https://www.granges.com/fixture.pdf", "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()}]}
            content = json.dumps(manifest).encode()
            (case / "source-manifest.json").write_bytes(content)
            with patch.multiple(fetch_granges, ROOT=root, BASE=base, CASE_DATA=case), patch.object(fetch_granges, "urlopen") as network:
                fetch_granges.fetch()
                self.assertEqual((base / "source-manifest.json").read_bytes(), content)
                (base / "source-manifest.json").write_text("different snapshot")
                with self.assertRaisesRegex(ValueError, "manifest differs"):
                    fetch_granges.fetch()
                network.assert_not_called()


class FinancialReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (PACKET / "snapshot/evidence.sqlite3").exists():
            raise unittest.SkipTest("Private frozen Gränges evidence is not installed")
        cls.manifest, cls.catalogue, cls.texts = verify_packet(PACKET)

    def test_quality_facts_have_verifiable_pages_and_quotes(self):
        records, notes = load_quality_facts(FACTS, self.catalogue, self.texts)
        self.assertEqual(len(records), 40)
        self.assertEqual(records[("trade_payables", 2025)]["value"], "3105")
        self.assertEqual(len(notes), 3)
        evidence = deepcopy(records[("trade_payables", 2025)]["evidence"])
        for field, value in (("sha256", "0" * 64), ("page", 10000), ("quote", "invented principal 69")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_quote(dict(evidence, **{field: value}), self.catalogue, self.texts)

    def test_review_keeps_cash_gaps_local_and_preserves_original_valuation(self):
        review = build_review(PACKET, FACTS, RUN, scenario_weights=[Decimal("0.25"), Decimal("0.55"), Decimal("0.20")])
        by_label = {c["label"]: c for c in review["calculations"]}
        cash = by_label["FY2025 group cash conversion before dividends"]
        self.assertEqual(cash["outputs"]["cash_after_capex_and_interest"]["value"], "289000000.0000")
        self.assertIsNone(cash["outputs"]["conversion_percent"]["value"])
        self.assertEqual(cash["missing_inputs"], ["lease_principal_outside_cfo"])
        quarter = by_label["Q3 2026 group cash bridge; only signed net interest disclosed"]
        self.assertEqual(Decimal(quarter["outputs"]["cash_after_capex_and_net_interest"]["value"]), 239000000)
        self.assertIn("interest_paid_outside_cfo", quarter["missing_inputs"])
        roic = by_label["FY2025 operating ROIC; explicit analyst operating-tax proxy"]
        self.assertEqual(roic["missing_inputs"], [])
        self.assertAlmostEqual(Decimal(roic["outputs"]["roic_percent"]["value"]), Decimal("8.575128673418562"), places=12)
        self.assertTrue(all(check for case in review["preserved_valuation"]["checks"].values() for check in case.values()))
        incremental = by_label["FY2025 reported group incremental margin; qualified"]
        self.assertIsNotNone(incremental["outputs"]["incremental_margin_percent"]["value"])
        self.assertTrue(any("organic" in warning for warning in incremental["warnings"]))
        weighted = by_label["Conditional analyst proposal: probability-weighted case values"]
        self.assertAlmostEqual(Decimal(weighted["outputs"]["expected_present_value"]["value"]), Decimal("155.38378421931"), places=10)
        self.assertIsNotNone(by_label["Conditional analyst proposal: IRR of expected cash flows"]["outputs"]["irr_percent"]["value"])
        self.assertTrue(any(c["formula"] == "ebit_margin" and c["outputs"]["margin_percent"]["value"] for c in review["calculations"]))

    def test_source_scale_currency_and_tax_assumption_are_explicit(self):
        self.assertEqual(normalized(dict(value="1.5", scale="1000000", unit="SEK", currency="SEK")), 1500000)
        for record in (dict(value="1", scale="1", unit="provider_defined"),
                       dict(value="1", scale="1", unit="currency"),
                       dict(value="1", scale="1", unit="currency", currency="USD"),
                       dict(value="1", scale="0", unit="SEK")):
            with self.assertRaises(ValueError):
                normalized(record)
        with self.assertRaisesRegex(ValueError, "requires a reason"):
            build_review(PACKET, FACTS, operating_tax_rate=Decimal("0.2"))

    def test_moved_example_cli_replays_from_outside_the_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "review"
            result = subprocess.run([
                sys.executable, str(ROOT / "examples/granges/scripts/build_financial_review.py"),
                "--output", str(output), "--scenario-weights", "0.25", "0.55", "0.20"],
                cwd=temp, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            review = json.loads((output / "review.json").read_text())
            self.assertTrue(all(check for case in review["preserved_valuation"]["checks"].values() for check in case.values()))
            self.assertEqual(Path(review["quality_facts"]), FACTS)

    def test_benchmark_checks_date_raw_sources_and_return_arithmetic(self):
        if not BENCHMARK.exists():
            self.skipTest("Private SIXRX source snapshot is not installed")
        result = load_market_benchmark(BENCHMARK, "2026-11-01")
        self.assertAlmostEqual(Decimal(result["reproduced_annualized_return_percent"]), Decimal("11.607798419547889"), places=12)
        with self.assertRaisesRegex(ValueError, "analysis date"):
            load_market_benchmark(BENCHMARK, "2026-11-02")
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "benchmark"
            shutil.copytree(BENCHMARK.parent, copied)
            context_path = copied / "context.json"
            manifest = json.loads((copied / "manifest.json").read_text())
            raw_path = copied / manifest["sources"][0]["file"]
            original = raw_path.read_bytes()
            raw_path.write_bytes(b"corrupted raw source")
            with self.assertRaisesRegex(ValueError, "raw source hash"):
                load_market_benchmark(context_path, "2026-11-01")
            raw_path.write_bytes(original)
            context = json.loads(context_path.read_text())
            context["calculation"]["annualized_return_percent"] = "99"
            context_path.write_text(json.dumps(context))
            with self.assertRaisesRegex(ValueError, "saved levels"):
                load_market_benchmark(context_path, "2026-11-01")


if __name__ == "__main__":
    unittest.main()
