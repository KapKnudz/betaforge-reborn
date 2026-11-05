from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_development_corpus as corpus
from serve_progress import load_corpus_catalogue
from betaforge.storage import EvidenceStore


class DevelopmentCorpusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def capture(self, instrument):
        directory = self.root / str(instrument)
        directory.mkdir()
        annual = {"year": 2025, "period": 5, "report_Start_Date": "2025-01-01T00:00:00",
                  "report_End_Date": "2025-12-31T00:00:00", "report_Date": "2026-01-30T00:00:00",
                  "currency": "SEK", "currency_Ratio": 1, "revenues": 10.25, "net_Debt": 5}
        records = []
        for name, endpoint, parameters in corpus.request_plan(instrument):
            parts = endpoint.strip("/").split("/")
            payload = {}
            if name == "instruments":
                payload = {"instruments": [{"insId": i, "name": "Synthetic issuer", "stockPriceCurrency": "SEK"} for i in (777, 888)]}
            elif name == "reports":
                payload = {"instrument": instrument, "reportsYear": [annual],
                           "reportsQuarter": [dict(annual, period=4, report_Start_Date="2025-10-01T00:00:00")],
                           "reportsR12": [annual]}
            elif name == "prices":
                payload = {"instrument": instrument, "stockPricesList": [{"d": "2026-11-02", "c": 12.5, "v": 100}]}
            elif endpoint.endswith("/summary"):
                payload = {"instrument": instrument, "reportType": parts[-2],
                           "kpis": [{"kpiId": 29, "values": [{"y": 2025, "p": 5, "v": 10}]}]}
            elif endpoint.endswith("/history"):
                payload = {"kpiId": int(parts[4]), "reportTime": parts[5], "priceValue": parts[6],
                           "values": [{"y": 2025, "p": 5, "v": 10}]}
            elif parts[-2:] == ["last", "latest"]:
                payload = {"kpiId": int(parts[4]), "group": "last", "calculation": "latest",
                           "value": {"i": instrument, "n": 10, "s": None}}
            elif name in ("description", "insider", "shorts", "buyback", "report-calendar", "dividend-calendar"):
                payload = {"list": [{"insId": instrument, "values": []}]}
            elif name == "splits":
                payload = {"stockSplitList": []}
            elif name in corpus.ARRAY_FIELDS:
                entry = {"reportPropery": "revenues", "nameEn": "Revenue"} if name == "report-metadata" else (
                    {"kpiId": 29, "format": "%", "isString": False} if name == "kpi-metadata" else (
                    {"translationKey": "L_SECTOR_1", "nameEn": "Synthetic sector"} if name == "translations" else
                    {"id": 1, "name": "Synthetic lookup"}))
                payload = {corpus.ARRAY_FIELDS[name]: [entry]}
            body = json.dumps(payload).encode()
            (directory / (name + ".json")).write_bytes(body)
            records.append({"dataset": name, "endpoint": endpoint, "parameters": parameters,
                            "status": "saved", "http_status": 200, "file": name + ".json",
                            "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        manifest = {"instrument_id": instrument, "retrieved_at_utc": "2026-11-03T00:00:00Z", "requests": records}
        (directory / "manifest.json").write_text(json.dumps(manifest))
        return directory

    def replace_payload(self, directory, dataset, payload):
        path = directory / "manifest.json"
        manifest = json.loads(path.read_text())
        record = next(row for row in manifest["requests"] if row["dataset"] == dataset)
        body = json.dumps(payload).encode()
        (directory / record["file"]).write_bytes(body)
        record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        path.write_text(json.dumps(manifest))

    def test_builds_portable_multiissuer_snapshot_and_keeps_coverage_limits(self):
        captures = [self.capture(i) for i in (777, 888)]
        destination = self.root / "published"
        result = corpus.build_corpus(captures, destination)
        manifest = json.loads(result.read_text())
        self.assertEqual(manifest["instrument_ids"], [777, 888])
        self.assertEqual(manifest["companies"][0]["reports"]["year"]["count"], 1)
        self.assertEqual(manifest["companies"][0]["prices"]["last_date"], "2026-11-02")
        self.assertIn("insider", manifest["companies"][0]["empty_datasets"])
        self.assertIn("Original report PDFs", manifest["limits"][0])
        catalogue = load_corpus_catalogue(result)
        self.assertEqual([company["instrument_id"] for company in catalogue], [777, 888])
        self.assertTrue(all(company["ticker"] == "" for company in catalogue))
        database = destination / "snapshot/evidence.sqlite3"
        self.assertEqual(corpus.digest(database), manifest["database_sha256"])
        with EvidenceStore(database, readonly=True) as store:
            for instrument in (777, 888):
                self.assertEqual(store.query_financials(instrument, "year", ["revenues"])[0]["value"], "10.25")
            second = store.freeze(self.root / "second-freeze")
        with EvidenceStore(second / "evidence.sqlite3", readonly=True) as repeated:
            self.assertEqual(repeated.stats(), manifest["counts"])
        (captures[0] / "reports.json").write_text("changed input after publication")
        self.assertTrue((destination / "captures/777/reports.json").read_text().startswith('{"instrument"'))
        with self.assertRaises(FileExistsError):
            corpus.build_corpus(captures, destination)

    def test_omitted_and_duplicate_requests_do_not_count_as_complete(self):
        directory = self.capture(777)
        path = directory / "manifest.json"
        original = json.loads(path.read_text())
        for records in (original["requests"][:-1], original["requests"] + [deepcopy(original["requests"][0])]):
            with self.subTest(count=len(records)):
                path.write_text(json.dumps(dict(original, requests=records)))
                with self.assertRaisesRegex(ValueError, "complete request plan"):
                    corpus.verify_capture(directory)

    def test_input_order_preserves_shared_kpi_definitions_in_utc_time(self):
        older, newer = [self.capture(i) for i in (777, 888)]
        definitions = {"kpiHistoryMetadatas": [{"kpiId": 29, "format": "%", "isString": False},
                                               {"kpiId": 64, "format": "MCURR", "isString": False}]}
        for directory, stamp in ((older, "2026-11-03T01:30:00+02:00"), (newer, "2026-11-03T00:00:00Z")):
            self.replace_payload(directory, "kpi-metadata", definitions)
            path = directory / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["retrieved_at_utc"] = stamp
            path.write_text(json.dumps(manifest))
        normalized = []
        for name, captures in (("chronological", [older, newer]), ("reversed", [newer, older])):
            result = corpus.build_corpus(captures, self.root / name)
            manifest = json.loads(result.read_text())
            records = {}
            with EvidenceStore(result.parent / "snapshot/evidence.sqlite3", readonly=True) as store:
                for instrument in (777, 888):
                    rows = store.query_financials(instrument, "year", ["kpi_29", "kpi_64"])
                    by_metric = {row["metric"]: row for row in rows}
                    for metric, expected in (("kpi_29", ("percent", "1")), ("kpi_64", ("currency", "1000000"))):
                        record = by_metric[metric]
                        self.assertEqual((record["unit"], record["scale"]), expected)
                        source = store.get_source(record["metadata_source_id"])
                        self.assertEqual(source["observed_at"], "2026-11-02T23:30:00+00:00")
                        records[instrument, metric] = (record["unit"], record["scale"], record["metadata_source_id"])
            self.assertEqual(manifest["instrument_ids"], [777, 888])
            normalized.append(records)
        self.assertEqual(normalized[0], normalized[1])

    def test_capture_timestamp_requires_valid_explicit_timezone(self):
        directory = self.capture(777)
        path = directory / "manifest.json"
        manifest = json.loads(path.read_text())
        for stamp in (None, "not-a-timestamp", "2026-11-03T12:00:00"):
            with self.subTest(timestamp=stamp):
                manifest["retrieved_at_utc"] = stamp
                path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "timestamp"):
                    corpus.verify_capture(directory)

    def test_corruption_never_publishes_partial_corpus(self):
        directory = self.capture(777)
        (directory / "prices.json").write_text('{}')
        destination = self.root / "published"
        with self.assertRaisesRegex(ValueError, "hash or size"):
            corpus.build_corpus([directory], destination)
        self.assertFalse(destination.exists())
        self.assertFalse(list(self.root.glob('.corpus-*')))

    def test_wrong_report_issuer_and_http200_error_are_rejected(self):
        directory = self.capture(777)
        original = json.loads((directory / "reports.json").read_text())
        for payload in ({"reportList": [dict(original, instrument=888)]},
                        {"reportList": [dict(original, error="No entitlement")]},
                        {"errorMessage": "No entitlement"}):
            with self.subTest(payload=payload):
                self.replace_payload(directory, "reports", payload)
                with self.assertRaisesRegex(ValueError, "mismatch or provider error|Provider error"):
                    corpus.verify_capture(directory)

    def test_required_arrays_distinguish_missing_definitions_from_empty_events(self):
        directory = self.capture(777)
        for name, field in corpus.ARRAY_FIELDS.items():
            original = json.loads((directory / (name + ".json")).read_text())
            for payload in ({}, {field: None}):
                with self.subTest(dataset=name, payload=payload):
                    self.replace_payload(directory, name, payload)
                    with self.assertRaisesRegex(ValueError, "Missing or invalid"):
                        corpus.verify_capture(directory)
            self.replace_payload(directory, name, {field: []})
            if name in corpus.REQUIRED_NONEMPTY:
                with self.subTest(empty_required=name), self.assertRaisesRegex(ValueError, "empty"):
                    corpus.verify_capture(directory)
            elif name not in ("instruments",):
                coverage, _ = corpus.verify_capture(directory)
                self.assertIn(name, coverage["empty_datasets"])
            if name in corpus.DEFINITION_IDS:
                self.replace_payload(directory, name, {field: [{}]})
                with self.assertRaisesRegex(ValueError, "definition identifier"):
                    corpus.verify_capture(directory)
            self.replace_payload(directory, name, original)

    def test_kpi_echoes_and_current_nested_issuer_must_match_request(self):
        directory = self.capture(777)
        manifest = json.loads((directory / "manifest.json").read_text())
        for suffix, changes in (("/summary", ({"instrument": 888}, {"reportType": "wrong"})),
                                ("/history", ({"kpiId": 999}, {"reportTime": "wrong"}, {"priceValue": "wrong"})),
                                ("/last/latest", ({"value": {"i": 888, "n": 10}},))):
            record = next(row for row in manifest["requests"] if row["endpoint"].endswith(suffix))
            original = json.loads((directory / record["file"]).read_text())
            for change in changes:
                with self.subTest(endpoint=record["endpoint"], change=change):
                    self.replace_payload(directory, record["dataset"], dict(original, **change))
                    with self.assertRaisesRegex(ValueError, "mismatch"):
                        corpus.verify_capture(directory)
            self.replace_payload(directory, record["dataset"], original)

    def test_nested_context_errors_and_scoped_ids_are_checked_without_rejecting_global_rows(self):
        directory = self.capture(777)
        for payload in ({"list": [{"insId": 777, "error": "No entitlement", "values": []}]},
                        {"list": [{"insId": 888, "values": []}]}):
            with self.subTest(payload=payload):
                self.replace_payload(directory, "insider", payload)
                with self.assertRaisesRegex(ValueError, "Provider error|instrument mismatch"):
                    corpus.verify_capture(directory)
        self.replace_payload(directory, "insider", {"list": []})
        self.replace_payload(directory, "shorts", {"list": [{"insId": 888, "shortsProc": 1}]})
        self.replace_payload(directory, "splits", {"stockSplitList": [{"instrumentId": 888, "values": []}]})
        corpus.verify_capture(directory)

    def test_provider_errors_inside_values_are_rejected_without_parsing_strings(self):
        directory = self.capture(777)
        manifest = json.loads((directory / "manifest.json").read_text())
        current = next(row for row in manifest["requests"] if row["endpoint"].endswith("/last/latest"))
        original = json.loads((directory / current["file"]).read_text())
        self.replace_payload(directory, current["dataset"], dict(original, value={"i": 777, "error": "No entitlement"}))
        with self.assertRaisesRegex(ValueError, "Provider error"):
            corpus.verify_capture(directory)
        self.replace_payload(directory, current["dataset"], original)
        self.replace_payload(directory, "insider", {"list": [{"insId": 777, "values": [{"errorMessage": "No entitlement"}]}]})
        with self.assertRaisesRegex(ValueError, "Provider error"):
            corpus.verify_capture(directory)
        self.replace_payload(directory, "insider", {"list": [{"insId": 777, "values": [],
                                                               "description": '{"error":"ordinary source text"}'}]})
        corpus.verify_capture(directory)

    def test_selected_identity_and_required_history_are_checked(self):
        directory = self.capture(777)
        original = json.loads((directory / "instruments.json").read_text())
        self.replace_payload(directory, "instruments", {"instruments": [{"insId": 888}]})
        with self.assertRaisesRegex(ValueError, "catalogue"):
            corpus.verify_capture(directory)
        self.replace_payload(directory, "instruments", original)
        self.replace_payload(directory, "prices", {"instrument": 777, "stockPricesList": []})
        with self.assertRaisesRegex(ValueError, "nonempty"):
            corpus.verify_capture(directory)


if __name__ == "__main__":
    unittest.main()
