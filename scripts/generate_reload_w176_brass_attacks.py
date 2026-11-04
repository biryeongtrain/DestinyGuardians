#!/usr/bin/env python3
"""W176 Brass Attacks: W143 exact semantic solids, authored grip-fed box magazine exchange (v3).

Observed Ultraclocked F6-wH23URIw Brass Attacks gameplay, not extracted animation. No hands, IK or runtime edits.
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
ART = Path('art/weapons/w176/brass_attacks')
KEY = 'weapon_reload_w176_brass_attacks/brass_attacks'
SOURCE = A/'models/weapon_surface_w123/brass_attacks.json'
TWOHAND = A/'models/weapon/sidearm/brass_attacks_twohand.json'
ITEM = A/'items/weapon/brass_attacks.json'
TEXTURE = A/'textures/item/weapon/w123/brass_attacks.png'
FP = ('firstperson_righthand', 'firstperson_lefthand')
# W143 semantic magazine_base, not the adjacent heel (which belongs to grip).
MOVING = (103,)
NAMES = ('magazine_base',)
FIXED_HOUSING = (45,56,63,64,95,96,97,98,99,100,101,102)
FIXED_NAMES = ('rear_breech_core','rear_cap','receiver_core','rear_shoulder',
 'grip_core','grip_wrist','grip_panel_-1','grip_panel_1','frontstrap','backstrap','upper_backstrap','heel')
GRIP = (8.,10.02,8.4)  # Exact W143 grip_core origin.
MAG_ANCHOR = (8.,6.62,9.34)  # Exact W143 magazine_base origin.
# -Y extraction through grip heel; same -19.05 degree cant as magazine_base.
MAG_AXIS = (0.,-math.cos(math.radians(19.05)),math.sin(math.radians(19.05)))
def withdrawal(distance): return tuple(distance*v for v in MAG_AXIS)
# Observed 13.2..15.0s normal-speed exchange. Angles and hidden travel authored.
# A quick sidearm cant, early magazine exchange, seating, follow-up action dip.
# V3 joins the authored magazine box to its canonical base with one neck; slide stays fixed.
KEYS = (
 (0., (0,0,0), (0,0,0), (0,0,0)),
 (.06,(27,-8,-12),(.18,.08,.02),(0,0,0)),
 (.12,(46,-14,-25),(.35,.18,.08),withdrawal(.5)),
 (.20,(40,-12,-23),(.20,.10,.12),withdrawal(7.5)),
 (.28,(36,-10,-22),(.12,.06,.10),withdrawal(7.5)),
 (.36,(33,-9,-20),(.08,.02,.06),(-.35,-2.25,.78)),
 (.43,(27,-8,-16),(.03,-.04,.02),(0,0,0)),
 (.50,(12,-7,-10),(0,-.08,0),(0,0,0)),
 (.58,(16,-12,-16),(-.08,-.02,.05),(0,0,0)),
 (.69,(25,-3,4),(-.10,-.12,.10),(0,0,0)),
 (.78,(-6,4,3),(-.08,-.38,.05),(0,0,0)),
 (.90,(-4,2,1),(-.02,-.14,.01),(0,0,0)),
 (1., (0,0,0), (0,0,0), (0,0,0)),
)
SOURCE_SHA256 = '49d02c139b239ecff7814bbb579ec0958a80d7bba75e3575f15b760a7e5dec09'
PINS = {
 'src/main/resources/assets/destiny/models/weapon/sidearm/brass_attacks.json':'225ab67eb09f06d81f4c962736f3a726974f8a9653e24d5907c96043efab145a',
 'src/main/resources/assets/destiny/models/weapon/sidearm/brass_attacks_twohand.json':'a9617a1be4aa3d30907c25af909d32e375c9974eb7c3d6215ed5ea95d1825494',
 'src/main/resources/assets/destiny/items/weapon/brass_attacks.json':'678051c7ff93f5171893a1234d7bd8b8c9d0a469fab7ccb65de0350f291f137b',
 'src/main/resources/assets/destiny/textures/item/weapon/w123/brass_attacks.png':'b5c08322401ae7b6c6511b3cfd58c087e93497ed75d93ec8752aedd87139682d',
}

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

CORE_NAME = 'authored_internal_magazine_core'
def internal_core(source):
    """One reload-only solid, strictly within opaque W143 grip_core at rest.

    Frame812/60 shows a box magazine, not its hidden dimensions or texels.
    Extents and UV allocation are authored; all canonical elements stay intact.
    The unmodified baseplate and core share one parent and rigid child display.
    """
    core=copy.deepcopy(source['elements'][95])
    core.update(name=CORE_NAME, **{'from':[7.42,7.15,7.32], 'to':[8.58,12.75,9.35]})
    return core


NECK_NAME = 'authored_internal_magazine_neck'
def internal_neck(source):
    """One small dark bridge from base103 to the core, in base103's frame.

    Hidden attachment is authored, not measured from gameplay. At rest it is
    recessed into the grip/heel housing; it shares the rigid magazine parent.
    """
    neck=copy.deepcopy(source['elements'][103])
    neck.update(name=NECK_NAME, **{'from':[7.5,6.70,8.55], 'to':[8.5,7.45,10.25]})
    neck['faces']=copy.deepcopy(source['elements'][95]['faces'])
    return neck


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
           if part=='magazine' else sub(h,vec(body,h)))
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
    paths={A/f'models/{KEY}_{part}.json' for part in ('body','magazine')}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in ('body','magazine') for grip in ('native','twohand'))
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}

def previews(source,reference,output):
    """Independent child-display reconstruction; offline views, not native QA.

    Uses emitted children and explicit axis matrices instead of pose_display's
    pivot/offset derivation. Existing inert raster helper supplies face UVs.
    """
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles={}
    for part in ('body','magazine'):
        parent=json.loads(output[A/f'models/{KEY}_{part}.json'])
        # Raster helper expects XYZ element rotation. Convert a render-only copy;
        # emitted axis/angle geometry and face UV remain byte-value exact.
        for element in parent['elements']:
            r=element.get('rotation',{})
            if 'axis' in r:
                element['rotation']={'origin':r['origin'],r['axis']:r['angle']}
        triangles[part]=helper['model_triangles']({part:parent},texture)
    def rotation(a):
        x,y,z=np.radians(a)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i,parts=('body','magazine')):
        ts=[]
        for part in parts:
            disp=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_native.json'])['display']['firstperson_righthand']
            rr=rotation(disp['rotation']);ss=np.array(disp['scale']);tt=np.array(disp['translation'])
            for points,uv,tex,normal in triangles[part]:
                ts.append(((np.asarray(points)-8)*ss@rr.T+tt,uv,tex,rr@normal))
        return ts
    def raster(ts,cam,w,h,extent=None):
        if extent is None: extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    sheet=Image.new('RGB',(1440,1410),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'W176 BRASS ATTACKS | independent reconstruction of emitted native display JSON | OFFLINE, no hands / IK',fill='white')
    for row,cam in enumerate(([1,.2,-.45],[-1,.35,.6],[.4,.4,1])):
        ts=[posed(i) for i in (0,5,20)]
        extent=helper['frame'](np.concatenate([t[0] for group in ts for t in group]),cam,480,300)
        for col,(i,group) in enumerate(zip((0,5,20),ts)):
            sheet.paste(raster(group,cam,480,300,extent),(col*480,50+row*330))
            draw.text((col*480+12,35+row*330),f'p={i/20:.2f} / '+('muzzle oblique','rear oblique','grip-facing oblique')[row],fill='white')
    draw.text((12,1035),'V3: 110 fixed + canonical base + authored box + neck = 113. All 111 W143 elements/UV exact; existing dark texels. Common framing per row.',fill='white')
    closeup=posed(5,('magazine',))
    for col,cam in enumerate(([1,.2,-.45],[-1,.35,.6],[.4,.4,1])):
        sheet.paste(raster(closeup,cam,480,295),(col*480,1090))
        draw.text((col*480+12,1073),'p=0.25 magazine close-up | existing base + authored core + connecting neck',fill='white')
    draw.text((12,1390),'Core + one recessed neck form a connected magazine. Existing dark grip UVs; hidden geometry authored. Native review pending.',fill='white')
    story=Image.new('RGB',(1600,1620),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL F6-wH23URIw gameplay vs AUTHORED Brass Attacks | source seconds / nearest authored sample | NO native or bone claim',fill='white')
    start,end=reference['selectedSeconds']
    for i,f in enumerate(reference['frames']):
        x=i%4*400;y=40+i//4*520
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
        p=(f['timestampSeconds']-start)/(end-start);index=max(0,min(20,round(p*20)))
        draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.6f}s / frame {f['sourceFrameIndex']}",fill='white')
        story.paste(raster(posed(index),[1,.2,.4],400,225),(x,y+260))
        draw.text((x+8,y+488),f'AUTHORED p={index/20:.2f} | '+f['phase'],fill='white')
    draw.text((12,1600),'Original frame pixels above; authored offline orthographic render below. Hand occlusion and HUD overlay limit exact magazine-path inference.',fill='white')
    return png(sheet),png(story)

def generate():
    source=json.loads((ROOT/SOURCE).read_bytes())
    twohand=json.loads((ROOT/TWOHAND).read_bytes())['display']
    item=json.loads((ROOT/ITEM).read_bytes())
    if sha((ROOT/SOURCE).read_bytes())!=SOURCE_SHA256: raise ValueError('Selected W143 source drift')
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest: raise ValueError('Canonical input drift: '+path)
    if len(source['elements'])!=111 or [source['elements'][i]['name'] for i in MOVING]!=list(NAMES) or [source['elements'][i]['name'] for i in FIXED_HOUSING]!=list(FIXED_NAMES):
        raise ValueError('W143 magazine-base/fixed-housing partition drift')
    design=json.loads((ROOT/'art/weapons/w123/brass_attacks/design.json').read_bytes())
    if design['revision']!='W143' or [p['geometry']['name'] for p in design['parts'] if p['group']=='magazine']!=list(NAMES):
        raise ValueError('Semantic magazine provenance drift')
    rules=json.loads((ROOT/'src/main/resources/weapon_surface_w123/manifest.json').read_bytes())['targets']
    rule=next(r for r in rules if r['path']=='assets/destiny/models/weapon/sidearm/brass_attacks.json')
    if rule['replacement']!='assets/destiny/models/weapon_surface_w123/brass_attacks.json' or rule['replacementSha256']!=SOURCE_SHA256:
        raise ValueError('Selected source mapping drift')
    ref=json.loads((ROOT/ART/'motion-reference.json').read_bytes())
    if not ref['inspectedActualFrames'] or len(ref['frames'])!=12: raise ValueError('Missing reviewed actual reference')
    for f in ref['frames']:
        if sha((ROOT/f['path']).read_bytes())!=f['sha256']: raise ValueError('Reference drift: '+f['path'])
    output={}
    def emit(path,v): output[path]=encode(v)
    for part in ('body','magazine'):
        geo={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        geo['elements']=[copy.deepcopy(e) for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='magazine')]
        if part=='magazine': geo['elements'].extend((internal_core(source),internal_neck(source)))
        emit(A/f'models/{KEY}_{part}.json',geo)
    entries=[]
    for i in range(21):
        p=i/20
        for part in ('body','magazine'):
            for grip in ('native','twohand'):
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],twohand,p,part,grip)))
        def composite(grip): return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in ('body','magazine')])
        entries.append(dict(threshold=p,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    wrapper=copy.deepcopy(item)
    wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model'])))],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    comparison,story=previews(source,ref,output)
    output[ART/'comparison.png']=comparison;output[ART/'storyboard.png']=story
    inputs=[Path('src/main/resources/weapon_surface_w123/manifest.json'),Path('art/weapons/w123/brass_attacks/design.json'),SOURCE,TWOHAND,ITEM,TEXTURE,ART/'motion-reference.json',Path('scripts/generate_reload_w176_brass_attacks.py'),Path('scripts/generate_surface_w123_hammerhead.py'),Path('src/main/resources/destiny/weapons/w46-timing.json'),Path('src/main/resources/destiny/sounds/w63-reload.json')]
    emit(ART/'manifest.json',dict(
        stage='W176',revision=3,weapon='brass_attacks',itemModel='destiny:'+KEY,
        ownedFiles=106,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,
        frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=111,bodyElements=110,movingElements=3,magazineElements=3,maxAssembledElements=113,elementLimit=1000,
        movingIndices=list(MOVING),movingNames=list(NAMES),fixedHousingIndices=list(FIXED_HOUSING),fixedHousingNames=list(FIXED_NAMES),
        partitionRationale='Existing W143 semantic magazine group: index103 magazine_base only. Adjacent heel102 belongs to grip and stays fixed, together with grip panels/core/wrist, shroud, receiver and trigger. All 111 canonical elements/face UV/paint preserved. One reload-only internal box lies within opaque grip_core95; one recessed neck joins it to magazine_base103 within grip/heel housing at rest. All three move rigidly together; no revoxelization.',
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceElementsAndUVSha256=sha(encode(source['elements'])),
        partElementsAndUVSha256={part:sha(encode([e for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='magazine')])) for part in ('body','magazine')},
        sourceRevision='W143 clean semantic solids selected by weapon_surface_w123 manifest; W30 base file remains untouched',geometryAndUVPreserved=True,addedElements=2,authoredCore=internal_core(source),authoredNeck=internal_neck(source),authoredCoreContainingElement=95,canonicalMovingElements=1,canonicalPartitionElements=111,
        authoredCorePolicy='Frame13.533 supports box volume; exact hidden extents,7.5-unit clearance stroke and copied dark grip_core face UVs are authored. Core remains inside opaque grip_core95; V3 neck bridges the base/core gap, recessed within grip/heel housing at rest. Basic offline idle and three magazine closeups, not exhaustive containment proof. Shares magazine parent/transform; no new texture.',
        hipEndpoints=[0,20],fallback='Exact canonical items/weapon/brass_attacks graph for all non-FP and inactive negative progress; ADS/inspect retained',
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,magazineExtractionAxis=MAG_AXIS,
        normalizedPhases={'quickCant':[0,.12],'withdrawalGuess':[.12,.20],'exchangeBelowFrame':[.20,.28],'replacementApproachGuess':[.28,.36],'reseat':[.36,.43],'lowerAfterSeat':[.43,.50],'actionGestureProxy':[.50,.78],'recover':[.78,1]},
        sourceObservedSeconds=ref['selectedSeconds'],reference=ref['url'],referenceConfidence=ref['referenceConfidence'],
        motionAuthorship='Brass-specific quick cant, early grip-fed baseplate exchange, seat, secondary action cant/dip, hip recovery authored after 12 inspected normal-speed Ultraclocked frames and inventory-name identity verification. W174 rigid composition/export pattern reused; Claws and Lonesome curves/extra inserts not used.',
        timingPolicy='Visual normalized phases only; observed seconds do not override catalog/perk reload speed.',
        rotationConvention='JOML Rx Ry Rz; R_idle * R_body about W143 grip_core pivot; source-local -Y withdrawal at -19.05-degree grip cant; scale once; twohand rigid carrier compensation',
        comparisonMethod='Independent explicit-axis reconstruction of emitted display children; three oblique cameras with common row framing, source axis/angle rotations preserved in render-only conversion. Actual-frame storyboard compares nearest authored sample.',
        nativeGameplayVerified=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration={'requiresNewMasterRoute':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'brass_attacks','liveOwnerOnly':'Master publishes float index1 only for live local owner first-person reload. Inactive negative progress and non-FP use canonical graph. Restore cancel/complete/equip/unequip/death/disconnect.','preserve':'Prior routes, catalog24 rounds, reload37ticks, 325rpm two-round burst, cadence/ammo-credit/perk-speed and all audio unchanged.'},
        nativeQueue=['Both FP hands/grips: quick cant, magazine_base103 plus authored core/neck separate rigidly, fixed heel102/core/panels, reseat seam and exact hip recovery','Non-FP/observer/GUI/ground and inactive negative progress canonical; ADS/inspect transitions retained','Master route plus live-owner float1 cancel/complete/equip/death/disconnect restore; capacity/timing/audio untouched','Brief 10-20 displayed weapons for obvious visual defects; offline imagery is not native/performance evidence'],
        limitations=ref['limitations'],sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},canonicalSha256=PINS,
        sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths(): raise ValueError('Output ownership mismatch')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    output=generate()
    scope=Path('/private/tmp/w176-manifest.json')
    if scope.exists():
        owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w176-brass-reload'))
        if not {str(p) for p in output}<=owned: raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b: raise SystemExit('Asset differs: '+str(p))
        else: dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 87 pack files; 110+3=113 assembled elements (111 exact W143 + authored core + neck)')
if __name__=='__main__': main()
