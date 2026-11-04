# Company design prototype

Separate local design trial; the working Company page remains at `web/progress/`.

```sh
.venv/bin/python scripts/preview_company_design.py --analysis PATH [--market-db PATH] [--port 8766]
```

Open <http://127.0.0.1:8766>. Select an explicit validated saved-view JSON export and, optionally, an existing quote store. The preview reads both once at startup; restart to refresh. Missing quotes stay unavailable. An unavailable or unsupported configured store stops startup.

The selected report may contain private research. Keep its data local and do not commit it here. The preview binds only to loopback, serves three static assets and the selected snapshot, and performs no provider, model or valuation call.
