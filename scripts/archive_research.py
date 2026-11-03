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

FORBIDDEN_PARTS = {".git", ".idea", ".venv", ".aws", ".ssh", ".codex", ".agents", ".config", "node_modules", "__pycache__"}


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def forbidden(path):
    return any(part.lower() in FORBIDDEN_PARTS or part.lower().startswith(".env") or
               part.lower() in {"auth.json", "credentials.json", "credentials"}
               for part in path.parts)


def research_path(root, value):
    """Only explicit research subpaths, never the repository or a home directory."""
    relative = Path(value)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in str(value) or
            forbidden(relative) or len(relative.parts) < 2):
        raise ValueError("Use a reviewed repository-relative research subpath")
    if relative.parts[0] == "data":
        if relative.parts[1] == "backups":
            raise ValueError("Backup output is not an archive input")
    elif relative.parts[0] == "examples":
        if len(relative.parts) < 3 or relative.parts[2] != "data":
            raise ValueError("Example inputs must be inside examples/<case>/data")
    else:
        raise ValueError("Research inputs must be under data/ or examples/<case>/data")
    path = root / relative
    if any(parent.is_symlink() for parent in (path, *path.parents) if parent != root and parent.is_relative_to(root)):
        raise ValueError("Research symlinks are not archived: " + str(relative))
    if not path.resolve().is_relative_to(root):
        raise ValueError("Research path escapes the repository")
    return path


def source_files(root, includes):
    """Select only named saved evidence, with no company-specific defaults."""
    root = Path(root).resolve()
    if isinstance(includes, (str, Path)) or not includes:
        raise ValueError("At least one explicit research include path is required")
    selected = {}
    for relative in includes:
        path = research_path(root, relative)
        if not path.exists():
            raise ValueError("Required research path missing: " + str(relative))
        for source in sorted(path.rglob("*")) if path.is_dir() else [path]:
            relative_path = source.relative_to(root)
            if source.is_symlink():
                raise ValueError("Research symlinks are not archived: " + str(relative_path))
            if source.is_file() and not forbidden(relative_path):
                selected[relative_path.as_posix()] = source
    if not selected:
        raise ValueError("No eligible research files selected")
    return [(source, name) for name, source in sorted(selected.items())]


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


def create_archive(root, destination, includes, db_path="data/evidence/evidence.sqlite3"):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    if not destination.name.endswith(".tar.gz"):
        raise ValueError("Archive filename must end in .tar.gz")
    checksum = destination.with_name(destination.name + ".sha256")
    index = destination.with_name(destination.name + ".manifest.json")
    if any(path.exists() for path in (destination, checksum, index)):
        raise FileExistsError("Archive or sidecar already exists; choose a new version")
    files = source_files(root, includes)
    database = research_path(root, db_path)
    if not database.is_file():
        raise ValueError("Evidence database missing: " + str(db_path))
    for relative in includes:
        source = research_path(root, relative)
        if source.is_relative_to(database.parent) or database.parent.is_relative_to(source):
            raise ValueError("Select saved evidence separately; the live store is frozen through --db")
        if destination == source or (source.is_dir() and destination.is_relative_to(source)):
            raise ValueError("Archive output must be outside its input paths")
    if destination.is_relative_to(database.parent):
        raise ValueError("Archive output must be outside the evidence store")
    store_relative = database.parent.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".archive-", dir=destination.parent))
    try:
        with EvidenceStore(database, readonly=True) as store:
            frozen = store.freeze(temporary / "canonical-evidence")
        files.extend((source, (store_relative / source.relative_to(frozen)).as_posix())
                     for source in sorted(frozen.rglob("*")) if source.is_file())
        manifest = {"created_at": datetime.now(timezone.utc).isoformat(),
                    "git": git_identity(root), "source_paths": sorted({Path(p).as_posix() for p in includes}),
                    "source_database": database.relative_to(root).as_posix(),
                    "canonical_store": store_relative.as_posix() + " (consistent SQLite backup and verified blobs)",
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
    parser.add_argument("--include", action="append", required=True, type=Path,
                        help="Reviewed repository-relative saved research path; repeat for each selection")
    parser.add_argument("--db", type=Path, default=Path("data/evidence/evidence.sqlite3"),
                        help="Repository-relative live evidence database; frozen consistently, not copied directly")
    args = parser.parse_args()
    print(json.dumps(create_archive(ROOT, args.output, args.include, args.db), indent=2))


if __name__ == "__main__":
    main()
