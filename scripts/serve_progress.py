"""Serve the local, read-only research workbench at http://127.0.0.1:8765."""
import argparse
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from betaforge.saved_view import load_saved_view
STATUSES = {"pending", "in_progress", "blocked", "done"}
DOCUMENTS = (
    "AGENTS.md", "CONTRIBUTING.md", "README.md", "docs/architecture.md",
    "work/README.md", "docs/analysis-policy.md", "docs/calculations.md", "docs/company-workflow.md",
    "docs/research/system-readiness-review.md",
    "docs/research/borsdata-retrieval-storage.md", "docs/codex-integration.md", "docs/saved-analysis-view.md", "docs/material-inputs.md",
)
ROUTES = {
    "/": ("web/progress/index.html", "text/html; charset=utf-8"),
    "/style.css": ("web/progress/style.css", "text/css; charset=utf-8"),
    "/app.js": ("web/progress/app.js", "text/javascript; charset=utf-8"),
    **{"/docs/" + name: (name, "text/plain; charset=utf-8") for name in DOCUMENTS},
}


def read_file(root, relative):
    """Read only an explicit project file, refusing symlinks along its path."""
    path = root
    for part in Path(relative).parts:
        if part in ("..", "/"):
            raise ValueError("Invalid project path")
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlinked project files are not served")
    return path.read_bytes()


def validate_plan(plan):
    """Reject incomplete plans rather than display misleading progress."""
    if not isinstance(plan, dict) or type(plan.get("version")) is not int or plan["version"] != 1:
        raise ValueError("Expected plan version 1")
    for name in ("updated_at", "goal", "scope"):
        if not isinstance(plan.get(name), str) or not plan[name]:
            raise ValueError("Missing plan field: " + name)
    for name in ("milestones", "tasks", "references"):
        if not isinstance(plan.get(name), list):
            raise ValueError("Expected plan list: " + name)
    ids = {}
    for kind, fields in (("milestones", ("id", "title", "summary")),
                         ("tasks", ("id", "milestone", "title", "note"))):
        ids[kind] = set()
        for item in plan[kind]:
            if not isinstance(item, dict) or any(not isinstance(item.get(f), str) for f in fields):
                raise ValueError("Incomplete " + kind)
            if not item["id"] or item["id"] in ids[kind] or item.get("status") not in STATUSES:
                raise ValueError("Invalid ID or status in " + kind)
            ids[kind].add(item["id"])
    for task in plan["tasks"]:
        if task["milestone"] not in ids["milestones"]:
            raise ValueError("Unknown task milestone")
        for field in ("acceptance", "evidence"):
            if not isinstance(task.get(field), list) or any(not isinstance(s, str) for s in task[field]):
                raise ValueError("Expected task list: " + field)
        if task.get("blocker") is not None and not isinstance(task["blocker"], str):
            raise ValueError("Invalid blocker")
        for field in ("summary", "purpose"):
            if field in task and not isinstance(task[field], str):
                raise ValueError("Invalid task " + field)
    if "next_task" not in plan:
        raise ValueError("Missing next task")
    if plan["next_task"] is None:
        if any(task["status"] != "done" for task in plan["tasks"]):
            raise ValueError("Unfinished plan needs a next task")
    elif not isinstance(plan["next_task"], str) or plan["next_task"] not in ids["tasks"]:
        raise ValueError("Unknown next task")
    elif any(task["id"] == plan["next_task"] and task["status"] == "done" for task in plan["tasks"]):
        raise ValueError("Next task is already done")
    session = plan.get("session")
    if not isinstance(session, dict) or any(not isinstance(session.get(f), str) for f in ("task", "summary", "next_step")):
        raise ValueError("Missing session handoff")
    if session["task"] not in ids["tasks"]:
        raise ValueError("Unknown session task")
    for reference in plan["references"]:
        if not isinstance(reference, dict) or any(not isinstance(reference.get(f), str) for f in ("label", "path")):
            raise ValueError("Invalid reference")
    return plan


class ProgressHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, root=ROOT, analyses=None, **kwargs):
        self.root = Path(root)
        self.analyses = analyses or {}
        super().__init__(*args, **kwargs)

    def respond(self, status, body, content_type="text/plain; charset=utf-8", head=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def serve(self, head=False):
        # Only loopback Host values are accepted, including for DNS-rebinding requests.
        host = self.headers.get("Host", "").split(":", 1)[0].lower()
        if host not in ("127.0.0.1", "localhost"):
            self.respond(403, b"Loopback access only.\n", head=head)
            return
        path = urlsplit(self.path).path
        if path == "/api/runs" or path.startswith("/api/runs/"):
            selected_id = None if path == "/api/runs" else path[len("/api/runs/"):]
            if selected_id is not None and selected_id not in self.analyses:
                self.respond(404, b'{"error":"Unknown saved analysis."}', "application/json; charset=utf-8", head=head)
                return
            try:
                if selected_id is None:
                    views = []
                    for view_id, file in self.analyses.items():
                        view = load_saved_view(file)
                        if view["id"] != view_id:
                            raise ValueError("Saved analysis identity changed")
                        views.append(view)
                    payload = {"runs": [{key: view[key] for key in ("id", "company", "analysis_date", "reviewed_at", "method")} for view in views]}
                else:
                    payload = load_saved_view(self.analyses[selected_id])
                    if payload["id"] != selected_id:
                        raise ValueError("Saved analysis identity changed")
            except (OSError, ValueError, TypeError, KeyError):
                self.respond(503, b'{"error":"Saved analysis unavailable. Check the configured export."}', "application/json; charset=utf-8", head=head)
                return
            self.respond(200, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8", head=head)
            return
        if path == "/api/plan":
            try:
                plan = validate_plan(json.loads(read_file(self.root, "work/plan.json")))
            except (OSError, ValueError, TypeError, KeyError):
                self.respond(503, b'{"error":"Plan unavailable. Check work/plan.json."}', "application/json; charset=utf-8", head=head)
                return
            self.respond(200, json.dumps(plan, ensure_ascii=False).encode(), "application/json; charset=utf-8", head=head)
            return
        route = ROUTES.get(path)
        if route is None:
            self.respond(404, b"Not found.\n", head=head)
            return
        try:
            body = read_file(self.root, route[0])
        except (OSError, ValueError):
            self.respond(404, b"Not found.\n", head=head)
            return
        self.respond(200, body, route[1], head=head)

    def do_GET(self):
        self.serve()

    def do_HEAD(self):
        self.serve(head=True)

    def do_POST(self):
        self.respond(405, b"Read-only dashboard.\n")

    do_PUT = do_PATCH = do_DELETE = do_POST

    def log_message(self, format, *args):
        return


def make_server(port=8765, root=ROOT, analyses=()):
    configured = {}
    for file in analyses:
        view = load_saved_view(file)
        if view["id"] in configured:
            raise ValueError("Duplicate saved analysis ID")
        configured[view["id"]] = Path(file).absolute()
    return ThreadingHTTPServer(("127.0.0.1", port), partial(ProgressHandler, root=root, analyses=configured))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--analysis", action="append", default=[], type=Path,
                        help="Explicit saved-view JSON export; repeat to show multiple runs")
    args = parser.parse_args()
    with make_server(args.port, analyses=args.analysis) as server:
        print(f"Research workbench: http://127.0.0.1:{server.server_port}", flush=True)
        print("Read-only. Press Ctrl-C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
