import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_borsdata_context as fetch
from betaforge import borsdata


def response(status, body=b'{"reports":[]}', headers=None):
    result = requests.Response()
    result.status_code = status
    result._content = body
    result.headers.update(headers or {})
    return result


class AcquisitionTests(unittest.TestCase):
    def test_shared_client_keeps_credentials_out_of_url_and_disables_redirects(self):
        with patch.object(borsdata.requests,'get') as get:
            borsdata.get_response('/v1/instruments/777/reports/year',{'original':1},'TEST_SECRET_VALUE')
        self.assertEqual(get.call_args.args[0],borsdata.BASE_URL+'/v1/instruments/777/reports/year')
        self.assertNotIn('TEST_SECRET_VALUE',get.call_args.args[0])
        self.assertEqual(get.call_args.kwargs['params'],{'authKey':'TEST_SECRET_VALUE','original':1})
        self.assertFalse(get.call_args.kwargs['allow_redirects'])

    def test_quoted_credential_values_and_duplicate_key_rejection_survive_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'.env.local'
            for value in ('TEST_SECRET_VALUE','"TEST_SECRET_VALUE"',"'TEST_SECRET_VALUE'"):
                path.write_text('BORSDATA_API_KEY='+value+'\n')
                self.assertEqual(borsdata.read_key(path),'TEST_SECRET_VALUE')
            path.write_text('BORSDATA_API_KEY=first\nBORSDATA_API_KEY=second\n')
            with self.assertRaisesRegex(ValueError,'exactly one'):
                borsdata.read_key(path)

    def run_fetch(self, replies):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        destination = Path(temp.name) / "snapshot"
        output = io.StringIO()
        with patch.object(fetch, "get_response", side_effect=replies) as get, contextlib.redirect_stdout(output):
            result = fetch.acquire(destination, 426, "TEST_SECRET_VALUE",
                                   [("one", "/v1/one", {}), ("two", "/v1/two", {})], pause=lambda _: None)
        return destination, result, get.call_count, output.getvalue()

    def test_access_failure_stops_and_redacts(self):
        path, manifest, calls, output = self.run_fetch([
            response(403, b'{"detail":"Denied TEST_SECRET_VALUE https://example.com/?authKey=TEST_SECRET_VALUE"}')])
        self.assertEqual(calls, 1)
        self.assertEqual(manifest["requests"][0]["status"], "failed")
        self.assertNotIn("TEST_SECRET_VALUE", output + (path / "manifest.json").read_text())
        self.assertFalse((path / "one.json").exists())

    def test_rate_limit_retry_is_bounded(self):
        _, manifest, calls, _ = self.run_fetch([response(429)] * 3)
        self.assertEqual(calls, 3)
        self.assertEqual(manifest["requests"][0]["attempts"], 3)

    def test_transient_transport_errors_retry_and_preserve_exact_bytes(self):
        body = b'{"reports": [null], "value": 1.2300}'
        message = 'https://example.com/?authKey=TEST_SECRET_VALUE'
        path, manifest, calls, output = self.run_fetch([
            requests.ConnectionError(message), requests.Timeout(message),
            response(200, body), response(200)])
        first = manifest['requests'][0]
        self.assertEqual(calls, 4)
        self.assertEqual(first['status'], 'saved')
        self.assertEqual(first['attempts'], 3)
        self.assertEqual(first['transport_errors'], ['ConnectionError', 'Timeout'])
        self.assertNotIn('error', first)
        self.assertEqual((path / 'one.json').read_bytes(), body)
        captured = output + (path / 'manifest.json').read_text()
        self.assertNotIn('TEST_SECRET_VALUE', captured)
        self.assertNotIn('https://example.com/', captured)

    def test_transport_exhaustion_is_failed_and_redacted(self):
        for error_type in (requests.ConnectionError, requests.Timeout):
            with self.subTest(error=error_type.__name__):
                path, manifest, calls, output = self.run_fetch([
                    error_type('https://example.com/?authKey=TEST_SECRET_VALUE')
                    for _ in range(3)] + [response(200)])
                first = manifest['requests'][0]
                self.assertEqual(calls, 4)
                self.assertEqual(first['status'], 'failed')
                self.assertEqual(first['attempts'], 3)
                self.assertEqual(first['error'], error_type.__name__)
                self.assertEqual(first['transport_errors'], [error_type.__name__] * 3)
                self.assertFalse((path / 'one.json').exists())
                self.assertEqual(manifest['requests'][1]['status'], 'saved')
                captured = output + (path / 'manifest.json').read_text()
                self.assertNotIn('TEST_SECRET_VALUE', captured)
                self.assertNotIn('https://example.com/', captured)

    def test_long_retry_after_defers_instead_of_retrying_early(self):
        _, manifest, calls, _ = self.run_fetch([response(429, headers={"Retry-After": "120"})])
        self.assertEqual(calls, 1)
        self.assertEqual(manifest["requests"][0]["retry_after_seconds"], 120)
        self.assertTrue(manifest["requests"][0]["retry_deferred"])

    def test_success_retains_exact_bytes_and_rejects_key_echo(self):
        body = b'{"reports": [null], "value": 1.2300}'
        path, manifest, calls, output = self.run_fetch([
            response(200, body), response(200, b'{"echo":"\\u0054EST_SECRET_VALUE"}')])
        self.assertEqual((path / "one.json").read_bytes(), body)
        self.assertEqual(manifest["requests"][1]["status"], "failed")
        self.assertNotIn("TEST_SECRET_VALUE", output)
        self.assertFalse((path / "two.json").exists())


if __name__ == "__main__":
    unittest.main()
