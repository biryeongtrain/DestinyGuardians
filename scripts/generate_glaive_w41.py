#!/usr/bin/env python3
"""Original glaive reticle and transparent shield outline; not extracted Bungie sprites."""
from pathlib import Path
import argparse,hashlib,io,json,math
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def encode(x):return (json.dumps(x,indent=2)+"\n").encode()
def generate():
    output={};assets=ROOT/'src/main/resources/assets/destiny'
    def asset(name,folder,paint):
        im=Image.new('RGBA',(512,512));paint(ImageDraw.Draw(im))
        buf=io.BytesIO();im.resize((128,128),Image.Resampling.LANCZOS).save(buf,format='PNG')
        output[assets/f'textures/item/{folder}/{name}.png']=buf.getvalue()
        key=f'gui/hud/{name}' if folder=='hud' else f'fx/{name}'
        output[assets/f'models/{key}.json']=encode({'gui_light':'front','textures':{'0':f'destiny:item/{folder}/{name}'},
            'elements':[{'from':[0,0,8],'to':[16,16,8],'faces':{f:{'texture':'#0','uv':[0,0,16,16],**({'tintindex':0} if folder=='hud' else {})} for f in ('north','south')}}]})
        output[assets/f'items/{key}.json']=encode({'model':{'type':'minecraft:model','model':f'destiny:{key}',
            **({'tints':[{'type':'minecraft:custom_model_data','index':0,'default':16777215}]} if folder=='hud' else {})}})
    def reticle(d):
        d.ellipse((236,236,276,276),outline='white',width=7)
        d.line([(158,204),(126,256),(158,308)],fill='white',width=10,joint='curve')
        d.line([(354,204),(386,256),(354,308)],fill='white',width=10,joint='curve')
    def shield(d):
        def hexagon(cx,cy,r,width,alpha):
            pts=[(cx+math.cos(i*math.tau/6)*r,cy+math.sin(i*math.tau/6)*r) for i in range(7)]
            d.line(pts,fill=(123,220,250,alpha),width=width,joint='curve')
        hexagon(256,256,243,7,225);hexagon(256,256,233,2,95)
        # Open centre keeps the player's aim visible; faint perimeter cells do not imply collisions.
        for i in range(6):
            a=i*math.tau/6;hexagon(256+math.cos(a)*190,256+math.sin(a)*190,30,2,120)
    asset('glaive_reticle_w41','hud',reticle);asset('glaive_shield_w41','fx',shield)
    output[ROOT/'art/hud/w41/manifest.json']=encode({'originalArtwork':True,'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(b).hexdigest() for p,b in output.items()}})
    return output
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
    for path,b in generate().items():
        if a.verify:assert path.read_bytes()==b,path
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    print('verified' if a.verify else 'generated','W41 glaive reticle/shield assets')
