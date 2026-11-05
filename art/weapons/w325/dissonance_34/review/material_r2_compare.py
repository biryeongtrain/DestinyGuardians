from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
r=Path(__file__).resolve().parents[2]
ids=['dissonance_34','requiem_si2','roderic_c','vinegaroon_2si','furina_2mg','whip_scorpion_3mg','traveler_s_chosen']
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
def fit(im,box,bg=(113,119,126),original=False):
 im=im.convert('RGBA')
 if original:
  b=im.getchannel('A').getbbox()
  if b:im=im.crop(b)
 scale=min(box[0]/im.width,box[1]/im.height)*(.86 if original else 1)
 im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if original else Image.Resampling.LANCZOS)
 out=Image.new('RGB',box,bg);out.paste(im,((box[0]-im.width)//2,(box[1]-im.height)//2),im);return out
combined=Image.new('RGB',(1800,7*390),(25,30,37));draw=ImageDraw.Draw(combined)
for i,wid in enumerate(ids):
 p=r/wid/'review';side=Image.open(p/(wid+'_west.png'));q=Image.open(p/(wid+'_q.png'));rip=Image.open(r/wid/'proj_cache/nx_albedo.png')
 cmp=Image.new('RGB',(2200,750),(25,30,37));d=ImageDraw.Draw(cmp)
 cmp.paste(fit(side,(1200,700)),(0,50));cmp.paste(fit(rip,(1000,700),original=True),(1200,50))
 d.text((20,12),wid+' - W325 material pass 2',font=font,fill='white');d.text((1220,12),'Original rip / base material reference',font=font,fill='white')
 cmp.save(p/(wid+'_material_r2_compare.png'))
 draw.text((20,i*390+8),wid,font=font,fill='white')
 combined.paste(fit(side,(600,340)),(0,i*390+45));combined.paste(fit(q,(600,340)),(600,i*390+45));combined.paste(fit(rip,(600,340),original=True),(1200,i*390+45))
combined.save(r/'dissonance_34/review/w325_7_material_r2_all.png')
