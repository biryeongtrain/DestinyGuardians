#!/usr/bin/env python3
"""Author and export reference reconstructions / provisional props using the running Blockbench MCP, no native fs eval.

Usage: rtk proxy python3 scripts/export_hunter_props.py [--url http://localhost:3000/bb-mcp]
Creates NEW tabs for selected models (default five); never clears or edits an existing user project.
"""
import argparse
import base64
import json
from pathlib import Path
import re
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["arc_flashbang", "solar_incendiary", "void_vortex", "solar_knife", "void_smoke_bomb"]


class Blockbench:
    def __init__(self, url):
        self.url = url
        self.sid = None
        self.call("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "destiny-props", "version": "1.0"}})

    def call(self, method, params):
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.sid:
            headers["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(self.url, json.dumps({"jsonrpc": "2.0", "id": 1,
                                    "method": method, "params": params}).encode(), headers)
        with urllib.request.urlopen(req, timeout=60) as res:
            self.sid = res.headers.get("mcp-session-id", self.sid)
            data = json.load(res)
        if "error" in data or data.get("result", {}).get("isError"):
            raise RuntimeError(data)
        return data["result"]

    def tool(self, name, args=None):
        return self.call("tools/call", {"name": name, "arguments": args or {}})

    def evaluate(self, code):
        # MCP deliberately rejects comments in executable eval. Authoring source retains them.
        code = re.sub(r"//[^\n]*", "", code)
        result = self.tool("risky_eval", {"code": code})
        return json.loads(next(c["text"] for c in result["content"] if c["type"] == "text"))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--url", default="http://localhost:3000/bb-mcp")
    args.add_argument("--models", nargs="+", choices=NAMES, default=NAMES)
    options = args.parse_args()
    bb = Blockbench(options.url)
    source = (ROOT / "scripts/build_hunter_props.js").read_text()
    preview = "destiny_props_" + uuid.uuid4().hex[:8]
    bb.tool("create_offscreen_view", {"id": preview, "width": 900, "height": 900, "copy_view": "none"})
    manifest_path = ROOT / "art/blockbench/hunter/manifest.json"
    manifest = {m["name"]: m for m in json.loads(manifest_path.read_text())["models"]} if manifest_path.exists() else {}
    try:
        for name in options.models:
            bb.tool("create_project", {"name": "H12_hunter_" + name, "format": "java_block"})
            info = bb.evaluate("const propName=" + json.dumps(name) + ";\n" + source)
            payload = bb.evaluate("({model:Codecs.java_block.compile({raw:true}),"
                                  "project:Codecs.project.compile({raw:true,absolute_paths:false}),"
                                  "texture:Texture.all[0].getDataURL()})")
            model = payload["model"]
            write_json(ROOT / f"src/main/resources/assets/destiny/models/hunter/{name}.json", model)
            write_json(ROOT / f"src/main/resources/assets/destiny/items/hunter/{name}.json",
                       {"model": {"type": "minecraft:model", "model": f"destiny:hunter/{name}"}})
            write_json(ROOT / f"art/blockbench/hunter/{name}.bbmodel", payload["project"])
            tex_path = ROOT / f"src/main/resources/assets/destiny/textures/item/hunter/{name}.png"
            tex_path.parent.mkdir(parents=True, exist_ok=True)
            tex_path.write_bytes(base64.b64decode(payload["texture"].split(",", 1)[1]))
            # Java Block preview offsets X/Z by -8; aim at local [0,8,0].
            shot = bb.tool("set_camera_angle", {"view": preview, "position": [0, 32, 6] if name == "solar_knife" else [25, 21, -30],
                            "target": [0, 8, 0], "projection": "orthographic", "zoom": .85})
            image = next(c for c in shot["content"] if c["type"] == "image")
            shot_path = ROOT / f"docs/qa/2026-10-22/props_h12_blockbench_{name}.png"
            shot_path.write_bytes(base64.b64decode(image["data"]))
            manifest[name] = {"name": name, "cubes": info["cubes"], "texture": info["texture"],
                             "source": f"art/blockbench/hunter/{name}.bbmodel",
                             "format": model.get("format_version"), "screenshot": shot_path.name}
            bb.evaluate("Project.save_path=" + json.dumps(str(ROOT / f"art/blockbench/hunter/{name}.bbmodel")) + ";Project.saved=true;true")
            print(name, info["cubes"], "cubes exported", flush=True)
    finally:
        try:
            bb.tool("delete_offscreen_view", {"view": preview})
        except RuntimeError as exc:
            # MCP 1.10.1 + BB 5.1.4 can throw onContextMenu during native preview disposal.
            print("Preview cleanup warning (exports preserved):", exc)
    sources = {
        "solar_knife": ["https://www.destinypedia.com/Hunter_Knife", "https://destiny.wiki.gallery/images/2/20/Destiny_Hunters_Knife.jpg"],
        "arc_flashbang": ["https://www.destinypedia.com/Flashbang_Grenade", "https://destiny.wiki.gallery/images/0/0a/Flashbang_Grenade.jpg"]
    }
    for name, entry in manifest.items():
        entry["design_status"] = "reference_verified_reconstruction" if name in sources else "provisional_not_destiny_verified"
        entry["visual_reference_urls"] = sources.get(name, [])
        entry["revision"] = "H12" if name in sources else "H11"
    write_json(manifest_path, {"authoring": "Blockbench 5.1.4 + MCP 1.10.1",
               "geometry": "New cuboids and atlas, not original game meshes. Only two designs source-verified; three provisional.",
               "models": [manifest[n] for n in NAMES if n in manifest]})


if __name__ == "__main__":
    main()
