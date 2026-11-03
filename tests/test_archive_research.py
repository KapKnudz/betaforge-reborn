import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_research as backup


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.includes = ["data/companies/777/reports", "data/runs/company-b"]
        for directory in self.includes:
            source = self.root / directory
            source.mkdir(parents=True)
            (source / "evidence.txt").write_text("Preserved evidence\n")
        with backup.EvidenceStore(self.root / "data/evidence/evidence.sqlite3"):
            pass
        self.output = self.root / "data/backups/test.tar.gz"

    def create(self, includes=None, output=None, db_path="data/evidence/evidence.sqlite3"):
        with patch.object(backup, "git_identity", return_value={"head_at_capture": "test", "tracked_changes": False, "untracked_project_files": False}):
            return backup.create_archive(self.root, output or self.output,
                                         self.includes if includes is None else includes, db_path)

    def test_explicit_company_paths_preserve_bytes_freeze_store_and_exclude_credentials(self):
        selected = self.root / self.includes[1]
        (selected / ".env.local").write_text("not research")
        (selected / "auth.json").write_text("not research")
        result = self.create()
        self.assertEqual(result["sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        with tarfile.open(self.output, "r:gz") as archive:
            names = archive.getnames()
            self.assertIn("data/evidence/manifest.json", names)
            self.assertIn("data/evidence/evidence.sqlite3", names)
            self.assertFalse(any(".env" in name or "auth.json" in name for name in names))
            self.assertTrue(all(not name.startswith("/") and ".." not in Path(name).parts for name in names))
            self.assertEqual(archive.extractfile(self.includes[1] + "/evidence.txt").read(), b"Preserved evidence\n")
            manifest = json.load(archive.extractfile("research-manifest.json"))
            self.assertEqual(manifest["source_paths"], self.includes)
            self.assertEqual(len(manifest["files"]), result["files"])
        with self.assertRaises(FileExistsError):
            self.create()

    def test_missing_research_and_symlinks_fail_without_publishing(self):
        source = self.root / self.includes[0] / "evidence.txt"
        source.unlink()
        source.symlink_to(self.root / ".env.local")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            self.create()
        self.assertFalse(self.output.exists())
        source.unlink()
        source.parent.rmdir()
        with self.assertRaisesRegex(ValueError, "missing"):
            self.create()

    def test_symlink_in_an_include_parent_is_rejected(self):
        folder = self.root / "data/linked"
        folder.symlink_to(self.root / "data/companies", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            self.create(includes=["data/linked/777/reports"])
        self.assertFalse(self.output.exists())

    def test_changed_source_does_not_publish_archive(self):
        name = self.includes[0] + "/evidence.txt"
        original = tarfile.TarFile.addfile
        def change_after_read(archive, member, body=None):
            original(archive, member, body)
            if member.name == name:
                (self.root / name).write_text("Changed while the archive was reading it\n")
        with patch.object(tarfile.TarFile, "addfile", new=change_after_read):
            with self.assertRaisesRegex(ValueError, "changed"):
                self.create()
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.output.parent.glob(".archive-*")))

    def test_broad_outside_and_configuration_inputs_are_rejected(self):
        for value in (".", "data", "../outside", str(self.root / "data/companies"),
                      ".git", ".env.local", "data/backups", "examples/company-b", "docs", "data/private/auth.json"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.create(includes=[value])
        with self.assertRaisesRegex(ValueError, "explicit research"):
            self.create(includes=[])
        self.assertFalse(self.output.exists())

    def test_output_inside_input_and_direct_live_store_capture_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside its input"):
            self.create(output=self.root / self.includes[0] / "recursive.tar.gz")
        with self.assertRaisesRegex(ValueError, "live store"):
            self.create(includes=["data/evidence"])
        blobs = self.root / "data/evidence/blobs"
        (blobs / "source.json").write_text('{"preserved":"source"}')
        with self.assertRaisesRegex(ValueError, "live store"):
            self.create(includes=["data/evidence/blobs"])
        self.assertFalse(self.output.exists())

    def test_case_data_and_custom_store_work_without_an_issuer_default(self):
        case = self.root / "examples/company-b/data"
        case.mkdir(parents=True)
        (case / "facts.json").write_text('{"instrument_id":777}')
        db = "data/company-b-store/evidence.sqlite3"
        with backup.EvidenceStore(self.root / db):
            pass
        result = self.create(includes=["examples/company-b/data", "examples/company-b/data/facts.json"], db_path=db)
        with tarfile.open(self.output, "r:gz") as archive:
            names = archive.getnames()
            self.assertEqual(names.count("examples/company-b/data/facts.json"), 1)
            self.assertIn("data/company-b-store/evidence.sqlite3", names)
            self.assertNotIn("data/evidence/evidence.sqlite3", names)
            manifest = json.load(archive.extractfile("research-manifest.json"))
            self.assertEqual(manifest["source_database"], db)
        self.assertGreater(result["files"], 1)


if __name__ == "__main__":
    unittest.main()
