#!/usr/bin/env python3
"""Create NEW Blockbench Generic projects and export versioned ultimate VFX via native MCP codec."""
import argparse
import base64
import json
import uuid
from pathlib import Path
from export_hunter_props import Blockbench, write_json
ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ["arc_sweep", "solar_muzzle", "solar_impact", "void_anchor"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--url",default="http://localhost:3000/bb-mcp")
    p.add_argument("--models",nargs="+",choices=VARIANTS,default=VARIANTS)
    args=p.parse_args(); bb=Blockbench(args.url)
    for prompt in ["blockbench_native_apis","blockbench_code_eval_safety"]:
        bb.call("prompts/get",{"name":prompt,"arguments":{}})
    view="super_vfx_"+uuid.uuid4().hex[:8]
    bb.tool("create_offscreen_view",{"id":view,"width":1000,"height":800,"copy_view":"none"})
    models=[]
    try:
        for v in args.models:
            name="destiny_super_"+v+"_h15"
            created=bb.tool("create_project",{"name":name,"format":"free"})
            uid=next(c["uri"].split("/")[-1].removesuffix(".bbmodel") for c in created["content"] if c["type"]=="resource_link")
            select="ModelProject.all.find(p=>p.uuid==="+json.dumps(uid)+").select();"
            info=bb.evaluate(select+"const superVfxName="+json.dumps(v)+";"+(ROOT/"scripts/build_hunter_super_vfx.js").read_text())
            # Reselect before each app operation, keeping other artists new tabs intact.
            bb.evaluate(select+"true")
            bb.tool("create_animation",{"name":info["animation"],"loop":info["animation"]=="loop","animation_length":info["duration"],"bones":info["bones"]})
            bb.evaluate(select+"Undo.initEdit({animations:[Animation.selected]});Animation.selected.name="+json.dumps(info["animation"])+";Undo.finishEdit(\"Name ultimate VFX clip\");true")
            model=bb.evaluate(select+"Codecs.project.compile({raw:true,absolute_paths:false})")
            path=ROOT/f"art/blockbench/vfx/{name}.bbmodel"
            write_json(path,model);write_json(ROOT/f"src/main/resources/destiny/vfx/{name}.bbmodel",model)
            bb.evaluate(select+"Project.save_path="+json.dumps(str(path))+";Project.saved=true;true")
            bb.tool("animation_timeline",{"action":"set_time","time":.15 if v!="void_anchor" else .3})
            shot=bb.tool("set_camera_angle",{"view":view,"position":[28,24,-32],"target":[0,1,5],"projection":"orthographic","zoom":.65})
            image=next(c for c in shot["content"] if c["type"]=="image")
            out=ROOT/f"docs/qa/2026-10-22/super_h15_blockbench_{v}.png"
            out.write_bytes(base64.b64decode(image["data"]))
            models.append({k:info[k] for k in ["name","variant","triangles","meshes","renderBones","duration","animation"]})
            print(models[-1],flush=True)
    finally:
        try:bb.tool("delete_offscreen_view",{"view":view})
        except RuntimeError as e:print("Preview disposal warning:",e)
    write_json(ROOT/"art/blockbench/vfx/manifest-super-h15.json",{"revision":"H15","original_game_assets_used":False,"rendering":"BetterModel fullbright triangulated meshes, no additive or bloom", "models":models})
if __name__=="__main__":main()
