#!/usr/bin/env python3
"""Read-only W86 source/JAR/pack verification; never builds or launches.

--audit is a preliminary stdout-only inventory, usable while workers are active.
Full verification needs parent-finalized pins and pack/config/historical cache.
The original W42 chain, all assets, compiled main classes and server resources
are checked by the unchanged W84 archive_verification implementation.
--variant pinned requires exact headless pack/config hashes and FOV=false;
--variant native retains source/JAR pins but reports separate FOV=true pack/config
hashes. Neither variant certifies rendering, damage-HUD tuning or gameplay.
Only an explicit --out in full mode writes a requested provenance report.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from pin_runtime_w86 import (
    ROOT, IMPLEMENTATION, ASSETS, PREVIOUS_PACK, PREVIOUS_PINS, PREVIOUS_ASSETS,
    file_sha, read, require, source_snapshot, run_components, summary,
)
from verify_runtime_w84 import archive_verification, variant_artifacts


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--audit", action="store_true", help="Preliminary source/asset audit only; no current JAR/pack claim or report-file write")
    result.add_argument("--components", action="store_true", help="During --audit also run W86 HUD --verify; always run in full mode")
    result.add_argument("--python", type=Path, default=Path(sys.executable), help="Python with Pillow for HUD --verify")
    result.add_argument("--variant", choices=("pinned", "native"), default="pinned",
                        help="pinned: exact headless pack/config hashes; native: same pinned source/JAR, separate FOV=true pack/config")
    result.add_argument("--previous-pack", type=Path, default=PREVIOUS_PACK, help="Hash-pinned archived W85 headless pack; sounds162 remain unchanged")
    result.add_argument("--jar", type=Path, default=ROOT / "build/libs/destiny-guardians-0.1.0+26.3.jar")
    result.add_argument("--server-pack", type=Path, help="Existing current generated headless/server pack")
    result.add_argument("--shader-config", type=Path, help="Config used to generate the current pack")
    result.add_argument("--baseline-cache", type=Path, help="Historical W40 downloaded cache, as required by the retained W84/W42 chain")
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
        require(manifest["pinStatus"] == "pinned", "W86 implementation is pending; parent must finalize only after workers/gates settle")
    before = source_snapshot(args.previous_pack, require_ready=not args.audit)
    if args.audit:
        report = summary(before)
        if args.components and not before["gaps"]:
            report["componentVerifiers"] = run_components(args.python)
            require(source_snapshot(args.previous_pack, require_ready=not args.audit) == before, "Sources changed during preliminary audit")
        elif args.components:
            report["componentVerifiersSkipped"] = "Pending deliverables; no component verification claim"
        print(json.dumps(report, indent=2))
        return
    require(manifest["stage"] == "W86" and manifest["baseline"] == "W85", "Wrong finalized manifest stage")
    require(manifest["sha256"] == before["sha256"], "Final source pin inventory/hash differs")
    require(manifest["externalSha256"] == before["externalSha256"], "External source pins differ")
    require(manifest["previousPinCount"] == PREVIOUS_PINS and manifest["previousClientAssetCount"] == PREVIOUS_ASSETS, "Historical pin coverage differs")
    require(manifest["newClientAssetPaths"] == before["newClientAssetPaths"], "New asset coverage differs")
    require(manifest["newClientAssets"] == len(before["newClientAssetPaths"]), "New asset count differs")
    require(manifest["soundPreservation"] == before["soundPreservation"], "Old/new sound proof differs")
    require(manifest["provenance"] == before["provenance"], "Research provenance proof differs")
    require(manifest["immutablePreviousPins"] == before["immutablePreviousPins"], "Old art/scripts/resources immutable coverage differs")
    require(manifest["preservationPolicy"] == before["preservationPolicy"], "Resource preservation exceptions/coverage differ")
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
        require(not any(output.is_relative_to(ROOT / folder) for folder in ("src", "scripts", "art")),
                "--out must not alter inventoried source/art/script trees")
    checks = run_components(args.python)
    report = archive_verification(args.jar.resolve(), args.server_pack.resolve(), args.shader_config.resolve(),
                                  args.baseline_cache.resolve(), args.client_cache.resolve() if args.client_cache else None, before)
    require(source_snapshot(args.previous_pack, require_ready=not args.audit) == before, "Source inventory changed during verification")
    require(all(file_sha(paths[key]) == digest for key, digest in artifact_hashes.items()), "Artifacts changed during verification")
    report.update(stage="W86", sourcePins=len(before["sha256"]), previousPins=PREVIOUS_PINS,
                  previousClientAssets=PREVIOUS_ASSETS, oldClientAssetBytesPreserved=PREVIOUS_ASSETS,
                  soundPreservation=before["soundPreservation"], newClientAssets=manifest["newClientAssets"],
                  provenance=before["provenance"], inventory=before["inventory"], immutablePreviousPins=before["immutablePreviousPins"],
                  preservationPolicy=before["preservationPolicy"],
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
        print(json.dumps(dict(stage="W86", variant=args.variant, sourcePins=report["sourcePins"], allClientAssets=len(report["allClientAssets"]),
                              serverResources=len(report["allServerResources"]), mainClasses=len(report["classes"]),
                              jarSha256=report["jar"]["sha256"], report=str(args.out), nativeClientRenderingCertified=False)))
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
