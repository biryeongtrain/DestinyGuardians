"""Material-pass review sheets and face-tile material swatches; no asset writes."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,sys,numpy as np
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/art/w325')); import kit
from identity_review import crop,fit,FONT,IDS

def run():
    root=ROOT/'art/weapons/w325'; combined=Image.new('RGB',(1800,3480),(31,35,40))
    for idx,wid in enumerate(IDS):
        d=root/wid; r=d/'review'; m=json.loads((d/'manifest.json').read_text()); atlas=m['atlas']
        rip=Image.open(d/'proj_cache/nx_albedo.png'); rip=rip.crop(rip.getbbox())
        canvas=Image.new('RGB',(1200,1260),(112,119,128)); dr=ImageDraw.Draw(canvas)
        for text,y in [('READ-ONLY RIP / original material placement',0),('W123 MATERIAL MODEL / west',370),('W123 MATERIAL MODEL / three-quarter',750)]:
            dr.rectangle((0,y,1200,y+35),fill=(30,34,39)); dr.text((12,y+5),f'{wid} | {text}',font=FONT,fill='white')
        fit(canvas,rip,(10,45,1180,310)); fit(canvas,crop(r/f'{wid}_west.png'),(10,415,1180,320)); fit(canvas,crop(r/f'{wid}_q.png'),(10,795,1180,450))
        canvas.save(r/f'{wid}_material_compare.png')
        beforeafter=Image.new('RGB',(2400,740),(31,35,40)); ba=ImageDraw.Draw(beforeafter)
        ba.text((12,8),'PREVIOUS FLAT PAINT',font=FONT,fill='white'); ba.text((1212,8),'MATERIAL PASS: steel / coating / polymer / rubber',font=FONT,fill='white')
        beforeafter.paste(Image.open(r/f'{wid}_flat_before.png').convert('RGB'),(0,40)); beforeafter.paste(Image.open(r/f'{wid}_q.png').convert('RGB'),(1200,40))
        beforeafter.save(r/f'{wid}_material_before_after.png')
        other=Image.new('RGB',(1200,1080),(112,119,128)); od=ImageDraw.Draw(other)
        for view,y in [('east',0),('top',370),('front',740)]:
            od.rectangle((0,y,1200,y+28),fill=(30,34,39)); od.text((12,y+3),f'{wid} | material / {view}',font=FONT,fill='white')
            fit(other,crop(r/f'{wid}_{view}.png'),(10,y+32,1180,325))
        other.save(r/f'{wid}_material_other_views.png')
        tile=Image.new('RGB',(900,870),(112,119,128)); td=ImageDraw.Draw(tile)
        td.rectangle((0,0,900,48),fill=(30,34,39)); td.text((12,7),f'{wid} | {m["element_total"]} elements | T20 / {atlas[0]}x{atlas[1]} | ADS OK',font=FONT,fill='white')
        fit(tile,rip,(10,53,880,220)); fit(tile,crop(r/f'{wid}_west.png'),(10,285,880,230)); fit(tile,crop(r/f'{wid}_q.png'),(10,525,880,330))
        combined.paste(tile,((idx%2)*900,(idx//2)*870))
        D=kit.load_design(wid); skin=json.loads(kit.skin_path(wid).read_text()); tex=Image.open(kit.atlas_path(wid)); choices={}
        for es in skin['parts'].values():
            for e in es:
                for face,data in e['faces'].items():
                    mat=D.material(e['name'],face)
                    if isinstance(mat,dict): mat=next((key for key,v in D.MATERIALS.items() if v['kind']==mat['kind'] and v['color']==mat['color']),None)
                    if mat is None: continue
                    uv=data['uv']; rect=tuple(round(uv[i]*tex.size[i%2]/16) for i in range(4)); patch=tex.crop(rect); area=patch.width*patch.height
                    if mat not in choices or area>choices[mat][0]: choices[mat]=(area,patch,e['name'],face)
        sw=Image.new('RGB',(1000,260*((len(choices)+3)//4)),(31,35,40)); sd=ImageDraw.Draw(sw)
        for i,(key,(_,patch,part,face)) in enumerate(choices.items()):
            x=(i%4)*250;y=(i//4)*260
            patch=patch.resize((238,160),Image.Resampling.NEAREST); sw.paste(patch,(x+6,y+78))
            sd.text((x+6,y+5),key,font=FONT,fill='white'); sd.text((x+6,y+28),D.MATERIALS[key]['kind']+' '+str(D.MATERIALS[key]['color']),font=FONT,fill=(190,198,207))
            sd.text((x+6,y+51),part[:24]+' / '+face,font=FONT,fill=(190,198,207))
        sw.save(r/f'{wid}_material_tiles.png')
    combined.save(root/'lost_and_found/review/w325_material_group5.png')
if __name__=='__main__': run()
