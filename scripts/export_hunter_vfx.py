#!/usr/bin/env python3
"""Author four animated Generic .bbmodels in NEW Blockbench MCP tabs, export bundled defaults.
Usage: rtk proxy python3 scripts/export_hunter_vfx.py
Requires local Blockbench MCP. No native filesystem access inside the app.
"""
import argparse
import base64
import json
from pathlib import Path
import uuid
from export_hunter_props import Blockbench, write_json

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["destiny_vfx_arc_h13", "destiny_vfx_solar_h13", "destiny_vfx_vortex_h13", "destiny_vfx_smoke_h13"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:3000/bb-mcp")
    bb = Blockbench(parser.parse_args().url)
    for prompt in ["blockbench_native_apis", "blockbench_code_eval_safety"]:
        bb.call("prompts/get", {"name": prompt, "arguments": {}})
    source = (ROOT / "scripts/build_hunter_vfx.js").read_text()
    view = "destiny_vfx_" + uuid.uuid4().hex[:8]
    bb.tool("create_offscreen_view", {"id": view, "width": 1000, "height": 800, "copy_view": "none"})
    models = []
    try:
        for name in NAMES:
            bb.tool("create_project", {"name": name, "format": "free"})
            info = bb.evaluate("const vfxName=" + json.dumps(name) + ";\n" + source)
            bb.tool("create_animation", {"name": info["animation"], "loop": info["animation"] == "loop",
                    "animation_length": info["duration"], "bones": info["bones"]})
            # MCP prefixes animation.; BetterModel's explicit runtime contract is spawn/loop.
            bb.evaluate("Undo.initEdit({animations:[Animation.selected]});Animation.selected.name=" +
                        json.dumps(info["animation"]) + ";Undo.finishEdit(\"Name VFX clip\");true")
            project = bb.evaluate("Codecs.project.compile({raw:true,absolute_paths:false})")
            path = ROOT / f"art/blockbench/vfx/{name}.bbmodel"
            write_json(path, project)
            write_json(ROOT / f"src/main/resources/destiny/vfx/{name}.bbmodel", project)
            bb.evaluate("Project.save_path=" + json.dumps(str(path)) + ";Project.saved=true;true")
            bb.tool("animation_timeline", {"action": "set_time", "time": .15 if info["animation"] == "spawn" else .35})
            result = bb.tool("set_camera_angle", {"view": view, "position": [32, 25, -36], "target": [0, 3, 0],
                             "projection": "orthographic", "zoom": .52})
            img = next(c for c in result["content"] if c["type"] == "image")
            shot = ROOT / f"docs/qa/2026-10-22/vfx_h13_blockbench_{info['variant']}.png"
            shot.write_bytes(base64.b64decode(img["data"]))
            references = {
                "arc": ["https://www.artstation.com/artwork/31lkyE", "https://destiny.wiki.gallery/images/0/0c/Grimoire_Flashbang.jpg"],
                "solar": ["https://destiny.wiki.gallery/images/1/1f/Incendiary_Grenade.jpg"],
                "vortex": ["https://destiny.wiki.gallery/images/f/ff/Vortex_Grenade.jpg"],
                "smoke": []
            }
            models.append({"design_status": "provisional_not_destiny_verified" if info["variant"] == "smoke" else "reference_based_lowpoly_adaptation",
                          "visual_reference_urls": references[info["variant"]], "name": name, "cubes": info["cubes"], "render_bones": info["renderBones"],
                          "animation": info["animation"], "clip_seconds": info["duration"], "source": str(path.relative_to(ROOT)),
                          "preview": shot.name})
            print(name, info["cubes"], "cubes", info["renderBones"], "render bones", flush=True)
    finally:
        try:
            bb.tool("delete_offscreen_view", {"view": view})
        except RuntimeError as e:
            print("Preview cleanup warning:", e)
    write_json(ROOT / "art/blockbench/vfx/manifest.json", {"revision": "H13", "authoring": "Blockbench5.1.4/MCP1.10.1",
               "reference_document": "docs/design/15_헌터_VFX_레퍼런스.md", "original_game_assets_used": False,
               "rendering": "BetterModel animated item displays; full-bright geometry, not additive volumetric shader",
               "models": models})


if __name__ == "__main__":
    main()
