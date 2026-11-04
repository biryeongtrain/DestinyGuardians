#!/usr/bin/env python3
"""W182 IKELOS_SMG_v1.0.1 reference-observed grip magazine exchange and palm seat.
Canonical 133 solids/UV/dye remain unchanged. No hands or charging stroke invented.
--render requires retained original gameplay frames in --evidence; --verify is read-only.
Uses numpy/Pillow and the existing CPU UV renderer, never a native client.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w182/ikelos_smg_v1_0_1')
KEY='weapon_reload_w182_ikelos_smg_v1_0_1/ikelos_smg_v1_0_1'
SOURCE=A/'models/weapon_surface_w123/ikelos_smg_v1_0_1.json'
TWOHAND=A/'models/weapon/submachine_gun/ikelos_smg_v1_0_1_twohand.json'
ITEM=A/'items/weapon/ikelos_smg_v1_0_1.json'
TEXTURE=A/'textures/item/weapon/w123/ikelos_smg_v1_0_1.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.4,8.25)
MAGAZINE_ANCHOR=(8.,4.577331375,8.26)
# p, carrier RxRyRz degrees, display shift, rigid magazine local offset.
# Reference order: reach -> muzzle lift / occluded grip exchange -> insert -> palm seat.
# Exact angles, clearance, relative phase lengths are authored, not extracted animation.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.06,(4,-2,-3),(.05,-.05,0),(0,0,0)),
 (.22,(58,-9,-17),(.2,.2,.1),(0,-2.8,.15)),
 (.34,(62,-9,-17),(.2,.2,.1),(0,-4.8,.3)),
 (.46,(48,-7,-19),(.2,.1,.1),(0,-4.8,.3)),
 (.62,(43,-7,-20),(.2,.1,.1),(0,-1.4,.1)),
 (.70,(43,-7,-20),(.2,.1,.1),(0,0,0)),
 (.76,(47,-7,-21),(.2,.16,.1),(0,0,0)),
 (.80,(42,-7,-20),(.2,.06,.1),(0,0,0)),
 (.88,(38,-5,-16),(.1,0,.05),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/ikelos_smg_v1_0_1.json': '953456dfd97404185ccb13dedb7d70a0f4110915ca405c4d0a6843a7578a791c', 'src/main/resources/assets/destiny/textures/item/weapon/w123/ikelos_smg_v1_0_1.png': '67169c7e0a97481c77de13b4a08fd9b63188359bdfef8075fd0e35dfb72e0690', 'src/main/resources/assets/destiny/items/weapon/ikelos_smg_v1_0_1.json': '4c6ccbcda6f81cb75eb8fe89fecf71aa78ba7f0b42ec8245247866cddcbb5e08', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_inspect_twohand.json': 'ed76502a03723011e81e7e9b0b98ad2262e55ff149e1d9563327211da9dc8d49', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_twohand.json': 'fd54f41d53da0dbfb74d500e93ab4416a0eed7bea54986ac8a08f2b78e30b8e4', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_ads_twohand.json': '8f19751f7b00ab71784027a0d4ce034dfb90977b73822a190be11b069880795c', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1.json': 'd0b5f0be06846af78d9c207889e33226694343f896e1bd4028776754df28bec8', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_ads.json': '888d2860e55eec215ca2ac9bffc9f70abd5c587bb1e1b4d6ebbf1706f854af89', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1_inspect.json': 'aa7578f2da14189c1670289f8b78ce2df03b5274e7d6a6430f86a9928c16050d'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=pJdMgzVISnM', 'title': 'IKELOS_SMG_v1.0.1 (Range Masterworked) review | Destiny 2', 'creator': 'Aztecross', 'uploadDate': '20180518', 'version': 'original Warmind v1.0.1, identified by original 2018 release review title/date and same mechanism/silhouette; no footage item hash recovered', 'fpsNumerator': 60000, 'fpsDenominator': 1001, 'metadataRoundedFps': 60, 'actionFrameRange': [1404, 1464], 'frames': [{'path': '/private/tmp/w182-ikelos-report/reference-01.png', 'sha256': 'c0a1f34e0e884d2da7d831740dd4ba1db47827f87ca697f819b335895b5618b8', 'sourceFrameIndex': 1380, 'timestampSeconds': 23.023, 'nearestAuthoredProgress': 0, 'observation': 'Original IKELOS silhouette in hip view: four wired cells, open angled foregrip, rear circular action and top charging knob. HUD empty.'}, {'path': '/private/tmp/w182-ikelos-report/reference-02.png', 'sha256': '7472c23a8c31add0017f6c75d21db066c50e6e092d588a56901a77147f8d0554', 'sourceFrameIndex': 1404, 'timestampSeconds': 23.4234, 'nearestAuthoredProgress': 0.06, 'observation': 'Support hand comes toward lower grip area before upward presentation.'}, {'path': '/private/tmp/w182-ikelos-report/reference-03.png', 'sha256': '9a66570647697e54561b133b6cf9d573950b7d8a3bddc31c78802714c8825444', 'sourceFrameIndex': 1410, 'timestampSeconds': 23.5235, 'nearestAuthoredProgress': 0.14, 'observation': 'Carrier begins raising muzzle; existing sight, cells and foregrip stay attached.'}, {'path': '/private/tmp/w182-ikelos-report/reference-04.png', 'sha256': 'b71dd554328ecb3e34c14fcb6ee704b0806347729f615112fd245d2bb521492c', 'sourceFrameIndex': 1416, 'timestampSeconds': 23.6236, 'nearestAuthoredProgress': 0.22, 'observation': 'Weapon rises strongly; support wrist below receiver, grip base partly occluded by hand.'}, {'path': '/private/tmp/w182-ikelos-report/reference-05.png', 'sha256': '2713ac1ec4f44432307baa5771abcecfa4862ca6108162e396b4ff834c8be0eb', 'sourceFrameIndex': 1422, 'timestampSeconds': 23.7237, 'nearestAuthoredProgress': 0.34, 'observation': 'Held high for grip-fed magazine exchange; hand obscures magazine clearance.'}, {'path': '/private/tmp/w182-ikelos-report/reference-06.png', 'sha256': '0db16528aaea71a73a73852b3d334b6278352e62d30845a7f9c5004a0bd7941e', 'sourceFrameIndex': 1428, 'timestampSeconds': 23.8238, 'nearestAuthoredProgress': 0.46, 'observation': 'Carrier rotates back toward camera while support hand remains below pistol grip.'}, {'path': '/private/tmp/w182-ikelos-report/reference-07.png', 'sha256': '4fc0ad179872dc2c5e204c1b19026cc4d636c06e2461bc1ac14053fe56e9bf5f', 'sourceFrameIndex': 1434, 'timestampSeconds': 23.9239, 'nearestAuthoredProgress': 0.54, 'observation': 'Grip-base handling continues; no top-hand charging stroke visible.'}, {'path': '/private/tmp/w182-ikelos-report/reference-08.png', 'sha256': '2d02b564c104ed0c2fa136aa3fce17e933cbc893c78a642258b8fcf11eca8d3f', 'sourceFrameIndex': 1440, 'timestampSeconds': 24.024, 'nearestAuthoredProgress': 0.62, 'observation': 'Incoming magazine and exact insertion boundary are hand-occluded below pistol grip.'}, {'path': '/private/tmp/w182-ikelos-report/reference-09.png', 'sha256': 'd769afa8ef0b2d912040f9b3bb82e5afc33aed8f7c8dff87c6a83c9d97f97fb7', 'sourceFrameIndex': 1446, 'timestampSeconds': 24.1241, 'nearestAuthoredProgress': 0.7, 'observation': 'Upward seating movement at lower grip; upper charging knob still visible and stationary relative to receiver.'}, {'path': '/private/tmp/w182-ikelos-report/reference-10.png', 'sha256': '6ec59267971ff09b4a86243e97906c8f93950817618cbe5a48495e00586f9f20', 'sourceFrameIndex': 1458, 'timestampSeconds': 24.3243, 'nearestAuthoredProgress': 0.8, 'observation': 'Open support palm reaches lower grip/base; loaded HUD29 appears. Authored seat accent follows this observation.'}, {'path': '/private/tmp/w182-ikelos-report/reference-11.png', 'sha256': '440d1d7906374ab35fd2432b92b86fb01b0405ac3dc928fa2a6c42f6e407010d', 'sourceFrameIndex': 1464, 'timestampSeconds': 24.4244, 'nearestAuthoredProgress': 0.88, 'observation': 'Support palm finishes grip-base contact/release; gun begins lowering.'}, {'path': '/private/tmp/w182-ikelos-report/reference-12.png', 'sha256': '0f325de173c9399eb3f17626c035cff32f265f8fe161b1134269dc0913efacce', 'sourceFrameIndex': 1614, 'timestampSeconds': 26.9269, 'nearestAuthoredProgress': 1, 'observation': 'Same IKELOS visible again after sprint transition; final canonical product recovery is authored, not source sprint tracking.'}], 'sourceVideoSha256': '0ecc32006ad239c1eeb7c664f456e7c07ecbb29c010ddf5d0fce121774e64196', 'sourceMetadataSha256': '3e737c68ce9353eecb89556bcf43ef07e3808b858068cd5e9e530a92faba34ef'}

def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
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
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError(p)
    for a,b in zip(KEYS,KEYS[1:]):
        if p <= b[0]:
            t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3))
    raise ValueError(p)

def is_payload(e):
    # Side cells, their leads, lower swivel and well are fixed to the receiver/grip.
    return e['name'] == 'magazine'


def partition(source):
    return {part:{**{k:copy.deepcopy(v) for k,v in source.items() if k!='elements'},
                  'elements':[copy.deepcopy(e) for e in source['elements']
                              if is_payload(e)==(part=='magazine')]}
            for part in PARTS}


def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Complete existing grip-fed magazine is one rigid payload; fixed cells are body.
    local=add(sub(pivot,vec(motion,pivot)),vec(motion,offset) if part=='magazine' else [0,0,0])
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);scale=idle['scale']
        if twohand[context]['scale']!=scale or len(set(scale))!=1:raise ValueError('Expected equal uniform canonical grip scales')
        rotation=mul(base,motion)
        position=add(add(idle['translation'],shift),vec(base,[scale[0]*v for v in local]))
        if grip=='twohand':
            carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation'])))
            rotation=mul(carrier,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display


def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in PARTS for grip in GRIPS)
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}


def previews(output,evidence):
    # Renderer reuse only. It knows XYZ rotations, so normalize legacy axis/angle
    # for the offline rasterizer without changing one byte of emitted geometry.
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    def triangles(model):
        model=copy.deepcopy(model)
        for e in model['elements']:
            r=e.get('rotation',{})
            if 'axis' in r:
                e['rotation']={'origin':r['origin'],r['axis']:r['angle']}
        return helper['model_triangles']({'part':model},texture)
    def posed(i,grip='native',hand=FP[0],detail=False,canonical=False):
        ts=[]
        for part in PARTS:
            model=json.loads(output[A/f'models/{KEY}_{part}.json'])
            if detail:
                model['elements']=[e for e in model['elements'] if e['name'].startswith(('grip_','magazine','lower_swivel'))]
            child=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])
            d=child['display'][hand];rr=np.asarray(xyz(d['rotation']));ss=np.array(d['scale']);tt=np.array(d['translation'])
            for pts,uv,tex,n in triangles(model):
                points=np.asarray(pts).copy();n=np.asarray(n).copy()
                if not canonical:
                    points-=8
                    if hand==FP[1]:points[:,0]*=-1;n[0]*=-1
                    points=(points*ss)@rr.T+tt;n=rr@n
                    if hand==FP[1]:points[:,0]*=-1;n[0]*=-1
                ts.append((points,uv,tex,n))
        return ts
    def raster(ts,cam,w,h,extent=None):
        extent=extent if extent is not None else helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    sheet=Image.new('RGB',(1600,1800),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((14,12),'W182 IKELOS v1.0.1 | independent textured JSON reconstruction | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.55,-.7],[-1,.45,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,310),(col*400,70))
        draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.35,.55];groups=[posed(i) for i in (0,7,14,20)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,350)
    for col,(i,g) in enumerate(zip((0,7,14,20),groups)):
        sheet.paste(raster(g,cam,400,350,extent),(col*400,420))
        draw.text((col*400+10,396),f'p={i/20:.2f} / fixed camera + common scale',fill='white')
    draw.text((14,794),'133 canonical cubes = 132 fixed body + 1 complete grip-fed magazine. Cells, wiring, sight and charging handle stay attached.',fill='white')
    for col,i in enumerate((0,7,12,16)):
        sheet.paste(raster(posed(i,detail=True),[1,.25,.25],400,350),(col*400,855))
        draw.text((col*400+10,828),f'GRIP / PAYLOAD DETAIL p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(7,grip=grip,hand=hand),[1,.35,-.5],400,410),(col*400,1270))
        draw.text((col*400+10,1244),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((14,1710),'Observed: muzzle-up grip magazine handling -> lower grip palm seat -> release. Exact hidden path/angles/phases are authored.',fill='white')
    draw.text((14,1740),'No invented bolt stroke; original footage enters sprint after seating. Product returns to exact canonical endpoints.',fill='white')
    draw.text((14,1770),'Actual footage and hashes: SOURCE.md + manifest. Native screen, hand contact, audio and performance remain pending.',fill='white')
    story=Image.new('RGB',(1600,1900),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL ORIGINAL v1.0.1: Aztecross / pJdMgzVISnM / 2018-05-18 | authored normalized reload below',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225))
        x=j%4*400;y=55+j//4*605;story.paste(im,(x,y))
        draw.text((x+8,y+232),f"ACTUAL n={f['sourceFrameIndex']} / {f['timestampSeconds']:.5f}s",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.35,.55],400,295),(x,y+263))
        draw.text((x+8,y+567),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((14,1876),'59.94005994 fps (60000/1001); frame-exact PNGs external. Occluded exchange path + canonical recovery authored. No item hash inferred.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w182-ikelos-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=133:raise ValueError('Canonical element drift')
    parts=partition(source);output={}
    def emit(p,v):output[p]=encode(v)
    for part,model in parts.items():emit(A/f'models/{KEY}_{part}.json',model)
    entries=[]
    for i in range(21):
        p=i/20
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],two,p,part,grip)))
        def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in PARTS])
        entries.append(dict(threshold=p,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    reload=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model']))
    guard=copy.deepcopy(item['model']);guard['fallback']=reload
    wrapper=copy.deepcopy(item);wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=guard)],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    if render:output[ART/'comparison.png'],output[ART/'storyboard.png']=previews(output,evidence)
    else:
        manifest=json.loads((ROOT/ART/'manifest.json').read_bytes())
        for name in ('comparison.png','storyboard.png'):
            path=ART/name;data=(ROOT/path).read_bytes()
            if sha(data)!=manifest['sha256'][str(path)]:raise ValueError('Preview drift: '+str(path))
            output[path]=data
    indices={part:[i for i,e in enumerate(source['elements']) if is_payload(e)==(part=='magazine')] for part in PARTS}
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w182_ikelos_smg_v1_0_1.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W182',weapon='ikelos_smg_v1_0_1',revision=1,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=133,bodyElements=132,movingElements=1,maxAssembledElements=133,elementLimit=1000,addedElements=0,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,
        geometryPolicy='Exact canonical W142 solids, source order reconstructed by indices. Magazine only separates; grip well, cells, wiring, foregrip, sight, disc and charging knob remain body. No geometry/UV/dye/scale edits, no added or hidden bullet solids.',
        payloadPolicy='Single complete existing magazine cube at pistol grip base moves as one rigid component. One proxy for outgoing/incoming magazine; no scale fade or duplication. No individual cell/cartridge movement.',
        semanticGroups={'body':132,'completeGripMagazine':1,'fixedChargingHandle':['charging_handle_stem','charging_handle_knob']},
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,hipEndpoints=[0,20],
        endpointPolicy='Both parts/hands/grips at0/1 exactly canonical. Non-FP and inactive progress<0 and canonical ADS/inspect branches bypass reload.',
        normalizedPhases={'reach':[0,.06],'liftWithdraw':[.06,.34],'occludedExchange':[.34,.46],'insert':[.46,.70],'palmSeatAccent':[.70,.80],'release':[.80,.88],'canonicalRecover':[.88,1]},
        reference=REFERENCE,
        referencePolicy='Original Warmind-era v1.0.1 source, not later v1.0.2/v1.0.3. Evidence: exact original review title/date and four-cell/foregrip/disc/knob silhouette. No API item hash, perk roll, bone or animation data recovered from pixels. Preserve local canonical base dye, geometry and timing independently of footage.',
        motionAuthorship='Observed muzzle rise, support-hand grip-base handling and palm-seat/release. Exact hidden magazine clearance, grip pivot, carrier angles, offsets, normalized timings and canonical recovery are authored interpretations. Footage follows seating with sprint; no invented charging stroke. W181/W180 conventions reused only for graph/matrix/CPU renderer, not motion reference.',
        authoredHiddenDetails='Exchange partially hand-occluded. Single magazine proxies removed/inserted magazines, without hand mesh/IK. Geometry does not expose a newly authored chamber. No visibly distinct top charging-handle stroke; both existing handle solids remain fixed. Numeric motion is not camera-tracked.',
        timingPolicy='Visual normalized progression only; preserve canonical magazine32, reload45ticks, RPM720, cadence1.666666666667ticks, burst1, shellReloadfalse, ammo transfer and reload audio. Source HUD29 is not a capacity/timing input.',
        rotationConvention='Display JOML Rx Ry Rz. Equal uniform scale; twohand carrier conjugates complete native motion. Left native apply uses F*T*F; offline render mirrors it independently. Legacy canonical element axis/angle retained unchanged.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration={'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'ikelos_smg_v1_0_1','assetInputs':'float1 normalized0..1 in21samples; boolean0 existing twohand; negative float1 canonical fallback; string0 canonical ads/inspect guard. Master owns route/admission/lifecycle.'},
        nativeQueue=['Route/admit ikelos_smg_v1_0_1 only, keeping base v1.0.1 identity and45tick reload clock.',
        'Both FP hands/grips: verify grip contact, muzzle rise, rigid magazine clearance/seat/recovery; fixed cells/foregrip/sight/knob, no unexplained tearing. Exact canonical endpoint display.',
        'ADS/inspect during progress, GUI/ground/fixed/head/observer3P and inactive float1=-1 must use exact canonical graph.',
        'Partial/empty/full/no-reserve reload and fire/reload spam; one ammo transfer. Cancel/switch/equip/unequip/death/disconnect restore canonical with no delayed transfer.',
        'Listen to unchanged reload audio; observe10-20weapons for visible stalls/artifacts. All native/audio/performance pending; no worker native session.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w182-ikelos-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w182-manifest.json').read_bytes())['features'] if f['name']=='w182-ikelos'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic core outputs/media hashes; 87 pack assets; 132+1=133 assembled elements; native pending')
if __name__=='__main__':main()
