"""Prepare an unchanged, page-addressable text corpus from the saved originals."""
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/granges-walkthrough"


def clean(text):
    # Preserve line order; do not remove headers, notes, or numeric values.
    return re.sub(r"\n{3,}", "\n\n", "\n".join(line.rstrip() for line in text.splitlines())).strip()


def prepare():
    manifest = json.loads((BASE / "source-manifest.json").read_text())
    dest = BASE / "prepared"
    dest.mkdir(exist_ok=True)
    reports = []
    corpus = []
    for doc in manifest["documents"]:
        source = ROOT / doc["local_path"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == doc["sha256"]
        reader = PdfReader(source)
        assert len(reader.pages) == doc["page_count"]
        pages = []
        for number, page in enumerate(reader.pages, 1):
            text = clean(page.extract_text() or "")
            pages.append({"page": number, "text": text})
            corpus.append(f"\n=== {doc['report_id']} | PDF PAGE {number} ===\n{text}\n=== END PAGE ===\n")
        content = json.dumps(pages, ensure_ascii=False, indent=2)
        (dest / f"{doc['report_id']}.json").write_text(content)
        reports.append({
            "report_id": doc["report_id"], "pages": len(pages),
            "characters": sum(len(p["text"]) for p in pages),
            "words": sum(len(p["text"].split()) for p in pages),
            "low_text_pages": [p["page"] for p in pages if len(p["text"]) < 100],
            "source_sha256": doc["sha256"],
            "prepared_sha256": hashlib.sha256(content.encode()).hexdigest(),
        })
        print(json.dumps(reports[-1]), flush=True)
    full = "".join(corpus)
    (dest / "corpus.txt").write_text(full)
    summary = {"extractor": "pypdf native text, default reading order", "reports": reports,
               "total_pages": sum(r["pages"] for r in reports),
               "total_characters": len(full), "total_words": len(full.split()),
               "corpus_sha256": hashlib.sha256(full.encode()).hexdigest(),
               "limits": "Native text only. Images/charts remain in PDFs. Empty-page and visual QA required; this is not proof of semantic fidelity."}
    (dest / "index.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k != "reports"}), flush=True)


if __name__ == "__main__":
    assert clean("A  B  \n\n\n10  20\n") == "A  B\n\n10  20"
    prepare()
