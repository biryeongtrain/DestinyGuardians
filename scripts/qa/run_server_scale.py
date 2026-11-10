#!/usr/bin/env python3
"""Opt-in native TCP GameTest cohort; never targets an existing game server."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile


def bounded(low: int, high: int):
    def parse(value: str) -> int:
        result = int(value)
        if not low <= result <= high:
            raise argparse.ArgumentTypeError(f"expected {low}..{high}")
        return result
    return parse


def groovy(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="new empty directory or this script's previous owned directory")
    parser.add_argument("--scenario", choices=("shared", "instances"), default="shared")
    parser.add_argument("--players", type=bounded(1, 40))
    parser.add_argument("--phase-ticks", type=bounded(100, 6000), default=600)
    parser.add_argument("--server-view", type=bounded(2, 32), default=32)
    parser.add_argument("--client-view", type=bounded(2, 32), default=32)
    parser.add_argument("--port", type=bounded(1024, 65535), default=25640)
    parser.add_argument("--jfr", action="store_true")
    parser.add_argument("--lifecycle", action="store_true", help="instances only: two admission/exit cycles, native reconnect and unchanged120s expiry")
    args = parser.parse_args()
    if args.players is None:
        args.players = 40 if args.scenario == "instances" else 30
    if args.scenario == "instances" and args.players != 40:
        parser.error("the production instance cohort currently requires exactly40 peers")
    if args.scenario == "instances" and args.jfr:
        parser.error("--jfr currently applies to the shared scenario; instance results include tick/GC/transport counters")
    if args.lifecycle and args.scenario != "instances":
        parser.error("--lifecycle requires --scenario instances")
    repo = Path(__file__).resolve().parents[2]
    run = args.run_dir.expanduser().resolve()
    marker = run / ".destiny-scale-owned.json"
    if run.exists() and any(run.iterdir()) and not marker.is_file():
        parser.error("nonempty run directory has no ownership marker; choose a new dedicated directory")
    if marker.exists() and json.loads(marker.read_text()).get("schema") != 1:
        parser.error("unsupported ownership marker")
    run.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"schema": 1, "purpose": "isolated Destiny native TCP GameTest"}) + "\n")
    addon = run / "scale-qa.jar"
    with zipfile.ZipFile(addon, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("fabric.mod.json", json.dumps({
            "schemaVersion": 1, "id": "destiny-scale-qa", "version": "1.0.0",
            "environment": "server", "entrypoints": {"fabric-gametest": [
                "kim.biryeong.destiny.test.ServerScaleInstancesGameTests" if args.scenario == "instances"
                else "kim.biryeong.destiny.test.ServerScaleGameTests"]},
            "depends": {"destiny-test": "*"},
        }))
    output = run / f"scale-{args.scenario}-{args.players}.json"
    properties = {
        "fabric.addMods": str(addon), "fabric-api.gametest.filter": "destiny-scale-qa:*",
        "destiny.gametest.scale.enabled": "true", "destiny.qa": "true",
        "destiny.gametest.scale.clients": str(args.players),
        "destiny.gametest.scale.phaseTicks": str(args.phase_ticks),
        "destiny.gametest.scale.serverViewDistance": str(args.server_view),
        "destiny.gametest.scale.requestedViewDistance": str(args.client_view),
        "destiny.gametest.scale.port": str(args.port),
        "destiny.gametest.scale.output": str(output),
        "destiny.gametest.scale.jfr": str(args.jfr).lower(),
        "destiny.gametest.packTimeoutSeconds": "600",
    }
    if args.scenario == "instances":
        properties.update({
            "destiny.guardianRises": "true",
            "destiny.gametest.scale.instances.enabled": "true",
            "destiny.gametest.scale.instances.lifecycle": str(args.lifecycle).lower(),
            "destiny.gametest.scale.instances.globalSimulation": "6",
            "destiny.gametest.scale.instances.globalView": str(args.server_view),
            "destiny.gametest.scale.instances.port": str(args.port),
            "destiny.gametest.scale.instances.steadyTicks": str(args.phase_ticks),
            "destiny.gametest.scale.instances.output": str(output),
        })
    init = run / "scale.init.gradle"
    init.write_text("gradle.projectsEvaluated {\n"
                    " rootProject.loom.runs.each { run -> if (run.name == 'gameTest') run.runDir " + groovy(str(run)) + " }\n"
                    " rootProject.tasks.named('runGameTest') {\n"
                    "  workingDir " + groovy(str(run)) + "\n  maxHeapSize = '8g'\n" +
                    "".join(f"  systemProperty {groovy(k)}, {groovy(v)}\n" for k, v in properties.items()) +
                    " }\n}\n")
    if os.name == "nt":
        # Invoke the wrapper's Java entry point directly: .bat execution would put
        # otherwise literal directory names through cmd.exe's metacharacter rules.
        java_home = os.environ.get("JAVA_HOME")
        java = str(Path(java_home) / "bin" / "java.exe") if java_home else shutil.which("java")
        if not java or not Path(java).is_file():
            parser.error("Java25 is required; set JAVA_HOME to an existing JDK")
        launch = [java, "-Xms64m", "-Xmx64m", "-classpath", str(repo / "gradle/wrapper/gradle-wrapper.jar"),
                  "org.gradle.wrapper.GradleWrapperMain"]
    else:
        launch = [str(repo / "gradlew")]
    print(f"Owned 8GiB GameTest, loopback port {args.port}; results: {output}", flush=True)
    print("Shares JVM/CPU with peers; excludes renderer, WAN, authentication and pack-download acceptance.", flush=True)
    return subprocess.run([*launch, "runGameTest", "--max-workers=2", "--init-script", str(init)], cwd=repo).returncode


if __name__ == "__main__":
    raise SystemExit(main())
