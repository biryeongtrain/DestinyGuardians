#!/usr/bin/env python3
"""W173 Salvo: authored break-open reload from inspected waod2MdK13w gameplay.

No extracted bones, hands, IK, runtime, timing, ammo or audio modifications.
"""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w173/salvager_s_salvo')
KEY = 'weapon_reload_w173_salvager_s_salvo/salvager_s_salvo'
SOURCE = A/'models/weapon_surface_w123/salvager_s_salvo.json'
TWOHAND = A/'models/weapon/grenade_launcher/salvager_s_salvo_twohand.json'
ITEM = A/'items/weapon/salvager_s_salvo.json'
TEXTURE = A/'textures/item/weapon/w123/salvager_s_salvo.png'
DESIGN = Path('art/weapons/w123/salvager_s_salvo/design.json')
SURFACE = Path('src/main/resources/weapon_surface_w123/manifest.json')
FP = ('firstperson_righthand','firstperson_lefthand')
PARTS = ('body','barrel','round')
GRIPS = ('native','twohand')
SOURCE_SHA256 = '4b0d239a58eea1b63837f2f42de60d75154a0f59c524ed7b8a4cd6ee84a553ec'
# Moving fore-end includes cradle, foregrip, rail and sights. The four solid
# breech_plug elements are the fixed receiver face, NOT a cartridge in the bore.
BARREL = tuple(range(32))+tuple(range(36,58))+tuple(range(73,76))+tuple(range(85,101))
GRIP = (8.,8.155,8.25)  # Existing grip_main origin, never recentered.
HINGE = (8.,10.91,4.14)  # Authored lower receiver / barrel seam.
ROUND_CENTER = (8.,12.27,2.85)
ROUND_VISIBLE = tuple(range(9,14))  # p=.45 .. .65, hidden before closure.
# p, body Euler, carrier shift, hinge X degrees, round-local approach.
# Salvo source: open by 84.55, round approach 84.85, closure 85.15, HIP 85.60.
KEYS = (
 (0., (0,0,0), (0,0,0), 0., (0,0,0)),
 (.10,(3,-3,-5),(.05,-.08,-.04),0.,(0,0,0)),
 (.20,(10,-7,-11),(.12,-.15,-.10),-24.,(0,0,0)),
 (.30,(17,-10,-16),(.18,-.20,-.15),-48.,(0,0,0)),
 (.40,(15,-10,-15),(.18,-.20,-.15),-48.,(-3.2,.6,3.5)),
 (.45,(14,-10,-15),(.18,-.20,-.15),-48.,(-2.4,.4,3.0)),
 (.53,(14,-10,-15),(.18,-.20,-.15),-48.,(0.,0.,2.8)),
 (.65,(14,-10,-15),(.18,-.20,-.15),-48.,(0.,0.,0.)),
 (.69,(14,-10,-15),(.18,-.20,-.15),-48.,(0,0,0)),
 (.76,(10,-7,-10),(.12,-.12,-.10),0.,(0,0,0)),
 (.86,(3,-2,-3),(.04,-.04,-.03),0.,(0,0,0)),
 (1., (0,0,0), (0,0,0), 0., (0,0,0)),
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
    if not math.isfinite(p) or not 0 <= p <= 1: raise ValueError(p)
    for a,b in zip(KEYS,KEYS[1:]):
        if p <= b[0]:
            t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple(a[k]+(b[k]-a[k])*t if k==3 else [a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3,4))
    raise ValueError(p)

def pose_display(original,twohand,p,part,grip):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,hinge,approach=sample(p)
    b=xyz(angles); h=sub(GRIP,(8,8,8)); q=sub(HINGE,(8,8,8))
    child=xyz((hinge,0,0)) if part!='body' else xyz((0,0,0))
    local=sub(h,vec(b,h))
    if part!='body':
        # B around grip, then child H around hinge. Round follows same H and
        # moves along its local bore axis only after lateral support-side entry.
        local=add(local,vec(b,sub(q,vec(child,q))))
        if part=='round': local=add(local,vec(mul(b,child),approach))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context]; base=xyz(idle['rotation']);s=idle['scale']
        if s!=twohand[context]['scale'] or len(set(s))!=1: raise ValueError('Uniform matching FP scale required')
        rotation=mul(base,mul(b,child))
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(vec(comp,position),sub(twohand[context]['translation'],vec(comp,idle['translation'])))
            rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def round_elements(source):
    # Six authored volumes form a short hex cartridge and its shallow rim.
    # Reuse the existing neutral metal face UV; no new atlas or paint changes.
    faces=source['elements'][75]['faces']
    elements=[]
    for name,r,z0,z1 in (('case',.61,1.65,4.05),('rim',.68,4.05,4.22)):
        for angle in (0,60,120):
            elements.append(dict(name=f'cosmetic_round_{name}_{angle}',
                **{'from':[8-r,12.27-r/math.sqrt(3),z0], 'to':[8+r,12.27+r/math.sqrt(3),z1]},
                rotation=dict(origin=[8,12.27,2.85],axis='z',angle=angle),faces=copy.deepcopy(faces)))
    return elements

def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in PARTS for grip in GRIPS)
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}

def previews(source,reference,output):
    """Reconstruct emitted child JSON with independent explicit-axis matrices.

    Raster helper reads face UV/element rotation only. Not native or hand QA.
    """
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles={part:helper['model_triangles']({part:json.loads(output[A/f'models/{KEY}_{part}.json'])},texture) for part in PARTS}
    def rotation(a):
        x,y,z=np.radians(a)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i,grip='native'):
        ts=[]
        for part in PARTS:
            if part=='round' and i not in ROUND_VISIBLE: continue
            d=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])['display']['firstperson_righthand']
            rr=rotation(d['rotation']);ss=np.array(d['scale']);tt=np.array(d['translation'])
            for points,uv,tex,normal in triangles[part]: ts.append(((np.asarray(points)-8)*ss@rr.T+tt,uv,tex,rr@normal))
        return ts
    def raster(ts,cam,w,h,extent=None):
        if extent is None: extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    comparison=Image.new('RGB',(1600,1120),'#111925');draw=ImageDraw.Draw(comparison)
    draw.text((12,10),'W173 SALVAGER SALVO | emitted JSON independently reconstructed | OFFLINE, no native hands / IK',fill='white')
    for row,cam in enumerate(([1,.3,-.5],[-1,.3,.7],[.45,.5,1])):
        groups=[posed(i) for i in (0,7,10,20)]
        extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,320)
        for col,(i,ts) in enumerate(zip((0,7,10,20),groups)):
            comparison.paste(raster(ts,cam,400,320,extent),(col*400,50+row*345))
            draw.text((col*400+10,35+row*345),f'p={i/20:.2f} / '+('muzzle oblique','rear breech oblique','grip oblique')[row],fill='white')
    draw.text((12,1090),'28 fixed + 73 hinged = 101 original elements; +6 round only during insertion = 107 maximum. Same camera scale per row.',fill='white')
    story=Image.new('RGB',(1600,1620),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL waod2MdK13w Salvo gameplay vs AUTHORED | original source seconds | OFFLINE orthographic model, no hands',fill='white')
    start,end=reference['selectedSeconds']
    for i,f in enumerate(reference['frames']):
        x=i%4*400;y=40+i//4*520
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
        index=max(0,min(20,round((f['timestampSeconds']-start)/(end-start)*20)))
        draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.3f}s / frame {f['sourceFrameIndex']}",fill='white')
        story.paste(raster(posed(index),[1,.2,.4],400,225),(x,y+260))
        draw.text((x+8,y+488),f'AUTHORED p={index/20:.2f} | '+f['phase'],fill='white')
    draw.text((12,1600),'Observed open/insert/close cadence; exact hinge angle, hand-hidden round travel and normalized timing are authored estimates.',fill='white')
    return png(comparison),png(story)

def generate():
    source=json.loads((ROOT/SOURCE).read_bytes());twohand=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if sha((ROOT/SOURCE).read_bytes())!=SOURCE_SHA256: raise ValueError('Canonical source drift')
    design=json.loads((ROOT/DESIGN).read_bytes())
    if design['revision']!='W149' or len(source['elements'])!=101: raise ValueError('W149 source revision drift')
    if [p['geometry']['name'] for p in design['parts']]!=[e['name'] for e in source['elements']]: raise ValueError('Semantic partition drift')
    rules=json.loads((ROOT/SURFACE).read_bytes())['targets']
    rule=next(r for r in rules if r['path']=='assets/destiny/models/weapon/grenade_launcher/salvager_s_salvo.json')
    if rule['replacement']!='assets/destiny/models/weapon_surface_w123/salvager_s_salvo.json' or rule['replacementSha256']!=SOURCE_SHA256: raise ValueError('Selected item surface drift')
    ref=json.loads((ROOT/ART/'motion-reference.json').read_bytes())
    if not ref['inspectedActualFrames'] or len(ref['frames'])!=12: raise ValueError('Missing inspected reference')
    for f in ref['frames']:
        if sha((ROOT/f['path']).read_bytes())!=f['sha256']: raise ValueError('Reference frame drift')
    output={}
    def emit(p,v):output[p]=encode(v)
    for part in PARTS:
        geo={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        geo['elements']=round_elements(source) if part=='round' else [copy.deepcopy(e) for i,e in enumerate(source['elements']) if (i in BARREL)==(part=='barrel')]
        emit(A/f'models/{KEY}_{part}.json',geo)
    entries=[]
    for i in range(21):
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],twohand,i/20,part,grip)))
        def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in PARTS if part!='round' or i in ROUND_VISIBLE])
        entries.append(dict(threshold=i/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    wrapper=copy.deepcopy(item)
    wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model'])))],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    comparison,story=previews(source,ref,output);output[ART/'comparison.png']=comparison;output[ART/'storyboard.png']=story
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,DESIGN,SURFACE,ART/'motion-reference.json',Path('scripts/generate_reload_w173_salvager_s_salvo.py'),Path('scripts/generate_surface_w123_hammerhead.py')]
    emit(ART/'manifest.json',dict(stage='W173',weapon='salvager_s_salvo',itemModel='destiny:'+KEY,
        ownedFiles=149,generatedFiles=133,packFiles=130,staticParts=3,parentDisplayChildren=126,frames=21,progressFloatIndex=1,gripFlagIndex=0,
        sourceRevision='W149 clean semantic solids selected through weapon_surface_w123 manifest',sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=SOURCE_SHA256,
        sourceElements=101,bodyElements=28,barrelElements=73,roundElements=6,maxAssembledElements=107,elementLimit=1000,
        barrelIndices=list(BARREL),barrelNames=[source['elements'][i]['name'] for i in BARREL],
        fixedNames=[e['name'] for i,e in enumerate(source['elements']) if i not in BARREL],
        partitionRationale='Barrel, bands, muzzle, forward cradle/straps, foregrip, rail and both sights hinge as one fore-end. Receiver, four breech-face plugs, trigger guard, pistol grip and stock stay rigid. Breech face is not a cartridge. One six-volume cosmetic round appears only at samples 9..13.',
        geometryAndUVPreserved=True,newTexture=False,roundUVSource='Existing steel foregrip_socket face UV; six authored cosmetic volumes only',
        gripPivot=GRIP,hingePivot=HINGE,roundCenter=ROUND_CENTER,roundVisibleSamples=list(ROUND_VISIBLE),keyframes=KEYS,hipEndpoints=[0,20],
        normalizedPhases={'unlock':[0,.10],'open':[.10,.30],'openDwell':[.30,.45],'roundApproach':[.45,.53],'insert':[.53,.65],'handClear':[.65,.69],'close':[.69,.76],'recover':[.76,1]},
        reference=ref['url'],sourceObservedSeconds=ref['selectedSeconds'],referenceConfidence=ref['referenceConfidence'],
        motionAuthorship='Weapon-specific authored grip-relative body cant, lower breech hinge and support-side single round insertion from inspected actual Salvo gameplay. No magazine exchange, bolt sweep, extracted animation, IK or bones.',
        rotationConvention='JOML Rx Ry Rz. R_idle * R_body about original grip pivot, then R_hinge about lower breech. Round follows hinge plus local approach. Uniform scale once; twohand carrier compensation.',
        fallback='Exact canonical items/weapon/salvager_s_salvo graph for every non-FP context and negative inactive progress. Existing ADS/inspect and hand_animation_on_swap retained.',
        timingPolicy='Normalized visual-only phases, existing runtime timing/perk credit/ammo/audio unchanged',
        comparisonMethod='Independent explicit-axis reconstruction of emitted native child display JSON; muzzle, rear breech and grip obliques; actual 12-frame storyboard',
        nativeGameplayVerified=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration={'intendedRouteNumber':18,'expectedExistingRouteCount':17,'requiresNewMasterRoute':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY},
        nativeQueue=['Both FP hands/grips: fixed pistol grip, hinge seam, front foregrip moving with fore-end, open dwell, single round entry, close and exact HIP recovery',
        'Inactive negative progress and all non-FP: canonical graph; ADS/inspect transitions and visible sights unchanged',
        'Master route 18, cancel/complete/equip restore and existing 17 routes; 3 master GameTests; existing timing/ammo/audio unchanged',
        'Brief 10-20 displayed weapons for visible defects; offline renders do not prove native grip or performance'],
        limitations=ref['limitations'],sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},
        sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths():raise ValueError('Output path mismatch')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    output=generate()
    scope=Path('/private/tmp/w173-manifest.json')
    if scope.exists():
        owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w173-salvo-reload'))
        if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 130 pack paths; 28+73+6=107 maximum elements')
if __name__=='__main__':main()
