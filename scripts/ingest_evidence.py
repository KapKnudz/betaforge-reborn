"""Ingest saved, credential-free acquisitions and freeze a local evidence snapshot."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from betaforge.storage import EvidenceStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshots", nargs="*", type=Path)
    parser.add_argument("--db", type=Path, default=ROOT / "data/evidence/evidence.sqlite3")
    parser.add_argument("--facts", action="append", default=[], type=Path)
    parser.add_argument("--freeze", type=Path)
    args = parser.parse_args()
    with EvidenceStore(args.db) as store:
        for snapshot in args.snapshots:
            print(json.dumps(store.ingest_snapshot(snapshot)))
        for path in args.facts:
            print(json.dumps(store.add_report_facts(path)))
        if args.freeze:
            print(json.dumps({"frozen": str(store.freeze(args.freeze))}))
        print(json.dumps(store.stats()))


if __name__ == "__main__":
    main()
