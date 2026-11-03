"""Save Gränges financial history locally; never print or persist the API key."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://apiservice.borsdata.se"
INSTRUMENT = 426


def read_key(path):
    values = []
    for line in path.read_text().splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == "BORSDATA_API_KEY":
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values.append(value)
    if len(values) != 1 or not values[0] or values[0] == "your-key":
        raise ValueError("Set exactly one BORSDATA_API_KEY in .env.local")
    return values[0]


def get_response(endpoint, parameters, key):
    # Redirects could forward the query credential to a different host.
    return requests.get(BASE_URL + endpoint, params={"authKey": key, **parameters},
                        headers={"Accept": "application/json"}, timeout=60,
                        allow_redirects=False)


def contains_secret(value, key):
    if isinstance(value, str):
        return key in value or quote(key, safe="") in value
    if isinstance(value, dict):
        return any(contains_secret(k, key) or contains_secret(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(contains_secret(item, key) for item in value)
    return False


def sanitize(value, key):
    value = str(value).replace(key, "[REDACTED]").replace(quote(key, safe=""), "[REDACTED]")
    return re.sub(r"https?://\S+", "[URL omitted]", value)[:500]


def validate_response(body, key):
    if key.encode() in body or quote(key, safe="").encode() in body:
        raise ValueError("Response unexpectedly contains the credential; not saved")
    data = json.loads(body)
    if not isinstance(data, (dict, list)):
        raise ValueError("Expected JSON object or array")
    if contains_secret(data, key):
        raise ValueError("Decoded response contains the credential; not saved")
    return data


def http_diagnostic(response, key):
    headers = response.headers
    result = {name.lower(): sanitize(headers[name], key) for name in
              ("Content-Type", "Server", "CF-Ray", "CF-Mitigated", "Retry-After")
              if headers.get(name)}
    if response.status_code == 200:
        return result
    raw = response.content[:100_000]
    body = raw.lower()
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        payload = None
    if isinstance(payload, dict):
        safe = {}
        for name in ("message", "error", "errorMessage", "title", "detail", "status", "code"):
            value = payload.get(name)
            if isinstance(value, (str, int)):
                safe[name] = sanitize(value, key)
        if safe:
            result["api_error"] = safe
    if headers.get("CF-Mitigated", "").lower() == "challenge":
        result["response_class"] = "cloudflare_challenge"
    elif b"sorry, you have been blocked" in body:
        result["response_class"] = "cloudflare_block_page"
    elif b"invalid api key" in body or b"invalid apikey" in body:
        result["response_class"] = "invalid_key_message"
    else:
        result["response_class"] = "unclassified_http_error"
    return result


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
