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

from examples.granges.scripts.build_financial_review import annual_fact, build_review, calculation_period, load_market_benchmark, load_quality_facts, normalized, select_fact, verify_packet, verify_quote
from examples.granges.scripts import fetch_granges, prepare_granges
from examples.granges.scripts.build_material_inputs import build_material_inputs


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "data/granges-codex/packet-20261101"
FACTS = ROOT / "examples/granges/data/quality-facts-20261103.json"
RUN = ROOT / "data/granges-codex/runs/20261101-full"
BENCHMARK = ROOT / "data/benchmarks/sixrx/20261103T121617260724Z/context.json"
CURRENT_FACTS = ROOT / "data/material-mapping-work/granges-current-facts-20261104.json"


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


class QualityFactPeriodTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = {"fixture": dict(source_sha256="source-hash", prepared_sha256="text-hash", pages=1)}
        self.texts = {"fixture": [{"text": "Synthetic sales 80 90 100"}]}
        self.evidence = dict(report_id="fixture", sha256="source-hash", prepared_sha256="text-hash",
                             page=1, quote="Synthetic sales 80 90 100", source_pointer="/0/text")

    def fact(self, report_type="quarter", **overrides):
        periods = {"year": (5, "2026-01-01", "2026-12-31"),
                   "quarter": (3, "2026-07-01", "2026-09-30"),
                   "r12": (3, "2025-10-01", "2026-09-30")}
        period, start, end = periods[report_type]
        return dict(dict(metric="net_sales", report_type=report_type, year=2026, period=period,
                         period_start=start, period_end=end, kind="flow", value="100", scale="1",
                         unit="SEK", currency="SEK", evidence=self.evidence), **overrides)

    def load(self, facts, cutoff="2027-01-01"):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "facts.json"
            path.write_text(json.dumps(dict(instrument_id=426, facts=facts)))
            return load_quality_facts(path, self.catalogue, self.texts, cutoff)[0]

    def test_mixed_periods_coexist_and_annual_selection_is_explicit(self):
        records = self.load([self.fact(kind) for kind in ("year", "quarter", "r12")])
        self.assertEqual(len(records), 3)
        self.assertEqual(annual_fact(records, "net_sales", 2026)["report_type"], "year")
        self.assertEqual(select_fact(records, "net_sales", 2026, "r12", 3)["period_start"], "2025-10-01")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.load([self.fact(), self.fact()])

    def test_future_and_inconsistent_flow_or_stock_dates_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "frozen analysis date"):
            self.load([self.fact("year")], "2026-11-01")
        for bad in (self.fact(period_end="2026-08-31"), self.fact(period_start="2026-01-01"),
                    self.fact(kind="stock")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.load([bad])
        self.assertEqual(len(self.load([self.fact(kind="stock", period_start=None)])), 1)

    def test_capital_dates_follow_the_economic_flow_and_reject_mismatches(self):
        flow = self.fact("r12")
        opening = self.fact(kind="stock", period_start=None, year=2025, period_end="2025-09-30")
        closing = self.fact(kind="stock", period_start=None)
        inputs = dict(ebit=flow, invested_capital_start=opening, invested_capital_end=closing)
        _, period = calculation_period("operating_roic", inputs)
        self.assertEqual(period["period_start"], "2025-10-01")
        self.assertEqual(period["period_end"], "2026-09-30")
        self.assertEqual(period["report_type"], "r12")
        for field, day in (("invested_capital_start", "2025-12-31"), ("invested_capital_end", "2026-06-30")):
            wrong = {name: dict(record) for name, record in inputs.items()}
            wrong[field]["period_end"] = day
            with self.subTest(field=field), self.assertRaises(ValueError):
                calculation_period("operating_roic", wrong)
        with self.assertRaisesRegex(ValueError, "incompatible period_end"):
            calculation_period("invested_capital", dict(group_equity=opening, cash=closing))


class FinancialReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (PACKET / "snapshot/evidence.sqlite3").exists():
            raise unittest.SkipTest("Private frozen Gränges evidence is not installed")
        cls.manifest, cls.catalogue, cls.texts = verify_packet(PACKET)

    def test_quality_facts_have_verifiable_pages_and_quotes(self):
        records, notes = load_quality_facts(FACTS, self.catalogue, self.texts)
        self.assertEqual(len(records), 40)
        self.assertEqual(annual_fact(records, "trade_payables")["value"], "3105")
        self.assertEqual(len(notes), 3)
        evidence = deepcopy(annual_fact(records, "trade_payables")["evidence"])
        for field, value in (("sha256", "0" * 64), ("page", 10000), ("quote", "invented principal 69")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_quote(dict(evidence, **{field: value}), self.catalogue, self.texts)

    def test_material_decisions_preserve_results_and_separate_definition_from_match(self):
        if not CURRENT_FACTS.exists():
            self.skipTest("Private current-period facts are not installed")
        review = build_review(PACKET, FACTS, RUN, current_facts_path=CURRENT_FACTS)
        original = deepcopy(review)
        rows = build_material_inputs(review, PACKET)
        self.assertEqual(review, original)
        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        by_id = {row["id"]: row for row in rows}
        reported = by_id["r12-ebit"]
        self.assertEqual(reported["definition_status"], "documented")
        self.assertEqual(reported["candidates"][0]["reconciliation_status"], "matched")
        self.assertEqual(reported["candidates"][0]["definition_status"], "unresolved")
        self.assertEqual(by_id["diluted-eps"]["candidates"][0]["reconciliation_status"], "disagrees")
        self.assertIsNone(by_id["lease-principal-outside-cfo"]["selected"])
        self.assertTrue(by_id["operating-tax"]["selected"]["kind"] == "assumption")
        self.assertTrue(all(row["selection_reason"] and row["valuation_uses"] for row in rows))
        cfo = by_id["cfo"]
        self.assertEqual(cfo["reconciliation_status"], "derived_match")
        self.assertEqual(len(cfo["evidence"]), 2)
        self.assertEqual(Decimal(cfo["candidates"][0]["residual"]["value"]), 0)
        self.assertNotEqual(Decimal(cfo["candidates"][1]["residual"]["value"]), 0)
        self.assertTrue(all(item["record"]["derivation"]["inputs"] for item in cfo["candidates"]))
        self.assertIsNotNone(by_id["pensions"]["selected"]["period_end"])
        self.assertEqual(by_id["provider-ev"]["candidates"][0]["record"]["provider"], "borsdata")
        self.assertEqual(by_id["provider-ev"]["candidates"][0]["reconciliation_status"], "not_comparable")
        for case in ("bear", "base", "bull"):
            self.assertTrue(by_id[case + "-exit-multiple"]["evidence"])
            self.assertTrue(by_id[case + "-annual-retained-cash"]["evidence"])

    def test_explicit_report_cfo_preserves_selection_and_both_reconciliation_residuals(self):
        if not CURRENT_FACTS.exists():
            self.skipTest("Private current-period facts are not installed")
        original = build_review(PACKET, FACTS, RUN, current_facts_path=CURRENT_FACTS)
        decisions = {row["id"]: row for row in build_material_inputs(original, PACKET)}
        alternative = deepcopy(decisions["cfo"]["candidates"][1]["record"])
        fact = {key: alternative[key] for key in ("value", "unit", "scale", "currency", "report_type", "period_start", "period_end", "evidence", "derivation")}
        fact.update(metric="statutory_cash_flow_operations", year=2026, period=3,
                    kind="flow", basis="Explicit report annual plus current YTD less prior YTD", status="derived_match")
        source = json.loads(CURRENT_FACTS.read_text())
        annual_ytd_value = fact["value"]
        source["facts"].append(fact)
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "explicit-current-facts.json"
            for selected_value in (annual_ytd_value, str(Decimal(annual_ytd_value) + Decimal("0.5"))):
                with self.subTest(selected_value=selected_value):
                    source["facts"][-1]["value"] = selected_value
                    path.write_text(json.dumps(source))
                    review = build_review(PACKET, FACTS, RUN, current_facts_path=path)
                    cfo = next(row for row in build_material_inputs(review, PACKET) if row["id"] == "cfo")
                    self.assertEqual(cfo["selected"]["value"], selected_value)
                    self.assertEqual(len(cfo["candidates"]), 3)
                    residuals = [Decimal(item["residual"]["value"]) for item in cfo["candidates"]]
                    if selected_value == annual_ytd_value:
                        self.assertNotEqual(residuals[0], 0)
                        self.assertEqual(residuals[1], 0)
                        self.assertEqual(cfo["reconciliation_status"], "derived_match")
                    else:
                        self.assertTrue(all(residual != 0 for residual in residuals))
                        self.assertEqual(cfo["reconciliation_status"], "disagrees")

    def test_review_keeps_cash_gaps_local_and_preserves_original_valuation(self):
        review = build_review(PACKET, FACTS, RUN, scenario_weights=[Decimal("0.25"), Decimal("0.55"), Decimal("0.20")])
        self.assertNotIn("current_facts", review)
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

    def test_latest_diagnostics_match_periods_keep_cash_gaps_and_preserve_valuation(self):
        if not CURRENT_FACTS.exists():
            self.skipTest("Private current-period facts are not installed")
        review = build_review(PACKET, FACTS, RUN, scenario_weights=[Decimal("0.25"), Decimal("0.55"), Decimal("0.20")],
                              current_facts_path=CURRENT_FACTS)
        current, _ = load_quality_facts(CURRENT_FACTS, self.catalogue, self.texts, review["frozen_analysis_date"])
        by_label = {c["label"]: c for c in review["calculations"]}
        roic = by_label["R12 September 2026 operating ROIC; explicit analyst operating-tax proxy"]
        self.assertEqual((roic["report_type"], roic["period_start"], roic["period_end"]),
                         ("r12", "2025-10-01", "2026-09-30"))
        self.assertEqual(roic["inputs"]["invested_capital_start"]["period_end"], "2025-09-30")
        self.assertEqual(roic["inputs"]["invested_capital_end"]["period_end"], "2026-09-30")
        expected_capital = []
        for year in (2025, 2026):
            amounts = {metric: normalized(select_fact(current, metric, year, "quarter", 3)) for metric in
                       ("group_equity", "gross_debt_including_leases", "net_pension_liability",
                        "cash_and_equivalents", "associates_joint_ventures_book_value")}
            expected_capital.append(amounts["group_equity"] + amounts["gross_debt_including_leases"] +
                                    amounts["net_pension_liability"] - amounts["cash_and_equivalents"] -
                                    amounts["associates_joint_ventures_book_value"])
        expected_roic = (normalized(select_fact(current, "reported_operating_profit", 2026, "r12", 3)) *
                         (1 - Decimal(roic["inputs"]["operating_tax_rate"]["value"])) / (sum(expected_capital) / 2) * 100)
        self.assertAlmostEqual(Decimal(roic["outputs"]["roic_percent"]["value"]), expected_roic, places=12)
        cash = by_label["R12 September 2026 group cash conversion before dividends"]
        self.assertEqual(Decimal(cash["outputs"]["cash_after_capex"]["value"]),
                         normalized(cash["inputs"]["cfo"]) - normalized(cash["inputs"]["cash_capex"]))
        self.assertIsNone(cash["outputs"]["conversion_percent"]["value"])
        self.assertIn("interest_paid_outside_cfo", cash["missing_inputs"])
        self.assertIn("lease_principal_outside_cfo", cash["missing_inputs"])
        self.assertEqual(cash["report_type"], "r12")
        self.assertTrue(all(c["display_role"] == "current" for c in (roic, cash)))
        for label in ("Dated price / R12 reported diluted EPS",
                      "Provider-convention EV / R12 reported EBIT; separate from full claim bridge"):
            ratio = by_label[label]
            self.assertEqual((ratio["display_role"], ratio["report_type"], ratio["period_end"]),
                             ("current", "r12", "2026-09-30"))
            self.assertIn("earnings denominator", ratio["current_period_reason"])
        pe = by_label["Dated price / R12 reported diluted EPS"]
        self.assertEqual(pe["price_date"], pe["inputs"]["price"]["period_end"])
        self.assertNotEqual(pe["price_date"], pe["period_end"])
        self.assertEqual(review["current_facts_sha256"], hashlib.sha256(CURRENT_FACTS.read_bytes()).hexdigest())
        self.assertTrue(any("actual trade" in limit for limit in review["current_data_limits"]))
        self.assertTrue(all(check for case in review["preserved_valuation"]["checks"].values() for check in case.values()))

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
