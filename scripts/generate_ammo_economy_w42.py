#!/usr/bin/env python3
"""Original ammo pickup shells and meter glyph. No marketplace files or extracted Bungie textures."""
from pathlib import Path
import argparse,base64,hashlib,io,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/destiny'
def encode(v):return (json.dumps(v,indent=2)+'\n').encode()
def png(im):
    b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def generate():
    out={}
    for kind,color in [('special',(110,227,153)),('heavy',(178,120,243))]:
        name=f'ammo_brick_{kind}_w42';im=Image.new('RGBA',(64,64));d=ImageDraw.Draw(im)
        colors=[(48,57,66),(116,128,136),color,(218,238,239),(21,28,37),(75,90,101),(240,201,90),(170,184,191)]
        for i,c in enumerate(colors):
            x=(i%4)*16;y=(i//4)*16;d.rectangle((x,y,x+15,y+15),fill=(*c,255))
            d.line((x,y,x+15,y),fill=tuple(min(255,v+15) for v in c)+(255,),width=1)
        texture=png(im);out[ASSETS/f'textures/item/fx/{name}.png']=texture
        elements=[]
        def cube(label,lo,hi,material):
            x=(material%4)*4;y=(material//4)*4
            uv=[x+.35,y+.35,x+3.65,y+3.65]
            elements.append({'name':label,'from':lo,'to':hi,'faces':{f:{'texture':'#0','uv':uv} for f in ('north','south','east','west','up','down')}})
        cube('lower dark chassis',[2,0,4],[14,2,12],0)
        cube('energy core',[3,1.5,4.5],[13,4,11.5],2)
        cube('top metal plate',[3,3.5,5],[13,4.5,11],1)
        for x in (2,12.5):
            cube('armoured end cap',[x,.2,4],[x+1.5,4.7,12],1)
            cube('cap inset',[x-.02,1.2,6],[x+1.52,3.2,10],4)
        for z in (4,11.4):
            cube('rail',[3,3.7,z],[13,5,z+.6],5)
            cube('luminous rail',[4,4.7,z-.02],[12,5.1,z+.62],2)
        for x in (4,10.5):
            cube('top clamp',[x,4.4,6],[x+1.5,5.1,10],0)
            cube('light insert',[x+.35,5.05,6.6],[x+1.15,5.2,9.4],3)
        cube('center badge',[7,4.5,7],[9,5.2,9],2)
        for x in (2.5,12):
            for z in (4.5,10.8):cube('corner fastener',[x,4.6,z],[x+.5,4.9,z+.5],7)
        model={'credit':'W42 original Minecraft approximation; not a ripped Destiny ammo asset',
               'textures':{'0':f'destiny:item/fx/{name}','particle':'#0'},'elements':elements}
        out[ASSETS/f'models/fx/{name}.json']=encode(model)
        out[ASSETS/f'items/fx/{name}.json']=encode({'model':{'type':'minecraft:model','model':f'destiny:fx/{name}'}})
        # Editable source. Deterministic UUIDs keep regeneration reviewable.
        bb=[]
        for i,e in enumerate(elements):
            uuid=hashlib.md5(f'{name}:{i}'.encode()).hexdigest()
            uuid=f'{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}'
            bb.append({**e,'uuid':uuid,'type':'cube','origin':[8,0,8],
                       'faces':{k:{'uv':v['uv'],'texture':0} for k,v in e['faces'].items()}})
        out[ROOT/f'art/blockbench/ammo/{name}.bbmodel']=encode({'meta':{'format_version':'5.0','model_format':'java_block','box_uv':False},
             'name':name,'resolution':{'width':64,'height':64},'elements':bb,'outliner':[e['uuid'] for e in bb],
             'textures':[{'name':name+'.png','id':'0','source':'data:image/png;base64,'+base64.b64encode(texture).decode()}]})
    im=Image.new('RGBA',(32,32));d=ImageDraw.Draw(im)
    for x in (7,19):d.polygon([(x,26),(x,9),(x+3,4),(x+6,9),(x+6,26)],outline='white',width=2)
    name='ammo_meter_w42'
    out[ASSETS/f'textures/item/hud/{name}.png']=png(im)
    out[ASSETS/f'models/gui/hud/{name}.json']=encode({'gui_light':'front','textures':{'0':f'destiny:item/hud/{name}','particle':'#0'},
        'elements':[{'from':[0,0,8],'to':[16,16,8],'faces':{f:{'texture':'#0','uv':[0,0,16,16],'tintindex':0} for f in ('north','south')}}]})
    out[ASSETS/f'items/gui/hud/{name}.json']=encode({'model':{'type':'minecraft:model','model':f'destiny:gui/hud/{name}',
        'tints':[{'type':'minecraft:custom_model_data','index':0,'default':16777215}]}})
    out[ROOT/'art/hud/w42/manifest.json']=encode({'originalArtwork':True,'sha256':{
        str(p.relative_to(ROOT)):hashlib.sha256(b).hexdigest() for p,b in out.items()}})
    return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
    for path,raw in generate().items():
        if a.verify:assert path.read_bytes()==raw,path
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    print('verified' if a.verify else 'generated','W42 ammo shells, editable sources and meter icon')
