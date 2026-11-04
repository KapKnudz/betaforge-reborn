"""Publish a company packet with frozen evidence and explicit analysis rules."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from betaforge.storage import EvidenceStore


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initial_context(store, resolution, instrument_id, analysis_date):
    fields = ["net_Sales", "operating_Income", "profit_To_Equity_Holders", "earnings_Per_Share",
              "cash_Flow_From_Operating_Activities", "cash_Flow_From_Investing_Activities",
              "free_Cash_Flow", "net_Debt", "total_Equity", "number_Of_Shares"]
    compact = []
    for family in ("year", "quarter", "r12"):
        rows = store.query_financials(instrument_id, report_type=family, fields=fields, limit=5000)
        rows = [row for row in rows if not row.get("period_end") or row["period_end"] <= analysis_date]
        periods = sorted({(r["year"], r["period"]) for r in rows}, reverse=True)
        selected = set(periods if family == "year" else periods[:8 if family == "quarter" else 1])
        for row in rows:
            if (row["year"], row["period"]) in selected:
                compact.append({k: row.get(k) for k in ("id", "metric", "value", "unit", "scale", "currency",
                                                       "report_type", "year", "period", "period_start", "period_end",
                                                       "provider_report_date", "source_first_captured_at",
                                                       "source_last_successful_check_at")})
    prices = store.query_financials(instrument_id, report_type="price", fields=["price_close"], limit=5000)
    latest = next(([row] for row in prices if row.get("period_end") and row["period_end"] <= analysis_date), [])
    if not latest or latest[0].get("value") is None or not latest[0].get("currency"):
        raise ValueError("Company packet needs a dated closing price with verified quote currency on or before the analysis date")
    definitions = [dict(row) for row in store.connection.execute(
        "SELECT DISTINCT metric,report_type FROM observations WHERE instrument_id=? ORDER BY metric,report_type", (instrument_id,))]
    return ("FROZEN FINANCIAL FOUNDATION\nValues below retain source scales. The calculation tool normalizes "
            "stored observations to base units by applying scale. Missing/ambiguous provider units must be resolved "
            "before arithmetic. The source-specific values remain distinct from issuer-report inputs. "
            "Period dates, provider_report_date and source capture/check dates have different meanings. "
            "provider_report_date is the supplied report_Date, with publication meaning unverified. "
            "Source checks confirm retrieval of a payload; definition validation is separate. Unknown dates stay null.\n" +
            json.dumps({"financials": compact, "latest_close": latest, "available_metrics": definitions}, ensure_ascii=False) +
            "\nMAPPING DECISIONS AND SOURCE DIFFERENCES\n" + resolution)


def copy_contract(destination):
    directory = destination / "analysis-contract"
    directory.mkdir()
    contract, texts = {}, []
    for role, name in (("policy", "analysis-policy.md"), ("calculations", "calculations.md")):
        body = (ROOT / "docs" / name).read_bytes()
        target = directory / name
        target.write_bytes(body)
        contract[role] = {"path": target.relative_to(destination).as_posix(), "sha256": digest(target)}
        texts.append("\nFROZEN ANALYSIS " + role.upper() + "\n" + body.decode("utf-8"))
    return contract, "".join(texts)


def relative_source(base, value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Invalid benchmark source path")
    relative = Path(value)
    path = (base / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not path.is_relative_to(base):
        raise ValueError("Benchmark source path escapes its context directory")
    return path


def copy_benchmarks(context_path, destination):
    context_path = Path(context_path).resolve()
    base = context_path.parent
    context_body = context_path.read_bytes()
    context = json.loads(context_body)
    manifest_path = relative_source(base, context["manifest"])
    manifest_body = manifest_path.read_bytes()
    if hashlib.sha256(manifest_body).hexdigest() != context["manifest_sha256"]:
        raise ValueError("Benchmark manifest hash mismatch")
    manifest = json.loads(manifest_body)
    if context.get("schema_version") != 1 or manifest.get("schema_version") != 1 or manifest.get("status") != "complete":
        raise ValueError("Benchmark context needs a complete version-1 source manifest")
    sources = {item["id"]: item for item in manifest["sources"]}
    files = {Path("context.json"): (context_path, hashlib.sha256(context_body).hexdigest()),
             Path(context["manifest"]): (manifest_path, context["manifest_sha256"])}
    for dataset in context["datasets"]:
        raw = relative_source(base, dataset["raw_file"])
        source = sources.get(dataset["id"])
        if (not source or source["file"] != dataset["raw_file"] or
                source["sha256"] != dataset["raw_sha256"] or digest(raw) != dataset["raw_sha256"]):
            raise ValueError("Benchmark workbook identity mismatch")
        relative = Path(dataset["raw_file"])
        if relative.parts[0] != "raw" or relative.suffix.lower() not in {".xls", ".xlsx"}:
            raise ValueError("Benchmark source must be a referenced raw workbook")
        if relative in files:
            raise ValueError("Duplicate benchmark source path")
        files[relative] = (raw, dataset["raw_sha256"])
    folder = destination / "benchmarks"
    metadata = {"context_path": "benchmarks/context.json", "files": []}
    for relative, (source, expected) in sorted(files.items()):
        target = folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if digest(target) != expected:
            raise ValueError("Copied benchmark hash mismatch")
        metadata["files"].append({"path": target.relative_to(destination).as_posix(), "sha256": expected})
    return metadata, ("\nSELECTED INDUSTRY CONTEXT — source observations, not company facts or automatic target multiples\n" +
                      (folder / "context.json").read_text())


def copy_market_benchmark(context_path, destination, analysis_date=None):
    """Freeze one sourced market return; do not acquire data during packet creation."""
    context_path = Path(context_path).resolve()
    base = context_path.parent
    context = json.loads(context_path.read_text())
    benchmark = context.get('benchmark',{})
    if benchmark.get('symbol') != 'SIXRX' or benchmark.get('currency') != 'SEK' or benchmark.get('return_type') != 'gross_total_return':
        raise ValueError('Market benchmark must be the adopted SIXRX SEK gross total-return series')
    if analysis_date is not None and context.get('analysis_date') != analysis_date:
        raise ValueError('Market benchmark analysis date does not match the company packet')
    manifest_path = relative_source(base, context['manifest'])
    if digest(manifest_path) != context['manifest_sha256']:
        raise ValueError('Market benchmark manifest hash mismatch')
    manifest = json.loads(manifest_path.read_text())
    if (context.get('schema_version') != 1 or manifest.get('schema_version') != 1 or
            context.get('status') != 'verified_from_rounded_public_levels' or manifest.get('series') != benchmark['symbol'] or
            manifest.get('analysis_date') != context.get('analysis_date')):
        raise ValueError('Market benchmark requires a verified version-1 context and matching source manifest')
    files = {Path('context.json'): context_path, Path(context['manifest']): manifest_path}
    for source in manifest['sources']:
        raw = relative_source(base, source['file'])
        relative = Path(source['file'])
        if relative.parts[0] != 'raw' or digest(raw) != source['sha256']:
            raise ValueError('Market benchmark raw source identity mismatch')
        if relative in files:
            raise ValueError('Duplicate market benchmark source path')
        files[relative] = raw
    script = manifest.get('calculation_script')
    if script:
        source = relative_source(base,script['file'])
        if script['file'] != 'calculation.py' or digest(source) != script['sha256']:
            raise ValueError('Market benchmark calculation script identity mismatch')
        files[Path(script['file'])] = source
    metadata = {'context_path':'market-benchmark/context.json', 'files':[]}
    for relative, source in sorted(files.items()):
        target = destination / 'market-benchmark' / relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        if digest(target) != digest(source):
            raise ValueError('Copied market benchmark hash mismatch')
        metadata['files'].append({'path':target.relative_to(destination).as_posix(),'sha256':digest(target)})
    return metadata, '\nVERIFIED MARKET TOTAL-RETURN CONTEXT — historical comparison, separate from discount rate\n'+context_path.read_text()


def prepare(snapshots, destination, db_path, facts_path, reports_base, *, analysis_date,
            instrument_id, prompt_path, extra_facts=(), resolution_path=None, benchmark_context=None,
            market_benchmark_context=None):
    if type(instrument_id) is not int or instrument_id <= 0:
        raise ValueError("Instrument ID must be a positive integer")
    if not isinstance(analysis_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", analysis_date):
        raise ValueError("Analysis date must be explicit YYYY-MM-DD")
    date.fromisoformat(analysis_date)
    reports_base = Path(reports_base).resolve()
    primary_facts = Path(facts_path).resolve() if facts_path is not None else None
    additional_facts = [Path(path).resolve() for path in extra_facts]
    fact_paths = ([primary_facts] if primary_facts else []) + additional_facts
    for path in fact_paths:
        fact_instrument = json.loads(path.read_text()).get("instrument_id")
        if type(fact_instrument) is not int or fact_instrument != instrument_id:
            raise ValueError("Report fact instrument does not match the packet")
    if prompt_path is None:
        raise ValueError("An explicit company analysis prompt is required")
    prompt_path = Path(prompt_path)
    if resolution_path is None:
        resolution = "No company-specific mapping note supplied. Verify material source definitions."
    else:
        resolution = Path(resolution_path).read_text()
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError("Packet destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".prepare-", dir=destination.parent))
    try:
        index_path = reports_base / "prepared/index.json"
        index = json.loads(index_path.read_text())
        copied = temporary / "reports"
        (copied / "prepared").mkdir(parents=True)
        (copied / "sources").mkdir()
        for report in index["reports"]:
            rid = report["report_id"]
            if not re.fullmatch(r"[a-z0-9-]+", rid):
                raise ValueError("Unsafe report identifier")
            for folder, suffix, hash_key in (("sources", ".pdf", "source_sha256"),
                                            ("prepared", ".json", "prepared_sha256")):
                source = reports_base / folder / (rid + suffix)
                target = copied / folder / source.name
                shutil.copyfile(source, target)
                if digest(target) != report[hash_key]:
                    raise ValueError("Report corpus differs from the fixed source hashes")
        shutil.copyfile(index_path, copied / "prepared/index.json")
        shutil.copyfile(reports_base / "source-manifest.json", copied / "source-manifest.json")
        (temporary / "mapping-resolution.md").write_text(resolution)
        if primary_facts:
            shutil.copyfile(primary_facts, temporary / "reconciled-facts.json")
        extra_metadata = []
        for position, source in enumerate(additional_facts, 1):
            target = temporary / "extra-report-facts" / f"{position:03d}-{source.name}"
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, target)
            extra_metadata.append({"path": target.relative_to(temporary).as_posix(), "sha256": digest(target)})
        shutil.copyfile(prompt_path, temporary / "prompt.md")
        contract, contract_text = copy_contract(temporary)
        benchmark_metadata, benchmark_text = (copy_benchmarks(benchmark_context, temporary) if benchmark_context else (None, ""))
        market_metadata, market_text = (copy_market_benchmark(market_benchmark_context,temporary,analysis_date) if market_benchmark_context else (None,''))
        with EvidenceStore(db_path) as store:
            for snapshot in snapshots:
                print(json.dumps(store.ingest_snapshot(snapshot)), flush=True)
            for path in fact_paths:
                print(json.dumps(store.add_report_facts(path)), flush=True)
            store.validate_report_links({r["report_id"]: r for r in index["reports"]}, instrument_id=instrument_id)
            context = initial_context(store, resolution, instrument_id, analysis_date) + contract_text + benchmark_text + market_text
            store.freeze(temporary / "snapshot")
        packet = {"instrument_id": instrument_id, "analysis_date": analysis_date,
                  "snapshot_dir": "snapshot", "reports_dir": "reports",
                  "required_reports": [r["report_id"] for r in index["reports"]],
                  "analysis_contract": contract, "extra_report_facts": extra_metadata,
                  "context": context,
                  "prompt_sha256": digest(temporary / "prompt.md"),
                  "mapping_resolution_sha256": digest(temporary / "mapping-resolution.md")}
        if benchmark_metadata:
            packet["benchmark_context"] = benchmark_metadata
        if market_metadata:
            packet['market_benchmark_context'] = market_metadata
        (temporary / "packet.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False))
        temporary.rename(destination)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return destination / "packet.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshots", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--db", type=Path, default=ROOT / "data/evidence/evidence.sqlite3")
    parser.add_argument("--facts", type=Path, help="Optional curated report facts for the selected company")
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--instrument", "--instrument-id", dest="instrument_id", type=int, required=True)
    parser.add_argument("--analysis-date", required=True, help="Explicit analysis date, YYYY-MM-DD; source capture dates remain separate")
    parser.add_argument("--extra-facts", action="append", type=Path, default=[])
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--mapping-resolution", type=Path)
    parser.add_argument("--benchmark-context", type=Path)
    parser.add_argument('--market-benchmark-context',type=Path)
    args = parser.parse_args()
    print("Packet:", prepare(args.snapshots, args.output, args.db, args.facts, args.reports,
                             instrument_id=args.instrument_id, analysis_date=args.analysis_date,
                             extra_facts=args.extra_facts, prompt_path=args.prompt,
                             resolution_path=args.mapping_resolution, benchmark_context=args.benchmark_context,
                             market_benchmark_context=args.market_benchmark_context))


if __name__ == "__main__":
    main()
