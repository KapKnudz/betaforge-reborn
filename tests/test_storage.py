import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from betaforge.storage import EvidenceStore


def report(amount="10.25", **changes):
    row = {"year": 2025, "period": 5, "report_Start_Date": "2025-01-01T00:00:00",
           "report_End_Date": "2025-12-31T00:00:00", "report_Date": "2026-01-29T00:00:00",
           "currency": "SEK", "currency_Ratio": 1.0, "revenues": float(amount),
           "net_Debt": 5, "free_Cash_Flow": None, "number_Of_Shares": 2,
           "earnings_Per_Share": 1.25, "dividend": 0.5}
    row.update(changes)
    return row


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = EvidenceStore(self.root / "store/evidence.sqlite3")
        self.counter = 0

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def snapshot(self, payload=None, endpoint="/v1/instruments/426/reports/year", parameters=None, timestamp=None):
        self.counter += 1
        directory = self.root / f"input{self.counter}"
        directory.mkdir()
        body = json.dumps(payload if payload is not None else {"instrument": 426, "reports": [report()]}).encode()
        (directory / "data.json").write_bytes(body)
        manifest = {"retrieved_at": timestamp or f"2026-11-01T00:00:{self.counter:02d}+00:00", "requests": [{"endpoint": endpoint, "parameters": parameters if parameters is not None else {"original": 1}, "http_status": 200, "file": "data.json", "sha256": hashlib.sha256(body).hexdigest()}]}
        (directory / "manifest.json").write_text(json.dumps(manifest))
        return directory

    def test_decimal_null_stock_flow_and_source_pointer(self):
        self.store.ingest_snapshot(self.snapshot())
        values = {r["metric"]: r for r in self.store.query_financials(426)}
        self.assertEqual(values["revenues"]["value"], "10.25")
        self.assertEqual(values["revenues"]["kind"], "flow")
        self.assertEqual(values["net_Debt"]["kind"], "stock")
        self.assertEqual(values["dividend"]["kind"], "distribution")
        self.assertIsNone(values["free_Cash_Flow"]["value"])
        self.assertEqual(values["earnings_Per_Share"]["scale"], "1")
        self.assertEqual(values["number_Of_Shares"]["scale"], "1000000")
        self.assertEqual(values["revenues"]["currency"], "SEK")
        self.assertEqual(values["revenues"]["pointer"], "/reports/0/revenues")
        source = self.store.get_source(values["revenues"]["source_id"])
        self.assertTrue(source["blob_path"].startswith("blobs/"))

    def test_revisions_deduplication_reversion_and_frozen_repeatability(self):
        first = self.snapshot()
        self.store.ingest_snapshot(first)
        count = self.store.stats()["observations"]
        self.store.ingest_snapshot(first)
        self.assertEqual(self.store.stats()["observations"], count)
        snapshot = self.store.freeze(self.root / "frozen")
        changed = self.snapshot({"instrument": 426, "reports": [report("20.5")]})
        self.store.ingest_snapshot(changed)
        self.assertEqual(self.store.query_financials(426, fields=["revenues"])[0]["value"], "20.5")
        with EvidenceStore(snapshot / "evidence.sqlite3", readonly=True) as frozen:
            self.assertEqual(frozen.query_financials(426, fields=["revenues"])[0]["value"], "10.25")
            with self.assertRaises(ValueError):
                frozen.ingest_snapshot(changed)
        reverted = self.snapshot()
        self.store.ingest_snapshot(reverted)
        self.assertEqual(self.store.query_financials(426, fields=["revenues"])[0]["value"], "10.25")
        self.store.ingest_snapshot(changed)  # Older acquisition cannot override later reversion.
        self.assertEqual(self.store.query_financials(426, fields=["revenues"])[0]["value"], "10.25")
        self.assertEqual(self.store.stats()["observations"], count + 1)
        with self.assertRaises(FileExistsError):
            self.store.freeze(snapshot)

    def test_bad_later_row_rolls_back_all_normalized_data(self):
        bad = self.snapshot({"instrument": 426, "reports": [report(), report(report_End_Date="2024-01-01")]})
        with self.assertRaises(ValueError):
            self.store.ingest_snapshot(bad)
        self.assertEqual(self.store.stats()["observations"], 0)
        self.assertEqual(self.store.stats()["sources"], 0)

    def test_identity_and_hash_validation(self):
        wrong = self.snapshot({"instrument": 999, "reports": [report()]})
        with self.assertRaises(ValueError):
            self.store.ingest_snapshot(wrong)
        corrupt = self.snapshot()
        (corrupt / "data.json").write_text("{}")
        with self.assertRaises(ValueError):
            self.store.ingest_snapshot(corrupt)
        self.assertEqual(self.store.stats()["observations"], 0)

    def test_converted_currency_never_uses_report_currency_without_quote_metadata(self):
        self.store.ingest_snapshot(self.snapshot(parameters={"original": 0}))
        observation = self.store.query_financials(426, fields=["revenues"])[0]
        self.assertIsNone(observation["currency"])
        self.assertEqual(observation["original_currency"], "SEK")
        self.assertEqual(observation["currency_mode"], "converted")

    def test_quote_currency_and_price_instrument_identity(self):
        self.store.ingest_snapshot(self.snapshot({"instruments": [{"insId": 426, "stockPriceCurrency": "EUR"}]}, "/v1/instruments", {}))
        self.store.ingest_snapshot(self.snapshot({"instrument": 426, "stockPricesList": [{"d": "2026-10-30", "c": 12.345, "v": 100}]}, "/v1/instruments/426/stockprices", {}))
        price = self.store.query_financials(426, "price", ["price_close"])[0]
        self.assertEqual(price["currency"], "EUR")
        self.assertEqual(price["value"], "12.345")
        self.assertEqual(price["period_end"], "2026-10-30")

    def test_annual_summary_latest_r12_and_pagination(self):
        payload = {"instrument": 426, "reportType": "year", "kpis": [{"KpiId": 2, "values": [{"y": 2026, "p": 3, "v": 12.1}, {"y": 2025, "p": 5, "v": 10}]}]}
        self.store.ingest_snapshot(self.snapshot(payload, "/v1/instruments/426/kpis/year/summary", {}))
        latest = self.store.query_financials(426, limit=1)[0]
        self.assertEqual(latest["report_type"], "r12")
        self.assertIsNone(latest["period_end"])
        self.assertIsNone(latest["price_type"])
        self.assertEqual(self.store.query_financials(426, limit=1, offset=1)[0]["year"], 2025)

    def test_report_fact_separate_from_provider_and_evidence_required(self):
        self.store.ingest_snapshot(self.snapshot())
        fact = {"metric": "eps_basic", "value": "3.63", "unit": "SEK/share", "scale": "1", "currency": "SEK", "report_type": "quarter", "year": 2026, "period": 3, "period_start": "2026-07-01", "period_end": "2026-09-30", "kind": "per_share", "basis": "basic", "status": "matched", "evidence": {"report_id": "granges-q3-2026", "page": 21}}
        data = {"instrument_id": 426, "mapping_version": "granges-v1", "observed_at": "2026-11-01T10:00:00Z", "facts": [fact]}
        path = self.root / "facts.json"; path.write_text(json.dumps(data))
        self.store.add_report_facts(path)
        record = self.store.query_financials(426, fields=["eps_basic"])[0]
        self.assertEqual(record["evidence"]["page"], 21)
        self.assertEqual(record["provider"], "issuer_report")
        self.assertTrue(self.store.query_financials(426, fields=["earnings_Per_Share"]))
        del fact["evidence"]
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.store.add_report_facts(path)

    def test_credentials_and_path_escape_rejected(self):
        path = self.snapshot(parameters={"authKey": "not-a-real-key"})
        with self.assertRaises(ValueError):
            self.store.ingest_snapshot(path)
        path = self.snapshot()
        manifest = json.loads((path / "manifest.json").read_text())
        manifest["requests"][0]["file"] = "../escape.json"
        (path / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            self.store.ingest_snapshot(path)

    def test_failed_fetch_does_not_erase_existing_data(self):
        self.store.ingest_snapshot(self.snapshot())
        path = self.snapshot()
        manifest = json.loads((path / "manifest.json").read_text())
        manifest["requests"][0] = {"endpoint": "/v1/instruments/426/reports/year", "http_status": 403}
        (path / "manifest.json").write_text(json.dumps(manifest))
        self.store.ingest_snapshot(path)
        self.assertEqual(self.store.query_financials(426, fields=["revenues"])[0]["value"], "10.25")
        self.assertEqual(self.store.stats()["acquisitions"], 2)

    def test_company_filter_does_not_return_other_short_positions(self):
        payload = {"list": [{"insId": 426, "shortsProc": -1.0}, {"insId": 999, "shortsProc": -2.0}]}
        self.store.ingest_snapshot(self.snapshot(payload, "/v1/holdings/shorts", {}))
        rows = self.store.query_dataset("holdings_shorts", 426)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["payload"]["insId"], 426)

    def test_price_row_identity_cannot_escape_requested_instrument(self):
        payload = {"instrument": 426, "stockPricesList": [{"i": 999, "d": "2026-10-30", "c": 10}]}
        with self.assertRaises(ValueError):
            self.store.ingest_snapshot(self.snapshot(payload, "/v1/instruments/426/stockprices", {}))
        self.assertEqual(self.store.stats()["observations"], 0)

    def test_freeze_rejects_corrupted_blob_without_publishing(self):
        self.store.ingest_snapshot(self.snapshot())
        next(self.store.blob_dir.glob('*.json')).write_text('{}')
        destination = self.root / "broken-freeze"
        with self.assertRaises(ValueError):
            self.store.freeze(destination)
        self.assertFalse(destination.exists())

    def test_original_and_converted_series_stay_distinct(self):
        self.store.ingest_snapshot(self.snapshot(parameters={"original": 1}))
        self.store.ingest_snapshot(self.snapshot(parameters={"original": 0}))
        rows = self.store.query_financials(426, fields=["revenues"])
        self.assertEqual({row["currency_mode"] for row in rows}, {"original", "converted"})

    def test_unknown_fields_retained_and_naive_acquisition_time_rejected(self):
        self.store.ingest_snapshot(self.snapshot({"instrument": 426, "reports": [report(new_Provider_Field="unmapped text")]}))
        self.assertEqual(self.store.query_dataset("reports", 426)[0]["payload"]["new_Provider_Field"], "unmapped text")
        with self.assertRaises(ValueError):
            self.store.ingest_snapshot(self.snapshot(timestamp="2026-11-01T12:00:00"))

    def test_kpi_units_bind_metadata_without_inventing_currency(self):
        definitions = {"kpiHistoryMetadatas": [
            {"kpiId": 29, "format": "%", "isString": False},
            {"kpiId": 62, "format": "MCURR", "isString": False},
            {"kpiId": 49, "format": None, "isString": False}]}
        self.store.ingest_snapshot(self.snapshot(definitions, "/v1/instruments/kpis/metadata", {}))
        payload = {"instrument": 426, "kpis": [{"kpiId": kpi, "values": [{"y": 2025, "p": 5, "v": 12.5}]} for kpi in [2, 3, 4, 10, 11, 15, 76, 29, 37, 62, 49]]}
        self.store.ingest_snapshot(self.snapshot(payload, "/v1/instruments/426/kpis/year/summary", {}))
        records = {r["metric"]: r for r in self.store.query_financials(426)}
        for kpi in [2, 3, 4, 10, 11, 15, 76]:
            self.assertEqual(records[f"kpi_{kpi}"]["unit"], "multiple")
            self.assertEqual(records[f"kpi_{kpi}"]["scale"], "1")
        self.assertEqual(records["kpi_29"]["unit"], "percent")
        self.assertEqual(records["kpi_29"]["value"], "12.5")
        self.assertEqual(records["kpi_29"]["scale"], "1")
        self.assertEqual(records["kpi_62"]["unit"], "currency")
        self.assertEqual(records["kpi_62"]["scale"], "1000000")
        self.assertIsNone(records["kpi_62"]["currency"])
        self.assertEqual(records["kpi_49"]["unit"], "provider_defined")
        self.assertEqual(records["kpi_37"]["unit"], "percent")
        self.assertEqual(records["kpi_37"]["mapping_version"], "borsdata-kpi-v2")
        self.assertEqual(self.store.get_source(records["kpi_29"]["metadata_source_id"])["endpoint"], "/v1/instruments/kpis/metadata")

    def test_report_links_reject_missing_stale_hash_and_page_bounds(self):
        digest = "a" * 64
        fact = {"metric": "eps_basic", "value": "3.63", "unit": "SEK/share", "scale": "1", "currency": "SEK", "report_type": "quarter", "year": 2026, "period": 3, "period_end": "2026-09-30", "kind": "per_share", "basis": "basic", "status": "matched", "evidence": {"report_id": "q3", "page": 21, "sha256": digest}}
        data = {"instrument_id": 426, "mapping_version": "granges-v1", "observed_at": "2026-11-01T10:00:00Z", "facts": [fact]}
        path = self.root / "facts.json"; path.write_text(json.dumps(data))
        self.store.add_report_facts(path)
        self.assertEqual(self.store.validate_report_links({"q3": {"source_sha256": digest, "pages": 21}}), {"validated_report_observations": 1})
        # A company packet must not demand unrelated issuers' PDFs from a shared store.
        other = dict(data, instrument_id=999, facts=[dict(fact, evidence={"report_id": "other", "page": 1, "sha256": "c" * 64})])
        other_path = self.root / "other-facts.json"; other_path.write_text(json.dumps(other))
        self.store.add_report_facts(other_path)
        self.assertEqual(self.store.validate_report_links({"q3": {"source_sha256": digest, "pages": 21}}, instrument_id=426), {"validated_report_observations": 1})
        with self.assertRaisesRegex(ValueError, 'absent report: other'):
            self.store.validate_report_links({"q3": {"source_sha256": digest, "pages": 21}})
        for catalogue in [{}, {"q3": {"source_sha256": "b" * 64, "pages": 21}}, {"q3": {"source_sha256": digest, "pages": 20}}]:
            with self.assertRaises(ValueError):
                self.store.validate_report_links(catalogue)
        # A newly selected revision must not conceal stale evidence still addressable by ID.
        fact["evidence"]["sha256"] = "b" * 64
        data["observed_at"] = "2026-11-01T11:00:00Z"
        path.write_text(json.dumps(data)); self.store.add_report_facts(path)
        with self.assertRaises(ValueError):
            self.store.validate_report_links({"q3": {"source_sha256": "b" * 64, "pages": 21}})


if __name__ == "__main__":
    unittest.main()
