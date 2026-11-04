"""Read-only native W30/W31 framebuffer crops; no source PNG is modified.

Requires both QA capture directories. Screenshot references may optionally be
read from the private download cache; only their contact comparison is written.
"""
import argparse,json,pathlib
from PIL import Image,ImageDraw,ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
p.add_argument('--before',type=pathlib.Path,default=ROOT/'docs/qa/2026-10-23/w30')
p.add_argument('--after',type=pathlib.Path,default=ROOT/'docs/qa/2026-10-23/w31')
p.add_argument('--references',type=pathlib.Path)
args=p.parse_args()
rows=json.loads((ROOT/'art/weapons/w30/catalog.json').read_text())
rows=[r for r in rows if r['id'] in ('duke_mk_44','austringer','cold_denial','biting_winds','apostate','hammerhead')]
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',16)
columns=[('W30: native / 51-128 cubes',args.before),('W31: native / 148-256 cubes',args.after)]
if args.references:columns.insert(0,('light.gg Item Screenshot',args.references))
sheet=Image.new('RGB',(len(columns)*560,70+len(rows)*295),'#151b23');d=ImageDraw.Draw(sheet)
for i,(label,_) in enumerate(columns):d.text((i*560+12,14),label,font=font,fill='white')
for y,r in enumerate(rows):
 for x,(_,folder) in enumerate(columns):
  path=folder/(r['id']+'.jpg') if folder==args.references else folder/'frames/gui'/(r['id']+'.png')
  im=Image.open(path).convert('RGB')
  if folder!=args.references:im=im.crop((380,140,1328,820))
  im.thumbnail((548,252));sheet.paste(im,(x*560+(560-im.width)//2,60+y*295))
  d.text((x*560+12,60+y*295+260),r['name'][:50],font=font,fill='#dce5ee')
args.after.mkdir(parents=True,exist_ok=True)
sheet.save(args.after/'native-comparison.jpg',quality=94)
