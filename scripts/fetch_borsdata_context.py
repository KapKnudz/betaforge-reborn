"""Acquire the agreed company datasets; retain raw responses and safe provenance."""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import sys
import time

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from betaforge.borsdata import BASE_URL, read_key, get_response, validate_response, http_diagnostic


def retry_delay(header):
    try:
        return max(1, int(header))
    except (TypeError, ValueError):
        try:
            date = parsedate_to_datetime(header)
            return max(1, int((date - datetime.now(timezone.utc)).total_seconds()) + 1)
        except (TypeError, ValueError, OverflowError):
            return 2


def request_plan(instrument):
    if not isinstance(instrument, int) or isinstance(instrument, bool) or instrument < 1:
        raise ValueError("Instrument must be a positive integer")
    prefix = f"/v1/instruments/{instrument}"
    selected = {"instList": str(instrument)}
    plan = [("instruments", "/v1/instruments", {}),
            ("description", "/v1/instruments/description", selected),
            ("prices", prefix + "/stockprices", {"maxCount": 20}),
            ("splits", "/v1/instruments/StockSplits", {"from": "2006-01-01"}),
            ("reports", prefix + "/reports", {"maxYearCount": 20, "maxR12QCount": 40, "original": 1}),
            ("report-metadata", "/v1/instruments/reports/metadata", {}),
            ("kpi-metadata", "/v1/instruments/kpis/metadata", {}),
            ("translations", "/v1/translationmetadata", {}),
            ("insider", "/v1/holdings/insider", selected),
            ("shorts", "/v1/holdings/shorts", {}),
            ("buyback", "/v1/holdings/buyback", selected),
            ("report-calendar", "/v1/instruments/report/calendar", selected),
            ("dividend-calendar", "/v1/instruments/dividend/calendar", selected)]
    for name in ("markets", "countries", "sectors", "branches"):
        plan.append((name, f"/v1/{name}", {}))
    for report_type, count in (("year", 20), ("r12", 40), ("quarter", 40)):
        plan.append((f"summary-{report_type}", prefix + f"/kpis/{report_type}/summary", {"maxCount": count}))
    # Supported combinations: official KPI-History table, saved in the research references.
    for kpi in (2, 3, 4, 10, 11, 15, 49, 50, 76):
        for basis, count in (("year", 20), ("r12", 40)):
            for price in ("mean", "low", "high"):
                plan.append((f"kpi-{kpi}-{basis}-{price}", prefix + f"/kpis/{kpi}/{basis}/{price}/history", {"maxCount": count}))
    for kpi in (37, 42, 61, 62, 63, 64):
        for basis, count in (("year", 20), ("r12", 40)):
            plan.append((f"kpi-{kpi}-{basis}-mean", prefix + f"/kpis/{kpi}/{basis}/mean/history", {"maxCount": count}))
    return plan


def acquire(directory, instrument, key, plan=None, pause=time.sleep):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {"instrument_id": instrument, "api_base": BASE_URL,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "http_client": "requests " + requests.__version__, "requests": []}
    for name, endpoint, parameters in plan or request_plan(instrument):
        record = {"endpoint": endpoint, "parameters": parameters, "dataset": name,
                  "retrieved_at_utc": datetime.now(timezone.utc).isoformat()}
        for attempt in range(3):
            record["attempts"] = attempt + 1
            try:
                with get_response(endpoint, parameters, key) as response:
                    record["http_status"] = response.status_code
                    record["diagnostic"] = http_diagnostic(response, key)
                    if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                        delay = retry_delay(response.headers.get("Retry-After", "2"))
                        if delay > 60:
                            # Preserve the provider's wait instead of retrying early or blocking the caller.
                            record.update(status="failed", retry_deferred=True, retry_after_seconds=delay)
                            break
                        pause(delay)
                        continue
                    if response.status_code != 200:
                        raise ValueError("Non-200 response")
                    body = response.content
                    data = validate_response(body, key)
                    target = directory / (name + ".json")
                    with target.open("xb") as file:
                        target.chmod(0o600)
                        file.write(body)
                    record.update(status="saved", file=target.name, bytes=len(body),
                                  sha256=hashlib.sha256(body).hexdigest())
                    if isinstance(data, dict):
                        record["response_keys"] = list(data)
                        record["array_lengths"] = {k: len(v) for k, v in data.items() if isinstance(v, list)}
                    else:
                        record["array_length"] = len(data)
                break
            except (requests.RequestException, OSError, ValueError) as error:
                # Exception messages can include the authenticated request URL.
                record.update(status="failed", error=type(error).__name__)
                break
        manifest["requests"].append(record)
        temporary = directory / "manifest.tmp"
        temporary.write_text(json.dumps(manifest, indent=2))
        temporary.replace(directory / "manifest.json")
        print(json.dumps(record), flush=True)
        if record.get("http_status") in (401, 403, 429) or record.get("retry_deferred"):
            break
        pause(0.2)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instrument", type=int, required=True)
    args = parser.parse_args()
    request_plan(args.instrument)
    key = read_key(ROOT / ".env.local")
    directory = ROOT / "data/borsdata/context" / str(args.instrument) / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = acquire(directory, args.instrument, key)
    print("Snapshot:", directory)
    return 0 if all(r.get("status") == "saved" for r in manifest["requests"]) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        print("Setup failed:", type(error).__name__)
        sys.exit(1)
