#!/usr/bin/env python3
"""Original Outlaw buff text sprite. Reuses W61 marker and W39 digits; no ripped sprite/font."""
from pathlib import Path
import argparse, hashlib, io, json
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/destiny'
FONT=Path('/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf')
def encode(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
def generate():
    name='perk_outlaw_w62';out={};s=4
    im=Image.new('RGBA',(94*s,24*s));d=ImageDraw.Draw(im);font=ImageFont.truetype(str(FONT),22*s)
    box=d.textbbox((0,0),'Outlaw',font=font)
    d.text(((94*s-box[2]+box[0])/2-box[0],(24*s-box[3]+box[1])/2-box[1]),'Outlaw',font=font,fill='white')
    im=im.resize((94,24),Image.Resampling.LANCZOS);stream=io.BytesIO();im.save(stream,format='PNG')
    out[ASSETS/f'textures/item/hud/{name}.png']=stream.getvalue()
    out[ASSETS/f'models/gui/hud/{name}.json']=encode({'gui_light':'front','textures':{'layer0':f'destiny:item/hud/{name}'},
        'elements':[{'from':[0,0,8],'to':[16,16,8],'faces':{f:{'texture':'#layer0','uv':[0,0,16,16],'tintindex':0} for f in ('north','south')}}]})
    out[ASSETS/f'items/gui/hud/{name}.json']=encode({'model':{'type':'minecraft:model','model':f'destiny:gui/hud/{name}',
        'tints':[{'type':'minecraft:custom_model_data','index':0,'default':16777215}]}})
    preview=Image.new('RGBA',(600,180),(28,32,39,255));pd=ImageDraw.Draw(preview)
    pd.text((12,10),'W62 OFFLINE SPRITE PREVIEW - NOT IN-GAME',fill='white')
    for label,y,seconds in [('perk_outlaw_w62',60,6),('perk_kill_clip_w61',112,5)]:
        parts=[('perk_buff_w61',36,36,35,y+6,(141,226,175)),(label,188,48,83,y,(241,243,245)),
            ('ammo_digit_0',20,40,296,y+4,(241,243,245)),('perk_colon_w61',8,40,320,y+4,(241,243,245)),
            ('ammo_digit_0',20,40,332,y+4,(241,243,245)),(f'ammo_digit_{seconds}',20,40,356,y+4,(241,243,245))]
        for part,w,h,x,py,rgb in parts:
            raw=out.get(ASSETS/f'textures/item/hud/{part}.png')
            sprite=Image.open(io.BytesIO(raw)) if raw else Image.open(ASSETS/f'textures/item/hud/{part}.png')
            sprite=sprite.convert('RGBA').resize((w,h),Image.Resampling.LANCZOS)
            tint=Image.new('RGBA',sprite.size,(*rgb,255));tint.putalpha(sprite.getchannel('A'));preview.alpha_composite(tint,(x,py))
    stream=io.BytesIO();preview.save(stream,format='PNG');out[ROOT/'art/hud/w62-outlaw/offline-preview.png']=stream.getvalue()
    manifest={'stage':'W62','font_source':str(FONT),'font_sha256':hashlib.sha256(FONT.read_bytes()).hexdigest(),
        'note':'Original rasterized glyphs, no font bundled. Preview is offline compositing, NOT a framebuffer.',
        'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(b).hexdigest() for p,b in out.items()}}
    out[ROOT/'art/hud/w62-outlaw/manifest.json']=encode(manifest);return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args();out=generate()
    for path,data in out.items():
        if args.verify:assert path.read_bytes()==data,path
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('verified' if args.verify else 'generated',len(out),'W62 HUD files')
