#!/usr/bin/env python3
"""Finite, read-only W100 boundary audit; only --out/--finalize write evidence.

Never invokes Gradle, the generator, a server or a client. See auditor-notes.md
for the master-authored integration/gate contract and evidence limitations.
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
QA = Path("docs/qa/2026-10-25/w100")
OLD_QA = Path("docs/qa/2026-10-25/w99")
OLD_MANIFEST = Path("art/qa/w99/implementation.json")
OLD_MANIFEST_SHA = "d4c7cf0950b3c5312379f24d6cc5309c9a69a9877edfdf9da800b59454d26fa6"
PROTECTED_SHA = "0c3d4beacb8744e76a7678766eb9dd34c3760d201e8d4d5d80ff1b91ef4b2c9c"
MAIN = "src/main/java/kim/biryeong/destiny/weapon/WeaponReloadPresentation.java"
REGISTRATION = "src/gametest/resources/fabric.mod.json"
GT = "src/gametest/java/kim/biryeong/destiny/test/RecluseReloadW100GameTests.java"
JUNIT = "src/test/java/kim/biryeong/destiny/fx/RecluseReloadW100Test.java"
INVENTORY_TEST = "src/test/java/kim/biryeong/destiny/sound/FireVariantsW98Test.java"
MIGRATION = (QA / "w98-inventory-migration.txt").as_posix()
MIGRATION_SHA = "8dfccd583ebb47450fbec1bfea1a0fa56bd9e3039579d9d7295b87e631d1457f"
MIGRATION_ANCHOR = (
    b'        assertEquals(sounds().stream().map(s -> "src/main/resources/assets/destiny/sounds/" + s.substring(8) + ".ogg")\n'
    b'                .collect(java.util.stream.Collectors.toSet()), added);\n'
)
SUPPORT_TEST = "src/gametest/java/kim/biryeong/destiny/test/HandCannonReloadW64GameTests.java"
SUPPORT_MIGRATION = (QA / "w64-support-migration.txt").as_posix()
SUPPORT_MIGRATION_SHA = "29e86dcf16a7327379fde0cc6d08973d8b6fab5d1b22aa790063d4916d5908f0"
SUPPORT_MIGRATION_ANCHOR = b'            if (e.id().equals("ammit_ar2")) continue;\n'
GT_CLASS = "kim.biryeong.destiny.test.RecluseReloadW100GameTests"
JUNIT_CLASS = "kim.biryeong.destiny.fx.RecluseReloadW100Test"
GENERATOR = "scripts/generate_reload_models_w100.py"
ASSET_MANIFEST = "art/weapons/w100/manifest.json"
SUPPLEMENTAL_SOURCE_PINS = {
    # Existing W30 source was not included in W99's 8,499 inventory.
    "art/blockbench/weapons/w30/the_recluse.bbmodel":
        "9d922885fd0055eba9ae83974df9938cceade443ae2a349e8afc7c610331f3a0",
}
ASSET_ROOT = "src/main/resources/"
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


def counts(contract, args):
    result = {}
    for key, override, total in (("expectedGameTests", args.expected_gametests, 829),
                                ("expectedJUnit", args.expected_junit, 715)):
        value = contract.get(key) if override is None else override
        need(type(value) is int and value == total, "Missing/invalid exact W100 " + key)
        need(key not in contract or value == contract[key], "CLI/contract count disagreement: " + key)
        result[key] = value
    need(result["expectedGameTests"] == 829, "W100 requires exactly 822 + 7 GameTests")
    return result


def verify_inventory_migration(inputs, pins, assets, reviewed):
    """Allow only the master's byte-pinned additive oracle insertion."""
    backup = QA / "before" / INVENTORY_TEST
    need(inputs.sha(backup) == pins[INVENTORY_TEST], "W98 inventory test backup differs from W99")
    need(reviewed.get(MIGRATION) == MIGRATION_SHA == inputs.sha(MIGRATION),
         "Missing/drifted exact master inventory-migration snippet pin")
    before, snippet = inputs.data(backup), inputs.data(MIGRATION)
    need(before.count(MIGRATION_ANCHOR) == 1, "W98 inventory assertion anchor must be unique")
    need(inputs.data(INVENTORY_TEST) == before.replace(MIGRATION_ANCHOR, snippet + MIGRATION_ANCHOR, 1),
         "W98 inventory test must equal W99 backup plus exact additive snippet")
    need(reviewed.get(INVENTORY_TEST) == inputs.sha(INVENTORY_TEST),
         "Missing/drifted reviewed W98 inventory test hash")
    # These are the exact names enumerated by the byte-pinned Java snippet,
    # checked against the generator manifest rather than treated as its oracle.
    root = ASSET_ROOT + "assets/destiny/"
    exempt = {root + "items/weapon_reload_w100/the_recluse.json"}
    for part in ("body", "magazine"):
        exempt.add(root + f"models/weapon_reload_w100/the_recluse_{part}.json")
        for frame in range(21):
            for grip in ("native", "twohand"):
                exempt.add(root + f"models/weapon_reload_w100/the_recluse_{frame:02d}_{part}_{grip}.json")
    need(len(exempt) == 87 and exempt == set(assets),
         "Exact inventory-migration exemptions differ from manifest's 87 assets")


def verify_support_migration(inputs, pins, reviewed):
    """Preserve every W64 guard, adding only the pinned positive Recluse case."""
    backup = QA / "before" / SUPPORT_TEST
    need(inputs.sha(backup) == pins[SUPPORT_TEST], "W64 support test backup differs from W99")
    need(reviewed.get(SUPPORT_MIGRATION) == SUPPORT_MIGRATION_SHA == inputs.sha(SUPPORT_MIGRATION),
         "Missing/drifted exact master W64 support-migration snippet pin")
    before, snippet = inputs.data(backup), inputs.data(SUPPORT_MIGRATION)
    need(before.count(SUPPORT_MIGRATION_ANCHOR) == 1, "W64 Ammit support anchor must be unique")
    need(inputs.data(SUPPORT_TEST) == before.replace(
        SUPPORT_MIGRATION_ANCHOR, SUPPORT_MIGRATION_ANCHOR + snippet, 1),
        "W64 support test must equal W99 backup plus exact positive Recluse snippet")
    need(reviewed.get(SUPPORT_TEST) == inputs.sha(SUPPORT_TEST),
         "Missing/drifted reviewed W64 support test hash")


def source_snapshot(inputs, contract):
    need(inputs.sha(OLD_MANIFEST) == OLD_MANIFEST_SHA == contract["previousManifestSha256"],
         "Sealed W99 manifest drift")
    old = inputs.json(OLD_MANIFEST)
    pins = hash_map(old["sha256"], "W99 pins")
    old_assets = hash_map(old["clientAssets"], "W99 assets")
    need(len(pins) == 8499 and len(old_assets) == 7019, "Unexpected W99 inventory counts")
    inherited_changes = [MAIN, REGISTRATION, INVENTORY_TEST, SUPPORT_TEST]
    exact_list(contract["acceptedOldChanges"], inherited_changes, "Accepted inherited changes")
    exact_list(contract["newSourcePaths"], [GT, JUNIT], "New source paths")
    current = {p: inputs.sha(relative(p)) for p in pins}
    exact_list([p for p in pins if pins[p] != current[p]], inherited_changes,
               "Actual inherited modifications")

    # Compare the entire backup bytes after precisely these three replacements.
    backup = QA / "before" / MAIN
    need(inputs.sha(backup) == pins[MAIN], "Main backup differs from W99")
    expected = inputs.data(backup).decode()
    replacements = (
        ("Ammit AR2 W69). Cosmetic", "Ammit AR2 W69, Recluse W100). Cosmetic"),
        ('|| entry.id().equals("ammit_ar2"));',
         '|| entry.id().equals("ammit_ar2") || entry.id().equals("the_recluse"));'),
        ('            case "ammit_ar2" -> "weapon_reload_w69/";\n',
         '            case "ammit_ar2" -> "weapon_reload_w69/";\n'
         '            case "the_recluse" -> "weapon_reload_w100/";\n'))
    for before, after in replacements:
        need(expected.count(before) == 1, "Backup anchor mismatch")
        expected = expected.replace(before, after)
    need(inputs.data(MAIN) == expected.encode(), "Main Java exceeds exact support/namespace/Javadoc diff")
    backup = QA / "before" / REGISTRATION
    need(inputs.sha(backup) == pins[REGISTRATION], "Registration backup differs from W99")
    registration = inputs.json(backup)
    registration["entrypoints"]["fabric-gametest"].append(GT_CLASS)
    need(inputs.json(REGISTRATION) == registration, "Registration must append exactly RecluseReloadW100GameTests")

    manifest = inputs.json(ASSET_MANIFEST)
    assets = hash_map(manifest["assetSha256"], "Generator assetSha256")
    need(manifest["stage"] == "W100" and manifest["generator"] == GENERATOR and
         type(manifest["assets"]) is int and manifest["assets"] == len(assets) == 87,
         "Generator manifest stage/count mismatch")
    for p, h in assets.items():
        relative(p)
        need(any(p.startswith(ASSET_ROOT + "assets/destiny/" + kind + "/weapon_reload_w100/")
                 for kind in ("models", "items")) and p.endswith(".json"),
             "Manifest asset outside exact W100 namespace: " + p)
        need(p not in pins and p not in old_assets and inputs.sha(p) == h,
             "New asset drift or inherited overlap: " + p)
    exact_list(contract["newClientAssets"], assets, "Contract/manifest new assets")
    for folder in SOURCE_FOLDERS:
        expected_paths = {p for p in pins if p.startswith(folder + "/")}
        expected_paths |= {p for p in [GT, JUNIT, *assets] if p.startswith(folder + "/")}
        need(inputs.files(folder) == expected_paths, "Source inventory changed: " + folder)
    all_assets = {p: inputs.sha(p) for p in inputs.files("src/main/resources/assets")}
    need(all_assets == {**old_assets, **assets}, "Client assets exceed exact additions")

    reviewed = hash_map(contract["reviewedSourceSha256"], "Reviewed source hashes")
    need({MAIN, REGISTRATION, INVENTORY_TEST, MIGRATION, SUPPORT_TEST, SUPPORT_MIGRATION,
          GT, JUNIT, GENERATOR, ASSET_MANIFEST} <= reviewed.keys(),
         "Missing required reviewed source/generator/manifest hashes")
    verify_inventory_migration(inputs, pins, assets, reviewed)
    verify_support_migration(inputs, pins, reviewed)
    for p, h in reviewed.items():
        relative(p)
        need(inputs.sha(p) == h, "Reviewed source drift: " + p)
        current[p] = h
    for key in ("sha256", "sourceSha256", "referenceSha256"):
        for p, h in hash_map(manifest[key], "Generator " + key).items():
            relative(p)
            need(inputs.sha(p) == h, "Generator manifest input/output drift: " + p)
            if key == "sourceSha256":
                need(pins.get(p, SUPPLEMENTAL_SOURCE_PINS.get(p)) == h,
                     "Generator source lacks inherited/supplemental pin: " + p)
            current[p] = h
    current.update(assets)
    current.update({p: inputs.sha(p) for p in [GT, JUNIT, GENERATOR, ASSET_MANIFEST]})
    need(inputs.sha("docs/qa/2026-10-25/w98/baseline.json") == PROTECTED_SHA,
         "Protected baseline drift")
    protected = inputs.json("docs/qa/2026-10-25/w98/baseline.json")
    for p, h in hash_map(protected["protected"], "Protected Vision inputs").items():
        need(Path(p).is_absolute() and inputs.sha(p) == h, "Protected Vision drift: " + p)
    for row in protected["normalQAPlayers"]:
        need(inputs.sha(relative(row["path"])) == row["sha256"], "Ordinary QA player drift")
    for p, h in hash_map(old["externalSha256"], "External pins").items():
        need(Path(p).is_absolute() and inputs.sha(p) == h, "External source drift: " + p)
    return dict(sha256=current, clientAssets=all_assets, externalSha256=old["externalSha256"]), old, assets


def junit_suites(inputs, folder):
    counts = dict(tests=0, failures=0, errors=0, skipped=0)
    identities = set()
    files = sorted(p for p in inputs.files(folder) if Path(p).name.startswith("TEST-") and p.endswith(".xml"))
    need(files, "Missing archived JUnit XML: " + str(folder))
    for path in files:
        raw = inputs.data(path)
        need(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "XML entity declarations forbidden")
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
            need(identity not in identities, "Duplicate JUnit identity")
            need(not any(case.find(k) is not None for k in ("failure", "error", "skipped")),
                 "Nonpassing XML testcase")
            identities.add(identity)
    need(counts["tests"] == len(identities), "JUnit identities/count mismatch")
    return counts, identities, {Path(p).name for p in files}


def verify_gates(inputs, contract, expected, jar_sha):
    summary = inputs.json(QA / "gate-summary.json")
    need(inputs.sha(QA / "gate-summary.json") == contract["gateSummarySha256"], "Gate summary drift")
    rows = summary["gates"]
    need(isinstance(rows, list) and len(rows) >= 2, "Two gates required")
    numbers = [row["gate"] for row in rows]
    need(all(type(n) is int and n > 0 for n in numbers) and numbers == sorted(set(numbers)),
         "Gate IDs must be unique and ordered")
    last = rows[-2:]
    need(numbers[-1] == numbers[-2] + 1 and summary["finalPassingGates"] == numbers[-2:] and
         summary["jarSha256"] == jar_sha, "Latest two consecutive gate selection/JAR mismatch")
    # A later failed/unselected gate cannot be hidden by an older passing summary.
    logs = {int(Path(p).stem.split("-")[1]) for p in inputs.files(QA)
            if re.fullmatch(r"gate-[0-9]+\.log", Path(p).name) and Path(p).parent == QA}
    need(logs == set(numbers), "Summary omits/adds archived gates")
    old_counts, old_ids, _ = junit_suites(inputs, OLD_QA / "gate-2-xml")
    need(old_counts == dict(tests=704, failures=0, errors=0, skipped=0), "Unexpected W99 JUnit baseline")
    new_ids_raw = contract["newJUnitIdentities"]
    need(isinstance(new_ids_raw, list) and all(isinstance(v, list) and len(v) == 2 and
         all(isinstance(s, str) and s for s in v) for v in new_ids_raw),
         "newJUnitIdentities must be [[classname, XML testcase name], ...]")
    new_ids = {tuple(v) for v in new_ids_raw}
    need(len(new_ids) == len(new_ids_raw) == expected["expectedJUnit"] - 704 and
         all(c == JUNIT_CLASS for c, _ in new_ids) and not new_ids & old_ids,
         "New JUnit identities/class/count mismatch")
    gt_ids = contract["newGameTestIdentities"]
    need(isinstance(gt_ids, list) and len(gt_ids) == len(set(gt_ids)) == 7 and
         all(isinstance(v, str) for v in gt_ids), "Seven new GameTest method names required")
    gt_source = inputs.data(GT).decode()
    declared = re.findall(r"@GameTest\s*\([^;]*?\)\s*public\s+(?:static\s+)?void\s+(\w+)\s*\(", gt_source)
    exact_list(declared, gt_ids, "New GameTest source identities")
    # Identity declarations are source/summary attestations; GameTest logs expose totals.
    previous_end = None
    for row in last:
        n = row["gate"]
        need(type(row["returncode"]) is int and row["returncode"] == 0 and
             row["forcedAllTasks"] is True and row["allXmlFresh"] is True,
             "Gate execution/freshness failed")
        actual_counts, ids, xml_names = junit_suites(inputs, QA / f"gate-{n}-xml")
        passing = dict(tests=expected["expectedJUnit"], failures=0, errors=0, skipped=0)
        need(actual_counts == row["junit"] == passing and ids == old_ids | new_ids,
             "Exact JUnit counts/identities mismatch")
        need(all(type(v) is int for v in row["junit"].values()), "Noninteger JUnit summary count")
        need(row["previousJUnitIdentitiesPreserved"] == 704 and row["newJUnit"] == len(new_ids),
             "JUnit summary identity counts mismatch")
        need(row["requiredPassed"] == row["gameTestsTotal"] == expected["expectedGameTests"] and
             row["jarSha256"] == jar_sha, "GameTest count/JAR mismatch")
        exit_data = inputs.json(QA / f"gate-{n}-exit.json")
        start, end = exit_data["startedAt"], exit_data["finishedAt"]
        need(all(type(t) in (int, float) and math.isfinite(t) for t in (start, end)) and
             0 < start <= end and (previous_end is None or start >= previous_end),
             "Invalid/overlapping gate execution times")
        previous_end = end
        need(exit_data["gate"] == n and type(exit_data["returncode"]) is int and
             exit_data["returncode"] == 0 and set(exit_data["xmlFreshness"]) == xml_names and
             all(v is True for v in exit_data["xmlFreshness"].values()),
             "Archived gate exit/fresh XML inventory mismatch")
        for name in xml_names:
            modified = inputs.path(QA / f"gate-{n}-xml" / name).stat().st_mtime
            need(start <= modified <= end, "Archived XML mtime outside its gate interval: " + name)
        need(inputs.data(QA / f"gate-{n}-jar.sha256").decode().strip() == jar_sha,
             "Archived gate JAR hash mismatch")
        text = inputs.data(QA / f"gate-{n}.log").decode()
        passed = re.findall(r"All (\d+) required tests passed", text)
        complete = re.findall(r"(\d+) GAME TESTS COMPLETE", text)
        tasks = re.findall(r"(\d+) actionable tasks: (\d+) executed", text)
        need(passed == complete == [str(expected["expectedGameTests"])] and
             "BUILD SUCCESSFUL" in text and "BUILD FAILED" not in text and
             len(tasks) == 1 and int(tasks[0][0]) > 0 and tasks[0][0] == tasks[0][1] and
             not re.search(r"\b(?:UP-TO-DATE|FROM-CACHE)\b", text),
             "Archived log lacks exact passing/forced task evidence")
    return dict(gates=numbers[-2:], gateSummarySha256=inputs.sha(QA / "gate-summary.json"),
                newGameTestIdentities=gt_ids, newJUnitIdentities=new_ids_raw)


def verify_generator_attestation(inputs, contract):
    """Read the master's --verify evidence; deliberately do not execute Python."""
    proof = contract["generatorVerification"]
    allowed_commands = (["python3", GENERATOR, "--verify"],
                        ["rtk", "proxy", "python3", GENERATOR, "--verify"])
    need(proof["command"] in allowed_commands and
         type(proof["returncode"]) is int and proof["returncode"] == 0,
         "Missing successful master generator --verify attestation")
    need(proof["generatorSha256"] == inputs.sha(GENERATOR) and
         proof["manifestSha256"] == inputs.sha(ASSET_MANIFEST), "Generator verification binding drift")
    log = relative(proof["log"])
    need(log.is_relative_to(QA) and inputs.sha(log) == proof["logSha256"],
         "Generator verification log drift/outside W100")
    need(re.search(rb"(?m)^Verified \d+ W100 files\s*$", inputs.data(log)) is not None,
         "Missing generator verification success line")
    return proof


def audit(args):
    inputs = Inputs()
    contract = inputs.json(QA / "integration.json")
    need(contract["stage"] == "W100", "Wrong integration stage")
    expected = counts(contract, args)
    snapshot, old, assets = source_snapshot(inputs, contract)
    jar = Path("build/libs/destiny-guardians-0.1.0+26.3.jar")
    prior = QA / "before-product.jar"
    need(inputs.sha(prior) == old["jarSha256"] == contract["previousJarSha256"], "Previous product JAR drift")
    prior_entries = zip_entries(inputs.data(prior))
    jar_entries = zip_entries(inputs.data(jar))
    new_jar_entries = {p.removeprefix(ASSET_ROOT): h for p, h in assets.items()}
    jar_delta = difference(prior_entries, jar_entries)
    need(jar_delta == dict(added=sorted(new_jar_entries), removed=[],
                          modified=["kim/biryeong/destiny/weapon/WeaponReloadPresentation.class"]),
         "Unexpected product JAR delta: " + str(jar_delta))
    need(all(jar_entries[p] == h for p, h in new_jar_entries.items()), "JAR new asset bytes differ from manifest")
    jar_sha = inputs.sha(jar)
    report = dict(stage="W100", status="passed", finalized=args.finalize,
                  previousSourcePins=8499, previousClientAssets=7019,
                  sourcePins=len(snapshot["sha256"]), clientAssets=len(snapshot["clientAssets"]),
                  newAssets=len(assets), jarSha256=jar_sha, jarDelta=jar_delta,
                  integrationSha256=inputs.sha(QA / "integration.json"), **expected,
                  oracleMigration=dict(source=INVENTORY_TEST, snippet=MIGRATION,
                                       snippetSha256=MIGRATION_SHA, exactAssetExemptions=87),
                  supportOracleMigration=dict(source=SUPPORT_TEST, snippet=SUPPORT_MIGRATION,
                                              snippetSha256=SUPPORT_MIGRATION_SHA),
                  generatorExecutedByAuditor=False, nativeRenderingAccepted=False,
                  nativeAudioAccepted=False, wholeGoalAchieved=False)
    need(len(args.client_cache) <= 1, "Exactly one cache at most; multiple caches forbidden")
    need(not args.client_cache or args.pack is not None, "--client-cache requires --pack")
    if args.pack is not None:
        prior_pack = OLD_QA / "server-generated/resource_pack.zip"
        need(inputs.sha(prior_pack) == old["serverPackSha256"], "W99 native reference pack drift")
        before_pack = zip_entries(inputs.data(prior_pack))
        pack_data = inputs.data(args.pack)
        pack = zip_entries(pack_data)
        pack_delta = difference(before_pack, pack)
        need(pack_delta == dict(added=sorted(new_jar_entries), removed=[], modified=[]),
             "Server pack must preserve all W99 entries and add only exact W100 assets: " + str(pack_delta))
        canonical_pack = zip_entries(pack_data, canonical_json=True)
        for source in assets:
            key = source.removeprefix(ASSET_ROOT)
            need(canonical_pack[key] == canonical_hash(inputs.data(source)),
                 "Polymer new asset JSON differs semantically: " + key)
        pack_sha = inputs.sha(args.pack)
        report.update(serverPackSha256=pack_sha, packEntries=len(pack), packEntryDelta=pack_delta,
                      previousPackSha256=inputs.sha(prior_pack))
        if args.client_cache:
            cache = args.client_cache[0]
            need(inputs.sha(cache) == pack_sha, "Single actual client cache SHA differs from server pack")
            report["clientCaches"] = {str(inputs.path(cache)): pack_sha}
            report["clientCacheProvenanceVerified"] = False
            # Optional explicit provenance proves an independent download origin;
            # hash equality alone is deliberately reported as equality only.
            if "clientCacheProvenance" in contract:
                binding = contract["clientCacheProvenance"]
                provenance = relative(binding["path"])
                need(inputs.sha(provenance) == binding["sha256"], "Cache provenance JSON drift")
                proof = inputs.json(provenance)
                original = Path(proof["original"])
                need(original.is_absolute(), "Cache origin must be absolute")
                cache_path, pack_path = inputs.path(cache), inputs.path(args.pack)
                original = inputs.path(original)
                paths = [original, cache_path, pack_path]
                need(len(set(paths)) == 3 and all(not a.samefile(b)
                     for i, a in enumerate(paths) for b in paths[i + 1:]),
                     "Pack, cache evidence and download origin must be distinct files")
                need(inputs.path(proof["cache"]) == cache_path and proof["sha256"] == pack_sha ==
                     inputs.sha(original), "Cache provenance path/SHA binding mismatch")
                report.update(clientCacheProvenanceVerified=True, clientCacheProvenanceSha256=binding["sha256"])
    if args.finalize:
        need(args.pack is not None and len(args.client_cache) == 1, "Finalization requires pack and exactly one cache")
        report.update(verify_gates(inputs, contract, expected, jar_sha))
        report["generatorVerification"] = verify_generator_attestation(inputs, contract)
        if "nativeSummarySha256" in contract:
            need(inputs.sha(QA / "native-summary.json") == contract["nativeSummarySha256"], "Master native summary drift")
            report["masterNativeSummarySha256"] = contract["nativeSummarySha256"]
            report["nativeAcceptanceDelegatedToMaster"] = True
    inputs.recheck()
    return report, snapshot, inputs


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, help="Actual W100 server-generated ZIP")
    parser.add_argument("--client-cache", type=Path, action="append", default=[], help="One actual downloaded cache, requires --pack")
    parser.add_argument("--expected-gametests", "--expected-game-tests", dest="expected_gametests", type=int)
    parser.add_argument("--expected-junit", type=int)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args(argv)
    target = ROOT / "art/qa/w100/implementation.json"
    # Allow external reports (including macOS /tmp), but no other repo subtree.
    out = args.out.resolve()
    qa_root = ROOT / QA
    try:
        need(not args.out.is_symlink() and out.suffix == ".json" and
             (out.is_relative_to(qa_root) or not out.is_relative_to(ROOT)),
             "--out must be a nonsymlink JSON path under W100 QA or outside the repo")
        need(out != target, "Report and implementation paths must differ")
        report, snapshot, inputs = audit(args)
        need(out not in inputs.hashes, "--out would overwrite an audit input")
        # Do not inject a report into an inventoried directory such as gate XML.
        need(all(not out.is_relative_to(folder) or folder == qa_root for folder in inputs.inventories),
             "--out would change an audited inventory")
        if args.finalize:
            need(target.resolve() == target, "Implementation target must not be a symlink")
            # Report clientAssets is a count; implementation clientAssets must
            # retain the complete inherited-plus-new path/hash dictionary.
            manifest = dict(stage="W100", baseline="W99", acceptance="Finite source/JAR/pack/cache audit; native acceptance belongs to master")
            manifest.update({k: v for k, v in report.items()
                             if k not in ("stage", "status", "finalized", "clientAssets")})
            manifest.update(snapshot)
            manifest["clientAssetCount"] = report["clientAssets"]
            write_json(target, manifest)
        write_json(out, report)
        print(json.dumps(report, sort_keys=True))
        return 0
    except (AuditError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ET.ParseError) as error:
        # Never write success, partial manifests or substitute evidence after failure.
        print("W100 audit FAILED: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
