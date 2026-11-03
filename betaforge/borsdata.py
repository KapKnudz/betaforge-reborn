"""Börsdata HTTP access with redacted diagnostics and credential-safe captures."""
import json
import re
from urllib.parse import quote

import requests

BASE_URL = "https://apiservice.borsdata.se"


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
