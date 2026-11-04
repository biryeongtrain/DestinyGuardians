#!/usr/bin/env python3
"""W168 Austringer: preserved W123 solids, independently swung cylinder.

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
ART = Path('art/weapons/w168/austringer')
KEY = 'weapon_reload_w168_austringer/austringer'
SOURCE = A/'models/weapon_surface_w123/austringer.json'
TWOHAND = A/'models/weapon/hand_cannon/austringer_twohand.json'
ITEM = A/'items/weapon/austringer.json'
TEXTURE = A/'textures/item/weapon/w123/austringer.png'
FP = ('firstperson_righthand', 'firstperson_lefthand')
# Current W129 authored clean W123 solids, not the old ripped/voxel model.
# Receiver group also includes FIXED frame and breech; only cylinder/bands move.
MOVING = tuple(range(32,44))
NAMES = tuple([f'Cylinder_{i}' for i in range(4)] +
              [f'Cylinder_{end}_band_{i}' for end in ('front','rear') for i in range(4)])
FIXED_FRAME = (44,45,46,47)
GRIP = (8,9.38,7.515)  # Current Grip_palm rotation origin.
HINGE = (7.3,11.06,4.34)  # Authored left-lower cylinder crane approximation.
SOURCE_SHA256 = '2026a115380d72420a5f7bd60928547ef567303addd511c75b92f58b0c3bf93c'
# Viewed actual AUSTRINGER TPWRjqb_O5U, 11.70..13.40 seconds.
# Roll/open -> muzzle-up open hold -> lower/loader contact -> closing flick.
# progress, body XYZ degrees, view translation, cylinder XYZ about HINGE.
# Numerical pose/hinge/timing are approximations, not extracted motion or hands.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.09,(8,-6,-12),(-.05,-.10,0),(0,0,68)),
 (.20,(48,-8,-16),(.15,-.10,-.15),(0,0,78)),
 (.29,(70,-5,-10),(.25,-.20,-.25),(0,0,78)),
 (.50,(65,-6,-12),(.25,-.20,-.25),(0,0,78)),
 (.62,(18,-10,18),(.10,-.35,-.10),(0,0,78)),
 (.76,(3,-8,23),(0,-.45,0),(0,0,78)),
 (.84,(0,-3,-12),(0,-.20,0),(0,0,12)),
 (.90,(6,2,-6),(0,-.05,0),(0,0,0)),
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
    angles,shift,cylinder=sample(p)
    body=xyz(angles);component=xyz(cylinder if part=='moving' else (0,0,0))
    h=sub(GRIP,(8,8,8));c=sub(HINGE,(8,8,8))
    # Independent cylinder rotation around its crane, then whole gun around grip.
    local=add(sub(h,vec(body,h)),vec(body,sub(c,vec(component,c))))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);scale=idle['scale']
        if len(set(scale))!=1: raise ValueError('Rigid motion requires uniform FP scale')
        if twohand[context]['scale']!=scale: raise ValueError('Grip scale mismatch')
        rotation=mul(mul(base,body),component)
        position=add(add(idle['translation'],shift),vec(base,[scale[0]*v for v in local]))
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
    """Textured offline diagnostics, never native captures or hand-contact proof."""
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles=[helper['model_triangles']({'part':{'elements':[e]}},texture) for e in source['elements']]
    def posed(p):
        angles,shift,cylinder=sample(p);b=np.array(xyz(angles));c=np.array(xyz(cylinder))
        g=np.array(GRIP);hinge=np.array(HINGE);result=[]
        for i,tris in enumerate(triangles):
            for points,uv,tex,normal in tris:
                points=np.asarray(points);normal=np.asarray(normal)
                if i in MOVING:
                    points=(points-hinge)@c.T+hinge;normal=c@normal
                points=(points-g)@b.T+g+np.array(shift)
                result.append((points,uv,tex,b@normal))
        return result
    poses={p:posed(p) for p in (0,.35,.70,.85,1)}
    allpoints=np.concatenate([t[0] for ts in poses.values() for t in ts])
    def render_pose(p,cam,w,hgt):
        ts=poses[p] if p in poses else posed(p)
        return helper['render'](ts,cam,helper['frame'](allpoints,cam,w,hgt),(w,hgt))[0]
    sheet=Image.new('RGB',(1440,1050),'#111925');d=ImageDraw.Draw(sheet)
    d.text((14,10),'W168 AUSTRINGER | exact W123 named solids + UV | OFFLINE diagnostic, not native',fill='white')
    for row,cam in enumerate(([1,.1,-.15],[-1,.30,.55],[.35,.30,1])):
        for col,p in enumerate((0,.35,1)):
            sheet.paste(render_pose(p,cam,480,300),(col*480,50+row*330))
            d.text((col*480+12,35+row*330),f'p={p:.2f} / '+('side','rear oblique','grip-facing oblique')[row],fill='white')
    d.text((14,1030),'114 fixed body + 12 moving cylinder = 126; cylinder frame/breech stay fixed. No hands/IK.',fill='white')
    story=Image.new('RGB',(1600,1440),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL AUSTRINGER GAMEPLAY | Aztecross TPWRjqb_O5U | source seconds | dark/silver appearance: motion only',fill='white')
    for i,f in enumerate(reference['frames']):
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));x=(i%4)*400;y=40+(i//4)*260
        story.paste(im,(x,y));draw.text((x+8,y+228),f"{f['timestampSeconds']:.3f}s",fill='white')
    draw.text((12,830),'AUTHORED MODEL | W123 default paint | open / raised hold / loader-contact gesture / flick close | no cartridge/hand claim',fill='white')
    for i,p in enumerate((0,.15,.35,.70,.85,1)):
        x=(i%3)*533;y=865+(i//3)*280
        story.paste(render_pose(p,[-1,.25,.45],533,250),(x,y));draw.text((x+8,y+250),f'p={p:.2f}',fill='white')
    return png(sheet),png(story)

def generate():
    source=json.loads((ROOT/SOURCE).read_bytes());twohand=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if sha((ROOT/SOURCE).read_bytes())!=SOURCE_SHA256: raise ValueError('Current cleaned source drift')
    if len(source['elements'])!=126 or [source['elements'][i]['name'] for i in MOVING]!=list(NAMES) or [source['elements'][i]['name'] for i in FIXED_FRAME]!=['Cylinder_lower_frame','Breech','Top_frame','Top_gold_rod']: raise ValueError('W123 cylinder partition drift')
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
    inputs=[Path('art/weapons/w123/austringer/design.json'),Path('art/weapons/w123/austringer/manifest.json'),SOURCE,TWOHAND,ITEM,TEXTURE,ART/'motion-reference.json',Path('scripts/generate_reload_w168_austringer.py'),Path('scripts/generate_surface_w123_hammerhead.py')]
    emit(ART/'manifest.json',dict(
        stage='W168',weapon='austringer',itemModel='destiny:'+KEY,
        ownedFiles=107,generatedFiles=90,packFiles=87,staticParts=2,
        parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,
        firstPersonContexts=list(FP),sourceElements=126,bodyElements=114,
        movingElements=12,maxAssembledElements=126,elementLimit=1000,
        movingIndices=list(MOVING),movingNames=list(NAMES),
        fixedFrameIndices=list(FIXED_FRAME),
        partitionRationale='Receiver semantic group includes cylinder and fixed frame. Only Cylinder_0..3 and front/rear cylinder bands 32..43 swing; Cylinder_lower_frame, Breech, Top_frame, Top_gold_rod 44..47 stay fixed. No geometry or UV edits.',
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),
        sourceElementsAndUVSha256=sha(encode(source['elements'])),
        partElementsAndUVSha256={part:sha(encode([e for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='moving')])) for part in ('body','moving')},
        sourceRevision='W129 clean authored solids in weapon_surface_w123',geometryAndUVPreserved=True,
        hipEndpoints=[0,20],
        fallback='Exact canonical items/weapon/austringer graph for non-FP and inactive negative progress; ADS and inspect graph preserved',
        keyframes=KEYS,gripPivot=GRIP,cylinderHinge=HINGE,
        normalizedPhases={'rollOpen':[0,.09],'raiseEjectionGesture':[.09,.29],'openHold':[.29,.50],'lowerLoaderContact':[.50,.76],'closeFlick':[.76,.90],'recover':[.90,1]},
        sourceObservedSeconds=ref['selectedSeconds'],
        timingPolicy='Normalized authored motion only; observed 1.7s window is not a gameplay duration override. Runtime/credit/audio unchanged.',
        rotationConvention='JOML Rx Ry Rz; R_idle * R_body * R_cylinder; cylinder hinge affine before body grip affine; uniform scale once, then twohand carrier compensation',
        referenceConfidence=ref['referenceConfidence'],reference=ref['url'],
        nativeGameplayVerified=False,handIK=False,extractedAnimation=False,
        mechanicsOrAudioChanged=False,
        limitations=ref['limitations']+['Cylinder travels as one rigid assembly; no crane linkage, cases, rounds or speedloader geometry.','Native framing, closed seams and open clearance require master QA.'],
        sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},
        sha256={str(p):sha(b) for p,b in output.items()}))
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
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack files; 114+12=126 elements')
if __name__=='__main__': main()
