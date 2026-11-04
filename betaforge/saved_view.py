"""Build and validate a display-only export of frozen analysis artifacts.

This module copies saved financial results. It never calls providers, runs a model,
solves a formula, or infers a valuation from prose.
"""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlsplit


MAX_BYTES = 16 * 1024 * 1024
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
HASH = re.compile(r"[a-f0-9]{64}")
NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
FIELDS = {
    "schema_version", "id", "company", "analysis_date", "reviewed_at", "method",
    "price", "conclusion", "scenarios", "probability", "calculations",
    "original_calculations", "interpretation", "notes", "narrative", "sources",
    "benchmark", "provenance",
}
PRICE_FIELDS = {"id", "value", "unit", "scale", "currency", "basis", "date", "source_id", "status"}
BENCHMARK_FIELDS = {
    "candidate_annualized_return_percent", "benchmark_annualized_return_percent",
    "difference_percentage_points", "interpretation", "limits", "context",
}
CONTEXT_FIELDS = {
    "schema_version", "context_type", "provider", "publisher", "retrieved_at_utc",
    "manifest_sha256", "benchmark", "analysis_date", "start_anchor_date",
    "start_observation", "end_observation", "boundary_rule", "calculation",
    "rounded_source", "source_sections", "caveats", "status",
}
PROVENANCE_FIELDS = {
    "database_sha256", "packet_sha256", "review_sha256", "run_sha256",
    "summary_sha256", "narrative_sha256", "model",
    "reasoning_effort", "status", "started_at", "finished_at", "coverage",
}
OPTIONAL_HASHES = {"current_facts_sha256", "material_inputs_sha256"}
DEFINITION_STATUSES = {"documented", "unresolved"}
RECONCILIATION_STATUSES = {"unreviewed", "matched", "derived_match", "disagrees", "not_comparable"}
SOURCE_RECORD_FIELDS = {
    "id", "metric", "value", "scale", "unit", "currency", "kind", "basis", "status",
    "period_start", "period_end", "report_type", "year", "period", "source_id", "pointer",
    "evidence", "provider", "instrument_id", "source_report_type", "original_currency",
    "currency_mode", "currency_ratio", "provider_report_date", "mapping_version", "observed_at",
    "metadata_source_id", "provider_format", "unit_definition", "price_type", "calc_group", "calc",
    "report_id", "source_pointer", "derivation", "selection_reason", "publication_date",
    "source_first_captured_at", "source_last_successful_check_at", "label", "page", "quote", "note",
}
NUMERIC_FIELDS = {
    "value", "scale", "result", "calculation_value", "weight",
    "candidate_annualized_return_percent", "benchmark_annualized_return_percent",
    "difference_percentage_points", "level", "elapsed_years",
}


def checked_path(path):
    """Reject symlink files and parents before opening a local artifact."""
    path = Path(path).absolute()
    if ".." in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Artifact paths must not contain symlinks or parent traversal")
    return path


def _body(path):
    path = checked_path(path)
    if not path.is_file():
        raise FileNotFoundError("Saved artifact is missing")
    with path.open("rb") as stream:
        body = stream.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Saved artifact exceeds 16 MiB")
    return body


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def _decode(body):
    try:
        return json.loads(body, object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Invalid saved JSON") from error


def _json(path):
    return _decode(_body(path))


def _digest(path):
    result = hashlib.sha256()
    with checked_path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def _number(value):
    if value is None:
        return
    if not isinstance(value, str) or not NUMBER.fullmatch(value):
        raise ValueError("Financial values must be finite decimal strings or null")
    try:
        if not Decimal(value).is_finite():
            raise ValueError("Non-finite financial value")
    except InvalidOperation as error:
        raise ValueError("Invalid financial value") from error


def _object(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError("Invalid saved-view object fields")


def _text(value, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty saved text")


def _date(value):
    _text(value)
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError("Invalid date")
    except ValueError as error:
        raise ValueError("Expected ISO analysis date") from error


def _timestamp(value):
    _text(value)
    try:
        if datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None:
            raise ValueError("Timestamp needs timezone")
    except ValueError as error:
        raise ValueError("Expected dated timestamp with timezone") from error


def _url(value):
    if value is None:
        return
    _text(value)
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in {"https", "http"} or not parsed.hostname or
                parsed.username is not None or parsed.password is not None or
                any(ord(c) < 33 or ord(c) == 127 for c in value) or "\\" in value):
            raise ValueError("Unsafe source URL")
        parsed.port
        for key, _ in parse_qsl(parsed.query):
            if re.search(r"token|secret|password|credential|api.?key|signature|authorization", key, re.I):
                raise ValueError("Source URL contains credentials")
    except ValueError as error:
        raise ValueError("Unsafe source URL") from error


def _tree(value, depth=0):
    """Validate retained calculation metadata without changing its shape."""
    if depth > 32:
        raise ValueError("Saved metadata is too deeply nested")
    if isinstance(value, dict):
        for key, item in value.items():
            if key in NUMERIC_FIELDS or (key.endswith(("_percent", "_fraction")) and isinstance(item, str)):
                _number(item)
            if (key == "path" or key.endswith("_path")) and isinstance(item, str) and Path(item).is_absolute():
                raise ValueError("Absolute artifact paths are not display metadata")
            if key in {"url", "source_url", "resolved_url"}:
                _url(item)
            _tree(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _tree(item, depth + 1)
    elif value is not None and not isinstance(value, (str, bool, int)):
        raise ValueError("Saved metadata must preserve decimals as strings")


def _texts(value):
    if not isinstance(value, list):
        raise ValueError("Expected saved text list")
    for item in value:
        _text(item)


def _evidence(value):
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError("Expected saved evidence objects")


def _material_statuses(record):
    if (not isinstance(record["definition_status"], str) or record["definition_status"] not in DEFINITION_STATUSES or
            not isinstance(record["reconciliation_status"], str) or record["reconciliation_status"] not in RECONCILIATION_STATUSES):
        raise ValueError("Invalid material input status")


def _source_record(record):
    _object(record, {"id", "value", "scale", "unit", "kind"}, SOURCE_RECORD_FIELDS)
    for key in ("id", "unit", "kind"):
        _text(record[key])
    for key in ("value", "scale", "currency_ratio"):
        if key in record:
            _number(record[key])
    if record["scale"] is None or Decimal(record["scale"]) <= 0:
        raise ValueError("Source record scale must be positive")
    for key in ("period_start", "period_end"):
        if record.get(key) is not None:
            _date(record[key])
    if record.get("period_start") and record.get("period_end") and record["period_start"] > record["period_end"]:
        raise ValueError("Source record period is reversed")
    for key in ("year", "period", "instrument_id"):
        if record.get(key) is not None and type(record[key]) is not int:
            raise ValueError("Invalid source record period or instrument")
    if "pointer" in record and not isinstance(record["pointer"], (str, dict)):
        raise ValueError("Invalid saved source pointer")
    if "evidence" in record:
        _evidence(record["evidence"] if isinstance(record["evidence"], list) else [record["evidence"]])
    if "derivation" in record:
        derivation = record["derivation"]
        _object(derivation, {"formula", "inputs"})
        _text(derivation["formula"])
        if not isinstance(derivation["inputs"], list):
            raise ValueError("Invalid source record derivation inputs")
        for item in derivation["inputs"]:
            _object(item, {"label", "value", "scale", "unit"})
            _text(item["label"])
            _text(item["unit"])
            _number(item["value"])
            _number(item["scale"])
    if record.get("publication_date") is not None:
        _date(record["publication_date"])
    for key in ("source_first_captured_at", "source_last_successful_check_at"):
        if record.get(key) is not None:
            _timestamp(record[key])
    if "page" in record and (type(record["page"]) is not int or record["page"] <= 0):
        raise ValueError("Invalid source record page")
    for key in SOURCE_RECORD_FIELDS - {"value", "scale", "currency_ratio", "year", "period", "instrument_id", "pointer", "evidence", "derivation", "page"}:
        if key in record:
            _text(record[key], nullable=True)


def _material_inputs(rows):
    if not isinstance(rows, list):
        raise ValueError("Invalid material input decisions")
    identifiers = set()
    for row in rows:
        _object(row, {"id", "label", "definition", "definition_status", "reconciliation_status",
                      "selected", "candidates", "selection_reason", "valuation_uses", "limitations", "evidence"})
        for key in ("id", "label", "definition", "selection_reason"):
            _text(row[key])
        if row["id"] in identifiers:
            raise ValueError("Duplicate material input decision")
        identifiers.add(row["id"])
        _material_statuses(row)
        if row["selected"] is not None:
            _source_record(row["selected"])
        _texts(row["valuation_uses"])
        _texts(row["limitations"])
        _evidence(row["evidence"])
        if not isinstance(row["candidates"], list):
            raise ValueError("Invalid material input candidates")
        for candidate in row["candidates"]:
            _object(candidate, {"record", "definition_status", "reconciliation_status", "comparison_basis", "residual"})
            _source_record(candidate["record"])
            _material_statuses(candidate)
            _text(candidate["comparison_basis"])
            if candidate["residual"] is not None:
                _object(candidate["residual"], {"value", "unit", "formula"})
                _number(candidate["residual"]["value"])
                _text(candidate["residual"]["unit"])
                _text(candidate["residual"]["formula"])


def validate_saved_view(view):
    """Validate the bounded display schema before a server exposes it."""
    _object(view, FIELDS, {"material_inputs", "current_data_limits"})
    if type(view["schema_version"]) is not int or view["schema_version"] != 1:
        raise ValueError("Unsupported saved-view version")
    if not isinstance(view["id"], str) or len(view["id"]) > 100 or not SLUG.fullmatch(view["id"]):
        raise ValueError("Saved-view id must be a URL-safe lowercase slug")
    _object(view["company"], {"name", "ticker", "instrument_id"})
    _text(view["company"]["name"])
    _text(view["company"]["ticker"])
    if type(view["company"]["instrument_id"]) is not int or view["company"]["instrument_id"] <= 0:
        raise ValueError("Invalid instrument id")
    _date(view["analysis_date"])
    _timestamp(view["reviewed_at"])
    for key in ("method", "conclusion", "narrative"):
        _text(view[key])
    if view["price"] is not None:
        _object(view["price"], PRICE_FIELDS)
        _number(view["price"]["value"])
        _number(view["price"]["scale"])
        if view["price"]["date"] is not None:
            _date(view["price"]["date"])
        for key in PRICE_FIELDS - {"value", "scale", "date"}:
            _text(view["price"][key], nullable=True)
    if not isinstance(view["scenarios"], list):
        raise ValueError("Invalid scenarios")
    for scenario in view["scenarios"]:
        _object(scenario, {"name", "value", "unit", "basis", "calculation_ids"}, {"weight"})
        for key in ("name", "unit", "basis"):
            _text(scenario[key])
        _number(scenario["value"])
        if not isinstance(scenario["calculation_ids"], list):
            raise ValueError("Invalid scenario calculation IDs")
        for calculation_id in scenario["calculation_ids"]:
            _text(calculation_id)
    probability = view["probability"]
    _object(probability, {"weights", "basis", "status"})
    if probability["status"] not in {"proposed", "saved", "missing"} or not isinstance(probability["weights"], dict):
        raise ValueError("Invalid probability status or weights")
    _text(probability["basis"], nullable=True)
    for name, weight in probability["weights"].items():
        _text(name)
        _number(weight)
        if weight is None or not 0 <= Decimal(weight) <= 1:
            raise ValueError("Probability weight outside zero to one")
    for scenario in view["scenarios"]:
        if "weight" in scenario and scenario["weight"] != probability["weights"].get(scenario["name"].lower()):
            raise ValueError("Scenario weight differs from saved probability")
    for key in ("calculations", "original_calculations", "interpretation", "notes", "sources"):
        if not isinstance(view[key], list):
            raise ValueError("Invalid saved-view list")
    for interpretation in view["interpretation"]:
        _text(interpretation)
    for note in view["notes"]:
        if isinstance(note, dict):
            _object(note, {"id", "text"}, {"evidence"})
            _text(note["id"])
            _text(note["text"])
        else:
            _text(note)
    for calc in view["calculations"]:
        _object(calc, {"id", "formula", "version", "formula_text", "outputs", "inputs", "options", "warnings", "missing_inputs"}, {"label", "primary_output", "preserved_assumptions", "display_role", "report_type", "period_start", "period_end", "year", "period", "current_period_reason", "price_date"})
        for key in ("id", "formula", "version", "formula_text"):
            _text(calc[key])
        if not isinstance(calc["outputs"], dict) or not isinstance(calc["inputs"], dict):
            raise ValueError("Invalid named calculation")
        if "display_role" in calc and calc["display_role"] != "current":
            raise ValueError("Invalid calculation display role")
        for key in ("period_start", "period_end", "price_date"):
            if calc.get(key) is not None:
                _date(calc[key])
        if calc.get("period_start") and calc.get("period_end") and calc["period_start"] > calc["period_end"]:
            raise ValueError("Calculation period is reversed")
        for key in ("report_type", "current_period_reason"):
            if key in calc:
                _text(calc[key])
        for key in ("year", "period"):
            if key in calc and type(calc[key]) is not int:
                raise ValueError("Invalid calculation period")
    for calc in view["original_calculations"]:
        required = {"id", "operation", "inputs", "result", "label", "unit", "scale", "basis"}
        optional = set()
        if isinstance(calc, dict) and calc.get("operation") == "financial_formula":
            required |= {"formula", "version", "primary_output", "formula_text", "outputs", "input_ids", "options", "warnings", "missing_inputs"}
            optional = {"period_start", "period_end"}
        _object(calc, required, optional)
        _text(calc["id"])
        if not isinstance(calc["inputs"], list):
            raise ValueError("Invalid original calculation inputs")
        if calc["operation"] == "financial_formula":
            for key in ("formula", "version", "primary_output", "formula_text"):
                _text(calc[key])
            if not isinstance(calc["outputs"], dict) or not isinstance(calc["input_ids"], dict):
                raise ValueError("Invalid original named calculation")
            for identifier in calc["input_ids"].values():
                _text(identifier)
            for key in optional & calc.keys():
                _date(calc[key])
    calculations_by_id = {calc["id"]: calc for calc in view["original_calculations"] + view["calculations"]}
    for scenario in view["scenarios"]:
        references = scenario["calculation_ids"]
        if scenario["value"] is not None and not references:
            raise ValueError("Scenario must reference calculations retained in this saved view")
        for reference in references:
            if reference in calculations_by_id:
                continue
            base, separator, output = reference.partition("#")
            if not separator or output not in calculations_by_id.get(base, {}).get("outputs", {}):
                raise ValueError("Scenario must reference a retained calculation or named output")
    for source in view["sources"]:
        _object(source, {"id", "title", "period", "published_at", "url", "sha256", "prepared_sha256", "pages"})
        _text(source["id"])
        _text(source["title"])
        _url(source["url"])
        for key in ("sha256", "prepared_sha256"):
            if not isinstance(source[key], str) or not HASH.fullmatch(source[key]):
                raise ValueError("Invalid source hash")
        if type(source["pages"]) is not int or source["pages"] <= 0:
            raise ValueError("Invalid source pages")
        _object(source["period"], {"start", "end"})
        for value in (*source["period"].values(), source["published_at"]):
            if value is not None:
                _date(value)
    benchmark = view["benchmark"]
    _object(benchmark, BENCHMARK_FIELDS)
    if not isinstance(benchmark["limits"], list):
        raise ValueError("Invalid benchmark limits")
    _text(benchmark["interpretation"], nullable=True)
    for limit in benchmark["limits"]:
        _text(limit)
    if benchmark["context"] is not None:
        _object(benchmark["context"], (), CONTEXT_FIELDS)
    provenance = view["provenance"]
    _object(provenance, PROVENANCE_FIELDS, OPTIONAL_HASHES)
    for key in {"database_sha256", "packet_sha256", "review_sha256", "run_sha256", "summary_sha256", "narrative_sha256"} | (OPTIONAL_HASHES & provenance.keys()):
        if not isinstance(provenance[key], str) or not HASH.fullmatch(provenance[key]):
            raise ValueError("Invalid provenance hash")
    if provenance["status"] != "completed" or not isinstance(provenance["coverage"], dict):
        raise ValueError("Saved view requires a completed run")
    for key in ("model", "reasoning_effort"):
        _text(provenance[key])
    for key in ("started_at", "finished_at"):
        _timestamp(provenance[key])
    if "material_inputs" in view:
        _material_inputs(view["material_inputs"])
    if "material_inputs_sha256" in provenance:
        if "material_inputs" not in view:
            raise ValueError("Material input hash requires its saved decisions")
        body = json.dumps(view["material_inputs"], sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if hashlib.sha256(body).hexdigest() != provenance["material_inputs_sha256"]:
            raise ValueError("Material input decision hash mismatch")
    if "current_data_limits" in view:
        _texts(view["current_data_limits"])
    _tree(view)
    return view


def load_saved_view(path):
    return validate_saved_view(_json(path))


def _child(base, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Frozen packet paths must be relative")
    return checked_path(Path(base) / path)


def build_saved_view(review_path, run_dir, packet_dir, company_name, ticker, view_id, method):
    """Copy one reviewed, completed run after checking its preserved identities."""
    review_path, run_dir, packet_dir = map(checked_path, (review_path, run_dir, packet_dir))
    review_body = _body(review_path)
    run_body = _body(run_dir / "run.json")
    packet_body = _body(packet_dir / "packet.json")
    review, run, packet = map(_decode, (review_body, run_body, packet_body))
    if run.get("status") != "completed" or run.get("smoke") is not False:
        raise ValueError("Export requires a completed non-smoke run")
    identity = run["identity"]
    packet_hash = hashlib.sha256(packet_body).hexdigest()
    snapshot = _child(packet_dir, packet["snapshot_dir"])
    database_hash = _digest(snapshot / "evidence.sqlite3")
    manifest = _json(snapshot / "manifest.json")
    if (identity.get("packet_sha256") != packet_hash or
            not database_hash == identity.get("database_sha256") == review.get("database_sha256") == manifest.get("database_sha256")):
        raise ValueError("Packet/database identities do not match the saved review and run")
    if (packet.get("instrument_id") != review.get("instrument_id") or
            packet.get("analysis_date") != review.get("frozen_analysis_date")):
        raise ValueError("Review instrument/date differs from the frozen packet")
    preserved = review["preserved_valuation"]
    original_bodies = {name: _body(run_dir / (name + ".json")) for name in ("inputs", "calculations")}
    for name, body in original_bodies.items():
        if hashlib.sha256(body).hexdigest() != preserved.get(name + "_sha256"):
            raise ValueError("Original valuation artifact hash mismatch: " + name)
    original_calculations = _decode(original_bodies["calculations"])
    summary_body = _body(run_dir / "review-summary.json")
    narrative_body = _body(run_dir / "answer.md")
    summary = _decode(summary_body)
    context = packet.get("context", {})
    if isinstance(context, str):
        try:
            context = json.JSONDecoder(object_pairs_hook=_pairs).raw_decode(context[context.index("{"):])[0]
        except (ValueError, json.JSONDecodeError) as error:
            raise ValueError("Frozen packet financial context is invalid") from error
    closes = context.get("latest_close", [])
    price = None
    if closes:
        saved_price = closes[0]
        if saved_price.get("instrument_id", packet["instrument_id"]) != packet["instrument_id"]:
            raise ValueError("Frozen price belongs to a different instrument")
        price = {key: saved_price.get(key) for key in PRICE_FIELDS}
        price["date"] = saved_price.get("date", saved_price.get("period_end"))
    probability_source = review.get("probability", review.get("probability_proposal"))
    probability = {"weights": {}, "basis": None, "status": "missing"}
    if probability_source is not None:
        probability.update(weights=probability_source.get("weights", {}), basis=probability_source.get("basis"),
                           status="saved" if "probability" in review else "proposed")
    scenarios = []
    for saved in summary.get("scenarios", []):
        scenario = dict(saved)
        if saved["name"].lower() in probability["weights"]:
            scenario["weight"] = probability["weights"][saved["name"].lower()]
        scenarios.append(scenario)
    reports_dir = _child(packet_dir, packet["reports_dir"])
    report_manifest = _json(reports_dir / "source-manifest.json")
    prepared = _json(reports_dir / "prepared/index.json")
    report_ids = [item["report_id"] for item in prepared["reports"]]
    for report_id in report_ids:
        _text(report_id)
    if len(report_ids) != len(set(report_ids)) or set(report_ids) != set(identity.get("reports", {})):
        raise ValueError("Prepared reports must uniquely match all saved run report identities")
    if report_manifest.get("borsdata_instrument_id") != packet["instrument_id"]:
        raise ValueError("Report manifest instrument differs from packet")
    originals = {item["report_id"]: item for item in report_manifest["documents"]}
    sources = []
    for item in prepared["reports"]:
        rid = item["report_id"]
        original = originals[rid]
        if original.get("borsdata_instrument_id", packet["instrument_id"]) != packet["instrument_id"]:
            raise ValueError("Report source belongs to a different instrument")
        if (original["sha256"] != item["source_sha256"] or
                identity.get("reports", {}).get(rid) != [item["source_sha256"], item["prepared_sha256"]]):
            raise ValueError("Saved report identities do not match")
        sources.append({"id": rid, "title": original.get("title") or rid,
                        "period": original.get("reporting_period", {"start": None, "end": None}),
                        "published_at": original.get("publication_date"), "url": original.get("source_url"),
                        "sha256": item["source_sha256"], "prepared_sha256": item["prepared_sha256"],
                        "pages": item["pages"]})
    comparison = review.get("market_benchmark_comparison")
    if comparison is None:
        comparison = {}
    if not isinstance(comparison, dict):
        raise ValueError("Saved benchmark comparison must be an object or null")
    benchmark_source = comparison.get("source")
    if benchmark_source is None:
        benchmark_source = {}
    if not isinstance(benchmark_source, dict):
        raise ValueError("Saved benchmark source must be an object or null")
    source_context = benchmark_source.get("context")
    if source_context is not None and not isinstance(source_context, dict):
        raise ValueError("Saved benchmark context must be an object or null")
    benchmark = {key: comparison.get(key) for key in BENCHMARK_FIELDS}
    benchmark["limits"] = comparison.get("limits", [])
    benchmark["context"] = ({key: value for key, value in source_context.items() if key in CONTEXT_FIELDS}
                            if source_context is not None else None)
    view = {
        "schema_version": 1, "id": view_id,
        "company": {"name": company_name, "ticker": ticker, "instrument_id": packet["instrument_id"]},
        "analysis_date": packet["analysis_date"], "reviewed_at": review["reviewed_at"], "method": method,
        "price": price, "conclusion": summary["conclusion"], "scenarios": scenarios,
        "probability": probability, "calculations": review["calculations"],
        "original_calculations": original_calculations,
        "interpretation": review.get("interpretation", []) + summary.get("interpretation", []),
        "notes": review.get("notes", []) + summary.get("notes", []),
        "narrative": narrative_body.decode("utf-8"), "sources": sources, "benchmark": benchmark,
        "provenance": {"database_sha256": database_hash, "packet_sha256": packet_hash,
                       "review_sha256": hashlib.sha256(review_body).hexdigest(),
                       "run_sha256": hashlib.sha256(run_body).hexdigest(),
                       "summary_sha256": hashlib.sha256(summary_body).hexdigest(),
                       "narrative_sha256": hashlib.sha256(narrative_body).hexdigest(),
                       **{key: run.get(key) for key in ("model", "reasoning_effort", "status", "started_at", "finished_at", "coverage")}},
    }
    for key in ("material_inputs", "current_data_limits"):
        if key in review:
            view[key] = review[key]
    for key in OPTIONAL_HASHES & review.keys():
        view["provenance"][key] = review[key]
    return validate_saved_view(view)
