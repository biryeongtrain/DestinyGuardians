#!/usr/bin/env python3
"""Read-only W84 source/JAR/generated-pack verifier; never builds or launches.

--audit checks only current source, the old 6467 assets and W83 sound definitions;
it works before final pinning and makes no JAR/runtime claim. Full verification
requires a finalized implementation.json and caller-supplied pack/config/cache.
--variant native retains source/JAR pins and verifies a separate FOV-enabled
pack/config, without changing the headless manifest.
Only --out writes a requested report; default output is stdout. W84 model/audio/
HUD/runtime-extraction --verify are used, never the old event-count-specific scripts.
No class or server-resource count is hardcoded; inventories must match in full.
"""
import argparse
import json
from pathlib import Path
import sys
import zipfile

from pin_runtime_w84 import (
    ROOT, BASELINE, IMPLEMENTATION, ASSETS, PREVIOUS_PACK, file_sha, read, require,
    source_snapshot, run_components, summary, sha,
)


def archive_verification(jar_path, pack_path, shader_config, baseline_cache, client_cache, snapshot):
    require(__debug__, "Run without -O: the retained W42 provenance chain uses assertions")
    from verify_runtime_w42 import verify
    # Retain the W83 provenance chain: historical W40/41/42 resources, compiled
    # main-class bytes, baseline downloaded cache and 542 preserved weapon assets.
    report = verify(jar_path, pack_path, baseline_cache, client_cache)
    shader = read(shader_config)
    enabled = shader.get("dynamic-fov-shader", False)
    require(type(enabled) is bool, "dynamic-fov-shader must be a boolean")
    shared = {"assets/destiny/sounds.json", "assets/destiny/lang/en_us.json", "assets/destiny/lang/ko_kr.json"}
    w76 = read(ROOT / "src/main/resources/destiny/hud/w76-vanilla.json")
    shared.update("assets/minecraft/lang/" + locale + ".json" for locale in w76["locales"])
    records = []
    server = []
    with zipfile.ZipFile(jar_path) as jar, zipfile.ZipFile(pack_path) as pack:
        require(len(jar.namelist()) == len(set(jar.namelist())), "Duplicate JAR entries")
        require(len(pack.namelist()) == len(set(pack.namelist())), "Duplicate pack entries")
        for path, digest in snapshot["clientAssets"].items():
            source = ROOT / path
            name = source.relative_to(ROOT / "src/main/resources").as_posix()
            raw = source.read_bytes()
            require(sha(raw) == digest, "Source changed during archive audit: " + path)
            require(jar.read(name) == raw, "JAR/source bytes differ: " + name)
            actual = pack.read(name)
            if name in shared:
                require(json.loads(actual) == json.loads(raw), "Pack/source JSON differs: " + name)
            else:
                require(actual == raw, "Pack/source bytes differ: " + name)
            records.append(dict(path=name, sourceJarSha256=digest, packSha256=sha(actual), jsonReserialized=name in shared))
        for source in sorted((ROOT / "src/main/resources").rglob("*")):
            if not source.is_file() or source.is_relative_to(ROOT / ASSETS):
                continue
            name = source.relative_to(ROOT / "src/main/resources").as_posix()
            if name == "fabric.mod.json":
                continue
            raw = source.read_bytes()
            require(jar.read(name) == raw, "JAR/server-resource mismatch: " + name)
            server.append(dict(path=name, sha256=sha(raw)))
        fabric = json.loads(jar.read("fabric.mod.json"))
        # processResources expands exactly these three pinned Gradle properties.
        properties=dict(line.strip().split("=",1) for line in (ROOT/"gradle.properties").read_text().splitlines()
                        if "=" in line and not line.lstrip().startswith("#"))
        replacements={"version":properties["mod_version"]+"+"+properties["minecraft_version"],
                      "minecraft_version":properties["minecraft_version"],"loader_version":properties["loader_version"]}
        raw=(ROOT/"src/main/resources/fabric.mod.json").read_text()
        for key,value in replacements.items(): raw=raw.replace("${"+key+"}",value)
        original=json.loads(raw)
        require(fabric == original and fabric["depends"]["minecraft"] == "26.3", "JAR fabric metadata differs")
        projection = "assets/minecraft/shaders/include/projection.glsl"
        require((projection in pack.namelist()) == enabled, "Pack dynamic-FOV configuration mismatch")
        if enabled:
            require(pack.read(projection) == (ROOT / "libs/minigame-lib/src/main/resources/shaders/optional/projection.glsl").read_bytes(),
                    "Optional projection shader differs")
        compiled = {p.relative_to(ROOT / "build/classes/java/main").as_posix()
                    for p in (ROOT / "build/classes/java/main/kim/biryeong/destiny").rglob("*.class")}
        packaged = {name for name in jar.namelist() if name.startswith("kim/biryeong/destiny/") and name.endswith(".class")}
        require(compiled and packaged == compiled, "Missing/stale main classes in JAR")
        source_classes = {Path(path).relative_to("src/main/java").with_suffix(".class").as_posix()
                          for path in snapshot["sha256"] if path.startswith("src/main/java/") and path.endswith(".java")
                          and Path(path).name != "package-info.java"}  # Documentation-only packages need not emit a class.
        require(source_classes <= packaged, "Source main types missing from JAR: " + ", ".join(sorted(source_classes-packaged)))
        jar_assets = {name for name in jar.namelist() if name.startswith("assets/") and not name.endswith("/")}
        source_assets = {Path(path).relative_to("src/main/resources").as_posix() for path in snapshot["clientAssets"]}
        require(jar_assets == source_assets, "JAR asset inventory differs from source: " + str(dict(
            extra=sorted(jar_assets-source_assets), missing=sorted(source_assets-jar_assets))))
    report.update(allClientAssets=records, allServerResources=server, dynamicFovConfigured=enabled,
                  fabricMetadataSourceJar=True, exactMainClassInventory=True,
                  sourceMainTypesCovered=len(source_classes), exactJarAssetInventory=True)
    return report


def variant_artifacts(manifest, variant, paths):
    """Both variants use the pinned JAR. Pack/config identities are distinct."""
    require(variant in ("pinned", "native"), "Unknown verification variant")
    actual = {key: file_sha(path) for key, path in paths.items()}
    require(actual["jarSha256"] == manifest["jarSha256"], "Pinned JAR differs")
    require(manifest["pinnedVariant"] == "headless" and manifest["headlessDynamicFov"] is False,
            "Manifest must retain the headless baseline")
    shader = read(paths["shaderConfigSha256"])
    enabled = shader.get("dynamic-fov-shader", False)
    require(type(enabled) is bool, "dynamic-fov-shader must be a boolean")
    if variant == "pinned":
        require(not enabled, "Pinned headless verification requires dynamic-FOV=false")
        require(all(manifest[key] == digest for key, digest in actual.items()), "Pinned JAR/pack/config differs")
    else:
        require(enabled, "Native variant requires dynamic-FOV=true")
    return actual


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--audit", action="store_true", help="Preliminary source/asset audit only; no current JAR/pack claim or report-file write")
    result.add_argument("--components", action="store_true", help="During --audit also run W84 model/audio/HUD/runtime-extraction --verify; always run in full mode")
    result.add_argument("--python", type=Path, default=Path(sys.executable), help="Python with Pillow for HUD --verify")
    result.add_argument("--model-source", type=Path, default=Path.home() / "Downloads/izanagi.bbmodel")
    result.add_argument("--variant", choices=("pinned", "native"), default="pinned",
                        help="pinned: exact headless pack/config hashes; native: same pinned source/JAR, separate FOV=true pack/config")
    result.add_argument("--previous-pack", type=Path, default=PREVIOUS_PACK, help="Hash-pinned W83 native pack for 156 sound definitions")
    result.add_argument("--jar", type=Path, default=ROOT / "build/libs/destiny-guardians-0.1.0+26.3.jar")
    result.add_argument("--server-pack", type=Path, help="Existing current generated headless/server pack")
    result.add_argument("--shader-config", type=Path, help="Config used to generate the current pack")
    result.add_argument("--baseline-cache", type=Path, help="Historical W40 downloaded cache, as required by W83/W42 verification")
    result.add_argument("--client-cache", type=Path, help="Optional current downloaded cache; must byte-match current server pack")
    result.add_argument("--out", type=Path, help="Full mode only: explicitly write provenance report; omitted means stdout only")
    return result


def main():
    args = parser().parse_args()
    require(not (args.audit and args.out), "--audit is stdout-only; omit --out")
    if not args.audit:
        require(args.server_pack and args.shader_config and args.baseline_cache,
                "Full verification requires --server-pack, --shader-config and --baseline-cache (or use --audit)")
        manifest = read(ROOT / IMPLEMENTATION)
        require(manifest["pinStatus"] == "pinned", "W84 implementation is pending; parent must finalize only after workers/gates settle")
    before = source_snapshot(args.previous_pack, args.model_source)
    if args.audit:
        report = summary(before)
        if args.components:
            report["componentVerifiers"] = run_components(args.python, args.model_source)
            require(source_snapshot(args.previous_pack, args.model_source) == before, "Sources changed during preliminary audit")
        print(json.dumps(report, indent=2))
        return
    require(manifest["stage"] == "W84" and manifest["baseline"] == "W83", "Wrong finalized manifest stage")
    require(manifest["sha256"] == before["sha256"], "Final source pin inventory/hash differs")
    require(manifest["externalSha256"] == before["externalSha256"], "External source pins differ")
    require(manifest["previousPinCount"] == 1173 and manifest["previousClientAssetCount"] == 6467, "Historical pin coverage differs")
    require(manifest["newClientAssetPaths"] == before["newClientAssetPaths"], "New asset coverage differs")
    require(manifest["newClientAssets"] == len(before["newClientAssetPaths"]), "New asset count differs")
    require(manifest["soundPreservation"] == before["soundPreservation"], "Old/new sound proof differs")
    require(manifest["provenance"] == before["provenance"], "Research provenance proof differs")
    require(manifest["immutableW83Pins"] == before["immutablePreviousPins"], "W83 immutable coverage differs")
    require(manifest["inventory"] == before["inventory"], "Source/resource inventory differs")
    paths = {"jarSha256": args.jar.resolve(), "serverPackSha256": args.server_pack.resolve(),
             "shaderConfigSha256": args.shader_config.resolve()}
    artifact_hashes = variant_artifacts(manifest, args.variant, paths)
    if args.out:
        output = args.out.resolve()
        protected = {(ROOT/p).resolve() for p in before["sha256"]}
        protected.update(Path(p).resolve() for p in before["externalSha256"])
        protected.update(paths.values())
        protected.update({(ROOT/IMPLEMENTATION).resolve(), args.previous_pack.resolve(), args.baseline_cache.resolve()})
        if args.client_cache:
            protected.add(args.client_cache.resolve())
        require(output not in protected, "--out cannot overwrite pinned sources, implementation or artifact inputs")
        require(not output.is_relative_to(ROOT / ASSETS), "--out cannot create a client asset")
    checks = run_components(args.python, args.model_source)
    report = archive_verification(args.jar.resolve(), args.server_pack.resolve(), args.shader_config.resolve(),
                                  args.baseline_cache.resolve(), args.client_cache.resolve() if args.client_cache else None, before)
    require(source_snapshot(args.previous_pack, args.model_source) == before, "Source inventory changed during verification")
    require(all(file_sha(paths[key]) == digest for key, digest in artifact_hashes.items()), "Artifacts changed during verification")
    report.update(stage="W84", sourcePins=len(before["sha256"]), previousPins=1173,
                  previousClientAssets=6467, oldClientAssetBytesPreserved=6466,
                  soundPreservation=before["soundPreservation"], newClientAssets=manifest["newClientAssets"],
                  provenance=before["provenance"], inventory=before["inventory"], immutableW83Pins=before["immutablePreviousPins"],
                  componentVerifiers=checks, sourceJarPackVerified=True, wholeGoalAchieved=False,
                  nativeClientRenderingCertified=False, gameplayCertified=False, acousticCertified=False,
                  evidenceBoundary="Read-only source/JAR/generated-pack provenance and deterministic component checks; no native framebuffer, gameplay or acoustic certification.")
    report["variant"] = args.variant
    report["pinnedHeadless"] = dict(serverPackSha256=manifest["serverPackSha256"],
                                     shaderConfigSha256=manifest["shaderConfigSha256"], dynamicFovConfigured=False)
    actual = dict(serverPackSha256=artifact_hashes["serverPackSha256"],
                  shaderConfigSha256=artifact_hashes["shaderConfigSha256"],
                  dynamicFovConfigured=report["dynamicFovConfigured"], samePinnedSourceAndJar=True)
    report["actualNative" if args.variant == "native" else "actualPinnedHeadless"] = actual
    report["packConfigIdentityWithPinnedHeadlessRequired"] = args.variant == "pinned"
    if args.out:
        args.out.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(dict(stage="W84", variant=args.variant, sourcePins=report["sourcePins"], allClientAssets=len(report["allClientAssets"]),
                              serverResources=len(report["allServerResources"]), mainClasses=len(report["classes"]),
                              jarSha256=report["jar"]["sha256"], report=str(args.out), nativeClientRenderingCertified=False)))
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
