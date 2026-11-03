"""Preserve the existing research as a private archive, separate from Git history."""
from datetime import datetime, timezone
import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from betaforge.storage import EvidenceStore

# These are the completed research inputs/results, never the user's home or config.
RESEARCH_DIRECTORIES = (
    "data/granges-codex/packet-20261101",
    "data/granges-codex/runs/20261101-full",
    "data/granges-walkthrough/sources",
    "data/granges-walkthrough/prepared",
    "data/granges-walkthrough/runs",
    "data/granges-walkthrough/qa",
    "data/borsdata",
)
OPTIONAL_RESEARCH_DIRECTORIES = (
    "data/granges-codex/packet-quality-20261103",
    "data/granges-codex/runs/20261103-quality-smoke",
    "data/financial-reviews",
    "data/benchmarks",
    "data/watchlists",
)
FORBIDDEN_PARTS = {".git", ".idea", ".venv", "node_modules", "__pycache__"}


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def forbidden(path):
    return any(part in FORBIDDEN_PARTS or part.startswith(".env") or
               part.lower() in {"auth.json", "credentials.json", "credentials"}
               for part in path.parts)


def source_files(root):
    """An explicit selection keeps secrets and unrelated workspace files out."""
    root = Path(root).resolve()
    selected = []
    directories = (*RESEARCH_DIRECTORIES, *(name for name in OPTIONAL_RESEARCH_DIRECTORIES if (root/name).exists()))
    for relative in directories:
        directory = root / relative
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Required research directory missing or linked: " + relative)
        for source in sorted(directory.rglob("*")):
            relative_path = source.relative_to(root)
            if source.is_symlink():
                raise ValueError("Research symlinks are not archived: " + str(relative_path))
            if source.is_file() and not forbidden(relative_path):
                selected.append((source, relative_path.as_posix()))
    directory = root / "data/granges-walkthrough"
    for source in sorted(directory.iterdir()):
        if source.is_symlink():
            raise ValueError("Research symlinks are not archived: " + str(source.relative_to(root)))
        if source.is_file() and source.suffix in {".json", ".md"} and not forbidden(source.relative_to(root)):
            selected.append((source, source.relative_to(root).as_posix()))
    return selected


def git_identity(root):
    def read(*arguments):
        result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True,
                                text=True, check=True)
        return result.stdout.strip()
    return {"head_at_capture": read("rev-parse", "HEAD"),
            "tracked_changes": bool(read("diff", "--name-only", "HEAD")),
            "untracked_project_files": bool(read("ls-files", "--others", "--exclude-standard"))}


def add_file(archive, source, name):
    before = source.stat()
    info = archive.gettarinfo(str(source), arcname=name)
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mode = 0o600
    with source.open("rb") as body:
        archive.addfile(info, body)
    after = source.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("Research changed during archival: " + name)
    return {"path": name, "bytes": before.st_size}


def create_archive(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if not destination.name.endswith(".tar.gz"):
        raise ValueError("Archive filename must end in .tar.gz")
    checksum = destination.with_name(destination.name + ".sha256")
    index = destination.with_name(destination.name + ".manifest.json")
    if any(path.exists() for path in (destination, checksum, index)):
        raise FileExistsError("Archive or sidecar already exists; choose a new version")
    files = source_files(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".archive-", dir=destination.parent))
    try:
        with EvidenceStore(root / "data/evidence/evidence.sqlite3", readonly=True) as store:
            frozen = store.freeze(temporary / "canonical-evidence")
        files.extend((source, "data/evidence/" + source.relative_to(frozen).as_posix())
                     for source in sorted(frozen.rglob("*")) if source.is_file())
        manifest = {"created_at": datetime.now(timezone.utc).isoformat(),
                    "git": git_identity(root), "source_directories": [*RESEARCH_DIRECTORIES, *(name for name in OPTIONAL_RESEARCH_DIRECTORIES if (root/name).exists())],
                    "canonical_store": "data/evidence (consistent SQLite backup and verified blobs)",
                    "files": []}
        pending = temporary / destination.name
        with tarfile.open(pending, "w:gz", compresslevel=6) as archive:
            for source, name in files:
                manifest["files"].append(add_file(archive, source, name))
            body = (json.dumps(manifest, indent=2) + "\n").encode()
            info = tarfile.TarInfo("research-manifest.json")
            info.size, info.mode = len(body), 0o600
            archive.addfile(info, io.BytesIO(body))
        pending.chmod(0o600)
        archive_hash = digest(pending)
        sidecar = {**manifest, "archive": destination.name, "archive_sha256": archive_hash,
                   "archive_bytes": pending.stat().st_size}
        (temporary / index.name).write_text(json.dumps(sidecar, indent=2) + "\n")
        (temporary / checksum.name).write_text(archive_hash + "  " + destination.name + "\n")
        for name in (index.name, checksum.name):
            (temporary / name).chmod(0o600)
        pending.rename(destination)
        (temporary / index.name).rename(index)
        (temporary / checksum.name).rename(checksum)
        return {"archive": str(destination), "sha256": archive_hash,
                "archive_bytes": destination.stat().st_size, "files": len(manifest["files"]),
                "source_bytes": sum(item["bytes"] for item in manifest["files"]),
                "manifest": str(index), "checksum": str(checksum)}
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(create_archive(ROOT, args.output), indent=2))


if __name__ == "__main__":
    main()
