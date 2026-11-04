#!/usr/bin/env python3
"""Offline W107 product audit. No subprocesses, builds, runtime or network access.

Run with `rtk proxy python3 scripts/qa/audit_use_trace_w107.py`.
`--check` recomputes the audit and verifies both frozen reports without writing.
Only product-audit.json and product-audit.md are written by the default mode.
The reviewed source/JAR allowlists are exact; no nested-class family exemption.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

QA = "docs/qa/2026-10-25/w107"
OLD = "docs/qa/2026-10-25/w106"
IMPLEMENTATION = "art/qa/w106/implementation.json"
JAR = "build/libs/destiny-guardians-0.1.0+26.3.jar"
VISION_JAR = "build/libs/coppergolem-vision-client-26.3-1.0.0-SNAPSHOT.jar"
OLD_SHA = "44dd3c7ac4194882f07a29880d01cfe1400807e4ee4cef6c7cfdbc9cf383f4bb"
NEW_SHA = "d7320b9334e9aa5d42d46be7c26e5931f0aa1a6445d66dc9261a5fd577a916c7"
PACK_SHA = "ebce97894607eae505d1347f4c41d5210797fab956bd1ef0e0f0eeb84606812e"
SOURCE_PINS = {
    "src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java": "973879293e2f6b892ecd79bc26150da149096f5c4392c8f77928685073b08fc5",
    "src/main/resources/destiny.mixins.json": "961dc2086e8fc49c5184217f118bd3694ba8e7595977008666ac6f9d74ac6c9a",
    "src/main/java/kim/biryeong/destiny/debug/WeaponUseTrace.java": "b1460ef2dec5c6bb7b9f6d3d44c885545eef5b6b183d3d53d6c406179c2097d5",
    "src/main/java/kim/biryeong/destiny/mixin/WeaponUseTraceMixin.java": "a4c1ab97a011accd673f50d870f6f17da69ce2983c0e00d4de88121c676b67df",
    "src/test/java/kim/biryeong/destiny/debug/WeaponUseTraceTest.java": "135be9ab4dee7e8ea89a87602933a2896d67e55e2085490e0213c74acbb4a5a5",
}
MODIFIED_SOURCE = {"src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java",
                   "src/main/resources/destiny.mixins.json"}
NESTED = {"kim/biryeong/destiny/weapon/WeaponRuntime$" + n + ".class"
          for n in ("FlightSnapshot", "GlaiveStatus", "HitDamage", "SwordStatus")}
MODIFIED_JAR = NESTED | {"destiny.mixins.json", "kim/biryeong/destiny/weapon/WeaponRuntime.class"}
ADDED_JAR = {"kim/biryeong/destiny/debug/WeaponUseTrace$TraceLimit.class",
             "kim/biryeong/destiny/debug/WeaponUseTrace.class",
             "kim/biryeong/destiny/mixin/WeaponUseTraceMixin.class"}
NEW_TESTS = {
    ("kim.biryeong.destiny.debug.WeaponUseTraceTest", name + "()") for name in (
        "rejectsInvalidCapsAndStartsEveryValidCapEmpty",
        "admitsExactlyTheCapAndNeverReopensAfterExhaustion",
        "concurrentAdmissionNeverExceedsCapOrLosesSuccessfulTakes",
        "optInAndExactPlayerSelectionPrecedeExistingStateOnlyProjection",
        "boundedPayloadUsesOnlyReviewedReadOnlyProjectionsAndNoSecretsOrSends",
        "registeredPacketObserversRunAfterExactMainThreadCheckWithoutCancellationOrMutation")
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def delta(before, after):
    return dict(added=sorted(after.keys() - before.keys()),
                removed=sorted(before.keys() - after.keys()),
                modified=sorted(k for k in before.keys() & after.keys() if before[k] != after[k]))


def normalize_lines(raw):
    """Zero ONLY the u2 line_number values in method Code/LineNumberTable.

    Preserve the entire class layout, constant pool, instructions, exception
    tables, start_pc values and every other attribute byte. Return exact offsets
    so equal normalized bytes prove all actual drift is in those line values.
    """
    class Reader:
        def __init__(self, start=0, end=None):
            self.pos, self.end = start, len(raw) if end is None else end

        def take(self, n):
            if n < 0 or self.pos + n > self.end:
                raise ValueError("truncated classfile")
            result = raw[self.pos:self.pos + n]
            self.pos += n
            return result

        def u2(self):
            return struct.unpack(">H", self.take(2))[0]

        def u4(self):
            return struct.unpack(">I", self.take(4))[0]

        def done(self):
            if self.pos != self.end:
                raise ValueError("unparsed classfile bytes")

    r = Reader()
    if r.take(4) != b"\xca\xfe\xba\xbe":
        raise ValueError("invalid classfile magic")
    r.take(4)
    count = r.u2()
    pool = [None]
    while len(pool) < count:
        tag = r.take(1)[0]
        if tag == 1:
            payload = r.take(r.u2())
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            payload = r.take(4)
        elif tag in (5, 6):
            payload = r.take(8)
        elif tag in (7, 8, 16, 19, 20):
            payload = r.take(2)
        elif tag == 15:
            payload = r.take(3)
        else:
            raise ValueError(f"unknown constant-pool tag {tag}")
        pool.append(payload if tag == 1 else None)
        if tag in (5, 6):
            pool.append(None)
    if len(pool) != count:
        raise ValueError("invalid constant-pool count")
    normalized, lines = bytearray(raw), []

    def utf(index):
        if not 0 < index < count or pool[index] is None:
            raise ValueError("invalid UTF constant-pool reference")
        return pool[index].decode("utf-8", errors="backslashreplace")

    def attributes(reader, context, method=None):
        for _ in range(reader.u2()):
            name, size = utf(reader.u2()), reader.u4()
            start = reader.pos
            reader.take(size)
            q = Reader(start, start + size)
            if name == "Code":
                if context != "method":
                    raise ValueError("Code outside method")
                q.take(4)
                q.take(q.u4())
                q.take(q.u2() * 8)
                attributes(q, "code", method)
                q.done()
            elif name == "LineNumberTable":
                if context != "code":
                    raise ValueError("LineNumberTable outside Code")
                for _ in range(q.u2()):
                    pc, offset = q.u2(), q.pos
                    line = q.u2()
                    normalized[offset:offset + 2] = b"\0\0"
                    lines.append(dict(method=method, start_pc=pc, offset=offset, line=line))
                q.done()

    r.take(6)
    r.take(r.u2() * 2)
    for context in ("field", "method"):
        for _ in range(r.u2()):
            r.take(2)
            name, descriptor = utf(r.u2()), utf(r.u2())
            attributes(r, context, name + descriptor)
    attributes(r, "class")
    r.done()
    return bytes(normalized), lines


class Audit:
    def __init__(self, root, vision):
        self.root, self.vision = root, vision
        self.inputs, self.anomalies, self.results = {}, [], {}

    def label(self, path):
        path = path.resolve()
        if path.is_relative_to(self.root):
            return path.relative_to(self.root).as_posix()
        if path.is_relative_to(self.vision):
            return "vision://" + path.relative_to(self.vision).as_posix()
        return str(path)

    def read(self, path):
        path = Path(path)
        if not path.is_absolute():
            path = self.root / path
        data = path.read_bytes()
        label, pin = self.label(path), sha(data)
        if label in self.inputs:
            self.need(self.inputs[label][1] == pin, "input_changed_between_reads", label)
        self.inputs[label] = (path, pin)
        return data

    def digest(self, path):
        return sha(self.read(path))

    def load(self, path):
        return json.loads(self.read(path))

    def need(self, condition, code, detail=None):
        if not condition:
            self.anomalies.append(dict(code=code, detail=detail))
        return bool(condition)

    def inventory(self, folder, base=None):
        base = base or self.root
        return {p.relative_to(base).as_posix(): self.digest(p)
                for p in sorted(folder.rglob("*")) if p.is_file()}

    def archive(self, path):
        with zipfile.ZipFile(io.BytesIO(self.read(path))) as jar:
            names = jar.namelist()
            self.need(len(names) == len(set(names)), "duplicate_zip_entry", self.label(self.root / path) if not Path(path).is_absolute() else self.label(path))
            files = {n: jar.read(n) for n in names if not n.endswith("/")}
        return files, names

    def run_section(self, name, function):
        try:
            self.results[name] = function()
        except (OSError, ValueError, KeyError, TypeError, ET.ParseError, zipfile.BadZipFile, struct.error) as exc:
            self.anomalies.append(dict(code=name + "_unavailable_or_invalid", detail=str(exc)))
            self.results[name] = dict(complete=False)

    def historical(self):
        seal = self.load(QA + "/previous-seal.json")
        self.need(self.digest(QA + "/previous-seal.json") == "6e241237555ec31929e2ef4211e7c063edb11a73029f890e28bb0d60bf85e11b", "previous_seal_pin")
        self.need(len(seal) == 629, "previous_seal_count", len(seal))
        observed = {p: self.digest(p) if (self.root / p).is_file() else None for p in sorted(seal)}
        changed = [p for p in seal if observed[p] != seal[p]]
        self.need(not changed, "historical_paths_changed_or_missing", changed)
        return dict(paths=len(seal), intact=len(seal) - len(changed), changed_or_missing=changed,
                    seal_sha256=self.digest(QA + "/previous-seal.json"))

    def source(self):
        old = self.load(IMPLEMENTATION)
        self.need(self.digest(IMPLEMENTATION) == "1ac0c8d690461ce268cae01e5eabf2d8dda5c712267ed01b28f323fbbef39d44", "w106_implementation_pin")
        before = {k: v for k, v in old["sha256"].items() if k.startswith("src/")}
        after = self.inventory(self.root / "src")
        change = delta(before, after)
        expected = dict(modified=sorted(MODIFIED_SOURCE), added=sorted(SOURCE_PINS.keys() - MODIFIED_SOURCE), removed=[])
        self.need(change == expected, "unexpected_source_delta", change)
        for path, pin in SOURCE_PINS.items():
            self.need(after.get(path) == pin, "reviewed_source_pin", path)
        for path in MODIFIED_SOURCE:
            self.need(self.digest(QA + "/before/" + path) == before[path], "w106_before_source_pin", path)
        assets = old["clientAssets"]
        asset_after = self.inventory(self.root / "src/main/resources/assets")
        asset_delta = delta(assets, asset_after)
        self.need(len(assets) == 7219 and all(not v for v in asset_delta.values()), "client_assets_changed", asset_delta)
        game_before = {k: v for k, v in before.items() if k.startswith("src/gametest/")}
        game_after = {k: v for k, v in after.items() if k.startswith("src/gametest/")}
        self.need(bool(game_before) and game_before == game_after, "gametest_source_or_registry_changed", delta(game_before, game_after))
        return dict(previous_source_paths=len(before), current_source_paths=len(after), delta=change,
                    delta_pins={k: dict(before=before.get(k), after=after.get(k)) for k in sorted(set().union(*map(set, change.values())))},
                    current_source_inventory_sha256=sha(encoded(after)), client_assets=dict(paths=len(assets), delta=asset_delta,
                    inventory_sha256=sha(encoded(asset_after))), gametest=dict(paths=len(game_after), unchanged=game_before == game_after,
                    registry="src/gametest/resources/fabric.mod.json", inventory_sha256=sha(encoded(game_after))))

    def product_jar(self):
        before, old_names = self.archive(OLD + "/product.jar")
        after, names = self.archive(JAR)
        bp, ap = ({k: sha(v) for k, v in files.items()} for files in (before, after))
        change = delta(bp, ap)
        self.need(self.digest(OLD + "/product.jar") == OLD_SHA, "previous_product_jar_pin")
        self.need(self.digest(JAR) == NEW_SHA, "reviewed_product_jar_pin")
        self.need(change == dict(added=sorted(ADDED_JAR), modified=sorted(MODIFIED_JAR), removed=[]), "unexpected_jar_delta", change)
        # Include directory entries and preserve order of all historical ZIP names.
        old_name_set = set(old_names)
        self.need([n for n in names if n in old_name_set] == old_names, "historical_jar_names_or_order_changed")
        self.need(set(names) - old_name_set == ADDED_JAR, "unexpected_jar_archive_names", sorted(set(names) - old_name_set))
        proof = {}
        for name in sorted(NESTED):
            a, al = normalize_lines(before[name])
            b, bl = normalize_lines(after[name])
            layout_a = [{k: v for k, v in row.items() if k != "line"} for row in al]
            layout_b = [{k: v for k, v in row.items() if k != "line"} for row in bl]
            same = a == b and layout_a == layout_b
            self.need(same, "nested_class_not_line_number_only", name)
            offsets = sorted(i for i, (x, y) in enumerate(zip(before[name], after[name])) if x != y)
            changes = [dict(method=x["method"], start_pc=x["start_pc"], byte_offset=x["offset"],
                            before=x["line"], after=y["line"]) for x, y in zip(al, bl) if x != y]
            self.need(bool(offsets) and bool(changes), "missing_nested_metadata_delta", name)
            proof[name] = dict(before_sha256=bp[name], after_sha256=ap[name], before_size=len(before[name]), after_size=len(after[name]),
                               before_normalized_sha256=sha(a), after_normalized_sha256=sha(b), line_number_only=same,
                               changed_byte_offsets=offsets, line_number_changes=changes)
        assets_before = {k: v for k, v in bp.items() if k.startswith("assets/")}
        assets_after = {k: v for k, v in ap.items() if k.startswith("assets/")}
        self.need(bool(assets_before) and assets_before == assets_after, "jar_client_assets_changed")
        archive = self.root / QA / "product.jar"
        # The central owner creates this copy; this auditor never writes it.
        if archive.exists():
            self.need(self.read(archive) == self.read(JAR), "archived_product_jar_mismatch")
        return dict(previous_sha256=self.digest(OLD + "/product.jar"), current_sha256=self.digest(JAR),
                    previous_entries=len(bp), current_entries=len(ap), delta=change,
                    delta_pins={k: dict(before=bp.get(k), after=ap.get(k)) for k in sorted(set().union(*map(set, change.values())))},
                    unchanged_asset_entries=len(assets_before), nested_class_proof=proof,
                    proof_method="Parse classfile; zero only u2 line_number values inside method Code/LineNumberTable. Compare every remaining byte and exact line-table layout, including start_pc. No other metadata is ignored.",
                    central_archive=dict(path=QA + "/product.jar", present=archive.exists(), required_for_this_built_jar_audit=False))

    def runtime(self):
        runtime = self.load(QA + "/native/runtime-provenance.json")
        result = {}
        for name, root, jar_path in (("server", self.root, self.root / JAR), ("vision", self.vision, self.vision / VISION_JAR)):
            pins = runtime[name]
            current = self.inventory(root / "src/main", root)
            classes, _ = self.archive(jar_path)
            classes = {k: sha(v) for k, v in classes.items() if k.endswith(".class")}
            sd, cd = delta(pins["sourcePins"], current), delta(pins["classPins"], classes)
            self.need(bool(current) and not any(sd.values()), name + "_runtime_source_pin_delta", sd)
            self.need(bool(classes) and not any(cd.values()), name + "_runtime_class_pin_delta", cd)
            result[name] = dict(source_paths=len(current), class_entries=len(classes), source_delta=sd, class_delta=cd,
                                source_inventory_sha256=sha(encoded(current)), class_inventory_sha256=sha(encoded(classes)),
                                jar_path=self.label(jar_path), jar_sha256=self.digest(jar_path))
        vision_archive = QA + "/vision-final/" + Path(VISION_JAR).name
        self.need(self.read(vision_archive) == self.read(self.vision / VISION_JAR), "vision_archived_jar_mismatch")
        return result

    def xml(self, folder, interval=None):
        counts = dict(tests=0, failures=0, errors=0, skipped=0)
        ids, fresh = [], {}
        paths = sorted(folder.glob("TEST-*.xml"))
        for p in paths:
            doc = ET.fromstring(self.read(p))
            local = {k: int(doc.attrib[k]) for k in counts}
            for k in counts:
                counts[k] += local[k]
            cases = doc.findall("testcase")
            self.need(local["tests"] == len(cases), "xml_declared_case_count", self.label(p))
            actual = dict(failures=sum(t.find("failure") is not None for t in cases),
                          errors=sum(t.find("error") is not None for t in cases),
                          skipped=sum(t.find("skipped") is not None for t in cases))
            self.need(all(actual[k] == local[k] for k in actual), "xml_failure_count_mismatch", self.label(p))
            ids.extend((t.attrib["classname"], t.attrib["name"]) for t in cases)
            if interval:
                stamp = datetime.fromisoformat(doc.attrib["timestamp"].replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                # XML embeds millisecond precision; filesystem mtimes can have nanoseconds.
                fresh[p.name] = interval[0] <= stamp.timestamp() <= interval[1] and interval[0] <= p.stat().st_mtime <= interval[1] + 0.001
        self.need(bool(paths) and len(ids) == len(set(ids)), "missing_or_duplicate_junit_identities", str(folder))
        return counts, set(ids), fresh, len(paths)

    def gates(self):
        old_counts, old_ids, _, old_files = self.xml(self.root / OLD / "gate-2-xml")
        self.need(old_counts == dict(tests=754, failures=0, errors=0, skipped=0) and len(old_ids) == 754, "w106_junit_baseline")
        result, windows = [], []
        for n in (1, 2):
            exit_data = self.load(QA + f"/gate-{n}-exit.json")
            window = (exit_data["startedAt"], exit_data["finishedAt"])
            windows.append(window)
            counts, ids, fresh, files = self.xml(self.root / QA / f"gate-{n}-xml", window)
            self.need(exit_data["gate"] == n and exit_data["returncode"] == 0 and window[0] < window[1], "gate_execution", n)
            self.need(bool(fresh) and all(fresh.values()) and fresh == exit_data["xmlFreshness"], "gate_xml_not_fresh", dict(gate=n, failed=[k for k, v in fresh.items() if not v]))
            self.need(counts == dict(tests=760, failures=0, errors=0, skipped=0), "gate_junit_counts", dict(gate=n, counts=counts))
            self.need(ids == old_ids | NEW_TESTS, "gate_junit_identity_delta", dict(gate=n, missing=sorted(old_ids - ids), added=sorted(ids - old_ids)))
            log = self.read(QA + f"/gate-{n}.log").decode()
            passed = [int(v) for v in re.findall(r"All (\d+) required tests passed", log)]
            complete = [int(v) for v in re.findall(r"(\d+) GAME TESTS COMPLETE", log)]
            executed = re.findall(r"(\d+) actionable tasks: (\d+) executed[^\n]*", log)
            self.need(passed == [869] and complete == [869], "gate_gametest_counts", dict(gate=n, passed=passed, complete=complete))
            self.need(executed == [("20", "20")] and "BUILD SUCCESSFUL" in log and "BUILD FAILED" not in log,
                      "gate_not_fully_forced_success", n)
            self.need(re.search(r"^> Task :test\s*$", log, re.M) is not None and re.search(r"^> Task :runGameTest\s*$", log, re.M) is not None,
                      "gate_test_task_not_executed", n)
            jar_pin = self.read(QA + f"/gate-{n}-jar.sha256").decode().strip()
            self.need(jar_pin == NEW_SHA == self.digest(JAR), "gate_product_jar_pin", n)
            result.append(dict(gate=n, returncode=exit_data["returncode"], xml_files=files, xml_fresh=all(fresh.values()),
                               junit=counts, preserved_old_identities=len(ids & old_ids), new_identities=sorted(ids - old_ids),
                               required_gametests=passed, completed_gametests=complete, executed_tasks=20, jar_sha256=jar_pin))
        self.need(windows[0][1] <= windows[1][0], "gates_overlap_or_reversed")
        return dict(previous_xml_files=old_files, previous_junit=old_counts, gates=result)

    def vision_tests(self):
        archived = self.root / QA / "vision-final/test-results"
        current = self.vision / "build/test-results/test"
        counts, ids, _, files = self.xml(archived)
        self.need(counts == dict(tests=52, failures=0, errors=0, skipped=0) and len(ids) == 52, "vision_junit_counts", counts)
        archive_pins = {p.name: self.digest(p) for p in sorted(archived.glob("TEST-*.xml"))}
        current_pins = {p.name: self.digest(p) for p in sorted(current.glob("TEST-*.xml"))}
        self.need(archive_pins == current_pins, "vision_current_xml_differs_from_archive")
        build_log = self.read(QA + "/vision-build.log").decode()
        self.need("BUILD SUCCESSFUL" in build_log and "BUILD FAILED" not in build_log and
                  re.search(r"^> Task :test\s*$", build_log, re.M) is not None, "vision_build_log")
        log = self.read(QA + "/vision-node-tests.log").decode()
        summary = {k: [int(v) for v in re.findall(r"^ℹ " + k + r" (\d+)\s*$", log, re.M)]
                   for k in ("tests", "pass", "fail", "cancelled", "skipped", "todo")}
        expected = {k: [31 if k in ("tests", "pass") else 0] for k in summary}
        self.need(summary == expected, "vision_node_test_counts", summary)
        return dict(junit=counts, xml_files=files, identities=sorted(ids), xml_inventory_sha256=sha(encoded(archive_pins)),
                    current_xml_matches_archive=archive_pins == current_pins, node_summary=summary,
                    freshness_limit="Vision has no gate start/finish freshness record; archived XML equals the current build XML. Build log records an executed test task.")

    def pack(self):
        before = self.read(OLD + "/native/resource_pack.zip")
        actual = self.read(QA + "/native/resource_pack.zip")
        provenance = self.load(QA + "/native/pack-provenance.json")
        cache = Path(provenance["actualCache"])
        cached = self.read(cache)
        self.need(sha(before) == PACK_SHA and actual == before and cached == actual, "actual_pack_or_cache_changed")
        self.need(provenance["actualPackSha256"] == PACK_SHA and all(provenance[k] is True for k in
                  ("matchesW106ByteForByte", "cacheByteIdentical", "packUnchanged")), "pack_provenance_claim_mismatch")
        return dict(previous_path=OLD + "/native/resource_pack.zip", actual_path=QA + "/native/resource_pack.zip",
                    actual_cache=str(cache), bytes=len(actual), sha256=sha(actual),
                    byte_equal_w106=before == actual, byte_equal_cache=actual == cached)

    def execute(self):
        self.digest(Path(__file__).resolve())
        for name, function in (("historical_w106", self.historical), ("source", self.source),
                               ("product_jar", self.product_jar), ("runtime_provenance", self.runtime),
                               ("gates", self.gates), ("vision_tests", self.vision_tests), ("actual_pack", self.pack)):
            self.run_section(name, function)
        # Catch concurrent replacement after a section was checked, without emitting time values.
        for label, (path, pin) in sorted(self.inputs.items()):
            self.need(path.is_file() and sha(path.read_bytes()) == pin, "input_changed_during_audit", label)
        return dict(schema=1, stage="W107", status="FAIL" if self.anomalies else "PASS", results=self.results,
                    anomalies=self.anomalies, input_sha256={k: v[1] for k, v in sorted(self.inputs.items())},
                    limits=["Offline evidence audit only; no builds, Minecraft runtime, Computer Use, network or child workers were executed.",
                            "Source/class correspondence is checked against recorded runtime-provenance pins and current artifacts; no independent recompilation is claimed.",
                            "Native PNG/contact review belongs to the central owner; this audit does not claim visual, audio or input acceptance.",
                            "The central owner supplies the W107 product.jar archive. Its absence is recorded; the built JAR and both gate JAR pins are audited directly.",
                            "PASS establishes this W107 product evidence boundary, not completion of the overall product goal."])


def markdown(report):
    r = report["results"]
    lines = [f"# W107 independent product audit: {report['status']}", "",
             "Offline and deterministic. Only the audit script and these two reports are owned by this auditor.", ""]
    if report["status"] == "PASS":
        s, j = r["source"], r["product_jar"]
        lines.extend([f"- W106 seal: {r['historical_w106']['intact']}/629 historical paths intact; implementation manifest SHA-256 verified.",
                      f"- Source: {s['previous_source_paths']} → {s['current_source_paths']} paths; {len(s['delta']['modified'])} modified, {len(s['delta']['added'])} new, {len(s['delta']['removed'])} removed. All {s['client_assets']['paths']} client assets and {s['gametest']['paths']} GameTest source/registry paths unchanged.",
                      f"- Built JAR SHA-256: `{j['current_sha256']}`. Exact entry delta: {len(j['delta']['modified'])} modified, {len(j['delta']['added'])} added, {len(j['delta']['removed'])} removed.",
                      "- Four nested WeaponRuntime classes (three records and HitDamage) are proven LineNumberTable line-value-only changes by parsing both classfiles and comparing every other byte. JSON includes both normalized hashes, byte offsets, methods, start_pc and old/new line values.",
                      "- Runtime provenance covers the exact complete current main-source and JAR class sets for server (7492 sources, 377 classes) and Vision (20 sources, 38 classes).",
                      "- Gate 1 and gate 2: each 760 JUnit, zero failures/errors/skips; all 754 W106 identities plus exactly six specified new identities. Archived XML freshness is checked against execution windows and owner records. Both logs: 869 required/completed GameTests, 20/20 tasks executed, success; both JAR pins match.",
                      "- Vision: archived/current XML byte-equal, 52 JUnit with zero failures/errors/skips; Node log 31 passed, zero failed/cancelled/skipped/todo. Vision lacks a separate XML freshness window record.",
                      f"- Actual pack: {r['actual_pack']['bytes']} bytes, byte-equal to W106 and recorded client cache; SHA-256 `{r['actual_pack']['sha256']}`.", "", "Exact source delta:", ""])
        for kind in ("modified", "added", "removed"):
            for p in s["delta"][kind]:
                lines.append(f"- {kind}: `{p}`")
        lines.extend(["", "Exact JAR entry delta:", ""])
        for kind in ("modified", "added", "removed"):
            for p in j["delta"][kind]:
                lines.append(f"- {kind}: `{p}`")
        lines.extend(["", f"Central W107 archive present: {str(j['central_archive']['present']).lower()}. The owner supplies this copy; the auditor never creates it."])
    lines.extend(["", "Anomalies:", ""])
    lines.extend(["- " + json.dumps(a, sort_keys=True) for a in report["anomalies"]] or ["- None."])
    lines.extend(["", "Limits:", ""] + ["- " + s for s in report["limits"]])
    lines.extend(["", "Rerun: `rtk proxy python3 scripts/qa/audit_use_trace_w107.py`.",
                  "Verify frozen reports: `rtk proxy python3 scripts/qa/audit_use_trace_w107.py --check`.",
                  "No timestamps are generated or copied into report fields. Input artifacts, reviewed source pins, exact deltas and strict classfile proofs define the freeze.", ""])
    return "\n".join(lines).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--vision-root", type=Path, default=Path("/Users/qf/IdeaProjects/copper-golem-vision-client-26.3"))
    parser.add_argument("--check", action="store_true", help="check reports without modifying any file")
    args = parser.parse_args()
    audit = Audit(args.root.resolve(), args.vision_root.resolve())
    report = audit.execute()
    outputs = {args.root / QA / "product-audit.json": encoded(report), args.root / QA / "product-audit.md": markdown(report)}
    mismatch = []
    for path, data in outputs.items():
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                mismatch.append(str(path))
        else:
            path.write_bytes(data)
    print(json.dumps(dict(status=report["status"], anomalies=report["anomalies"], reports=[str(p) for p in outputs], frozen_report_mismatches=mismatch), sort_keys=True))
    return 1 if report["anomalies"] or mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
