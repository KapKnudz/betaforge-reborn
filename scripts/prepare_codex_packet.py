"""Publish a self-contained Gränges packet with frozen numbers, PDFs and page text."""
import argparse
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


def initial_context(store, resolution):
    fields = ["net_Sales", "operating_Income", "profit_To_Equity_Holders", "earnings_Per_Share",
              "cash_Flow_From_Operating_Activities", "cash_Flow_From_Investing_Activities",
              "free_Cash_Flow", "net_Debt", "total_Equity", "number_Of_Shares"]
    compact = []
    for family in ("year", "quarter", "r12"):
        rows = store.query_financials(426, report_type=family, fields=fields, limit=5000)
        periods = sorted({(r["year"], r["period"]) for r in rows}, reverse=True)
        selected = set(periods if family == "year" else periods[:8 if family == "quarter" else 1])
        for row in rows:
            if (row["year"], row["period"]) in selected:
                compact.append({k: row.get(k) for k in ("id", "metric", "value", "unit", "scale", "currency",
                                                       "report_type", "year", "period", "period_end")})
    latest = store.query_financials(426, report_type="price", fields=["price_close"], limit=1)
    if not latest or latest[0].get("value") is None or not latest[0].get("currency"):
        raise ValueError("Gränges packet needs a dated closing price with verified quote currency")
    definitions = [dict(row) for row in store.connection.execute(
        "SELECT DISTINCT metric,report_type FROM observations WHERE instrument_id=426 ORDER BY metric,report_type")]
    return ("FROZEN FINANCIAL FOUNDATION\nValues below retain source scales. The calculation tool normalizes "
            "stored observations to base units by applying scale. Missing/ambiguous provider units must be resolved "
            "before arithmetic. The source-specific values remain distinct from issuer-report inputs.\n" +
            json.dumps({"financials": compact, "latest_close": latest, "available_metrics": definitions}, ensure_ascii=False) +
            "\nMAPPING DECISIONS AND SOURCE DIFFERENCES\n" + resolution)


def prepare(snapshots, destination, db_path, facts_path, reports_base):
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
        resolution_path = ROOT / "docs/research/granges-mapping-resolution.md"
        resolution = resolution_path.read_text()
        (temporary / "mapping-resolution.md").write_text(resolution)
        shutil.copyfile(facts_path, temporary / "reconciled-facts.json")
        prompt_path = ROOT / "data/granges-walkthrough/codex-questions.md"
        shutil.copyfile(prompt_path, temporary / "prompt.md")
        with EvidenceStore(db_path) as store:
            for snapshot in snapshots:
                print(json.dumps(store.ingest_snapshot(snapshot)), flush=True)
            print(json.dumps(store.add_report_facts(facts_path)), flush=True)
            store.validate_report_links({r["report_id"]: r for r in index["reports"]})
            context = initial_context(store, resolution)
            store.freeze(temporary / "snapshot")
        packet = {"instrument_id": 426, "analysis_date": "2026-11-01",
                  "snapshot_dir": "snapshot", "reports_dir": "reports",
                  "required_reports": [r["report_id"] for r in index["reports"]],
                  "context": context,
                  "prompt_sha256": digest(temporary / "prompt.md"),
                  "mapping_resolution_sha256": digest(temporary / "mapping-resolution.md")}
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
    parser.add_argument("--facts", type=Path, default=ROOT / "data/granges-walkthrough/reconciled-facts.json")
    parser.add_argument("--reports", type=Path, default=ROOT / "data/granges-walkthrough")
    args = parser.parse_args()
    print("Packet:", prepare(args.snapshots, args.output, args.db, args.facts, args.reports))


if __name__ == "__main__":
    main()
