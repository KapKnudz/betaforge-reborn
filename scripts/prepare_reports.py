"""Prepare page-linked native text from an explicit, preserved report corpus."""
import argparse
from datetime import date
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import tempfile

from pypdf import PdfReader


def clean(text):
    # Preserve line order, headers, notes and numeric values.
    return re.sub(r"\n{3,}", "\n\n", "\n".join(line.rstrip() for line in text.splitlines())).strip()


def regular_source(base, value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Invalid report source path")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Report source path must stay inside its corpus")
    path = base
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Report source path must not contain symlinks")
    if not path.resolve().is_relative_to(base) or not path.is_file():
        raise ValueError("Report source must be a contained regular file")
    return path


def prepare(reports_base):
    base = Path(reports_base).resolve()
    destination = base / "prepared"
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Prepared report corpus already exists")
    manifest = json.loads(regular_source(base, "source-manifest.json").read_text(encoding="utf-8"))
    documents = manifest.get("documents") if isinstance(manifest, dict) else None
    if not isinstance(documents, list) or not documents:
        raise ValueError("Report manifest needs a nonempty documents list")
    seen = set()
    for doc in documents:
        rid = doc.get("report_id") if isinstance(doc, dict) else None
        if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", rid):
            raise ValueError("Unsafe report identifier")
        if rid in seen:
            raise ValueError("Duplicate report identifier")
        seen.add(rid)
        if doc.get("local_path") != f"sources/{rid}.pdf":
            raise ValueError("Report source must be sources/<report_id>.pdf")
        if not isinstance(doc.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", doc["sha256"]):
            raise ValueError("Report needs a SHA-256 hash")
        if type(doc.get("page_count")) is not int or doc["page_count"] <= 0:
            raise ValueError("Report needs a positive page count")
        publication = doc.get("publication_date")
        if publication is not None:
            if not isinstance(publication, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", publication):
                raise ValueError("Report publication date must be YYYY-MM-DD")
            date.fromisoformat(publication)
        if "reporting_period" in doc:
            period = doc["reporting_period"]
            if not isinstance(period, dict) or set(period) != {"start", "end"}:
                raise ValueError("Report reporting_period must contain exactly start and end")
            for field in ("start", "end"):
                value = period.get(field)
                if value is not None:
                    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                        raise ValueError("Reporting period dates must be YYYY-MM-DD")
                    date.fromisoformat(value)
            if period.get("start") is not None and period.get("end") is not None and period["start"] > period["end"]:
                raise ValueError("Reporting period start must not follow its end")
    temporary = Path(tempfile.mkdtemp(prefix=".prepare-reports-", dir=base))
    try:
        reports, corpus = [], []
        for doc in documents:
            source = regular_source(base, doc["local_path"])
            body = source.read_bytes()
            if hashlib.sha256(body).hexdigest() != doc["sha256"]:
                raise ValueError("Report source hash mismatch: " + doc["report_id"])
            reader = PdfReader(BytesIO(body))
            if len(reader.pages) != doc["page_count"]:
                raise ValueError("Report page count mismatch: " + doc["report_id"])
            pages = []
            for number, page in enumerate(reader.pages, 1):
                text = clean(page.extract_text() or "")
                pages.append({"page": number, "text": text})
                corpus.append(f"\n=== {doc['report_id']} | PDF PAGE {number} ===\n{text}\n=== END PAGE ===\n")
            content = json.dumps(pages, ensure_ascii=False, indent=2).encode("utf-8")
            (temporary / f"{doc['report_id']}.json").write_bytes(content)
            reports.append({
                "report_id": doc["report_id"], "pages": len(pages),
                "characters": sum(len(p["text"]) for p in pages),
                "words": sum(len(p["text"].split()) for p in pages),
                "low_text_pages": [p["page"] for p in pages if len(p["text"]) < 100],
                "source_sha256": doc["sha256"],
                "prepared_sha256": hashlib.sha256(content).hexdigest(),
            })
        full = "".join(corpus).encode("utf-8")
        (temporary / "corpus.txt").write_bytes(full)
        summary = {
            "extractor": "pypdf native text, default reading order", "reports": reports,
            "total_pages": sum(r["pages"] for r in reports),
            "total_characters": len(full.decode("utf-8")), "total_words": len(full.decode("utf-8").split()),
            "corpus_sha256": hashlib.sha256(full).hexdigest(),
            "limits": "Native text only. Images/charts remain in PDFs. Empty-page and visual QA required; this is not proof of semantic fidelity.",
        }
        (temporary / "index.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("Prepared report corpus already exists")
        temporary.rename(destination)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return destination / "index.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True, help="Corpus root containing source-manifest.json and sources/")
    args = parser.parse_args()
    print("Prepared reports:", prepare(args.reports))


if __name__ == "__main__":
    main()
