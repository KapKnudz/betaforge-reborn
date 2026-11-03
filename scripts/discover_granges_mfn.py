"""Verify public MFN discovery for the frozen Gränges corpus; never replace sources.

Uses the pagination URL pattern exposed by MFN's public Show more JavaScript.
Downloads PDF bytes only in memory to compare SHA-256 with the saved originals.
"""
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/granges-walkthrough"
ARCHIVE = "https://mfn.se/all/a/granges"
PAGINATION_SOURCE = "https://mfn.se/assets/js/show-more_6IEBXRx0.js"
SLUGS = {
    "granges-annual-2021": "granges-publishes-the-annual-and-sustainability-report-for-2021",
    "granges-annual-2022": "granges-publishes-annual-and-sustainability-report-2022",
    "granges-annual-2023": "granges-publishes-annual-and-sustainability-report-2023",
    "granges-annual-2024": "granges-publishes-annual-and-sustainability-report-2024",
    "granges-annual-2025": "annual-and-sustainability-report-2025",
    "granges-q1-2026": "granges-q1-interim-report-record-first-quarter-and-strong-momentum",
    "granges-h1-2026": "granges-half-year-report-2026-strong-execution-drives-record-volume-and-earnings",
    "granges-q3-2026": "granges-q3-interim-report-2026-record-earnings-and-improved-cash-flow",
}


def fetch(url):
    with urlopen(url, timeout=45) as response:
        return response.read(), response.geturl()


def links(text):
    return list(dict.fromkeys(html.unescape(value) for value in re.findall(r'href=["\']([^"\']+)', text)))


def main():
    manifest_bytes = (DATA / "source-manifest.json").read_bytes()
    original = {row["report_id"]: row for row in json.loads(manifest_bytes)["documents"]}
    found = {}
    archive_pages = []
    errors = []
    for offset in range(0, 241, 48):
        url = ARCHIVE if offset == 0 else f"{ARCHIVE}.html?offset={offset}&limit=48"
        try:
            raw, resolved = fetch(url)
            archive_pages.append({"url": url, "resolved_url": resolved, "sha256": hashlib.sha256(raw).hexdigest()})
            hrefs = links(raw.decode("utf8"))
            for report_id, slug in SLUGS.items():
                matches = [link for link in hrefs if link == f"/a/granges/{slug}"]
                if matches:
                    found[report_id] = {"release_url": urljoin(ARCHIVE, matches[0]), "discovered_on": url}
        except Exception as error:
            errors.append({"url": url, "error": str(error)})
        if len(found) == len(SLUGS):
            break
    documents = []
    for report_id in SLUGS:
        saved = original[report_id]
        row = {"report_id": report_id, "saved_issuer_pdf_url": saved["source_url"], "saved_pdf_sha256": saved["sha256"], "saved_publication_date": saved["publication_date"], "initial_acquisition": "issuer_ir_direct", "attachments": []}
        documents.append(row)
        if report_id not in found:
            row["status"] = "not_discovered_within_bounded_archive_scan"
            continue
        row.update(found[report_id])
        try:
            raw, row["resolved_release_url"] = fetch(row["release_url"])
            text = raw.decode("utf8")
            row["release_html_sha256"] = hashlib.sha256(raw).hexdigest()
            metadata = [json.loads(value) for value in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)]
            article = next(value for value in metadata if value.get("@type") == "NewsArticle")
            row["release_title"] = article["headline"]
            row["published_at_utc"] = article["datePublished"]
            row["publication_date_matches_saved"] = article["datePublished"][:10] == saved["publication_date"]
            row["release_metadata_source"] = "NewsArticle JSON-LD datePublished and headline in public release HTML"
            pdfs = [url for url in links(text) if url.startswith("https://storage.mfn.se/") and url.lower().split("?")[0].endswith(".pdf")]
            for url in pdfs:
                attachment = {"url": url, "linked_from_release_html": True, "url_matches_saved_issuer_pdf_url": url == saved["source_url"]}
                row["attachments"].append(attachment)
                try:
                    pdf, resolved = fetch(url)
                    digest = hashlib.sha256(pdf).hexdigest()
                    attachment.update(resolved_url=resolved, size_bytes=len(pdf), pdf_magic_valid=pdf.startswith(b"%PDF-"), sha256=digest, exact_saved_pdf_hash_match=digest == saved["sha256"])
                except Exception as error:
                    attachment["error"] = str(error)
            row["status"] = "exact_pdf_match" if any(a.get("exact_saved_pdf_hash_match") for a in row["attachments"]) else "release_found_pdf_match_not_established"
            if row["attachments"] and all("error" in a for a in row["attachments"]):
                row["status"] = "release_and_attachment_found_pdf_download_failed"
        except Exception as error:
            row.update(status="release_fetch_or_parse_failed", error=str(error))
        print(report_id, row["status"], flush=True)
    assert (DATA / "source-manifest.json").read_bytes() == manifest_bytes
    for saved in original.values():
        assert hashlib.sha256((ROOT / saved["local_path"]).read_bytes()).hexdigest() == saved["sha256"]
    output = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Supplemental MFN discovery and byte-identity test for the existing eight-report corpus",
        "initial_acquisition": "The frozen PDFs were downloaded directly from issuer IR links, not from MFN.",
        "method": "Follow public company archive links using the existing Show more pagination pattern; parse release JSON-LD and PDF links; fetch PDFs into memory and compare SHA-256 to frozen saved issuer PDFs.",
        "pagination_implementation_source": PAGINATION_SOURCE,
        "maximum_archive_pages": 6,
        "archive_pages": archive_pages,
        "errors": errors,
        "download_failures": [{"report_id": row["report_id"], "url": a["url"], "error": a["error"]} for row in documents for a in row["attachments"] if "error" in a],
        "coverage": {"requested": len(SLUGS), "release_links_discovered": len(found), "pdf_attachment_links_found": sum(bool(row["attachments"]) for row in documents), "pdf_downloads_failed": sum(row["status"] == "release_and_attachment_found_pdf_download_failed" for row in documents), "exact_pdf_hash_matches": sum(row["status"] == "exact_pdf_match" for row in documents)},
        "frozen_manifest_and_original_hashes_unchanged": True,
        "limits": "A bounded test for these eight reports. It does not establish archive completeness, stable endpoints, refresh/revision behavior or general issuer coverage. PDF identity requires a hash match; titles alone are not used as identity proof.",
        "documents": documents,
    }
    (DATA / "mfn-discovery.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
