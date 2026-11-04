#!/usr/bin/env python3
"""W166 Bug-Out Bag: preserved W123 solids, independently withdrawn magazine.

Offline authored approximation after inspecting actual gameplay frames. No hands,
IK, animation rip, runtime edits or DCC control. --verify performs read-only byte checks.
"""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
from PIL import Image, ImageDraw
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w166/bug_out_bag')
KEY = 'weapon_reload_w166_bug_out_bag/bug_out_bag'
SOURCE = A/'models/weapon_surface_w123/bug_out_bag.json'
TWOHAND = A/'models/weapon/submachine_gun/bug_out_bag_twohand.json'
ITEM = A/'items/weapon/bug_out_bag.json'
TEXTURE = A/'textures/item/weapon/w123/bug_out_bag.png'
FP = ('firstperson_righthand', 'firstperson_lefthand')
MOVING = (63,64,65,66)
NAMES = ('magazine_core','magazine_front_spine','magazine_rear_spine','magazine_base')
GRIP = (8,9.12,7.42)
# progress, local body XYZ degrees, view translation, local magazine displacement.
# Observed steep SMG lift, underside exchange, upward seat, ready recovery.
# 130.40..131.92s source; displacement under the hand is authored, not measured.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.10,(28,-5,-8),(.10,.25,-.20),(0,0,0)),
 (.20,(64,-10,-16),(.20,.60,-.45),(-.12,-.85,.04)),
 (.34,(57,-13,-19),(.15,.50,-.40),(-.65,-5.20,.20)),
 (.46,(57,-13,-19),(.15,.50,-.40),(-.65,-5.20,.20)),
 (.60,(61,-11,-17),(.15,.65,-.45),(-.12,-1.50,.06)),
 (.66,(64,-9,-15),(.12,.70,-.50),(0,0,0)),
 (.78,(39,-5,-9),(.05,.30,-.30),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
)


def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def add(a,b): return [x+y for x,y in zip(a,b)]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def mul(a,b): return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(m,v): return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]
def transpose(m): return list(map(list,zip(*m)))
def xyz(angles):
    x,y,z=map(math.radians,angles);a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]
def euler(m):
    b=math.asin(max(-1.,min(1.,m[0][2])))
    a,c=(math.atan2(-m[1][2],m[2][2]),math.atan2(-m[0][1],m[0][0])) if abs(math.cos(b))>1e-8 else (math.atan2(m[2][1],m[1][1]),0)
    return [round(math.degrees(v),9) for v in (a,b,c)]
def sample(p):
    if not math.isfinite(p) or not 0<=p<=1: raise ValueError(p)
    for a,b in zip(KEYS,KEYS[1:]):
        if p<=b[0]:
            t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3))
    raise ValueError(p)

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8))
    local=add(sub(h,vec(body,h)),vec(body,offset if part=='moving' else (0,0,0)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
        if len(set(s))!=1: raise ValueError('Rigid part motion requires uniform first-person scale')
        rotation=mul(base,body)
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            carrier=sub(twohand[context]['translation'],vec(comp,idle['translation']))
            position=add(vec(comp,position),carrier);rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in ('body','moving')}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in ('body','moving') for grip in ('native','twohand'))
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}

def previews(source,reference):
    """Textured orthographic diagnostics, not native captures or hand-contact proof."""
    h=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    # Build posed copies only for the offline raster helper (26.3 source element
    # rotations use its established element convention; products retain exact bytes).
    def render_pose(p,cam,w,hgt):
        angles,shift,offset=sample(p);b=np.array(xyz(angles));g=np.array(GRIP)
        ts=[]
        for i,e in enumerate(source['elements']):
            local=h['model_triangles']({'part':{'elements':[e]}},texture)
            delta=np.array(offset if i in MOVING else [0,0,0])
            for tri in local:
                points,uv,tex,normal=tri
                points=(np.asarray(points)+delta-g)@b.T+g+np.array(shift)
                ts.append((points,uv,tex,b@normal))
        points=np.concatenate([t[0] for t in ts])
        return h['render'](ts,cam,h['frame'](points,cam,w,hgt),(w,hgt))[0]
    sheet=Image.new('RGB',(1440,720),'#111925');d=ImageDraw.Draw(sheet)
    d.text((14,10),'W166 BUG-OUT BAG | W123 exact solids/UV | OFFLINE textured diagnostic, not native',fill='white')
    for row,cam in enumerate(([1,.15,-.35],[-1,.30,.55])):
        for col,p in enumerate((0,.45,1)):
            sheet.paste(render_pose(p,cam,480,300),(col*480,50+row*330))
            d.text((col*480+12,35+row*330),f'p={p:.2f} / '+('muzzle oblique' if row==0 else 'rear oblique'),fill='white')
    d.text((14,700),'96 body + 4 magazine = 100 at every sample; detached magazine retains its source shape and UV.',fill='white')
    story=Image.new('RGB',(1600,1440),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL VIDEO FRAMES | 2foTjMetsbw | timestamps are source seconds | hand-occluded exchange',fill='white')
    for i,f in enumerate(reference['frames']):
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));x=(i%4)*400;y=40+(i//4)*260
        story.paste(im,(x,y));draw.text((x+8,y+228),f"{f['timestampSeconds']:.3f}s",fill='white')
    draw.text((12,830),'AUTHORED MODEL SAMPLES | approximate phase timing; default paint retained | not extracted animation / no hands',fill='white')
    for i,p in enumerate((0,.2,.4,.6,.75,1)):
        x=(i%3)*533;y=865+(i//3)*280
        story.paste(render_pose(p,[1,.25,-.45],533,250),(x,y));draw.text((x+8,y+250),f'p={p:.2f}',fill='white')
    return png(sheet),png(story)

def generate():
    source=json.loads((ROOT/SOURCE).read_bytes());twohand=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=100 or [source['elements'][i]['name'] for i in MOVING]!=list(NAMES): raise ValueError('W123 magazine partition drift')
    design=json.loads((ROOT/'art/weapons/w123/bug_out_bag/design.json').read_bytes())
    if tuple(i for i,p in enumerate(design['parts']) if p['group']=='magazine')!=MOVING: raise ValueError('Semantic magazine group drift')
    if tuple(design['parts'][57]['geometry']['rotation']['origin'])!=GRIP: raise ValueError('Source grip pivot drift')
    ref=json.loads((ROOT/ART/'motion-reference.json').read_bytes())
    if not ref['inspectedActualFrames'] or len(ref['frames'])!=12: raise ValueError('Missing reviewed actual reference')
    for f in ref['frames']:
        if sha((ROOT/f['path']).read_bytes())!=f['sha256']: raise ValueError('Reference drift: '+f['path'])
    output={}
    def emit(path,v): output[path]=encode(v)
    for part in ('body','moving'):
        geo={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        geo['elements']=[copy.deepcopy(e) for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='moving')]
        emit(A/f'models/{KEY}_{part}.json',geo)
    entries=[]
    for i in range(21):
        p=i/20
        for part in ('body','moving'):
            for grip in ('native','twohand'):
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],twohand,p,part,grip)))
        def composite(grip): return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in ('body','moving')])
        entries.append(dict(threshold=p,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    wrapper=copy.deepcopy(item)
    wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model'])))],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    comparison,story=previews(source,ref);output[ART/'comparison.png']=comparison;output[ART/'storyboard.png']=story
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('art/weapons/w123/bug_out_bag/design.json'),ART/'motion-reference.json',Path('scripts/generate_reload_w166_bug_out_bag.py'),Path('scripts/generate_surface_w123_hammerhead.py')]
    emit(ART/'manifest.json',dict(stage='W166',weapon='bug_out_bag',itemModel='destiny:'+KEY,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),sourceElements=100,bodyElements=96,movingElements=4,maxAssembledElements=100,elementLimit=1000,movingIndices=list(MOVING),movingNames=list(NAMES),geometryAndUVPreserved=True,hipEndpoints=[0,20],fallback='Exact canonical items/weapon/bug_out_bag graph for non-FP and inactive negative progress',keyframes=KEYS,gripPivot=GRIP,rotationConvention='JOML Rx Ry Rz; R_idle * R_body; magazine local displacement is rotated by both, scaled once, then carrier compensation',referenceConfidence=ref['referenceConfidence'],reference=ref['url'],nativeGameplayVerified=False,handIK=False,extractedAnimation=False,mechanicsOrAudioChanged=False,limitations=ref['limitations']+['Magazine travels as one rigid assembly; hand contact and native framing require master QA.','No independent bolt or charging-handle motion claimed.'],sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths(): raise ValueError('Output ownership mismatch')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    output=generate()
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b: raise SystemExit('Asset differs: '+str(p))
        else: dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack files; 96+4=100 elements')
if __name__=='__main__': main()
