#!/usr/bin/env python3
"""H15 original Hunter super props. New BB tabs, native Undo/codecs, no OS API eval.

rtk proxy python3 -B scripts/export_hunter_supers.py
Uses localhost Blockbench MCP. Does not run Gradle or edit runtime Java.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("arc_staff", "golden_gun", "shadow_bow", "shadow_arrow")
ART = ROOT / "art/blockbench/supers"
ASSETS = ROOT / "src/main/resources/assets/destiny"
DISPLAYS = {
    "arc_staff": {"gui": {"rotation": [0, 0, -35], "scale": [.6, .6, .6]},
                  "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [1, 1, 1]}},
    "golden_gun": {"gui": {"rotation": [20, 135, -10], "scale": [1.2, 1.2, 1.2]},
                   "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [1, 1, 1]}},
    "shadow_bow": {"gui": {"rotation": [0, 20, -20], "scale": [.8, .8, .8]},
                   "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [1, 1, 1]}},
    "shadow_arrow": {"gui": {"rotation": [30, 135, 0], "scale": [1, 1, 1]},
                     "thirdperson_righthand": {"rotation": [0, 0, 0], "scale": [1, 1, 1]},
                     "fixed": {"rotation": [0, 0, 0], "scale": [1, 1, 1]}}
}


class Blockbench:
    def __init__(self, url):
        self.url, self.sid = url, None
        self.call("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "destiny-h15-supers", "version": "1.0"}})

    def call(self, method, params):
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.sid:
            headers["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(self.url, json.dumps({"jsonrpc": "2.0", "id": 1,
                                    "method": method, "params": params}).encode(), headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            self.sid = response.headers.get("mcp-session-id", self.sid)
            data = json.load(response)
        if "error" in data or data.get("result", {}).get("isError"):
            raise RuntimeError(data)
        return data["result"]

    def tool(self, name, args=None):
        return self.call("tools/call", {"name": name, "arguments": args or {}})

    def evaluate(self, code):
        # Only strip whole-line comments: URLs/string values must remain intact.
        code = re.sub(r"(?m)^\s*//[^\n]*", "", code)
        result = self.tool("risky_eval", {"code": code})
        return json.loads(next(c["text"] for c in result["content"] if c["type"] == "text"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def select_project(project_id):
    return ("const target=ModelProject.all.find(p=>p.uuid===" + json.dumps(project_id) + ");"
            "if(!target)throw new Error('H15 project missing');target.select();"
            "if(Project.uuid!==target.uuid)throw new Error('H15 UUID mismatch');")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:3000/bb-mcp")
    parser.add_argument("--models", nargs="+", choices=NAMES, default=NAMES)
    parser.add_argument("--empty-project", help="UUID of one newly created EMPTY H15 tab (one model only)")
    options = parser.parse_args()
    if options.empty_project and len(options.models) != 1:
        parser.error("--empty-project requires exactly one --models name")
    bb = Blockbench(options.url)
    source = re.sub(r"(?m)^\s*//[^\n]*", "", (ROOT / "scripts/build_hunter_supers.js").read_text())
    preview = "h15_supers_" + uuid.uuid4().hex[:10]
    bb.tool("create_offscreen_view", {"id": preview, "width": 1100, "height": 1100,
                                     "antialias": True, "copy_view": "none"})
    manifest_path = ART / "manifest.json"
    models = {e["name"]: e for e in json.loads(manifest_path.read_text())["models"]} if manifest_path.exists() else {}
    try:
        for name in options.models:
            if options.empty_project:
                pid = options.empty_project
            else:
                created = bb.tool("create_project", {"name": "H15_super_" + name, "format": "java_block"})
                link = next(c["uri"] for c in created["content"] if c["type"] == "resource_link")
                pid = link.rsplit("/", 1)[1].removesuffix(".bbmodel")
            # Selecting by UUID, authoring and native compilation are ONE synchronous call.
            # No interleaving with other agents' BB tabs is possible within this transaction.
            code = ("(()=>{" + select_project(pid) + "const superName=" + json.dumps(name) + ";"
                    "const superProjectId=" + json.dumps(pid) + ";const superDisplay=" + json.dumps(DISPLAYS[name]) + ";"
                    "const info=" + source + ";"
                    "if(Project.uuid!==superProjectId)throw new Error('Export UUID mismatch');"
                    "return {info,model:Codecs.java_block.compile({raw:true}),"
                    "project:Codecs.project.compile({raw:true,absolute_paths:false}),texture:Texture.all[0].getDataURL()};})()")
            payload = bb.evaluate(code)
            model, project, info = payload["model"], payload["project"], payload["info"]
            if info["project"] != pid:
                raise RuntimeError("Exported another agent's project")
            write_json(ASSETS / f"models/item/{name}.json", model)
            item_path = ASSETS / f"items/{name}.json"
            item = {"model": {"type": "minecraft:model", "model": f"destiny:item/{name}"}}
            if not item_path.exists() or json.loads(item_path.read_text()) != item:
                write_json(item_path, item)
            write_json(ART / f"{name}.bbmodel", project)
            texture = base64.b64decode(payload["texture"].split(",", 1)[1])
            texture_path = ASSETS / f"textures/item/supers/{name}.png"
            texture_path.parent.mkdir(parents=True, exist_ok=True)
            texture_path.write_bytes(texture)
            # Camera setup changes only our private view. Capture explicitly selects UUID.
            angles = [([26, 17, 28], .43), ([0, 8, 40], .43)]
            if name == "golden_gun":
                angles = [([29, 19, 27], 1.55), ([40, 8, 0], 1.55)]
            elif name == "shadow_bow":
                angles = [([20, 15, 40], .84), ([0, 8, 40], .84)]
            elif name == "shadow_arrow":
                angles = [([24, 24, -28], 1.7), ([0, 40, 0], 1.7)]
            screenshots = []
            for suffix, (position, zoom) in zip(("hero", "profile"), angles):
                bb.tool("set_camera_angle", {"view": preview, "position": position, "target": [0, 8, 0],
                                            "projection": "orthographic", "zoom": zoom})
                shot = bb.tool("capture_screenshot", {"project": pid, "view": preview})
                data = next(c["data"] for c in shot["content"] if c["type"] == "image")
                path = ROOT / f"docs/qa/2026-10-22/supers_h15_{name}_{suffix}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(base64.b64decode(data))
                screenshots.append(str(path.relative_to(ROOT)))
            bb.evaluate("(()=>{" + select_project(pid) + "Project.save_path=" + json.dumps(str(ART / f"{name}.bbmodel"))
                        + ";Project.saved=true;return Project.uuid;})()")
            low = [min(c["from"][axis] for c in model["elements"]) for axis in range(3)]
            high = [max(c["to"][axis] for c in model["elements"]) for axis in range(3)]
            info.update(source=f"art/blockbench/supers/{name}.bbmodel", model=f"destiny:item/{name}",
                        item=f"destiny:{name}", screenshots=screenshots, bounds={"from": low, "to": high},
                        dimensions=[round(b-a, 5) for a, b in zip(low, high)],
                        texture_size=[256, 128], texture_sha256=hashlib.sha256(texture).hexdigest(),
                        design_status="original_reference_reconstruction", forward="-Z" if name == "shadow_arrow" else None,
                        display_baseline=DISPLAYS[name])
            models[name] = info
            print(name, info["cubes"], "cubes", info["triangles"], "triangles", "UUID", pid, flush=True)
            write_json(manifest_path, {"revision": "H15", "authoring": "Blockbench 5.1.4 + MCP 1.10.1; native Undo and codecs",
                       "provenance": "Original cuboid reconstruction and hand/procedural atlas; no game mesh or texture extraction. Bungie owns reference designs.",
                       "references": "art/blockbench/supers/references/manifest.json", "models": [models[n] for n in NAMES if n in models]})
    finally:
        try:
            bb.tool("delete_offscreen_view", {"view": preview})
        except RuntimeError:
            print("Blockbench preview disposal warning; exported assets preserved.")


if __name__ == "__main__":
    main()
