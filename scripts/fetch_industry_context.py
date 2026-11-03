"""Save selected Damodaran Global industry rows and their original XLS sources."""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import requests
import xlrd


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/"
DATASETS = {
    "margins": "marginGlobal.xls",
    "working_capital": "wcdataGlobal.xls",
    "return_on_capital": "EVAGlobal.xls",
    "reinvestment": "capexGlobal.xls",
    "ev_ebit": "vebitdaGlobal.xls",
}
DEFINITIONS_URL = "https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/variable.htm"
CAVEATS = [
    "Global industry aggregates, not company-level peer medians or a verified Gränges peer group.",
    "A broad Metals & Mining row includes different business models and cannot set an exit multiple.",
    "Many source ratios use aggregate sector numerators and denominators; no peer median is inferred.",
    "The source analysis date, underlying financial periods and retrieval date are different; exact constituent reporting periods are not supplied here.",
    "Leases, R&D capitalization, taxes, stock compensation and invested-capital definitions may differ from issuer metrics; match column definitions before comparison.",
    "XLS values are cached values read by xlrd. Formulas are not evaluated or exposed, and their cache freshness is not verified; the original workbook preserves them.",
    "Unknown units and fields are preserved without financial interpretation. No valuation input is changed by this context.",
    "The reported firm count does not prove identical usable coverage for every metric. Source WACC and other risk inputs are retained source columns, not adopted company valuation assumptions.",
]


def normalized(value):
    return " ".join(str(value).split()).casefold()


def sha256(body):
    return hashlib.sha256(body).hexdigest()


def write_json(path, value):
    body = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    with path.open("xb") as file:
        file.write(body)
    return sha256(body)


def number_format(book, cell):
    xf = book.xf_list[cell.xf_index]
    return book.format_map[xf.format_key].format_str


def cell_record(book, cell, name, column):
    kind = {0: "empty", 1: "text", 2: "number", 3: "date", 4: "boolean",
            5: "error", 6: "blank"}[cell.ctype]
    value = cell.value
    if cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
        value = None
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Non-finite XLS value")
    fmt = number_format(book, cell)
    unit = "unknown"
    label = normalized(name)
    if label == "industry name":
        unit = "industry_label"
    elif label in ("number of firms", "number of companies"):
        unit = "count"
    elif "us $ millions" in label or label in ("bv of equity", "equity eva", "bv of capital", "eva"):
        unit = "USD_millions"
    elif label in ("cap ex/deprecn", "sales/ invested capital (ltm)") or label.startswith("ev/ebit"):
        unit = "multiple"
    elif label == "beta":
        unit = "coefficient"
    elif cell.ctype == xlrd.XL_CELL_NUMBER and "%" in re.sub(r'"[^"]*"|\\.', "", fmt):
        unit = "fraction_displayed_as_percent"
    return {"column": column, "name": name, "value": value,
            "cell_type": kind, "excel_number_format": fmt, "unit": unit}


def source_date(book, sheet, header):
    dates = []
    for row in range(header):
        for col in range(sheet.ncols - 1):
            label = sheet.cell_value(row, col)
            if normalized(label).rstrip(":") in ("date updated", "date of analysis"):
                cell = sheet.cell(row, col + 1)
                if cell.ctype != xlrd.XL_CELL_DATE:
                    raise ValueError("Source date must be an Excel date")
                value = xlrd.xldate_as_datetime(cell.value, book.datemode).date().isoformat()
                dates.append((str(label), value))
    if len(dates) != 1:
        raise ValueError("Missing or ambiguous workbook analysis date")
    return dates[0]


def parse_workbook(body, industries):
    """Read one exact row per requested industry; preserve columns and cached values."""
    book = xlrd.open_workbook(file_contents=body, formatting_info=True)
    try:
        headers = []
        for sheet in book.sheets():
            for row in range(sheet.nrows):
                if (normalized(sheet.cell_value(row, 0)) == "industry name"
                        and any(normalized(value) in ("number of firms", "number of companies")
                                for value in sheet.row_values(row))):
                    headers.append((sheet, row))
        if len(headers) != 1:
            raise ValueError("Expected one unambiguous industry table header")
        sheet, header = headers[0]
        names = sheet.row_values(header)
        while names and not str(names[-1]).strip():
            names.pop()
        if any(not isinstance(name, str) or not name.strip() for name in names):
            raise ValueError("Every industry column needs a source header")
        if not any(normalized(value) == "global" for row in range(header)
                   for value in sheet.row_values(row)):
            raise ValueError("Expected an explicit Global scope label")
        label, date = source_date(book, sheet, header)
        selected = []
        for industry in industries:
            matches = [row for row in range(header + 1, sheet.nrows)
                       if normalized(sheet.cell_value(row, 0)) == normalized(industry)]
            if len(matches) != 1:
                raise ValueError(f"Industry must match exactly one source row: {industry}")
            row = matches[0]
            if any(value != "" for value in sheet.row_values(row)[len(names):]):
                raise ValueError("Industry row has data beyond its source headers")
            selected.append({"industry": sheet.cell_value(row, 0), "excel_row": row + 1,
                             "cells": [cell_record(book, sheet.cell(row, col), name, col + 1)
                                       for col, name in enumerate(names)]})
        return {"sheet": sheet.name, "header_row": header + 1,
                "source_date_label": label, "source_analysis_date": date,
                "definition_sheet": "Variables & FAQ" if "Variables & FAQ" in book.sheet_names() else None,
                "preamble": [[cell_record(book, sheet.cell(row, col), "", col + 1)
                              for col in range(sheet.ncols)
                              if sheet.cell(row, col).ctype not in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK)]
                             for row in range(header)],
                "selected_rows": selected}
    finally:
        book.release_resources()


def acquire(directory, industries, include_ev_ebit=False):
    if not industries or any(not industry.strip() for industry in industries):
        raise ValueError("Choose at least one exact industry name")
    if len({normalized(industry) for industry in industries}) != len(industries):
        raise ValueError("Duplicate industry selections")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "raw").mkdir()
    retrieved = datetime.now(timezone.utc).isoformat()
    manifest = {"schema_version": 1, "provider": "Damodaran", "geographic_scope": "Global",
                "retrieved_at_utc": retrieved, "status": "incomplete", "sources": []}
    datasets = []
    try:
        for identifier, filename in DATASETS.items():
            if identifier == "ev_ebit" and not include_ev_ebit:
                continue
            url = BASE + filename
            with requests.get(url, timeout=60, allow_redirects=False,
                              headers={"Accept": "application/vnd.ms-excel"}) as response:
                if response.status_code != 200:
                    raise ValueError(f"Non-200 response for {identifier}: {response.status_code}")
                body = response.content
                raw_file = "raw/" + filename
                with (directory / raw_file).open("xb") as file:
                    file.write(body)
                source = {"id": identifier, "url": url, "file": raw_file,
                          "sha256": sha256(body), "bytes": len(body),
                          "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                          "http_last_modified": response.headers.get("Last-Modified")}
                manifest["sources"].append(source)
            parsed = parse_workbook(body, industries)
            source["source_analysis_date"] = parsed["source_analysis_date"]
            caveats = []
            if source["http_last_modified"]:
                modified = parsedate_to_datetime(source["http_last_modified"]).date()
                if modified.year != int(parsed["source_analysis_date"][:4]):
                    caveats.append("The workbook date label and HTTP modification year differ; underlying freshness is unresolved. The workbook date label is preserved without correction.")
            datasets.append({"id": identifier, "source_url": url, "raw_file": raw_file,
                             "raw_sha256": source["sha256"], "caveats": caveats, **parsed})
        manifest["status"] = "complete"
    finally:
        manifest_hash = write_json(directory / "manifest.json", manifest)
    context = {"schema_version": 1, "provider": "Damodaran", "geographic_scope": "Global",
               "retrieved_at_utc": retrieved, "manifest": "manifest.json",
               "manifest_sha256": manifest_hash, "industry_selections": industries,
               "definitions_url": DEFINITIONS_URL, "caveats": CAVEATS, "datasets": datasets}
    write_json(directory / "context.json", context)
    return context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--industry", action="append", required=True,
                        help="Exact source industry label; may be repeated")
    parser.add_argument("--include-ev-ebit", action="store_true")
    parser.add_argument("--output-root", type=Path, default=ROOT / "data/benchmarks/damodaran")
    args = parser.parse_args()
    directory = args.output_root / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    acquire(directory, args.industry, args.include_ev_ebit)
    print(directory / "context.json")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, requests.RequestException, xlrd.XLRDError) as error:
        print(f"Industry context failed: {error}", file=sys.stderr)
        sys.exit(1)
