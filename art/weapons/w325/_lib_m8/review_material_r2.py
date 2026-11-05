from pathlib import Path
import json,sys,subprocess
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'art/weapons/w325'
IDS=['harmony_21','protostar_csu','philippis_b','sondok_c','badlands_mk_24','botheration_mk_28','fussed_dark_mk_21']
FONT=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',18)

def trim(im,rip=False):
    im=im.convert('RGBA')
    if rip:
        bb=im.getchannel('A').getbbox()
        im=im.crop(bb)
        bg=Image.new('RGBA',im.size,(151,155,160,255));bg.alpha_composite(im);return bg.convert('RGB')
    a=np.asarray(im).astype(int);r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    mask=~((r>140)&(r<175)&((g-r)>=2)&((g-r)<=4)&((b-g)>=3)&((b-g)<=5))
    yy,xx=np.where(mask)
    return im.crop((max(0,min(xx)-12),max(0,min(yy)-12),min(im.width,max(xx)+13),min(im.height,max(yy)+13))).convert('RGB')

def place(canvas,im,box,rip=False):
    im=trim(im,rip);x,y,w,h=box
    scale=min(w/im.width,h/im.height)
    im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if rip else Image.Resampling.LANCZOS)
    canvas.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))
combined=Image.new('RGB',(2160,7*360),(151,155,160));dr=ImageDraw.Draw(combined)
for row,n in enumerate(IDS):
    p=BASE/n;review=p/'review';m=json.loads((p/'manifest.json').read_text())
    ref=Image.open(p/'proj_cache/nx_albedo.png');side=Image.open(review/(n+'_west.png'));q=Image.open(review/(n+'_q.png'))
    compare=Image.new('RGB',(2000,620),(151,155,160));d=ImageDraw.Draw(compare)
    d.text((20,10),n+' | ripped source / material r2 native model',font=FONT,fill='white')
    place(compare,ref,(20,45,950,555),True);place(compare,side,(1020,45,960,555));compare.save(review/(n+'_compare.png'))
    y=row*360;dr.rectangle((0,y,2160,y+34),fill=(37,41,46));dr.text((12,y+7),n+' | RIP / WEST / THREE-QUARTER | '+str(m['element_total'])+' elements',font=FONT,fill='white')
    for col,im in enumerate((ref,side,q)):place(combined,im,(col*720+12,y+40,696,308),col==0)
    # Two side views, top, three-quarter, front are kept at full native render size.
combined.save(BASE/'_lib_m8/material_r2_combined_review.png')
print(BASE/'_lib_m8/material_r2_combined_review.png')
