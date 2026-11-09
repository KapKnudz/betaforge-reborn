import hashlib
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from betaforge.saved_view import MAX_BYTES, attach_reader_memo, build_saved_view, load_saved_view, validate_saved_view


def minimal_view():
    return {
        "schema_version": 1, "id": "sample-20261101",
        "company": {"name": "Sample", "ticker": "SAMP", "instrument_id": 1},
        "analysis_date": "2026-11-01", "reviewed_at": "2026-11-03T12:00:00Z",
        "method": "Saved scenario analysis", "price": None, "conclusion": "Conditional saved result",
        "scenarios": [], "probability": {"weights": {}, "basis": None, "status": "missing"},
        "calculations": [], "original_calculations": [], "interpretation": [], "notes": [],
        "narrative": "Saved report", "sources": [],
        "benchmark": {"candidate_annualized_return_percent": None, "benchmark_annualized_return_percent": None,
                      "difference_percentage_points": None, "interpretation": None, "limits": [], "context": None},
        "provenance": {"database_sha256": "a" * 64, "packet_sha256": "b" * 64,
                       "review_sha256": "c" * 64, "run_sha256": "d" * 64,
                       "summary_sha256": "e" * 64, "narrative_sha256": "f" * 64,
                       "model": "gpt-6.1-sol", "reasoning_effort": "high", "status": "completed",
                       "started_at": "2026-11-01T12:00:00Z", "finished_at": "2026-11-01T12:01:00Z", "coverage": {}},
    }


def material_input():
    record = {"id": "fact:revenue", "metric": "revenue", "value": "123.000000000000000001",
              "unit": "currency", "scale": "1000000", "currency": "SEK", "kind": "flow",
              "basis": "Group sales", "status": "matched", "report_type": "r12",
              "period_start": "2025-10-01", "period_end": "2026-09-30", "year": 2026, "period": 3,
              "source_id": "sample-interim", "pointer": "/facts/0", "evidence": {"report_id": "sample-interim", "page": 3}}
    return {"id": "revenue", "label": "Group sales", "definition": "Group revenue over the stated flow period",
            "definition_status": "documented", "reconciliation_status": "matched", "selected": record,
            "candidates": [{"record": dict(record, id="provider:revenue", provider="sample", status="unreviewed"),
                            "definition_status": "unresolved", "reconciliation_status": "matched",
                            "comparison_basis": "Same displayed amount; provider scope is unresolved",
                            "residual": {"value": "0.000000000000000000", "unit": "SEK million", "formula": "candidate minus selected"}}],
            "selection_reason": "Issuer states the operating revenue scope", "valuation_uses": ["Revenue × EBIT margin"],
            "limitations": ["Rounded issuer disclosure"], "evidence": [{"report_id": "sample-interim", "page": 3}]}


class SavedViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.packet = self.root / "packet"
        self.run = self.root / "run"
        self.review_path = self.root / "review.json"
        (self.packet / "snapshot").mkdir(parents=True)
        (self.packet / "reports/prepared").mkdir(parents=True)
        self.run.mkdir()
        database = self.packet / "snapshot/evidence.sqlite3"
        database.write_bytes(b"frozen fixture database")
        self.database_hash = self.digest(database)
        self.write(self.packet / "snapshot/manifest.json", {"database_sha256": self.database_hash})
        self.source = {"report_id": "sample-annual", "title": "Annual report", "borsdata_instrument_id": 1,
                       "reporting_period": {"start": "2025-01-01", "end": "2025-12-31"},
                       "publication_date": "2026-03-01", "source_url": "https://example.org/annual.pdf",
                       "sha256": "a" * 64, "local_path": "/private/research/source.pdf"}
        self.manifest = {"borsdata_instrument_id": 1, "documents": [self.source]}
        self.write(self.packet / "reports/source-manifest.json", self.manifest)
        self.prepared = {"report_id": "sample-annual", "pages": 12, "source_sha256": "a" * 64,
                         "prepared_sha256": "b" * 64}
        self.write(self.packet / "reports/prepared/index.json", {"reports": [self.prepared]})
        self.price = {"id": "obs:price", "instrument_id": 1, "value": "172.2000", "scale": "1",
                      "currency": "SEK", "unit": "currency/share", "basis": "Adjustment unknown",
                      "period_end": "2026-10-30", "source_id": "src:price", "status": "unreviewed"}
        self.packet_data = {"instrument_id": 1, "analysis_date": "2026-11-01", "snapshot_dir": "snapshot",
                            "reports_dir": "reports", "context": 'FROZEN FOUNDATION\n' + json.dumps({"latest_close": [self.price]})}
        self.write(self.packet / "packet.json", self.packet_data)
        self.originals = [{"operation": "divide", "inputs": [], "result": "168.140000000000000001",
                           "label": "Saved result", "unit": "SEK/share", "scale": "1", "basis": "Saved basis", "id": "calc:one"}]
        self.write(self.run / "inputs.json", [{"value": "1.000000000000000001"}])
        self.write(self.run / "calculations.json", self.originals)
        self.run_data = {"status": "completed", "smoke": False, "model": "gpt-6.1-sol", "reasoning_effort": "high",
                         "started_at": "2026-11-01T12:00:00Z", "finished_at": "2026-11-01T12:01:00Z",
                         "identity": {"packet_sha256": self.digest(self.packet / "packet.json"), "database_sha256": self.database_hash,
                                      "reports": {"sample-annual": ["a" * 64, "b" * 64]}},
                         "coverage": {"complete": True, "delivered_pages": 12, "total_pages": 12},
                         "turns": [{"secret": "Excluded run internals"}]}
        self.write(self.run / "run.json", self.run_data)
        self.summary = {"conclusion": "Conditional saved result", "scenarios": [
            {"name": "Base", "value": "168.1400", "unit": "SEK/share today",
             "basis": "Saved November 2029 target: 212.54 SEK/share", "calculation_ids": ["calc:one"]}],
            "notes": ["Saved summary note"]}
        self.write(self.run / "review-summary.json", self.summary)
        (self.run / "answer.md").write_text("# Saved narrative\n\nUnchanged prose.")
        self.named = {"id": "quality:one", "formula": "group_cash_conversion", "version": "1", "formula_text": "Saved named formula",
                      "inputs": {"cfo": {"value": "1.000000000000000001", "scale": "1000000", "status": "matched"}},
                      "options": {}, "outputs": {"conversion_percent": {"value": None, "unit": "percent"}},
                      "missing_inputs": ["lease_principal"], "warnings": ["Not parent-owner FCF"]}
        self.review = {"instrument_id": 1, "frozen_analysis_date": "2026-11-01", "reviewed_at": "2026-11-03T12:00:00Z",
                       "database_sha256": self.database_hash, "calculations": [self.named],
                       "preserved_valuation": {"inputs_sha256": self.digest(self.run / "inputs.json"),
                                               "calculations_sha256": self.digest(self.run / "calculations.json")},
                       "probability_proposal": {"weights": {"base": "1.0000"}, "basis": "Subjective proposed weights; not adopted"},
                       "notes": [{"id": "gap", "text": "Missing stays missing"}], "interpretation": ["Saved interpretation"],
                       "market_benchmark_comparison": {
                           "candidate_annualized_return_percent": None, "benchmark_annualized_return_percent": "11.60779841954788908461573210577814081810",
                           "difference_percentage_points": None, "interpretation": None, "limits": ["Rounded levels"],
                           "source": {"context_path": "/private/research/context.json", "context": {
                               "context_type": "historical_market_total_return", "rounded_source": True,
                               "benchmark": {"name": "Saved index", "symbol": "INDEX"}, "context_path": "/private/secret"}}}}
        self.write(self.review_path, self.review)

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value))

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def build(self):
        return build_saved_view(self.review_path, self.run, self.packet, "Sample", "SAMP", "sample-20261101", "Explicit CLI method")

    def test_copies_saved_decimals_missing_flags_and_proposed_weights(self):
        view = self.build()
        self.assertEqual(view["calculations"], [self.named])
        self.assertEqual(view["original_calculations"], self.originals)
        self.assertEqual(view["scenarios"][0], dict(self.summary["scenarios"][0], weight="1.0000"))
        self.assertEqual(view["price"]["value"], "172.2000")
        self.assertEqual(view["price"]["date"], "2026-10-30")
        self.assertEqual(view["probability"]["status"], "proposed")
        self.assertEqual(view["provenance"]["summary_sha256"], self.digest(self.run / "review-summary.json"))
        self.assertEqual(view["provenance"]["narrative_sha256"], self.digest(self.run / "answer.md"))
        self.assertIsNone(view["benchmark"]["candidate_annualized_return_percent"])
        self.assertTrue(view["benchmark"]["context"]["rounded_source"])
        self.assertEqual(view["notes"], self.review["notes"] + self.summary["notes"])
        self.assertNotIn("/private/", json.dumps(view))
        self.assertNotIn("Excluded run internals", json.dumps(view))
        output = self.root / "view.json"
        self.write(output, view)
        self.assertEqual(load_saved_view(output), view)

    def test_optional_material_decisions_recency_and_hashes_are_preserved(self):
        self.review.update(material_inputs=[material_input()], current_data_limits=["Trade receivables are annual only"],
                           current_facts_sha256="1" * 64)
        self.review["material_inputs"][0]["selected"]["derivation"] = {
            "formula": "annual + current_ytd - previous_ytd", "inputs": [
                {"label": "Annual", "value": "12.0001", "scale": "1000000", "unit": "currency"}]}
        self.review["material_inputs"][0]["selected"].update(
            source_first_captured_at="2026-11-01T10:00:00Z", source_last_successful_check_at=None,
            label="Saved report input", page=3, quote="Group revenue", note="Issued share basis explained")
        self.review["material_inputs"][0]["candidates"][0]["record"].update(
            source_first_captured_at="2026-11-01T10:00:00Z", source_last_successful_check_at="2026-11-03T10:00:00Z")
        self.review["material_inputs_sha256"] = hashlib.sha256(json.dumps(
            self.review["material_inputs"], sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.named.update(display_role="current", report_type="r12", period_start="2025-10-01",
                          period_end="2026-09-30", year=2026, period=3, price_date="2026-10-30", current_period_reason="Latest matching R12 flow period")
        self.write(self.review_path, self.review)
        view = self.build()
        self.assertEqual(view["material_inputs"], self.review["material_inputs"])
        self.assertEqual(view["current_data_limits"], self.review["current_data_limits"])
        self.assertEqual(view["calculations"][0], self.named)
        self.assertEqual(view["provenance"]["current_facts_sha256"], "1" * 64)
        self.assertEqual(view["provenance"]["material_inputs_sha256"], self.review["material_inputs_sha256"])
        self.assertEqual(view["material_inputs"][0]["candidates"][0]["definition_status"], "unresolved")
        self.assertEqual(view["material_inputs"][0]["selected"]["value"], "123.000000000000000001")
        output = self.root / "view.json"
        self.write(output, view)
        self.assertEqual(load_saved_view(output), view)
        view["material_inputs"][0]["selection_reason"] = "Changed decision"
        self.write(output, view)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            load_saved_view(output)
        self.review["material_inputs"][0]["selection_reason"] = "Changed decision"
        self.write(self.review_path, self.review)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.build()

    def test_old_exports_and_missing_material_selections_stay_valid(self):
        view = self.build()
        self.assertNotIn("material_inputs", view)

        self.assertNotIn("current_data_limits", view)
        self.assertNotIn("current_facts_sha256", view["provenance"])
        row = material_input()
        row.update(selected=None, definition_status="unresolved", reconciliation_status="unreviewed")
        view["material_inputs"] = [row]
        output = self.root / "view.json"
        self.write(output, view)
        self.assertIsNone(load_saved_view(output)["material_inputs"][0]["selected"])

    def test_legacy_run_rejects_structured_return_selection(self):
        with self.assertRaisesRegex(ValueError, "structured analysis"):
            build_saved_view(self.review_path, self.run, self.packet, "Sample", "SAMP", "sample-20261101", "Saved",
                             return_calculation_id="calc:one")

    def test_rejects_malformed_material_decisions_and_sources(self):
        base = minimal_view()
        base["material_inputs"] = [material_input()]
        mutations = [
            lambda row: row.update(definition_status="verified"),
            lambda row: row.update(definition_status=[]),
            lambda row: row.update(reconciliation_status="verified"),
            lambda row: row.update(selected=[]),
            lambda row: row["selected"].update(unknown_payload={"secret": "not display metadata"}),
            lambda row: row["selected"].update(value=12),
            lambda row: row["selected"].update(scale="0"),
            lambda row: row["selected"].update(period_start="2027-01-01"),
            lambda row: row["selected"].update(pointer=[]),
            lambda row: row["selected"].update(evidence="unstructured evidence"),
            lambda row: row["selected"].update(source_first_captured_at="2026-11-01"),
            lambda row: row["selected"].update(source_last_successful_check_at="invalid"),
            lambda row: row["selected"].update(page=0),
            lambda row: row["selected"].update(page=True),
            lambda row: row["selected"].update(quote={"text": "Unexpected object"}),
            lambda row: row["candidates"][0].update(definition_status="verified"),
            lambda row: row["candidates"][0].update(residual={"value": "0", "unit": "SEK"}),
            lambda row: row.update(valuation_uses="valuation"),
            lambda row: row.update(evidence=["not an evidence object"]),
        ]
        output = self.root / "view.json"
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                view = copy.deepcopy(base)
                mutate(view["material_inputs"][0])
                self.write(output, view)
                with self.assertRaises(ValueError):
                    load_saved_view(output)
        for extra in ({"material_inputs": {}}, {"material_inputs": base["material_inputs"] * 2}, {"current_data_limits": "Not a list"}):
            self.write(output, dict(base, **extra))
            with self.assertRaises(ValueError):
                load_saved_view(output)

    def test_rejects_bad_optional_hashes_and_current_calculation_metadata(self):
        output = self.root / "view.json"
        for key in ("current_facts_sha256", "material_inputs_sha256"):
            view = minimal_view()
            view["provenance"][key] = "invalid"
            self.write(output, view)
            with self.assertRaises(ValueError):
                load_saved_view(output)
        for change in ({"display_role": "fresh"}, {"period_end": "2026-99-99"}, {"period_start": "2026-09-30", "period_end": "2025-09-30"}, {"year": "2026"}, {"current_period_reason": ""}):
            view = minimal_view()
            view["calculations"] = [dict(self.named, **change)]
            self.write(output, view)
            with self.assertRaises(ValueError):
                load_saved_view(output)
    def test_preserves_real_runner_named_calculations_and_qualified_references(self):
        from betaforge.tools import EvidenceTools

        # Exercise the producer with local saved assumptions; no evidence/model run.
        tools = EvidenceTools.__new__(EvidenceTools)
        tools.state = {"inputs": {}, "calculations": {}}
        revenue = tools.record_input("10.250000000000000001", "Saved revenue", "SEK", "assumption", scale="1000000")
        margin = tools.record_input("0.1234567890123456789", "Explicit forecast margin", "fraction", "assumption")
        named = tools.calculate_financial("revenue_ebit", {"revenue": revenue["id"], "ebit_margin": margin["id"]},
                                          "Forecast EBIT", "Saved annual revenue and explicit operating margin")
        cfo = tools.record_input("10", "Saved group CFO", "SEK", "assumption")
        capex = tools.record_input("3", "Saved cash capex", "SEK", "assumption")
        missing = tools.calculate_financial("group_cash_conversion", {"cfo": cfo["id"], "cash_capex": capex["id"]},
                                            "Conditional cash bridge", "Interest and lease principal remain missing")
        # The runner serializes all state records without changing either shape.
        self.originals += list(tools.state["calculations"].values())
        self.write(self.run / "calculations.json", self.originals)
        self.review["preserved_valuation"]["calculations_sha256"] = self.digest(self.run / "calculations.json")
        self.write(self.review_path, self.review)
        self.summary["scenarios"][0]["calculation_ids"] = [named["id"], named["id"] + "#ebit", missing["id"] + "#cash_after_capex"]
        self.write(self.run / "review-summary.json", self.summary)
        view = self.build()
        self.assertEqual(view["original_calculations"], self.originals)
        self.assertEqual(view["original_calculations"][1]["input_ids"], named["input_ids"])
        self.assertEqual(view["original_calculations"][1]["outputs"], named["outputs"])
        self.assertIsNone(view["original_calculations"][2]["result"])
        self.assertEqual(view["original_calculations"][2]["missing_inputs"], missing["missing_inputs"])
        output = self.root / "view.json"
        self.write(output, view)
        self.assertEqual(load_saved_view(output), view)
        for reference in (named["id"] + "#unknown", "calc:unknown#ebit", "calc:one#ebit"):
            with self.subTest(reference=reference):
                self.summary["scenarios"][0]["calculation_ids"] = [reference]
                self.write(self.run / "review-summary.json", self.summary)
                with self.assertRaises(ValueError):
                    self.build()

    def test_explicit_null_benchmark_from_review_producer_stays_missing(self):
        # build_financial_review returns an explicit null when no market context is requested.
        for comparison in (None, {"source": None}, {"source": {"context": None}}):
            with self.subTest(comparison=comparison):
                self.review["market_benchmark_comparison"] = comparison
                self.write(self.review_path, self.review)
                view = self.build()
                self.assertEqual(view["benchmark"], minimal_view()["benchmark"])
                self.assertEqual(view["scenarios"][0]["value"], "168.1400")

    def test_rejects_non_object_benchmark_metadata(self):
        for position in ("comparison", "source", "context"):
            for malformed in (False, [], "invalid", 7):
                with self.subTest(position=position, malformed=malformed):
                    comparison = malformed
                    if position == "source":
                        comparison = {"source": malformed}
                    elif position == "context":
                        comparison = {"source": {"context": malformed}}
                    self.review["market_benchmark_comparison"] = comparison
                    self.write(self.review_path, self.review)
                    with self.assertRaisesRegex(ValueError, "must be an object or null"):
                        self.build()

    def test_rejects_swapped_summary_or_missing_scenario_references(self):
        for references in (["calc:other-run"], [], ["calc:one", "calc:other-run"]):
            with self.subTest(references=references):
                self.summary["scenarios"][0]["calculation_ids"] = references
                self.write(self.run / "review-summary.json", self.summary)
                with self.assertRaises(ValueError):
                    self.build()
        # A named calculation is also an inspectable saved reference.
        self.summary["scenarios"][0]["calculation_ids"] = ["quality:one"]
        self.write(self.run / "review-summary.json", self.summary)
        view = self.build()
        self.assertEqual(view["scenarios"][0]["calculation_ids"], ["quality:one"])
        view["scenarios"][0]["calculation_ids"] = ["quality:not-saved"]
        output = self.root / "view.json"
        self.write(output, view)
        with self.assertRaises(ValueError):
            load_saved_view(output)

    def test_sidecar_hashes_are_required_and_record_changed_bytes(self):
        first = self.build()
        self.summary["notes"].append("New local annotation")
        self.write(self.run / "review-summary.json", self.summary)
        (self.run / "answer.md").write_text("Changed local narrative")
        second = self.build()
        for name in ("summary_sha256", "narrative_sha256"):
            self.assertNotEqual(first["provenance"][name], second["provenance"][name])
            value = second["provenance"].pop(name)
            output = self.root / "view.json"
            self.write(output, second)
            with self.assertRaises(ValueError):
                load_saved_view(output)
            second["provenance"][name] = "invalid"
            self.write(output, second)
            with self.assertRaises(ValueError):
                load_saved_view(output)
            second["provenance"][name] = value

    def test_missing_price_probability_benchmark_remain_missing(self):
        self.packet_data["context"] = {"latest_close": []}
        self.write(self.packet / "packet.json", self.packet_data)
        self.run_data["identity"]["packet_sha256"] = self.digest(self.packet / "packet.json")
        self.write(self.run / "run.json", self.run_data)
        del self.review["probability_proposal"]
        del self.review["market_benchmark_comparison"]
        self.write(self.review_path, self.review)
        view = self.build()
        self.assertIsNone(view["price"])
        self.assertEqual(view["probability"], {"weights": {}, "basis": None, "status": "missing"})
        self.assertNotIn("weight", view["scenarios"][0])
        self.assertIsNone(view["benchmark"]["context"])

    def test_rejects_mixed_identities_dates_and_tampered_originals(self):
        mutations = [
            (self.review_path, dict(self.review, instrument_id=2)),
            (self.review_path, dict(self.review, frozen_analysis_date="2026-10-31")),
            (self.review_path, dict(self.review, database_sha256="f" * 64)),
            (self.run / "inputs.json", [{"value": "2"}]),
            (self.run / "calculations.json", []),
            (self.packet / "packet.json", dict(self.packet_data, instrument_id=2)),
        ]
        for path, mutated in mutations:
            with self.subTest(path=path.name, mutated=mutated):
                old = path.read_bytes()
                self.write(path, mutated)
                with self.assertRaises(ValueError):
                    self.build()
                path.write_bytes(old)
        database = self.packet / "snapshot/evidence.sqlite3"
        database.write_bytes(b"changed snapshot")
        with self.assertRaises(ValueError):
            self.build()

    def test_rejects_incomplete_and_smoke_runs(self):
        for status, smoke in [("running", False), ("smoke_completed", True), ("completed", True)]:
            with self.subTest(status=status, smoke=smoke):
                self.write(self.run / "run.json", dict(self.run_data, status=status, smoke=smoke))
                with self.assertRaises(ValueError):
                    self.build()

    def test_rejects_truncated_or_duplicate_prepared_report_identity(self):
        for reports in ([], [self.prepared, self.prepared]):
            with self.subTest(reports=reports):
                self.write(self.packet / "reports/prepared/index.json", {"reports": reports})
                with self.assertRaises(ValueError):
                    self.build()

    def test_rejects_unsafe_source_urls(self):
        for url in ("javascript:alert(1)", "file:///etc/passwd", "https://u:p@example.org/a", "https://example.org/a?token=secret", "https://example.org/a?api_key=secret", "https://example.org/\nattack"):
            with self.subTest(url=url):
                self.source["source_url"] = url
                self.write(self.packet / "reports/source-manifest.json", self.manifest)
                with self.assertRaises(ValueError):
                    self.build()

    def test_invalid_exports_fail_closed(self):
        output = self.root / "view.json"
        with self.assertRaises(FileNotFoundError):
            load_saved_view(output)
        valid = minimal_view()
        changes = [{"schema_version": 2}, {"id": "../secret"}, {"logs": "secret"}, {"company": "bad"}]
        for change in changes:
            with self.subTest(change=change):
                self.write(output, dict(valid, **change))
                with self.assertRaises(ValueError):
                    load_saved_view(output)
        for body in ('{"schema_version":1,"schema_version":1}', '{"n":NaN}', '[]', 'not JSON'):
            output.write_text(body)
            with self.assertRaises(ValueError):
                load_saved_view(output)
        view = self.build()
        for value in ("NaN", "Infinity", "-Infinity", "1,000", 1.2):
            view["scenarios"][0]["value"] = value
            self.write(output, view)
            with self.assertRaises(ValueError):
                load_saved_view(output)
        output.write_bytes(b" " * (MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            load_saved_view(output)

    def test_rejects_symlink_file_and_parent(self):
        output = self.root / "view.json"
        self.write(output, minimal_view())
        link = self.root / "linked.json"
        link.symlink_to(output)
        with self.assertRaises(ValueError):
            load_saved_view(link)
        folder = self.root / "linked-folder"
        folder.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            load_saved_view(folder / "view.json")

    def test_cli_requires_private_output_and_does_not_overwrite(self):
        from scripts.export_saved_analysis import main
        args = ["--review", str(self.review_path), "--run", str(self.run), "--packet", str(self.packet),
                "--company", "Sample", "--ticker", "SAMP", "--id", "sample-20261101", "--method", "Saved scenarios"]
        with self.assertRaises(SystemExit):
            main(args + ["--output", str(self.root / "public.json")])
        with patch("scripts.export_saved_analysis.__file__", str(self.root / "scripts/export_saved_analysis.py")):
            with self.assertRaises(SystemExit):
                main(args + ["--output", str(self.root / "data/bf-borsdata-research/public.json")])
        # Patch the script location so its ignored data directory is in this fixture.
        private_output = self.root / "data/view.json"
        with patch("scripts.export_saved_analysis.__file__", str(self.root / "scripts/export_saved_analysis.py")):
            self.assertEqual(main(args + ["--output", str(private_output)]), 0)
            original = private_output.read_bytes()
            with self.assertRaises(SystemExit):
                main(args + ["--output", str(private_output)])
            self.assertEqual(private_output.read_bytes(), original)


class StructuredSavedViewTests(unittest.TestCase):
    """Use the actual frozen SQLite/report tools, without model or provider calls."""

    def setUp(self):
        import test_tools
        from test_analysis_report import AnalysisReportTests
        from betaforge.tools import EvidenceTools, write_json
        test_tools.ToolsTests.setUp(self)
        self.tools.store.close()
        self.root = self.root.resolve()
        self.packet = self.packet.resolve()
        packet = json.loads(self.packet.read_text())
        from betaforge.storage import EvidenceStore
        capture = self.root / "price-capture"
        capture.mkdir()
        requests = []
        for name, endpoint, payload in (
                ("instruments", "/v1/instruments", {"instruments": [{"insId": 426, "stockPriceCurrency": "SEK"}]}),
                ("prices", "/v1/instruments/426/stockprices", {"instrument": 426, "stockPricesList": [{"d": "2026-11-03", "c": 100}]})):
            body = json.dumps(payload).encode()
            (capture / (name + ".json")).write_bytes(body)
            requests.append({"endpoint": endpoint, "parameters": {}, "http_status": 200,
                             "file": name + ".json", "sha256": hashlib.sha256(body).hexdigest()})
        write_json(capture / "manifest.json", {"retrieved_at": "2026-11-04T00:00:00Z", "requests": requests})
        with EvidenceStore(self.root / "live/evidence.sqlite3") as store:
            store.ingest_snapshot(capture)
            store.freeze(self.root / "price-snapshot")
            packet["context"] = {"latest_close": store.query_financials(426, "price", ["price_close"], limit=1)}
        packet["snapshot_dir"] = "price-snapshot"
        packet["analysis_date"] = "2026-11-04"
        self.benchmark_context = {
            "benchmark": {"symbol": "SIXRX", "currency": "SEK", "return_type": "gross_total_return"},
            "analysis_date": "2026-11-04", "status": "verified_from_rounded_public_levels",
            "calculation": {"annualized_return_percent": "7.250000000000000001"},
            "caveats": ["Rounded historical levels; not a forecast"], "rounded_source": True,
        }
        market = self.root / "market.json"
        write_json(market, self.benchmark_context)
        packet["market_benchmark_context"] = {"context_path": "market.json", "files": [
            {"path": "market.json", "sha256": SavedViewTests.digest(market)}]}
        write_json(self.packet, packet)
        prepared = json.loads((self.root / "reports/prepared/index.json").read_text())["reports"][0]
        write_json(self.root / "reports/source-manifest.json", {
            "borsdata_instrument_id": 426, "documents": [{"report_id": "example", "sha256": prepared["source_sha256"],
            "title": "Example annual", "publication_date": "2026-01-01", "source_url": "https://example.org/report.pdf",
            "reporting_period": {"start": "2025-01-01", "end": "2025-12-31"}}]})
        self.run = self.root / "structured-run"
        self.tools = EvidenceTools(self.packet, self.run, structured=True)
        self.tools.submit_analysis(AnalysisReportTests.report(self))
        self.tools.save()
        self.addCleanup(self.tools.store.close)
        self.addCleanup(self.temp.cleanup)
        for name in ("inputs", "calculations"):
            write_json(self.run / (name + ".json"), list(self.tools.state[name].values()))
        self.run_data = {"status": "completed", "smoke": False, "structured": True, "identity": self.tools.identity,
                         "model": "gpt-6.1-sol", "reasoning_effort": "xhigh", "coverage": self.tools.coverage(),
                         "started_at": "2026-11-04T12:00:00Z", "finished_at": "2026-11-04T12:01:00Z",
                         **{name + "_sha256": SavedViewTests.digest(self.run / (name + ".json")) for name in ("inputs", "calculations", "analysis")}}
        write_json(self.run / "run.json", self.run_data)

    def build(self, **kwargs):
        return build_saved_view(None, self.run, self.root, "Sample", "SAMP", "sample-20261104", "Saved structured analysis", **kwargs)

    def persist_run(self):
        from betaforge.tools import write_json

        self.tools.save()
        for name in ("inputs", "calculations"):
            write_json(self.run / (name + ".json"), list(self.tools.state[name].values()))
            self.run_data[name + "_sha256"] = SavedViewTests.digest(self.run / (name + ".json"))
        self.run_data["analysis_sha256"] = SavedViewTests.digest(self.run / "analysis.json")
        write_json(self.run / "run.json", self.run_data)

    def save_return_calculations(self, count=2):
        from betaforge.analysis_report import render_markdown, validate_report
        from betaforge.tools import write_json
        from test_analysis_report import AnalysisReportTests

        legacy = validate_report(AnalysisReportTests.report(self, version=1), self.tools, saved=True)
        write_json(self.run / "analysis.json", legacy)
        (self.run / "answer.md").write_text(render_markdown(legacy))
        self.tools.state["analysis_sha256"] = SavedViewTests.digest(self.run / "analysis.json")
        price = self.tools.get_financials(report_type="price", fields=["price_close"])["observations"][0]
        inputs = {"price": price["id"], **{field: self.tools.record_input(value, field, unit, "assumption")["id"]
                  for field, value, unit in (("expected_annual_dividend_per_share", "2", "SEK/shares"),
                                             ("years", "3", "dimensionless"))}}
        calculations = []
        for target in ("120", "130")[:count]:
            inputs["expected_future_target"] = self.tools.record_input(target, "Terminal target", "SEK/shares", "assumption")["id"]
            calculations.append(self.tools.calculate_financial("expected_cashflow_irr", inputs, "Saved return", "Report-price cash flows"))
        self.persist_run()
        return calculations

    def record_case_returns(self, report):
        price = self.tools.get_financials(report_type="price", fields=["price_close"])["observations"][0]
        weighted_inputs = {}
        for scenario in report["scenarios"]:
            case = scenario["id"]
            valuation = self.tools.state["calculations"][scenario["valuation_calculation_id"]]
            target = valuation["id"] + "#future_target"
            dividend = valuation["input_ids"]["annual_dividend_per_share"]
            years = valuation["input_ids"]["years"]
            weighted_inputs.update({
                "years": years, f"{case}_weight": scenario["weight_ref"],
                f"{case}_present_value": valuation["id"],
                f"{case}_future_target": target, f"{case}_annual_dividend_per_share": dividend,
            })
        individual = self.tools.calculate_financial("expected_cashflow_irr", {
            "price": price["id"], "expected_future_target": target,
            "expected_annual_dividend_per_share": dividend, "years": years,
        }, "Individual return", "Report-price cash flows")
        weighted = self.tools.calculate_financial("scenario_weighted_values", weighted_inputs,
                                                  "Weighted values", "Same date, scope and horizon")
        aggregate = self.tools.calculate_financial("expected_cashflow_irr", {
            "price": price["id"], "expected_future_target": weighted["id"] + "#expected_future_target",
            "expected_annual_dividend_per_share": weighted["id"] + "#expected_annual_dividend_per_share", "years": years,
        }, "Weighted return", "Report-price cash flows")
        return individual, aggregate

    def test_supported_return_selects_weighted_cash_flows_and_retains_probability_sources(self):
        from test_analysis_report import AnalysisReportTests

        report = AnalysisReportTests.report(self)
        observation = self.tools.get_financials(report_type="price", fields=["price_close"])["observations"][0]
        report["scenarios"][0]["probability_references"] = [observation["id"]]
        individual, aggregate = self.record_case_returns(report)
        self.tools.submit_analysis(report)
        self.persist_run()
        view = self.build()
        self.assertEqual(view["benchmark"]["return_calculation_id"], aggregate["id"])
        self.assertEqual(view["benchmark"]["candidate_annualized_return_percent"], aggregate["outputs"]["irr_percent"]["value"])
        self.assertIn(observation["id"], {record["id"] for record in view["saved_records"]})
        with self.assertRaisesRegex(ValueError, "ineligible"):
            self.build(return_calculation_id=individual["id"])
        view["benchmark"]["return_calculation_id"] = individual["id"]
        with self.assertRaisesRegex(ValueError, "eligible"):
            validate_saved_view(view)

    def test_unweighted_export_and_reader_memo_preserve_individual_returns_in_trace(self):
        from test_analysis_report import AnalysisReportTests

        individual, aggregate = self.record_case_returns(AnalysisReportTests.report(self))
        report = AnalysisReportTests.report(self, weighted=False)
        self.tools.submit_analysis(report)
        self.persist_run()
        view = self.build()
        self.assertEqual(view["probability"], {"weights": {}, "basis": report["probability_limits"], "status": "missing"})
        self.assertTrue(all("weight" not in scenario for scenario in view["scenarios"]))
        self.assertIsNone(view["benchmark"]["candidate_annualized_return_percent"])
        self.assertNotIn("return_calculation_id", view["benchmark"])
        self.assertIn(individual, view["original_calculations"])
        self.assertIn(aggregate, view["original_calculations"])
        for calc in (individual, aggregate):
            with self.assertRaisesRegex(ValueError, "ineligible"):
                self.build(return_calculation_id=calc["id"])
        memo = self.reader_memo(view)
        for scenario in memo["scenarios"]:
            del scenario["probability_rationale"]
        self.assertEqual(attach_reader_memo(view, memo)["reader_memo"], memo)
        memo["scenarios"][0]["probability_rationale"] = "A proposed weight."
        with self.assertRaises(ValueError):
            attach_reader_memo(view, memo)

    def test_named_calculation_input_ids_must_match_retained_inputs(self):
        from test_analysis_report import AnalysisReportTests

        _, aggregate = self.record_case_returns(AnalysisReportTests.report(self))
        calculations = self.tools.state["calculations"]
        del calculations[aggregate.pop("id")]
        aggregate["input_ids"]["expected_future_target"] = aggregate["input_ids"]["expected_annual_dividend_per_share"]
        aggregate["id"] = "calc:" + hashlib.sha256(json.dumps(aggregate, sort_keys=True).encode()).hexdigest()[:20]
        calculations[aggregate["id"]] = aggregate
        self.persist_run()
        with self.assertRaisesRegex(ValueError, "input IDs differ"):
            self.build()

    def test_explicit_return_selection_copies_saved_output_and_keeps_history(self):
        calculations = self.save_return_calculations()
        original = self.build()
        self.assertIsNone(original["benchmark"]["candidate_annualized_return_percent"])
        selected = calculations[1]
        view = self.build(return_calculation_id=selected["id"])
        self.assertEqual(view["benchmark"]["return_calculation_id"], selected["id"])
        self.assertEqual(view["benchmark"]["candidate_annualized_return_percent"], selected["outputs"]["irr_percent"]["value"])
        original["benchmark"] = view["benchmark"]
        self.assertEqual(original, view)
        self.assertEqual(validate_saved_view(view), view)
        output = self.root / "view.json"
        SavedViewTests.write(output, view)
        self.assertEqual(load_saved_view(output), view)
        from scripts.export_saved_analysis import main
        cli_output = self.root / "data/selected.json"
        with patch("scripts.export_saved_analysis.__file__", str(self.root / "scripts/export_saved_analysis.py")):
            self.assertEqual(main(["--run", str(self.run), "--packet", str(self.root), "--company", "Sample",
                                   "--ticker", "SAMP", "--id", "sample-20261104", "--method", "Saved structured analysis",
                                   "--return-calculation-id", selected["id"], "--output", str(cli_output)]), 0)
        self.assertEqual(load_saved_view(cli_output), view)

    def test_return_selection_rejects_unknown_stale_wrong_formula_and_price_tampering(self):
        calculations = self.save_return_calculations()
        for identifier in ("calc:missing", next(iter(self.tools.state["calculations"])), "", None, []):
            view = self.build()
            view["benchmark"].update(return_calculation_id=identifier,
                                     candidate_annualized_return_percent=calculations[1]["outputs"]["irr_percent"]["value"])
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                validate_saved_view(view)
        original = self.build(return_calculation_id=calculations[1]["id"])
        mutations = [lambda view: view["benchmark"].update(return_calculation_id=calculations[0]["id"]),
                     lambda view: view["benchmark"].update(candidate_annualized_return_percent="99"),
                     lambda view: view.update(price=None)]
        mutations.extend(lambda view, key=key, value=value: view["price"].update({key: value})
                         for key, value in (("id", "obs:other"), ("value", "101"), ("unit", "currency"),
                                            ("scale", "10"), ("currency", "USD"), ("source_id", "src:other"),
                                            ("date", "2026-11-02")))
        for index, mutate in enumerate(mutations):
            view = copy.deepcopy(original)
            mutate(view)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                validate_saved_view(view)
        with self.assertRaises(ValueError):
            self.build(return_calculation_id="calc:missing")

    def test_unique_return_exports_keep_the_existing_implicit_selection(self):
        selected = self.save_return_calculations(count=1)[0]
        view = self.build()
        self.assertNotIn("return_calculation_id", view["benchmark"])
        self.assertEqual(view["benchmark"]["candidate_annualized_return_percent"], selected["outputs"]["irr_percent"]["value"])

    @staticmethod
    def reader_memo(view):
        return {
            "schema_version": 1, "analysis_sha256": view["provenance"]["analysis_sha256"],
            "edited_at": "2026-11-04T16:00:00+00:00", "summary": "A shorter investment case.",
            "sections": [{"id": section["id"], "title": section["title"], "paragraphs": [
                {"kind": "interpretation", "text": "Read the saved evidence before deciding.", "references": ["example:p1"]}]
                } for section in view["analysis"]["sections"]],
            "scenarios": [{"id": scenario["id"], "rationale": "A conditional outcome.",
                           "assumption_rationale": "The saved inputs explain the operating assumptions.",
                           "probability_rationale": "The weights remain conditional judgments.",
                           "references": scenario["references"]}
                          for scenario in view["analysis"]["scenarios"]],
        }

    def test_reader_memo_preserves_every_original_field_and_does_not_alias_inputs(self):
        original = self.build()
        memo = self.reader_memo(original)
        original_bytes = json.dumps(original, ensure_ascii=False).encode()
        memo_before = copy.deepcopy(memo)
        attached = attach_reader_memo(original, memo)
        attached_memo = attached.pop("reader_memo")
        self.assertEqual(attached_memo, memo_before)
        self.assertEqual(attached, original)
        self.assertEqual(json.dumps(original, ensure_ascii=False).encode(), original_bytes)
        attached["analysis"]["summary"] = "Local copy changed"
        memo["sections"][0]["paragraphs"][0]["text"] = "Caller changed"
        self.assertEqual(json.dumps(original, ensure_ascii=False).encode(), original_bytes)
        self.assertEqual(attached_memo, memo_before)

    def test_reader_memo_rejects_stale_invalid_or_unavailable_content(self):
        original = self.build()
        mutations = [
            lambda m: m.update(analysis_sha256="f" * 64),
            lambda m: m.update(schema_version=True),
            lambda m: m.update(edited_at="2026-11-04T16:00:00"),
            lambda m: m.update(summary="x" * 1001),
            lambda m: m.update(sources=[]),
            lambda m: m.update(sections=m["sections"][:-1]),
            lambda m: m["sections"][0].update(id=m["sections"][1]["id"]),
            lambda m: m["sections"][0].update(title=1),
            lambda m: m["sections"][0].update(paragraphs=[]),
            lambda m: m["sections"][0].update(paragraphs=m["sections"][0]["paragraphs"] * 7),
            lambda m: m["sections"][0]["paragraphs"][0].update(kind=[]),
            lambda m: m["sections"][0]["paragraphs"][0].update(text="x" * 1501),
            lambda m: m["sections"][0]["paragraphs"][0].update(value="5"),
            lambda m: m["sections"][0]["paragraphs"][0].update(references=[]),
            lambda m: m["sections"][0]["paragraphs"][0].update(references=["missing:p1"]),
            lambda m: m["sections"][0]["paragraphs"][0].update(references=["example:p0"]),
            lambda m: m["sections"][0]["paragraphs"][0].update(references=["example:p3"]),
            lambda m: m["scenarios"][0].update(references=["input:missing"]),
            lambda m: m["scenarios"][0].update(references=["example:p1"] * 101),
            lambda m: m["scenarios"][0].update(probability_rationale="x" * 1201),
            lambda m: m["scenarios"][0].update(weight="0.5"),
            lambda m: m["scenarios"][0].update(id=m["scenarios"][1]["id"]),
            lambda m: m.update(scenarios=m["scenarios"][:-1]),
        ]
        for index, mutate in enumerate(mutations):
            memo = self.reader_memo(original)
            mutate(memo)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                attach_reader_memo(original, memo)
        oversized = self.reader_memo(original)
        for section in oversized["sections"]:
            section["paragraphs"] *= 6
            for paragraph in section["paragraphs"]:
                paragraph["text"] = "å" * 1500
        with self.assertRaisesRegex(ValueError, "64 KiB"):
            attach_reader_memo(original, oversized)
        with self.assertRaisesRegex(ValueError, "canonical analysis"):
            attach_reader_memo(minimal_view(), self.reader_memo(original))

    def test_reader_memo_cli_preserves_original_and_restricts_new_output(self):
        from scripts.attach_reader_memo import main
        original = self.build()
        original_path, memo_path = self.root / "view.json", self.root / "memo.json"
        SavedViewTests.write(original_path, original)
        SavedViewTests.write(memo_path, self.reader_memo(original))
        original_bytes = original_path.read_bytes()
        args = ["--view", str(original_path), "--memo", str(memo_path)]
        output = self.root / "data/reader-view.json"
        with patch("scripts.attach_reader_memo.__file__", str(self.root / "scripts/attach_reader_memo.py")):
            for invalid in (self.root / "public.json", self.root / "data/bf-borsdata-research/view.json",
                            self.root / "data/../view.json"):
                with self.subTest(output=invalid), self.assertRaises(SystemExit):
                    main(args + ["--output", str(invalid)])
            self.assertEqual(main(args + ["--output", str(output)]), 0)
            attached = load_saved_view(output)
            self.assertEqual(attached.pop("reader_memo"), self.reader_memo(original))
            self.assertEqual(attached, original)
            output_bytes = output.read_bytes()
            with self.assertRaises(SystemExit):
                main(args + ["--output", str(output)])
            self.assertEqual(output.read_bytes(), output_bytes)
            link = self.root / "data/link"
            link.symlink_to(self.root, target_is_directory=True)
            with self.assertRaises(SystemExit):
                main(args + ["--output", str(link / "unsafe.json")])
            memo_link = self.root / "memo-link.json"
            memo_link.symlink_to(memo_path)
            with self.assertRaises(SystemExit):
                main(["--view", str(original_path), "--memo", str(memo_link), "--output", str(self.root / "data/new.json")])
            memo_path.write_text('{"schema_version": 1, "schema_version": 1}')
            with self.assertRaises(SystemExit):
                main(args + ["--output", str(self.root / "data/new.json")])
        self.assertEqual(original_path.read_bytes(), original_bytes)

    def test_exports_actual_completed_run_without_legacy_review_or_summary(self):
        view = self.build()
        self.assertFalse((self.run / "review-summary.json").exists())
        self.assertEqual(view["analysis"], json.loads((self.run / "analysis.json").read_text()))
        self.assertEqual(view["original_calculations"], list(self.tools.state["calculations"].values()))
        self.assertIsNone(view["provenance"]["review_sha256"])
        self.assertNotIn("analysis_review", view)
        self.assertEqual(view["scenarios"][0]["target_date"], {"value": "2029", "precision": "year"})
        self.assertEqual(view["probability"]["weights"], {"bear": "0.2", "base": "0.5", "bull": "0.3"})
        self.assertEqual(view["calculations"][0]["basis"], "Test basis")
        self.assertIn("forecast_ebit", view["calculations"][0]["inputs"])
        output = self.root / "view.json"
        SavedViewTests.write(output, view)
        self.assertEqual(load_saved_view(output), view)

    def test_cli_omits_review_for_structured_run(self):
        from scripts.export_saved_analysis import main
        output = self.root / "data/view.json"
        with patch("scripts.export_saved_analysis.__file__", str(self.root / "scripts/export_saved_analysis.py")):
            self.assertEqual(main(["--run", str(self.run), "--packet", str(self.root), "--company", "Sample",
                                   "--ticker", "SAMP", "--id", "sample-20261104", "--method", "Structured", "--output", str(output)]), 0)
        self.assertIn("analysis", load_saved_view(output))

    def test_copies_matching_historical_benchmark_without_return_gap_math(self):
        view = self.build()
        self.assertEqual(view["benchmark"]["benchmark_annualized_return_percent"], "7.250000000000000001")
        self.assertEqual(view["benchmark"]["context"], self.benchmark_context)
        self.assertIsNone(view["benchmark"]["difference_percentage_points"])
        self.assertTrue(view["benchmark"]["limits"])
        output = self.root / "view.json"
        SavedViewTests.write(output, view)
        self.assertEqual(load_saved_view(output), view)
        view["benchmark"]["benchmark_annualized_return_percent"] = "99"
        with self.assertRaisesRegex(ValueError, "Benchmark must preserve"):
            validate_saved_view(view)

    def test_unmatched_or_missing_benchmark_has_no_selected_return(self):
        original = self.build()
        mutations = [
            lambda c: c.update(analysis_date="2026-11-03"),
            lambda c: c["benchmark"].update(symbol="OTHER"),
            lambda c: c["benchmark"].update(currency="USD"),
            lambda c: c["benchmark"].update(return_type="price_return"),
            lambda c: c.update(status="unreviewed"),
            lambda c: c.pop("calculation"),
            lambda c: c["calculation"].pop("annualized_return_percent"),
            lambda c: c.update(benchmark=None),
            lambda c: c.update(calculation=[]),
        ]
        for index, mutate in enumerate(mutations):
            view = copy.deepcopy(original)
            mutate(view["benchmark"]["context"])
            with self.subTest(mutation=index):
                with self.assertRaisesRegex(ValueError, "Benchmark must preserve"):
                    validate_saved_view(view)
                view["benchmark"]["benchmark_annualized_return_percent"] = None
                self.assertEqual(validate_saved_view(view), view)
        view = copy.deepcopy(original)
        view["benchmark"].update(context=None, benchmark_annualized_return_percent=None)
        self.assertEqual(validate_saved_view(view), view)

    def test_load_preserves_unselected_benchmark_from_earlier_structured_export(self):
        view = self.build()
        view["benchmark"]["benchmark_annualized_return_percent"] = None
        output = self.root / "earlier-structured-view.json"
        SavedViewTests.write(output, view)
        loaded = load_saved_view(output)
        self.assertEqual(loaded, view)
        self.assertEqual(loaded["benchmark"]["context"], self.benchmark_context)
        self.assertIsNone(loaded["benchmark"]["benchmark_annualized_return_percent"])
        view["benchmark"]["benchmark_annualized_return_percent"] = "99"
        SavedViewTests.write(output, view)
        with self.assertRaisesRegex(ValueError, "Benchmark must preserve"):
            load_saved_view(output)

    def test_historical_return_selector_requires_a_finite_decimal_string(self):
        from betaforge.saved_view import _historical_benchmark_return
        for value in (None, "NaN", "Infinity", "-Infinity", "1,000", 7.25):
            context = copy.deepcopy(self.benchmark_context)
            context["calculation"]["annualized_return_percent"] = value
            with self.subTest(value=value):
                self.assertIsNone(_historical_benchmark_return(context, "2026-11-04"))
        self.assertIsNone(_historical_benchmark_return([], "2026-11-04"))

    def test_freeform_scenario_name_uses_stable_probability_id(self):
        from betaforge.tools import write_json
        report = json.loads((self.run / "analysis.json").read_text())
        for key in ("identity", "validation_status", "review_status"):
            report.pop(key)
        for scenario in report["scenarios"]:
            scenario.pop("present_value")
            scenario.pop("future_target")
        report["scenarios"][0]["name"] = "Bear — weaker demand"
        self.tools.submit_analysis(report)
        self.tools.save()
        self.run_data["analysis_sha256"] = SavedViewTests.digest(self.run / "analysis.json")
        write_json(self.run / "run.json", self.run_data)
        view = self.build()
        self.assertEqual(view["scenarios"][0]["name"], "Bear — weaker demand")
        self.assertEqual(view["scenarios"][0]["weight"], view["probability"]["weights"]["bear"])

    def test_saved_independent_review_is_bound_and_retained(self):
        from betaforge.tools import write_json
        review = {"schema_version": 1, "packet_sha256": self.tools.identity["packet_sha256"],
                  "analysis_sha256": self.run_data["analysis_sha256"], "reviewer": "Independent reviewer",
                  "verdict": "accept", "summary": "Conditional assumptions remain uncertain.", "findings": [], "disagreements": []}
        path = self.run / "analysis-review.json"
        write_json(path, review)
        view = self.build()
        self.assertEqual(view["analysis_review"], review)
        self.assertEqual(view["provenance"]["review_sha256"], SavedViewTests.digest(path))
        canonical_hash = view["provenance"]["review_sha256"]
        path.write_text(json.dumps(review, indent=4) + "\n")
        reformatted = self.build()
        self.assertEqual(reformatted["analysis_review"], review)
        self.assertEqual(reformatted["provenance"]["review_sha256"], canonical_hash)
        review["analysis_sha256"] = "a" * 64
        write_json(path, review)
        with self.assertRaisesRegex(ValueError, "hash"):
            self.build()

    def test_review_only_observation_and_output_are_inspectable(self):
        from betaforge.tools import write_json
        observation = self.tools.store.query_financials(426, fields=["revenues"], limit=1)[0]
        calculation = next(iter(self.tools.state["calculations"]))
        output = calculation + "#future_target"
        prose_reference = "data/sample/answer.md § Management"
        self.assertNotIn(observation["id"], json.dumps(self.tools.state))
        self.assertNotIn(observation["id"], (self.run / "analysis.json").read_text())
        self.assertNotIn(output, {record["id"] for record in self.build()["saved_records"]})
        review = {"schema_version": 1, "packet_sha256": self.tools.identity["packet_sha256"],
                  "analysis_sha256": self.run_data["analysis_sha256"], "reviewer": "Independent reviewer",
                  "verdict": "accept", "summary": "Inspect the frozen revenue and target.", "disagreements": [],
                  "findings": [{"id": "revenue", "verdict": "bounded concern", "reasoning": "Compare source and target.",
                                "references": [observation["id"], output, "example:p2", prose_reference], "missing_evidence": ""}]}
        write_json(self.run / "analysis-review.json", review)
        view = self.build()
        records = {record["id"]: record for record in view["saved_records"]}
        self.assertEqual(records[observation["id"]]["value"], observation["value"])
        self.assertEqual(records[observation["id"]]["source_id"], observation["source_id"])
        self.assertEqual(records[observation["id"]]["instrument_id"], 426)
        self.assertEqual(records[output]["value"], self.tools.state["calculations"][calculation]["outputs"]["future_target"]["value"])
        self.assertEqual(view["analysis_review"], review)
        self.assertNotIn(prose_reference, records)
        path = self.root / "view.json"
        write_json(path, view)
        self.assertEqual(load_saved_view(path), view)

    def test_review_saved_references_use_existing_resolution_boundaries(self):
        from betaforge.tools import write_json
        observation = self.tools.store.query_financials(426, fields=["revenues"], limit=1)[0]
        calculation = next(iter(self.tools.state["calculations"]))
        review = {"schema_version": 1, "packet_sha256": self.tools.identity["packet_sha256"],
                  "analysis_sha256": self.run_data["analysis_sha256"], "reviewer": "Independent reviewer",
                  "verdict": "accept", "summary": "Inspect the frozen source.", "disagreements": [],
                  "findings": [{"id": "source", "verdict": "bounded concern", "reasoning": "Check the reference.",
                                "references": [], "missing_evidence": ""}]}
        path = self.run / "analysis-review.json"
        for reference in ("obs_missing", "input:missing", "calc:missing", calculation + "#missing", "example:p0", "example:p3", "missing:p1"):
            with self.subTest(reference=reference):
                review["findings"][0]["references"] = [reference]
                write_json(path, review)
                with self.assertRaises(ValueError):
                    self.build()
        review["findings"][0]["references"] = [observation["id"]]
        write_json(path, review)
        with patch("betaforge.storage.EvidenceStore.get_observation", return_value=dict(observation, instrument_id=427)):
            with self.assertRaisesRegex(ValueError, "outside selected instrument"):
                self.build()

    def test_run_artifact_and_tool_state_identity_tampering_are_rejected(self):
        from betaforge.tools import write_json
        mutations = [
            ("inputs.json", lambda value: value[0].update(value="999")),
            ("calculations.json", lambda value: value[0]["outputs"]["present_value"].update(value="999")),
            ("tool-state.json", lambda value: value["identity"].update(packet_sha256="a" * 64)),
            ("analysis.json", lambda value: value.update(summary="Changed report")),
            ("run.json", lambda value: value.update(smoke=True)),
        ]
        for name, mutate in mutations:
            path = self.run / name
            original = path.read_bytes()
            value = json.loads(original)
            mutate(value)
            write_json(path, value)
            with self.subTest(artifact=name), self.assertRaises(ValueError):
                self.build()
            path.write_bytes(original)

    def test_frozen_source_and_quote_verification_is_real(self):
        source = self.root / "reports/sources/example.pdf"
        source.write_bytes(b"changed PDF")
        with self.assertRaisesRegex(ValueError, "hash"):
            self.build()

    def test_export_checks_original_quote_even_with_rebound_artifact_hashes(self):
        from betaforge.tools import write_json
        path = self.run / "analysis.json"
        report = json.loads(path.read_text())
        report["management_comparisons"][0]["evidence"]["quote"] = "A promise absent from the original report."
        write_json(path, report)
        changed_hash = SavedViewTests.digest(path)
        self.run_data["analysis_sha256"] = changed_hash
        write_json(self.run / "run.json", self.run_data)
        state = json.loads((self.run / "tool-state.json").read_text())
        state["analysis_sha256"] = changed_hash
        write_json(self.run / "tool-state.json", state)
        with self.assertRaisesRegex(ValueError, "quote"):
            self.build()

    def test_stale_narrative_is_rejected_at_export_and_display_load(self):
        view = self.build()
        (self.run / "answer.md").write_text("An older full report with different conclusions.")
        with self.assertRaisesRegex(ValueError, "narrative differs"):
            self.build()
        view["narrative"] = "A substituted report."
        view["provenance"]["narrative_sha256"] = hashlib.sha256(view["narrative"].encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "narrative differs"):
            validate_saved_view(view)

    def test_bare_diagnostic_reference_preserves_unavailable_primary_output(self):
        from betaforge.tools import write_json
        cfo = self.tools.record_input("10", "Group CFO", "SEK", "assumption")
        capex = self.tools.record_input("3", "Cash capex", "SEK", "assumption")
        diagnostic = self.tools.calculate_financial("group_cash_conversion", {"cfo": cfo["id"], "cash_capex": capex["id"]},
                                                    "Incomplete cash conversion", "Lease principal remains unknown")
        self.assertIsNone(diagnostic["result"])
        report = json.loads((self.run / "analysis.json").read_text())
        for key in ("identity", "validation_status", "review_status"):
            report.pop(key)
        for scenario in report["scenarios"]:
            scenario.pop("present_value")
            scenario.pop("future_target")
        report["sections"][0]["paragraphs"][0]["references"].append(diagnostic["id"])
        self.tools.submit_analysis(report)
        self.tools.save()
        for name in ("inputs", "calculations"):
            write_json(self.run / (name + ".json"), list(self.tools.state[name].values()))
        self.run_data.update({name + "_sha256": SavedViewTests.digest(self.run / (name + ".json")) for name in ("inputs", "calculations", "analysis")})
        write_json(self.run / "run.json", self.run_data)
        view = self.build()
        saved = next(record for record in view["saved_records"] if record["id"] == diagnostic["id"])
        self.assertIsNone(saved["value"])
        self.assertIn(diagnostic["id"], {calc["id"] for calc in view["calculations"]})

    def test_load_rejects_canonical_and_display_tampering(self):
        from betaforge.saved_view import _saved_json_hash
        original = self.build()
        mutations = [
            lambda v: v["analysis"].update(extra="unknown"),
            lambda v: v["analysis"]["scenarios"][0]["target_date"].update(value="2028"),
            lambda v: v["analysis"]["scenarios"][0]["present_value"].update(value="999"),
            lambda v: v["scenarios"][0].update(value="999"),
            lambda v: v["analysis"]["sections"][0]["paragraphs"][0].update(references=["missing:p1"]),
            lambda v: v["analysis"]["management_comparisons"][0].update(statement_date="2026-02-01"),
            lambda v: v["sources"][0].update(published_at=None),
            lambda v: v["saved_records"][0].update(scale="0"),
            lambda v: v["calculations"][0].update(basis="Altered basis"),
            lambda v: v["benchmark"].update(candidate_annualized_return_percent="99"),
            lambda v: v["analysis"]["identity"].update(packet_sha256="a" * 64),
            lambda v: v.update(narrative="Altered narrative"),
        ]
        for index, mutate in enumerate(mutations):
            changed = copy.deepcopy(original)
            mutate(changed)
            # Exercise retained consistency checks even when an attacker updates the embedded hash.
            changed["provenance"]["analysis_sha256"] = _saved_json_hash(changed["analysis"])
            changed["provenance"]["summary_sha256"] = changed["provenance"]["analysis_sha256"]
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                validate_saved_view(changed)


if __name__ == "__main__":
    unittest.main()
