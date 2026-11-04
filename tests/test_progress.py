import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

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

    def configure_view(self):
        file = self.root / "data/saved-view.json"
        file.write_text(json.dumps(self.saved_view()))
        self.stop()
        self.server = progress.make_server(0, root=self.root, analyses=[file])
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return file

    def test_saved_runs_are_opt_in_and_only_expose_configured_exports(self):
        self.assertEqual(json.loads(self.request("/api/runs")[2]), {"runs": []})
        self.assertEqual(self.request("/api/runs/sample-20261101")[0], 404)
        self.configure_view()
        status, _, body = self.request("/api/runs")
        self.assertEqual(status, 200)
        summary = json.loads(body)["runs"][0]
        self.assertEqual(summary["company"]["name"], "Sample")
        self.assertNotIn("narrative", summary)
        self.assertEqual(json.loads(self.request("/api/runs/sample-20261101")[2]), self.saved_view())
        for path in ("/api/runs/../private.json", "/api/runs/%2e%2e%2fprivate.json",
                     "/api/runs/unknown", "/api/runs/sample-20261101/answer.md", "/data/saved-view.json"):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)
        self.assertEqual(self.request("/api/runs/sample-20261101", "HEAD")[2], b"")
        self.assertEqual(self.request("/api/runs", headers={"Host": "remote.example"})[0], 403)

    def test_saved_view_refresh_failures_do_not_leak_paths_or_change_identity(self):
        file = self.configure_view()
        for content in ("{", json.dumps(dict(self.saved_view(), id="changed-id"))):
            file.write_text(content)
            for endpoint in ("/api/runs", "/api/runs/sample-20261101"):
                status, _, body = self.request(endpoint)
                self.assertEqual(status, 503)
                self.assertNotIn(str(file).encode(), body)
        file.unlink()
        self.assertEqual(self.request("/api/runs")[0], 503)
        file.symlink_to(self.root / ".env")
        self.assertEqual(self.request("/api/runs/sample-20261101")[0], 503)

    def test_duplicate_or_invalid_saved_views_fail_before_binding(self):
        file = self.root / "data/saved-view.json"
        file.write_text(json.dumps(self.saved_view()))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            progress.make_server(0, root=self.root, analyses=[file, file])
        file.write_text('{"secret":"not a saved view"}')
        with self.assertRaises(ValueError):
            progress.make_server(0, root=self.root, analyses=[file])

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
