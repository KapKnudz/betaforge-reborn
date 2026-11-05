from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_reports


class ReportPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "sources").mkdir()
        self.documents = [self.report("issuer-annual", ["Header 2025", "Revenue 10  20", None]),
                          self.report("issuer-interim", ["Current report 2026"])]
        self.save_manifest()

    def report(self, rid, lines, encryption=None):
        writer = PdfWriter()
        for line in lines:
            page = writer.add_blank_page(width=300, height=300)
            if line is not None:
                font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                                         NameObject("/Subtype"): NameObject("/Type1"),
                                         NameObject("/BaseFont"): NameObject("/Helvetica")})
                page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
                stream = DecodedStreamObject()
                stream.set_data(f"BT /F1 12 Tf 10 250 Td ({line}) Tj ET".encode())
                page[NameObject("/Contents")] = writer._add_object(stream)
        if encryption:
            writer.encrypt("", owner_password="fixture-owner", algorithm=encryption)
        path = self.root / "sources" / (rid + ".pdf")
        writer.write(path)
        return {"report_id": rid, "local_path": f"sources/{rid}.pdf", "page_count": len(lines),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "publication_date": "2026-10-30",
                "source_url": "https://issuer.example/report.pdf"}

    def save_manifest(self, documents=None):
        (self.root / "source-manifest.json").write_text(json.dumps({"documents": self.documents if documents is None else documents}))

    def assert_unpublished(self):
        self.assertFalse((self.root / "prepared").exists())
        self.assertFalse(list(self.root.glob(".prepare-reports-*")))

    def test_native_text_hashes_page_order_and_limits_preserve_originals(self):
        originals = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        result = prepare_reports.prepare(self.root)
        summary = json.loads(result.read_text())
        self.assertEqual(summary["total_pages"], 4)
        self.assertIn("not proof of semantic fidelity", summary["limits"])
        for report in summary["reports"]:
            path = result.parent / (report["report_id"] + ".json")
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), report["prepared_sha256"])
            self.assertEqual(report["source_sha256"], next(d["sha256"] for d in self.documents if d["report_id"] == report["report_id"]))
        pages = json.loads((result.parent / "issuer-annual.json").read_text())
        self.assertEqual(pages, [{"page": 1, "text": "Header 2025"},
                                 {"page": 2, "text": "Revenue 10  20"}, {"page": 3, "text": ""}])
        self.assertEqual(summary["reports"][0]["low_text_pages"], [1, 2, 3])
        corpus = (result.parent / "corpus.txt").read_bytes()
        self.assertEqual(hashlib.sha256(corpus).hexdigest(), summary["corpus_sha256"])
        self.assertIn(b"=== issuer-annual | PDF PAGE 3 ===\n\n=== END PAGE ===", corpus)
        for path, body in originals.items():
            self.assertEqual(path.read_bytes(), body)
        prepared = result.read_bytes()
        with self.assertRaises(FileExistsError):
            prepare_reports.prepare(self.root)
        self.assertEqual(result.read_bytes(), prepared)

    def test_line_cleanup_preserves_headers_numbers_and_order(self):
        self.assertEqual(prepare_reports.clean("Header  \n\n\nRevenue  10 20 \nNote 1\n"),
                         "Header\n\nRevenue  10 20\nNote 1")

    def test_empty_password_aes_pdf_extracts_text_without_changing_original(self):
        self.documents[0] = self.report("issuer-annual", ["Encrypted annual revenue 123"], encryption="AES-256")
        self.save_manifest()
        source = self.root / self.documents[0]["local_path"]
        original = source.read_bytes()
        self.assertTrue(PdfReader(source).is_encrypted)
        result = prepare_reports.prepare(self.root)
        pages = json.loads((result.parent / "issuer-annual.json").read_text())
        self.assertEqual(pages, [{"page": 1, "text": "Encrypted annual revenue 123"}])
        self.assertEqual(source.read_bytes(), original)
        summary = json.loads(result.read_text())
        self.assertEqual(summary["reports"][0]["source_sha256"], hashlib.sha256(original).hexdigest())

    def test_reporting_period_dates_validate_calendar_and_order_without_filling_gaps(self):
        for period in ({"start": "2026-01-01", "end": "2026-09-31"},
                       {"start": "2026-10-01", "end": "2026-09-30"},
                       {"start": "20260101", "end": None}):
            documents = deepcopy(self.documents)
            documents[0]["reporting_period"] = period
            self.save_manifest(documents)
            with self.subTest(period=period), self.assertRaises(ValueError):
                prepare_reports.prepare(self.root)
            self.assert_unpublished()
        self.documents[0]["reporting_period"] = {"start": None, "end": "2026-09-30"}
        self.documents[1]["reporting_period"] = {"start": None, "end": None}
        self.save_manifest()
        manifest = (self.root / "source-manifest.json").read_bytes()
        prepare_reports.prepare(self.root)
        self.assertEqual((self.root / "source-manifest.json").read_bytes(), manifest)

    def test_supplied_reporting_period_requires_canonical_shape(self):
        for period in (None, {}, {"start": None}, {"end": None},
                       {"start": None, "end": None, "quarter": 3}, [], "2026"):
            documents = deepcopy(self.documents)
            documents[0]["reporting_period"] = period
            self.save_manifest(documents)
            with self.subTest(period=period), self.assertRaisesRegex(ValueError, "exactly start and end"):
                prepare_reports.prepare(self.root)
            self.assert_unpublished()
        self.save_manifest()
        manifest = (self.root / "source-manifest.json").read_bytes()
        prepare_reports.prepare(self.root)
        self.assertEqual((self.root / "source-manifest.json").read_bytes(), manifest)

    def test_bad_manifest_fields_and_duplicates_fail_without_partial_output(self):
        invalid = [("report_id", "../escape"), ("local_path", "../report.pdf"),
                   ("local_path", "/tmp/report.pdf"), ("local_path", "sources\\issuer-annual.pdf"),
                   ("local_path", "sources/other.pdf"), ("local_path", "sources/issuer-annual.txt"),
                   ("sha256", "not-a-hash"), ("page_count", True), ("page_count", 0),
                   ("publication_date", "2026-02-30"), ("publication_date", "20261030")]
        for field, value in invalid:
            documents = deepcopy(self.documents)
            documents[0][field] = value
            with self.subTest(field=field, value=value):
                self.save_manifest(documents)
                with self.assertRaises(ValueError):
                    prepare_reports.prepare(self.root)
                self.assert_unpublished()
        for documents in ([], self.documents + [self.documents[0]], [None]):
            self.save_manifest(documents)
            with self.assertRaises(ValueError):
                prepare_reports.prepare(self.root)
            self.assert_unpublished()

    def test_hash_page_count_and_extraction_failure_roll_back_prior_reports(self):
        for field, value in (("sha256", "0" * 64), ("page_count", 2)):
            documents = deepcopy(self.documents)
            documents[1][field] = value
            self.save_manifest(documents)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "mismatch"):
                prepare_reports.prepare(self.root)
            self.assert_unpublished()
        self.save_manifest()
        with patch.object(prepare_reports, "clean", side_effect=RuntimeError("extraction failed")):
            with self.assertRaisesRegex(RuntimeError, "extraction failed"):
                prepare_reports.prepare(self.root)
        self.assert_unpublished()

    def test_symlink_sources_and_manifest_are_rejected(self):
        path = self.root / self.documents[0]["local_path"]
        real = self.root / "original.pdf"
        path.rename(real)
        path.symlink_to(real)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            prepare_reports.prepare(self.root)
        self.assert_unpublished()
        path.unlink()
        real.rename(path)
        manifest = self.root / "source-manifest.json"
        real_manifest = self.root / "original-manifest.json"
        manifest.rename(real_manifest)
        manifest.symlink_to(real_manifest)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            prepare_reports.prepare(self.root)
        self.assert_unpublished()

    def test_cli_accepts_explicit_corpus_from_another_directory(self):
        script = Path(prepare_reports.__file__).resolve()
        result = subprocess.run([sys.executable, str(script), "--reports", str(self.root)],
                                cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "prepared/index.json").is_file())


if __name__ == "__main__":
    unittest.main()
