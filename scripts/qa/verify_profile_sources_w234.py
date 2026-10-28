#!/usr/bin/env python3
"""Verify complete historical profile sources offline; no Gradle or game process.

Only explicit --rebuild-archive/--populate-cache write files. Network is used only
by explicit --recover while rebuilding the archive, never during verification.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import urllib.request
import zipfile

CATALOG = "art/weapons/w234/pinned-sources.json"
MANIFESTS = (
    "art/weapons/w170/perpetual-motion/manifest.json",
    "art/weapons/w171/tap-the-trigger/manifest.json",
    "art/weapons/w172/frenzy/manifest.json",
    "art/weapons/w176/stats-for-all/manifest.json",
)


def checked(stream, expected, size, label):
    digest = hashlib.sha256()
    count = 0
    while block := stream.read(65536):
        count += len(block)
        if count > size:
            raise ValueError(f"Full-source byte count exceeds pin: {label}")
        digest.update(block)
    actual = digest.hexdigest()
    if count != size or actual != expected:
        raise ValueError(f"Full-source SHA-256/size mismatch: {label}: {actual}/{count}, expected {expected}/{size}")
    return count


def check_file(path, pin):
    with path.open("rb") as stream:
        return checked(stream, pin["sha256"], pin["bytes"], str(path))


def repository_path(root, name):
    if Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError(f"Not a repository-relative source path: {name}")
    return root / name


class Sources:
    def __init__(self, root, catalog, cache=None):
        self.root, self.catalog, self.cache = root, catalog, cache
        if catalog["schemaVersion"] != 1:
            raise ValueError("Unsupported W234 source catalog schema")
        self.archive_verified = False

    def open_source(self, pin):
        if not Path(pin["path"]).is_absolute():
            return repository_path(self.root, pin["path"]).open("rb")
        matches = [s for s in self.catalog["sources"] if s["path"] == pin["path"]]
        if len(matches) != 1:
            raise ValueError(f"Expected one complete source mapping: {pin['path']}")
        source = matches[0]
        if any(source[k] != pin[k] for k in ("sha256", "bytes")):
            raise ValueError(f"Historical pin disagrees with catalog: {pin['path']}")
        if self.cache:
            cached = self.cache / (pin["sha256"] + ".json")
            if cached.exists():
                return cached.open("rb")
        for name in source["repositoryPaths"]:
            candidate = repository_path(self.root, name)
            if candidate.exists():
                return candidate.open("rb")
        if "archiveEntry" in source:
            fixture = self.catalog["archive"]
            archive = repository_path(self.root, fixture["path"])
            if not self.archive_verified:
                check_file(archive, fixture)
                self.archive_verified = True
            # ZipExtFile owns a reference to the ZIP handle until it is closed.
            with zipfile.ZipFile(archive) as bundle:
                if bundle.getinfo(source["archiveEntry"]).file_size != pin["bytes"]:
                    raise ValueError(f"ZIP original entry size mismatch: {pin['path']}")
                return bundle.open(source["archiveEntry"])
        raise FileNotFoundError(f"Missing complete pinned source: {pin['path']}")

    def verify(self, pin):
        with self.open_source(pin) as stream:
            return checked(stream, pin["sha256"], pin["bytes"], pin["path"])


def verify(root, catalog, cache):
    sources = Sources(root, catalog, cache)
    pins = outputs = 0
    for name in MANIFESTS:
        manifest = json.loads((root / name).read_text())
        for pin in manifest["sourcePins"].values():
            sources.verify(pin)
            pins += 1
        check_file(root / manifest["generator"], {"sha256": manifest["generatorSha256"], "bytes": (root / manifest["generator"]).stat().st_size})
        for output, digest in manifest["outputSha256"].items():
            path = root / output
            check_file(path, {"sha256": digest, "bytes": path.stat().st_size})
            outputs += 1
    print(f"PASS: {len(MANIFESTS)} historical manifests, {pins} full source-pin checks, 4 generator hashes, {outputs} output hashes; no legacy /tmp paths read")
    return sources


def populate_cache(sources, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for pin in sources.catalog["sources"]:
        target = destination / (pin["sha256"] + ".json")
        if target.exists():
            check_file(target, pin)
            continue
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination, prefix=".w234-", delete=False) as out:
                temporary = Path(out.name)
                with sources.open_source(pin) as stream:
                    while block := stream.read(65536):
                        out.write(block)
            check_file(temporary, pin)
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        print(f"Cached exact original {pin['id']}: {target}")


def rebuild(args, catalog):
    if args.rebuild_archive.exists():
        raise FileExistsError(f"Refusing to overwrite archive: {args.rebuild_archive}")
    originals = []
    for key, path in (("inventory", args.inventory), ("plugSets", args.plug_sets), ("manifest", args.manifest), ("clarity", args.clarity)):
        pin = next(s for s in catalog["sources"] if s["id"] == key)
        if path is not None:
            raw = path.read_bytes()
        elif any((args.root / name).exists() for name in pin["repositoryPaths"]):
            raw = next(args.root / name for name in pin["repositoryPaths"] if (args.root / name).exists()).read_bytes()
        elif args.recover and pin.get("url"):
            with urllib.request.urlopen(pin["url"], timeout=60) as response:
                raw = response.read(pin["bytes"] + 1)
        else:
            option = "plug-sets" if key == "plugSets" else key
            raise ValueError(f"Provide complete --{option} original; absent historical evidence is never accepted")
        checked(io.BytesIO(raw), pin["sha256"], pin["bytes"], key)
        originals.append((pin["archiveEntry"], raw))
    args.rebuild_archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.rebuild_archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for entry, raw in originals:
            info = zipfile.ZipInfo(entry, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    check_file(args.rebuild_archive, catalog["archive"])
    print(f"PASS: reproducible complete original archive {args.rebuild_archive}")


def self_test(repository_root, real_catalog):
    original = b"complete original source including unrelated records\n"
    pin = {"path": "/absent-w234-source.json", "sha256": hashlib.sha256(original).hexdigest(), "bytes": len(original), "repositoryPaths": ["absent-preserved.json"], "archiveEntry": "original.json"}
    rejected = 0

    def rejects(action):
        nonlocal rejected
        try:
            action()
        except (ValueError, OSError, KeyError, zipfile.BadZipFile):
            rejected += 1
        else:
            raise AssertionError("Negative case unexpectedly accepted")

    for bad, size in ((original[:-1], len(original)), (original + b"x", len(original)), (b"X" + original[1:], len(original))):
        rejects(lambda bad=bad, size=size: checked(io.BytesIO(bad), pin["sha256"], size, "negative"))
    with tempfile.TemporaryDirectory(prefix="w234-source-self-test-") as directory:
        root = Path(directory)
        with zipfile.ZipFile(root / "original.zip", "w") as bundle:
            bundle.writestr("original.json", original)
        archive = (root / "original.zip").read_bytes()
        catalog = {"schemaVersion": 1, "sources": [pin], "archive": {"path": "original.zip", "sha256": hashlib.sha256(archive).hexdigest(), "bytes": len(archive)}}
        assert Sources(root, catalog).verify(pin) == len(original)
        rejects(lambda: Sources(root, catalog).verify(dict(pin, sha256="0" * 64)))
        rejects(lambda: Sources(root, catalog).verify(dict(pin, path="/unknown.json")))
        rejects(lambda: Sources(root, catalog).verify(dict(pin, path="../escape.json")))
        altered = json.loads(json.dumps(catalog)); altered["sources"][0]["archiveEntry"] = "missing.json"
        rejects(lambda: Sources(root, altered).verify(pin))
        (root / "original.zip").write_bytes(b"X" + archive[1:])
        rejects(lambda: Sources(root, catalog).verify(pin))
        (root / "original.zip").unlink()
        rejects(lambda: Sources(root, catalog).verify(pin))
    print(f"PASS: complete-source offline ZIP resolution and {rejected} fail-closed negative cases")
    with tempfile.TemporaryDirectory(prefix="w234-four-originals-offline-") as directory:
        isolated = Path(directory)
        archive_name = real_catalog["archive"]["path"]
        archive_link = isolated / archive_name
        archive_link.parent.mkdir(parents=True)
        archive_link.symlink_to(repository_root / archive_name)
        assert not (isolated / "art/weapons/w83").exists()
        sources = Sources(isolated, real_catalog)
        for source in real_catalog["sources"]:
            sources.verify(source)
    print("PASS: all 4 complete real originals resolve from ZIP with W83 repository sources absent; no legacy /tmp paths read")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--catalog", type=Path, help="Optional catalog location, for isolated review")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--populate-cache", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--rebuild-archive", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--plug-sets", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--clarity", type=Path)
    parser.add_argument("--recover", action="store_true", help="Explicit network recovery when rebuilding only")
    args = parser.parse_args()
    if args.populate_cache and args.cache_dir is None:
        parser.error("--populate-cache requires explicit --cache-dir")
    if args.recover and not args.rebuild_archive:
        parser.error("--recover requires --rebuild-archive")
    root = args.root.resolve()
    catalog = json.loads((args.catalog or root / CATALOG).read_text())
    if args.self_test:
        self_test(root, catalog)
    if args.rebuild_archive:
        rebuild(args, catalog)
        return
    cache = args.cache_dir
    if cache is None and os.environ.get("DESTINY_PROFILE_SOURCE_CACHE"):
        cache = Path(os.environ["DESTINY_PROFILE_SOURCE_CACHE"])
    sources = verify(root, catalog, cache)
    if args.populate_cache:
        populate_cache(sources, args.cache_dir)


if __name__ == "__main__":
    main()
