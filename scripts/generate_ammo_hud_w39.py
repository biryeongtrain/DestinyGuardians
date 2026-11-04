#!/usr/bin/env python3
"""Original HUD panel/family silhouettes and rasterized numeric glyphs; no Destiny texture rip.
Requires Pillow and the pinned local Arial Narrow Bold font (font file is not redistributed).
"""
from pathlib import Path
import argparse, hashlib, io, json
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
FONT = Path("/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf")
S = 4
def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
def generate():
    output = {}
    def asset(name, width, height, paint):
        im = Image.new("RGBA", (width*S, height*S))
        d = ImageDraw.Draw(im)
        paint(d, im)
        im = im.resize((width, height), Image.Resampling.LANCZOS)
        stream = io.BytesIO(); im.save(stream, format="PNG")
        output[ASSETS / f"textures/item/hud/{name}.png"] = stream.getvalue()
        model = {"gui_light":"front","textures":{"layer0":f"destiny:item/hud/{name}"},
            "elements":[{"from":[0,0,8],"to":[16,16,8],"faces":{
                f:{"texture":"#layer0","uv":[0,0,16,16],"tintindex":0} for f in ("north","south")}}]}
        output[ASSETS / f"models/gui/hud/{name}.json"] = encode(model)
        output[ASSETS / f"items/gui/hud/{name}.json"] = encode({"model":{
            "type":"minecraft:model","model":f"destiny:gui/hud/{name}",
            "tints":[{"type":"minecraft:custom_model_data","index":0,"default":16777215}]}})
    font = ImageFont.truetype(str(FONT), 61*S)
    for digit in range(10):
        def paint(d, im, text=str(digit)):
            # Tight glyph bounds use the entire quad without invisible font ascender/descender.
            box = d.textbbox((0,0),text,font=font)
            glyph=Image.new("RGBA",(box[2]-box[0],box[3]-box[1]))
            ImageDraw.Draw(glyph).text((-box[0],-box[1]),text,font=font,fill="white")
            glyph.thumbnail((27*S,57*S),Image.Resampling.LANCZOS)
            im.alpha_composite(glyph,((32*S-glyph.width)//2,(64*S-glyph.height)//2))
        asset(f"ammo_digit_{digit}",32,64,paint)
    def panel(d, im):
        d.rectangle((0,0,280*S-1,56*S-1),fill=(22,27,33,145))
        d.line([(1*S,55*S),(279*S,55*S),(279*S,1*S),(1*S,1*S)],fill=(255,255,255,205),width=S)
        d.line([(1*S,1*S),(1*S,55*S)],fill=(255,255,255,90),width=S)
    asset("ammo_panel",280,56,panel)
    families=json.loads((ROOT/"src/main/resources/destiny/weapons/w30.json").read_text())
    for family in sorted({e["family"] for e in families}):
        def silhouette(d, im, f=family):
            def line(points,w=2):d.line([(x*S,y*S) for x,y in points],fill="white",width=w*S,joint="curve")
            def poly(points):d.polygon([(x*S,y*S) for x,y in points],fill="white")
            if f=="glaive":
                line([(4,22),(72,11)],3);poly([(68,4),(92,5),(77,13),(66,14)])
            elif f=="sword":
                poly([(8,23),(15,19),(19,22),(81,4),(90,4),(84,10),(24,27),(23,31),(17,30),(18,25)])
            elif f=="bow":
                line([(19,3),(48,10),(53,16),(48,22),(19,29)],2);line([(19,3),(26,16),(19,29)],1)
                line([(25,16),(87,16)],2);poly([(82,12),(92,16),(82,20)])
            elif f=="hand_cannon":
                poly([(9,7),(75,7),(81,11),(77,18),(42,18),(35,29),(22,29),(27,18),(9,18)])
                line([(40,20),(51,20),(54,16)],2)
            elif f in ("rocket_launcher","grenade_launcher","heavy_grenade_launcher"):
                poly([(7,9),(79,9),(87,12),(87,20),(79,23),(7,23)])
                poly([(27,23),(38,23),(34,30),(26,30)])
                line([(19,6),(68,6)],3)
            else:
                long = f in ("sniper_rifle","scout_rifle","linear_fusion_rifle")
                poly([(6,12),(62,12),(64,15),(90 if long else 80,15),(90 if long else 80,19),(50,19),(46,26),(36,26),(38,19),(22,19),(8,24)])
                line([(30,9),(50 if long else 42,9)],4)
                if long:line([(46,5),(63,5)],4)
                if f in ("machine_gun","trace_rifle"):poly([(47,20),(65,20),(65,29),(47,29)])
                if f=="sidearm":d.rectangle((62*S,0,96*S,32*S),fill=(0,0,0,0))
        asset("ammo_"+family,96,32,silhouette)
    manifest={"stage":"W39","font_source":str(FONT),"font_sha256":hashlib.sha256(FONT.read_bytes()).hexdigest(),
        "note":"Only rasterized numeric glyphs; font not bundled. Original family silhouettes, not ripped sprites.",
        "sha256":{str(p.relative_to(ROOT)):hashlib.sha256(b).hexdigest() for p,b in output.items()}}
    output[ROOT/"art/hud/w39/manifest.json"]=encode(manifest)
    return output
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--verify",action="store_true");args=parser.parse_args()
    generated=generate()
    for p,b in generated.items():
        if args.verify:assert p.read_bytes()==b,p
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    print(("verified" if args.verify else "generated"),len(generated),"W39 files")
