#!/usr/bin/env python3
"""Original buff-feed sprites; rasterized system glyphs, no ripped Destiny texture/font."""
from pathlib import Path
import argparse, hashlib, io, json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
FONT = Path('/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf')
S = 4
def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode()
def generate():
    out = {}
    def asset(name, width, height, paint):
        im = Image.new('RGBA', (width*S,height*S))
        paint(ImageDraw.Draw(im), im)
        im = im.resize((width,height),Image.Resampling.LANCZOS)
        stream=io.BytesIO();im.save(stream,format='PNG')
        out[ASSETS/f'textures/item/hud/{name}.png']=stream.getvalue()
        out[ASSETS/f'models/gui/hud/{name}.json']=encode({'gui_light':'front',
            'textures':{'layer0':f'destiny:item/hud/{name}'},'elements':[{'from':[0,0,8],'to':[16,16,8],
            'faces':{f:{'texture':'#layer0','uv':[0,0,16,16],'tintindex':0} for f in ('north','south')}}]})
        out[ASSETS/f'items/gui/hud/{name}.json']=encode({'model':{'type':'minecraft:model',
            'model':f'destiny:gui/hud/{name}','tints':[{'type':'minecraft:custom_model_data','index':0,'default':16777215}]}})
    def label(d, im):
        font=ImageFont.truetype(str(FONT),22*S)
        box=d.textbbox((0,0),'Kill Clip',font=font)
        d.text(((94*S-(box[2]-box[0]))/2-box[0],(24*S-(box[3]-box[1]))/2-box[1]),'Kill Clip',font=font,fill='white')
    def marker(d, im):
        d.polygon([(9*S,0),(18*S,9*S),(9*S,18*S),(0,9*S)],fill='white')
        # Transparent upward chevron cutouts distinguish a positive buff from ammo/super icons.
        d.line([(5*S,10*S),(9*S,6*S),(13*S,10*S)], fill=(0,0,0,0),width=2*S)
    def colon(d, im):
        for y in (6,13):d.ellipse((S,y*S,3*S,(y+2)*S),fill='white')
    asset('perk_buff_w61',18,18,marker)
    asset('perk_kill_clip_w61',94,24,label)
    asset('perk_colon_w61',4,20,colon)
    manifest={'stage':'W61','font_source':str(FONT),'font_sha256':hashlib.sha256(FONT.read_bytes()).hexdigest(),
        'note':'Original buff marker and text raster only; no font bundled. Reuses W39 numeric sprites. Offline art, not framebuffer evidence.',
        'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(b).hexdigest() for p,b in out.items()}}
    out[ROOT/'art/hud/w61-perks/manifest.json']=encode(manifest)
    return out
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    generated=generate()
    for path,data in generated.items():
        if args.verify:assert path.read_bytes()==data,path
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('verified' if args.verify else 'generated',len(generated),'W61 HUD files')
