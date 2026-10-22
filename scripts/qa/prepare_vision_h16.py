#!/usr/bin/env python3
"""Create a disposable 26.3 Vision snapshot. Never edits the original project/options.

Adds read-only FPS/entity diagnostics to /state, and launch properties for a second
offline account/run directory. Uses the installed vision client, not a replacement
renderer. Requires a fresh destination. No server authority/input is added.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("destination", type=Path)
    p.add_argument("--source", type=Path, default=Path("/Users/qf/IdeaProjects/copper-golem-vision-client-26.3"))
    a = p.parse_args()
    a.destination.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name in ("src", "gradle", "gradlew", "gradlew.bat", "build.gradle", "settings.gradle", "gradle.properties"):
        source = a.source / name
        if source.is_dir():
            shutil.copytree(source, a.destination / name)
        else:
            shutil.copy2(source, a.destination / name)
    for source in sorted((a.source / "src").rglob("*")):
        if source.is_file():
            hashes[str(source.relative_to(a.source))] = hashlib.sha256(source.read_bytes()).hexdigest()
    build = a.destination / "build.gradle"
    text = build.read_text().replace("runDir 'run-26.3'", "runDir providers.gradleProperty('qaRunDir').getOrElse('run-26.3')")
    text = text.replace("programArgs '--username', 'MinigameQA'", "programArgs '--username', providers.gradleProperty('qaUsername').getOrElse('MinigameQA')")
    build.write_text(text)
    aux = a.destination / "src/main/java/com/coppergolem/visionclient/ClientAuxControl.java"
    text = aux.read_text()
    needle = '        out.append("}");\n        return out.toString();'
    assert text.count(needle) == 1
    extra = '''        out.append(",\\"fps\\":").append(mc.getFps());
        out.append(",\\"frameTimeNsSnapshot\\":").append(mc.getFrameTimeNs());
        if (mc.level != null) {
            com.google.gson.JsonArray entities = new com.google.gson.JsonArray();
            for (net.minecraft.world.entity.Entity e : mc.level.entitiesForRendering()) {
                com.google.gson.JsonObject row = new com.google.gson.JsonObject();
                row.addProperty("id", e.getId());
                row.addProperty("type", net.minecraft.core.registries.BuiltInRegistries.ENTITY_TYPE.getKey(e.getType()).toString());
                row.addProperty("x", e.getX()); row.addProperty("y", e.getY()); row.addProperty("z", e.getZ());
                entities.add(row);
            }
            out.append(",\\"loadedEntities\\":").append(entities);
        }
'''
    aux.write_text(text.replace(needle, extra + needle))
    # Only isolated new options files. The user's original options are read, never written.
    base = (a.source / "run-26.3/options.txt").read_text()
    overrides = {"enableVsync": "false", "pauseOnLostFocus": "false", "maxFps": "120",
                 "renderDistance": "10", "simulationDistance": "10", "inactivityFpsLimit": '"minimized"'}
    lines = [line for line in base.splitlines() if line.partition(":")[0] not in overrides]
    for key, value in overrides.items():
        lines.append(f"{key}:{value}")
    for role in ("caster", "observer"):
        run = a.destination / f"run-{role}"
        run.mkdir()
        (run / "options.txt").write_text("\n".join(lines) + "\n")
    (a.destination / "h16-source-manifest.json").write_text(json.dumps({"source": str(a.source), "original_source_sha256": hashes,
        "added_metrics": ["Minecraft.getFps", "Minecraft.getFrameTimeNs snapshot (not percentile)", "loaded client entity list"],
        "options_original_sha256": hashlib.sha256((a.source / "run-26.3/options.txt").read_bytes()).hexdigest()}, indent=2) + "\n")
    print(a.destination)


if __name__ == "__main__":
    main()
