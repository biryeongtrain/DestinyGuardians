#!/usr/bin/env python3
"""Read-only item -> geometry/special base -> model parent ZIP closure audit.

Stdlib only. Each item JSON is released before reading the next; model JSONs
are reduced immediately to a cached parent string (never retained as trees).
Minecraft refs are external vanilla dependencies and are deliberately skipped.
Exit: 0 complete closure, 1 missing custom model/invalid input data, 2 I/O/CLI.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile


RESOURCE = re.compile(r"[a-z0-9_.-]+:[a-z0-9/._-]+\Z")
JSON_ERRORS = (ValueError, UnicodeError, RecursionError, zipfile.BadZipFile)


def resource_id(value):
    """Unqualified resource locations always default to minecraft, not owner."""
    if not isinstance(value, str):
        raise ValueError("model reference must be a string")
    ref = value if ":" in value else "minecraft:" + value
    if not RESOURCE.fullmatch(ref):
        raise ValueError("invalid model resource location: " + repr(value))
    return ref


def is_asset(name, kind):
    parts = name.split("/")
    return (len(parts) >= 4 and parts[0] == "assets" and bool(parts[1])
            and parts[2] == kind and name.endswith(".json"))


def dictionaries(value):
    """Iterative traversal, including all selector branches and nested lists."""
    pending = [iter((value,))]
    while pending:
        try:
            node = next(pending[-1])
        except StopIteration:
            pending.pop()
            continue
        if isinstance(node, dict):
            yield node
            pending.append(iter(node.values()))
        elif isinstance(node, list):
            pending.append(iter(node))


class Closure:
    def __init__(self, archive):
        self.archive = archive
        self.parents = {}  # custom resource id -> parent id or None; no JSON
        self.done = set()
        self.vanilla = set()
        self.missing = {}
        self.errors = []
        self.model_raw_bytes = 0

    def error(self, path, message):
        self.errors.append({"path": path, "message": message})

    def visit(self, root, item):
        chain = []
        active = set()
        current = root
        while current is not None:
            if current.startswith("minecraft:"):
                self.vanilla.add(current)
                break
            if current in active:
                self.error(item, "model parent cycle: " + " -> ".join(chain + [current]))
                break
            if current in self.done:
                break
            chain.append(current)
            active.add(current)
            namespace, name = current.split(":", 1)
            path = f"assets/{namespace}/models/{name}.json"
            try:
                info = self.archive.getinfo(path)
            except KeyError:
                self.missing[current] = {
                    "model": current, "expected_path": path,
                    "first_item": item, "chain": list(chain),
                }
                break
            try:
                with self.archive.open(info) as stream:
                    data = json.load(stream)
                if not isinstance(data, dict):
                    raise ValueError("model JSON must be an object")
                parent = resource_id(data["parent"]) if "parent" in data else None
                del data
            except JSON_ERRORS as exc:
                self.error(path, str(exc))
                break
            self.parents[current] = parent
            self.model_raw_bytes += info.file_size
            current = parent
        self.done.update(active)


def top(rows, metric):
    return sorted(rows, key=lambda row: (-row[metric], row["path"]))[:10]


def audit_pack(pack):
    pack = Path(pack)
    before = pack.stat()
    digest = hashlib.sha256()
    with pack.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    rows = []
    roots = set()
    tint_types = Counter()
    groups = {}
    with zipfile.ZipFile(pack, "r") as archive:
        closure = Closure(archive)
        names = set()
        infos = archive.infolist()
        for info in infos:
            path = info.filename
            if is_asset(path, "items") or is_asset(path, "models"):
                if path in names:
                    closure.error(path, "duplicate ZIP item/model path")
                names.add(path)
            if not is_asset(path, "items"):
                continue
            refs = set()
            row = {"path": path, "raw_bytes": info.file_size,
                   "compressed_bytes": info.compress_size,
                   "geometry_count": 0, "special_base_count": 0,
                   "reference_count": 0, "unique_refs": 0, "tint_source_count": 0}
            try:
                with archive.open(info) as stream:
                    data = json.load(stream)
                if not isinstance(data, dict) or not isinstance(data.get("model"), dict):
                    raise ValueError("item JSON must contain an object-valued model")
                for node in dictionaries(data):
                    kind = node.get("type")
                    if kind in ("minecraft:model", "model"):
                        row["geometry_count"] += 1
                        key = "model"
                        tints = node.get("tints", [])
                        if not isinstance(tints, list):
                            raise ValueError("geometry tints must be a list")
                        row["tint_source_count"] += len(tints)
                        for tint in tints:
                            if not isinstance(tint, dict) or not isinstance(tint.get("type"), str):
                                raise ValueError("tint source must be an object with a type")
                            tint_types[tint["type"]] += 1
                    elif kind in ("minecraft:special", "special"):
                        row["special_base_count"] += 1
                        key = "base"
                    else:
                        continue
                    # Selector `model` and special renderer `model` are objects.
                    # Only these typed fields are geometry resource locations.
                    try:
                        refs.add(resource_id(node.get(key)))
                        row["reference_count"] += 1
                    except ValueError as exc:
                        closure.error(path, str(exc))
            except JSON_ERRORS as exc:
                closure.error(path, str(exc))
            finally:
                # Loop variables can otherwise retain the final subtree while
                # json.load constructs the next (potentially very large) item.
                data = node = tints = tint = None
            row["unique_refs"] = len(refs)
            roots.update(refs)
            for ref in sorted(refs):
                closure.visit(ref, path)
            rows.append(row)
            parts = path.split("/")
            group = "/".join(parts[:4]) if len(parts) > 4 else "/".join(parts[:3])
            stats = groups.setdefault(group, {"count": 0, "raw_bytes": 0})
            stats["count"] += 1
            stats["raw_bytes"] += info.file_size
        item_totals = {key: sum(row[key] for row in rows) for key in (
            "raw_bytes", "compressed_bytes", "geometry_count", "special_base_count",
            "reference_count", "tint_source_count")}
        item_totals.update({
            "count": len(rows), "unique_refs": len(roots),
            "unique_custom_refs": sum(not ref.startswith("minecraft:") for ref in roots),
            "max_raw_bytes": max((row["raw_bytes"] for row in rows), default=0),
            "max_unique_refs": max((row["unique_refs"] for row in rows), default=0),
            "max_tint_source_count": max((row["tint_source_count"] for row in rows), default=0),
            "top_by_raw_bytes": top(rows, "raw_bytes"),
            "top_by_unique_refs": top(rows, "unique_refs"),
            "top_by_tint_source_count": top(rows, "tint_source_count"),
            "tint_source_types": dict(sorted(tint_types.items())),
            "groups": dict(sorted(groups.items())),
        })
        after = pack.stat()
        unchanged = all(getattr(before, field) == getattr(after, field)
                        for field in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns"))
        if not unchanged:
            closure.error(str(pack), "input ZIP changed during audit; discard measurements")
        if not rows:
            closure.error(str(pack), "no assets/*/items/**/*.json entries found")
        return {
            "schema_version": 1,
            "pack": {"path": str(pack.resolve()), "zip_bytes": before.st_size,
                     "sha256": digest.hexdigest(), "unchanged_during_audit": unchanged,
                     "entry_count": len(infos), "raw_bytes": sum(i.file_size for i in infos)},
            "items": item_totals,
            "closure": {
                "ok": not closure.missing and not closure.errors,
                "unique_custom_refs": len(closure.done),
                "custom_models_loaded": len(closure.parents),
                "custom_model_raw_bytes": closure.model_raw_bytes,
                "parent_edge_count": sum(p is not None for p in closure.parents.values()),
                "unique_vanilla_refs_skipped": len(closure.vanilla),
                "missing_custom_count": len(closure.missing),
                "missing_custom_models": [closure.missing[k] for k in sorted(closure.missing)],
                "error_count": len(closure.errors), "errors": closure.errors,
            },
        }


def compare_reports(baseline, current):
    if baseline.get("schema_version") != current["schema_version"]:
        raise ValueError("comparison report schema_version does not match")
    deltas = {}
    for section in ("pack", "items", "closure"):
        for key, value in current[section].items():
            old = baseline[section].get(key)
            if type(value) is int and type(old) is int:
                deltas[f"{section}.{key}"] = value - old
    old_missing = {row["model"] for row in baseline["closure"]["missing_custom_models"]}
    new_missing = {row["model"] for row in current["closure"]["missing_custom_models"]}
    return {"baseline_sha256": baseline["pack"]["sha256"],
            "delta_current_minus_baseline": deltas,
            "missing_added": sorted(new_missing - old_missing),
            "missing_resolved": sorted(old_missing - new_missing)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path, help="resource pack ZIP (opened read-only)")
    parser.add_argument("--report", type=Path, help="write full JSON report; otherwise print it")
    parser.add_argument("--compare", type=Path, help="baseline JSON report; include metric deltas")
    args = parser.parse_args(argv)
    try:
        if args.report and args.report.resolve() in {
                args.pack.resolve(), args.compare.resolve() if args.compare else None}:
            raise ValueError("report output must differ from ZIP and baseline report")
        baseline = json.loads(args.compare.read_text()) if args.compare else None
        report = audit_pack(args.pack)
        if baseline is not None:
            report["comparison"] = compare_reports(baseline, report)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.report:
            args.report.write_text(rendered, encoding="utf-8")
            print(json.dumps({"report": str(args.report.resolve()),
                              "ok": report["closure"]["ok"],
                              "item_count": report["items"]["count"],
                              "item_raw_bytes": report["items"]["raw_bytes"],
                              "missing_custom_count": report["closure"]["missing_custom_count"],
                              "error_count": report["closure"]["error_count"]}))
        else:
            print(rendered, end="")
        return 0 if report["closure"]["ok"] else 1
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print("pack_model_closure_w236: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
