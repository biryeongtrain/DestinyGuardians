#!/usr/bin/env python3
"""W171 Aishas Embrace: preserved W142 solids and rear magazine reload.

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
ART = Path('art/weapons/w171/aishas_embrace')
KEY = 'weapon_reload_w171_aishas_embrace/aishas_embrace'
SOURCE = A/'models/weapon_surface_w123/aishas_embrace.json'
TWOHAND = A/'models/weapon/scout_rifle/aishas_embrace_twohand.json'
ITEM = A/'items/weapon/aishas_embrace.json'
TEXTURE = A/'textures/item/weapon/w123/aishas_embrace.png'
FP = ('firstperson_righthand', 'firstperson_lefthand')
# Current W142 semantic magazine group. Fixed palm_block/grip/stock/receiver
# never moves independently. Geometry, UV, paint and rotation origins preserved.
MOVING = (56,57,58,59)
NAMES = ('magazine_feed','magazine_curve','magazine_lower','magazine_floor')
FIXED_HOUSING = (30,35,36,37,38,39,45,46,47,48)
FIXED_NAMES = ('receiver_core','guard_top_bridge','curved_stock_segment_0',
 'curved_stock_segment_1','curved_stock_segment_2','curved_stock_segment_3',
 'grip_frontstrap','palm_block','grip_heel','gold_upper_palm_insert')
GRIP = (8.0,8.850000000000001,10.265)  # source grip_frontstrap rotation origin
MAG_ANCHOR = (8.0,7.725,11.385000000000002)  # source magazine_feed rotation origin
# Source feed top face center after its existing element rotation. Derived point,
# not an extracted Destiny socket/bone. Withdrawal follows negative local feed Y.
PACK_INSERTION_ANCHOR = (8.0,8.27,11.72)
MAG_AXIS = (0,-math.cos(math.radians(31.578165)),-math.sin(math.radians(31.578165)))
def withdrawal(distance): return tuple(distance*v for v in MAG_AXIS)
# Actual ytb7f7nyrl8 84.60..86.40: raise/roll, rear mag down, replacement
# from below, reseat, support arm across action, recover. All numbers authored.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.09,(16,-8,10),(.10,.05,-.08),(0,0,0)),
 (.20,(61,-14,24),(.22,.15,-.18),withdrawal(.3)),
 (.30,(62,-14,25),(.22,.15,-.18),withdrawal(4.8)),
 (.38,(60,-13,25),(.22,.15,-.18),withdrawal(4.8)),
 (.46,(59,-12,24),(.22,.15,-.18),withdrawal(2.5)),
 (.54,(58,-12,24),(.22,.20,-.18),(0,0,0)),
 (.62,(28,-5,10),(.14,.12,-.10),(0,0,0)),
 (.78,(25,-7,11),(.12,.10,-.08),(0,0,0)),
 (.88,(15,-4,6),(.07,.04,-.04),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
)
SOURCE_SHA256 = 'a0dec168016ca1d3245519b93ffc74bb1df207a929063d13db74540b2dce5c5d'

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
    anchor=sub(MAG_ANCHOR,(8,8,8))
    # Place the unchanged magazine anchor at its body-carried position plus
    # source-local withdrawal, then subtract its rotated child-space anchor.
    # This is translation only; no recentering or extra magazine spin.
    local=(sub(add(h,vec(body,add(sub(anchor,h),offset))),vec(body,anchor))
           if part=='moving' else sub(h,vec(body,h)))
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
            # Shared offline helper consumes xyz rotation records; retain
            # source W142 xyz records, with axis/angle compatibility if needed.
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
    d.text((14,10),'W171 AISHAS EMBRACE | W142 clean source exact solids/UV | OFFLINE textured diagnostic, not native',fill='white')
    for row,cam in enumerate(([1,.15,-.35],[-1,.30,.55],[.35,.30,1])):
        for col,p in enumerate((0,.45,1)):
            sheet.paste(render_pose(p,cam,480,300),(col*480,50+row*330))
            d.text((col*480+12,35+row*330),f'p={p:.2f} / '+('muzzle oblique','rear oblique','grip-facing oblique')[row],fill='white')
    d.text((14,1030),'88 fixed + 4 magazine solids = 92; grip/stock/receiver fixed. Hidden travel is an authored guess.',fill='white')
    story=Image.new('RGB',(1600,1440),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL VIDEO FRAMES | ytb7f7nyrl8 | source seconds | Aishas Embrace rear magazine exchange; hand contact partly occluded',fill='white')
    for i,f in enumerate(reference['frames']):
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));x=(i%4)*400;y=40+(i//4)*260
        story.paste(im,(x,y));draw.text((x+8,y+228),f"{f['timestampSeconds']:.3f}s",fill='white')
    draw.text((12,830),'AUTHORED MODEL SAMPLES | raise and roll / rear magazine exchange / reseat / action-area hand sweep / recovery | NO hands, IK or extracted bones',fill='white')
    for i,p in enumerate((0,.2,.4,.6,.75,1)):
        x=(i%3)*533;y=865+(i//3)*280
        story.paste(render_pose(p,[1,.25,-.45],533,250),(x,y));draw.text((x+8,y+250),f'p={p:.2f}',fill='white')
    return png(sheet),png(story)

def generate():
    source=json.loads((ROOT/SOURCE).read_bytes());twohand=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if sha((ROOT/SOURCE).read_bytes())!=SOURCE_SHA256: raise ValueError('Current clean source drift')
    if len(source['elements'])!=92 or [source['elements'][i]['name'] for i in MOVING]!=list(NAMES) or [source['elements'][i]['name'] for i in FIXED_HOUSING]!=list(FIXED_NAMES): raise ValueError('W142 magazine/housing partition drift')
    design=json.loads((ROOT/'art/weapons/w123/aishas_embrace/design.json').read_bytes())
    if design['revision']!='W142' or [p['geometry']['name'] for p in design['parts'] if p['group']=='magazine']!=list(NAMES): raise ValueError('Existing semantic magazine provenance drift')
    rules=json.loads((ROOT/'src/main/resources/weapon_surface_w123/manifest.json').read_bytes())['targets']
    rule=next(r for r in rules if r['path']=='assets/destiny/models/weapon/scout_rifle/aishas_embrace.json')
    if rule['replacement']!='assets/destiny/models/weapon_surface_w123/aishas_embrace.json' or rule['replacementSha256']!=SOURCE_SHA256: raise ValueError('Selected native source mapping drift')
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
    inputs=[Path('src/main/resources/weapon_surface_w123/manifest.json'),Path('art/weapons/w123/aishas_embrace/design.json'),Path('art/weapons/w123/aishas_embrace/manifest.json'),SOURCE,TWOHAND,ITEM,TEXTURE,ART/'motion-reference.json',Path('scripts/generate_reload_w171_aishas_embrace.py'),Path('scripts/generate_surface_w123_hammerhead.py')]
    emit(ART/'manifest.json',dict(
        stage='W171',weapon='aishas_embrace',itemModel='destiny:'+KEY,
        ownedFiles=106,generatedFiles=90,packFiles=87,staticParts=2,
        parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,
        firstPersonContexts=list(FP),sourceElements=92,bodyElements=88,
        movingElements=4,maxAssembledElements=92,elementLimit=1000,
        movingIndices=list(MOVING),movingNames=list(NAMES),fixedHousingIndices=list(FIXED_HOUSING),fixedHousingNames=list(FIXED_NAMES),
        partitionRationale='Existing W142 magazine group 56..59: complete magazine feed, curve, lower and floor. Source palm_block, grip_frontstrap, grip_heel, stock and receiver remain fixed. No added hidden insert; exact original rig segmentation unknown.',
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceElementsAndUVSha256=sha(encode(source['elements'])),
        partElementsAndUVSha256={part:sha(encode([e for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='moving')])) for part in ('body','moving')},
        sourceRevision='W142 semantic filled solids in weapon_surface_w123 (current selected source verified against surface manifest)',geometryAndUVPreserved=True,
        hipEndpoints=[0,20],fallback='Exact canonical items/weapon/aishas_embrace graph for non-FP and inactive negative progress; ADS/inspect graph preserved',
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,packInsertionAnchor=PACK_INSERTION_ANCHOR,magazineExtractionAxis=MAG_AXIS,
        normalizedPhases={'raiseRollAccess':[0,.20],'withdrawGuess':[.20,.30],'exchangeBelowFrame':[.30,.38],'insertGuess':[.38,.54],'actionAreaSweep':[.54,.78],'recover':[.78,1]},
        sourceObservedSeconds=ref['selectedSeconds'],
        motionAuthorship='Aisha-specific observed raise/roll, rear-magazine exchange, support-arm action sweep and recovery. Independent magazine travel is a disclosed authored approximation. Established W170/W168 rigid-display math/graph reused, not their pose curves.',
        timingPolicy='Normalized authored motion only; observed 1.80s combat window is not a reload duration/perk certification or runtime override.',
        rotationConvention='JOML Rx Ry Rz; R_idle * R_body about source grip pivot; magazine travel along existing rotated feed axis using source magazine anchor, body and idle rotations, uniform scale once, then twohand carrier compensation',
        referenceConfidence=ref['referenceConfidence'],reference=ref['url'],
        nativeGameplayVerified=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration={'currentRuntimeSupportsAisha':False,'expectedExistingRouteCount':15,'requiresNewMasterRoute':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:weapon_reload_w171_aishas_embrace/aishas_embrace','preserve':'All 15 existing routes including W170 Retraced Path; master adds Aisha as intended route 16'},
        nativeQueue=['Both FP hands, native and twohand: raise, roll, rear magazine separation, fixed stock/grip, reseat seam and recovery','Negative progress/inactive and all non-FP contexts canonical; ADS/inspect canonical transitions','Master adds route 16 plus reload cancel/complete/equip restore; audio/ammo/timing/perk speed unchanged','Brief 10-20 displays for obvious defects; no performance certification from offline PNG'],
        limitations=ref['limitations']+['No hidden insert added; existing fixed palm and receiver form housing.','One magazine solid assembly reused as replacement; no spawned duplicate or original bone rig.'],
        sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths(): raise ValueError('Output ownership mismatch')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    output=generate()
    scope=Path('/private/tmp/w171-manifest.json')
    if scope.exists():
        owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w171-aisha-reload'))
        if not {str(p) for p in output}<=owned: raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b: raise SystemExit('Asset differs: '+str(p))
        else: dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack files; 88+4=92 elements')
if __name__=='__main__': main()
