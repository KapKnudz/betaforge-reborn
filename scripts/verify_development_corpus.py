"""Verify saved Börsdata captures and publish an API-only development snapshot.

Keep --output in ignored/private storage. This command makes no network calls.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from betaforge.storage import EvidenceStore
from fetch_borsdata_context import request_plan

ARRAY_FIELDS = {"instruments": "instruments", "report-metadata": "reportMetadatas",
                "kpi-metadata": "kpiHistoryMetadatas", "translations": "translationMetadatas",
                "markets": "markets", "countries": "countries", "sectors": "sectors", "branches": "branches",
                "description": "list", "insider": "list", "shorts": "list", "buyback": "list",
                "report-calendar": "list", "dividend-calendar": "list", "splits": "stockSplitList"}
REQUIRED_NONEMPTY = {"report-metadata", "kpi-metadata", "translations", "markets", "countries", "sectors", "branches"}
DEFINITION_IDS = {"report-metadata": "reportPropery", "kpi-metadata": "kpiId", "translations": "translationKey"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def request_key(name, endpoint, parameters):
    return name, endpoint, json.dumps(parameters, sort_keys=True, separators=(",", ":"))


def source_file(directory, name):
    if not isinstance(name, str) or Path(name).name != name or not name.endswith(".json"):
        raise ValueError("Capture response needs a plain JSON filename")
    path = directory / name
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing or symlinked capture response")
    return path


def provider_error(payload):
    if isinstance(payload, dict):
        return any(value for key, value in payload.items() if key.lower() in {"error", "errors", "errormessage"}) or any(
            provider_error(value) for value in payload.values())
    if isinstance(payload, list):
        return any(provider_error(value) for value in payload)
    return False


def validate_payload(record, payload, instrument):
    name, endpoint = record["dataset"], record["endpoint"]
    if not isinstance(payload, dict) or provider_error(payload):
        raise ValueError("Provider error or invalid response in dataset: " + name)
    field = ARRAY_FIELDS.get(name)
    parts = endpoint.strip("/").split("/")
    if endpoint.endswith("/summary"):
        field = "kpis"
        if payload.get("instrument") != instrument or payload.get("reportType") != parts[-2]:
            raise ValueError("KPI summary identity or basis mismatch")
    elif endpoint.endswith("/history"):
        field = "values"
        if (payload.get("kpiId") != int(parts[4]) or payload.get("reportTime") != parts[5] or
                payload.get("priceValue") != parts[6]):
            raise ValueError("KPI history identity or basis mismatch")
    elif len(parts) == 7 and parts[3] == "kpis" and parts[-2:] == ["last", "latest"]:
        if (payload.get("kpiId") != int(parts[4]) or payload.get("group") != "last" or
                payload.get("calculation") != "latest" or not isinstance(payload.get("value"), dict) or
                payload["value"].get("i") != instrument):
            raise ValueError("Current KPI identity mismatch")
    if field:
        rows = payload.get(field)
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError("Missing or invalid " + field + " array in dataset: " + name)
        if name in REQUIRED_NONEMPTY and not rows:
            raise ValueError("Required definitions or lookup are empty: " + name)
        for row in rows:
            if provider_error(row):
                raise ValueError("Provider error in dataset group: " + name)
            if name in DEFINITION_IDS:
                identifier = row.get(DEFINITION_IDS[name])
                if ((name == "kpi-metadata" and (type(identifier) is not int or identifier < 1)) or
                        (name != "kpi-metadata" and (not isinstance(identifier, str) or not identifier))):
                    raise ValueError("Missing definition identifier in dataset: " + name)
            if field == "list" and "instList" in record["parameters"]:
                if row.get("insId", row.get("instrumentId")) != instrument:
                    raise ValueError("Scoped context instrument mismatch: " + name)


def row_count(payload):
    if isinstance(payload, list):
        return len(payload)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object or array")
    for key in ("values", "stockPricesList", "stockPrices", "instruments", "list", "kpis", "stockSplitList"):
        rows = payload.get(key)
        if isinstance(rows, list):
            if rows and all(isinstance(row, dict) and isinstance(row.get("values"), list) for row in rows):
                return sum(len(row["values"]) for row in rows)
            return len(rows)
    if isinstance(payload.get("value"), dict):
        return int(any(payload["value"].get(key) is not None for key in ("n", "s")))
    arrays = [value for value in payload.values() if isinstance(value, list)]
    return sum(map(len, arrays)) if arrays else None


def date_coverage(rows, start_key, end_key=None):
    starts = [row[start_key][:10] for row in rows if isinstance(row.get(start_key), str)]
    ends = [row[end_key or start_key][:10] for row in rows if isinstance(row.get(end_key or start_key), str)]
    return {"count": len(rows), "first_date": min(starts, default=None), "last_date": max(ends, default=None)}


def capture_time(manifest):
    stamp = manifest.get("retrieved_at") or manifest.get("retrieved_at_utc")
    if not isinstance(stamp, str):
        raise ValueError("Capture needs a timestamp with an explicit timezone")
    try:
        captured_at = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Invalid capture timestamp") from error
    if captured_at.tzinfo is None:
        raise ValueError("Capture timestamp needs an explicit timezone")
    return captured_at.astimezone(timezone.utc)


def verify_capture(directory):
    directory = Path(directory)
    if directory.is_symlink():
        raise ValueError("Symlinked captures are not accepted")
    directory = directory.resolve()
    manifest_path = source_file(directory, "manifest.json")
    manifest = json.loads(manifest_path.read_bytes())
    instrument = manifest.get("instrument_id")
    if type(instrument) is not int or instrument < 1:
        raise ValueError("Capture needs a positive instrument ID")
    capture_time(manifest)
    requests = manifest.get("requests")
    if not isinstance(requests, list):
        raise ValueError("Capture requests are missing")
    expected = Counter(request_key(*item) for item in request_plan(instrument))
    actual = Counter(request_key(row.get("dataset"), row.get("endpoint"), row.get("parameters", {})) for row in requests)
    if expected != actual or any(count != 1 for count in actual.values()):
        raise ValueError("Capture does not contain the exact complete request plan")
    payloads, datasets, files = {}, [], []
    for row in requests:
        if row.get("status") != "saved" or row.get("http_status") != 200:
            raise ValueError("Unsuccessful dataset: " + row["dataset"])
        path = source_file(directory, row.get("file"))
        if digest(path) != row.get("sha256") or path.stat().st_size != row.get("bytes"):
            raise ValueError("Capture response hash or size mismatch")
        payload = json.loads(path.read_bytes())
        validate_payload(row, payload, instrument)
        count = row_count(payload)
        datasets.append({"dataset": row["dataset"], "rows": count, "state": "empty" if count == 0 else "present"})
        payloads[row["dataset"]] = payload
        files.append(row["file"])
    catalogue = payloads["instruments"].get("instruments") if isinstance(payloads["instruments"], dict) else None
    identities = [item for item in catalogue if item.get("insId") == instrument] if isinstance(catalogue, list) else []
    if len(identities) != 1:
        raise ValueError("Selected instrument is missing or duplicated in catalogue")
    reports = payloads["reports"]
    if not isinstance(reports, dict):
        raise ValueError("Reports response must be an object")
    groups = reports.get("reportList", [reports])
    if not isinstance(groups, list) or len(groups) != 1:
        raise ValueError("Single-company capture needs exactly one report group")
    group = groups[0]
    if not isinstance(group, dict) or group.get("instrument") != instrument or provider_error(group):
        raise ValueError("Report group instrument mismatch or provider error")
    series = {}
    for field, family in (("reportsYear", "year"), ("reportsQuarter", "quarter"), ("reportsR12", "r12")):
        rows = group.get(field)
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise ValueError("Missing or invalid report series: " + field)
        selected = [row for row in rows if row.get("period") == 5] if family == "year" else rows
        series[family] = {**date_coverage(selected, "report_Start_Date", "report_End_Date"), "source_rows": len(rows)}
    prices = payloads["prices"]
    if not isinstance(prices, dict):
        raise ValueError("Price response must be an object")
    if prices.get("instrument", instrument) != instrument:
        raise ValueError("Price instrument mismatch")
    price_rows = prices.get("stockPricesList", prices.get("stockPrices"))
    if not isinstance(price_rows, list) or not all(isinstance(row, dict) for row in price_rows):
        raise ValueError("Missing price series")
    if any(row.get("i", row.get("instrumentId", instrument)) != instrument for row in price_rows):
        raise ValueError("Price row instrument mismatch")
    if not series["year"]["count"] or not price_rows:
        raise ValueError("Annual financials and prices must be nonempty")
    return {"instrument_id": instrument, "identity": identities[0], "retrieved_at_utc": manifest.get("retrieved_at_utc"),
            "capture_manifest_sha256": digest(manifest_path), "request_count": len(requests), "reports": series,
            "prices": date_coverage(price_rows, "d"), "datasets": datasets,
            "empty_datasets": [item["dataset"] for item in datasets if item["state"] == "empty"]}, files


def build_corpus(captures, destination):
    captures, destination = [Path(path) for path in captures], Path(destination).resolve()
    if any(path.is_symlink() for path in captures):
        raise ValueError("Symlinked captures are not accepted")
    captures = [path.resolve() for path in captures]
    if not captures:
        raise ValueError("Supply saved acquisition directories")
    if destination.exists():
        raise FileExistsError("Corpus destination already exists")
    if any(destination.is_relative_to(path) or path.is_relative_to(destination) for path in captures):
        raise ValueError("Corpus output must be separate from its capture inputs")
    verified = [(path, *verify_capture(path)) for path in captures]
    # Shared metadata deduplicates by content; store its earliest acquisition first.
    verified.sort(key=lambda item: (capture_time(json.loads((item[0] / "manifest.json").read_bytes())), item[1]["instrument_id"]))
    ids = [coverage["instrument_id"] for _, coverage, _ in verified]
    if len(ids) != len(set(ids)):
        raise ValueError("Supply one capture per distinct instrument")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".corpus-", dir=destination.parent))
    try:
        scratch = temporary / ".store"
        with EvidenceStore(scratch / "evidence.sqlite3") as store:
            for original, coverage, files in verified:
                target = temporary / "captures" / str(coverage["instrument_id"])
                target.mkdir(parents=True)
                for filename in {"manifest.json", *files}:
                    shutil.copyfile(source_file(original, filename), target / filename)
                copied, _ = verify_capture(target)
                if copied != coverage:
                    raise ValueError("Capture changed during publication")
                store.ingest_snapshot(target)
            financial_ids = {row[0] for row in store.connection.execute("SELECT DISTINCT instrument_id FROM observations")}
            if financial_ids != set(ids):
                raise ValueError("Normalized financial coverage differs from selected instruments")
            for instrument in ids:
                annual = store.query_financials(instrument, report_type="year",
                                               fields=["net_Sales", "revenues", "operating_Income", "total_Assets", "total_Equity"],
                                               limit=5000)
                if not any(row["value"] is not None for row in annual):
                    raise ValueError("Selected instrument has no non-null annual financial observations")
            snapshot = store.freeze(temporary / "snapshot")
        shutil.rmtree(scratch)
        with EvidenceStore(snapshot / "evidence.sqlite3", readonly=True) as store:
            if store.connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Frozen database failed integrity check")
            if store.connection.execute("PRAGMA foreign_key_check").fetchone():
                raise ValueError("Frozen database has foreign-key violations")
            counts = store.stats()
        frozen_manifest = json.loads((snapshot / "manifest.json").read_text())
        if digest(snapshot / "evidence.sqlite3") != frozen_manifest["database_sha256"]:
            raise ValueError("Frozen database hash mismatch")
        manifest = {"version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
                    "status": "verified_api_capture", "instrument_ids": ids,
                    "snapshot": "snapshot", "database_sha256": frozen_manifest["database_sha256"], "counts": counts,
                    "companies": [coverage for _, coverage, _ in verified],
                    "limits": ["Original report PDFs are not part of this API-only corpus.",
                               "Provider/report financial reconciliation remains unreviewed.",
                               "Empty optional datasets and actual history coverage are recorded, not filled or inferred."]}
        (temporary / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        temporary.rename(destination)
        return destination / "manifest.json"
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build_corpus(args.captures, args.output))


if __name__ == "__main__":
    main()
