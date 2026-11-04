"""Preview the separate local Company design with one explicitly selected saved view."""
import argparse
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from betaforge.saved_view import load_saved_view
from scripts.serve_progress import ProgressHandler, read_file, read_market_price

ROUTES = {
    "/": ("web/prototypes/company/index.html", "text/html; charset=utf-8"),
    "/style.css": ("web/prototypes/company/style.css", "text/css; charset=utf-8"),
    "/app.js": ("web/prototypes/company/app.js", "text/javascript; charset=utf-8"),
}


class DesignPreviewHandler(ProgressHandler):
    def __init__(self, *args, snapshot, **kwargs):
        self.snapshot = snapshot
        super().__init__(*args, **kwargs)

    def serve(self, head=False):
        host = self.headers.get("Host", "").split(":", 1)[0].lower()
        if host not in ("127.0.0.1", "localhost"):
            self.respond(403, b"Loopback access only.\n", head=head)
            return
        path = urlsplit(self.path).path
        if path == "/data.json":
            self.respond(200, self.snapshot, "application/json; charset=utf-8", head=head)
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


def make_server(analysis, market_db=None, port=8766, root=ROOT):
    run = load_saved_view(analysis)
    try:
        quote = read_market_price(market_db, run["company"]["instrument_id"])
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError):
        raise ValueError("Market evidence store unavailable or unsupported") from None
    snapshot = json.dumps({"run": run, "quote": quote}, ensure_ascii=False).encode()
    return ThreadingHTTPServer(("127.0.0.1", port), partial(
        DesignPreviewHandler, root=root, snapshot=snapshot))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", required=True, type=Path, help="Validated saved-view JSON export")
    parser.add_argument("--market-db", type=Path, help="Existing read-only evidence SQLite store")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    try:
        server = make_server(args.analysis, args.market_db, args.port)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    with server:
        print(f"Company design preview: http://127.0.0.1:{server.server_port}", flush=True)
        print("Read-only snapshot. Restart to refresh. Press Ctrl-C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
