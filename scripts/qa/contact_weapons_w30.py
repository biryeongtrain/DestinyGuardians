"""Contact sheets only. Raw native framebuffer PNGs remain unmodified beside them."""
import argparse,json,math,pathlib
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,default=ROOT/'docs/qa/2026-10-23/w30');p.add_argument('--label',default='W30');args=p.parse_args()
QA=args.out
rows=json.loads((ROOT/'art/weapons/w30/catalog.json').read_text())
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',14)
small=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',11)
for context in ('gui','hip','ads','inspect','third_front'):
    present=[r for r in rows if (QA/'frames'/context/(r['id']+'.png')).exists()]
    per_page=21 if len(present)>21 else 20
    for page in range(math.ceil(len(present)/per_page)):
        group=present[page*per_page:(page+1)*per_page];cols=3 if len(present)>21 else 4;w=420;h=300
        sheet=Image.new('RGB',(cols*w,math.ceil(len(group)/cols)*h+52),'#11161c');d=ImageDraw.Draw(sheet)
        d.text((18,16),f'{args.label} / native {context} / page {page+1} / unmodified source frames: frames/{context}/',font=font,fill='#d8e3ef')
        for i,r in enumerate(group):
            im=Image.open(QA/'frames'/context/(r['id']+'.png')).convert('RGB')
            crop={'gui':(380,140,1328,820),'hip':(680,140,1708,950),'ads':(350,150,1358,900),'inspect':(480,100,1708,950),'third_front':(330,220,1200,840)}[context]
            im=im.crop(crop);im.thumbnail((w-16,h-64))
            x=(i%cols)*w;y=(i//cols)*h+52;sheet.paste(im,(x+(w-im.width)//2,y))
            d.text((x+10,y+h-55),r['name'][:48],font=font,fill='white')
            d.text((x+10,y+h-31),r['family']+' / '+r['frame'],font=small,fill='#88a8c8')
        sheet.save(QA/f'{context}-contact-{page+1}.jpg',quality=92)
print('W30 contact sheets saved')
