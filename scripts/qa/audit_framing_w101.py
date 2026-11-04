#!/usr/bin/env python3
"""Finite W101 source/JAR/optional pack audit; never builds or runs a client.

--finalize seals a candidate only after two fresh completed gates and an actual
server pack. Client cache and native visual/audio acceptance remain independent.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
QA = Path("docs/qa/2026-10-25/w101")
OLD_QA = Path("docs/qa/2026-10-25/w100")
OLD_MANIFEST = Path("art/qa/w100/implementation.json")
OLD_MANIFEST_SHA = "34c035c4756111fd318235581fba11366f7ceae71205ed955869c3e39afb5f0f"
OLD_SEAL_SHA = "4800bf226968cf5e7f874c15333472a31cd9f41c7381bf2c12018c7986166d0e"
MAIN = "src/main/java/kim/biryeong/destiny/weapon/WeaponReloadPresentation.java"
GT = "src/gametest/java/kim/biryeong/destiny/test/RecluseReloadW100GameTests.java"
SUPPORT_TEST = "src/gametest/java/kim/biryeong/destiny/test/HandCannonReloadW64GameTests.java"
INVENTORY_TEST = "src/test/java/kim/biryeong/destiny/sound/FireVariantsW98Test.java"
INHERITED_CHANGES = (MAIN, GT, SUPPORT_TEST, INVENTORY_TEST)
JUNIT = "src/test/java/kim/biryeong/destiny/fx/RecluseFramingW101Test.java"
JUNIT_CLASS = "kim.biryeong.destiny.fx.RecluseFramingW101Test"
GENERATOR = "scripts/generate_reload_framing_w101.py"
ASSET_MANIFEST = "art/weapons/w101/manifest.json"
SELF = "scripts/qa/audit_framing_w101.py"
MIGRATION = QA / "w98-framing-migration.txt"
MIGRATION_SHA = "2000615f5ff5d7fb3da1eccc802f7cc4f22e47bbb2f5535af6e5000770b98d32"
MIGRATION_ANCHOR = (
    b'        assertEquals(sounds().stream().map(s -> "src/main/resources/assets/destiny/sounds/" + s.substring(8) + ".ogg")\n'
    b'                .collect(java.util.stream.Collectors.toSet()), added);\n'
)
ASSET_ROOT = "src/main/resources/"
DESTINY = ASSET_ROOT + "assets/destiny/"
SOURCE_FOLDERS = ("src/main/java", "src/main/resources", "src/test/java",
                  "src/test/resources", "src/gametest/java", "src/gametest/resources")
MAX_FILE_BYTES = 1024 * 1024 * 1024
MAX_ZIP_ENTRIES = 50000
MAX_ZIP_MEMBER_BYTES = 64 * 1024 * 1024


class AuditError(RuntimeError):
    pass


def need(value, reason):
    if not value:
        raise AuditError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def decode_json(data):
    def invalid(value):
        raise AuditError("Non-finite JSON value: " + value)
    return json.loads(data, object_pairs_hook=unique_object, parse_constant=invalid)


def relative(value):
    need(isinstance(value, str) and value, "Expected nonempty relative path")
    path = PurePosixPath(value)
    need(not path.is_absolute() and path.as_posix() == value and
         all(part not in (".", "..") for part in path.parts) and "\\" not in value,
         "Unsafe/noncanonical relative path: " + value)
    return Path(value)


def hash_map(value, label):
    need(isinstance(value, dict) and value, "Missing hash dictionary: " + label)
    need(all(isinstance(h, str) and re.fullmatch(r"[0-9a-f]{64}", h)
             for h in value.values()), "Invalid SHA-256 in " + label)
    return value


def difference(before, after):
    return dict(added=sorted(after.keys() - before.keys()),
                removed=sorted(before.keys() - after.keys()),
                modified=sorted(k for k in before.keys() & after.keys()
                                if before[k] != after[k]))


class Inputs:
    """Record every read and directory listing, then recheck before writing."""
    def __init__(self):
        self.hashes = {}
        self.metadata = {}
        self.inventories = {}

    def path(self, path):
        path = Path(path)
        path = path if path.is_absolute() else ROOT / path
        # macOS /tmp itself is a symlink. Resolve parent aliases, while refusing
        # a substituted leaf; canonical paths also prevent output/input aliases.
        need(not path.is_symlink(), "Symlink input forbidden: " + str(path))
        return path.resolve()

    def data(self, path):
        path = self.path(path)
        need(path.is_file() and path.stat().st_size <= MAX_FILE_BYTES,
             "Missing/oversized input: " + str(path))
        stat = path.stat()
        data = path.read_bytes()
        after = path.stat()
        state = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
        need(state == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and
             self.metadata.get(path, state) == state, "Input metadata changed: " + str(path))
        pin = digest(data)
        need(self.hashes.get(path, pin) == pin, "Input changed during audit: " + str(path))
        self.hashes[path] = pin
        self.metadata[path] = state
        return data

    def sha(self, path):
        return digest(self.data(path))

    def json(self, path):
        return decode_json(self.data(path))

    def files(self, folder):
        path = self.path(folder)
        need(not path.exists() or path.is_dir(), "Not a directory: " + str(path))
        paths = set()
        for file in path.rglob("*"):
            need(not file.is_symlink(), "Symlink in inventory: " + str(file))
            if file.is_file():
                paths.add(file.relative_to(ROOT).as_posix())
        need(self.inventories.get(path, paths) == paths,
             "Directory changed during audit: " + str(path))
        self.inventories[path] = paths
        return paths

    def recheck(self):
        for path in list(self.hashes):
            self.data(path)
        for path in list(self.inventories):
            self.files(path)


def zip_entries(data, canonical_json=False):
    """Canonicalize JSON only for source-to-Polymer comparison, never inherited ZIPs."""
    result = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        need(len(infos) <= MAX_ZIP_ENTRIES, "ZIP entry limit exceeded")
        names = [info.filename for info in infos]
        need(len(names) == len(set(names)), "Duplicate ZIP path")
        need(sum(info.file_size for info in infos) <= MAX_FILE_BYTES,
             "ZIP uncompressed size limit exceeded")
        for info in infos:
            name = info.filename
            relative(name.rstrip("/"))
            need(info.file_size <= MAX_ZIP_MEMBER_BYTES and not info.flag_bits & 1,
                 "Oversized/encrypted ZIP member: " + name)
            need((info.external_attr >> 16) & 0o170000 != 0o120000,
                 "Symlink ZIP member: " + name)
            if info.is_dir():
                continue
            raw = archive.read(info)
            result[name] = canonical_hash(raw) if canonical_json and name.endswith(".json") else digest(raw)
    return result


def canonical_hash(data):
    return digest(json.dumps(decode_json(data), sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode())


def exact_list(value, expected, label):
    need(isinstance(value, list) and len(value) == len(set(value)) and
         set(value) == set(expected), label + " mismatch")


def expected_assets():
    result = {DESTINY + "items/weapon_reload_w101/the_recluse.json"}
    result.update(DESTINY + f"models/weapon_reload_w101/the_recluse_{n:02d}_{part}_{grip}.json"
                  for n in range(21) for part in ("body", "magazine")
                  for grip in ("native", "twohand"))
    need(len(result) == 85, "Internal exact asset inventory error")
    return result


def literal_migrations(inputs, pins):
    for source in INHERITED_CHANGES:
        backup = QA / "before" / source
        need(inputs.sha(backup) == pins[source], "W100 backup drift: " + source)
        before = inputs.data(backup)
        if source == INVENTORY_TEST:
            need(inputs.sha(MIGRATION) == MIGRATION_SHA, "Exact additive W98 snippet drift")
            need(before.count(MIGRATION_ANCHOR) == 1, "W98 assertion anchor must be unique")
            after = before.replace(MIGRATION_ANCHOR, inputs.data(MIGRATION) + MIGRATION_ANCHOR, 1)
        else:
            route = b"weapon_reload_w100/"
            need(before.count(route) == 1, "W100 route must occur exactly once: " + source)
            after = before.replace(route, b"weapon_reload_w101/", 1)
        need(inputs.data(source) == after, "Source exceeds exact permitted byte diff: " + source)


def old_seal(inputs):
    seal = OLD_QA / "SHA256SUMS"
    need(inputs.sha(seal) == OLD_SEAL_SHA, "Sealed W100 QA inventory drift")
    pins = {}
    for line in inputs.data(seal).decode().splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        need(match is not None, "Malformed W100 seal row")
        key = (OLD_QA / relative(match[2])).as_posix()
        need(key not in pins, "Duplicate W100 seal row")
        pins[key] = match[1]
    need(len(pins) == 627, "W100 seal inventory count drift")
    return pins


def validate_graph(inputs, assets):
    """Independent structural check; no authored transform values are hardcoded."""
    for n in range(21):
        for part in ("body", "magazine"):
            parent = f"destiny:weapon_reload_w100/the_recluse_{part}"
            for grip in ("native", "twohand"):
                path = DESTINY + f"models/weapon_reload_w101/the_recluse_{n:02d}_{part}_{grip}.json"
                pose = inputs.json(path)
                need(set(pose) == {"parent", "display"} and pose["parent"] == parent and
                     isinstance(pose["display"], dict), "Pose must reuse only W100 geometry: " + path)
                base_key = "the_recluse" + ("_twohand" if grip == "twohand" else "")
                original = inputs.json(DESTINY + "models/weapon/submachine_gun/" + base_key + ".json")
                need(set(pose["display"]) == set(original["display"]), "Display context inventory drift")
                for context, transform in pose["display"].items():
                    need(isinstance(transform, dict) and set(transform) == set(original["display"][context]),
                         "Display transform shape drift: " + path)
                    for field, vector in transform.items():
                        need(field in ("rotation", "translation", "scale") and isinstance(vector, list) and
                             len(vector) == 3 and all(type(v) in (int, float) and math.isfinite(v) for v in vector),
                             "Non-finite/non-vector display: " + path)
                    if n in (0, 20) or context not in ("firstperson_righthand", "firstperson_lefthand"):
                        need(transform == original["display"][context], "Endpoint/other-context display changed")
    body = inputs.json(DESTINY + "models/weapon_reload_w100/the_recluse_body.json")
    magazine = inputs.json(DESTINY + "models/weapon_reload_w100/the_recluse_magazine.json")
    need(len(body["elements"]) == 193 and len(magazine["elements"]) == 24,
         "Inherited 217-cube geometry count drift")
    original = inputs.json(DESTINY + "items/weapon/the_recluse.json")
    entries = []
    for n in range(21):
        def composite(grip):
            return {"type": "minecraft:composite", "models": [
                {"type": "minecraft:model", "model": f"destiny:weapon_reload_w101/the_recluse_{n:02d}_{part}_{grip}"}
                for part in ("body", "magazine")]}
        entries.append({"threshold": n / 20, "model": {
            "type": "minecraft:condition", "property": "minecraft:custom_model_data", "index": 0,
            "on_true": composite("twohand"), "on_false": composite("native")}})
    expected = dict(original)
    expected["model"] = {"type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": ["firstperson_righthand", "firstperson_lefthand"], "model": {
            "type": "minecraft:range_dispatch", "property": "minecraft:custom_model_data", "index": 1,
            "entries": entries, "fallback": original["model"]}}], "fallback": original["model"]}
    need(inputs.json(DESTINY + "items/weapon_reload_w101/the_recluse.json") == expected,
         "Wrapper must have exact 21 frames, native/twohand routing and original fallback")


def source_snapshot(inputs, contract):
    need(inputs.sha(OLD_MANIFEST) == OLD_MANIFEST_SHA, "Sealed W100 implementation drift")
    old = inputs.json(OLD_MANIFEST)
    pins = hash_map(old["sha256"], "W100 source pins")
    old_assets = hash_map(old["clientAssets"], "W100 assets")
    need(old["stage"] == "W100" and len(pins) == 8609 and len(old_assets) == 7106,
         "Unexpected W100 baseline inventory")
    need(all(pins.get(p) == h for p, h in old_assets.items()), "W100 asset/source pin disagreement")
    for p in pins:
        relative(p)
    current = {p: inputs.sha(p) for p in pins}
    exact_list([p for p in pins if current[p] != pins[p]], INHERITED_CHANGES,
               "Exactly four inherited source changes")
    literal_migrations(inputs, pins)
    manifest = inputs.json(ASSET_MANIFEST)
    assets = hash_map(manifest["sha256"], "W101 asset hashes")
    need(manifest["stage"] == "W101" and manifest["generator"] == GENERATOR and
         type(manifest["assets"]) is int and manifest["assets"] == 85 and
         type(manifest["frames"]) is int and manifest["frames"] == 21,
         "W101 generator manifest stage/count mismatch")
    exact_list(list(assets), expected_assets(), "Exact 85 asset paths")
    need(not assets.keys() & pins.keys(), "W101 asset overlaps inherited source")
    for p, h in assets.items():
        need(inputs.sha(p) == h, "W101 asset drift: " + p)
    need(manifest["generatorSha256"] == inputs.sha(GENERATOR), "Generator manifest binding drift")
    for field in ("baselinePins", "originalPins"):
        for p, h in hash_map(manifest[field], field).items():
            relative(p)
            need(pins.get(p) == h == inputs.sha(p), "Unsealed/drifted generator input: " + p)
    new_sources = [JUNIT]
    for folder in SOURCE_FOLDERS:
        expected = {p for p in pins if p.startswith(folder + "/")}
        expected |= {p for p in [*new_sources, *assets] if p.startswith(folder + "/")}
        need(inputs.files(folder) == expected, "Unexpected added/removed source inventory: " + folder)
    all_assets = {p: inputs.sha(p) for p in inputs.files("src/main/resources/assets")}
    need(all_assets == {**old_assets, **assets}, "Inherited asset change or unexpected addition")
    validate_graph(inputs, assets)
    for p in (JUNIT, GENERATOR, ASSET_MANIFEST, SELF, MIGRATION.as_posix()):
        need(p not in pins, "Expected new source/evidence path already inherited: " + p)
        current[p] = inputs.sha(p)
    current.update(assets)
    # Optional master review bindings may extend the finite snapshot, never its allowed changes.
    reviewed = contract.get("reviewedSourceSha256", {})
    if reviewed:
        for p, h in hash_map(reviewed, "Reviewed source hashes").items():
            relative(p)
            need(inputs.sha(p) == h, "Reviewed source drift: " + p)
            current[p] = h
    if "acceptedOldChanges" in contract:
        exact_list(contract["acceptedOldChanges"], INHERITED_CHANGES, "Accepted inherited changes")
    if "newSourcePaths" in contract:
        exact_list(contract["newSourcePaths"], new_sources, "New Java source paths")
    if "newClientAssets" in contract:
        exact_list(contract["newClientAssets"], assets, "Contract new assets")
    if "previousManifestSha256" in contract:
        need(contract["previousManifestSha256"] == OLD_MANIFEST_SHA, "Contract baseline disagreement")
    external = hash_map(old["externalSha256"], "W100 external pins")
    for p, h in external.items():
        need(Path(p).is_absolute() and inputs.sha(p) == h, "External source drift: " + p)
    return dict(sha256=current, clientAssets=all_assets, externalSha256=external), old, assets


def junit_suites(inputs, folder):
    counts = dict(tests=0, failures=0, errors=0, skipped=0)
    identities = set()
    files = sorted(p for p in inputs.files(folder) if Path(p).name.startswith("TEST-") and p.endswith(".xml"))
    need(files, "Missing archived JUnit XML: " + str(folder))
    for path in files:
        raw = inputs.data(path)
        need(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "XML declarations forbidden")
        suite = ET.fromstring(raw)
        need(suite.tag == "testsuite", "Expected Gradle testsuite XML")
        for key in counts:
            count = int(suite.attrib[key])
            need(count >= 0, "Negative XML count")
            counts[key] += count
        cases = suite.findall("testcase")
        need(len(cases) == int(suite.attrib["tests"]), "XML testcase/count mismatch")
        for case in cases:
            identity = (case.attrib["classname"], case.attrib["name"])
            need(all(identity) and identity not in identities, "Empty/duplicate JUnit identity")
            need(not any(case.find(k) is not None for k in ("failure", "error", "skipped")),
                 "Nonpassing XML testcase")
            identities.add(identity)
    need(counts["tests"] == len(identities), "JUnit identities/count mismatch")
    return counts, identities, {Path(p).name for p in files}


def verify_gates(inputs, contract, old, expected_junit, jar_sha):
    need(type(expected_junit) is int and expected_junit > 715,
         "--finalize requires exact --expected-junit > 715 (or integration expectedJUnit)")
    summary_path = QA / "gate-summary.json"
    summary = inputs.json(summary_path)
    if "gateSummarySha256" in contract:
        need(inputs.sha(summary_path) == contract["gateSummarySha256"], "Gate summary binding drift")
    rows = summary["gates"]
    need(isinstance(rows, list) and len(rows) >= 2, "Two completed gates required")
    numbers = [row["gate"] for row in rows]
    need(all(type(n) is int and n > 0 for n in numbers) and numbers == sorted(set(numbers)),
         "Gate IDs must be positive, unique and ordered")
    need(numbers[-1] == numbers[-2] + 1 and summary["finalPassingGates"] == numbers[-2:] and
         summary["jarSha256"] == jar_sha, "Latest consecutive gates/JAR selection mismatch")
    logs = {int(Path(p).stem.split("-")[1]) for p in inputs.files(QA)
            if re.fullmatch(r"gate-[0-9]+\.log", Path(p).name) and Path(p).parent == QA}
    need(logs == set(numbers), "Gate summary omits/adds archived runs")
    seal = old_seal(inputs)
    old_folder = OLD_QA / f"gate-{old['gates'][-1]}-xml"
    baseline_counts, baseline_ids, _ = junit_suites(inputs, old_folder)
    need(baseline_counts == dict(tests=715, failures=0, errors=0, skipped=0), "W100 JUnit baseline drift")
    for p in inputs.files(old_folder):
        need(seal.get(p) == inputs.sha(p), "W100 archived baseline XML drift: " + p)
    new_ids = None
    previous_end = None
    for row in rows[-2:]:
        n = row["gate"]
        need(type(row["returncode"]) is int and row["returncode"] == 0 and
             row["forcedAllTasks"] is True and row["allXmlFresh"] is True,
             "Gate execution/freshness failed")
        actual, ids, xml_names = junit_suites(inputs, QA / f"gate-{n}-xml")
        need(actual == row["junit"] == dict(tests=expected_junit, failures=0, errors=0, skipped=0),
             "Exact JUnit count mismatch")
        need(all(type(v) is int for v in row["junit"].values()), "Noninteger JUnit summary")
        additions = ids - baseline_ids
        need(baseline_ids <= ids and len(additions) == expected_junit - 715 and
             all(c == JUNIT_CLASS for c, _ in additions), "Inherited/new JUnit identity mismatch")
        need(new_ids is None or new_ids == additions, "New JUnit identities differ between gates")
        new_ids = additions
        if "newJUnitIdentities" in contract:
            raw = contract["newJUnitIdentities"]
            need(isinstance(raw, list) and all(isinstance(v, list) and len(v) == 2 and
                 all(isinstance(s, str) for s in v) for v in raw), "Invalid contract JUnit identities")
            need(len(raw) == len(additions) and {tuple(v) for v in raw} == additions,
                 "Contract JUnit identity disagreement")
        need(row["previousJUnitIdentitiesPreserved"] == 715 and row["newJUnit"] == len(additions),
             "Summary JUnit identity count mismatch")
        need(type(row["requiredPassed"]) is int and type(row["gameTestsTotal"]) is int and
             row["requiredPassed"] == row["gameTestsTotal"] == 829 and row["jarSha256"] == jar_sha,
             "Exact 829 GameTests/JAR binding mismatch")
        exit_data = inputs.json(QA / f"gate-{n}-exit.json")
        start, end = exit_data["startedAt"], exit_data["finishedAt"]
        need(all(type(t) in (int, float) and math.isfinite(t) for t in (start, end)) and
             0 < start <= end and (previous_end is None or start >= previous_end),
             "Invalid/overlapping gate execution times")
        previous_end = end
        need(type(exit_data["gate"]) is int and exit_data["gate"] == n and
             type(exit_data["returncode"]) is int and exit_data["returncode"] == 0 and
             set(exit_data["xmlFreshness"]) == xml_names and
             all(v is True for v in exit_data["xmlFreshness"].values()), "Archived exit/freshness mismatch")
        for name in xml_names:
            mtime = inputs.path(QA / f"gate-{n}-xml" / name).stat().st_mtime
            need(start <= mtime <= end, "XML mtime outside gate interval: " + name)
        need(inputs.data(QA / f"gate-{n}-jar.sha256").decode().strip() == jar_sha, "Gate JAR hash drift")
        log = inputs.data(QA / f"gate-{n}.log").decode()
        passed = re.findall(r"All (\d+) required tests passed", log)
        complete = re.findall(r"(\d+) GAME TESTS COMPLETE", log)
        tasks = re.findall(r"(\d+) actionable tasks: (\d+) executed", log)
        need(passed == complete == ["829"] and "BUILD SUCCESSFUL" in log and "BUILD FAILED" not in log and
             len(tasks) == 1 and int(tasks[0][0]) > 0 and tasks[0][0] == tasks[0][1] and
             not re.search(r"\b(?:UP-TO-DATE|FROM-CACHE)\b", log), "Incomplete/nonforced gate log")
    return dict(gates=numbers[-2:], gateSummarySha256=inputs.sha(summary_path),
                expectedJUnit=expected_junit, newJUnitIdentities=sorted(new_ids),
                previousJUnitIdentitiesPreserved=715, newGameTests=0)


def audit(args):
    inputs = Inputs()
    contract_path = args.integration if args.integration else QA / "integration.json"
    contract = inputs.json(contract_path) if args.integration or inputs.path(contract_path).exists() else {}
    if contract:
        need(contract["stage"] == "W101", "Wrong integration stage")
    expected_junit = args.expected_junit if args.expected_junit is not None else contract.get("expectedJUnit")
    if expected_junit is not None:
        need(type(expected_junit) is int and expected_junit > 715, "Exact expected JUnit must exceed W100's 715")
    if "expectedJUnit" in contract:
        need(type(contract["expectedJUnit"]) is int and contract["expectedJUnit"] == expected_junit,
             "CLI/contract expected JUnit disagreement")
    if "expectedGameTests" in contract:
        need(type(contract["expectedGameTests"]) is int and contract["expectedGameTests"] == 829,
             "W101 GameTest count must remain exactly 829")
    need(args.expected_gametests == 829, "W101 requires exactly 829 GameTests")
    snapshot, old, assets = source_snapshot(inputs, contract)
    prior = QA / "before-product.jar"
    need(inputs.sha(prior) == old["jarSha256"], "W100 product JAR backup drift")
    jar_data = inputs.data(args.jar)
    before_entries, entries = zip_entries(inputs.data(prior)), zip_entries(jar_data)
    additions = {p.removeprefix(ASSET_ROOT): h for p, h in assets.items()}
    delta = difference(before_entries, entries)
    need(delta == dict(added=sorted(additions), removed=[],
                       modified=["kim/biryeong/destiny/weapon/WeaponReloadPresentation.class"]),
         "Product JAR delta exceeds 85 assets plus presentation class: " + str(delta))
    need(all(entries[p] == h for p, h in additions.items()), "JAR assets differ from source bytes")
    jar_sha = digest(jar_data)
    report = dict(stage="W101", baseline="W100", status="passed", finalized=args.finalize,
        candidateOnly=True, acceptance="Finite source/JAR/optional pack candidate; native acceptance belongs to master",
        previousManifestSha256=OLD_MANIFEST_SHA, previousSourcePins=8609, previousClientAssets=7106,
        sourcePins=len(snapshot["sha256"]), clientAssets=len(snapshot["clientAssets"]),
        newAssets=85, acceptedOldChanges=list(INHERITED_CHANGES), expectedGameTests=829,
        jarSha256=jar_sha, previousJarSha256=old["jarSha256"], jarDelta=delta,
        migrationSha256=MIGRATION_SHA, generatorSha256=inputs.sha(GENERATOR),
        assetManifestSha256=inputs.sha(ASSET_MANIFEST), generatorExecutedByAuditor=False,
        cacheVerified=False, clientCacheProvenanceVerified=False,
        nativeRenderingAccepted=False, nativeAudioAccepted=False, pendingNative=True,
        nativeAcceptanceDelegatedToMaster=True, wholeGoalAchieved=False)
    if expected_junit is not None:
        report["expectedJUnit"] = expected_junit
    if contract:
        report["integrationSha256"] = inputs.sha(contract_path)
    need(len(args.client_cache) <= 1, "At most one actual client cache is allowed")
    need(not args.client_cache or args.pack is not None, "--client-cache requires --pack")
    if args.pack is not None:
        prior_pack = OLD_QA / "server-generated/resource_pack.zip"
        need(inputs.sha(prior_pack) == old["serverPackSha256"], "W100 actual server pack drift")
        pack_data = inputs.data(args.pack)
        pack = zip_entries(pack_data)
        pack_delta = difference(zip_entries(inputs.data(prior_pack)), pack)
        need(pack_delta == dict(added=sorted(additions), removed=[], modified=[]),
             "Pack must preserve every W100 entry and add exactly 85: " + str(pack_delta))
        canonical = zip_entries(pack_data, canonical_json=True)
        need(all(canonical[p] == canonical_hash(inputs.data(ASSET_ROOT + p)) for p in additions),
             "Server pack W101 JSON differs from source")
        pack_sha = digest(pack_data)
        report.update(serverPackSha256=pack_sha, previousPackSha256=old["serverPackSha256"],
                      packEntries=len(pack), packEntryDelta=pack_delta)
        if args.client_cache:
            cache = args.client_cache[0]
            # A caller must supply an actual downloaded file. Equality is independent
            # of filesystem identity; a copied ZIP alone proves no download origin.
            paths = [inputs.path(cache), inputs.path(args.pack), inputs.path(prior_pack), inputs.path(args.jar)]
            need(len(set(paths)) == len(paths) and all(not a.samefile(b)
                 for i, a in enumerate(paths) for b in paths[i + 1:]), "Cache/pack/JAR inputs alias")
            need(inputs.sha(cache) == pack_sha, "Actual client cache differs from actual server pack")
            report.update(cacheVerified=True, clientCaches={str(inputs.path(cache)): pack_sha},
                          cacheVerification="Distinct file with equal SHA-256; download provenance unverified")
            if "clientCacheProvenance" in contract:
                binding = contract["clientCacheProvenance"]
                proof_path = relative(binding["path"])
                need(inputs.sha(proof_path) == binding["sha256"], "Cache provenance JSON drift")
                proof = inputs.json(proof_path)
                need(Path(proof["original"]).is_absolute(), "Cache download origin must be absolute")
                origin = inputs.path(proof["original"])
                need(origin not in paths and all(not origin.samefile(p) for p in paths), "Cache origin aliases input")
                need(inputs.path(proof["cache"]) == paths[0] and
                     inputs.sha(origin) == proof["sha256"] == pack_sha, "Cache provenance binding mismatch")
                report.update(clientCacheProvenanceVerified=True,
                              clientCacheProvenanceSha256=binding["sha256"])
    if args.finalize:
        need(args.pack is not None, "Candidate finalization requires the actual server pack")
        report.update(verify_gates(inputs, contract, old, expected_junit, jar_sha))
    inputs.recheck()
    # Complete finite read inventory accompanies the candidate (including archive evidence).
    report["inputSha256"] = {str(p): h for p, h in sorted(inputs.hashes.items())}
    return report, snapshot, inputs


def output_path(path):
    raw = Path(path)
    resolved = raw.resolve()
    need(not raw.is_symlink() and resolved.suffix == ".json", "Output must be a nonsymlink JSON path")
    need(resolved.is_relative_to(ROOT / QA) or not resolved.is_relative_to(ROOT),
         "Report output must be inside W101 QA or outside repository")
    return resolved


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path, default=Path("build/libs/destiny-guardians-0.1.0+26.3.jar"))
    parser.add_argument("--pack", type=Path, help="Actual generated W101 server ZIP")
    parser.add_argument("--client-cache", type=Path, action="append", default=[], help="Optional actual downloaded cache")
    parser.add_argument("--integration", type=Path, help="Optional master integration contract; defaults to W101/integration.json if present")
    parser.add_argument("--expected-gametests", "--expected-game-tests", dest="expected_gametests", type=int, default=829)
    parser.add_argument("--expected-junit", type=int, help="Strict total: 715 inherited plus W101 test cases")
    parser.add_argument("--out", type=Path, help="Optional report JSON; otherwise stdout only")
    parser.add_argument("--finalize", action="store_true", help="Seal candidate after pack and two complete fresh gates; cache optional")
    args = parser.parse_args(argv)
    target = ROOT / "art/qa/w101/implementation.json"
    try:
        out = output_path(args.out) if args.out else None
        need(out != target, "Report and implementation paths must differ")
        report, snapshot, inputs = audit(args)
        for dest in [out] + ([target] if args.finalize else []):
            if dest is None:
                continue
            need(dest.resolve() == dest and not dest.is_symlink(), "Output target has a symlink alias")
            need(dest not in inputs.hashes, "Output would overwrite audit input")
            need(all(not dest.is_relative_to(folder) or folder == ROOT / QA
                     for folder in inputs.inventories), "Output would change audited inventory")
        if args.finalize:
            manifest = {k: v for k, v in report.items() if k != "clientAssets"}
            manifest.update(snapshot)
            manifest["clientAssetCount"] = report["clientAssets"]
            write_json(target, manifest)
        if out:
            write_json(out, report)
        # Hash inventories go to JSON output; keep terminal summary finite and readable.
        print(json.dumps({k: v for k, v in report.items() if k != "inputSha256"}, sort_keys=True))
        return 0
    except (AuditError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ET.ParseError) as error:
        print("W101 audit FAILED: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
