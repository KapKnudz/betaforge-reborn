"""Build and validate a display-only export of frozen analysis artifacts.

This module copies saved financial results. It never calls providers, runs a model,
solves a formula, or infers a valuation from prose.
"""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.parse import parse_qsl, urlsplit


MAX_BYTES = 16 * 1024 * 1024
MAX_READER_MEMO_BYTES = 64 * 1024
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
OPTIONAL_HASHES = {"current_facts_sha256", "material_inputs_sha256", "analysis_sha256"}
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
        if set(value) == {"value", "precision"}:
            from betaforge.analysis_report import dated_endpoint
            dated_endpoint(value)
            return
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
    _object(view, FIELDS, {"material_inputs", "current_data_limits", "analysis", "analysis_review", "saved_records", "reader_memo"})
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
        _object(scenario, {"name", "value", "unit", "basis", "calculation_ids"}, {"weight", "id", "present_value", "future_target", "present_value_date", "target_date"} if "analysis" in view else {"weight"})
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
        if "weight" in scenario and scenario["weight"] != probability["weights"].get(scenario.get("id", scenario["name"].lower())):
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
        _object(calc, {"id", "formula", "version", "formula_text", "outputs", "inputs", "options", "warnings", "missing_inputs"}, {"label", "basis", "primary_output", "preserved_assumptions", "display_role", "report_type", "period_start", "period_end", "year", "period", "current_period_reason", "price_date"})
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
            optional = {"period_start", "period_end", "report_type"}
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
            for key in {"period_start", "period_end"} & calc.keys():
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
        if key == "review_sha256" and provenance[key] is None and "analysis" in view and "analysis_review" not in view:
            continue
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
    if "analysis" in view:
        _validate_structured_view(view)
    elif {"analysis_review", "saved_records", "reader_memo"} & view.keys() or "analysis_sha256" in provenance:
        raise ValueError("Structured metadata requires its canonical analysis")
    _tree(view)
    return view


def load_saved_view(path):
    return validate_saved_view(_json(path))


def attach_reader_memo(view, memo):
    """Attach editorial text to a copy, preserving the canonical saved analysis."""
    validate_saved_view(view)
    result = deepcopy(view)
    result["reader_memo"] = deepcopy(memo)
    return validate_saved_view(result)


def _validate_reader_memo(memo, view, references):
    """Check editorial structure and reference identity, not the prose's claims."""
    from betaforge.analysis_report import SECTIONS, text
    _object(memo, {"schema_version", "analysis_sha256", "edited_at", "summary", "sections", "scenarios"})
    if type(memo["schema_version"]) is not int or memo["schema_version"] != 1:
        raise ValueError("Unsupported reader-memo version")
    if memo["analysis_sha256"] != view["provenance"]["analysis_sha256"]:
        raise ValueError("Reader memo requires the current canonical analysis hash")
    text(memo["edited_at"], "reader-memo timestamp", 80)
    _timestamp(memo["edited_at"])
    text(memo["summary"], "reader-memo summary", 1000)

    sections = memo["sections"]
    if not isinstance(sections, list) or len(sections) != len(SECTIONS):
        raise ValueError("Reader memo requires the six canonical sections")
    section_ids = []
    for section in sections:
        _object(section, {"id", "title", "paragraphs"})
        section_ids.append(text(section["id"], "reader-memo section ID", 100))
        text(section["title"], "reader-memo section title", 150)
        if not isinstance(section["paragraphs"], list) or not 1 <= len(section["paragraphs"]) <= 6:
            raise ValueError("Invalid reader-memo paragraphs")
        for paragraph in section["paragraphs"]:
            _object(paragraph, {"kind", "text", "references"})
            if not isinstance(paragraph["kind"], str) or paragraph["kind"] not in {"fact", "interpretation", "assumption"}:
                raise ValueError("Invalid reader-memo paragraph kind")
            text(paragraph["text"], "reader-memo paragraph", 1500)
            references(paragraph["references"])
    if set(section_ids) != set(SECTIONS):
        raise ValueError("Reader memo requires the six canonical sections")
    scenarios = memo["scenarios"]
    canonical_ids = {item["id"] for item in view["analysis"]["scenarios"]}
    if not isinstance(scenarios, list) or len(scenarios) != len(canonical_ids):
        raise ValueError("Reader memo requires each canonical scenario")
    scenario_ids = []
    for scenario in scenarios:
        _object(scenario, {"id", "rationale", "assumption_rationale", "probability_rationale", "references"})
        scenario_ids.append(text(scenario["id"], "reader-memo scenario ID", 100))
        for key in ("rationale", "assumption_rationale", "probability_rationale"):
            text(scenario[key], "reader-memo " + key, 1200)
        references(scenario["references"])
    if set(scenario_ids) != canonical_ids:
        raise ValueError("Reader memo requires each canonical scenario")
    if len(json.dumps(memo, ensure_ascii=False, allow_nan=False).encode("utf-8")) > MAX_READER_MEMO_BYTES:
        raise ValueError("Reader memo exceeds 64 KiB")


def _child(base, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Frozen packet paths must be relative")
    return checked_path(Path(base) / path)


def _saved_json_hash(value):
    """Match the runner's preserved JSON encoding, including its field order."""
    return hashlib.sha256(json.dumps(value, indent=2, ensure_ascii=False).encode("utf-8")).hexdigest()


def _normalized_calculation(record):
    keys = {"id", "formula", "version", "formula_text", "outputs", "options", "warnings", "missing_inputs",
            "label", "basis", "primary_output", "report_type", "period_start", "period_end"}
    result = {key: value for key, value in record.items() if key in keys}
    result["inputs"] = {item["field"]: dict(item) for item in record["inputs"]}
    if len(result["inputs"]) != len(record["inputs"]):
        raise ValueError("Duplicate named calculation input field")
    return result


def _probability_value(record):
    with localcontext() as context:
        context.prec = max(40, len(record["value"]) + len(record["scale"]) + 10)
        return str(Decimal(record["value"]) * Decimal(record["scale"]))


def _historical_benchmark_return(context, analysis_date):
    if not isinstance(context, dict):
        return None
    benchmark, calculation = context.get("benchmark"), context.get("calculation")
    if (not isinstance(benchmark, dict) or not isinstance(calculation, dict) or
            benchmark.get("symbol") != "SIXRX" or benchmark.get("currency") != "SEK" or
            benchmark.get("return_type") != "gross_total_return" or
            context.get("analysis_date") != analysis_date or
            context.get("status") != "verified_from_rounded_public_levels"):
        return None
    value = calculation.get("annualized_return_percent")
    try:
        _number(value)
    except ValueError:
        return None
    return value


def _validate_structured_view(view):
    """Check retained claims; original PDFs are verified only by the exporter."""
    from betaforge.analysis_report import SECTIONS, dated_endpoint, fields, render_markdown, text, validate_review
    from betaforge.financials import FORMULAS
    from betaforge.tools import unit_dimensions
    report, provenance = view["analysis"], view["provenance"]
    fields(report, ("schema_version", "analysis_date", "summary", "sections", "management_comparisons", "scenarios",
                    "probability_limits", "identity", "validation_status", "review_status"))
    if (type(report["schema_version"]) is not int or report["schema_version"] != 1 or
            report["analysis_date"] != view["analysis_date"] or report["summary"] != view["conclusion"] or
            report["validation_status"] != "syntax_and_identity_valid" or report["review_status"] != "unreviewed"):
        raise ValueError("Canonical analysis claims differ from saved view")
    analysis_hash = _saved_json_hash(report)
    if provenance.get("analysis_sha256") != analysis_hash or provenance["summary_sha256"] != analysis_hash:
        raise ValueError("Canonical analysis hash mismatch")
    if hashlib.sha256(view["narrative"].encode("utf-8")).hexdigest() != provenance["narrative_sha256"]:
        raise ValueError("Structured narrative hash mismatch")
    if view["narrative"] != render_markdown(report):
        raise ValueError("Structured narrative differs from canonical analysis")
    identity = report["identity"]
    fields(identity, ("packet_sha256", "database_sha256", "reports", "source_manifest_sha256"),
           ("analysis_contract", "benchmark_context", "market_benchmark_context"))
    for key in ("packet_sha256", "database_sha256", "source_manifest_sha256"):
        if not isinstance(identity[key], str) or not HASH.fullmatch(identity[key]):
            raise ValueError("Invalid canonical evidence identity")
    if any(identity[key] != provenance[key] for key in ("packet_sha256", "database_sha256")):
        raise ValueError("Canonical evidence identity differs from provenance")
    sources = {source["id"]: source for source in view["sources"]}
    if len(sources) != len(view["sources"]) or identity["reports"] != {
            identifier: [source["sha256"], source["prepared_sha256"]] for identifier, source in sources.items()}:
        raise ValueError("Canonical report sources differ from saved sources")
    records = view.get("saved_records")
    if not isinstance(records, list):
        raise ValueError("Canonical analysis requires saved reference records")
    by_id = {}
    for record in records:
        _source_record(record)
        if record["id"] in by_id:
            raise ValueError("Duplicate saved reference record")
        by_id[record["id"]] = record
        if record["id"].startswith("input:"):
            content = {key: value for key, value in record.items() if key != "id"}
            if record["id"] != "input:" + hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:20]:
                raise ValueError("Saved input content hash mismatch")
        if record.get("instrument_id", view["company"]["instrument_id"]) != view["company"]["instrument_id"]:
            raise ValueError("Saved reference belongs to another instrument")
        if record.get("report_id"):
            source = sources.get(record["report_id"])
            if source is None or type(record.get("page")) is not int or not 1 <= record["page"] <= source["pages"]:
                raise ValueError("Saved reference report page is unavailable")
    originals = {calc["id"]: calc for calc in view["original_calculations"]}
    if len(originals) != len(view["original_calculations"]):
        raise ValueError("Duplicate original calculation")
    for identifier, record in originals.items():
        content = {key: value for key, value in record.items() if key != "id"}
        if identifier != "calc:" + hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:20]:
            raise ValueError("Saved calculation content hash mismatch")
    expected_calculations = [_normalized_calculation(calc) for calc in originals.values() if calc["operation"] == "financial_formula"]
    if view["calculations"] != expected_calculations:
        raise ValueError("Named calculations differ from original trace")
    returns = [calc for calc in originals.values() if calc.get("formula") == "expected_cashflow_irr"]
    candidate = returns[0]["outputs"].get("irr_percent", {}).get("value") if len(returns) == 1 else None
    # Earlier structured exports left the comparator unselected despite retaining its context.
    if (view["benchmark"]["candidate_annualized_return_percent"] != candidate or
            view["benchmark"]["benchmark_annualized_return_percent"] not in
            (None, _historical_benchmark_return(view["benchmark"]["context"], view["analysis_date"])) or
            view["benchmark"]["difference_percentage_points"] is not None):
        raise ValueError("Benchmark must preserve the saved return without inventing a comparison")

    def reference(identifier):
        text(identifier, "reference", 200)
        match = re.fullmatch(r"([A-Za-z0-9_-]+):p([1-9]\d*)", identifier)
        if match:
            source = sources.get(match[1])
            if source is None or int(match[2]) > source["pages"]:
                raise ValueError("Reference page is unavailable")
            return
        if identifier not in by_id:
            raise ValueError("Analysis reference lacks its saved record")

    def references(values, required=True):
        if not isinstance(values, list) or len(values) > 100 or (required and not values):
            raise ValueError("Invalid canonical references")
        for identifier in values:
            reference(identifier)

    for record in by_id.values():
        base, separator, output = record["id"].partition("#")
        if base in originals:
            calc = originals[base]
            saved = calc.get("outputs", {}).get(output) if separator else {"value": calc["result"], "unit": calc["unit"]}
            if saved is None or record["value"] != saved["value"] or record["unit"] != saved["unit"] or record["scale"] != "1":
                raise ValueError("Saved calculation reference differs from original output")
    for calc in originals.values():
        for item in calc["inputs"]:
            reference(item["id"])
            retained = by_id[item["id"]]
            if {key: value for key, value in item.items() if key in SOURCE_RECORD_FIELDS} != retained:
                raise ValueError("Calculation input differs from retained source record")
    text(report["summary"], "summary")
    text(report["probability_limits"], "probability limits")
    sections = report["sections"]
    if not isinstance(sections, list) or len(sections) != 6 or {s.get("id") for s in sections if isinstance(s, dict)} != set(SECTIONS):
        raise ValueError("Invalid canonical analysis sections")
    for section in sections:
        fields(section, ("id", "title", "paragraphs"))
        text(section["title"], "section title", 300)
        if not isinstance(section["paragraphs"], list) or not 1 <= len(section["paragraphs"]) <= 50:
            raise ValueError("Invalid canonical paragraphs")
        for paragraph in section["paragraphs"]:
            fields(paragraph, ("kind", "text", "references"))
            if paragraph["kind"] not in {"fact", "interpretation", "assumption"}:
                raise ValueError("Invalid canonical paragraph kind")
            text(paragraph["text"], "paragraph")
            references(paragraph["references"])
    comparisons = report["management_comparisons"]
    if not isinstance(comparisons, list) or len(comparisons) > 100:
        raise ValueError("Invalid management comparisons")
    comparison_ids = set()
    for item in comparisons:
        fields(item, ("id", "metric_key", "metric_label", "relationship", "statement_type", "statement", "statement_date", "target_period", "basis", "actual", "actual_references", "references", "evidence"))
        if not re.fullmatch(r"[a-z0-9_-]+", text(item["id"], "management ID", 100)) or item["id"] in comparison_ids or item["metric_key"] not in FORMULAS:
            raise ValueError("Invalid management comparison identity")
        comparison_ids.add(item["id"])
        for key in ("metric_label", "statement", "basis"):
            text(item[key], key)
        for key in ("actual", "target_period"):
            if item[key] is not None:
                text(item[key], key)
        references(item["references"])
        references(item["actual_references"], item["actual"] is not None)
        if item["statement_date"] is not None:
            _date(item["statement_date"])
            if item["statement_date"] > view["analysis_date"]:
                raise ValueError("Management statement follows analysis date")
        if item["relationship"] not in {"direct", "related", "not_stated"} or item["statement_type"] not in {"target", "guidance", "driver", "not_stated"}:
            raise ValueError("Invalid management classification")
        if item["relationship"] == "not_stated" or item["statement_type"] == "not_stated":
            if item["relationship"] != "not_stated" or item["statement_type"] != "not_stated" or item["evidence"] is not None or item["statement_date"] is not None or not any(":p" in ref for ref in item["references"]):
                raise ValueError("Invalid explicit management absence")
        else:
            evidence = item["evidence"]
            fields(evidence, ("report_id", "page", "quote"))
            text(evidence["quote"], "source quote", 4000)
            if type(evidence["page"]) is not int or evidence["page"] <= 0:
                raise ValueError("Invalid management page")
            source_ref = f"{evidence['report_id']}:p{evidence['page']}"
            reference(source_ref)
            if source_ref not in item["references"]:
                raise ValueError("Management evidence lacks its page reference")
            published = sources[evidence["report_id"]]["published_at"]
            if item["statement_date"] != published:
                raise ValueError("Management statement date differs from source publication")
    scenarios = report["scenarios"]
    if not isinstance(scenarios, list) or len(scenarios) != 3 or {s.get("id") for s in scenarios if isinstance(s, dict)} != {"bear", "base", "bull"} or len(view["scenarios"]) != 3:
        raise ValueError("Invalid canonical scenarios")
    weights, endpoints = {}, set()
    for item, display in zip(scenarios, view["scenarios"]):
        fields(item, ("id", "name", "valuation_calculation_id", "present_value_date", "target_date", "rationale", "assumption_rationale", "references", "weight_ref", "probability_rationale", "present_value", "future_target"))
        for key in ("name", "rationale", "assumption_rationale", "probability_rationale"):
            text(item[key], key)
        references(item["references"])
        pv_date, target = (dated_endpoint(item[key]) for key in ("present_value_date", "target_date"))
        endpoints.add((target, item["target_date"]["precision"]))
        calc = originals.get(item["valuation_calculation_id"], {})
        if calc.get("formula") != "valuation_case" or item["present_value_date"] != {"value": view["analysis_date"], "precision": "day"}:
            raise ValueError("Invalid canonical valuation endpoint")
        years = next((r["calculation_value"] for r in calc["inputs"] if r["field"] == "years"), None)
        if years is None or int(target[:4]) - int(pv_date[:4]) != Decimal(years) or int(target[:4]) <= int(pv_date[:4]) or (len(target) > 4 and target[5:] != pv_date[5:len(target)]):
            raise ValueError("Scenario target differs from retained horizon")
        for key in ("present_value", "future_target"):
            fields(item[key], ("value", "unit"))
            output = calc["outputs"].get(key)
            if item[key] != output or unit_dimensions(output) != {"SEK": 1, "shares": -1} or Decimal(output["value"]) < 0:
                raise ValueError("Canonical scenario differs from retained valuation output")
        weight = by_id.get(item["weight_ref"], {})
        if weight.get("kind") != "assumption" or unit_dimensions(weight) or weight.get("value") is None:
            raise ValueError("Scenario lacks a saved probability assumption")
        weights[item["id"]] = _probability_value(weight)
        expected = {"id": item["id"], "name": item["name"], "value": item["present_value"]["value"], "unit": item["present_value"]["unit"],
                    "basis": calc["basis"], "calculation_ids": [calc["id"]], "weight": weights[item["id"]],
                    **{key: item[key] for key in ("present_value", "future_target", "present_value_date", "target_date")}}
        if display != expected:
            raise ValueError("Displayed scenario differs from canonical analysis")
    if len(endpoints) != 1 or sum(map(Decimal, weights.values())) != 1 or view["probability"] != {"weights": weights, "basis": report["probability_limits"], "status": "proposed"}:
        raise ValueError("Canonical probability claims differ from saved view")
    if "analysis_review" in view:
        review = validate_review(view["analysis_review"], provenance["packet_sha256"], analysis_hash)
        if _saved_json_hash(review) != provenance["review_sha256"]:
            raise ValueError("Independent review hash mismatch")
    elif provenance["review_sha256"] is not None:
        raise ValueError("Independent review hash requires its retained review")
    if "reader_memo" in view:
        _validate_reader_memo(view["reader_memo"], view, references)


def build_structured_saved_view(run_dir, packet_dir, company_name, ticker, view_id, method):
    """Export a submitted structured run after verifying all frozen evidence."""
    from betaforge.analysis_report import references as validate_references, render_markdown, validate_saved_report, validate_review
    from betaforge.tools import EvidenceTools
    run_dir, packet_dir = map(checked_path, (run_dir, packet_dir))
    run_body, analysis_body = (_body(run_dir / name) for name in ("run.json", "analysis.json"))
    run, report = map(_decode, (run_body, analysis_body))
    analysis_hash = hashlib.sha256(analysis_body).hexdigest()
    if not isinstance(run, dict) or run.get("status") != "completed" or run.get("smoke") is not False or run.get("structured") is not True or run.get("analysis_sha256") != analysis_hash:
        raise ValueError("Export requires a completed non-smoke structured run with bound analysis")
    state = _json(run_dir / "tool-state.json")
    if not isinstance(state, dict) or any(not isinstance(state.get(name), dict) for name in ("inputs", "calculations")):
        raise ValueError("Structured tool state requires input and calculation mappings")
    original_bodies = {name: _body(run_dir / (name + ".json")) for name in ("inputs", "calculations")}
    originals = {name: _decode(body) for name, body in original_bodies.items()}
    for name, body in original_bodies.items():
        if run.get(name + "_sha256") != hashlib.sha256(body).hexdigest() or originals[name] != list(state.get(name, {}).values()):
            raise ValueError("Structured artifact differs from saved run/state: " + name)
    if state.get("analysis_sha256") != analysis_hash:
        raise ValueError("Structured analysis differs from tool state")
    with TemporaryDirectory() as temporary:
        tools = EvidenceTools(checked_path(packet_dir / "packet.json"), temporary, structured=True)
        try:
            if run.get("identity") != tools.identity or state.get("identity") != tools.identity:
                raise ValueError("Structured evidence identity differs from run/tool state")
            tools.state = state
            if not tools.coverage()["complete"] or run.get("coverage") != tools.coverage():
                raise ValueError("Structured reading coverage differs from completed run")
            validate_saved_report(report, tools)
            packet, identity = tools.packet, tools.identity
            review_path = run_dir / "analysis-review.json"
            review = validate_review(_json(review_path), identity["packet_sha256"], analysis_hash) if review_path.exists() else None
            report_manifest = _json(checked_path(tools.report_dir / "source-manifest.json"))
            if report_manifest.get("borsdata_instrument_id") != packet["instrument_id"]:
                raise ValueError("Report manifest instrument differs from packet")
            manifest_entries = {item["report_id"]: item for item in report_manifest["documents"]}
            if len(manifest_entries) != len(report_manifest["documents"]) or set(manifest_entries) != set(tools.reports):
                raise ValueError("Report manifest must uniquely match all prepared sources")
            sources = []
            for item in tools.index["reports"]:
                original = manifest_entries[item["report_id"]]
                if original["sha256"] != item["source_sha256"] or original.get("borsdata_instrument_id", packet["instrument_id"]) != packet["instrument_id"]:
                    raise ValueError("Manifest source differs from verified report")
                sources.append({"id": item["report_id"], "title": original.get("title") or item["report_id"],
                                "period": original.get("reporting_period", {"start": None, "end": None}),
                                "published_at": original.get("publication_date"), "url": original.get("source_url"),
                                "sha256": item["source_sha256"], "prepared_sha256": item["prepared_sha256"], "pages": item["pages"]})
            references = set(state["inputs"])
            for calc in originals["calculations"]:
                references.update(item["id"] for item in calc["inputs"])
            for section in report["sections"]:
                for paragraph in section["paragraphs"]:
                    references.update(paragraph["references"])
            for item in report["management_comparisons"]:
                references.update(item["references"] + item["actual_references"])
            for item in report["scenarios"]:
                references.update(item["references"] + [item["weight_ref"]])
            if review is not None:
                for finding in review["findings"]:
                    saved_references = [identifier for identifier in finding["references"]
                                        if identifier.startswith(("obs_", "input:", "calc:")) or
                                        re.fullmatch(r"[A-Za-z0-9_-]+:p\d+", identifier)]
                    validate_references(saved_references, tools)
                    references.update(saved_references)
            records = []
            for identifier in sorted(references):
                if re.fullmatch(r"[A-Za-z0-9_-]+:p[1-9]\d*", identifier):
                    continue
                if identifier in state["calculations"]:
                    calc = state["calculations"][identifier]
                    record = {"id": identifier, "value": calc["result"], "unit": calc["unit"], "scale": "1", "kind": "calculation",
                              **{key: calc[key] for key in ("period_start", "period_end", "report_type") if key in calc}}
                else:
                    record = tools.resolve_input(identifier)
                records.append({key: value for key, value in record.items() if key in SOURCE_RECORD_FIELDS})
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
                    raise ValueError("Frozen price belongs to another instrument")
                price = {key: saved_price.get(key) for key in PRICE_FIELDS}
                price["date"] = saved_price.get("date", saved_price.get("period_end"))
            benchmark = dict.fromkeys(BENCHMARK_FIELDS)
            benchmark["limits"] = ["Saved expected return and historical benchmark context are not a forecast comparison."]
            returns = [calc for calc in originals["calculations"] if calc.get("formula") == "expected_cashflow_irr"]
            if len(returns) == 1:
                benchmark["candidate_annualized_return_percent"] = returns[0]["outputs"].get("irr_percent", {}).get("value")
            benchmark_entry = packet.get("market_benchmark_context", packet.get("benchmark_context"))
            if benchmark_entry:
                saved_context = _json(_child(packet_dir, benchmark_entry["context_path"]))
                benchmark["context"] = {key: value for key, value in saved_context.items() if key in CONTEXT_FIELDS}
            benchmark["benchmark_annualized_return_percent"] = _historical_benchmark_return(
                benchmark["context"], packet["analysis_date"])
        finally:
            tools.store.close()
    probabilities = {item["id"]: _probability_value(state["inputs"][item["weight_ref"]]) for item in report["scenarios"]}
    calculations = {calc["id"]: calc for calc in originals["calculations"]}
    scenarios = [{"id": item["id"], "name": item["name"], "value": item["present_value"]["value"], "unit": item["present_value"]["unit"],
                  "basis": calculations[item["valuation_calculation_id"]]["basis"], "calculation_ids": [item["valuation_calculation_id"]],
                  "weight": probabilities[item["id"]], **{key: item[key] for key in ("present_value", "future_target", "present_value_date", "target_date")}} for item in report["scenarios"]]
    narrative_body = _body(run_dir / "answer.md")
    if narrative_body.decode("utf-8") != render_markdown(report):
        raise ValueError("Structured narrative differs from canonical analysis")
    view = {"schema_version": 1, "id": view_id, "company": {"name": company_name, "ticker": ticker, "instrument_id": packet["instrument_id"]},
            "analysis_date": packet["analysis_date"], "reviewed_at": run["finished_at"], "method": method, "price": price,
            "conclusion": report["summary"], "scenarios": scenarios, "probability": {"weights": probabilities, "basis": report["probability_limits"], "status": "proposed"},
            "calculations": [_normalized_calculation(calc) for calc in originals["calculations"] if calc["operation"] == "financial_formula"],
            "original_calculations": originals["calculations"], "interpretation": [], "notes": [], "narrative": narrative_body.decode("utf-8"),
            "sources": sources, "benchmark": benchmark, "analysis": report, "saved_records": records,
            "provenance": {"database_sha256": identity["database_sha256"], "packet_sha256": identity["packet_sha256"], "review_sha256": None,
                           "run_sha256": hashlib.sha256(run_body).hexdigest(), "summary_sha256": analysis_hash, "analysis_sha256": analysis_hash,
                           "narrative_sha256": hashlib.sha256(narrative_body).hexdigest(),
                           **{key: run.get(key) for key in ("model", "reasoning_effort", "status", "started_at", "finished_at", "coverage")}}}
    if review is not None:
        view["analysis_review"] = review
        view["provenance"]["review_sha256"] = _saved_json_hash(review)
    return validate_saved_view(view)


def build_saved_view(review_path, run_dir, packet_dir, company_name, ticker, view_id, method):
    """Copy one reviewed, completed run after checking its preserved identities."""
    if review_path is None:
        return build_structured_saved_view(run_dir, packet_dir, company_name, ticker, view_id, method)
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
