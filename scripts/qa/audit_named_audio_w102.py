#!/usr/bin/env python3
"""Finite W102 audit. Never builds, executes generators, launches games or plays audio.

Default is source-only. --jar audits an existing product; --pack requires --jar.
--finalize requires both artifacts and two archived fresh full gates. Only master
may authorize invoking --finalize; it is never implied by a passing source audit.
All normal output is stdout; redirect it to retain the bound-input JSON report.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
QA = "docs/qa/2026-10-25/w102"
OLD = "art/qa/w101/implementation.json"
OLD_SHA = "ef0f613ba36552caeffe3135cc63ef6eb8e3eed5755860df06f279947ecd1947"
OLD_SEAL_SHA = "4f9d2ccfc6c7d1ee40042991ec302a7f7a2a079bb2fa0ed4d63a463df0427f1d"
RES = "src/main/resources/"
SOUNDS = RES + "assets/destiny/sounds.json"
REGISTRY = "src/gametest/resources/fabric.mod.json"
BASE = "src/main/java/kim/biryeong/destiny/sound/"
TEST = "src/test/java/kim/biryeong/destiny/sound/"
GT = "src/gametest/java/kim/biryeong/destiny/test/"
ART = "art/weapons/w102/audio/"
SELF = "scripts/qa/audit_named_audio_w102.py"
PROFILE = RES + "destiny/sounds/w102-reload.json"
SOURCE_ROOTS = ("src/main/java", "src/main/resources", "src/test/java", "src/test/resources", "src/gametest/java", "src/gametest/resources")
FAMILIES = {"blast_furnace": "pulse_rifle", "chattering_bone": "pulse_rifle",
            "aishas_embrace": "scout_rifle", "long_arm": "scout_rifle",
            "whispering_slab": "bow", "retrofit_escapade": "machine_gun"}
FOLDERS = dict(zip(FAMILIES, ("1_lzX2VeWtM9APWox0nRDqCbiHoEx65rE", "1ZJiFDuXrgh8QBqaSfSNpEOyTCMBmeiSr",
    "1cxZNF8D46mAb-iBWbJwxmqYzOu4NGl2g", "1_1pwacAXcVs6wJm7U9OuscnGbrGg9K7p",
    "1EnZCnW__Yu5QV3FxG0Ns_fUGCUR502Nk", "1bAwsxY_CNiiiFKC8zzyZlt7UyAav4erF")))
TIMED = {("aishas_embrace", 46), ("blast_furnace", 24), ("blast_furnace", 43),
         ("chattering_bone", 24), ("chattering_bone", 34), ("retrofit_escapade", 90)}
RELOAD_IDS = {i for i, _ in TIMED}
# Reviewed literal Java diffs, not an arbitrary prefix allowlist.
MIGRATIONS = {
 TEST + "SoundAssetsW33Test.java": "0bf589e7e90b25159dedcce6767c9ab22b6b2cb4ac3ca512e12d41b957a51cbe",
 BASE + "ReloadAudioProfile.java": "788d5a6d62a5e3ce4616eaed3bba80ef654941e4572171f92c9c7792ccf96d6e",
 TEST + "FireVariantsW98Test.java": "fbdae84aca0b0f6ec7537683b3bc056a4afb45a223ce8af8a5f2beb397ffd51a",
 TEST + "SwordAudioW56Test.java": "5963323e9cc9b974dfa6bc00e552122cf53dbbe916e384cfd0747bca2e0b0be5",
 GT + "ReloadAudioW63GameTests.java": "ea69087c058d303c4e53e289d47413144d9ad90460a7044e687f25cbaeca2b6b",
}
FROZEN = {
 QA + "/w33-admission-migration.patch": "0cc1685c23ee3f773c4f65567b1727f6fba7606414f6f8feeffa856b24163f50",
 QA + "/first-failure.json": "f02ce338cc502cf1a41364e9f2e683c932a9c70f65cd69bff9f24d9deb9d9bad",
 TEST + "NamedAudioW102Test.java": "9b041ea83d936b3f7cbabeec3237ae84d61e75d3673eec16c80312e48c1a1fe4",
 GT + "NamedAudioW102GameTests.java": "7c49ae59ec3416d4af686c93245b5611eae58d480dc048cf06dd29b514fd366d",
 BASE + "NamedReloadAudioW102.java": "6f1998527145d54f07ed043790f55708cbe6ac828510a856469dc0673d931014",
 ART + "implementation.json": "031cd8c9c5206b2e3a7cb1fd73435a26655547787e477c1e01ef89dd359c24bb",
 ART + "source-pins.json": "6f7387393467c23171c19236b3fce65915e430b1758fc1e0d73a69f85649471f",
 ART + "folder-discovery.json": "c784105fd9d39a03ad8e599642963647de2e018333917cb4664e89211c010fef",
 ART + "event-definitions.json": "a9d70a0f9f9c1793ea18444d1988c85b6f75dbb7e1083abfdccf3ec53516fee9",
 "scripts/audio/build_named_sounds_w102.py": "afe54d8ff6ad8c1b197ae4c91f6fbe923091dbd61710f7d11cfd67e718e1de47",
 QA + "/finite-oracle-migrations.patch": "48d28b59d3ae9c1c9a4e3e1d80f4c06a677f04433d4f514b562318d456685f06",
}

class AuditError(RuntimeError):
    pass

def need(value, reason):
    if not value:
        raise AuditError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def safe(name):
    need(isinstance(name, str) and bool(name), "Empty path")
    p = PurePosixPath(name)
    need(not p.is_absolute() and p.as_posix() == name and "\\" not in name and
         all(v not in ("..", ".") for v in p.parts), "Unsafe path: " + name)
    return name

def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "Duplicate JSON key " + key)
        result[key] = value
    return result

def decode(raw):
    def invalid(v):
        raise AuditError("Nonfinite JSON " + v)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)

class Inputs:
    def __init__(self):
        self.hashes = {}
        self.lists = {}
    def data(self, name):
        p = Path(name)
        p = p if p.is_absolute() else ROOT / safe(str(name))
        need(not p.is_symlink(), "Symlink leaf " + str(p))
        p = p.resolve()
        need(p.is_file() and p.stat().st_size <= 1024**3, "Missing/oversized input " + str(p))
        a = p.stat()
        raw = p.read_bytes()
        b = p.stat()
        need((a.st_ino, a.st_size, a.st_mtime_ns) == (b.st_ino, b.st_size, b.st_mtime_ns), "Unstable input " + str(p))
        h = sha(raw)
        need(self.hashes.get(str(p), h) == h, "Input changed " + str(p))
        self.hashes[str(p)] = h
        return raw
    def hash(self, p):
        return sha(self.data(p))
    def json(self, p):
        return decode(self.data(p))
    def files(self, folder):
        p = ROOT / safe(folder)
        paths = set()
        if p.exists():
            for f in p.rglob("*"):
                need(not f.is_symlink(), "Symlink inventory " + str(f))
                if f.is_file():
                    paths.add(f.relative_to(ROOT).as_posix())
        need(self.lists.get(folder, paths) == paths, "Inventory changed " + folder)
        self.lists[folder] = paths
        return paths
    def recheck(self):
        for p in list(self.hashes):
            self.data(p)
        for p in list(self.lists):
            self.files(p)

def delta(a, b):
    return {"added": sorted(b.keys() - a.keys()), "removed": sorted(a.keys() - b.keys()),
            "modified": sorted(k for k in a.keys() & b.keys() if a[k] != b[k])}

def archive(raw):
    result = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        need(len(infos) <= 50000 and len({i.filename for i in infos}) == len(infos), "ZIP count/duplicate")
        need(sum(i.file_size for i in infos) <= 1024**3, "ZIP total size")
        for i in infos:
            safe(i.filename.rstrip("/"))
            need(i.file_size <= 64*1024**2 and not i.flag_bits & 1 and
                 (i.external_attr >> 16) & 0o170000 != 0o120000, "Unsafe ZIP member " + i.filename)
            if not i.is_dir():
                result[i.filename] = z.read(i)
    return result

def hashes(entries):
    return {k: sha(v) for k, v in entries.items()}

def definitions():
    specs = [("weapon."+i+".fire", i, "fire", "fire") for i in FAMILIES]
    specs += [("weapon."+i+".reload", i, "reload", "reload") for i in sorted(RELOAD_IDS)]
    specs += [(f"weapon.reload_w102.{i}.{t}", i, "reload", f"reload_{t}") for i,t in sorted(TIMED)]
    return {event: {"subtitle": f"subtitles.destiny.weapon.{FAMILIES[i]}.{action}", "sounds": [{
            "name": f"destiny:w102/{i}/{file}", "stream": False, "attenuation_distance": 32}]}
            for event,i,action,file in specs}

def expected_assets():
    return {RES+"assets/destiny/sounds/"+v["sounds"][0]["name"][8:]+".ogg" for v in definitions().values()}

def ogg_samples(raw):
    offset = 0
    granule = -1
    first = True
    eos = False
    while offset < len(raw):
        need(offset+27 <= len(raw) and raw[offset:offset+5] == b"OggS\0", "Invalid Ogg page")
        n = raw[offset+26]
        body = offset+27+n
        need(body <= len(raw), "Truncated Ogg segments")
        end = body+sum(raw[offset+27:body])
        need(end <= len(raw), "Truncated Ogg body")
        if first:
            need(raw[body:body+7] == b"\1vorbis" and raw[body+11] == 1 and
                 struct.unpack_from("<I", raw, body+12)[0] == 32000, "Expected mono 32k Vorbis")
            first = False
        g = struct.unpack_from("<q", raw, offset+6)[0]
        if g >= 0:
            granule = g
        eos = bool(raw[offset+5] & 4)
        offset = end
    need(not first and eos and granule > 0, "Missing Vorbis EOS")
    return granule

def audio_sources(inp, assets):
    pins = inp.json(ART+"source-pins.json")
    need(len(pins) == 10, "Ten named action pins required")
    seen = set()
    discoveries = inp.json(ART+"folder-discovery.json")
    need(len(discoveries) == 6 and {d["id"] for d in discoveries} == set(FAMILIES), "Folder inventory")
    by_id = {d["id"]: d for d in discoveries}
    for d in discoveries:
        need(d["folderId"] == FOLDERS[d["id"]] and d["family"] == FAMILIES[d["id"]], "Folder identity")
        need(inp.hash(d["privateHtml"]) == d["sha256"], "Cached folder HTML drift")
        for e in d["parentEvidence"]:
            need(inp.hash(e["path"]) == e["sha256"], "Cached parent listing drift")
            parent = inp.json(e["path"])
            def contains(value, row):
                if isinstance(value, dict):
                    return value == row or any(contains(v, row) for v in value.values())
                return isinstance(value, list) and any(contains(v, row) for v in value)
            need(contains(parent, e["row"]) and e["row"]["id"] == d["folderId"] and e["row"]["folder"] is True,
                 "Parent row does not prove folder")
    for p in pins:
        i, action = p["id"], p["action"]
        need(i in FAMILIES and action in ({"fire", "reload"} if i in RELOAD_IDS else {"fire"}), "Unexpected named action")
        need((i, action) not in seen, "Duplicate source action")
        seen.add((i, action))
        need(p["folderId"] == FOLDERS[i] and p["family"] == FAMILIES[i] and
             p["originalName"] == ("Fire_1.mp3" if action == "fire" else "Reload_1.mp3"), "Action identity mismatch")
        rows = [r for r in by_id[i]["rows"] if r["id"] == p["driveId"]]
        need(len(rows) == 1 and p["originalName"] in rows[0]["text"], "Named action absent from listing")
        raw = inp.data(p["privatePath"])
        need(len(raw) == p["bytes"] and sha(raw) == p["sourceSha256"] == p["actualPayloadSha256"] and
             (raw[:3] == b"ID3" or raw[:1] == b"\xff"), "Payload differs from source pin")
    expected = {(i,"fire") for i in FAMILIES} | {(i,"reload") for i in RELOAD_IDS}
    need(seen == expected, "Action coverage")
    impl = inp.json(ART+"implementation.json")
    need(impl["runtimeAudioAccepted"] is False and impl["events"] == definitions(), "Audio claim/definitions drift")
    for file,h in impl["inputPins"].items():
        need(inp.hash(ART+safe(file)) == h, "Builder input pin drift")
    for file,meta in impl["outputs"].items():
        raw = inp.data(safe(file))
        need(sha(raw) == meta["sha256"] and len(raw) == meta["bytes"], "Generated output drift " + file)
    for file in assets:
        ogg_samples(inp.data(file))
    profile = inp.json(PROFILE)
    need(profile == inp.json(ART+"timed-profile.json") and set(profile) == {"stage","entries"} and
         profile["stage"] == "W102", "Timed profile shape")
    entries = profile["entries"]
    need(len(entries) == 6 and {(c["id"],c["ticks"]) for c in entries} == TIMED, "Exact six timed keys")
    legacy = inp.json(RES+"destiny/sounds/w63-reload.json")["entries"]
    for c in entries:
        i,t = c["id"], c["ticks"]
        old = [v for v in legacy if v["id"] == i and v["ticks"] == t]
        need(len(old) == 1 and old[0]["sourceEvent"] == "weapon."+FAMILIES[i]+".reload", "Not an existing W63 key")
        need(c["event"] == f"weapon.reload_w102.{i}.{t}" and c["sourceEvent"] == f"weapon.{i}.reload" and
             c["asset"] == f"assets/destiny/sounds/w102/{i}/reload_{t}.ogg" and
             c["sourceSha256"] == inp.hash(RES+f"assets/destiny/sounds/w102/{i}/reload.ogg"), "Timed identity/source hash")
        need(ogg_samples(inp.data(RES+c["asset"])) == t*1600, "Timed EOS deadline")
    return impl

def junit(inp, folder):
    paths = inp.files(folder)
    xmls = sorted(p for p in paths if p.endswith(".xml"))
    need(xmls, "No JUnit XML")
    identities = set()
    for p in xmls:
        doc = ET.fromstring(inp.data(p))
        need(doc.tag == "testsuite", "JUnit XML root must be one testsuite: " + p)
        need(all(child.tag in {"properties", "testcase", "system-out", "system-err"} for child in doc),
             "Unexpected/nested JUnit suite structure: " + p)
        cases = doc.findall("testcase")
        need(len(list(doc.iter("testcase"))) == len(cases), "Nested JUnit testcase: " + p)
        counts = {}
        for field in ("tests", "failures", "errors", "skipped"):
            value = doc.attrib.get(field)
            need(isinstance(value, str) and re.fullmatch(r"[0-9]+", value) is not None,
                 "Missing/invalid JUnit suite count " + field + ": " + p)
            counts[field] = int(value)
        need(counts["tests"] == len(cases), "JUnit suite tests header differs from direct testcase count: " + p)
        need(all(counts[field] == 0 for field in ("failures", "errors", "skipped")),
             "JUnit suite declares failure/error/skip: " + p)
        for case in cases:
            identity = (case.attrib.get("classname"),case.attrib.get("name"))
            need(all(identity) and identity not in identities, "Duplicate/unnamed JUnit case")
            need(not any(case.find(x) is not None for x in ("failure","error","skipped")), "JUnit case did not pass")
            identities.add(identity)
    return identities

def gates(inp, args, jar_sha):
    new_gt = len(re.findall(r"^\s*@GameTest\(", inp.data(GT+"NamedAudioW102GameTests.java").decode(), re.M))
    new_junit = len(re.findall(r"^\s*@Test\b", inp.data(TEST+"NamedAudioW102Test.java").decode(), re.M))
    need(new_gt == 2 and new_junit == 4 and args.expected_gametests == 829+new_gt and args.expected_junit == 721+new_junit, "Exact independently reviewed new test counts")
    old = junit(inp, "docs/qa/2026-10-25/w101/gate-2-xml")
    need(len(old) == 721, "Inherited JUnit identity inventory")
    results = []
    need(args.gates[0] >= 1 and args.gates[1] == args.gates[0]+1, "Choose two consecutive full gates")
    for n in args.gates:
        prefix = QA+f"/gate-{n}"
        row = inp.json(prefix+"-exit.json")
        need(row["returncode"] == 0 and row["finishedAt"] > row["startedAt"] and
             row["xmlFreshness"] and all(v is True for v in row["xmlFreshness"].values()), "Incomplete/stale full gate")
        log = inp.data(prefix+".log").decode()
        need(re.findall(r"All (\d+) required tests passed", log) == [str(args.expected_gametests)] and
             re.findall(r"(\d+) GAME TESTS COMPLETE", log) == [str(args.expected_gametests)] and
             "BUILD SUCCESSFUL" in log and "BUILD FAILED" not in log and "UP-TO-DATE" not in log and
             "FROM-CACHE" not in log, "Full forced gate log mismatch")
        need(re.search(r"(\d+) actionable tasks: \1 executed", log), "Not all actionable tasks executed")
        cases = junit(inp, prefix+"-xml")
        need(len(cases) == args.expected_junit and old <= cases and
             all(c[0] == "kim.biryeong.destiny.sound.NamedAudioW102Test" for c in cases-old), "JUnit identity preservation/new scope")
        need(inp.data(prefix+"-jar.sha256").decode().strip().split()[0] == jar_sha, "Gate JAR pin mismatch")
        need(set(row["xmlFreshness"]) == {Path(p).name for p in inp.files(prefix+"-xml") if p.endswith(".xml")}, "Freshness inventory mismatch")
        results.append({"gate":n,"junit":len(cases),"inheritedJUnit":len(old),"gametests":args.expected_gametests,
                        "startedAt":row["startedAt"],"finishedAt":row["finishedAt"]})
    need(results[0]["finishedAt"] <= results[1]["startedAt"], "Gates must be separate serial full runs")
    failures = []
    for n in range(1, args.gates[-1]+1):
        exit_path = QA+f"/gate-{n}-exit.json"
        prior = inp.json(exit_path)
        if prior["returncode"] != 0:
            log_path = QA+f"/gate-{n}.log"
            failures.append({"gate":n,"returncode":prior["returncode"],"exitSha256":inp.hash(exit_path),"logSha256":inp.hash(log_path)})
    return results, failures

def audit(args):
    inp = Inputs()
    need(inp.hash(OLD) == OLD_SHA, "W101 baseline manifest changed")
    old = inp.json(OLD)
    need(len(old["sha256"]) == 8704 and len(old["clientAssets"]) == 7191, "Baseline counts")
    seal = "docs/qa/2026-10-25/w101/SHA256SUMS"
    need(inp.hash(seal) == OLD_SEAL_SHA, "W101 QA seal changed")
    lines = inp.data(seal).decode().splitlines()
    need(len(lines) == 273, "W101 seal count")
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        need(match is not None, "Malformed seal")
        need(inp.hash("docs/qa/2026-10-25/w101/"+safe(match[2])) == match[1], "W101 sealed file changed")
    allowed_old = set(MIGRATIONS) | {SOUNDS, REGISTRY}
    for file,h in old["sha256"].items():
        if file not in allowed_old:
            need(inp.hash(safe(file)) == h, "Unexpected inherited change " + file)
    for file,h in {**MIGRATIONS, **FROZEN}.items():
        need(inp.hash(file) == h, "Reviewed finite bytes changed " + file)
    for file in allowed_old:
        need(inp.hash(QA+"/before/"+file) == old["sha256"][file], "Migration backup not W101 " + file)
    before = inp.json(QA+"/before/"+SOUNDS)
    now = inp.json(SOUNDS)
    need(set(now)-set(before) == set(definitions()) and not set(before)-set(now), "Sound event additions/removals")
    need(all(now[k] == v for k,v in before.items()) and all(now[k] == v for k,v in definitions().items()), "Inherited/new sound definitions")
    need(inp.json(ART+"event-definitions.json") == definitions(), "Independent definition contract")
    reg_before = inp.json(QA+"/before/"+REGISTRY)
    reg = inp.json(REGISTRY)
    expected_reg = decode(json.dumps(reg_before))
    expected_reg["entrypoints"]["fabric-gametest"].append("kim.biryeong.destiny.test.NamedAudioW102GameTests")
    pending = []
    if args.pending_tests and reg == reg_before:
        pending.append("GameTest registration not yet integrated")
    else:
        need(reg == expected_reg, "Registry must append only exact W102 GameTest")
    integration = inp.json(QA+"/integration.json")
    need(integration["stage"] == "W102" and integration["previous"] == "W101" and
         integration["expectedJUnit"] == 725 and integration["expectedGameTests"] == 831 and
         integration["nativeSequences"] == integration["nativePNG"] == 0 and
         integration["nativeAudioAccepted"] is False and integration["wholeGoalAchieved"] is False, "Master integration boundary")
    junit_names = set(re.findall(r"^\s*@Test void (\w+)\(", inp.data(TEST+"NamedAudioW102Test.java").decode(), re.M))
    gt_names = set(re.findall(r"^\s*public void (\w+)\(GameTestHelper", inp.data(GT+"NamedAudioW102GameTests.java").decode(), re.M))
    need(len(junit_names) == 4 and {tuple(v) for v in integration["newJUnitIdentities"]} ==
         {("kim.biryeong.destiny.sound.NamedAudioW102Test",n+"()") for n in junit_names} and
         len(gt_names) == 2 and set(integration["newGameTestMethods"]) == gt_names, "Exact source test identities")
    assets = expected_assets()
    new_source = assets | {PROFILE, BASE+"NamedReloadAudioW102.java", TEST+"NamedAudioW102Test.java", GT+"NamedAudioW102GameTests.java"}
    actual_source = set().union(*(inp.files(folder) for folder in SOURCE_ROOTS))
    inherited_source = {p for p in old["sha256"] if any(p.startswith(f+"/") for f in SOURCE_ROOTS)}
    missing = new_source-actual_source
    if args.pending_tests:
        need(missing <= {GT+"NamedAudioW102GameTests.java",TEST+"NamedAudioW102Test.java"}, "Only pending test sources may be missing")
        pending += sorted(missing)
    else:
        need(not missing, "Missing exact additions " + repr(sorted(missing)))
    need(actual_source-inherited_source == new_source-missing and inherited_source <= actual_source, "Finite source inventory drift")
    need(inp.files(RES+"assets/destiny/sounds/w102") == assets, "Exactly sixteen Ogg files required")
    audio_sources(inp, assets)
    snapshot = {p:inp.hash(p) for p in sorted(set(old["sha256"]) | new_source-missing | set(FROZEN) |
                {SELF,"scripts/audio/build_named_sounds_w102.py"} | inp.files(ART.rstrip("/")))}
    client = {p:inp.hash(p) for p in sorted(inp.files(RES+"assets"))}
    need(len(client) == 7207, "Client asset inventory must grow by sixteen")
    report = {"stage":"W102", "status":"SOURCE_PENDING_TESTS" if pending else "SOURCE_PASS", "pending":pending,
        "previousManifestSha256":OLD_SHA,"previousSourcePins":8704,"previousClientAssets":7191,
        "sourcePins":len(snapshot),"clientAssetCount":len(client),"newAssets":sorted(assets),
        "acceptedOldChanges":sorted(allowed_old),"newSourcePaths":sorted(new_source-assets),
        "nativeAudioAccepted":False,"nativeRenderingAccepted":False,"wholeGoalAchieved":False,
        "candidateOnly":True,"finalized":False,"generatorExecutedByAuditor":False,"childAgentAvailable":False}
    old_jar = inp.data(QA+"/before-product.jar")
    need(sha(old_jar) == old["jarSha256"], "Wrong baseline JAR")
    if args.jar:
        need(not pending, "Cannot audit JAR while tests pending")
        current_raw = inp.data(args.jar)
        current = archive(current_raw)
        previous = archive(old_jar)
        jar_delta = delta(hashes(previous),hashes(current))
        added = {p[len(RES):] for p in assets | {PROFILE}} | {
            "kim/biryeong/destiny/sound/NamedReloadAudioW102.class", "kim/biryeong/destiny/sound/NamedReloadAudioW102$Data.class"}
        need(jar_delta == {"added":sorted(added),"removed":[],"modified":["assets/destiny/sounds.json","kim/biryeong/destiny/sound/ReloadAudioProfile.class"]}, "Finite main JAR delta " + repr(jar_delta))
        for p in set(client) | {PROFILE}:
            need(current.get(p[len(RES):]) == inp.data(p), "Source/JAR resource mismatch " + p)
        report.update(jarSha256=sha(current_raw),previousJarSha256=sha(old_jar),jarDelta=jar_delta,status="JAR_PASS")
    if args.pack:
        need(args.jar is not None, "Pack audit requires product JAR")
        previous_raw = inp.data(args.before_pack)
        need(sha(previous_raw) == old["serverPackSha256"], "Not actual W101 baseline pack")
        before_pack = archive(previous_raw)
        raw = inp.data(args.pack)
        pack = archive(raw)
        pack_delta = delta(hashes(before_pack),hashes(pack))
        need(pack_delta == {"added":sorted(p[len(RES):] for p in assets),"removed":[],"modified":["assets/destiny/sounds.json"]}, "Finite actual pack delta " + repr(pack_delta))
        pack_sounds = decode(pack["assets/destiny/sounds.json"])
        old_pack_sounds = decode(before_pack["assets/destiny/sounds.json"])
        need(set(pack_sounds)-set(old_pack_sounds) == set(definitions()) and all(pack_sounds.get(k)==v for k,v in old_pack_sounds.items()) and
             all(pack_sounds.get(k)==v for k,v in definitions().items()), "Actual pack event contract")
        for p in assets:
            key = p[len(RES):]
            if key.endswith(".json"):
                need(decode(pack[key]) == inp.json(p), "Source/pack JSON mismatch " + key)
            else:
                need(pack.get(key) == inp.data(p), "Source/pack asset mismatch " + key)
        report.update(serverPackSha256=sha(raw),previousPackSha256=sha(previous_raw),packEntries=len(pack),packEntryDelta=pack_delta,status="PACK_PASS")
    if args.finalize:
        need(args.jar and args.pack and args.expected_gametests and args.expected_junit and not args.pending_tests,
             "Finalization requires JAR, actual pack, exact gate counts and complete tests")
        report["gates"], report["retainedPriorGateFailures"] = gates(inp,args,report["jarSha256"])
        report["finalPassingGates"] = args.gates
        report.update(finalized=True,status="SEALED_CANDIDATE")
    inp.recheck()
    report["inputSha256"] = dict(sorted(inp.hashes.items()))
    return report, snapshot, client

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jar", type=Path)
    p.add_argument("--pack", type=Path)
    p.add_argument("--before-pack", type=Path, default=Path("/tmp/destiny-w101-native/server/polymer/resource_pack.zip"))
    p.add_argument("--pending-tests", action="store_true", help="Source-only partial report; never a completed stage")
    p.add_argument("--gates", nargs=2, type=int, default=[1,2], metavar=("FIRST","SECOND"), help="Explicit consecutive passing gate numbers; earlier failures remain bound/reported")
    p.add_argument("--expected-gametests", type=int)
    p.add_argument("--expected-junit", type=int)
    p.add_argument("--finalize", action="store_true", help="Master-authorized seal only after two full forced gates")
    args = p.parse_args()
    try:
        report, snapshot, client = audit(args)
        if args.finalize:
            target = ROOT/"art/qa/w102/implementation.json"
            need(not target.is_symlink() and str(target.resolve()) not in report["inputSha256"], "Unsafe finalization target")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({**report,"sha256":snapshot,"clientAssets":client},sort_keys=True,indent=2)+"\n")
        print(json.dumps(report,sort_keys=True,indent=2))
        return 0
    except (AuditError,OSError,ValueError,KeyError,TypeError,ET.ParseError,zipfile.BadZipFile,IndexError,struct.error) as e:
        print(json.dumps({"stage":"W102","status":"FAIL","error":str(e)},sort_keys=True))
        return 1

if __name__ == "__main__":
    sys.exit(main())
