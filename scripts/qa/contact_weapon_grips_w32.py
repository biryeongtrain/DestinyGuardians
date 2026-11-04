from PIL import Image,ImageDraw,ImageFont
import pathlib,json,collections,math,argparse
p=argparse.ArgumentParser();p.add_argument("--out",type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[2]/"docs/qa/2026-10-23/w32");root=p.parse_args().out
records=json.loads((root/"frames/captures.json").read_text())["records"]
font=ImageFont.truetype("/System/Library/Fonts/Menlo.ttc",14)
groups=collections.defaultdict(list)
for r in records:groups[r["context"]].append(r)
for context,rs in groups.items():
 if context.startswith("compare_"):continue
 for page in range(math.ceil(len(rs)/21)):
  group=rs[page*21:(page+1)*21];w=420;h=270;sheet=Image.new("RGB",(1260,50+math.ceil(len(group)/3)*h),"#11161c");d=ImageDraw.Draw(sheet)
  d.text((12,12),"W32 "+context+" native frame crops / "+str(page+1),font=font,fill="white")
  for i,r in enumerate(group):
   im=Image.open(root/"frames"/r["file"]).convert("RGB")
   crop=(420,370,1100,850) if context in ("observer","optional_two_hand") else (650,370,1100,840) if context=="third_front" else (680,140,1708,950) if context=="hip" else (350,150,1358,900) if context=="ads" else (480,100,1708,950)
   im=im.crop(crop);im.thumbnail((410,215));x=i%3*w;y=50+i//3*h;sheet.paste(im,(x+(w-im.width)//2,y));d.text((x+8,y+220),r["id"][:40],font=font,fill="white");d.text((x+8,y+242),r["family"],font=font,fill="#88a8c8")
  sheet.save(root/(context+"-contact-"+str(page+1)+".jpg"),quality=92)
# Two-hand versus native uses the SAME build and actor, not a Blender render.
comp=Image.new("RGB",(1440,1100),"#11161c");d=ImageDraw.Draw(comp)
for i,context in enumerate(("third_front","hip","ads","inspect")):
 for j,grip in enumerate(("native","two_hand")):
  record=next(r for r in records if r["context"]=="compare_"+grip+"_"+context)
  im=Image.open(root/"frames"/record["file"]).convert("RGB")
  im=im.crop((650,330,1120,840) if context=="third_front" else (500,200,1708,950));im.thumbnail((690,235))
  x=j*720;y=i*275;comp.paste(im,(x+(720-im.width)//2,y+30));d.text((x+15,y+8),context+" / "+grip,font=font,fill="white")
comp.save(root/"native-grip-comparison.jpg",quality=94)
print("Contact sheets",len(list(root.glob("*-contact-*.jpg"))))
