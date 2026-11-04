#!/usr/bin/env python3
"""Original infinite-reserve, damage-type glyphs and stowed-weapon panel. No extracted Bungie textures."""
from pathlib import Path
import argparse,hashlib,io,json,math
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/"src/main/resources/assets/destiny"
def encode(v):return (json.dumps(v,indent=2)+"\n").encode()
def generate():
    output={}
    def asset(name,w,h,paint):
        im=Image.new("RGBA",(w*4,h*4));paint(ImageDraw.Draw(im))
        stream=io.BytesIO();im.resize((w,h),Image.Resampling.LANCZOS).save(stream,format="PNG")
        output[ASSETS/f"textures/item/hud/{name}.png"]=stream.getvalue()
        model={"gui_light":"front","textures":{"layer0":f"destiny:item/hud/{name}"},
            "elements":[{"from":[0,0,8],"to":[16,16,8],"faces":{f:{"texture":"#layer0","uv":[0,0,16,16],"tintindex":0} for f in ("north","south")}}]}
        output[ASSETS/f"models/gui/hud/{name}.json"]=encode(model)
        output[ASSETS/f"items/gui/hud/{name}.json"]=encode({"model":{"type":"minecraft:model",
            "model":f"destiny:gui/hud/{name}","tints":[{"type":"minecraft:custom_model_data","index":0,"default":16777215}]}})
    def line(d,p,width=3):d.line([(x*4,y*4) for x,y in p],fill="white",width=width*4,joint="curve")
    def infinity(d):
        points=[(32+28*math.cos(t)/(1+math.sin(t)**2),16+25*math.sin(t)*math.cos(t)/(1+math.sin(t)**2)) for t in [i*math.tau/160 for i in range(161)]]
        line(d,points,3)
    asset("ammo_infinity",64,32,infinity)
    def panel(d):
        d.rectangle((0,0,999,111),fill=(20,25,31,95));d.line([(4,108),(996,108),(996,4)],fill=(255,255,255,100),width=4)
    asset("ammo_stowed_panel",250,28,panel)
    def glyph(kind):
        def paint(d):
            if kind=="kinetic":line(d,[(8,22),(20,22),(27,12),(43,12),(56,22),(43,32),(27,32),(20,22)],4)
            elif kind=="arc":line(d,[(37,3),(18,31),(32,29),(24,60),(48,25),(35,27),(37,3)],3)
            elif kind=="solar":
                d.ellipse((48,48,208,208),outline="white",width=12)
                for i in range(8):
                    a=i*math.tau/8;line(d,[(32+25*math.cos(a),32+25*math.sin(a)),(32+30*math.cos(a),32+30*math.sin(a))],2)
            elif kind=="void":
                for x,y in [(19,20),(44,20),(32,42)]:d.ellipse(((x-10)*4,(y-10)*4,(x+10)*4,(y+10)*4),outline="white",width=10)
            elif kind=="stasis":
                for i in range(3):
                    a=i*math.pi/3;line(d,[(32+28*math.cos(a),32+28*math.sin(a)),(32-28*math.cos(a),32-28*math.sin(a))],3)
            else:
                line(d,[(7,18),(23,7),(45,18),(53,38),(38,55),(17,48),(11,30),(31,18),(46,29),(37,43),(24,37),(30,28)],3)
        return paint
    for kind in ["kinetic","arc","solar","void","stasis","strand"]:asset("ammo_damage_"+kind,64,64,glyph(kind))
    output[ROOT/"art/hud/w40/manifest.json"]=encode({"originalArtwork":True,"sha256":{
        str(p.relative_to(ROOT)):hashlib.sha256(b).hexdigest() for p,b in output.items()}})
    return output
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--verify",action="store_true");args=p.parse_args()
    for path,data in generate().items():
        if args.verify:assert path.read_bytes()==data,path
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print("verified" if args.verify else "generated","W40 infinite, elemental and backup HUD assets")
