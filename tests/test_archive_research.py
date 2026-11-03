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
        for directory in backup.RESEARCH_DIRECTORIES:
            source = self.root / directory
            source.mkdir(parents=True, exist_ok=True)
            (source / "evidence.txt").write_text("Preserved evidence\n")
        with backup.EvidenceStore(self.root / "data/evidence/evidence.sqlite3"):
            pass
        self.output = self.root / "data/backups/test.tar.gz"

    def create(self):
        with patch.object(backup, "git_identity", return_value={"head_at_capture": "test", "tracked_changes": False, "untracked_project_files": False}):
            return backup.create_archive(self.root, self.output)

    def test_archive_preserves_bytes_freezes_store_and_excludes_credentials(self):
        (self.root / ".env.local").write_text("not research")
        selected = self.root / backup.RESEARCH_DIRECTORIES[1]
        (selected / ".env.local").write_text("not research")
        (selected / "auth.json").write_text("not research")
        result = self.create()
        self.assertEqual(result["sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        with tarfile.open(self.output, "r:gz") as archive:
            names = archive.getnames()
            self.assertIn("data/evidence/manifest.json", names)
            self.assertIn("data/evidence/evidence.sqlite3", names)
            self.assertNotIn(str(selected.relative_to(self.root) / ".env.local"), names)
            self.assertFalse(any("auth.json" in name for name in names))
            self.assertTrue(all(not name.startswith("/") and ".." not in Path(name).parts for name in names))
            self.assertEqual(archive.extractfile(str(selected.relative_to(self.root) / "evidence.txt")).read(), b"Preserved evidence\n")
            manifest = json.load(archive.extractfile("research-manifest.json"))
            self.assertEqual(len(manifest["files"]), result["files"])
        with self.assertRaises(FileExistsError):
            self.create()

    def test_missing_research_and_symlinks_fail_without_publishing(self):
        source = self.root / backup.RESEARCH_DIRECTORIES[0] / "evidence.txt"
        source.unlink()
        source.symlink_to(self.root / ".env.local")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            self.create()
        self.assertFalse(self.output.exists())
        source.unlink()
        (self.root / backup.RESEARCH_DIRECTORIES[0]).rmdir()
        with self.assertRaisesRegex(ValueError, "missing"):
            self.create()

    def test_changed_source_does_not_publish_archive(self):
        name = backup.RESEARCH_DIRECTORIES[0] + "/evidence.txt"
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


if __name__ == "__main__":
    unittest.main()
