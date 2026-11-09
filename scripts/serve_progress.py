"""Serve the local, read-only research workbench at http://127.0.0.1:8765."""
import argparse
from datetime import date, datetime
from decimal import Decimal, DecimalException
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from betaforge.saved_view import checked_path, load_saved_view
from betaforge.storage import EvidenceStore
STATUSES = {"pending", "in_progress", "blocked", "done"}
DOCUMENTS = (
    "AGENTS.md", "CONTRIBUTING.md", "README.md", "DESIGN.md", "docs/architecture.md", "docs/analysis-process.md",
    "work/README.md", "docs/analysis-policy.md", "docs/calculations.md", "docs/company-workflow.md",
    "docs/research/system-readiness-review.md",
    "docs/research/borsdata-retrieval-storage.md", "docs/codex-integration.md", "docs/saved-analysis-view.md", "docs/material-inputs.md", "docs/analysis-workflow.md",
    "docs/skill-drafts/betaforge-market-peer-research/SKILL.md",
    "docs/skill-drafts/betaforge-company-analysis/SKILL.md",
    "docs/skill-drafts/betaforge-financial-report/SKILL.md",
    "docs/skill-drafts/betaforge-valuation-review/SKILL.md",
)
ROUTES = {
    "/": ("web/progress/index.html", "text/html; charset=utf-8"),
    "/style.css": ("web/progress/style.css", "text/css; charset=utf-8"),
    "/app.js": ("web/progress/app.js", "text/javascript; charset=utf-8"),
    "/process.js": ("web/progress/process.js", "text/javascript; charset=utf-8"),
    "/process.css": ("web/progress/process.css", "text/css; charset=utf-8"),
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


def read_market_price(database, instrument_id):
    """Expose only a valid stored daily close, preserving its source units."""
    if database is None:
        return None
    with EvidenceStore(database, readonly=True) as store:
        records = store.query_financials(instrument_id, report_type="price", fields=["price_close"], limit=1)
    if not records:
        return None
    row = records[0]
    try:
        if (row.get("provider") != "borsdata" or row.get("instrument_id") != instrument_id or
                row.get("report_type") != "price" or row.get("metric") != "price_close" or
                row.get("unit") != "currency/share" or row.get("currency_mode") != "quote" or
                not isinstance(row.get("value"), str) or not isinstance(row.get("scale"), str) or
                not re.fullmatch(r"[A-Z]{3}", row.get("currency") or "") or
                not re.fullmatch(r"src_[0-9a-f]{24}", row.get("source_id") or "")):
            return None
        value, scale = Decimal(row["value"]), Decimal(row["scale"])
        amount = value * scale
        if any(not number.is_finite() or number <= 0 for number in (value, scale, amount)):
            return None
        day = row["period_end"]
        if date.fromisoformat(day).isoformat() != day:
            return None
        retrieved = row.get("source_first_captured_at") or row["observed_at"]
        checked = row.get("source_last_successful_check_at") or row["observed_at"]
        for stamp in (retrieved, checked):
            if not isinstance(stamp, str) or datetime.fromisoformat(stamp.replace("Z", "+00:00")).tzinfo is None:
                return None
        return {"instrument_id": instrument_id, "value": row["value"], "scale": row["scale"],
                "unit": row["unit"], "currency": row["currency"], "date": day,
                "source_id": row["source_id"], "provider": "Börsdata", "kind": "daily_close",
                "retrieved_at": retrieved, "checked_at": checked}
    except (ValueError, TypeError, KeyError, DecimalException):
        return None


def load_corpus_catalogue(path):
    """Read display identities only; frozen evidence stays unopened."""
    def unique_fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate corpus manifest field")
            result[key] = value
        return result

    path = checked_path(path)
    if not path.is_file():
        raise ValueError("Corpus manifest is missing")
    with path.open("rb") as stream:
        body = stream.read(16 * 1024 * 1024 + 1)
    if len(body) > 16 * 1024 * 1024:
        raise ValueError("Corpus manifest exceeds 16 MiB")
    manifest = json.loads(body, object_pairs_hook=unique_fields)
    if (not isinstance(manifest, dict) or type(manifest.get("version")) is not int or
            manifest["version"] != 1 or manifest.get("status") != "verified_api_capture"):
        raise ValueError("Expected verified API corpus manifest version 1")
    ids, companies = manifest.get("instrument_ids"), manifest.get("companies")
    if (not isinstance(ids, list) or any(type(i) is not int or i <= 0 for i in ids) or
            len(set(ids)) != len(ids) or not isinstance(companies, list)):
        raise ValueError("Invalid or duplicate corpus instrument IDs")
    catalogue, seen = [], set()
    for company in companies:
        if not isinstance(company, dict):
            raise ValueError("Invalid corpus company")
        instrument, identity = company.get("instrument_id"), company.get("identity")
        if type(instrument) is not int or instrument <= 0 or instrument in seen:
            raise ValueError("Invalid or duplicate corpus company ID")
        if not isinstance(identity, dict):
            raise ValueError("Missing corpus company identity")
        name, ticker = identity.get("name"), identity.get("ticker")
        if ticker is None:
            ticker = ""
        for field, value, maximum in (("name", name, 250), ("ticker", ticker, 100)):
            if (not isinstance(value, str) or len(value) > maximum or
                    (not value.strip() and (field == "name" or value != "")) or
                    any(not char.isprintable() or char in "<>" for char in value)):
                raise ValueError("Invalid corpus company " + field)
        captured = company.get("retrieved_at_utc")
        if (not isinstance(captured, str) or not re.fullmatch(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)", captured)):
            raise ValueError("Invalid corpus capture timestamp")
        try:
            stamp = datetime.fromisoformat(captured.replace("Z", "+00:00"))
            if stamp.utcoffset() is None:
                raise ValueError("Capture timestamp needs timezone")
        except ValueError:
            raise ValueError("Invalid corpus capture timestamp") from None
        seen.add(instrument)
        catalogue.append({"instrument_id": instrument, "name": name,
                          "ticker": ticker, "captured_at": captured})
    if seen != set(ids):
        raise ValueError("Corpus company IDs differ from instrument IDs")
    return catalogue


class ProgressHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, root=ROOT, analyses=None, market_db=None, instruments=(), companies=(), **kwargs):
        self.root = Path(root)
        self.analyses = analyses or {}
        self.market_db = market_db
        self.instruments = instruments
        self.companies = companies
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
        if path.startswith("/api/market-price/"):
            selected = path[len("/api/market-price/"):]
            if selected not in self.instruments:
                self.respond(404, b'{"error":"Unknown saved company."}', "application/json; charset=utf-8", head=head)
                return
            try:
                payload = {"quote": read_market_price(self.market_db, int(selected))}
            except (OSError, sqlite3.Error, ValueError, TypeError, KeyError):
                self.respond(503, b'{"error":"Market price unavailable. Check the configured evidence store."}', "application/json; charset=utf-8", head=head)
                return
            self.respond(200, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8", head=head)
            return
        if path == "/api/runs" or path.startswith("/api/runs/"):
            selected_id = None if path == "/api/runs" else path[len("/api/runs/"):]
            if selected_id is not None and selected_id not in self.analyses:
                self.respond(404, b'{"error":"Unknown saved analysis."}', "application/json; charset=utf-8", head=head)
                return
            if selected_id is None:
                payload = {"runs": [{**{key: view[key] for key in ("id", "company", "analysis_date", "reviewed_at", "method")},
                                     "analysis_kind": "structured" if "analysis" in view else "legacy"}
                                    for view in self.analyses.values()],
                           "companies": self.companies}
            else:
                payload = self.analyses[selected_id]
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


def make_server(port=8765, root=ROOT, analyses=(), market_db=None, corpus=None):
    companies = load_corpus_catalogue(corpus) if corpus is not None else []
    configured = {}
    instruments = set()
    for file in analyses:
        view = load_saved_view(file)
        if view["id"] in configured:
            raise ValueError("Duplicate saved analysis ID")
        # Keep the validated export in memory; adopting a revised artifact requires a restart.
        configured[view["id"]] = view
        instruments.add(str(view["company"]["instrument_id"]))
    if market_db is not None:
        market_db = Path(market_db).absolute()
        try:
            # Opening through EvidenceStore checks its version without creating or migrating it.
            read_market_price(market_db, 0)
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError):
            raise ValueError("Market evidence store unavailable or unsupported") from None
    return ThreadingHTTPServer(("127.0.0.1", port), partial(
        ProgressHandler, root=root, analyses=configured, market_db=market_db, instruments=instruments,
        companies=companies))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--analysis", action="append", default=[], type=Path,
                        help="Explicit saved-view JSON export; repeat for multiple runs, restart to adopt changes")
    parser.add_argument("--market-db", type=Path,
                        help="Existing evidence SQLite store for latest stored daily closes")
    parser.add_argument("--corpus", type=Path,
                        help="Explicit frozen corpus manifest for company browsing; restart to adopt changes")
    args = parser.parse_args()
    with make_server(args.port, analyses=args.analysis, market_db=args.market_db, corpus=args.corpus) as server:
        print(f"Research workbench: http://127.0.0.1:{server.server_port}", flush=True)
        print("Read-only. Press Ctrl-C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
