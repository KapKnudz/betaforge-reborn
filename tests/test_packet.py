import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_codex_packet as packet


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reports = self.root / "reports"
        (self.reports / "sources").mkdir(parents=True)
        (self.reports / "prepared").mkdir()
        pdf = self.reports / "sources/granges-test.pdf"
        pdf.write_bytes(b"%PDF-test-evidence")
        pages = self.reports / "prepared/granges-test.json"
        pages.write_text('[{"page":1,"text":"Revenue 10"}]')
        self.index = {"reports": [{"report_id": "granges-test", "pages": 1,
                                  "source_sha256": packet.digest(pdf), "prepared_sha256": packet.digest(pages)}]}
        (self.reports / "prepared/index.json").write_text(json.dumps(self.index))
        (self.reports / "source-manifest.json").write_text('{"documents":[]}')
        (self.root / "docs/research").mkdir(parents=True)
        (self.root / "docs/research/granges-mapping-resolution.md").write_text("Test mapping")
        (self.root / "data/granges-walkthrough").mkdir(parents=True)
        (self.root / "data/granges-walkthrough/codex-questions.md").write_text("Test prompt")
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

    def build(self):
        with patch.object(packet, "ROOT", self.root):
            return packet.prepare([self.input], self.root / "published", self.root / "store/evidence.sqlite3", self.facts, self.reports)

    def test_packet_preserves_independent_corpus_and_current_price(self):
        result = self.build()
        data = json.loads(result.read_text())
        self.assertIn('"metric": "price_close"', data["context"])
        copied = result.parent / "reports/sources/granges-test.pdf"
        original = self.reports / "sources/granges-test.pdf"
        self.assertEqual(packet.digest(copied), packet.digest(original))
        original.write_bytes(b"changed later")
        self.assertEqual(packet.digest(copied), self.index["reports"][0]["source_sha256"])
        with self.assertRaises(FileExistsError):
            self.build()

    def test_corrupt_report_does_not_publish_partial_packet(self):
        (self.reports / "sources/granges-test.pdf").write_bytes(b"not the frozen report")
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse((self.root / "published").exists())
        self.assertFalse(list(self.root.glob('.prepare-*')))


if __name__ == "__main__":
    unittest.main()
