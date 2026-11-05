import http.client
import hashlib
from copy import deepcopy
from contextlib import closing
import json
from pathlib import Path
import sys
import sqlite3
import tempfile
import threading
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import serve_progress as progress


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "work").mkdir()
        (self.root / "web/progress").mkdir(parents=True)
        (self.root / "web/progress/index.html").write_text("<h1>Progress</h1>")
        (self.root / "web/progress/app.js").write_text("console.log('progress')")
        (self.root / "README.md").write_text("Public project overview")
        (self.root / ".env").write_text("secret must never be served")
        (self.root / "data").mkdir()
        (self.root / "data/private.json").write_text('{"secret":true}')
        self.plan_path = self.root / "work/plan.json"
        self.plan = {
            "version": 1, "updated_at": "2026-11-03T15:00:00Z",
            "goal": "Explain the project", "scope": "Operating companies", "next_task": "task-1",
            "milestones": [{"id": "first", "title": "First milestone", "status": "in_progress", "summary": "Validate evidence"}],
            "tasks": [{"id": "task-1", "milestone": "first", "title": "Check inputs", "status": "pending",
                       "acceptance": ["Sources match"], "evidence": [], "blocker": None, "note": "Use existing data"}],
            "session": {"task": "task-1", "summary": "Prepared plan", "next_step": "Check inputs"},
            "references": [{"label": "Overview", "path": "README.md"}],
        }
        self.save_plan()
        self.server = progress.make_server(0, root=self.root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def save_plan(self):
        self.plan_path.write_text(json.dumps(self.plan))

    def request(self, path, method="GET", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_live_plan_updates_without_restart(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, headers, body = self.request("/api/plan")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertTrue(headers["Content-Type"].startswith("application/json"))
        self.assertEqual(json.loads(body)["goal"], "Explain the project")
        self.plan["goal"] = "New goal with <script>text</script>"
        self.save_plan()
        self.assertEqual(json.loads(self.request("/api/plan")[2])["goal"], self.plan["goal"])

    def test_process_view_assets_and_guide_are_explicit_routes(self):
        for name, content_type in (("process.js", "text/javascript"), ("process.css", "text/css")):
            body = "public process explanation: " + name
            (self.root / "web/progress" / name).write_text(body)
            code, headers, actual = self.request("/" + name)
            self.assertEqual((code, actual), (200, body.encode()))
            self.assertTrue(headers["Content-Type"].startswith(content_type))
            self.assertEqual(headers["Cache-Control"], "no-store")
        (self.root / "docs").mkdir(exist_ok=True)
        (self.root / "docs/analysis-process.md").write_text("Public process guide")
        self.assertEqual(self.request("/docs/docs/analysis-process.md")[2], b"Public process guide")
        self.assertEqual(self.request("/web/progress/process.js")[0], 404)
        self.assertEqual(self.request("/docs/data/private.json")[0], 404)

    def test_completed_plan_allows_no_next_task(self):
        self.plan["next_task"] = None
        self.plan["tasks"][0]["status"] = "done"
        self.plan["milestones"][0]["status"] = "done"
        self.save_plan()
        status, _, body = self.request("/api/plan")
        self.assertEqual(status, 200)
        self.assertIsNone(json.loads(body)["next_task"])
        self.plan["tasks"][0]["status"] = "pending"
        self.save_plan()
        self.assertEqual(self.request("/api/plan")[0], 503)

    def test_completed_task_cannot_be_the_next_action(self):
        self.plan["tasks"][0]["status"] = "done"
        self.plan["milestones"][0]["status"] = "done"
        self.save_plan()
        self.assertEqual(self.request("/api/plan")[0], 503)

        self.plan["tasks"].append(dict(self.plan["tasks"][0], id="task-2", status="pending"))
        self.plan["milestones"][0]["status"] = "in_progress"
        self.save_plan()
        self.assertEqual(self.request("/api/plan")[0], 503)

        self.plan["next_task"] = "task-2"
        for status in ("pending", "in_progress", "blocked"):
            with self.subTest(status=status):
                self.plan["tasks"][1]["status"] = status
                self.save_plan()
                self.assertEqual(self.request("/api/plan")[0], 200)

    def test_version_and_session_task_are_validated(self):
        for version in (True, 1.0, "1", 2):
            with self.subTest(version=version):
                self.plan["version"] = version
                self.save_plan()
                self.assertEqual(self.request("/api/plan")[0], 503)
        self.plan["version"] = 1
        self.plan["session"]["task"] = "unknown-task"
        self.save_plan()
        self.assertEqual(self.request("/api/plan")[0], 503)

    def test_optional_task_summaries_are_validated(self):
        self.plan["tasks"][0].update(summary="Preserve evidence", purpose="Explain the inputs")
        self.save_plan()
        self.assertEqual(self.request("/api/plan")[0], 200)
        self.plan["tasks"][0]["purpose"] = []
        self.save_plan()
        self.assertEqual(self.request("/api/plan")[0], 503)

    def saved_view(self):
        return {
            "schema_version": 1, "id": "sample-20261101",
            "company": {"name": "Sample", "ticker": "SAMP", "instrument_id": 1},
            "analysis_date": "2026-11-01", "reviewed_at": "2026-11-03T12:00:00Z",
            "method": "Saved scenario analysis", "price": None,
            "conclusion": "Conditional saved result", "scenarios": [],
            "probability": {"weights": {}, "basis": None, "status": "missing"},
            "calculations": [], "original_calculations": [], "interpretation": [],
            "notes": [], "narrative": "Saved report", "sources": [],
            "benchmark": {"candidate_annualized_return_percent": None,
                          "benchmark_annualized_return_percent": None,
                          "difference_percentage_points": None,
                          "interpretation": None, "limits": [], "context": None},
            "provenance": {"database_sha256": "a" * 64, "packet_sha256": "b" * 64,
                           "review_sha256": "c" * 64, "run_sha256": "d" * 64,
                           "summary_sha256": "e" * 64, "narrative_sha256": "f" * 64,
                           "model": "gpt-6.1-sol", "reasoning_effort": "high", "status": "completed",
                           "started_at": "2026-11-01T12:00:00Z", "finished_at": "2026-11-01T12:01:00Z",
                           "coverage": {}},
        }

    def configure_view(self, market_db=None, corpus=None):
        file = self.root / "data/saved-view.json"
        file.write_text(json.dumps(self.saved_view()))
        self.stop()
        self.server = progress.make_server(0, root=self.root, analyses=[file], market_db=market_db, corpus=corpus)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return file

    def corpus_manifest(self):
        return {
            "version": 1, "status": "verified_api_capture", "instrument_ids": [1, 2],
            "snapshot": "snapshot", "database_sha256": "a" * 64,
            "companies": [
                {"instrument_id": instrument,
                 "identity": {"name": name, "ticker": ticker, "provider_private": "secret provider data"},
                 "retrieved_at_utc": "2026-11-04T12:00:00+00:00", "datasets": [{"private": "raw values"}]}
                for instrument, name, ticker in ((1, "Sample", "SAMP"), (2, "Captured issuer", ""))],
        }

    def save_corpus(self, manifest=None):
        file = self.root / "data/corpus-manifest.json"
        file.write_text(json.dumps(self.corpus_manifest() if manifest is None else manifest))
        return file

    def test_corpus_lists_only_company_metadata_without_saved_runs_or_evidence_reads(self):
        file = self.save_corpus()
        (self.root / "data/evidence.sqlite3").write_bytes(b"private database")
        (self.root / "data/raw.json").write_text('{"private":"raw provider response"}')
        self.stop()
        with mock.patch.object(progress, "EvidenceStore") as store:
            self.server = progress.make_server(0, root=self.root, corpus=file)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            status, headers, body = self.request("/api/runs")
            self.assertEqual(status, 200)
            self.assertEqual(headers["Cache-Control"], "no-store")
            expected = {"runs": [], "companies": [
                {"instrument_id": instrument, "name": name, "ticker": ticker,
                 "captured_at": "2026-11-04T12:00:00+00:00"}
                for instrument, name, ticker in ((1, "Sample", "SAMP"), (2, "Captured issuer", ""))]}
            self.assertEqual(json.loads(body), expected)
            self.assertNotIn(str(file).encode(), body)
            for path in ("/api/market-price/1", "/api/market-price/2", "/api/runs/2",
                         "/data/corpus-manifest.json", "/data/evidence.sqlite3", "/data/raw.json",
                         "/api/corpus", "/api/companies/2"):
                with self.subTest(path=path):
                    self.assertEqual(self.request(path)[0], 404)
            store.assert_not_called()
        file.unlink()
        self.assertEqual(json.loads(self.request("/api/runs")[2]), expected)
        self.assertEqual(self.request("/api/runs", "HEAD")[2], b"")

    def test_corpus_and_saved_runs_keep_existing_analysis_and_quote_boundaries(self):
        file = self.save_corpus()
        self.configure_view(corpus=file)
        payload = json.loads(self.request("/api/runs")[2])
        self.assertEqual(len(payload["runs"]), 1)
        self.assertEqual(len(payload["companies"]), 2)
        self.assertEqual(json.loads(self.request("/api/runs/sample-20261101")[2]), self.saved_view())
        self.assertEqual(json.loads(self.request("/api/market-price/1")[2]), {"quote": None})
        self.assertEqual(self.request("/api/market-price/2")[0], 404)

    def test_invalid_corpus_catalogue_fails_before_binding(self):
        invalid = [{}, {**self.corpus_manifest(), "version": True},
                   {**self.corpus_manifest(), "status": "incomplete"}]
        for ids in (None, [1, 1], [1, 0], [1, -2], [1, True], [1, "2"], [1, 2, 3]):
            invalid.append({**self.corpus_manifest(), "instrument_ids": ids})
        for change in ({"instrument_id": 1}, {"instrument_id": True}, {"instrument_id": 0},
                       {"identity": None}, {"identity": {"name": "Issuer", "ticker": False}},
                       {"identity": {"name": "", "ticker": "A"}},
                       {"identity": {"name": "Unsafe\nname", "ticker": "A"}},
                       {"identity": {"name": "<script>", "ticker": "A"}},
                       {"identity": {"name": "Issuer", "ticker": "   "}},
                       {"identity": {"name": "Issuer", "ticker": "A\x00"}},
                       {"retrieved_at_utc": None}, {"retrieved_at_utc": "2026-11-04"},
                       {"retrieved_at_utc": "2026-11-04T12:00:00"},
                       {"retrieved_at_utc": "2026-02-30T12:00:00Z"},
                       {"retrieved_at_utc": "2026-11-04T12:00:00+00:99"}):
            manifest = deepcopy(self.corpus_manifest())
            manifest["companies"][1].update(change)
            invalid.append(manifest)
        manifest = self.corpus_manifest()
        manifest["companies"].append(None)
        invalid.append(manifest)
        with mock.patch.object(progress, "ThreadingHTTPServer") as server:
            for manifest in invalid:
                with self.subTest(manifest=manifest):
                    with self.assertRaises(ValueError):
                        progress.make_server(0, root=self.root, corpus=self.save_corpus(manifest))
            server.assert_not_called()

    def test_corpus_missing_and_null_tickers_do_not_block_startup(self):
        for identity in ({"name": "Named issuer"}, {"name": "Named issuer", "ticker": None}):
            with self.subTest(identity=identity):
                manifest = self.corpus_manifest()
                manifest["companies"][1]["identity"] = identity
                self.configure_view(corpus=self.save_corpus(manifest))
                company = json.loads(self.request("/api/runs")[2])["companies"][1]
                self.assertEqual(company, {"instrument_id": 2, "name": "Named issuer", "ticker": "",
                                           "captured_at": "2026-11-04T12:00:00+00:00"})

    def test_corpus_requires_explicit_regular_manifest_path_and_valid_json(self):
        file = self.save_corpus()
        link = self.root / "data/linked.json"
        link.symlink_to(file)
        directory_link = self.root / "linked-data"
        directory_link.symlink_to(file.parent, target_is_directory=True)
        with mock.patch.object(progress, "ThreadingHTTPServer") as server:
            for path in (self.root / "missing.json", link, directory_link / file.name,
                         file.parent / ".." / "data" / file.name, file.parent):
                with self.subTest(path=path):
                    with self.assertRaises(ValueError):
                        progress.make_server(0, root=self.root, corpus=path)
            for body in ("{", "[]", '{"version":1,"version":1}', "null"):
                file.write_text(body)
                with self.subTest(body=body):
                    with self.assertRaises(ValueError):
                        progress.make_server(0, root=self.root, corpus=file)
            server.assert_not_called()

    def ingest_market_data(self, database, rows=(), timestamp="2026-11-04T17:00:00Z"):
        directory = Path(tempfile.mkdtemp(dir=self.root))
        payloads = [({"instruments": [{"insId": 1, "stockPriceCurrency": "SEK"}]}, "/v1/instruments")]
        if rows:
            payloads.append(({"instrument": 1, "stockPricesList": rows}, "/v1/instruments/1/stockprices"))
        requests = []
        for index, (payload, endpoint) in enumerate(payloads):
            body = json.dumps(payload).encode()
            name = f"{index}.json"
            (directory / name).write_bytes(body)
            requests.append({"endpoint": endpoint, "parameters": {}, "http_status": 200,
                             "file": name, "sha256": hashlib.sha256(body).hexdigest()})
        (directory / "manifest.json").write_text(json.dumps({"retrieved_at": timestamp, "requests": requests}))
        with progress.EvidenceStore(database) as store:
            store.ingest_snapshot(directory)

    def test_market_quotes_are_opt_in_and_company_allowlisted(self):
        self.assertEqual(self.request("/api/market-price/1")[0], 404)
        self.configure_view()
        self.assertEqual(json.loads(self.request("/api/market-price/1")[2]), {"quote": None})
        for identifier in ("2", "01", "1/anything", "../data/private.json", "%31"):
            with self.subTest(identifier=identifier):
                self.assertEqual(self.request("/api/market-price/" + identifier)[0], 404)
        self.assertEqual(self.request("/api/market-price/1", "HEAD")[2], b"")

    def test_latest_stored_close_updates_without_touching_saved_report(self):
        database = self.root / "market/evidence.sqlite3"
        self.ingest_market_data(database)
        file = self.configure_view(market_db=database)
        saved = file.read_bytes()
        self.assertEqual(json.loads(self.request("/api/market-price/1")[2]), {"quote": None})
        rows = [{"d": "2026-11-02", "c": 10.25}, {"d": "2026-11-03", "c": 12.5}]
        self.ingest_market_data(database, rows)
        before = database.read_bytes()
        with mock.patch.object(progress, "EvidenceStore", wraps=progress.EvidenceStore) as store:
            status, headers, body = self.request("/api/market-price/1")
            self.assertEqual(status, 200)
            store.assert_called_once_with(database, readonly=True)
        quote = json.loads(body)["quote"]
        self.assertEqual(quote, {"instrument_id": 1, "value": "12.5", "scale": "1",
                                "unit": "currency/share", "currency": "SEK", "date": "2026-11-03",
                                "source_id": quote["source_id"], "provider": "Börsdata", "kind": "daily_close",
                                "retrieved_at": "2026-11-04T17:00:00+00:00", "checked_at": "2026-11-04T17:00:00+00:00"})
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(database.read_bytes(), before)
        self.assertNotIn(str(database).encode(), body)
        self.ingest_market_data(database, rows, timestamp="2026-11-05T17:00:00Z")
        checked = json.loads(self.request("/api/market-price/1")[2])["quote"]
        self.assertEqual(checked["retrieved_at"], quote["retrieved_at"])
        self.assertEqual(checked["checked_at"], "2026-11-05T17:00:00+00:00")
        self.ingest_market_data(database, [{"d": "2026-11-04", "c": 15.75}], "2026-11-05T18:00:00Z")
        self.assertEqual(json.loads(self.request("/api/market-price/1")[2])["quote"]["value"], "15.75")
        self.assertEqual(file.read_bytes(), saved)
        self.assertEqual(json.loads(self.request("/api/runs/sample-20261101")[2]), self.saved_view())

    def test_invalid_quotes_stay_unavailable(self):
        database = self.root / "market/evidence.sqlite3"
        self.ingest_market_data(database, [{"d": "2026-11-03", "c": 12.5}])
        self.configure_view(market_db=database)
        with closing(sqlite3.connect(database)) as connection, connection:
            original = json.loads(connection.execute("SELECT record FROM observations WHERE metric='price_close'").fetchone()[0])
        for changes in ({"value": "0"}, {"value": "-1"}, {"value": "NaN"}, {"value": True}, {"scale": "Infinity"},
                        {"scale": "0"}, {"unit": "shares"}, {"currency": None}, {"currency": "private/path"},
                        {"period_end": "2026-02-30"}, {"period_end": "2026-11-03T00:00:00"},
                        {"provider": "other"}, {"currency_mode": "converted"}, {"source_id": "/private/secret"}):
            with self.subTest(changes=changes):
                with closing(sqlite3.connect(database)) as connection, connection:
                    connection.execute("UPDATE observations SET record=? WHERE metric='price_close'", (json.dumps({**original, **changes}),))
                self.assertEqual(json.loads(self.request("/api/market-price/1")[2]), {"quote": None})

    def test_market_store_failures_are_safe_and_reports_remain_available(self):
        database = self.root / "market/evidence.sqlite3"
        self.ingest_market_data(database, [{"d": "2026-11-03", "c": 12.5}])
        self.configure_view(market_db=database)
        for content in (b"not sqlite", None):
            if content is None:
                database.unlink()
            else:
                database.write_bytes(content)
            status, _, body = self.request("/api/market-price/1")
            self.assertEqual(status, 503)
            self.assertNotIn(str(database).encode(), body)
            self.assertEqual(self.request("/api/runs/sample-20261101")[0], 200)
        self.assertFalse(database.exists())

    def test_market_database_is_validated_before_binding_without_creation(self):
        database = self.root / "missing/evidence.sqlite3"
        with mock.patch.object(progress, "ThreadingHTTPServer") as server:
            with self.assertRaisesRegex(ValueError, "Market evidence store unavailable"):
                progress.make_server(0, root=self.root, market_db=database)
            server.assert_not_called()
        self.assertFalse(database.parent.exists())
        database.parent.mkdir()
        with closing(sqlite3.connect(database)) as connection, connection:
            connection.execute("CREATE TABLE private_data (secret TEXT)")
            connection.execute("PRAGMA user_version=99")
        before = database.read_bytes()
        with mock.patch.object(progress, "ThreadingHTTPServer") as server:
            with self.assertRaises(ValueError):
                progress.make_server(0, root=self.root, market_db=database)
            server.assert_not_called()
        self.assertEqual(database.read_bytes(), before)
        self.assertFalse((database.parent / "blobs").exists())

    def test_saved_runs_are_opt_in_and_only_expose_configured_exports(self):
        self.assertEqual(json.loads(self.request("/api/runs")[2]), {"runs": [], "companies": []})
        self.assertEqual(self.request("/api/runs/sample-20261101")[0], 404)
        self.configure_view()
        status, _, body = self.request("/api/runs")
        self.assertEqual(status, 200)
        summary = json.loads(body)["runs"][0]
        self.assertEqual(summary["company"]["name"], "Sample")
        self.assertEqual(summary["analysis_kind"], "legacy")
        self.assertNotIn("narrative", summary)
        self.assertEqual(json.loads(self.request("/api/runs/sample-20261101")[2]), self.saved_view())
        for path in ("/api/runs/../private.json", "/api/runs/%2e%2e%2fprivate.json",
                     "/api/runs/unknown", "/api/runs/sample-20261101/answer.md", "/data/saved-view.json"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request("/api/runs/sample-20261101", "HEAD")[2], b"")
        self.assertEqual(self.request("/api/runs", headers={"Host": "remote.example"})[0], 403)

    def test_saved_views_are_validated_once_and_requests_do_not_reread_exports(self):
        with mock.patch.object(progress, "load_saved_view", wraps=progress.load_saved_view) as load:
            file = self.configure_view()
            load.assert_called_once_with(file)
            saved = file.read_bytes()
            for endpoint in ("/api/runs", "/api/runs/sample-20261101"):
                for method in ("GET", "HEAD"):
                    self.assertEqual(self.request(endpoint, method)[0], 200)
            load.assert_called_once_with(file)
            self.assertEqual(file.read_bytes(), saved)

    def test_saved_view_snapshot_survives_edited_or_unavailable_exports(self):
        file = self.configure_view()
        index = json.loads(self.request("/api/runs")[2])
        for content in ("{", json.dumps(dict(self.saved_view(), id="changed-id")),
                        json.dumps(dict(self.saved_view(), narrative="Changed report")), None, "symlink"):
            if content is None:
                file.unlink()
            elif content == "symlink":
                file.symlink_to(self.root / ".env")
            else:
                file.write_text(content)
            for endpoint in ("/api/runs", "/api/runs/sample-20261101"):
                status, _, body = self.request(endpoint)
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(body), index if endpoint == "/api/runs" else self.saved_view())
                self.assertNotIn(str(file).encode(), body)
            self.assertEqual(self.request("/api/runs/changed-id")[0], 404)
        self.assertEqual((self.root / ".env").read_text(), "secret must never be served")

    def test_restart_validates_and_adopts_revised_saved_export(self):
        file = self.configure_view()
        revised = dict(self.saved_view(), id="sample-revised", narrative="Revised report")
        file.write_text(json.dumps(revised))
        saved = file.read_bytes()
        self.stop()
        self.server = progress.make_server(0, root=self.root, analyses=[file])
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.assertEqual(self.request("/api/runs/sample-20261101")[0], 404)
        self.assertEqual(json.loads(self.request("/api/runs/sample-revised")[2]), revised)
        self.assertEqual(json.loads(self.request("/api/runs")[2])["runs"][0]["id"], "sample-revised")
        self.assertEqual(file.read_bytes(), saved)

    def test_duplicate_or_invalid_saved_views_fail_before_binding(self):
        file = self.root / "data/saved-view.json"
        file.write_text(json.dumps(self.saved_view()))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            progress.make_server(0, root=self.root, analyses=[file, file])
        file.write_text('{"secret":"not a saved view"}')
        with self.assertRaises(ValueError):
            progress.make_server(0, root=self.root, analyses=[file])

    def test_invalid_saved_source_is_rejected_before_binding_without_edits(self):
        view = self.saved_view()
        view["sources"] = [{"id": "annual-report", "title": "Annual report",
                            "period": {"start": None, "end": "2025-12-31"},
                            "published_at": "2026-02-01", "url": "https://example.com/report.pdf",
                            "sha256": "invalid", "prepared_sha256": "a" * 64, "pages": 1}]
        file = self.root / "data/saved-view.json"
        file.write_text(json.dumps(view))
        before = file.read_bytes()
        with mock.patch.object(progress, "ThreadingHTTPServer") as server:
            with self.assertRaisesRegex(ValueError, "Invalid source hash"):
                progress.make_server(0, root=self.root, analyses=[file])
            server.assert_not_called()
        self.assertEqual(file.read_bytes(), before)

    def test_missing_malformed_and_inconsistent_plan_return_safe_errors(self):
        for content in ("{", "[]", '{"version":1}', "null"):
            with self.subTest(content=content):
                self.plan_path.write_text(content)
                status, _, body = self.request("/api/plan")
                self.assertEqual(status, 503)
                self.assertNotIn(str(self.root).encode(), body)
        self.plan["tasks"][0]["milestone"] = "not-a-milestone"
        self.save_plan()
        self.assertEqual(self.request("/api/plan")[0], 503)
        self.plan_path.unlink()
        self.assertEqual(self.request("/api/plan")[0], 503)

    def test_only_fixed_files_are_available(self):
        for path in ("/.env", "/data/private.json", "/.git/config", "/README.md", "/work/plan.json",
                     "/../.env", "/%2e%2e/.env", "/docs/../.env", "/docs/%2e%2e/.env",
                     "/docs/%2fetc/passwd", "/docs/README.md/../.env", "/docs/unknown.md"):
            with self.subTest(path=path):
                status, _, body = self.request(path)
                self.assertEqual(status, 404)
                self.assertNotIn(b"secret", body)
        self.assertEqual(self.request("/")[0], 200)
        status, headers, body = self.request("/docs/README.md")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"Public project overview")
        self.assertTrue(headers["Content-Type"].startswith("text/plain"))
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])

    def test_symlink_files_and_directories_are_not_served(self):
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to(self.root / ".env")
        self.assertEqual(self.request("/docs/README.md")[0], 404)
        self.plan_path.unlink()
        self.plan_path.symlink_to(self.root / ".env")
        self.assertEqual(self.request("/api/plan")[0], 503)
        (self.root / "docs").symlink_to(self.root / "data", target_is_directory=True)
        (self.root / "data/architecture.md").write_text("private")
        self.assertEqual(self.request("/docs/docs/architecture.md")[0], 404)

    def test_write_methods_and_remote_host_are_rejected(self):
        before = self.plan_path.read_bytes()
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(self.request("/api/plan", method)[0], 405)
        self.assertEqual(self.plan_path.read_bytes(), before)
        self.assertEqual(self.request("/api/plan", headers={"Host": "attacker.example"})[0], 403)
        status, headers, body = self.request("/api/plan", "HEAD")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")
        self.assertGreater(int(headers["Content-Length"]), 0)


if __name__ == "__main__":
    unittest.main()
