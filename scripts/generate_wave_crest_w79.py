#!/usr/bin/env python3
"""Authored rolling energy ribbons; no extracted game texture or remote input.

--verify is a read-only byte comparison. Pillow is supplied by Codex's bundled runtime.
Java model geometry and editable Blockbench source share the same panel description.
"""
from pathlib import Path
import argparse,base64,hashlib,io,json,math,uuid
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/destiny'
def encode(x):return (json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode()
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w79:'+s))

def texture(stasis):
    image=Image.new('RGBA',(64,256))
    for frame in range(4):
        phase=frame*math.tau/4
        for y in range(64):
            for x in range(64):
                u=x/63;v=y/63
                filament=(math.sin(u*math.tau*3+v*13-phase)+math.sin(u*17-v*23+phase*.8))*.25+.5
                vein=abs(math.sin(u*24+math.sin(v*11-phase)*1.4+phase))**16
                pulse=.78+.22*math.sin(v*18+u*12-phase)
                # Body, halo and ground ribbons occupy separate UV bands.
                if y<48 and stasis:
                    height=y/47;edge=abs(u-.5)
                    half=.018+.18*height
                    alpha=max(0,min(1,(half-edge)*75))
                    bright=.85 if u>.5 else .42+.25*height
                elif y<48:
                    front=max(0,math.sin(y/47*math.pi))**.7
                    # Gaps and luminous filaments, not an opaque purple rectangular sheet.
                    alpha=(.05+.88*max(0,(filament-.4)/.6)**1.3)*front*pulse
                    bright=.25+.6*filament+.15*vein
                elif y<56:
                    alpha=(.03+.5*max(0,(filament-.7)/.3))*pulse;bright=.5+.25*vein
                else:
                    alpha=(.25+.7*vein)*(.45+.55*math.sin(u*math.pi));bright=.5+.5*vein
                low,high=((38,62,152),(188,245,255)) if stasis else ((60,12,114),(224,172,255))
                color=tuple(round(a+(b-a)*min(1,bright)) for a,b in zip(low,high))
                # Zero-alpha gaps remain holes even on cutout material paths; don't rely on alpha blending.
                alpha=max(0,min(1,(alpha-.24)/.76))
                image.putpixel((x,frame*64+y),(*color,round(255*alpha)))
    b=io.BytesIO();image.save(b,format='PNG');return b.getvalue()

def panels(stasis=False):
    # Thin overlapping sheets approximate a curling energy front, with its trailing body behind tip z0.
    zs=[-1.35,-1.25,-1,-.75,-.5,-.3,-.2,-.1,0]
    ys=[.04,.07,.14,.27,.43,.55,.61,.56,.38]
    result=[]
    for layer in range(3):
        for i in range(8):
            z0,z1=zs[i],zs[i+1];y0,y1=ys[i],ys[i+1]
            if layer==2:
                cy=.018+i*.001;cz=(z0+z1)/2-.10;length=(z1-z0)*16*1.12;angle=0
                uv=[0,14,16,16]
            else:
                cy=(y0+y1)/2+(0 if layer==0 else .055);cz=(z0+z1)/2-(0 if layer==0 else .045)
                length=math.hypot(z1-z0,y1-y0)*16*1.12
                angle=min([-45,-22.5,0,22.5,45],key=lambda a:abs(a+math.degrees(math.atan2(y1-y0,z1-z0))))
                uv=[0,i*1.5,16,(i+1)*1.5] if layer==0 else [0,12,16,14]
            origin=[8,cy*16,8+cz*16]
            result.append(dict(name=f'{["body","halo","ground"][layer]}_{i}',
                **{'from':[0,origin[1],origin[2]-length/2],'to':[16,origin[1],origin[2]+length/2]},
                shade=False,light_emission=15,rotation=dict(angle=angle,axis='x',origin=origin),
                faces={side:dict(texture='#0',uv=uv) for side in ['up','down']}))
    if not stasis:return result
    # Artist's Stasis presentation has a luminous ground fissure with small needle shards,
    # scattered airborne chips and a low haze: it is not the Void ribbon tinted blue.
    result=[]
    def card(name,a,b,origin,axis,angle,uv,sides):
        result.append(dict(name=name,**{'from':a,'to':b},shade=False,light_emission=15,
            rotation=dict(angle=angle,axis=axis,origin=origin),faces={f:dict(texture='#0',uv=uv) for f in sides}))
    for i in range(6):
        z=8-i*4
        card(f'ground_{i}',[0,.24,z-4],[16,.24,z],[8,.24,z-2],'x',0,[0,14,16,16],['up','down'])
    for i in range(4):
        x=[2,7,11,14][i];z=[7,4,6,2][i];h=[5.5,9.5,7,10.5][i]
        card(f'ice_{i}',[x-2.5,0,z],[x+2.5,h,z],[x,0,z],'y',[-22.5,22.5,45,-45][i],[0,0,16,12],['north','south'])
    for i in range(6):
        x=(i*7)%15+.5;y=5+(i*3)%10;z=5-i*2.7
        card(f'chip_{i}',[x-1,y,z],[x+1,y+2.6,z],[x,y,z],'y',22.5 if i%2 else -45,[0,0,16,12],['north','south'])
    for i in range(8):
        z=5-i*2.4;y=1.8+(i%3)*1.4
        card(f'haze_{i}',[0,y,z-2],[16,y,z+2],[8,y,z],'x',-45 if i%2 else 45,[0,12,16,14],['up','down'])
    return result

def generate():
    output={}
    for element in ['void','stasis']:
        elements=panels(element=='stasis')
        for panel in elements:
            assert all(-16<=v<=32 for field in ['from','to'] for v in panel[field]),panel['name']
        name=f'wave_crest_{element}_w79';png=texture(element=='stasis')
        output[ASSETS/f'textures/item/fx/{name}.png']=png
        output[ASSETS/f'textures/item/fx/{name}.png.mcmeta']=encode(dict(animation=dict(frametime=2,frames=[0,1,2,3],interpolate=False,width=64,height=64)))
        output[ASSETS/f'models/fx/{name}.json']=encode(dict(ambientocclusion=False,gui_light='front',
            textures={'0':f'destiny:item/fx/{name}','particle':f'destiny:item/fx/{name}'},elements=elements))
        output[ASSETS/f'items/fx/{name}.json']=encode(dict(model=dict(type='minecraft:model',model=f'destiny:fx/{name}')))
        bb=[];outliner=[]
        for layer in range(3):
            children=[]
            for i,e in enumerate(elements[layer*8:(layer+1)*8]):
                u=uid(name+e['name']);children.append(u)
                rotation=[0,0,0];rotation['xyz'.index(e['rotation']['axis'])]=e['rotation']['angle']
                bb.append(dict(name=e['name'],uuid=u,type='cube',box_uv=False,origin=e['rotation']['origin'],
                    rotation=rotation,**{'from':e['from'],'to':e['to']},shade=False,
                    faces={face:dict(uv=[v*4 for v in data['uv']],texture=0) for face,data in e['faces'].items()}))
            outliner.append(dict(name=['body','halo','ground'][layer],uuid=uid(name+str(layer)),origin=[8,0,8],children=children))
        model=dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name=name,
            resolution=dict(width=64,height=64),elements=bb,outliner=outliner,
            textures=[dict(name=name+'.png',uuid=uid(name+'texture'),id='0',width=64,height=256,
                uv_width=64,uv_height=64,frameCount=4,source='data:image/png;base64,'+base64.b64encode(png).decode())])
        output[ROOT/f'art/blockbench/vfx/w79/{name}.bbmodel']=encode(model)
    output[ROOT/'art/weapons/w79/asset-manifest.json']=encode(dict(stage='W79',originalArtwork=True,
        panelsPerLane=24,frames=4,frameTimeTicks=2,modelWidthBlocks=1,tipLocalZ=0,trailLengthBlocks=1.5,geometryBoundsModelUnits=[-16,32],
        nominalVisualHeightBlocks={'void':.665,'stasis':1.1},boundsAreAuthoredApproximation=True,source='Shared panel/UV description, not extracted Bungie geometry',
        sha256={str(p.relative_to(ROOT)):hashlib.sha256(b).hexdigest() for p,b in output.items()}))
    return output

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate()
    for p,data in outputs.items():
        if args.verify:assert p.read_bytes()==data,p
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    print(('Verified' if args.verify else 'Generated'),len(outputs),'W79 ribbon source/asset files')
