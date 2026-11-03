"""Save Gränges financial history locally; never print or persist the API key."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from betaforge.borsdata import BASE_URL, read_key, get_response, validate_response, http_diagnostic
INSTRUMENT = 426


def fetch():
    key = read_key(ROOT / ".env.local")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = ROOT / "data/borsdata/granges" / stamp
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {"instrument_id": INSTRUMENT, "original_currency": True,
                "retrieved_at_utc": stamp, "api_base": BASE_URL,
                "http_client": "requests " + requests.__version__,
                "documentation": "https://github.com/Borsdata-Sweden/API/wiki/Reports",
                "requests": []}
    failed = False
    for period, count in [("year", 20), ("quarter", 40), ("r12", 40)]:
        endpoint = f"/v1/instruments/{INSTRUMENT}/reports/{period}"
        parameters = {"maxcount": count, "original": 1}
        record = {"endpoint": endpoint, "parameters": parameters, "period": period}
        try:
            with get_response(endpoint, parameters, key) as response:
                record["http_status"] = response.status_code
                record["diagnostic"] = http_diagnostic(response, key)
                if response.status_code != 200:
                    raise ValueError("Expected HTTP 200")
                body = response.content
            data = validate_response(body, key)
            destination = directory / f"{period}.json"
            with destination.open("xb") as file:
                destination.chmod(0o600)
                file.write(body)
            record.update(status="saved", file=destination.name, bytes=len(body),
                          sha256=hashlib.sha256(body).hexdigest())
            if isinstance(data, dict):
                record["response_keys"] = list(data)
                record["array_lengths"] = {k: len(v) for k, v in data.items() if isinstance(v, list)}
            else:
                record["array_length"] = len(data)
        except (requests.RequestException, TimeoutError, OSError, ValueError) as error:
            # Exception messages can contain URLs; retain the class only.
            record.update(status="failed", error=type(error).__name__)
            failed = True
        manifest["requests"].append(record)
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print(json.dumps(record), flush=True)
        if record.get("http_status") in (401, 403, 429):
            break
    print("Snapshot:", directory)
    return 1 if failed else 0


def self_test():
    from unittest.mock import patch
    key = "TEST_SECRET_VALUE"
    assert validate_response(b'{"reports":[]}', key) == {"reports": []}
    for body in [b"<html>error</html>", json.dumps({"echo": key}).encode(),
                 b'{"nested":[{"echo":"\\u0054EST_SECRET_VALUE"}]}', b"null"]:
        try:
            validate_response(body, key)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsafe or invalid response accepted")
    with patch.object(requests, "get") as get:
        get_response("/test", {"original": 1}, key)
        assert get.call_args.kwargs["allow_redirects"] is False
        assert get.call_args.kwargs["params"] == {"authKey": key, "original": 1}
        assert key not in get.call_args.args[0]
    response = requests.Response()
    response.status_code = 403
    response.headers["CF-Ray"] = key
    response._content = json.dumps({"message": "Denied " + key + " https://example.com/?authKey=" + key}).encode()
    diagnostic = json.dumps(http_diagnostic(response, key))
    assert key not in diagnostic and "authKey=" not in diagnostic
    print("Response validation and credential-forwarding checks passed")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        try:
            sys.exit(fetch())
        except (OSError, ValueError) as error:
            print("Setup failed:", type(error).__name__)
            sys.exit(1)
