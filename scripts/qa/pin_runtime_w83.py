#!/usr/bin/env python3
"""W83 source inventory and deferred source/JAR/pack pinning; never builds.

Default/--audit is read-only, safe for an initial inventory while work continues.
Run --finalize only after the parent has stopped all workers and completed gates.
Finalization runs the three W83 --verify commands, compares two inventories and
artifact hashes, then writes only art/weapons/w83/implementation.json. Pinning is
not a gameplay, native framebuffer or acoustic certification.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path("docs/qa/2026-10-25/w83/baseline.json")
PREVIOUS = Path("art/weapons/w82/implementation.json")
IMPLEMENTATION = Path("art/weapons/w83/implementation.json")
ASSETS = Path("src/main/resources/assets")
SOUNDS = "src/main/resources/assets/destiny/sounds.json"
PREVIOUS_PACK = Path("/tmp/destiny-w82-native/server/polymer/resource_pack.zip")
PREVIOUS_PACK_SHA256 = "d32a3c846a9e81cd7e41d4712980c25e9544919a7bfd03fc34bb4722d2a16709"
MANIFESTS = (
    (Path("art/weapons/w83/model/manifest.json"), "outputSha256"),
    (Path("art/weapons/w83/audio/implementation.json"), "outputs"),
    (Path("art/weapons/w83/hud/manifest.json"), "outputs"),
)
EVENTS = {
    "weapon.ace_of_spades.fire", "weapon.ace_of_spades.reload",
    "weapon.reload_w83.ace_of_spades.55", "weapon.reload_w83.ace_of_spades.39",
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
    require(value["stage"] == "W83" and value["baselineStage"] == "W82", "Wrong baseline stages")
    require(value["previousImplementation"] == previous, "W82 manifest differs from saved baseline snapshot")
    require(len(previous["sha256"]) == 977, "Expected all 977 W82 pins")
    require(len(value["clientAssets"]) == 6404, "Expected all 6404 old client assets")
    return value


def sound_preservation(previous_pack, current_raw, audio):
    require(file_sha(previous_pack) == PREVIOUS_PACK_SHA256, "Previous pack is not the pinned W82 native archive")
    with zipfile.ZipFile(previous_pack) as archive:
        old_raw = archive.read("assets/destiny/sounds.json")
    old = json.loads(old_raw)
    current = json.loads(current_raw)
    require(len(old) == 152, "Expected 152 W82 sound definitions")
    require(set(audio["events"]) == EVENTS, "W83 audio declares unexpected events")
    require(set(current) - set(old) == EVENTS and len(current) == 156, "Expected exactly four new sound events")
    require(all(current.get(k) == v for k, v in old.items()), "An old sound definition changed semantically")
    require(all(current[k] == v for k, v in audio["events"].items()), "W83 event definitions differ from audio manifest")
    return dict(previousDefinitions=152, newDefinitions=4, currentDefinitions=156,
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
    # Full non-client resource coverage includes fabric metadata and all W83 data.
    paths.update(p for p in files("src/main/resources") if not Path(p).is_relative_to(ASSETS))
    paths.update(p for p in files("art/weapons/w83") if p != IMPLEMENTATION.as_posix())
    paths.update(p for p in files("scripts") if "w83" in Path(p).name.lower())
    declared = {}
    expected_inputs = {}
    for path, key in MANIFESTS:
        manifest = read(ROOT / path)
        require(manifest["stage"] == "W83", "Wrong component manifest: " + str(path))
        for name, digest in manifest[key].items():
            name = relative(name)
            paths.add(name)
            if Path(name).is_relative_to(ASSETS):
                require(name not in declared or declared[name] == digest, "Conflicting asset declarations: " + name)
                declared[name] = digest
            expected_inputs[name] = digest
        for name, digest in manifest.get("inputSha256", {}).items():
            name = relative(name)
            paths.add(name)
            expected_inputs[name] = digest
    audio = read(ROOT / MANIFESTS[1][0])
    for row in audio["sourcePins"]:
        name = relative(row["privatePath"])
        paths.add(name)
        expected_inputs[name] = row["sourceSha256"]
    provenance = read(ROOT / "art/weapons/w83/references/provenance.json")
    for row in provenance["sourceCaches"]:
        name = relative(row["path"])
        paths.add(name)
        expected_inputs[name] = row["sha256"]
    extraction = read(ROOT / "art/weapons/w83/data/extraction.json")
    formula = relative(extraction["formulaSource"])
    paths.add(formula)
    expected_inputs[formula] = extraction["formulaSha256"]
    current = {p: file_sha(ROOT / p) for p in sorted(files(ASSETS))}
    old_assets = saved["clientAssets"]
    drift = [p for p, digest in old_assets.items() if p != SOUNDS and current.get(p) != digest]
    require(not drift, "Old client assets missing/changed: " + ", ".join(drift))
    added = set(current) - set(old_assets)
    require(added == set(declared), "New asset inventory differs from W83 component manifests: " +
            str(dict(undeclared=sorted(added - set(declared)), missing=sorted(set(declared) - added))))
    require(all(current[p] == digest for p, digest in declared.items()), "Declared W83 asset hash drift")
    sounds = sound_preservation(previous_pack, (ROOT / SOUNDS).read_bytes(), audio)
    paths.update(added)
    paths.add(SOUNDS)
    hashes = {relative(p): file_sha(ROOT / p) for p in sorted(paths)}
    bad = [p for p, digest in expected_inputs.items() if hashes[p] != digest]
    require(not bad, "Component outputs/source inputs differ from recorded provenance: " + ", ".join(bad))
    model = read(ROOT / MANIFESTS[0][0])
    hud = read(ROOT / MANIFESTS[2][0])
    external = {str(model_source.resolve()): file_sha(model_source), hud["font"]: file_sha(Path(hud["font"]))}
    require(external[str(model_source.resolve())] == model["source"]["sha256"], "Original model SHA differs")
    require(external[hud["font"]] == hud["fontSha256"], "HUD font SHA differs")
    return dict(sha256=hashes, externalSha256=external, clientAssets=current, soundPreservation=sounds,
                previousPins=977, changedPreviousPins=sorted(p for p, digest in previous.items() if hashes[p] != digest),
                addedPins=sorted(set(hashes) - set(previous)), newClientAssetPaths=sorted(added),
                previousClientAssets=6404, unchangedClientAssetBytes=6403)


def run_components(python, model_source):
    commands = [
        ["scripts/art/build_ace_w83.py", "--source", str(model_source), "--verify"],
        ["scripts/audio/build_ace_sounds_w83.py", "--verify"],
        ["scripts/generate_ace_hud_w83.py", "--verify"],
    ]
    results = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for command in commands:
        result = subprocess.run(["rtk", "proxy", str(python), "-B", *command], cwd=ROOT,
                                env=env, capture_output=True, text=True)
        require(result.returncode == 0, "W83 component verifier failed: " + command[0] + "\n" + result.stdout + result.stderr)
        results.append(dict(script=command[0], arguments=command[1:], returncode=0, output=result.stdout.strip(),
                            repositoryOutputsReadOnly=True, audioTemporaryReencode=command[0].startswith("scripts/audio/")))
    return results


def summary(snapshot):
    return dict(stage="W83", preliminary=True, previousPins=snapshot["previousPins"],
                candidatePins=len(snapshot["sha256"]), changedPreviousPins=snapshot["changedPreviousPins"],
                addedPins=len(snapshot["addedPins"]), previousClientAssets=6404, unchangedClientAssetBytes=6403,
                newClientAssets=len(snapshot["newClientAssetPaths"]), sounds=snapshot["soundPreservation"],
                runtimeVerified=False, nativeClientRenderingCertified=False)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--audit", action="store_true", help="Read-only source/old-asset audit (default); no final hashes written")
    mode.add_argument("--finalize", action="store_true", help="Parent-only after workers stop: run verifiers, double-check stability and write implementation.json")
    result.add_argument("--components", action="store_true", help="Also run W83 model/audio/HUD --verify during an audit")
    result.add_argument("--python", type=Path, default=Path(sys.executable), help="Python with Pillow for HUD verification")
    result.add_argument("--model-source", type=Path, default=Path.home() / "Downloads/Ace.bbmodel")
    result.add_argument("--previous-pack", type=Path, default=PREVIOUS_PACK, help="Read-only W82 archive, must match d32a... SHA")
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
    manifest = dict(schema=1, stage="W83", baseline="W82", pinStatus="pinned", wholeGoalAchieved=False,
                    runtimeVerified=False, nativeClientRenderingCertified=False,
                    evidenceBoundary="Stable source/JAR/pack hashes only; run verify_runtime_w83.py separately. No final gameplay/framebuffer/acoustic claim.",
                    baselineSnapshot=BASELINE.as_posix(), previousImplementation=PREVIOUS.as_posix(),
                    pinnedVariant="headless", headlessDynamicFov=False,
                    previousPinCount=977, previousClientAssetCount=6404,
                    newClientAssets=len(before["newClientAssetPaths"]), **artifacts,
                    sourceDelta=dict(changedPreviousPins=before["changedPreviousPins"], addedPins=before["addedPins"]),
                    soundPreservation=before["soundPreservation"], newClientAssetPaths=before["newClientAssetPaths"],
                    componentVerifiers=checks, externalSha256=before["externalSha256"], sha256=before["sha256"])
    (ROOT / IMPLEMENTATION).write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(dict(stage="W83", pinStatus="pinned", sourcePins=len(before["sha256"]),
                          newClientAssets=manifest["newClientAssets"], runtimeVerified=False)))


if __name__ == "__main__":
    main()
