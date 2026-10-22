#!/usr/bin/env python3
"""H17 original vector artwork; no extracted textures or external fonts. Requires Pillow."""
from pathlib import Path
import json
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1] / "src/main/resources/assets/destiny"
S = 3

def save(name, image):
    texture = ROOT / "textures/item/hud" / (name + ".png")
    texture.parent.mkdir(parents=True, exist_ok=True)
    image.save(texture)
    model = {"gui_light":"front", "textures":{"layer0":"destiny:item/hud/"+name,"particle":"destiny:item/hud/"+name}, "elements":[{
        "from":[0,0,8], "to":[16,16,8], "faces":{f:{"texture":"#layer0","uv":[0,0,16,16],"tintindex":0} for f in ("north","south")}}]}
    item = {"model":{"type":"minecraft:model","model":"destiny:gui/hud/"+name,
                     "tints":[{"type":"minecraft:custom_model_data","index":0,"default":16777215}]}}
    for folder, data in (("models",model),("items",item)):
        path = ROOT / folder / "gui/hud" / (name+".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2)+"\n")

# Original single-stroke tracked capitals, independent of the game's typeface.
GLYPHS = {
    "S":[[(10,0),(2,0),(0,2),(0,7),(2,9),(8,9),(10,11),(10,16),(8,18),(0,18)]],
    "U":[[(0,0),(0,15),(3,18),(7,18),(10,15),(10,0)]],
    "P":[[(0,18),(0,0),(8,0),(10,2),(10,7),(8,9),(0,9)]],
    "E":[[(10,0),(0,0),(0,18),(10,18)],[(0,9),(8,9)]],
    "R":[[(0,18),(0,0),(8,0),(10,2),(10,7),(8,9),(0,9)],[(5,9),(10,18)]],
    "C":[[(10,0),(3,0),(0,3),(0,15),(3,18),(10,18)]],
    "H":[[(0,0),(0,18)],[(10,0),(10,18)],[(0,9),(10,9)]],
    "A":[[(0,18),(0,4),(4,0),(6,0),(10,4),(10,18)],[(0,10),(10,10)]],
    "G":[[(10,2),(8,0),(3,0),(0,3),(0,15),(3,18),(10,18),(10,9),(6,9)]],
    "D":[[(0,0),(6,0),(10,4),(10,14),(6,18),(0,18),(0,0)]]
}

def banner(opacity):
    im = Image.new("RGBA", (640*S,128*S))
    d=ImageDraw.Draw(im)
    def line(points, alpha=255, width=1):
        d.line([(round(x*S),round(y*S)) for x,y in points], fill=(255,255,255,round(alpha*opacity)),width=width*S,joint="curve")
    # A quiet graphite scrim keeps gold readable against bright skies, not a full-screen dim.
    d.rectangle((4*S,27*S,636*S,101*S),fill=(12,14,18,round(95*opacity)))
    line([(4,27),(636,27),(636,101),(4,101),(4,27)],230)
    # Faint original energy sigil; not an extracted subclass emblem.
    line([(320,5),(379,64),(320,123),(261,64),(320,5)],45)
    line([(320,17),(367,64),(320,111),(273,64),(320,17)],30)
    phrase="SUPER CHARGED"
    tracking=30
    start=(640-(len(phrase)-1)*tracking-14)/2
    for i,ch in enumerate(phrase):
        if ch==" ": continue
        for path in GLYPHS[ch]:
            line([(start+i*tracking+x*1.5,50+y*1.5) for x,y in path],255,3)
    return im.resize((640,128),Image.Resampling.LANCZOS)

for i,a in enumerate((0.35,0.65,0.85,1.0,0.8,0.5,0.22)):
    save("ready_banner_"+str(i),banner(a))

im=Image.new("RGBA",(64*S,64*S)); d=ImageDraw.Draw(im)
d.polygon([(32*S,0),(64*S,32*S),(32*S,64*S),(0,32*S)],fill=(255,255,255,255))
save("diamond_ready",im.resize((64,64),Image.Resampling.LANCZOS))
for i,a in enumerate((220,160,95,40)):
    im=Image.new("RGBA",(128*S,128*S)); d=ImageDraw.Draw(im)
    d.line([(64*S,2*S),(126*S,64*S),(64*S,126*S),(2*S,64*S),(64*S,2*S)],fill=(255,255,255,a),width=2*S)
    save("ready_echo_"+str(i),im.resize((128,128),Image.Resampling.LANCZOS))

# Transparent centre 70% of view; slim peripheral filaments, not bloom or world lighting.
for frame in range(6):
    im=Image.new("RGBA",(512,288)); d=ImageDraw.Draw(im)
    alpha=(135,115,90,65,40,20)[frame]
    inset=10+frame*2
    for side in (0,1):
        x = inset if side==0 else 511-inset
        sign=1 if side==0 else -1
        d.line([(x+sign*16,94),(x,110),(x,178),(x+sign*16,194)],fill=(255,255,255,alpha),width=1)
        d.line([(x+sign*22,112),(x+sign*9,123),(x+sign*9,165),(x+sign*22,176)],fill=(255,255,255,alpha//2),width=1)
    save("cast_flash_"+str(frame),im)
print("Generated 18 original H17 HUD textures and matching item/model definitions")
