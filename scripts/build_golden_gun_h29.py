#!/usr/bin/env python3
"""Rebuild H29 from the committed colored source derivative; no Blender required."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
SOURCE = ROOT / "art/mesh/supers/h29/golden_gun.mesh.json"


def encode(value):
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def generate():
    cache = Path.home() / ".gradle/caches/modules-2/files-2.1"
    deps = ("io.github.toxicity188/java-mesh/0.0.1", "com.google.code.gson/gson/2.14.0",
            "org.joml/joml/1.10.9", "it.unimi.dsi/fastutil/8.5.18")
    jars = [next((cache / dep).glob("*/*.jar")) for dep in deps]
    cp = os.pathsep.join(map(str, jars))
    java = Path(os.environ["JAVA_HOME"]) / "bin"
    source = json.loads(SOURCE.read_text())
    output = {}
    # Dedicated first-person context: aim view, not inventory preview yaw135.
    display = {
        "firstperson_righthand": {"rotation": [8, -170, 0]},
        "firstperson_lefthand": {"rotation": [8, 170, 0]},
        "thirdperson_righthand": {"translation": [0, 2, 0]},
        "thirdperson_lefthand": {"translation": [0, 2, 0]},
        "gui": {"rotation": [20, 135, -10], "scale": [1.2, 1.2, 1.2]},
    }
    primitive = {
        "ambientocclusion": False, "display": display,
        "textures": {"0": "destiny:item/supers/mesh_triangle_h28",
                     "particle": "destiny:item/supers/mesh_triangle_h28"},
        "elements": [{"from": [-16, 0, 0], "to": [0, 16, 0], "shade": False,
                      "light_emission": 12,
                      "faces": {"north": {"uv": [0, 0, 16, 16], "texture": "#0", "tintindex": 0},
                                "south": {"uv": [16, 0, 0, 16], "texture": "#0", "tintindex": 0}}}]
    }
    output[ASSETS / "models/mesh/h29/golden_gun_triangle.json"] = encode(primitive)
    with tempfile.TemporaryDirectory(prefix="destiny-h29-") as temp:
        subprocess.run([str(java / "javac"), "-cp", cp, "-d", temp,
                        str(ROOT / "scripts/mesh/HunterMeshCompiler.java")], check=True)
        target = Path(temp) / "model.json"
        subprocess.run([str(java / "java"), "-cp", temp + os.pathsep + cp,
                        "HunterMeshCompiler", str(SOURCE), str(target),
                        "destiny:mesh/h29/golden_gun_triangle"], check=True)
        compiled = json.loads(target.read_text())
    output[ASSETS / "items/golden_gun_h29.json"] = encode({"model": compiled})
    output[ASSETS / "models/item/golden_gun_h29.json"] = encode({
        "credit": "Bungie Eyasluna source derivative; see design43 for provenance and limitations",
        "display": copy.deepcopy(display), "elements": []})
    manifest = {
        "model": "golden_gun_h29", "triangles": len(source["triangles"]),
        "mesh_parts": len(compiled["models"]),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "compiler_dependencies": {dep: hashlib.sha256(j.read_bytes()).hexdigest()
                                  for dep, j in zip(deps, jars)},
        "runtime_sha256": {str(p.relative_to(ASSETS)): hashlib.sha256(b).hexdigest()
                           for p, b in output.items()},
        "shared_texture_sha256": hashlib.sha256(
            (ASSETS / "textures/item/supers/mesh_triangle_h28.png").read_bytes()).hexdigest(),
        "source_rights": "Bungie design; original DMR rip not open licensed; see design43",
    }
    output[SOURCE.parent / "manifest.json"] = encode(manifest)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    for path, data in generate().items():
        if args.verify:
            assert path.read_bytes() == data, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        print("verified" if args.verify else "wrote", path.relative_to(ROOT))
