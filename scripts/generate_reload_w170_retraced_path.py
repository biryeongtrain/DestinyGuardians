#!/usr/bin/env python3
"""W170 Retraced Path: preserved W150 solids and underslung charge-pack reload.

Motion authored after direct gameplay-frame inspection. Hidden extraction travel
is an explicit guess, not animation/bone extraction. No hands, IK or runtime edits.
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
ART = Path('art/weapons/w170/retraced_path')
KEY = 'weapon_reload_w170_retraced_path/retraced_path'
SOURCE = A/'models/weapon_surface_w123/retraced_path.json'
TWOHAND = A/'models/weapon/trace_rifle/retraced_path_twohand.json'
ITEM = A/'items/weapon/retraced_path.json'
TEXTURE = A/'textures/item/weapon/w123/retraced_path.png'
FP = ('firstperson_righthand', 'firstperson_lefthand')
# W150's existing semantic magazine group, not its fixed circular power discs.
# Despite its historical name, magazine_well is the full tilted black pack solid
# extending to the floorplate. Receiver_solid and sweeping_receiver_lower are
# the fixed enclosure; selecting only the foot would leave a floating empty box.
MOVING = (78,79,80,81)
NAMES = ('magazine_well','magazine_foot','magazine_blue_edge_-1','magazine_blue_edge_1')
FIXED_HOUSING = (17,19,21,22,25,26,33,35,37,38,41,42,49,74,75)
FIXED_NAMES = ('upper_rail_-1','lower_rail_-1','upper_broad_casing_-1','lower_broad_casing_-1',
 'sweeping_receiver_-1','sweeping_receiver_lower_-1','upper_rail_1','lower_rail_1',
 'upper_broad_casing_1','lower_broad_casing_1','sweeping_receiver_1','sweeping_receiver_lower_1',
 'receiver_solid','rear_action','upper_action_spine')
GRIP = (8,9.145,9.61)  # Existing pistol_grip rotation origin, never recentered.
PACK_INSERTION_ANCHOR = (8,9.12,3.55)  # Existing magazine beam's receiver-side end.
# Pack axis follows W150 beam from [8,9.12,3.55] to [8,5.34,4.42].
# Actual Y8qyeBBXBgA 247.15..248.85: dip, upward side roll, underside
# hand access, replacement/base press, recovery. All numeric poses are authored.
# Hidden downward pack withdrawal/reinsertion is explicitly low-confidence.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.09,(-7,-3,4),(-.08,-.12,0),(0,0,0)),
 (.23,(39,-10,23),(-.18,.12,-.20),(0,-.35,.080555556)),
 (.35,(40,-10,24),(-.18,.12,-.20),(0,-4.5,1.035714286)),
 (.51,(39,-10,24),(-.18,.10,-.20),(0,-4.5,1.035714286)),
 (.62,(37,-10,23),(-.17,.10,-.20),(0,-2.5,.575396825)),
 (.70,(39,-10,24),(-.18,.15,-.20),(0,0,0)),
 (.76,(43,-10,25),(-.18,.25,-.20),(0,0,0)),
 (.84,(34,-8,20),(-.12,.08,-.14),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
)
SOURCE_SHA256 = '74e3b6a7589f09a3763a0f5258dad5fb74feb880a5392751579fbc17480446a8'

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
        if twohand[context]['scale'] != s: raise ValueError('Grip scale mismatch')
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
            # W134 uses axis/angle element records; the shared offline helper
            # consumes xyz records. Convert a diagnostic copy only.
            diagnostic=copy.deepcopy(e)
            rot=diagnostic.get('rotation',{})
            if 'axis' in rot:
                diagnostic['rotation']={'origin':rot['origin'],rot['axis']:rot['angle']}
            local=h['model_triangles']({'part':{'elements':[diagnostic]}},texture)
            delta=np.array(offset if i in MOVING else [0,0,0])
            for tri in local:
                points,uv,tex,normal=tri
                points=(np.asarray(points)+delta-g)@b.T+g+np.array(shift)
                ts.append((points,uv,tex,b@normal))
        points=np.concatenate([t[0] for t in ts])
        return h['render'](ts,cam,h['frame'](points,cam,w,hgt),(w,hgt))[0]
    sheet=Image.new('RGB',(1440,1050),'#111925');d=ImageDraw.Draw(sheet)
    d.text((14,10),'W170 RETRACED PATH | W150 clean W123 exact solids/UV | OFFLINE textured diagnostic, not native',fill='white')
    for row,cam in enumerate(([1,.15,-.35],[-1,.30,.55],[.35,.30,1])):
        for col,p in enumerate((0,.45,1)):
            sheet.paste(render_pose(p,cam,480,300),(col*480,50+row*330))
            d.text((col*480+12,35+row*330),f'p={p:.2f} / '+('muzzle oblique','rear oblique','grip-facing oblique')[row],fill='white')
    d.text((14,1030),'95 fixed + 4 charge-pack solids = 99; rails/receiver/discs fixed. Hidden pack travel is an authored guess.',fill='white')
    story=Image.new('RGB',(1600,1440),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL VIDEO FRAMES | Y8qyeBBXBgA | source seconds | Retraced Path underside hand access; extraction partly occluded',fill='white')
    for i,f in enumerate(reference['frames']):
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));x=(i%4)*400;y=40+(i//4)*260
        story.paste(im,(x,y));draw.text((x+8,y+228),f"{f['timestampSeconds']:.3f}s",fill='white')
    draw.text((12,830),'AUTHORED MODEL SAMPLES | dip / upward side roll / guessed hidden pack exchange / base press / recovery | NO hands, IK or extracted bones',fill='white')
    for i,p in enumerate((0,.2,.4,.6,.75,1)):
        x=(i%3)*533;y=865+(i//3)*280
        story.paste(render_pose(p,[1,.25,-.45],533,250),(x,y));draw.text((x+8,y+250),f'p={p:.2f}',fill='white')
    return png(sheet),png(story)

def generate():
    source=json.loads((ROOT/SOURCE).read_bytes());twohand=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if sha((ROOT/SOURCE).read_bytes())!=SOURCE_SHA256: raise ValueError('Current clean source drift')
    if len(source['elements'])!=99 or [source['elements'][i]['name'] for i in MOVING]!=list(NAMES) or [source['elements'][i]['name'] for i in FIXED_HOUSING]!=list(FIXED_NAMES): raise ValueError('W150 pack/housing partition drift')
    design=json.loads((ROOT/'art/weapons/w123/retraced_path/design.json').read_bytes())
    if design['revision']!='W150' or [p['geometry']['name'] for p in design['parts'] if p['group']=='magazine']!=list(NAMES): raise ValueError('Existing semantic magazine provenance drift')
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
    inputs=[Path('art/weapons/w123/retraced_path/design.json'),Path('art/weapons/w123/retraced_path/manifest.json'),SOURCE,TWOHAND,ITEM,TEXTURE,ART/'motion-reference.json',Path('scripts/generate_reload_w170_retraced_path.py'),Path('scripts/generate_surface_w123_hammerhead.py')]
    emit(ART/'manifest.json',dict(
        stage='W170',weapon='retraced_path',itemModel='destiny:'+KEY,
        ownedFiles=106,generatedFiles=90,packFiles=87,staticParts=2,
        parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,
        firstPersonContexts=list(FP),sourceElements=99,bodyElements=95,
        movingElements=4,maxAssembledElements=99,elementLimit=1000,
        movingIndices=list(MOVING),movingNames=list(NAMES),fixedHousingIndices=list(FIXED_HOUSING),fixedHousingNames=list(FIXED_NAMES),
        partitionRationale='W150 semantic magazine group 78..81: complete tilted underslung black charge-pack, silver foot and blue edges. Historical magazine_well name describes this authored pack solid, not a separate fixed socket. Fixed receiver_solid, sweeping receiver shell, rails, rear action, spine and ALL 24 circular power-disc solids remain body. Selection informed by clean design group and visible gameplay underside; exact original animation bone/component segmentation unknown.',
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceElementsAndUVSha256=sha(encode(source['elements'])),
        partElementsAndUVSha256={part:sha(encode([e for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='moving')])) for part in ('body','moving')},
        sourceRevision='W150 semantic filled solids in weapon_surface_w123 (verified current, not W136)',geometryAndUVPreserved=True,
        hipEndpoints=[0,20],fallback='Exact canonical items/weapon/retraced_path graph for non-FP and inactive negative progress; ADS/inspect graph preserved',
        keyframes=KEYS,gripPivot=GRIP,packInsertionAnchor=PACK_INSERTION_ANCHOR,
        normalizedPhases={'dip':[0,.09],'raiseRollAccess':[.09,.23],'withdrawGuess':[.23,.35],'occludedExchangeGuess':[.35,.51],'insertGuess':[.51,.70],'basePress':[.70,.84],'recover':[.84,1]},
        sourceObservedSeconds=ref['selectedSeconds'],
        motionAuthorship='Retraced Path-specific observed dip, side roll and base press; independent pack translation is a disclosed approximation of hidden travel. Established W168 rigid-display math/graph reused, not its body/magazine curve.',
        timingPolicy='Normalized authored motion only; observed 1.70s window is not a reload duration/perk certification or runtime override.',
        rotationConvention='JOML Rx Ry Rz; R_idle * R_body; pack translation along source tilted insertion axis, rotated by body and idle, uniformly scaled once, then twohand carrier compensation',
        referenceConfidence=ref['referenceConfidence'],reference=ref['url'],
        nativeGameplayVerified=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration={'currentRuntimeSupportsRetracedPath':False,'expectedExistingRouteCount':14,'requiresNewMasterRoute':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:weapon_reload_w170_retraced_path/retraced_path','preserve':'All 14 existing routes including W159 Ace and W169 Duke; master owns adding Retraced Path as route 15'},
        nativeQueue=['Both FP hands, native and twohand: dip, roll, underside pack visibility, reseat seam and recovery','Negative progress/inactive and non-FP contexts canonical; ADS/inspect canonical transitions','Master adds Retraced Path route plus reload cancel/complete/equip restore; audio/ammo/timing/perk speed unchanged','Brief 10-20 displays for obvious defects; no performance certification from offline PNG'],
        limitations=ref['limitations']+['No separate fixed socket geometry was added: existing receiver and shell form the housing.','One rigid pack is reused to represent replacement; no spawned duplicate or original bone rig.'],
        sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths(): raise ValueError('Output ownership mismatch')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    output=generate()
    scope=Path('/private/tmp/w170-manifest.json')
    if scope.exists():
        owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w170-retraced-reload'))
        if not {str(p) for p in output}<=owned: raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b: raise SystemExit('Asset differs: '+str(p))
        else: dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack files; 95+4=99 elements')
if __name__=='__main__': main()
