"""SQLite observations backed by immutable, hashed source files.

Amounts remain decimal strings in original units. This module never sums periods
or silently resolves disagreements between provider and issuer observations.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile

SCHEMA_VERSION = 1
REPORT_META = {"year", "period", "report_Start_Date", "report_End_Date", "report_Date",
               "broken_Fiscal_Year", "currency", "currency_Ratio"}
STOCKS = {"intangible_Assets", "tangible_Assets", "financial_Assets", "non_Current_Assets",
          "cash_And_Equivalents", "current_Assets", "total_Assets", "total_Equity",
          "non_Current_Liabilities", "current_Liabilities", "total_Liabilities_And_Equity", "net_Debt"}
FLOWS = {"revenues", "net_Sales", "gross_Income", "operating_Income", "profit_Before_Tax",
         "profit_To_Equity_Holders", "cash_Flow_From_Operating_Activities",
         "cash_Flow_From_Investing_Activities", "cash_Flow_From_Financing_Activities",
         "cash_Flow_For_The_Year", "free_Cash_Flow"}
PRICE_FIELDS = {"stock_Price_Average", "stock_Price_High", "stock_Price_Low"}
# Confirmed in the provider's KPI History table, referenced by the storage spec.
VALUATION_MULTIPLES = {2, 3, 4, 10, 11, 15, 76}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      default=lambda v: str(v) if isinstance(v, Decimal) else str(v))


def _hash(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _load(body):
    return json.loads(body, parse_float=Decimal,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON number")))


def _safe(value):
    """Reject credential-bearing artifacts instead of attempting secret discovery."""
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower().replace("_", "") in {"authkey", "apikey", "authorization"}:
                raise ValueError("Credential-bearing evidence is forbidden")
            _safe(item)
    elif isinstance(value, list):
        for item in value:
            _safe(item)
    elif isinstance(value, str) and re.search(r"[?&](authkey|api_key)=", value, re.I):
        raise ValueError("Credential-bearing URL is forbidden")


def _number(value):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("Boolean is not a financial amount")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal amount") from exc
    if not number.is_finite():
        raise ValueError("Nonfinite amount")
    return str(number)


def _day(value, required=False):
    if value is None:
        if required:
            raise ValueError("Missing period date")
        return None
    if not isinstance(value, str):
        raise ValueError("Invalid date")
    return date.fromisoformat(value[:10]).isoformat()


def _timestamp(value):
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("Acquisition timestamp needs an explicit timezone")
    return timestamp.astimezone(timezone.utc).isoformat()


def _row_get(row, *names, default=None):
    lowered = {key.lower(): value for key, value in row.items()}
    for key in names:
        if key.lower() in lowered:
            return lowered[key.lower()]
    return default


class EvidenceStore:
    def __init__(self, db_path, blob_dir=None, readonly=False):
        self.db_path = Path(db_path).resolve()
        self.blob_dir = Path(blob_dir).resolve() if blob_dir else self.db_path.parent / "blobs"
        self.readonly = readonly
        if readonly:
            self.connection = sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True)
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(self.db_path)
        try:
            self.connection.row_factory = sqlite3.Row
            version = self.connection.execute("PRAGMA user_version").fetchone()[0]
            has_schema = self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name NOT GLOB 'sqlite_*' LIMIT 1"
            ).fetchone()
            if version != SCHEMA_VERSION and (readonly or version != 0 or has_schema):
                raise ValueError("Unsupported storage schema")
            self.connection.execute("PRAGMA foreign_keys=ON")
            if not readonly:
                self.blob_dir.mkdir(parents=True, exist_ok=True)
                self.connection.executescript("""
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY, provider TEXT NOT NULL, endpoint TEXT NOT NULL,
                    parameters TEXT NOT NULL, sha256 TEXT NOT NULL, blob_path TEXT NOT NULL,
                    observed_at TEXT NOT NULL, metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS acquisitions (
                    id TEXT PRIMARY KEY, source_id TEXT REFERENCES sources(id), endpoint TEXT NOT NULL,
                    observed_at TEXT NOT NULL, status TEXT NOT NULL, details TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY, logical_key TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES sources(id),
                    instrument_id INTEGER NOT NULL, report_type TEXT NOT NULL, metric TEXT NOT NULL,
                    year INTEGER, period INTEGER, period_start TEXT, period_end TEXT,
                    observed_at TEXT NOT NULL, record TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS observations_lookup ON observations(instrument_id,report_type,metric);
                CREATE INDEX IF NOT EXISTS observations_ordered_lookup ON observations(instrument_id,report_type,metric,year DESC,period DESC,period_end DESC,id);
                CREATE TABLE IF NOT EXISTS current_observations (
                    logical_key TEXT PRIMARY KEY, observation_id TEXT NOT NULL REFERENCES observations(id),
                    observed_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS observation_sources (
                    observation_id TEXT REFERENCES observations(id), source_id TEXT REFERENCES sources(id),
                    pointer TEXT NOT NULL, PRIMARY KEY(observation_id,source_id,pointer));
                CREATE TABLE IF NOT EXISTS revisions (
                    id INTEGER PRIMARY KEY, logical_key TEXT NOT NULL, previous_id TEXT,
                    observation_id TEXT NOT NULL, source_id TEXT NOT NULL, observed_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS datasets (
                    id TEXT PRIMARY KEY, dataset TEXT NOT NULL, instrument_id INTEGER,
                    source_id TEXT NOT NULL REFERENCES sources(id), pointer TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS instrument_versions (
                    id TEXT PRIMARY KEY, instrument_id INTEGER NOT NULL, source_id TEXT NOT NULL REFERENCES sources(id),
                    observed_at TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS datasets_lookup ON datasets(dataset,source_id);
                CREATE INDEX IF NOT EXISTS instrument_versions_lookup ON instrument_versions(instrument_id,observed_at DESC,id DESC);
                CREATE INDEX IF NOT EXISTS acquisitions_source_check ON acquisitions(source_id,status,observed_at);
                PRAGMA user_version=1;
                """)
                self.connection.commit()
        except BaseException:
            self.connection.close()
            raise

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _write_blob(self, body):
        digest = _hash(body)
        path = self.blob_dir / (digest + ".json")
        if path.exists():
            if _hash(path.read_bytes()) != digest:
                raise ValueError("Stored source hash mismatch")
        else:
            # Exclusive create prevents an existing immutable source being replaced.
            with path.open("xb") as file:
                path.chmod(0o600)
                file.write(body)
        return digest, path.name

    def _source(self, provider, endpoint, parameters, body, observed_at, metadata):
        digest, filename = self._write_blob(body)
        source_id = "src_" + _hash(_json([provider, endpoint, parameters, digest]))[:24]
        self.connection.execute("INSERT OR IGNORE INTO sources VALUES (?,?,?,?,?,?,?,?)",
                                (source_id, provider, endpoint, _json(parameters), digest, filename,
                                 observed_at, _json(metadata)))
        return source_id

    def _currency(self, instrument_id):
        row = self.connection.execute("SELECT payload FROM instrument_versions WHERE instrument_id=? ORDER BY observed_at DESC,id DESC LIMIT 1", (instrument_id,)).fetchone()
        return _row_get(json.loads(row[0]), "stockPriceCurrency") if row else None

    def _observation(self, record, source_id, pointer, observed_at):
        record = dict(record)
        record.update(source_id=source_id, pointer=pointer, observed_at=observed_at)
        identity = {key: record.get(key) for key in (
            "provider", "instrument_id", "report_type", "metric", "period_start", "period_end",
            "year", "period", "currency_mode", "price_type", "calc_group", "calc", "basis")}
        logical_key = _hash(_json(identity))
        # Source serialization changes do not create a new financial revision.
        content = {k: v for k, v in record.items() if k not in {"source_id", "pointer", "observed_at"}}
        observation_id = "obs_" + _hash(_json([logical_key, content]))[:24]
        record["id"] = observation_id
        previous = self.connection.execute("SELECT observation_id,observed_at FROM current_observations WHERE logical_key=?", (logical_key,)).fetchone()
        self.connection.execute("INSERT OR IGNORE INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                (observation_id, logical_key, source_id, record["instrument_id"],
                                 record["report_type"], record["metric"], record.get("year"), record.get("period"),
                                 record.get("period_start"), record.get("period_end"), observed_at, _json(record)))
        self.connection.execute("INSERT OR IGNORE INTO observation_sources VALUES (?,?,?)", (observation_id, source_id, pointer))
        if previous is None or observed_at >= previous["observed_at"]:
            self.connection.execute("INSERT INTO current_observations VALUES (?,?,?) ON CONFLICT(logical_key) DO UPDATE SET observation_id=excluded.observation_id, observed_at=excluded.observed_at", (logical_key, observation_id, observed_at))
            if previous is None or previous[0] != observation_id:
                self.connection.execute("INSERT INTO revisions(logical_key,previous_id,observation_id,source_id,observed_at) VALUES (?,?,?,?,?)", (logical_key, previous[0] if previous else None, observation_id, source_id, observed_at))
        return observation_id

    def _dataset(self, dataset, instrument_id, payload, source_id, pointer):
        identifier = "row_" + _hash(_json([dataset, instrument_id, source_id, pointer, payload]))[:24]
        self.connection.execute("INSERT OR IGNORE INTO datasets VALUES (?,?,?,?,?,?)", (identifier, dataset, instrument_id, source_id, pointer, _json(payload)))
        return identifier

    def ingest_snapshot(self, directory):
        """Validate an entire manifest before committing any normalized observations."""
        if self.readonly:
            raise ValueError("Read-only store")
        directory = Path(directory).resolve()
        manifest_body = (directory / "manifest.json").read_bytes()
        manifest = _load(manifest_body)
        _safe(manifest)
        stamp = manifest.get("retrieved_at") or manifest.get("retrieved_at_utc")
        if not isinstance(stamp, str) or not stamp:
            raise ValueError("Snapshot needs acquisition time")
        # Canonical timestamps make out-of-order ingestion deterministic.
        observed_at = _timestamp(stamp)
        prepared = []
        for index, request in enumerate(manifest.get("requests", [])):
            endpoint = request["endpoint"]
            if not endpoint.startswith("/") or "?" in endpoint or "#" in endpoint:
                raise ValueError("Store a path without an authenticated URL")
            body, payload = None, None
            if request.get("http_status") == 200 and "file" in request:
                source_file = (directory / request["file"]).resolve()
                if not source_file.is_relative_to(directory):
                    raise ValueError("Source path escapes snapshot")
                body = source_file.read_bytes()
                if request.get("sha256") != _hash(body):
                    raise ValueError("Acquired source hash mismatch")
                payload = _load(body)
                _safe(payload)
                if not isinstance(payload, (dict, list)):
                    raise ValueError("Expected JSON object or array")
            prepared.append((index, request, body, payload))
        before = self.connection.total_changes
        with self.connection:
            # Interpret values with definitions from this same acquisition even
            # when the caller listed metadata after financial endpoints.
            ordered = sorted(prepared, key=lambda item: 0 if "metadata" in item[1]["endpoint"].lower() else 1)
            metadata_source_id = None
            for index, request, body, payload in ordered:
                endpoint = request["endpoint"]
                parameters = request.get("parameters", {})
                source_id = None
                if body is not None:
                    source_id = self._source("borsdata", endpoint, parameters, body, observed_at,
                                             {"schema_version": SCHEMA_VERSION, "manifest_sha256": _hash(manifest_body)})
                    if endpoint.lower().endswith("/kpis/metadata"):
                        metadata_source_id = source_id
                    self._normalize(endpoint, parameters, payload, source_id, observed_at,
                                    manifest.get("instrument_id"), metadata_source_id)
                acquisition_id = "acq_" + _hash(manifest_body + str(index).encode())[:24]
                self.connection.execute("INSERT OR IGNORE INTO acquisitions VALUES (?,?,?,?,?,?)",
                                        (acquisition_id, source_id, endpoint, observed_at,
                                         "saved" if source_id else "failed", _json({"http_status": request.get("http_status"), "parameters": parameters})))
        return {"directory": str(directory), "requests": len(prepared), "database_changes": self.connection.total_changes - before, **self.stats()}

    def _normalize(self, endpoint, parameters, payload, source_id, observed_at, expected_id, metadata_source_id=None):
        path = endpoint.lower()
        match = re.search(r"/instruments/(\d+)/", path)
        path_id = int(match[1]) if match else expected_id
        if isinstance(payload, dict):
            instrument = _row_get(payload, "instrument", "instrumentId", default=path_id)
            if path_id is not None and instrument is not None and int(instrument) != int(path_id):
                raise ValueError("Response instrument mismatch")
        else:
            instrument = path_id
        if "metadata" in path:
            self._dataset("metadata", None, payload, source_id, "")
            return
        if path.endswith("/instruments"):
            rows = _row_get(payload, "instruments") if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                raise ValueError("Missing instruments array")
            for i, row in enumerate(rows):
                ins = _row_get(row, "insId")
                if not isinstance(ins, int):
                    raise ValueError("Invalid instrument identifier")
                identifier = _hash(_json([source_id, ins, row]))
                self.connection.execute("INSERT OR IGNORE INTO instrument_versions VALUES (?,?,?,?,?)", (identifier, ins, source_id, observed_at, _json(row)))
                self._dataset("instruments", ins, row, source_id, f"/instruments/{i}")
            return
        if "/reports" in path:
            if not isinstance(payload, dict):
                raise ValueError("Reports response must be an object")
            groups = _row_get(payload, "reportList")
            if groups is not None:
                if not isinstance(groups, list):
                    raise ValueError("Invalid reportList")
                for i, group in enumerate(groups):
                    self._report_group(group, parameters, source_id, observed_at, f"/reportList/{i}")
            elif path.rsplit("/", 1)[-1] in {"year", "quarter", "r12"}:
                rows = _row_get(payload, "reports")
                self._reports(rows, int(instrument), path.rsplit("/", 1)[-1], parameters, source_id, observed_at, "/reports")
            else:
                self._report_group(payload, parameters, source_id, observed_at, "")
            return
        if "/stockprices" in path:
            if not isinstance(payload, dict):
                raise ValueError("Price response must be an object")
            rows = _row_get(payload, "stockPricesList", "stockPrices")
            if not isinstance(rows, list):
                raise ValueError("Missing price rows")
            for i, row in enumerate(rows):
                ins = _row_get(row, "i", "instrumentId", default=instrument)
                if ins is None:
                    raise ValueError("Missing price instrument")
                if match and int(ins) != int(match[1]):
                    raise ValueError("Price row instrument mismatch")
                day = _day(_row_get(row, "d", "date", "price_Date"), True)
                self._dataset("prices", int(ins), row, source_id, f"/stockPricesList/{i}")
                for short, metric in [("o", "price_open"), ("h", "price_high"), ("l", "price_low"), ("c", "price_close"), ("v", "volume")]:
                    raw = _row_get(row, short, default=None)
                    if short == "c" and raw is None:
                        raise ValueError("Missing closing price")
                    if short not in {key.lower() for key in row}:
                        continue
                    self._observation({"provider": "borsdata", "instrument_id": int(ins), "report_type": "price", "metric": metric,
                                       "value": _number(raw), "unit": "shares" if short == "v" else "currency/share", "scale": "1",
                                       "currency": None if short == "v" else self._currency(int(ins)), "period_start": None, "period_end": day,
                                       "year": int(day[:4]), "period": None, "kind": "market", "basis": "provider daily price; adjustment basis unverified",
                                       "status": "unreviewed", "currency_mode": "quote"}, source_id, f"/stockPricesList/{i}/{short}", observed_at)
            return
        if "/kpis/" in path and (path.endswith("/summary") or path.endswith("/history")):
            self._kpis(endpoint, payload, instrument, source_id, observed_at, metadata_source_id)
            return
        # Full event/lookup payloads remain queryable even before specialized mapping.
        dataset = "holdings_" + path.rsplit("/", 1)[-1] if "/holdings/" in path else path.strip("/").replace("/", "_")
        if isinstance(payload, dict):
            for field in ("list", "stockSplitList"):
                groups = _row_get(payload, field)
                if not isinstance(groups, list):
                    continue
                for i, row in enumerate(groups):
                    ins = _row_get(row, "insId", "instrumentId")
                    if ins is None:
                        raise ValueError("Context row has no instrument identity")
                    values = _row_get(row, "values")
                    if isinstance(values, list) and values:
                        for j, item in enumerate(values):
                            self._dataset(dataset, int(ins), item, source_id, f"/{field}/{i}/values/{j}")
                    else:
                        self._dataset(dataset, int(ins), row, source_id, f"/{field}/{i}")
                return
        self._dataset(dataset, int(instrument) if instrument is not None else None, payload, source_id, "")

    def _report_group(self, group, parameters, source_id, observed_at, prefix):
        if not isinstance(group, dict) or _row_get(group, "instrument") is None:
            raise ValueError("Invalid combined report group")
        ins = int(_row_get(group, "instrument"))
        error = _row_get(group, "error")
        if error:
            self._dataset("instrument_errors", ins, {"error": error}, source_id, prefix)
            return
        for field, family in [("reportsYear", "year"), ("reportsQuarter", "quarter"), ("reportsR12", "r12")]:
            self._reports(_row_get(group, field), ins, family, parameters, source_id, observed_at, prefix + "/" + field)

    def _reports(self, rows, ins, family, parameters, source_id, observed_at, prefix):
        if not isinstance(rows, list):
            raise ValueError("Missing report series")
        original = parameters.get("original", 0)
        if original not in (0, 1, "0", "1"):
            raise ValueError("Invalid report currency mode")
        original = int(original)
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError("Invalid report row")
            year, period = row.get("year"), row.get("period")
            if not isinstance(year, int) or not isinstance(period, int) or period not in range(1, 6):
                raise ValueError("Invalid fiscal year/period")
            start, end = _day(row.get("report_Start_Date"), True), _day(row.get("report_End_Date"), True)
            if start > end:
                raise ValueError("Report period reversed")
            report_currency = row.get("currency")
            if not isinstance(report_currency, str) or not report_currency:
                raise ValueError("Missing report currency")
            self._dataset("reports", ins, row, source_id, f"{prefix}/{i}")
            # Annual endpoints may append a latest R12 observation.
            actual_family = "r12" if family == "year" and period != 5 else family
            for metric, value in row.items():
                if metric in REPORT_META:
                    continue
                kind = "stock" if metric in STOCKS else "flow" if metric in FLOWS else "unresolved"
                unit, scale = ("currency", "1000000") if metric in STOCKS | FLOWS else ("unknown", "1")
                currency = report_currency if original else self._currency(ins)
                basis = "provider definition; report reconciliation not applied"
                if metric == "number_Of_Shares":
                    unit, scale, currency, kind = "shares", "1000000", None, "share_basis_unresolved"
                elif metric == "earnings_Per_Share":
                    unit, scale, kind, basis = "currency/share", "1", "per_share", "basic/diluted basis unresolved"
                elif metric == "dividend":
                    unit, scale, kind, basis = "currency/share", "1", "distribution", "distribution period/payment status unresolved; do not sum quarters"
                elif metric in PRICE_FIELDS:
                    unit, scale, kind, currency = "currency/share", "1", "market_summary", self._currency(ins)
                    basis = "price interval/adjustment basis unresolved"
                if metric not in STOCKS | FLOWS | PRICE_FIELDS | {"number_Of_Shares", "earnings_Per_Share", "dividend"}:
                    # New provider fields remain in the raw row until their type is defined.
                    continue
                record = {"provider": "borsdata", "instrument_id": ins, "report_type": actual_family, "source_report_type": family,
                          "metric": metric, "value": _number(value), "unit": unit, "scale": scale, "currency": currency,
                          "original_currency": report_currency, "currency_mode": "original" if original else "converted",
                          "currency_ratio": _number(row.get("currency_Ratio")), "period_start": start, "period_end": end,
                          "provider_report_date": row.get("report_Date"), "year": year, "period": period, "kind": kind,
                          "basis": basis, "status": "unreviewed", "mapping_version": "borsdata-report-v1"}
                self._observation(record, source_id, f"{prefix}/{i}/{metric}", observed_at)

    def _kpi_units(self, kpi, observed_at, metadata_source_id=None):
        result = {"unit": "provider_defined", "scale": "1", "currency": None,
                  "mapping_version": "borsdata-kpi-v1"}
        if metadata_source_id is not None:
            # Deduplicated sources retain their first ingested timestamp. Bind the
            # actual capture's metadata directly, including older imports/reversions.
            rows = self.connection.execute("SELECT payload,source_id FROM datasets WHERE dataset='metadata' AND source_id=?", (metadata_source_id,))
        else:
            # A repeated metadata body may have been acquired before or after a
            # changed definition; source first-ingested time cannot order checks.
            rows = self.connection.execute(
                "SELECT d.payload,d.source_id FROM datasets d JOIN sources s ON s.id=d.source_id "
                "LEFT JOIN acquisitions a ON a.source_id=s.id AND a.status='saved' "
                "WHERE d.dataset='metadata' AND s.endpoint LIKE '%/kpis/metadata' "
                "AND COALESCE(a.observed_at,s.observed_at)<=? "
                "AND (a.id IS NOT NULL OR NOT EXISTS (SELECT 1 FROM acquisitions history WHERE history.source_id=s.id)) "
                "GROUP BY d.id ORDER BY MAX(COALESCE(a.observed_at,s.observed_at)) DESC,d.id DESC",
                (observed_at,))
        for row in rows:
            payload = json.loads(row["payload"])
            definitions = _row_get(payload, "kpiHistoryMetadatas", default=[])
            definition = next((item for item in definitions if _row_get(item, "kpiId") == kpi), None)
            if definition is None:
                continue
            result["metadata_source_id"] = row["source_id"]
            result["provider_format"] = definition.get("format")
            if definition.get("isString"):
                return result
            if definition.get("format") == "%":
                result.update(unit="percent")  # 12 means 12%, not 0.12.
            elif definition.get("format") == "MCURR":
                # Metadata defines the magnitude, not the conversion currency.
                result.update(unit="currency", scale="1000000")
            break
        if kpi in VALUATION_MULTIPLES:
            result.update(unit="multiple", scale="1",
                          unit_definition="https://github.com/Borsdata-Sweden/API/wiki/KPI-History#kpi-table")
        elif kpi == 37:
            # Provider ROIC is profit / its own capital base, expressed in percent.
            # It is not our NOPAT / average invested capital diagnostic.
            result.update(unit="percent", scale="1", mapping_version="borsdata-kpi-v2",
                          unit_definition="https://borsdata.se/info/nyckeltal/roic")
        return result

    def _kpis(self, endpoint, payload, instrument, source_id, observed_at, metadata_source_id=None):
        if not isinstance(payload, dict):
            raise ValueError("KPI response must be an object")
        parts = endpoint.lower().strip("/").split("/")
        summary = parts[-1] == "summary"
        family = parts[-2] if summary else parts[-3]
        price_type = None if summary else parts[-2]
        if family not in {"year", "quarter", "r12"}:
            raise ValueError("Invalid KPI family")
        if instrument is None:
            raise ValueError("KPI instrument absent; batch KPI normalization not implemented")
        if summary:
            groups = _row_get(payload, "kpis")
        else:
            requested_kpi = int(parts[-4])
            if int(_row_get(payload, "kpiId", default=requested_kpi)) != requested_kpi:
                raise ValueError("KPI identity mismatch")
            groups = [{"kpiId": requested_kpi, "values": _row_get(payload, "values")}]
        if not isinstance(groups, list):
            raise ValueError("Missing KPI groups")
        for gi, group in enumerate(groups):
            kpi = _row_get(group, "kpiId")
            values = _row_get(group, "values")
            if not isinstance(kpi, int) or not isinstance(values, list):
                raise ValueError("Invalid KPI group")
            units = self._kpi_units(kpi, observed_at, metadata_source_id)
            for i, row in enumerate(values):
                year, period = row.get("y"), row.get("p")
                if not isinstance(year, int) or period not in range(1, 6):
                    raise ValueError("Invalid KPI period")
                pointer = f"/kpis/{gi}/values/{i}" if summary else f"/values/{i}"
                self._dataset("kpis", int(instrument), {"kpi_id": kpi, "report_type": family, "price_type": price_type, **row}, source_id, pointer)
                self._observation({"provider": "borsdata", "instrument_id": int(instrument), "report_type": "r12" if family == "year" and period != 5 else family,
                                   "source_report_type": family, "metric": f"kpi_{kpi}", "value": _number(row.get("v")), **units,
                                   "year": year, "period": period, "period_start": None, "period_end": None, "kind": "provider_kpi",
                                   "basis": "summary price basis unspecified" if summary else f"{family}/{price_type}", "price_type": price_type,
                                   "status": "unreviewed", "currency_mode": "provider_defined"}, source_id, pointer + "/v", observed_at)

    def add_report_facts(self, path):
        if self.readonly:
            raise ValueError("Read-only store")
        path = Path(path).resolve()
        body = path.read_bytes()
        data = _load(body)
        _safe(data)
        if not isinstance(data.get("instrument_id"), int) or not data.get("mapping_version") or not data.get("observed_at"):
            raise ValueError("Report facts need instrument, mapping version and observed time")
        observed_at = _timestamp(data["observed_at"])
        with self.connection:
            source_id = self._source("issuer_report", "/report-facts", {"mapping_version": data["mapping_version"]}, body, observed_at, {"schema_version": SCHEMA_VERSION})
            for i, fact in enumerate(data["facts"]):
                evidence = fact.get("evidence", fact.get("source"))
                if not isinstance(evidence, dict) or not evidence.get("report_id") or not isinstance(evidence.get("page"), int) or evidence["page"] < 1:
                    raise ValueError("Report fact requires report ID and physical PDF page")
                if not all(fact.get(k) for k in ("metric", "unit", "scale", "report_type", "kind", "basis", "status")):
                    raise ValueError("Incomplete report fact definition")
                if Decimal(_number(fact["scale"])) <= 0:
                    raise ValueError("Scale must be positive")
                start, end = _day(fact.get("period_start")), _day(fact.get("period_end"), True)
                if start and start > end:
                    raise ValueError("Reversed report fact period")
                record = dict(fact)
                record.update(provider="issuer_report", instrument_id=data["instrument_id"], value=_number(fact.get("value")),
                              scale=_number(fact["scale"]), period_start=start, period_end=end, evidence=evidence,
                              currency_mode="original", mapping_version=data["mapping_version"])
                self._observation(record, source_id, f"/facts/{i}", observed_at)
        return {"source_id": source_id, "facts": len(data["facts"])}

    def validate_report_links(self, catalogue, instrument_id=None):
        """Check every saved report fact against an already verified PDF catalogue.

        Catalogue entries contain source_sha256 and physical page count (pages).
        Filesystem paths from fact evidence are never opened here.
        """
        count = 0
        for row in self.connection.execute("SELECT record FROM observations"):
            record = json.loads(row[0])
            if record.get("provider") != "issuer_report":
                continue
            if instrument_id is not None and record.get("instrument_id") != instrument_id:
                continue
            evidence = record.get("evidence", {})
            report_id = evidence.get("report_id")
            report = catalogue.get(report_id)
            if not isinstance(report, dict):
                raise ValueError(f"Report fact references absent report: {report_id}")
            expected = report.get("source_sha256")
            actual = evidence.get("sha256")
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected) or actual != expected:
                raise ValueError(f"Report fact source hash mismatch: {report_id}")
            page, pages = evidence.get("page"), report.get("pages")
            if type(page) is not int or type(pages) is not int or not 1 <= page <= pages:
                raise ValueError(f"Report fact page outside PDF bounds: {report_id}")
            count += 1
        return {"validated_report_observations": count}

    def _freshness(self, identifiers, observations=False):
        """Derive raw-source capture/check dates, preserving immutable records.

        A raw body can support different metadata interpretations. These dates
        describe its acquisition history, not confirmation of a definition.
        """
        if not identifiers:
            return {}
        if observations:
            origin = "observation_sources os JOIN sources s ON s.id=os.source_id"
            key = "os.observation_id"
        else:
            origin, key = "sources s", "s.id"
        rows = self.connection.execute(
            f"SELECT {key} AS id, MIN(COALESCE(a.observed_at,s.observed_at)) AS source_first_captured_at, "
            "MAX(a.observed_at) AS source_last_successful_check_at "
            f"FROM {origin} LEFT JOIN acquisitions a ON a.source_id=s.id AND a.status='saved' "
            f"WHERE {key} IN (" + ",".join("?" for _ in identifiers) + f") GROUP BY {key}",
            identifiers)
        return {row["id"]: {field: row[field] for field in
                ("source_first_captured_at", "source_last_successful_check_at")} for row in rows}

    def _observation_records(self, rows):
        records = [json.loads(row[0]) for row in rows]
        freshness = self._freshness([record["id"] for record in records], observations=True)
        return [{**record, **freshness[record["id"]]} for record in records]

    def query_financials(self, instrument_id, report_type=None, fields=None, limit=200, offset=0):
        if not isinstance(limit, int) or not 1 <= limit <= 5000 or offset < 0:
            raise ValueError("limit must be 1–5000 and offset nonnegative")
        where, args = ["o.instrument_id=?"], [instrument_id]
        if report_type:
            where.append("o.report_type=?"); args.append(report_type)
        if fields:
            if not isinstance(fields, (list, tuple)) or not all(isinstance(x, str) for x in fields):
                raise ValueError("fields must be a list of names")
            where.append("o.metric IN (" + ",".join("?" for _ in fields) + ")"); args.extend(fields)
        rows = self.connection.execute("SELECT o.record FROM observations o JOIN current_observations c ON c.logical_key=o.logical_key AND c.observation_id=o.id WHERE " + " AND ".join(where) + " ORDER BY o.year DESC,o.period DESC,o.period_end DESC,o.metric,o.id LIMIT ? OFFSET ?", [*args, limit, offset])
        return self._observation_records(rows)

    def get_observation(self, observation_id):
        row = self.connection.execute("SELECT record FROM observations WHERE id=?", (observation_id,)).fetchone()
        if row is None:
            raise KeyError("Unknown observation")
        return self._observation_records([row])[0]

    def get_source(self, source_id):
        row = self.connection.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        if row is None:
            raise KeyError("Unknown source")
        result = {**dict(row), **self._freshness([source_id])[source_id]}
        result["parameters"] = json.loads(result["parameters"])
        result["metadata"] = json.loads(result["metadata"])
        result["blob_path"] = "blobs/" + result["blob_path"]
        return result

    def query_dataset(self, dataset, instrument_id=None, limit=100, offset=0):
        if not 1 <= limit <= 5000 or offset < 0:
            raise ValueError("Invalid dataset query bounds")
        where, args = ["d.dataset=?"], [dataset]
        if instrument_id is not None:
            where.append("(d.instrument_id=? OR d.instrument_id IS NULL)"); args.append(instrument_id)
        rows = self.connection.execute("SELECT d.*,s.observed_at FROM datasets d JOIN sources s ON s.id=d.source_id WHERE " + " AND ".join(where) + " ORDER BY s.observed_at DESC,d.id LIMIT ? OFFSET ?", [*args, limit, offset])
        rows = list(rows)
        freshness = self._freshness(list({row["source_id"] for row in rows}))
        result = []
        for row in rows:
            value = {**dict(row), **freshness[row["source_id"]]}
            value["payload"] = json.loads(value["payload"])
            result.append(value)
        return result

    def list_datasets(self):
        return [dict(row) for row in self.connection.execute("SELECT dataset,count(*) AS records FROM datasets GROUP BY dataset ORDER BY dataset")]

    def stats(self):
        return {table: self.connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in ("sources", "acquisitions", "observations", "current_observations", "revisions", "datasets")}

    def freeze(self, destination):
        """Publish an independent database plus verified blobs by atomic rename."""
        destination = Path(destination).resolve()
        if destination.exists():
            raise FileExistsError("Snapshot destination already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".freeze-", dir=destination.parent))
        try:
            database = temporary / "evidence.sqlite3"
            target = sqlite3.connect(database)
            try:
                self.connection.backup(target)
                target.row_factory = sqlite3.Row
                source_rows = list(target.execute("SELECT DISTINCT blob_path,sha256 FROM sources ORDER BY blob_path"))
                counts = {table: target.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                          for table in ("sources", "acquisitions", "observations", "current_observations", "revisions", "datasets")}
            finally:
                target.close()
            blobs = temporary / "blobs"; blobs.mkdir()
            files = []
            for row in source_rows:
                source = self.blob_dir / row["blob_path"]
                body = source.read_bytes()
                if _hash(body) != row["sha256"]:
                    raise ValueError("Source corruption detected during freeze")
                target = blobs / row["blob_path"]; target.write_bytes(body); target.chmod(0o600)
                files.append({"path": "blobs/" + row["blob_path"], "sha256": row["sha256"], "bytes": len(body)})
            database.chmod(0o600)
            manifest = {"schema_version": SCHEMA_VERSION, "frozen_at": datetime.now(timezone.utc).isoformat(),
                        "database": "evidence.sqlite3", "database_sha256": _hash(database.read_bytes()),
                        "blobs": files, "counts": counts,
                        "normalizer_sha256": _hash(Path(__file__).read_bytes())}
            (temporary / "manifest.json").write_text(json.dumps(manifest, indent=2))
            temporary.rename(destination)
        except BaseException:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return destination
