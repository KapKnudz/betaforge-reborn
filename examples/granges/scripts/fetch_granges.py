"""Re-fetch the exact issuer originals recorded in the frozen source manifest."""
import hashlib
import json
from pathlib import Path
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "data/granges-walkthrough"
CASE_DATA = Path(__file__).resolve().parents[1] / "data"


def validate(content, expected_hash):
    if not content.startswith(b"%PDF-"):
        raise ValueError("Response is not a PDF")
    if hashlib.sha256(content).hexdigest() != expected_hash:
        raise ValueError("PDF differs from the frozen snapshot; do not silently replace it")


def fetch():
    manifest_bytes = (CASE_DATA / "source-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    BASE.mkdir(parents=True, exist_ok=True)
    saved_manifest = BASE / "source-manifest.json"
    if saved_manifest.exists() and saved_manifest.read_bytes() != manifest_bytes:
        raise ValueError("Private corpus manifest differs from this frozen example")
    if not saved_manifest.exists():
        saved_manifest.write_bytes(manifest_bytes)
    for report in manifest["documents"]:
        target = (ROOT / report["local_path"]).resolve()
        if not target.is_relative_to((BASE / "sources").resolve()):
            raise ValueError("Source path is outside the report directory")
        if target.exists():
            validate(target.read_bytes(), report["sha256"])
            print(report["report_id"], "already verified")
            continue
        url = report["source_url"]
        if urlparse(url).scheme != "https" or urlparse(url).hostname != "www.granges.com":
            raise ValueError("Expected an HTTPS Gränges issuer source")
        with urlopen(url, timeout=90) as response:
            if urlparse(response.url).hostname != "www.granges.com":
                raise ValueError("Unexpected download redirect")
            content = response.read()
        validate(content, report["sha256"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(content)
        try:
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        print(report["report_id"], "downloaded and verified")


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        sample = b"%PDF-test"
        digest = hashlib.sha256(sample).hexdigest()
        validate(sample, digest)
        for content, expected in [(b"<html>denied</html>", digest), (sample, "wrong")]:
            try:
                validate(content, expected)
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid download was accepted")
        print("Download validation checks passed")
    else:
        fetch()
