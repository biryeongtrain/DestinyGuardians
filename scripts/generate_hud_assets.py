#!/usr/bin/env python3
"""Original vector HUD artwork; no extracted Destiny textures. Requires Pillow.
26.3 client JAR is inspected ONLY for vanilla heart sprite names and dimensions.
"""
from pathlib import Path
import io, json, zipfile
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1] / 'src/main/resources/assets'
UI = ROOT / 'destiny/textures/item/hud'
UI.mkdir(parents=True, exist_ok=True)
S = 4

def asset(name, paint):
    im = Image.new('RGBA', (64*S,64*S))
    d = ImageDraw.Draw(im)
    def line(points, width=3, fill='white'):
        d.line([(x*S,y*S) for x,y in points],fill=fill,width=width*S,joint='curve')
    def poly(points, fill='white'):
        d.polygon([(x*S,y*S) for x,y in points],fill=fill)
    paint(d,line,poly)
    im.resize((64,64), Image.Resampling.LANCZOS).save(UI/(name+'.png'))
    model = {'gui_light':'front','textures':{'layer0':'destiny:item/hud/'+name},
             'elements':[{'from':[0,0,8],'to':[16,16,8],'faces':{
                 f:{'texture':'#layer0','uv':[0,0,16,16],'tintindex':0} for f in ('north','south')}}]}
    definition={'model':{'type':'minecraft:model','model':'destiny:gui/hud/'+name,
                         'tints':[{'type':'minecraft:custom_model_data','index':0,'default':16777215}]}}
    for path,data in [(ROOT/'destiny/models/gui/hud'/f'{name}.json',model),
                      (ROOT/'destiny/items/gui/hud'/f'{name}.json',definition)]:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data,indent=2)+'\n')

asset('solid',lambda d,l,p:p([(0,0),(64,0),(64,64),(0,64)]))
def tile(d,l,p):
    p([(1,1),(56,1),(63,8),(63,63),(8,63),(1,56)],(35,39,44,200))
    l([(1,54),(1,1),(54,1),(63,10),(63,63),(10,63),(1,54)],1,(255,255,255,180))
asset('tile',tile)
def diamond(d,l,p):
    p([(32,0),(64,32),(32,64),(0,32)],(38,42,48,220))
    l([(32,1),(63,32),(32,63),(1,32),(32,1)],2)
asset('diamond',diamond)
# Distinct, legible silhouettes for each equipped ability.
asset('flash',lambda d,l,p:(p([(28,7),(38,7),(35,22),(49,28),(37,35),(36,49),(25,54),(20,42),(11,32),(25,24)]),l([(45,9),(50,4)],2),l([(49,43),(57,48)],2)))
asset('flame',lambda d,l,p:(p([(34,5),(44,23),(50,34),(48,48),(38,57),(24,57),(14,49),(12,36),(22,20),(22,34),(29,28)]),p([(32,32),(39,44),(34,53),(27,51),(25,44)],(35,39,44,255))))
asset('vortex',lambda d,l,p:(l([(50,21),(42,12),(28,9),(15,17),(9,29),(12,43),(24,53),(39,53),(50,43),(53,31),(43,24),(31,24),(24,31),(25,39),(34,43),(41,37),(38,32)],4),p([(47,10),(53,23),(39,22)])))
asset('fist',lambda d,l,p:(p([(13,26),(18,18),(24,18),(24,13),(31,11),(36,15),(43,14),(49,20),(51,34),(44,48),(23,53),(16,44),(8,34)]),l([(24,23),(27,34),(38,32),(42,24)],2,(35,39,44,255))))
asset('knife',lambda d,l,p:(p([(44,5),(47,25),(25,43),(19,37)]),l([(14,33),(31,49)],4),l([(19,43),(10,54)],6)))
asset('smoke',lambda d,l,p:(p([(15,26),(17,18),(28,13),(40,16),(47,24),(45,34),(53,40),(50,49),(39,53),(22,50),(12,53),(7,45),(10,35)]),l([(23,21),(19,29),(25,34),(35,30),(39,22)],2,(35,39,44,255))))
asset('dodge',lambda d,l,p:(l([(48,20),(35,12),(19,19),(12,33),(21,47),(37,50),(48,42)],4),p([(44,11),(57,22),(41,25)]),l([(26,31),(39,35)],4),l([(4,54),(20,54)],2)))
asset('staff',lambda d,l,p:(l([(19,53),(44,10)],5),l([(32,9),(53,21)],4),l([(13,43),(29,54)],4)))
asset('gun',lambda d,l,p:(p([(9,20),(51,20),(55,26),(50,33),(31,33),(26,49),(16,49),(20,33),(9,33)]),l([(35,34),(33,40),(27,40)],2)))
asset('bow',lambda d,l,p:(l([(17,7),(39,17),(46,32),(39,47),(17,57)],3),l([(17,7),(22,32),(17,57)],2),l([(15,32),(55,32)],3),p([(48,25),(58,32),(48,39)])))

# Only player hearts are suppressed; mount health keeps its vanilla sprites.
jar=Path.home()/'.gradle/caches/fabric-loom/26.3/minecraft-client.jar'
manifest=[]
with zipfile.ZipFile(jar) as z:
    for name in z.namelist():
        if not (name.startswith('assets/minecraft/textures/gui/sprites/hud/heart/') and name.endswith('.png')):continue
        if '/vehicle_' in name:continue
        original=Image.open(io.BytesIO(z.read(name)))
        out=ROOT.parent/name
        out.parent.mkdir(parents=True,exist_ok=True)
        Image.new('RGBA',original.size).save(out)
        manifest.append({'path':name,'width':original.width,'height':original.height})
(ROOT/'destiny/hud_heart_sprites.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Generated {len(list(UI.glob("*.png")))} HUD sprite models and {len(manifest)} transparent player-heart sprites')
