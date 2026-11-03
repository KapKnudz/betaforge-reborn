import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import requests
import xlrd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_industry_context as fetch


def cell(value, ctype=None, fmt=0):
    if ctype is None:
        ctype = xlrd.XL_CELL_TEXT if isinstance(value, str) else xlrd.XL_CELL_NUMBER
    return SimpleNamespace(value=value, ctype=ctype, xf_index=fmt)


class Sheet:
    name = "Global Industry"

    def __init__(self, rows):
        self.ncols = max(map(len, rows))
        self.rows = [[value if hasattr(value, "ctype") else cell(value) for value in row]
                     + [cell("", xlrd.XL_CELL_EMPTY)] * (self.ncols - len(row)) for row in rows]
        self.nrows = len(rows)

    def cell(self, row, col):
        return self.rows[row][col]

    def cell_value(self, row, col):
        return self.cell(row, col).value

    def row_values(self, row):
        return [entry.value for entry in self.rows[row]]


class Book:
    datemode = 0

    def __init__(self, rows):
        self.sheet = Sheet(rows)
        self.closed = False
        self.xf_list = [SimpleNamespace(format_key=i) for i in range(5)]
        self.format_map = {i: SimpleNamespace(format_str=value) for i, value in enumerate(
            ("General", "m/d/yy", "0.00%", '0.00"%"', r"0.00\%"))}

    def sheets(self):
        return [self.sheet]

    def sheet_names(self):
        return [self.sheet.name]

    def release_resources(self):
        self.closed = True


def rows():
    return [
        ["Operating margins", "Global"],
        ["Date updated:", cell(xlrd.xldate.xldate_from_date_tuple((2026, 1, 9), 0), xlrd.XL_CELL_DATE, 1)],
        ["Industry Name", "Number of firms", "EBIT Margin", "Unfamiliar field"],
        ["Metals & Mining", 12, cell(0.125, fmt=2), "=2+2"],
    ]


class ParsingTests(unittest.TestCase):
    def parse(self, data=None, industries=None):
        book = Book(data or rows())
        self.addCleanup(lambda: self.assertTrue(book.closed))
        with patch.object(fetch.xlrd, "open_workbook", return_value=book) as open_book:
            result = fetch.parse_workbook(b"source bytes", industries or ["Metals & Mining"])
        open_book.assert_called_once_with(file_contents=b"source bytes", formatting_info=True)
        return result

    def test_finds_header_after_preamble_and_retains_source_location_and_date(self):
        result = self.parse()
        self.assertEqual(result["header_row"], 3)
        self.assertEqual(result["source_analysis_date"], "2026-01-09")
        self.assertEqual(result["selected_rows"][0]["excel_row"], 4)
        self.assertEqual(result["selected_rows"][0]["cells"][1]["unit"], "count")

    def test_missing_or_ambiguous_header_is_rejected(self):
        for data in ([rows()[0], rows()[1], rows()[3]], rows() + [rows()[2]]):
            with self.subTest(data=data), self.assertRaisesRegex(ValueError, "header"):
                self.parse(data)

    def test_missing_or_ambiguous_exact_industry_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            self.parse(industries=["Metals"])
        with self.assertRaisesRegex(ValueError, "exactly one"):
            self.parse(rows() + [rows()[3]])

    def test_missing_or_text_date_is_rejected_without_using_file_timestamp(self):
        data = rows()
        data[1] = ["Date updated:", "2026-01-09"]
        with self.assertRaisesRegex(ValueError, "Excel date"):
            self.parse(data)

    def test_geography_is_checked_and_duplicate_headers_keep_column_identity(self):
        data = rows()
        data[0] = ["Operating margins", "US"]
        with self.assertRaisesRegex(ValueError, "Global scope"):
            self.parse(data)
        data = rows()
        data[2][3] = "EBIT Margin"
        entries = self.parse(data)["selected_rows"][0]["cells"]
        self.assertEqual([entry["name"] for entry in entries[2:]], ["EBIT Margin", "EBIT Margin"])
        self.assertEqual([entry["column"] for entry in entries[2:]], [3, 4])

    def test_percent_value_keeps_fraction_and_format(self):
        entry = self.parse()["selected_rows"][0]["cells"][2]
        self.assertEqual(entry["value"], 0.125)
        self.assertEqual(entry["excel_number_format"], "0.00%")
        self.assertEqual(entry["unit"], "fraction_displayed_as_percent")
        book = Book(rows())
        for fmt in (3, 4):
            self.assertEqual(fetch.cell_record(book, cell(12.5, fmt=fmt), "Unknown", 1)["unit"], "unknown")

    def test_formula_text_unknown_fields_and_cached_numbers_are_not_evaluated(self):
        result = self.parse()
        entry = result["selected_rows"][0]["cells"][3]
        self.assertEqual(entry["name"], "Unfamiliar field")
        self.assertEqual(entry["value"], "=2+2")
        self.assertEqual(entry["cell_type"], "text")
        self.assertEqual(entry["unit"], "unknown")
        self.assertTrue(any("cached values" in note and "not evaluated" in note for note in fetch.CAVEATS))

    def test_documented_money_and_multiple_units_do_not_change_raw_values(self):
        book = Book(rows())
        money = fetch.cell_record(book, cell(102821.933), "Capital Expenditures (US $ millions)", 3)
        multiple = fetch.cell_record(book, cell(2.0676, fmt=2), "Cap Ex/Deprecn", 5)
        self.assertEqual((money["value"], money["unit"]), (102821.933, "USD_millions"))
        self.assertEqual((multiple["value"], multiple["unit"]), (2.0676, "multiple"))
        self.assertEqual(multiple["excel_number_format"], "0.00%")
        self.assertEqual(fetch.cell_record(book, cell(7, xlrd.XL_CELL_ERROR), "Unknown", 1)["cell_type"], "error")
        self.assertIsNone(fetch.cell_record(book, cell("", xlrd.XL_CELL_BLANK), "Unknown", 1)["value"])


class AcquisitionTests(unittest.TestCase):
    def destination(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return Path(temp.name) / "snapshot"

    def response(self, body):
        result = requests.Response()
        result.status_code = 200
        result._content = body
        result._content_consumed = True
        result.headers["Last-Modified"] = "Thu, 08 Jan 2026 19:22:46 GMT"
        return result

    def test_downloads_four_allowlisted_sources_once_retains_bytes_and_hashes(self):
        directory = self.destination()
        with patch.object(fetch.requests, "get", side_effect=lambda *a, **kw: self.response(b"exact raw bytes")) as get:
            with patch.object(fetch, "parse_workbook", return_value={"source_analysis_date": "2026-01-09", "selected_rows": []}):
                context = fetch.acquire(directory, ["Metals & Mining"])
        self.assertEqual(get.call_count, 4)
        for call in get.call_args_list:
            self.assertIn(call.args[0], [fetch.BASE + name for name in list(fetch.DATASETS.values())[:4]])
            self.assertFalse(call.kwargs["allow_redirects"])
            self.assertEqual(call.kwargs["timeout"], 60)
        manifest = json.loads((directory / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "complete")
        self.assertEqual(context["manifest_sha256"], hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest())
        for source in manifest["sources"]:
            self.assertEqual((directory / source["file"]).read_bytes(), b"exact raw bytes")
            self.assertEqual(source["sha256"], hashlib.sha256(b"exact raw bytes").hexdigest())
        with self.assertRaises(FileExistsError):
            fetch.acquire(directory, ["Metals & Mining"])

    def test_failed_parse_preserves_raw_manifest_and_has_no_usable_context(self):
        directory = self.destination()
        with patch.object(fetch.requests, "get", return_value=self.response(b"bad workbook")):
            with patch.object(fetch, "parse_workbook", side_effect=ValueError("missing row")):
                with self.assertRaisesRegex(ValueError, "missing row"):
                    fetch.acquire(directory, ["Metals & Mining"])
        self.assertFalse((directory / "context.json").exists())
        manifest = json.loads((directory / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "incomplete")
        self.assertEqual(len(manifest["sources"]), 1)

    def test_optional_fifth_source_and_date_mismatch_are_explicit(self):
        directory = self.destination()
        with patch.object(fetch.requests, "get", side_effect=lambda *a, **kw: self.response(b"source")) as get:
            with patch.object(fetch, "parse_workbook", return_value={"source_analysis_date": "2025-01-05", "selected_rows": []}):
                context = fetch.acquire(directory, ["Metals & Mining"], include_ev_ebit=True)
        self.assertEqual(get.call_count, 5)
        self.assertEqual(context["datasets"][-1]["id"], "ev_ebit")
        self.assertEqual(context["datasets"][0]["source_analysis_date"], "2025-01-05")
        self.assertIn("freshness is unresolved", context["datasets"][0]["caveats"][0])

    def test_non_200_stops_without_retrying_or_following_redirects(self):
        directory = self.destination()
        reply = self.response(b"rate limited")
        reply.status_code = 429
        with patch.object(fetch.requests, "get", return_value=reply) as get:
            with self.assertRaisesRegex(ValueError, "429"):
                fetch.acquire(directory, ["Metals & Mining"])
        self.assertEqual(get.call_count, 1)
        self.assertFalse((directory / "context.json").exists())


if __name__ == "__main__":
    unittest.main()
