#!/usr/bin/env python3
"""W85 inventory and parent-deferred pinning. Never builds or launches.

Default/--audit is stdout-only and read-only while workers are active. Missing
incoming HUD/research deliverables are reported as gaps, not final source pins.
--finalize is for the parent ONLY after workers/gates settle: verify the HUD,
check source/artifact stability, then write W85 implementation.json. This script
does not certify gameplay, native rendering, flinch tuning or research accuracy.
"""
import argparse
import fnmatch
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from pin_runtime_w84 import ROOT, ASSETS, file_sha, files, read, relative, require, sha

BASELINE = Path("docs/qa/2026-10-25/w85/baseline.json")
PREVIOUS = Path("art/weapons/w84/implementation.json")
PREVIOUS_PACK = ROOT / "docs/qa/2026-10-25/w85/w84-pack.zip"
IMPLEMENTATION = Path("art/weapons/w85/implementation.json")
ART = Path("art/weapons/w85")
HUD_MANIFEST = ART / "hud/manifest.json"
HUD_GENERATOR = Path("scripts/generate_no_distractions_hud_w85.py")
SOUNDS = "src/main/resources/assets/destiny/sounds.json"
PREVIOUS_PINS = 1373
PREVIOUS_ASSETS = 6537
MUTABLE_RESOURCE_PATHS = {
    "src/main/resources/destiny.mixins.json",
    "src/gametest/resources/fabric.mod.json",
}


def baseline():
    saved = read(ROOT / BASELINE)
    previous = read(ROOT / PREVIOUS)
    require(saved["stage"] == "W85" and saved["baselineStage"] == "W84", "Wrong W85 baseline stages")
    require(previous == saved["previousImplementation"], "W84 implementation differs from the baseline snapshot")
    require(previous["stage"] == "W84" and previous["pinStatus"] == "pinned", "Previous W84 manifest is not pinned")
    require(len(previous["sha256"]) == PREVIOUS_PINS, "Expected all 1373 inherited W84 pins")
    require(len(saved["clientAssets"]) == PREVIOUS_ASSETS, "Expected all 6537 old client assets")
    return saved


def sound_preservation(previous_pack, current_raw, expected_pack_sha):
    require(file_sha(previous_pack) == expected_pack_sha, "Archived pack differs from pinned W84 headless pack")
    with zipfile.ZipFile(previous_pack) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), "Duplicate previous-pack entries")
        old_raw = archive.read("assets/destiny/sounds.json")
    old, current = json.loads(old_raw), json.loads(current_raw)
    require(len(old) == 162 and current == old, "W85 must preserve all 162 sound events; no additions or edits")
    return dict(previousDefinitions=162, currentDefinitions=162, newDefinitions=0,
                oldDefinitionsSemanticallyExact=True, sourceBytesExactToBaseline=True,
                previousPackSha256=expected_pack_sha, previousPackSoundsSha256=sha(old_raw))


def source_snapshot(previous_pack=PREVIOUS_PACK, *, require_ready=False):
    saved = baseline()
    previous = saved["previousImplementation"]["sha256"]
    paths = {relative(name) for name in previous}
    paths.update((BASELINE.as_posix(), PREVIOUS.as_posix()))
    if previous_pack.resolve().is_relative_to(ROOT):
        paths.add(previous_pack.resolve().relative_to(ROOT).as_posix())
    paths.update(("scripts/qa/pin_runtime_w84.py", "scripts/qa/verify_runtime_w84.py"))
    for folder in ("src/main/java", "src/test/java", "src/gametest/java", "src/gametest/resources"):
        paths.update(files(folder))
    paths.update(p for p in files("src/main/resources") if not Path(p).is_relative_to(ASSETS))
    paths.update(p for p in files(ART) if p != IMPLEMENTATION.as_posix())
    paths.update(p for p in files("scripts") if "w85" in Path(p).name.lower())
    expected = {}
    external_expected = dict(saved["previousImplementation"]["externalSha256"])
    gaps = []

    def expect(name, digest):
        require(isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
                "Invalid declared SHA256: " + str(name))
        path = Path(name)
        if path.is_absolute():
            key = str(path.resolve())
            require(key not in external_expected or external_expected[key] == digest, "Conflicting external pin: " + key)
            external_expected[key] = digest
        else:
            key = relative(name)
            paths.add(key)
            require(key not in expected or expected[key] == digest, "Conflicting declared pin: " + key)
            expected[key] = digest

    declared = {}
    if (ROOT / HUD_MANIFEST).is_file():
        hud = read(ROOT / HUD_MANIFEST)
        require(hud["stage"] == "W85", "Wrong HUD manifest stage")
        for name, digest in hud["outputs"].items():
            name = relative(name)
            expect(name, digest)
            if Path(name).is_relative_to(ASSETS):
                declared[name] = digest
        for name, digest in hud.get("inputSha256", {}).items():
            expect(name, digest)
        if "font" in hud or "fontSha256" in hud:
            expect(hud["font"], hud["fontSha256"])
        if "generatorSha256" in hud:
            expect(HUD_GENERATOR.as_posix(), hud["generatorSha256"])
    else:
        gaps.append("Missing W85 HUD manifest: " + HUD_MANIFEST.as_posix())
    if not (ROOT / HUD_GENERATOR).is_file():
        gaps.append("Missing W85 HUD generator: " + HUD_GENERATOR.as_posix())

    # Verify the actual declarations already used by this research sidecar.
    # Do not reinterpret copied W84 provenance as a live W85 component manifest.
    research_counts = {}
    references = ART / "references"
    for filename in ("retrievals.json", "reuse-provenance.json"):
        path = references / filename
        if not (ROOT / path).is_file():
            continue
        rows = read(ROOT / path)
        require(isinstance(rows, list), "Expected research record list: " + str(path))
        count = 0
        for row in rows:
            if "sha256" not in row:
                continue  # Failed/unhashed retrievals remain pinned evidence, not verified downloads.
            name = relative(row["path"])
            expect((references / name).as_posix(), row["sha256"])
            if "reusedFrom" in row:
                expect(row["reusedFrom"], row["sha256"])
            count += 1
        research_counts[filename] = count
    for name in (ART / "reference-notes.md", ART / "data/research.json"):
        if not (ROOT / name).is_file():
            gaps.append("Missing research deliverable: " + name.as_posix())
    research_manifest = references / "provenance.json"
    if (ROOT / research_manifest).is_file():
        provenance = read(ROOT / research_manifest)
        require(provenance["stage"].startswith("W85"), "Wrong research provenance stage")
        scopes = [relative(name) for name in provenance["ownedPaths"]]
        require(set(scopes) == {(ART/"reference-notes.md").as_posix(), (ART/"references/*").as_posix(),
                                (ART/"data/research.json").as_posix()}, "Unexpected research ownership scope")
        require(provenance["retrievals"] == read(ROOT/references/"retrievals.json"), "Research retrieval declarations differ")
        require(provenance["byteIdenticalReuses"] == read(ROOT/references/"reuse-provenance.json"), "Research reuse declarations differ")
        research_outputs = set()
        for row in provenance["outputHashes"]:
            name = relative((ART/relative(row["path"])).as_posix())
            require(name not in research_outputs, "Duplicate research output pin: " + name)
            require(any(fnmatch.fnmatchcase(name, scope) for scope in scopes), "Research output outside ownership scope: " + name)
            require(type(row["bytes"]) is int and row["bytes"] >= 0, "Invalid research byte count: " + name)
            require((ROOT/name).stat().st_size == row["bytes"], "Research byte-length drift: " + name)
            expect(name, row["sha256"])
            research_outputs.add(name)
        research_files = {p for p in files(ART) if any(fnmatch.fnmatchcase(p, scope) for scope in scopes)}
        research_files.discard(research_manifest.as_posix())  # Provenance cannot hash itself; inventory pins it.
        require(research_files == research_outputs, "Research hash inventory differs: " + str(dict(
            undeclared=sorted(research_files-research_outputs), missing=sorted(research_outputs-research_files))))
        research_counts["outputHashes"] = len(research_outputs)
        research = read(ROOT/ART/"data/research.json")
        require(research["stage"].startswith("W85") and research["provenance"] == "references/provenance.json",
                "Research document points at wrong provenance/stage")
    else:
        gaps.append("Missing strict research provenance: " + research_manifest.as_posix())

    current = {relative(p): file_sha(ROOT / p) for p in sorted(files(ASSETS))}
    drift = [p for p, digest in saved["clientAssets"].items() if current.get(p) != digest]
    require(not drift, "Old client assets missing/changed (sounds included): " + ", ".join(drift))
    added = set(current) - set(saved["clientAssets"])
    if added != set(declared):
        gaps.append("New asset inventory differs from HUD outputs: " + str(dict(
            undeclared=sorted(added-set(declared)), missing=sorted(set(declared)-added))))
    require(all(current.get(p) == digest for p, digest in declared.items()), "Declared W85 HUD asset hash drift")
    sounds = sound_preservation(previous_pack, (ROOT / SOUNDS).read_bytes(), saved["previousImplementation"]["serverPackSha256"])
    paths.update(added)
    missing = [p for p in sorted(paths) if not (ROOT / p).is_file()]
    require(not missing, "Inherited/declared source pin missing: " + ", ".join(missing))
    hashes = {relative(p): file_sha(ROOT / p) for p in sorted(paths)}
    bad = [p for p, digest in expected.items() if hashes[p] != digest]
    require(not bad, "Declared component/research hash drift: " + ", ".join(bad))
    immutable_art_scripts = {p for p in previous if p.startswith(("art/", "scripts/"))}
    immutable_resources = {p for p in previous if p.startswith(("src/main/resources/", "src/gametest/resources/"))
                           and p not in MUTABLE_RESOURCE_PATHS}
    immutable = immutable_art_scripts | immutable_resources
    drift = sorted(p for p in immutable if hashes[p] != previous[p])
    require(not drift, "Immutable old art/scripts/resources changed: " + ", ".join(drift))
    external = {name: file_sha(Path(name)) for name in sorted(external_expected)}
    require(external == external_expected, "Inherited/declared external pins differ")
    require(not require_ready or not gaps, "W85 not ready for finalization: " + "; ".join(gaps))
    return dict(sha256=hashes, externalSha256=external, clientAssets=current,
                previousPins=PREVIOUS_PINS, previousClientAssets=PREVIOUS_ASSETS,
                unchangedClientAssetBytes=PREVIOUS_ASSETS, soundPreservation=sounds,
                changedPreviousPins=sorted(p for p, digest in previous.items() if hashes[p] != digest),
                addedPins=sorted(set(hashes)-set(previous)), newClientAssetPaths=sorted(added),
                immutablePreviousPins=len(immutable), gaps=gaps,
                preservationPolicy=dict(immutableArtScriptPins=len(immutable_art_scripts),
                    immutableResourcePins=len(immutable_resources),
                    mutableResourceExceptions=sorted(MUTABLE_RESOURCE_PATHS)),
                provenance=dict(verifiedResearchDeclarations=research_counts,
                    researchPolicy="Strict W85 research output/retrieval/reuse hashes and complete owned-scope coverage; no research-truth certification"),
                inventory=dict(mainJavaFiles=sum(p.startswith("src/main/java/") and p.endswith(".java") for p in hashes),
                    testJavaFiles=sum(p.startswith("src/test/java/") and p.endswith(".java") for p in hashes),
                    gameTestJavaFiles=sum(p.startswith("src/gametest/java/") and p.endswith(".java") for p in hashes),
                    nonClientMainResources=sum(p.startswith("src/main/resources/") and not Path(p).is_relative_to(ASSETS) for p in hashes),
                    currentClientAssets=len(current), componentClientAssets=dict(hud=len(declared)),
                    newMainJavaPaths=sorted(p for p in hashes if p not in previous and p.startswith("src/main/java/") and p.endswith(".java"))))


def run_components(python):
    command = ["rtk", "proxy", str(python), "-B", HUD_GENERATOR.as_posix(), "--verify"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONOPTIMIZE="0"))
    require(result.returncode == 0, "W85 HUD verifier failed:\n" + result.stdout + result.stderr)
    return [dict(script=HUD_GENERATOR.as_posix(), arguments=["--verify"], returncode=0,
                 output=result.stdout.strip(), repositoryOutputsReadOnly=True)]


def summary(snapshot):
    return dict(stage="W85", preliminary=True, auditPassed=not snapshot["gaps"], gaps=snapshot["gaps"],
                previousPins=PREVIOUS_PINS, candidatePins=len(snapshot["sha256"]),
                addedPins=len(snapshot["addedPins"]), changedPreviousPins=snapshot["changedPreviousPins"],
                previousClientAssets=PREVIOUS_ASSETS, unchangedClientAssetBytes=PREVIOUS_ASSETS,
                newClientAssets=len(snapshot["newClientAssetPaths"]), sounds=snapshot["soundPreservation"],
                immutablePreviousPins=snapshot["immutablePreviousPins"], externalPins=len(snapshot["externalSha256"]),
                inventory=snapshot["inventory"], provenance=snapshot["provenance"],
                preservationPolicy=snapshot["preservationPolicy"],
                runtimeVerified=False, nativeClientRenderingCertified=False)


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--audit", action="store_true", help="Read-only inventory with pending gaps (default); stdout only")
    mode.add_argument("--finalize", action="store_true", help="Parent ONLY after workers/gates stop: verify HUD, check stability, write W85 implementation")
    result.add_argument("--components", action="store_true", help="Also run W85 HUD --verify during an audit")
    result.add_argument("--python", type=Path, default=Path(sys.executable), help="Python with Pillow for HUD --verify")
    result.add_argument("--previous-pack", type=Path, default=PREVIOUS_PACK, help="Archived W84 headless pack; SHA must match W84 manifest")
    result.add_argument("--jar", type=Path, default=ROOT / "build/libs/destiny-guardians-0.1.0+26.3.jar")
    result.add_argument("--server-pack", type=Path, help="Existing current headless pack, required for --finalize")
    result.add_argument("--shader-config", type=Path, help="Config for that pack, required for --finalize")
    return result


def main():
    args = parser().parse_args()
    require(not args.finalize or (args.server_pack and args.shader_config), "--finalize requires --server-pack and --shader-config")
    before = source_snapshot(args.previous_pack, require_ready=args.finalize)
    if not args.finalize:
        report = summary(before)
        if args.components:
            report["componentVerifiers"] = run_components(args.python)
            require(source_snapshot(args.previous_pack) == before, "Sources changed during audit; retry after workers settle")
        print(json.dumps(report, indent=2))
        return
    shader = read(args.shader_config)
    require(type(shader.get("dynamic-fov-shader", False)) is bool and not shader.get("dynamic-fov-shader", False),
            "Final pin requires headless dynamic-FOV=false; native verification is a separate variant")
    paths = dict(jarSha256=args.jar, serverPackSha256=args.server_pack, shaderConfigSha256=args.shader_config)
    artifacts = {key: file_sha(path) for key, path in paths.items()}
    checks = run_components(args.python)
    require(source_snapshot(args.previous_pack, require_ready=True) == before, "Sources changed during finalization; no pins written")
    require({key: file_sha(path) for key, path in paths.items()} == artifacts, "Artifacts changed during finalization; no pins written")
    manifest = dict(schema=1, stage="W85", baseline="W84", pinStatus="pinned", wholeGoalAchieved=False,
                    runtimeVerified=False, nativeClientRenderingCertified=False,
                    evidenceBoundary="Stable source/JAR/pack pins only; run verify_runtime_w85.py separately. No gameplay/native/flinch certification.",
                    baselineSnapshot=BASELINE.as_posix(), previousImplementation=PREVIOUS.as_posix(),
                    pinnedVariant="headless", headlessDynamicFov=False,
                    previousPinCount=PREVIOUS_PINS, previousClientAssetCount=PREVIOUS_ASSETS,
                    newClientAssets=len(before["newClientAssetPaths"]), newClientAssetPaths=before["newClientAssetPaths"], **artifacts,
                    sourceDelta=dict(changedPreviousPins=before["changedPreviousPins"], addedPins=before["addedPins"]),
                    soundPreservation=before["soundPreservation"], provenance=before["provenance"], inventory=before["inventory"],
                    immutablePreviousPins=before["immutablePreviousPins"], preservationPolicy=before["preservationPolicy"],
                    componentVerifiers=checks,
                    externalSha256=before["externalSha256"], sha256=before["sha256"])
    (ROOT / IMPLEMENTATION).write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(dict(stage="W85", pinStatus="pinned", sourcePins=len(before["sha256"]), runtimeVerified=False)))


if __name__ == "__main__":
    main()
