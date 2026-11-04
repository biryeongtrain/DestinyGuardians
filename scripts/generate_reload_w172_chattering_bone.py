#!/usr/bin/env python3
"""W172 Chattering Bone: W128 clean solids, authored rear magazine reload.

Observed ZWqQimJFVb4 gameplay, not extracted animation. No hands, IK or runtime edits.
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
ART = Path('art/weapons/w172/chattering_bone')
KEY = 'weapon_reload_w172_chattering_bone/chattering_bone'
SOURCE = A/'models/weapon_surface_w123/chattering_bone.json'
TWOHAND = A/'models/weapon/pulse_rifle/chattering_bone_twohand.json'
ITEM = A/'items/weapon/chattering_bone.json'
TEXTURE = A/'textures/item/weapon/w123/chattering_bone.png'
FP = ('firstperson_righthand', 'firstperson_lefthand')
MOVING = (59,60,61)
NAMES = ('magazine_root','magazine_main','magazine_foot')
FIXED_HOUSING = (14,36,37,48,49,50,51,62,63,64)
FIXED_NAMES = ('receiver_violet_core','receiver_wrist_core','grip_upper_socket',
 'stock_comb','stock_main','stock_lower_front','stock_lower_rear',
 'grip_wrist','grip_main','grip_heel')
GRIP = (8.,8.16,8.67)  # Existing W128 grip_main rotation origin.
MAG_ANCHOR = (8.,8.98,11.75)  # Existing magazine_root rotation origin.
MAG_AXIS = (0.,-math.cos(math.radians(15)),-math.sin(math.radians(15)))
def withdrawal(distance): return tuple(distance*v for v in MAG_AXIS)
# Chattering Bone-specific near-vertical access, rear exchange, reseat, return.
# Observed source window 87.166667..88.333333s. Hidden travel authored; no bolt sweep.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.10,(43,-18,-10),(.10,.02,-.06),(0,0,0)),
 (.19,(79,-23,-17),(.20,.06,-.12),withdrawal(.15)),
 (.29,(80,-23,-17),(.20,.06,-.12),withdrawal(4.2)),
 (.48,(78,-22,-16),(.20,.06,-.12),withdrawal(4.2)),
 (.57,(78,-22,-16),(.20,.06,-.12),withdrawal(3.5)),
 (.71,(77,-22,-16),(.20,.08,-.12),(0,0,0)),
 (.78,(75,-21,-15),(.18,.08,-.10),(0,0,0)),
 (.87,(39,-11,-7),(.10,.04,-.06),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
)
SOURCE_SHA256 = '13351acc4b518c112fef49c75726cb2b2cfabdf13efaad77368f426f8448b29c'

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

def previews(source,reference,output):
    """Independent child-display reconstruction; offline views, not native QA.

    Uses emitted children and explicit axis matrices instead of pose_display's
    pivot/offset derivation. Existing inert raster helper supplies face UVs.
    """
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles={}
    for part in ('body','moving'):
        parent=json.loads(output[A/f'models/{KEY}_{part}.json'])
        triangles[part]=helper['model_triangles']({part:parent},texture)
    def rotation(a):
        x,y,z=np.radians(a)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i):
        ts=[]
        for part in ('body','moving'):
            disp=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_native.json'])['display']['firstperson_righthand']
            rr=rotation(disp['rotation']);ss=np.array(disp['scale']);tt=np.array(disp['translation'])
            for points,uv,tex,normal in triangles[part]:
                ts.append(((np.asarray(points)-8)*ss@rr.T+tt,uv,tex,rr@normal))
        return ts
    def raster(ts,cam,w,h,extent=None):
        if extent is None: extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    sheet=Image.new('RGB',(1440,1060),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'W172 CHATTERING BONE | independent reconstruction of emitted native display JSON | OFFLINE, no hands / IK',fill='white')
    for row,cam in enumerate(([1,.2,-.45],[-1,.35,.6],[.4,.4,1])):
        ts=[posed(i) for i in (0,9,20)]
        extent=helper['frame'](np.concatenate([t[0] for group in ts for t in group]),cam,480,300)
        for col,(i,group) in enumerate(zip((0,9,20),ts)):
            sheet.paste(raster(group,cam,480,300,extent),(col*480,50+row*330))
            draw.text((col*480+12,35+row*330),f'p={i/20:.2f} / '+('muzzle oblique','rear oblique','grip-facing oblique')[row],fill='white')
    draw.text((12,1035),'87 fixed + 3 rear-magazine elements = 90. Exact W128 geometry / face UV / paint. Common framing per row.',fill='white')
    story=Image.new('RGB',(1600,1620),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL ZWqQimJFVb4 gameplay vs AUTHORED Chattering Bone | source seconds / nearest authored sample | NO native or bone claim',fill='white')
    start,end=reference['selectedSeconds']
    for i,f in enumerate(reference['frames']):
        x=i%4*400;y=40+i//4*520
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
        p=(f['timestampSeconds']-start)/(end-start);index=max(0,min(20,round(p*20)))
        draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.6f}s / frame {f['sourceFrameIndex']}",fill='white')
        story.paste(raster(posed(index),[1,.2,.4],400,225),(x,y+260))
        draw.text((x+8,y+488),f'AUTHORED p={index/20:.2f} | '+f['phase'],fill='white')
    draw.text((12,1600),'Original frame pixels above; authored offline orthographic render below. Hand occlusion and streamer overlay limit exact magazine-path inference.',fill='white')
    return png(sheet),png(story)

def generate():
    source=json.loads((ROOT/SOURCE).read_bytes());twohand=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if sha((ROOT/SOURCE).read_bytes())!=SOURCE_SHA256: raise ValueError('Current clean source drift')
    if len(source['elements'])!=90 or [source['elements'][i]['name'] for i in MOVING]!=list(NAMES) or [source['elements'][i]['name'] for i in FIXED_HOUSING]!=list(FIXED_NAMES): raise ValueError('W128 magazine/housing partition drift')
    design=json.loads((ROOT/'art/weapons/w123/chattering_bone/design.json').read_bytes())
    if design['revision']!='W128' or [p['geometry']['name'] for p in design['parts']['full'] if p['group']=='magazine']!=list(NAMES): raise ValueError('Semantic magazine provenance drift')
    rules=json.loads((ROOT/'src/main/resources/weapon_surface_w123/manifest.json').read_bytes())['targets']
    rule=next(r for r in rules if r['path']=='assets/destiny/models/weapon/pulse_rifle/chattering_bone.json')
    if rule['replacement']!='assets/destiny/models/weapon_surface_w123/chattering_bone.json' or rule['replacementSha256']!=SOURCE_SHA256: raise ValueError('Selected source mapping drift')
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
    comparison,story=previews(source,ref,output);output[ART/'comparison.png']=comparison;output[ART/'storyboard.png']=story
    inputs=[Path('src/main/resources/weapon_surface_w123/manifest.json'),Path('art/weapons/w123/chattering_bone/design.json'),Path('art/weapons/w123/chattering_bone/manifest.json'),SOURCE,TWOHAND,ITEM,TEXTURE,ART/'motion-reference.json',Path('scripts/generate_reload_w172_chattering_bone.py'),Path('scripts/generate_surface_w123_hammerhead.py')]
    emit(ART/'manifest.json',dict(
        stage='W172',weapon='chattering_bone',itemModel='destiny:'+KEY,
        ownedFiles=106,generatedFiles=90,packFiles=87,staticParts=2,
        parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,
        firstPersonContexts=list(FP),sourceElements=90,bodyElements=87,movingElements=3,
        maxAssembledElements=90,elementLimit=1000,
        movingIndices=list(MOVING),movingNames=list(NAMES),fixedHousingIndices=list(FIXED_HOUSING),fixedHousingNames=list(FIXED_NAMES),
        partitionRationale='Existing W128 semantic magazine group 59..61: root, main and foot. All receiver, stock, grip and guard elements remain fixed. No hidden insert or invented geometry.',
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceElementsAndUVSha256=sha(encode(source['elements'])),
        partElementsAndUVSha256={part:sha(encode([e for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='moving')])) for part in ('body','moving')},
        sourceRevision='W128 clean semantic solids selected through weapon_surface_w123 manifest',geometryAndUVPreserved=True,
        hipEndpoints=[0,20],fallback='Exact canonical items/weapon/chattering_bone graph for all non-FP and inactive negative progress; ADS/inspect retained',
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,magazineExtractionAxis=MAG_AXIS,
        normalizedPhases={'raiseForRearAccess':[0,.19],'withdrawGuess':[.19,.29],'exchangeBelowFrame':[.29,.48],'replacementApproachGuess':[.48,.57],'reseat':[.57,.71],'supportHandRelease':[.71,.78],'recover':[.78,1]},
        sourceObservedSeconds=ref['selectedSeconds'],
        motionAuthorship='Chattering Bone-specific near-vertical raise, rear-magazine exchange, lower replacement approach, reseat and recovery, authored from inspected actual gameplay. W171 rigid-display math and graph reused; its Aisha pose curve is not reused.',
        timingPolicy='Normalized visual phases only. The observed combat clip is not a reload/perk-speed certification or runtime override.',
        rotationConvention='JOML Rx Ry Rz; R_idle * R_body about W128 grip_main pivot; magazine withdrawal along source 15-degree feed axis, uniform scale once, twohand carrier compensation',
        comparisonMethod='Independent explicit-axis reconstruction of emitted display children; three oblique cameras with common row framing. Actual-frame storyboard compares nearest 21-sample authored model.',
        referenceConfidence=ref['referenceConfidence'],reference=ref['url'],
        nativeGameplayVerified=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration={'workerBaselineIncludesChatteringBoneRoute':False,'intendedRouteNumber':17,'expectedExistingRouteCount':16,'requiresNewMasterRoute':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'preserve':'All 16 existing routes including W171 Aishas Embrace; master adds Chattering Bone as intended route 17'},
        nativeQueue=['Both FP hands and grips: near-vertical raise, rear magazine separation, fixed receiver/stock/grip, reseat seam, HIP recovery','All non-FP and inactive negative progress canonical; ADS/inspect transitions','Master route 17 plus cancel/complete/equip restore; ammo/audio/timing/perk-speed untouched','Brief 10-20 displayed weapons for obvious defects; offline render is not native or performance proof'],
        limitations=ref['limitations']+['One unchanged magazine assembly represents exchange; no duplicated replacement or hidden insert.'],
        sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths(): raise ValueError('Output ownership mismatch')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    output=generate()
    scope=Path('/private/tmp/w172-manifest.json')
    if scope.exists():
        owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w172-chattering-reload'))
        if not {str(p) for p in output}<=owned: raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b: raise SystemExit('Asset differs: '+str(p))
        else: dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack files; 87+3=90 elements')
if __name__=='__main__': main()
