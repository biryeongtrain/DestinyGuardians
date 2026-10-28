#!/usr/bin/env python3
"""Seed dirty, isolated linked worktrees; inspect/export exact owned-file deltas.

No integration, cleanup, commit, stash, reset, or push operations are provided.
Run with Python 3.10+; all subprocesses go through rtk.
"""

import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys


STATE = "worktree-batch.json"  # In each linked worktree's private Git directory.
VERSION = 1
CLONE_NOFOLLOW = 1
SKIP_DIRS = frozenset({
    ".git", ".gradle", ".cache", ".codegraph", "__pycache__", "node_modules",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "out", "target",
    "run", "runs", "logs", "cache", "caches",
})
QA_ARCHIVES = (".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar",
               ".jar", ".zst", ".mp4", ".mov", ".mkv", ".webm")
QA_CAPTURES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff",
               ".ico", ".wav", ".ogg", ".mp3", ".flac", ".opus", ".aac", ".m4a",
               ".aif", ".aiff", ".class", ".bin", ".dat", ".nbt", ".pdf", ".avi",
               ".exe", ".dll", ".so", ".dylib", ".glb", ".blend", ".npy", ".npz")
QA_BINARY_LIMIT = 8 * 1024 * 1024
DEPENDENCIES = ("libs/minigame-lib", "libs/gcb-server")


class BatchError(Exception):
    """A safety check failed. Existing files are left in place."""


def git(root, *args):
    result = subprocess.run(
        ["rtk", "proxy", "git", "-C", str(root), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if result.returncode:
        raise BatchError(result.stderr.decode(errors="replace").strip())
    return result.stdout.decode().strip()


def clean_absolute(value):
    """Do not normalize away symlinks or '..' before checking them."""
    path = Path(value).expanduser()
    if ".." in path.parts:
        raise BatchError(f"Parent traversal: {value}")
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if part.is_symlink():
            raise BatchError(f"Symlink path: {part}")
    return path


def relative(value):
    if not isinstance(value, str) or not value or any(c in value for c in "\\\0\r\n:"):
        raise BatchError(f"Invalid relative file path: {value!r}")
    p = PurePosixPath(value)
    if p.is_absolute() or p.as_posix() != value or any(x in {".", ".."} for x in p.parts):
        raise BatchError(f"Unsafe relative file path: {value!r}")
    return value


def joined(root, value):
    path = root / relative(value)
    clean_absolute(path)
    return path


def excluded(value):
    parts = PurePosixPath(value).parts
    return (any(p.lower() in SKIP_DIRS for p in parts)
            or parts[-1] == ".DS_Store"
            or bool(re.search(r"\.log(?:\.\d+)?$", parts[-1], re.I))
            or (parts[:2] == ("docs", "qa") and value.lower().endswith(QA_ARCHIVES + QA_CAPTURES)))


def token(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_mode)


def read_file(path, output=None):
    """Hash stable regular files without following a leaf symlink."""
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise BatchError(f"Not a regular file: {path}")
    digest = hashlib.sha256()
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        if token(os.fstat(stream.fileno())) != token(before):
            raise BatchError(f"File changed before read: {path}")
        sample = stream.read(8192)
        digest.update(sample)
        if output:
            output.write(sample)
        while block := stream.read(1024 * 1024):
            digest.update(block)
            if output:
                output.write(block)
        if token(os.fstat(stream.fileno())) != token(before):
            raise BatchError(f"File changed during read: {path}")
    if token(path.lstat()) != token(before):
        raise BatchError(f"File replaced during read: {path}")
    record = {"sha256": digest.hexdigest(), "size": before.st_size,
              "executable": bool(before.st_mode & 0o111)}
    try:
        sample.decode("utf-8")
        binary = b"\0" in sample
    except UnicodeDecodeError:
        binary = True
    return record, token(before), binary


def scan(root, skip_dependencies=False):
    """Walk disk, not git status: ignored and untracked working inputs matter."""
    files, tokens = {}, {}
    clean_absolute(root)
    for directory, dirs, names in os.walk(root, followlinks=False):
        base = Path(directory)
        # Check ancestors too, including directories replaced since os.walk saw them.
        clean_absolute(base)
        for name in sorted(dirs + names):
            path = base / name
            rel = path.relative_to(root).as_posix()
            skip = excluded(rel) or (skip_dependencies and rel in DEPENDENCIES)
            if skip:
                if name in dirs:
                    dirs.remove(name)
                continue
            if path.is_symlink():
                raise BatchError(f"Included symlink is unsupported: {path}")
            if name in dirs:
                continue
            # Do not read/hash multi-GB QA captures just to decide to exclude them.
            if rel.startswith("docs/qa/") and path.lstat().st_size > QA_BINARY_LIMIT:
                with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
                    sample = stream.read(8192)
                try:
                    sample.decode("utf-8")
                    binary = b"\0" in sample
                except UnicodeDecodeError:
                    binary = True
                if binary:
                    continue
            record, stamp, binary = read_file(path)
            if rel.startswith("docs/qa/") and record["size"] > QA_BINARY_LIMIT and binary:
                continue
            files[rel], tokens[rel] = record, stamp
    return files, tokens


def fingerprint(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _try_clone(source: Path, target: Path) -> bool:
    """Atomically create a Darwin CoW clone; only unsupported cases fall back."""
    if sys.platform != "darwin":
        return False
    try:
        clonefile = ctypes.CDLL(None, use_errno=True).clonefile
    except AttributeError:
        return False
    clonefile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    clonefile.restype = ctypes.c_int
    if clonefile(os.fsencode(source), os.fsencode(target), CLONE_NOFOLLOW) == 0:
        return True
    error = ctypes.get_errno()
    if error in {errno.EXDEV, errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS}:
        return False
    raise OSError(error, os.strerror(error), str(target))


def copy_file(source, target, expected):
    clean_absolute(source)
    clean_absolute(target)
    before = source.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise BatchError(f"Not a regular file: {source}")
    if target.exists():
        raise FileExistsError(errno.EEXIST, os.strerror(errno.EEXIST), str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    if _try_clone(source, target):
        actual, stamp, _ = read_file(source)
    else:
        with target.open("xb") as output:
            actual, stamp, _ = read_file(source, output)
    if actual != expected or stamp != token(before) or token(source.lstat()) != token(before):
        raise BatchError(f"Source drift while copying: {source}")
    # Check identity before chmod: a faulty clone must never change the source mode.
    copied = target.lstat()
    if (not stat.S_ISREG(copied.st_mode)
            or (copied.st_dev, copied.st_ino) == (before.st_dev, before.st_ino)):
        raise BatchError(f"Copy is not an independent regular file: {target}")
    with os.fdopen(os.open(target, os.O_RDONLY | os.O_NOFOLLOW), "rb") as output:
        if token(os.fstat(output.fileno())) != token(copied):
            raise BatchError(f"Copy changed before chmod: {target}")
        os.fchmod(output.fileno(), 0o755 if expected["executable"] else 0o644)
        copied_record, copied_stamp, _ = read_file(target)
        if copied_record != expected or copied_stamp != token(os.fstat(output.fileno())):
            raise BatchError(f"Copied file mismatch: {target}")
    if token(source.lstat()) != token(before):
        raise BatchError(f"Source drift while copying: {source}")


def owned_paths(values):
    if not isinstance(values, list) or not values:
        raise BatchError("owned_paths must be a nonempty list of exact file paths")
    result = []
    for value in values:
        rel = relative(value)
        if rel == "." or excluded(rel) or any(rel == d or rel.startswith(d + "/") for d in DEPENDENCIES):
            raise BatchError(f"Excluded or dependency scope: {rel}")
        if any(c in rel for c in "*?[]"):
            raise BatchError(f"Scope must name exact files: {rel}")
        for other in result:
            a, b = rel.casefold(), other.casefold()
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                raise BatchError(f"Overlapping ownership: {rel}, {other}")
        result.append(rel)
    return result


def repo_root(path):
    path = clean_absolute(path)
    if not path.is_dir() or Path(git(path, "rev-parse", "--show-toplevel")) != path:
        raise BatchError(f"Not a Git worktree root: {path}")
    return path


def state_path(worker):
    return clean_absolute(git(worker, "rev-parse", "--absolute-git-dir")) / STATE


def registered_worktrees(source):
    return {Path(line[9:]) for line in git(source, "worktree", "list", "--porcelain", "-z").split("\0")
            if line.startswith("worktree ")}


def write_json(path, value, mode="x"):
    with path.open(mode, encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")


def create(source, manifest, minigame_lib=None, gcb_server=None):
    source = repo_root(source)
    dependencies = {
        DEPENDENCIES[0]: clean_absolute(minigame_lib or source / DEPENDENCIES[0]),
        DEPENDENCIES[1]: clean_absolute(gcb_server or source / DEPENDENCIES[1]),
    }
    for root in dependencies.values():
        if not root.is_dir() or root == source or not (root / "build.gradle").is_file():
            raise BatchError(f"Dependency needs its own source directory with build.gradle: {root}")
    features = manifest.get("features") if isinstance(manifest, dict) else None
    if not isinstance(features, list) or not features:
        raise BatchError("Manifest needs a nonempty features list")
    prepared, all_owned, names = [], [], set()
    registered = registered_worktrees(source)
    for feature in features:
        if not isinstance(feature, dict) or set(feature) != {"name", "destination", "owned_paths"}:
            raise BatchError("Each feature needs exactly name, destination, owned_paths")
        name = feature["name"]
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name) or name.casefold() in names:
            raise BatchError(f"Invalid/duplicate feature name: {name!r}")
        names.add(name.casefold())
        destination = clean_absolute(feature["destination"])
        if destination.exists() or destination in registered or not destination.parent.is_dir():
            raise BatchError(f"Destination exists, is registered, or lacks a parent: {destination}")
        for root in [source, *dependencies.values(), *(x[1] for x in prepared)]:
            if destination == root or root in destination.parents or destination in root.parents:
                raise BatchError(f"Overlapping destination/source: {destination}, {root}")
        scope = owned_paths(feature["owned_paths"])
        owned_paths(all_owned + scope)  # Disjoint ownership across the whole batch.
        all_owned.extend(scope)
        for rel in scope:
            if joined(source, rel).is_dir():
                raise BatchError(f"Ownership must be a file, not a directory: {rel}")
        prepared.append((name, destination, scope))

    head = git(source, "rev-parse", "HEAD")
    source_snapshot = scan(source, skip_dependencies=True)
    dependency_snapshots = {rel: scan(root) for rel, root in dependencies.items()}
    baseline = dict(source_snapshot[0])
    for rel, snapshot in dependency_snapshots.items():
        baseline.update({f"{rel}/{p}": record for p, record in snapshot[0].items()})
    for rel in all_owned:
        if joined(source, rel).exists() and rel not in baseline:
            raise BatchError(f"Owned input was excluded: {rel}")

    workers = []
    for name, destination, scope in prepared:
        # Reserve atomically. Git accepts our empty directory, never a preexisting one.
        destination.mkdir()
        git(source, "worktree", "add", "--detach", "--no-checkout", "--", str(destination), head)
        git(destination, "read-tree", "HEAD")  # Private index; no checkout can resurrect deletions.
        metadata = {
            "version": VERSION, "status": "incomplete", "name": name,
            "source": str(source), "worktree": str(destination), "head": head,
            "dependency_sources": [str(p) for p in dependencies.values()],
            "owned_paths": scope, "baseline": baseline,
            "baseline_sha256": fingerprint(baseline),
            "gradle_env": {"ORG_GRADLE_PROJECT_gcb_server_dir": str(destination / DEPENDENCIES[1])},
        }
        write_json(state_path(destination), metadata)
        workers.append((destination, metadata))
        for rel, record in source_snapshot[0].items():
            copy_file(joined(source, rel), joined(destination, rel), record)
        for prefix, snapshot in dependency_snapshots.items():
            for rel, record in snapshot[0].items():
                copy_file(joined(dependencies[prefix], rel), joined(destination, prefix + "/" + rel), record)

    # Full inventories catch additions/deletions as well as content/mode changes.
    if git(source, "rev-parse", "HEAD") != head or scan(source, True) != source_snapshot:
        raise BatchError("Source drift during batch copy; worktrees remain incomplete")
    for prefix, root in dependencies.items():
        if scan(root) != dependency_snapshots[prefix]:
            raise BatchError(f"Dependency drift during batch copy: {root}")
    for destination, _ in workers:
        if scan(destination)[0] != baseline:
            raise BatchError(f"Copied baseline mismatch: {destination}")
    for destination, metadata in workers:
        metadata["status"] = "ready"
        write_json(state_path(destination), metadata, "w")
    return [{"name": m["name"], "worktree": str(d), "baseline_files": len(baseline),
             "baseline_sha256": m["baseline_sha256"], "gradle_env": m["gradle_env"]} for d, m in workers]


def load(worker):
    worker = repo_root(worker)
    metadata = json.loads(state_path(worker).read_text(encoding="utf-8"))
    if (metadata.get("version") != VERSION or metadata.get("status") != "ready"
            or metadata.get("worktree") != str(worker)):
        raise BatchError("Missing, incomplete, or mismatched worktree baseline")
    owned_paths(metadata["owned_paths"])
    if fingerprint(metadata["baseline"]) != metadata["baseline_sha256"]:
        raise BatchError("Baseline checksum mismatch")
    for rel in metadata["baseline"]:
        relative(rel)
    if git(worker, "rev-parse", "HEAD") != metadata["head"]:
        raise BatchError("Worktree HEAD changed since create")
    return worker, metadata


def describe(worker, metadata, current):
    baseline, scope = metadata["baseline"], set(metadata["owned_paths"])
    changed = sorted(p for p in baseline.keys() | current.keys() if baseline.get(p) != current.get(p))
    changes = [{"path": p, "operation": "delete" if p not in current else "add" if p not in baseline else "modify"}
               for p in changed if p in scope]
    return {"name": metadata["name"], "worktree": str(worker),
            "baseline_sha256": metadata["baseline_sha256"], "changes": changes,
            "out_of_scope": [p for p in changed if p not in scope], "gradle_env": metadata["gradle_env"]}


def inspect(worker):
    worker, metadata = load(worker)
    return describe(worker, metadata, scan(worker)[0])


def owned_snapshot(root, scope):
    result = {}
    for rel in scope:
        path = joined(root, rel)
        try:
            record, stamp, _ = read_file(path)
            result[rel] = (record, stamp)
        except FileNotFoundError:
            result[rel] = (None, None)
    return result


def export(worker, output=None, allow_deletes=False):
    """Output=None is a dry run. Export never modifies the source or worker."""
    worker, metadata = load(worker)
    before = scan(worker)
    report = describe(worker, metadata, before[0])
    if report["out_of_scope"]:
        raise BatchError("Out-of-scope changes: " + ", ".join(report["out_of_scope"]))
    if not allow_deletes and any(c["operation"] == "delete" for c in report["changes"]):
        raise BatchError("Owned deletions require --allow-deletes (bundle records only)")
    source = repo_root(metadata["source"])
    source_before = owned_snapshot(source, metadata["owned_paths"])
    for rel in metadata["owned_paths"]:
        joined(worker, rel)
        if source_before[rel][0] != metadata["baseline"].get(rel):
            raise BatchError(f"Main/source baseline conflict: {rel}")
    plan = {**report, "source": str(source), "status": "dry-run", "files": []}
    for change in report["changes"]:
        rel = change["path"]
        plan["files"].append({**change, "before": metadata["baseline"].get(rel), "after": before[0].get(rel)})
    target = None
    if output is not None:
        target = clean_absolute(output)
        protected = registered_worktrees(source) | {clean_absolute(p) for p in metadata["dependency_sources"]}
        for root in protected:
            if target == root or root in target.parents or target in root.parents:
                raise BatchError("Export destination must be outside source and worktree")
        if target.exists() or not target.parent.is_dir():
            raise BatchError(f"Export destination exists or lacks a parent: {target}")
        target.mkdir()  # No overwrite. Failed exports retain INCOMPLETE, never a manifest.
        (target / "INCOMPLETE").write_text("Export incomplete; do not integrate.\n")
        for change in plan["files"]:
            if change["after"] is not None:
                copy_file(joined(worker, change["path"]), joined(target / "files", change["path"]), change["after"])
    if scan(worker) != before or owned_snapshot(source, metadata["owned_paths"]) != source_before:
        raise BatchError("Source/worktree drift during export")
    if target is not None:
        plan["status"] = "exported"
        write_json(target / "manifest.json", plan)
        (target / "INCOMPLETE").unlink()  # Only our marker; never working inputs.
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("create", help="Seed a manifest batch from a dirty source")
    seed.add_argument("--source", required=True)
    seed.add_argument("--manifest", required=True)
    seed.add_argument("--minigame-lib", help="Default: SOURCE/libs/minigame-lib")
    seed.add_argument("--gcb-server", help="Default: SOURCE/libs/gcb-server; otherwise pass sibling checkout")
    for name in ("inspect", "export"):
        sub = commands.add_parser(name)
        sub.add_argument("--worktree", required=True)
        if name == "export":
            group = sub.add_mutually_exclusive_group(required=True)
            group.add_argument("--output", help="New directory outside source/worktree")
            group.add_argument("--dry-run", action="store_true")
            sub.add_argument("--allow-deletes", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            result = create(args.source, json.loads(Path(args.manifest).read_text()), args.minigame_lib, args.gcb_server)
        elif args.command == "inspect":
            result = inspect(args.worktree)
        else:
            result = export(args.worktree, args.output, args.allow_deletes)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (BatchError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"worktree-batch: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
