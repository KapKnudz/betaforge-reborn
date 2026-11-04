import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from betaforge.saved_view import MAX_BYTES, build_saved_view, load_saved_view


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


if __name__ == "__main__":
    unittest.main()
