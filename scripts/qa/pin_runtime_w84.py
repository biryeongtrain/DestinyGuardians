#!/usr/bin/env python3
"""W84 source inventory and deferred source/JAR/pack pinning; never builds.

Default/--audit is read-only, safe for an initial inventory while work continues.
Run --finalize only after the parent has stopped all workers and completed gates.
Finalization runs W84 model/audio/HUD/runtime-extraction --verify, compares inventories and
artifact hashes, then writes only art/weapons/w84/implementation.json. Pinning is
not a gameplay, native framebuffer or acoustic certification.
"""
import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path("docs/qa/2026-10-25/w84/baseline.json")
PREVIOUS = Path("art/weapons/w83/implementation.json")
IMPLEMENTATION = Path("art/weapons/w84/implementation.json")
ASSETS = Path("src/main/resources/assets")
SOUNDS = "src/main/resources/assets/destiny/sounds.json"
PREVIOUS_PACK = Path("/tmp/destiny-w83-native/server/polymer/resource_pack.zip")
PREVIOUS_PACK_SHA256 = "c216b157d453741f3dd76cffd26e375bceedf298236ad6bc0073144204de850e"
MANIFESTS = (
    (Path("art/weapons/w84/model/manifest.json"), "outputSha256"),
    (Path("art/weapons/w84/audio/implementation.json"), "outputs"),
    (Path("art/weapons/w84/hud/manifest.json"), "outputs"),
)
EVENTS = {
    "weapon.izanagis_burden.fire", "weapon.izanagis_burden.reload",
    "weapon.izanagis_burden.honed_fire", "weapon.izanagis_burden.honed_reload",
    "weapon.reload_w84.izanagis_burden.61", "weapon.reload_w84.izanagis_burden.honed.61",
}
HELPERS = (
    "build.gradle", "gradle.properties",
    "scripts/build_weapons_w30.py", "scripts/audio/import_sounds_w33.py",
    "scripts/qa/verify_runtime_w42.py",
    "docs/qa/2026-10-24/w40/runtime-pack-verification.json",
    "art/hud/w41/manifest.json", "art/hud/w42/manifest.json",
    "libs/minigame-lib/src/main/resources/shaders/optional/projection.glsl",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text())


def relative(name):
    path = Path(name)
    require(not path.is_absolute() and ".." not in path.parts, "Expected safe repository-relative pin: " + str(name))
    require((ROOT / path).resolve().is_relative_to(ROOT), "Pin escapes repository: " + str(name))
    return path.as_posix()


def files(folder):
    return {p.relative_to(ROOT).as_posix() for p in (ROOT / folder).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store"}


def baseline():
    value = read(ROOT / BASELINE)
    previous = read(ROOT / PREVIOUS)
    require(value["stage"] == "W84" and value["baselineStage"] == "W83", "Wrong baseline stages")
    require(value["previousImplementation"] == previous, "W83 manifest differs from saved baseline snapshot")
    require(len(previous["sha256"]) == 1173, "Expected all 1173 W83 pins")
    require(len(value["clientAssets"]) == 6467, "Expected all 6467 old client assets")
    return value


def sound_preservation(previous_pack, current_raw, audio):
    require(file_sha(previous_pack) == PREVIOUS_PACK_SHA256, "Previous pack is not the pinned W83 native archive")
    with zipfile.ZipFile(previous_pack) as archive:
        old_raw = archive.read("assets/destiny/sounds.json")
    old = json.loads(old_raw)
    current = json.loads(current_raw)
    require(len(old) == 156, "Expected 156 W83 sound definitions")
    require(set(audio["events"]) == EVENTS, "W84 audio declares unexpected events")
    require(set(current) - set(old) == EVENTS and len(current) == 162, "Expected exactly six new sound events")
    require(all(current.get(k) == v for k, v in old.items()), "An old sound definition changed semantically")
    require(all(current[k] == v for k, v in audio["events"].items()), "W84 event definitions differ from audio manifest")
    return dict(previousDefinitions=156, newDefinitions=6, currentDefinitions=162,
                oldDefinitionsSemanticallyExact=True, addedEvents=sorted(EVENTS),
                previousPackSha256=PREVIOUS_PACK_SHA256, previousPackSoundsSha256=sha(old_raw))


def source_snapshot(previous_pack, model_source):
    saved = baseline()
    previous = saved["previousImplementation"]["sha256"]
    paths = {relative(p) for p in previous}
    paths.update((BASELINE.as_posix(), PREVIOUS.as_posix()))
    paths.update(HELPERS)
    for folder in ("src/main/java", "src/test/java", "src/gametest/java", "src/gametest/resources"):
        paths.update(files(folder))
    # Full non-client resource coverage includes fabric metadata and all W84 data.
    paths.update(p for p in files("src/main/resources") if not Path(p).is_relative_to(ASSETS))
    paths.update(p for p in files("art/weapons/w84") if p != IMPLEMENTATION.as_posix())
    paths.update(p for p in files("scripts") if "w84" in Path(p).name.lower())
    declared = {}
    component_assets = {}
    expected_inputs = {}
    # Retain the inherited external originals too, not just the 1173 repo pins.
    expected_external = dict(saved["previousImplementation"]["externalSha256"])

    def expect(name, digest):
        """Repo-relative pins remain repo-relative; external caches stay external."""
        path = Path(name)
        if path.is_absolute():
            key = str(path.resolve())
            require(key not in expected_external or expected_external[key] == digest, "Conflicting external provenance: " + key)
            expected_external[key] = digest
        else:
            key = relative(name)
            paths.add(key)
            require(key not in expected_inputs or expected_inputs[key] == digest, "Conflicting component provenance: " + key)
            expected_inputs[key] = digest

    for path, key in MANIFESTS:
        manifest = read(ROOT / path)
        require(manifest["stage"] == "W84", "Wrong component manifest: " + str(path))
        component_assets[path.parent.name] = sum(Path(name).is_relative_to(ASSETS) for name in manifest[key])
        for name, digest in manifest[key].items():
            name = relative(name)
            paths.add(name)
            if Path(name).is_relative_to(ASSETS):
                require(name not in declared or declared[name] == digest, "Conflicting asset declarations: " + name)
                declared[name] = digest
            expect(name, digest)
        for name, digest in manifest.get("inputSha256", {}).items():
            name = relative(name)
            expect(name, digest)
    audio = read(ROOT / MANIFESTS[1][0])
    for row in audio["sourcePins"]:
        name = relative(row["privatePath"])
        expect(name, row["sourceSha256"])
    toolchain = audio["toolchain"]
    expect(toolchain["ffmpegPath"], toolchain["ffmpegSha256"])
    expect(toolchain["w33HelperPath"], toolchain["w33HelperSha256"])
    expect("scripts/audio/build_izanagi_sounds_w84.py", toolchain["generatorSha256"])
    expect("art/weapons/w84/audio/source-pins.json", audio["sourcePinsSha256"])
    expect("art/weapons/w84/audio/folder-discovery.json", audio["discoverySha256"])
    provenance = read(ROOT / "art/weapons/w84/references/provenance.json")
    require(provenance["stage"].startswith("W84"), "Wrong research provenance stage")
    for row in provenance["sourceCaches"]:
        expect(row["path"], row["sha256"])
    reference_dir = Path("art/weapons/w84/references")
    for row in provenance["byteIdenticalReuses"]:
        name = relative(row["path"])
        expect((reference_dir/name).as_posix(), row["sha256"])
        expect(row["reusedFrom"], row["sha256"])
    for row in provenance["retrievals"]:
        name = relative(row["path"])
        expect((reference_dir/name).as_posix(), row["sha256"])
    # The research worker took a broad historical snapshot while model/audio
    # workers were still changing outputs. Enforce its declared research scope;
    # pin/report out-of-scope captures as history, never substitute them for the
    # current component manifests or silently rewrite the provenance file.
    scopes = [relative(pattern) for pattern in provenance["ownedPaths"]]
    historical_captures = {}
    research_outputs = set()
    for name,digest in provenance["outputHashes"].items():
        name = relative(name)
        if any(fnmatch.fnmatchcase(name, pattern) for pattern in scopes):
            expect(name,digest)
            research_outputs.add(name)
        else:
            historical_captures[name] = digest
    research_files = {p for p in files("art/weapons/w84") if any(fnmatch.fnmatchcase(p, pattern) for pattern in scopes)}
    research_files.discard("art/weapons/w84/references/provenance.json")  # Cannot self-hash.
    require(research_files == research_outputs, "Research provenance coverage differs: " + str(dict(
        undeclared=sorted(research_files-research_outputs), missing=sorted(research_outputs-research_files))))
    extraction = read(ROOT / "art/weapons/w84/data/runtime-extraction.json")
    require(extraction["stage"] == "W84", "Wrong runtime extraction stage")
    expect(extraction["formulaSource"], extraction["formulaSha256"])
    expect(extraction["researchSource"], extraction["researchSha256"])
    expect("src/main/resources/destiny/weapons/w84-exotics.json", extraction["runtimeSha256"])
    current = {p: file_sha(ROOT / p) for p in sorted(files(ASSETS))}
    old_assets = saved["clientAssets"]
    drift = [p for p, digest in old_assets.items() if p != SOUNDS and current.get(p) != digest]
    require(not drift, "Old client assets missing/changed: " + ", ".join(drift))
    added = set(current) - set(old_assets)
    require(added == set(declared), "New asset inventory differs from W84 component manifests: " +
            str(dict(undeclared=sorted(added - set(declared)), missing=sorted(set(declared) - added))))
    require(all(current[p] == digest for p, digest in declared.items()), "Declared W84 asset hash drift")
    sounds = sound_preservation(previous_pack, (ROOT / SOUNDS).read_bytes(), audio)
    paths.update(added)
    paths.add(SOUNDS)
    hashes = {relative(p): file_sha(ROOT / p) for p in sorted(paths)}
    bad = [p for p, digest in expected_inputs.items() if hashes[p] != digest]
    require(not bad, "Component outputs/source inputs differ from recorded provenance: " + ", ".join(bad))
    immutable = {p for p in previous if p.startswith("art/weapons/w83/") or
                 p.startswith("scripts/") and "w83" in Path(p).name.lower() or
                 p.startswith("src/main/resources/") and "w83" in Path(p).name.lower()}
    require(all(hashes[p] == previous[p] for p in immutable), "Old W83 art/scripts/resources changed")
    model = read(ROOT / MANIFESTS[0][0])
    hud = read(ROOT / MANIFESTS[2][0])
    expect(str(model_source.resolve()), model["source"]["sha256"])
    expect(hud["font"], hud["fontSha256"])
    external = {p: file_sha(Path(p)) for p in sorted(expected_external)}
    require(external == expected_external, "External cache/original/font SHA differs")
    history_drift = [p for p,digest in sorted(historical_captures.items())
                     if not (ROOT/p).is_file() or file_sha(ROOT/p) != digest]
    return dict(sha256=hashes, externalSha256=external, clientAssets=current, soundPreservation=sounds,
                previousPins=1173, changedPreviousPins=sorted(p for p, digest in previous.items() if hashes[p] != digest),
                addedPins=sorted(set(hashes) - set(previous)), newClientAssetPaths=sorted(added),
                previousClientAssets=6467, unchangedClientAssetBytes=6466,
                inventory=dict(mainJavaFiles=sum(p.startswith("src/main/java/") and p.endswith(".java") for p in hashes),
                    testJavaFiles=sum(p.startswith("src/test/java/") and p.endswith(".java") for p in hashes),
                    gameTestJavaFiles=sum(p.startswith("src/gametest/java/") and p.endswith(".java") for p in hashes),
                    nonClientMainResources=sum(p.startswith("src/main/resources/") and not Path(p).is_relative_to(ASSETS) for p in hashes),
                    currentClientAssets=len(current), componentClientAssets=component_assets,
                    newMainJavaPaths=sorted(p for p in hashes if p not in previous and p.startswith("src/main/java/") and p.endswith(".java"))),
                immutablePreviousPins=len(immutable),
                provenance=dict(verifiedResearchOutputs=len(research_outputs),
                    verifiedRetrievals=len(provenance["retrievals"]),
                    verifiedByteIdenticalReuses=len(provenance["byteIdenticalReuses"]),
                    verifiedSourceCaches=len(provenance["sourceCaches"]),
                    historicalOutOfScopeCaptures=len(historical_captures),
                    staleHistoricalOutOfScopeCaptures=history_drift,
                    policy="Research-owned outputs strict; historical cross-worker captures informational; current component manifests authoritative"))


def run_components(python, model_source):
    commands = [
        ["scripts/art/build_izanagi_w84.py", "--source", str(model_source), "--verify"],
        ["scripts/audio/build_izanagi_sounds_w84.py", "--verify"],
        ["scripts/generate_honed_hud_w84.py", "--verify"],
        ["scripts/extract_izanagi_w84.py", "--verify"],
    ]
    results = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONOPTIMIZE="0")
    for command in commands:
        result = subprocess.run(["rtk", "proxy", str(python), "-B", *command], cwd=ROOT,
                                env=env, capture_output=True, text=True)
        require(result.returncode == 0, "W84 component verifier failed: " + command[0] + "\n" + result.stdout + result.stderr)
        results.append(dict(script=command[0], arguments=command[1:], returncode=0, output=result.stdout.strip(),
                            repositoryOutputsReadOnly=True, audioTemporaryReencode=command[0].startswith("scripts/audio/")))
    return results


def summary(snapshot):
    return dict(stage="W84", preliminary=True, previousPins=snapshot["previousPins"],
                candidatePins=len(snapshot["sha256"]), changedPreviousPins=snapshot["changedPreviousPins"],
                addedPins=len(snapshot["addedPins"]), previousClientAssets=6467, unchangedClientAssetBytes=6466,
                newClientAssets=len(snapshot["newClientAssetPaths"]), sounds=snapshot["soundPreservation"],
                immutableW83Pins=snapshot["immutablePreviousPins"], externalPins=len(snapshot["externalSha256"]),
                provenance=snapshot["provenance"], inventory=snapshot["inventory"],
                runtimeVerified=False, nativeClientRenderingCertified=False)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--audit", action="store_true", help="Read-only source/old-asset audit (default); no final hashes written")
    mode.add_argument("--finalize", action="store_true", help="Parent-only after workers stop: run verifiers, double-check stability and write implementation.json")
    result.add_argument("--components", action="store_true", help="Also run W84 model/audio/HUD/runtime-extraction --verify during an audit")
    result.add_argument("--python", type=Path, default=Path(sys.executable), help="Python with Pillow for HUD verification")
    result.add_argument("--model-source", type=Path, default=Path.home() / "Downloads/izanagi.bbmodel")
    result.add_argument("--previous-pack", type=Path, default=PREVIOUS_PACK, help="Read-only W83 archive, must match c216... SHA")
    result.add_argument("--jar", type=Path, default=ROOT / "build/libs/destiny-guardians-0.1.0+26.3.jar")
    result.add_argument("--server-pack", type=Path, help="Current generated headless/server pack, required for --finalize")
    result.add_argument("--shader-config", type=Path, help="Config used to create that pack, required for --finalize")
    return result


def main():
    args = parser().parse_args()
    require(not args.finalize or (args.server_pack and args.shader_config), "--finalize requires --server-pack and --shader-config")
    before = source_snapshot(args.previous_pack, args.model_source)
    if not args.finalize:
        report = summary(before)
        if args.components:
            report["componentVerifiers"] = run_components(args.python, args.model_source)
            require(source_snapshot(args.previous_pack, args.model_source) == before, "Sources changed during audit; retry after workers settle")
        print(json.dumps(report, indent=2))
        return
    shader = read(args.shader_config)
    require(type(shader.get("dynamic-fov-shader", False)) is bool and not shader.get("dynamic-fov-shader", False),
            "Final pin must use the headless dynamic-FOV=false config; native verification is a separate variant")
    artifacts = dict(jarSha256=file_sha(args.jar), serverPackSha256=file_sha(args.server_pack), shaderConfigSha256=file_sha(args.shader_config))
    checks = run_components(args.python, args.model_source)
    require(source_snapshot(args.previous_pack, args.model_source) == before, "Sources changed during finalization; no pins written")
    require(artifacts == dict(jarSha256=file_sha(args.jar), serverPackSha256=file_sha(args.server_pack),
                              shaderConfigSha256=file_sha(args.shader_config)), "JAR/pack/config changed during finalization; no pins written")
    manifest = dict(schema=1, stage="W84", baseline="W83", pinStatus="pinned", wholeGoalAchieved=False,
                    runtimeVerified=False, nativeClientRenderingCertified=False,
                    evidenceBoundary="Stable source/JAR/pack hashes only; run verify_runtime_w84.py separately. No final gameplay/framebuffer/acoustic claim.",
                    baselineSnapshot=BASELINE.as_posix(), previousImplementation=PREVIOUS.as_posix(),
                    pinnedVariant="headless", headlessDynamicFov=False,
                    previousPinCount=1173, previousClientAssetCount=6467,
                    newClientAssets=len(before["newClientAssetPaths"]), **artifacts,
                    sourceDelta=dict(changedPreviousPins=before["changedPreviousPins"], addedPins=before["addedPins"]),
                    soundPreservation=before["soundPreservation"], newClientAssetPaths=before["newClientAssetPaths"],
                    provenance=before["provenance"], immutableW83Pins=before["immutablePreviousPins"],
                    inventory=before["inventory"],
                    componentVerifiers=checks, externalSha256=before["externalSha256"], sha256=before["sha256"])
    (ROOT / IMPLEMENTATION).write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(dict(stage="W84", pinStatus="pinned", sourcePins=len(before["sha256"]),
                          newClientAssets=manifest["newClientAssets"], runtimeVerified=False)))


if __name__ == "__main__":
    main()
