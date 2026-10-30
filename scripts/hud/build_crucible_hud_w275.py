#!/usr/bin/env python3
"""W275: Destiny-2-style Crucible HUD sprites (white/alpha masks, tinted at runtime via custom_model_data).
Writes textures, models and item definitions for destiny:gui/hud/crucible_*.  Deterministic."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parents[2];RES=ROOT/'src/main/resources/assets/destiny'
TEX=RES/'textures/item/hud';MOD=RES/'models/gui/hud';ITM=RES/'items/gui/hud'
FONT='/System/Library/Fonts/Supplemental/Arial Black.ttf'
S=4  # supersample
def save(name,img):
    TEX.mkdir(parents=True,exist_ok=True);MOD.mkdir(parents=True,exist_ok=True);ITM.mkdir(parents=True,exist_ok=True)
    img.save(TEX/f'{name}.png')
    base=json.loads((MOD/'solid.json').read_text())
    base['textures']['layer0']=f'destiny:item/hud/{name}'
    (MOD/f'{name}.json').write_text(json.dumps(base,indent=2)+'\n')
    item=json.loads((ITM/'solid.json').read_text());item['model']['model']=f'destiny:gui/hud/{name}'
    (ITM/f'{name}.json').write_text(json.dumps(item,indent=2)+'\n')
def down(img,w,h):return img.resize((w,h),Image.LANCZOS)
def canvas(w,h):return Image.new('RGBA',(w*S,h*S),(255,255,255,0))
def diamond_pts(cx,cy,r):return [(cx,cy-r),(cx+r,cy),(cx,cy+r),(cx-r,cy)]

# ---- zone diamond family (96px) ------------------------------------------------
W=96
def diamond(fill_alpha=0,ring=0,fraction=None,inset=0):
    im=canvas(W,W);d=ImageDraw.Draw(im);c=W*S/2;r=(W/2-3-inset)*S
    if fill_alpha:d.polygon(diamond_pts(c,c,r),fill=(255,255,255,fill_alpha))
    if ring:d.polygon(diamond_pts(c,c,r),outline=(255,255,255,255),width=ring*S)
    return im
save('crucible_diamond_bg',down(diamond(fill_alpha=150),W,W))
ringim=diamond(ring=5);d=ImageDraw.Draw(ringim);c=W*S/2
d.polygon(diamond_pts(c,c,(W/2-12)*S),outline=(255,255,255,90),width=2*S)
save('crucible_diamond_ring',down(ringim,W,W))
for k in range(1,11):
    im=canvas(W,W);mask=Image.new('L',im.size,0);md=ImageDraw.Draw(mask);c=W*S/2
    md.polygon(diamond_pts(c,c,(W/2-10)*S),fill=255)
    cut=Image.new('L',im.size,0);cd=ImageDraw.Draw(cut)
    top=W*S-(W*S*k/10)  # fill from bottom
    cd.rectangle((0,top,W*S,W*S),fill=255)
    m=Image.composite(mask,Image.new('L',im.size,0),cut)
    # reproduce min via multiply
    from PIL import ImageChops
    m=ImageChops.multiply(mask,cut)
    solid=Image.new('RGBA',im.size,(255,255,255,235));solid.putalpha(m)
    save(f'crucible_diamond_fill_{k:02d}',down(solid,W,W))
# letters
font=ImageFont.truetype(FONT,52*S)
for ch in 'ABC':
    im=canvas(W,W);d=ImageDraw.Draw(im);bb=d.textbbox((0,0),ch,font=font)
    d.text(((W*S-(bb[2]-bb[0]))/2-bb[0],(W*S-(bb[3]-bb[1]))/2-bb[1]),ch,font=font,fill=(255,255,255,255))
    save(f'crucible_letter_{ch.lower()}',down(im,W,W))

# ---- plates, bars, banners -----------------------------------------------------
def para(w,h,slant,fill,outline=0,glow=0):
    im=canvas(w,h);d=ImageDraw.Draw(im);s=slant*S
    pts=[(s,0),(w*S,0),(w*S-s,h*S),(0,h*S)]
    d.polygon(pts,fill=fill)
    if outline:d.polygon(pts,outline=(255,255,255,255),width=outline*S)
    return im
# score bar frames: left leans "/" ... right mirrored
fl=para(580,26,14,(255,255,255,120),outline=2);save('crucible_bar_frame_l',down(fl,580,26))
save('crucible_bar_frame_r',down(fl.transpose(Image.FLIP_LEFT_RIGHT),580,26))
fi=para(580,26,14,(255,255,255,255));save('crucible_bar_fill_l',down(fi,580,26))
save('crucible_bar_fill_r',down(fi.transpose(Image.FLIP_LEFT_RIGHT),580,26))
# center timer plate: hexagon-ish
w,h=230,64;im=canvas(w,h);d=ImageDraw.Draw(im);s=22*S
pts=[(s,0),(w*S-s,0),(w*S,h*S/2),(w*S-s,h*S),(s,h*S),(0,h*S/2)]
d.polygon(pts,fill=(255,255,255,170));d.polygon(pts,outline=(255,255,255,255),width=2*S)
save('crucible_timer_plate',down(im,w,h))
# banners: horizontal fade strip and accent line
w,h=512,64;im=Image.new('RGBA',(w,h))
px=im.load()
for x in range(w):
    t=abs(x-w/2)/(w/2);a=int(235*max(0,1-t**2.2))
    for y in range(h):px[x,y]=(255,255,255,a)
save('crucible_banner',im)
w,h=512,4;im=Image.new('RGBA',(w,h));px=im.load()
for x in range(w):
    t=abs(x-w/2)/(w/2);a=int(255*max(0,1-t**1.6))
    for y in range(h):px[x,y]=(255,255,255,a)
save('crucible_line',im)
# left/right anchored fades (title card, rosters)
for side in('l','r'):
    w,h=512,64;im=Image.new('RGBA',(w,h));px=im.load()
    for x in range(w):
        t=x/w if side=='l' else 1-x/w;a=int(225*max(0,1-t**1.4))
        for y in range(h):px[x,y]=(255,255,255,a)
    save(f'crucible_fade_{side}',im)
# emblems (128px): alpha = chevrons, bravo = ring with bars
w=128;im=canvas(w,w);d=ImageDraw.Draw(im)
for off in(0,26):
    d.polygon([(24*S,(34+off)*S),(64*S,(70+off)*S-34*S+34*S-10*S),(104*S,(34+off)*S),(104*S,(52+off)*S),(64*S,(88+off)*S-10*S),(24*S,(52+off)*S)],fill=(255,255,255,255))
save('crucible_emblem_alpha',down(im,w,w))
im=canvas(w,w);d=ImageDraw.Draw(im);c=w*S/2
d.ellipse((c-44*S,c-44*S,c+44*S,c+44*S),outline=(255,255,255,255),width=9*S)
d.rectangle((c-7*S,c-62*S,c+7*S,c+62*S),fill=(255,255,255,255))
d.rectangle((c-62*S,c-7*S,c+62*S,c+7*S),fill=(255,255,255,255))
d.ellipse((c-24*S,c-24*S,c+24*S,c+24*S),fill=(0,0,0,0))
save('crucible_emblem_bravo',down(im,w,w))
# countdown tick marks: thin diamond for the objective banner icon
save('crucible_pip',down(diamond(fill_alpha=255),W,W))
print('ok')
