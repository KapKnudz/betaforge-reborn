import hashlib
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from betaforge.saved_view import load_saved_view
from betaforge.storage import EvidenceStore
from scripts import preview_company_design as preview
from scripts import serve_progress as progress
from test_saved_view import minimal_view


class DesignPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        assets = self.root / "web/prototypes/company"
        assets.mkdir(parents=True)
        for name in ("index.html", "style.css", "app.js"):
            (assets / name).write_text("static " + name)
        self.view = minimal_view()
        self.view["price"] = {"id": "obs:price", "value": "123.000000000000000001", "scale": "1",
                              "currency": "SEK", "unit": "currency/share", "basis": "Saved close",
                              "date": "2026-10-30", "source_id": "src:price", "status": "unreviewed"}
        self.analysis = self.root / "saved-view.json"
        self.analysis.write_text(json.dumps(self.view, ensure_ascii=False, indent=3) + "\n")

    def start(self, market_db=None):
        self.server = preview.make_server(self.analysis, market_db, port=0, root=self.root)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()

        def stop():
            self.server.shutdown()
            self.server.server_close()
            thread.join(timeout=2)
        self.addCleanup(stop)

    def request(self, path, method="GET", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_snapshot_preserves_validated_values_and_original_bytes(self):
        original = self.analysis.read_bytes()
        expected = load_saved_view(self.analysis)
        self.start()
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, headers, body = self.request("/data.json")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"run": expected, "quote": None})
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertEqual(self.analysis.read_bytes(), original)
        self.analysis.write_text("invalid after startup")
        self.assertEqual(self.request("/data.json")[2], body)

    def test_validation_precedes_binding(self):
        self.analysis.write_text('{"schema_version": 0}')
        with patch.object(preview, "ThreadingHTTPServer") as server:
            with self.assertRaises(ValueError):
                preview.make_server(self.analysis, port=0)
            server.assert_not_called()

    def test_explicit_routes_and_symlinks_do_not_expose_other_files(self):
        private = self.root / "secret.txt"
        private.write_text("private credential")
        self.start()
        for route, name in (("/", "index.html"), ("/style.css", "style.css"), ("/app.js", "app.js")):
            self.assertEqual(self.request(route)[2], ("static " + name).encode())
        for route in ("/secret.txt", "/saved-view.json", "/api/plan", "/api/runs", "/docs/AGENTS.md",
                      "/../secret.txt", "/%2e%2e/secret.txt", "/web/progress/index.html"):
            with self.subTest(route=route):
                self.assertEqual(self.request(route)[0], 404)
        asset = self.root / "web/prototypes/company/style.css"
        asset.unlink()
        asset.symlink_to(private)
        self.assertEqual(self.request("/style.css")[0], 404)

    def test_loopback_host_head_and_write_rejection(self):
        self.start()
        for host in ("external.example", "127.0.0.1.external.example", ""):
            with self.subTest(host=host):
                self.assertEqual(self.request("/data.json", headers={"Host": host})[0], 403)
        self.assertEqual(self.request("/data.json", headers={"Host": "localhost"})[0], 200)
        status, headers, body = self.request("/data.json", "HEAD")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")
        self.assertEqual(int(headers["Content-Length"]), len(self.request("/data.json")[2]))
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            self.assertEqual(self.request("/data.json", method)[0], 405)

    def test_optional_quote_is_a_read_only_snapshot(self):
        database = self.root / "evidence.sqlite3"
        payload = json.dumps({"instrument": 1, "stockPricesList": [{"d": "2026-11-03", "c": 12.5}]}).encode()
        snapshot = self.root / "quote"
        snapshot.mkdir()
        (snapshot / "quote.json").write_bytes(payload)
        instrument = json.dumps({"instruments": [{"insId": 1, "stockPriceCurrency": "SEK"}]}).encode()
        (snapshot / "instrument.json").write_bytes(instrument)
        (snapshot / "manifest.json").write_text(json.dumps({"retrieved_at": "2026-11-04T17:00:00Z", "requests": [{
            "endpoint": "/v1/instruments", "parameters": {}, "http_status": 200,
            "file": "instrument.json", "sha256": hashlib.sha256(instrument).hexdigest()}, {
            "endpoint": "/v1/instruments/1/stockprices", "parameters": {}, "http_status": 200,
            "file": "quote.json", "sha256": hashlib.sha256(payload).hexdigest()}]}))
        with EvidenceStore(database) as store:
            store.ingest_snapshot(snapshot)
        before = database.read_bytes()
        with patch.object(progress, "EvidenceStore", wraps=EvidenceStore) as store:
            self.start(database)
            store.assert_called_once_with(database, readonly=True)
        quote = json.loads(self.request("/data.json")[2])["quote"]
        self.assertEqual(quote["value"], "12.5")
        self.assertEqual(quote["currency"], "SEK")
        self.assertEqual(quote, progress.read_market_price(database, 1))
        self.assertEqual(database.read_bytes(), before)

    def test_empty_quote_and_invalid_store(self):
        database = self.root / "evidence.sqlite3"
        with EvidenceStore(database):
            pass
        self.start(database)
        self.assertIsNone(json.loads(self.request("/data.json")[2])["quote"])
        for invalid in (self.root / "missing.sqlite3", self.analysis):
            with self.subTest(database=invalid), patch.object(preview, "ThreadingHTTPServer") as server:
                with self.assertRaisesRegex(ValueError, "unavailable or unsupported"):
                    preview.make_server(self.analysis, invalid, port=0)
                server.assert_not_called()
        self.assertFalse((self.root / "missing.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
