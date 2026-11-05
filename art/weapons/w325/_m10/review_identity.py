from PIL import Image, ImageDraw
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
IDS=['cup_bearer_sa_2','reginar_b','weaver_c','plemusa_b','stampede_mk_32','future_imperfect','rest_for_the_wicked']
def paste_fit(canvas,im,rect):
 x,y,w,h=rect;im=im.convert('RGB');im.thumbnail((w,h));canvas.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))
combined=Image.new('RGB',(1800,2800),'#25282c'); d=ImageDraw.Draw(combined)
for i,w in enumerate(IDS):
 p=ROOT/'art/weapons/w325'/w
 rip=Image.open(p/'proj_cache/nx_albedo.png').convert('RGBA')
 if rip.getchannel('A').getbbox():rip=rip.crop(rip.getchannel('A').getbbox())
 bg=Image.new('RGB',rip.size,'#747980');bg.paste(rip,mask=rip.getchannel('A'));rip=bg
 west=Image.open(p/'review'/f'{w}_west.png');q=Image.open(p/'review'/f'{w}_q.png')
 sword=w in IDS[-2:]
 if sword:
  comp=Image.new('RGB',(1500,1200),'#25282c')
  for j,im in enumerate((rip,west,q)):paste_fit(comp,im,(j*500,30,500,1160))
 else:
  comp=Image.new('RGB',(1200,1300),'#25282c')
  for j,im in enumerate((rip,west,q)):paste_fit(comp,im,(0,j*425+25,1200,400))
 ImageDraw.Draw(comp).text((10,5),w+' | RIP / IDENTITY SIDE / THREE QUARTER',fill='white')
 comp.save(p/'review'/f'{w}_compare.png')
 # Each row shows source side and new three-quarter, with full sword silhouette.
 yy=i*400; d.text((12,yy+7),w+' | RIP                                              IDENTITY',fill='white')
 paste_fit(combined,rip,(0,yy+28,800,362));paste_fit(combined,q,(800,yy+28,1000,362))
combined.save(ROOT/'art/weapons/w325/_m10/identity_review.png')
