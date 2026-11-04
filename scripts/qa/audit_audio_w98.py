#!/usr/bin/env python3
"""Exact finite W98 source/JAR/pack delta audit. No runtime or playback. No namespace exemptions."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / "docs/qa/2026-10-25/w98"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def require(ok, why):
    if not ok: raise RuntimeError(why)


def entries(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), "Duplicate ZIP entries")
        return {n: hashlib.sha256(z.read(n)).hexdigest() for n in names if not n.endswith("/")}


def delta(old, new):
    return dict(added=sorted(new.keys() - old.keys()), removed=sorted(old.keys() - new.keys()),
                modified=sorted(n for n in old.keys() & new.keys() if old[n] != new[n]))


def snapshot():
    baseline = read(QA / "baseline.json")
    old_path = ROOT / "art/qa/w96/implementation.json"
    require(sha(old_path) == baseline["previousManifestSha256"], "W96 manifest drift")
    old = read(old_path)
    accepted = read(QA / "integration.json")
    inherited = {p: sha(ROOT / p) for p in old["sha256"]}
    changed = sorted(p for p, h in old["sha256"].items() if inherited[p] != h)
    require(changed == sorted(accepted["acceptedOldChanges"]), "Unexpected previous source changes: " + str(changed))
    added = set()
    for folder in ("src/main/java", "src/main/resources", "src/test/java", "src/test/resources", "src/gametest/java", "src/gametest/resources"):
        current = {p.relative_to(ROOT).as_posix() for p in (ROOT / folder).rglob("*") if p.is_file()}
        previous = {p for p in inherited if p.startswith(folder + "/")}
        require(previous <= current, "Old source removed")
        added |= current - previous
    expected_added = set(accepted["newSourcePaths"]) | set(baseline["pendingCandidate"])
    require(added == expected_added, "Unexpected source additions: " + str(added ^ expected_added))
    for p, h in baseline["pendingCandidate"].items(): require(sha(ROOT / p) == h, "Unregistered W97 candidate changed")
    require("CriticalHudLayerW97GameTests" not in (ROOT / "src/gametest/resources/fabric.mod.json").read_text(), "W97 accidentally registered")
    for p, h in accepted["reviewedSourceSha256"].items(): require(sha(ROOT / p) == h, "Reviewed source drift " + p)
    require(all(sha(p) == h for p, h in old["externalSha256"].items()), "External source drift")
    require(all(sha(p) == h for p, h in baseline["protected"].items()), "Protected Vision drift")
    require(all(sha(ROOT / p["path"]) == p["sha256"] for p in baseline["normalQAPlayers"]), "Normal QA drift")
    assets = {p.relative_to(ROOT).as_posix(): sha(p) for p in (ROOT / "src/main/resources/assets").rglob("*") if p.is_file()}
    new_assets = accepted["newClientAssets"]
    d = delta(old["clientAssets"], assets)
    require(d == dict(added=sorted(new_assets), removed=[], modified=["src/main/resources/assets/destiny/sounds.json"]), "Asset delta " + str(d))
    before = read(QA / "before/src/main/resources/assets/destiny/sounds.json")
    now = read(ROOT / "src/main/resources/assets/destiny/sounds.json")
    definitions = read(ROOT / "art/weapons/w98/audio/event-definitions.json")
    require(before.keys() == now.keys() and set(definitions) == set(accepted["changedEvents"]), "Sound event identity drift")
    changed_events = sorted(k for k in before if before[k] != now[k])
    require(changed_events == sorted(accepted["changedEvents"]), "Unexpected changed event")
    for key, value in definitions.items(): require(now[key] == value and before[key]["sounds"][0] == value["sounds"][0], "Exact event/retained clip drift")
    pins = dict(inherited, **{p: sha(ROOT / p) for p in added})
    for p, h in accepted["reviewedSourceSha256"].items(): pins[p] = h
    return dict(sha256=pins, externalSha256=old["externalSha256"], clientAssets=assets,
                changedPreviousPins=changed, changedEvents=changed_events, assetDelta=d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--finalize", action="store_true")
    args = ap.parse_args()
    before = snapshot()
    accepted = read(QA / "integration.json")
    base = read(QA / "baseline.json")
    jar = ROOT / "build/libs/destiny-guardians-0.1.0+26.3.jar"
    old_jar = QA / "before-product.jar"
    require(sha(old_jar) == base["previousJarSha256"], "Archived prior JAR drift")
    expected = dict(added=sorted(p.removeprefix("src/main/resources/") for p in accepted["newClientAssets"]), removed=[],
                    modified=["assets/destiny/sounds.json"])
    jar_delta = delta(entries(old_jar), entries(jar))
    require(jar_delta == expected, "Unexpected product JAR entries " + str(jar_delta))
    report = dict(stage="W98", jarSha256=sha(jar), sourcePins=len(before["sha256"]), clientAssets=len(before["clientAssets"]),
                  jarDelta=jar_delta, wholeGoalAchieved=False, nativeAudioAccepted=False,
                  evidenceBoundary="Source/asset/build/server-pack provenance only; no native playback, selection distribution, acoustic or framebuffer certification.")
    if args.pack:
        old_pack = ROOT / "docs/qa/2026-10-25/w96/native/resource_pack.zip"
        pack_delta = delta(entries(old_pack), entries(args.pack))
        require(pack_delta == expected, "Unexpected FOVtrue server pack entries " + str(pack_delta))
        resource_entries = entries(args.pack)
        # Explicit finite serialization contract: all paths below are pinned and checked
        # against BOTH the historical W96 pack and this generated pack. No prefix skips.
        policy = read(QA / "pack-serialization-policy.json")
        serialized = set(policy["exactCompactJson"])
        require(len(serialized) == policy["serializedAssetCount"] == 146, "Serialization scope drift")
        require("assets/destiny/sounds.json" in serialized, "Missing sound serialization contract")
        for name in serialized:
            current_source = ROOT / "src/main/resources" / name
            old_source = QA / "before/src/main/resources/assets/destiny/sounds.json" if name == "assets/destiny/sounds.json" else current_source
            for pack, source in ((old_pack, old_source), (args.pack, current_source)):
                expected_json = json.dumps(read(source), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                with zipfile.ZipFile(pack) as zipped:
                    require(zipped.read(name) == expected_json, "Exact compact serialization differs " + name + " in " + str(pack))
        byte_identical = 0
        for path, h in before["clientAssets"].items():
            name = path.removeprefix("src/main/resources/")
            if name in serialized:
                continue  # Exact old/new serialized bytes required above.
            require(resource_entries.get(name) == h, "Actual pack differs from source asset " + name)
            byte_identical += 1
        require(byte_identical == policy["byteExactSourceAssets"] == 6873, "Unexpected byte-exact asset count")
        report.update(serverGeneratedPackSha256=sha(args.pack), serverGeneratedPackDelta=pack_delta,
                      serverGeneratedPackEntries=len(resource_entries), packVariant="FOVtrue server-generated; no W98 client/cache",
                      sourceByteIdenticalPackAssets=byte_identical,
                      exactSerializedJsonAssets={name: resource_entries[name] for name in sorted(serialized)})
    require(snapshot() == before, "Inputs changed during audit")
    if args.finalize:
        require(args.pack is not None, "Actual pack required")
        gates = read(QA / "gate-summary.json")
        require(gates["jarSha256"] == sha(jar) and len(gates["finalPassingGates"]) == 2, "Gates mismatch")
        output = ROOT / "art/qa/w98/implementation.json"; output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(dict(stage="W98", baseline="W96; W97 layer candidate remains unregistered",
                                         acceptance="automated/source/server-pack only; native audio pending", wholeGoalAchieved=False,
                                         jarSha256=sha(jar), serverPackSha256=sha(args.pack), **before), indent=2) + "\n")
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__": main()
