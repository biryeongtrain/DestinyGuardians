#!/usr/bin/env python3
"""Officer-specific FP cylinder reload. Exact canonical solids, UV and paint.
--render reconstructs emitted JSON with an independent NumPy path and actual frames;
--verify needs no raw video and compares deterministic assets and retained art hashes.
Master owns all routing/runtime/native execution. No hands, bones or new 3P animation.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w181/seventh_seraph_officer_revolver')
KEY='weapon_reload_w181_seventh_seraph_officer_revolver/seventh_seraph_officer_revolver'
SOURCE=A/'models/weapon_surface_w123/seventh_seraph_officer_revolver.json'
TWOHAND=A/'models/weapon/hand_cannon/seventh_seraph_officer_revolver_twohand.json'
ITEM=A/'items/weapon/seventh_seraph_officer_revolver.json'
TEXTURE=A/'textures/item/weapon/w123/seventh_seraph_officer_revolver.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
# 'magazine' is the established graph suffix; geometry is the entire original cylinder.
MOVING=tuple(range(72,82))
CYLINDER_NAMES=('rear_chamber','chamber_bevel_-1','chamber_bevel_1','chamber_underside',
 'chamber_brass_side_-1','chamber_brass_bevel_-1','chamber_brass_side_1',
 'chamber_brass_bevel_1','chamber_brass_top','chamber_brass_bottom')
GRIP=(8.,8.09,8.765)  # Existing grip_core origin, never recentered.
HINGE=(7.25,10.56,4.32)  # Authored left-lower crane axis beside chamber_bottom_rail.
# Officer-specific observations at 18.50..20.3333 source seconds. Numeric authoring.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (1/11,(22,-3,-14),(-.10,-.15,0),(0,0,0)),
 (2/11,(20,-8,-8),(-.15,-.20,-.10),(0,0,82)),
 (4/11,(78,-10,-6),(.05,-.35,-.20),(0,0,82)),
 (5/11,(78,-10,-6),(.05,-.35,-.20),(0,0,82)),
 (6/11,(34,-9,12),(-.10,-.30,-.10),(0,0,82)),
 (7/11,(6,-9,24),(-.10,-.40,0),(0,0,82)),
 (8/11,(3,-8,22),(-.10,-.40,0),(0,0,82)),
 (9/11,(5,-3,-18),(0,-.20,0),(0,0,0)),
 (10/11,(18,-1,-12),(0,-.10,0),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/seventh_seraph_officer_revolver.json': '089fd5426ba2c2047c386391c1f38031193a3c71c71e60187291cea687a348bb', 'src/main/resources/assets/destiny/textures/item/weapon/w123/seventh_seraph_officer_revolver.png': '3960e31bbddd2c381cde3a0fc4efa61c5beac54220806103718c1e91c1948ed5', 'src/main/resources/assets/destiny/items/weapon/seventh_seraph_officer_revolver.json': '9dca487d736b14c4782412305def195b0d156023c84f96dac5a9a55c06fab693', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/sounds/w63/reload/weapon_seventh_seraph_officer_revolver_reload_52.ogg': '54d616a55df97389848499873b91ba4c6ccd63ca2da91c0d43037ce7f4eaff0a', 'src/main/resources/assets/destiny/models/weapon/hand_cannon/seventh_seraph_officer_revolver_inspect.json': 'f8ef73d1544bfdcc079d48d71d5dccfa75114a77dd9fa5ac5ccef6934ab463ab', 'src/main/resources/assets/destiny/models/weapon/hand_cannon/seventh_seraph_officer_revolver_ads.json': '29849ace6fa0f190096f3d715e842dcf38c85a0ea1b67da3925d771f2e82f96e', 'src/main/resources/assets/destiny/models/weapon/hand_cannon/seventh_seraph_officer_revolver_ads_twohand.json': '4576a0d83ac8b1460eed79e54ed24518868d792e6988ad9ef9eb5a45c956c8b7', 'src/main/resources/assets/destiny/models/weapon/hand_cannon/seventh_seraph_officer_revolver.json': '54769897a32bc162e895ae2dac586527494cd898e0a744aef3832d196d5004a5', 'src/main/resources/assets/destiny/models/weapon/hand_cannon/seventh_seraph_officer_revolver_twohand.json': 'ad91ca62b8cba32bd293a149cbc218b4a8c95ceb5d43e1190d893fd19dfa71d4', 'src/main/resources/assets/destiny/models/weapon/hand_cannon/seventh_seraph_officer_revolver_inspect_twohand.json': 'c845ed87b2c33804cf73ba31a18691670ea443a4b610363cccb7f7a0953256e0', 'src/main/resources/assets/destiny/items/weapon_aim_w70/seventh_seraph_officer_revolver.json': '97bb3fdbf8aa4a168f82fb1e1385394246b789e53b4e9fa80d4b5facf83fb952', 'src/main/resources/assets/destiny/items/weapon_sight_w151/seventh_seraph_officer_revolver.json': 'bfd45520bbb4b100cef65200d6c380ff0161af2f4810f4f0f824839bfbba48d6'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=CT0EUpyTweM', 'title': 'Seventh Seraph Officer Revolver  with Timed Payload', 'creator': 'madmaxdrj Gaming', 'published': '2022-01-05', 'fps': 60, 'width': 1280, 'height': 720, 'selectedSeconds': [18.5, 20.333333333333332], 'inspectedActualFrames': True, 'frames': [{'file': 'reference-01.png', 'timestampSeconds': 18.5, 'sourceFrameIndex': 1110, 'nearestAuthoredProgress': 0.0, 'sha256': '9448b48bb5d28df1a93c506a4de5883acbd5581d83750b210671483fd34d010b', 'observation': 'Ready after emptying; Officer long shroud, raised rear sight, swept grip; source HUD 0.'}, {'file': 'reference-02.png', 'timestampSeconds': 18.666666666666668, 'sourceFrameIndex': 1120, 'nearestAuthoredProgress': 0.09090909090909091, 'sha256': '5cb7f97794122edb51de8756cac7f951d4c30060e5c953eb9750022338d715a8', 'observation': 'Initial roll and presentation before cylinder opening.'}, {'file': 'reference-03.png', 'timestampSeconds': 18.833333333333332, 'sourceFrameIndex': 1130, 'nearestAuthoredProgress': 0.18181818181818182, 'sha256': '18e0e45d957410c7bea2fd1acd2d3d918572e95675caccb7b0b52054e8da7804', 'observation': 'Complete cylinder swung to screen-left; circular rear face and chambers visible.'}, {'file': 'reference-04.png', 'timestampSeconds': 19.0, 'sourceFrameIndex': 1140, 'nearestAuthoredProgress': 0.2727272727272727, 'sha256': '74a6e877665b755de0055df023591b2adf15af47451738adbc17097eced6986b', 'observation': 'Muzzle rises with cylinder held open beside frame.'}, {'file': 'reference-05.png', 'timestampSeconds': 19.166666666666668, 'sourceFrameIndex': 1150, 'nearestAuthoredProgress': 0.36363636363636365, 'sha256': '66066565f693536d11b5f47cfd1e603e506bc33d10d146f0863ce0654fb22f4b', 'observation': 'Steep upright open-cylinder presentation, long shroud overhead.'}, {'file': 'reference-06.png', 'timestampSeconds': 19.333333333333332, 'sourceFrameIndex': 1160, 'nearestAuthoredProgress': 0.45454545454545453, 'sha256': 'd640bf642368c52dbdffd1e47a6aa80a328fd7658fd934ec361613ebaca6db64', 'observation': 'Upright open hold; chamber and frame remain distinct.'}, {'file': 'reference-07.png', 'timestampSeconds': 19.5, 'sourceFrameIndex': 1170, 'nearestAuthoredProgress': 0.5454545454545454, 'sha256': 'ae14ac2f7f62d2e104e9781ae0606bd4472c49bcd95d9863d77888a3112ffd03', 'observation': 'Lowering toward loader; open cylinder rear face visible.'}, {'file': 'reference-08.png', 'timestampSeconds': 19.666666666666668, 'sourceFrameIndex': 1180, 'nearestAuthoredProgress': 0.6363636363636364, 'sha256': '1c32b9140617745ab5f06937f50e2b10dab8c310ceab1131180d2c718755da8d', 'observation': 'Support hand and loader approach open cylinder rear face.'}, {'file': 'reference-09.png', 'timestampSeconds': 19.833333333333332, 'sourceFrameIndex': 1190, 'nearestAuthoredProgress': 0.7272727272727273, 'sha256': '2298829aac776cd0d91c8107d2c1ce41ffbc54ca4b5a91216d105096b3450d24', 'observation': 'Loader/hand contact obscures rear; source counter 0 to 11, not a local timing rule.'}, {'file': 'reference-10.png', 'timestampSeconds': 20.0, 'sourceFrameIndex': 1200, 'nearestAuthoredProgress': 0.8181818181818182, 'sha256': '4954a877f8af8906a77c9023c3be720f3fe426f851353150c348a3db3d64e6d9', 'observation': 'Closing wrist flick and recovery begin; cylinder reseated.'}, {'file': 'reference-11.png', 'timestampSeconds': 20.166666666666668, 'sourceFrameIndex': 1210, 'nearestAuthoredProgress': 0.9090909090909091, 'sha256': 'f10e49e6f1d3f340d62b52740f9562b7d7c6eea9191ef77953a5a0dae52af539', 'observation': 'Brief post-close raised recovery with support hand leaving.'}, {'file': 'reference-12.png', 'timestampSeconds': 20.333333333333332, 'sourceFrameIndex': 1220, 'nearestAuthoredProgress': 1.0, 'sha256': '5fcf841615fd98a36c131360e034763e81e9ca36f3ecff858f9583c4623e6653', 'observation': 'Ready hip restored after complete reload.'}], 'sourceVideoSha256': '29642397a6df638fcf6b02bc732f131c3598dbeff98e976fa83aabc6374308c5', 'sourceMetadataSha256': '3f5ceb515f469e7811c6cf28df00c10c298380865b016934b8b06311e74e01d4', 'timeBasis': 'Sequential decoded frame n/60 from source video; no approximate input seek used for final frames.', 'identification': 'Same-weapon title plus long vented shroud, raised hood/rail and rear fork, rectangular brass-trimmed cylinder, underbarrel module and swept perforated grip match official Officer photo. Source uses red/green alternate shader; motion only.', 'authorship': 'Observed order: roll/open, steep upright open hold, lower to loader contact, flick cylinder closed, recovery. All numeric angles, pivot and normalized phases authored; no recovered bones or hand IK.', 'limitations': ['Source shader and perks uncontrolled; no source paint, reload duration or counter timing copied.', 'Hands occlude exact loader contact and hinge linkage. Existing clean solid chamber has no newly modeled rounds, chamber bores or crane.', 'Observed 14.33-14.83s open attempt was dodge-interrupted and excluded from completion reference.', 'Offline asset renders establish no native hand contact, third-person reload, audio listening or performance acceptance.']}

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
    if not math.isfinite(p) or not 0<=p<=1: raise ValueError(p)
    for a,b in zip(KEYS,KEYS[1:]):
        if p<=b[0]:
            t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3))
    raise ValueError(p)


def partition(source):
    if len(source['elements'])!=121 or tuple(source['elements'][i]['name'] for i in MOVING)!=CYLINDER_NAMES:
        raise ValueError('Officer canonical partition drift')
    parts={}
    for part in PARTS:
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='magazine')]
        parts[part]=model
    return parts

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    if not math.isfinite(p) or not 0<=p<=1:raise ValueError(p)
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    angles,shift,cylinder=sample(p)
    body=xyz(angles);component=xyz(cylinder if part=='magazine' else (0,0,0))
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
    paths={A/f'models/{KEY}_{part}.json' for part in ('body','magazine')}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in ('body','magazine') for grip in ('native','twohand'))
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}


def previews(output,evidence):
    """Read emitted JSON only; independent NumPy matrices, not sample/pose_display.
    Shared helper supplies face UV triangulation and rasterization only.
    """
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles={part:helper['model_triangles']({part:json.loads(output[A/f'models/{KEY}_{part}.json'])},texture) for part in PARTS}
    def rotation(angles):
        x,y,z=np.radians(angles)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i,grip='native',hand=FP[0],parts=PARTS):
        ts=[]
        for part in parts:
            d=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])['display'][hand]
            r=rotation(d['rotation']);s=np.asarray(d['scale']);t=np.asarray(d['translation'])
            for pts,uv,tex,normal in triangles[part]:
                pts=np.asarray(pts).copy();normal=normal.copy()
                if hand==FP[1]:pts[:,0]=16-pts[:,0];normal[0]*=-1
                world=((pts-8)*s)@r.T+t;normal=r@normal
                if hand==FP[1]:world[:,0]*=-1;normal[0]*=-1
                ts.append((world,uv,tex,normal))
        return ts
    def extent(groups,cam,w,h):return helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,w,h)
    def raster(ts,cam,w,h,ext=None):
        return helper['render'](ts,cam,extent([ts],cam,w,h) if ext is None else ext,(w,h))[0]
    sheet=Image.new('RGB',(1600,2200),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'W181 OFFICER REVOLVER | independently reconstructed emitted JSON | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    photo=evidence/'canonical-officer.jpg'
    if sha(photo.read_bytes())!='386a6d3061bda47461fc85650e8c9d8bcb013c53af7379ec2ac0f28fc7332d46':raise ValueError('Canonical photo drift')
    image=Image.open(photo).convert('RGB');image.thumbnail((800,450));sheet.paste(image,(0,40))
    sheet.paste(raster(posed(0),[1,.3,-.55],800,450),(800,40))
    draw.text((12,496),'ACTUAL Bungie 3037520408 default art                             AUTHORED exact canonical W136 121 cubes / 726 explicit face UVs',fill='white')
    for row,(cam,label) in enumerate((([1,.3,-.5],'muzzle oblique'),([-1,.3,.5],'open-side oblique'),([.35,.3,1],'rear oblique'))):
        groups=[posed(i) for i in (0,7,14,20)];ext=extent(groups,cam,400,280)
        for col,(i,g) in enumerate(zip((0,7,14,20),groups)):
            sheet.paste(raster(g,cam,400,280,ext),(col*400,555+row*315))
            draw.text((col*400+8,535+row*315),f'p={i/20:.2f} / {label} / common framing',fill='white')
    draw.text((12,1498),'Cylinder-only diagnostic: all ten chamber/brass solids rotate together; no detachable box, scale fade, shards or invented cases.',fill='white')
    for col,i in enumerate((0,4,14,20)):
        sheet.paste(raster(posed(i,parts=('magazine',)),[-1,.35,.7],400,230),(col*400,1540))
        draw.text((col*400+8,1518),f'WHOLE CYLINDER p={i/20:.2f}',fill='white')
    draw.text((12,1785),'FP item-display reconstruction (oblique camera; per-grip framing) | left reflection follows native ItemTransform convention',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(7,grip,hand),[.25,.15,1],400,310),(col*400,1830))
        draw.text((col*400+8,1810),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((12,2160),'111 fixed + 10 cylinder = 121 assembled cubes, zero adapters/added elements. Native contact/framing and actual sound pending master.',fill='white')
    story=Image.new('RGB',(1600,1950),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL madmaxdrj Gaming / CT0EUpyTweM | completed Officer reload 18.50-20.333s | AUTHORED pairs below / OFFLINE',fill='white')
    cam=[-1,.3,.6];groups=[posed(round(f['nearestAuthoredProgress']*20)) for f in REFERENCE['frames']];ext=extent(groups,cam,400,280)
    for i,(f,g) in enumerate(zip(REFERENCE['frames'],groups)):
        path=evidence/f['file']
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        image=Image.open(path).convert('RGB');image.thumbnail((400,225));x=i%4*400;y=45+i//4*625
        story.paste(image,(x,y));draw.text((x+8,y+230),f"ACTUAL {f['timestampSeconds']:.4f}s / n={f['sourceFrameIndex']}",fill='white')
        draw.text((x+8,y+250),f['observation'][:59],fill='white')
        story.paste(raster(g,cam,400,280,ext),(x,y+280));j=round(f['nearestAuthoredProgress']*20)
        draw.text((x+8,y+570),f'AUTHORED p={j/20:.2f} / common oblique framing',fill='white')
    draw.text((12,1920),'Source alternate red/green shader is motion evidence only. Canonical black/silver/brass retained. Numeric pivots/curves authored; no hand IK.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w181-officer-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    parts=partition(source);output={}
    def emit(p,v):output[p]=encode(v)
    for part,model in parts.items():emit(A/f'models/{KEY}_{part}.json',model)
    entries=[]
    for i in range(21):
        for part in PARTS:
            for grip in GRIPS:
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],two,i/20,part,grip)))
        def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in PARTS])
        entries.append(dict(threshold=i/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    reload=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model']))
    guard=copy.deepcopy(item['model']);guard['fallback']=reload
    wrapper=copy.deepcopy(item);wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=guard)],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    if render:output[ART/'comparison.png'],output[ART/'storyboard.png']=previews(output,evidence)
    else:
        retained=json.loads((ROOT/ART/'manifest.json').read_bytes())
        for name in ('comparison.png','storyboard.png'):
            path=ART/name;data=(ROOT/path).read_bytes()
            if sha(data)!=retained['sha256'][str(path)]:raise ValueError('Preview drift: '+str(path))
            output[path]=data
    indices={part:[i for i in range(121) if (i in MOVING)==(part=='magazine')] for part in PARTS}
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w181_seventh_seraph_officer_revolver.py'),Path('scripts/generate_surface_w123_hammerhead.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W181',weapon='seventh_seraph_officer_revolver',revision=1,itemModel='destiny:'+KEY,
      ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
      sourceElements=121,bodyElements=111,movingElements=10,cubeElements=121,maxAssembledElements=121,triangleAdapterElements=0,elementLimit=1000,addedElements=0,
      sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceRevision='W136 canonical 121 opaque semantic solids in weapon_surface_w123',geometryAndUVPreserved=True,
      partitionIndices=indices,cylinderNames=CYLINDER_NAMES,fixedFrameNames=['rear_frame','rear_frame_slope','rear_dark_wrist','chamber_bottom_rail'],
      partitionRationale='The entire ten-solid rear chamber plus brass rim (72..81) swings rigidly around a longitudinal left-lower hinge. Rear frame, lower rail, fixed shroud, controls, sight and grip stay body. Every original element/field/UV appears once. The suffix magazine is only the existing graph convention, not box geometry.',
      authoredHiddenDetails='Numeric 82 degree hinge, left-lower pivot, grip pivot, hidden linkage and phase mapping are authored. Existing solid chamber has no modeled chamber bores, separate rounds, ejection, loader or crane link; no new geometry or pseudo shards.',
      keyframes=KEYS,gripPivot=GRIP,cylinderHinge=HINGE,hipEndpoints=[0,20],
      normalizedPhases={'present':[0,1/11],'swingOpen':[1/11,2/11],'raiseUpright':[2/11,4/11],'openHold':[4/11,5/11],'lowerToLoader':[5/11,7/11],'loaderContactHold':[7/11,8/11],'closeFlick':[8/11,9/11],'postCloseRecovery':[9/11,10/11],'hipReturn':[10/11,1]},
      endpointPolicy='Both parts and FP hands/grips exactly accepted at 0/1; constant scale, all nonFP contexts and ADS/inspect retain canonical graph even with positive progress.',
      reference=REFERENCE,canonicalReference={'url':'https://www.bungie.net/common/destiny2_content/screenshots/3037520408.jpg','sha256':'386a6d3061bda47461fc85650e8c9d8bcb013c53af7379ec2ac0f28fc7332d46'},
      sourceChronology=[{'stage':'W136','evidence':'art/weapons/w123/seventh_seraph_officer_revolver/review.md','role':'Canonical art and clean 121 cubes/726 UVs.'},
       {'stage':'W168/W169','evidence':'scripts/generate_reload_w168_austringer.py and scripts/generate_reload_w169_duke_mk_44.py','role':'Cylinder hinge/display algebra only, no other weapon motion keys.'},
       {'stage':'W180','evidence':'scripts/generate_reload_w180_halfdan_d.py and scripts/generate_reload_w180_edge_transit.py','role':'Exact 94-file ownership, ADS/inspect guard, retained media and independent emitted-JSON rendering conventions.'},
       {'stage':'W181','evidence':REFERENCE['url'],'role':'Independently reviewed actual same-weapon complete reload and alternate shader distinction.'}],
      timingPolicy='Normalized visuals only; preserve 11 rounds, 52 reload ticks, 180 RPM, 6.666666666667 cadence ticks, burst1 and single whole-reload credit. Source HUD clock is not timing calibration.',
      rotationConvention='Element Rz Ry Rx, display JOML Rx Ry Rz. Cylinder hinge then grip pivot then idle carrier; uniform scale once, twohand carrier compensation, native left reflection.',
      nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
      integration={'requiresMasterRouting':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'catalogId':'seventh_seraph_officer_revolver','requiredMasterModel':'destiny:'+KEY,'assetInputs':'float1 normalized reload progress, boolean0 twohand, string0 ADS/inspect guard, negative inactive; master owns admission/routing/lifecycle.'},
      nativeQueue=['Master admission/routing first; both FP hands x native/twohand: open cylinder, upright hold, loader lowering, close flick, exact hip recovery. Check frame/rail seam, near plane, mirror and real hand contact.',
       'ADS/inspect precedence at positive progress, negative inactive; GUI/ground/fixed/head/third-person observer remain canonical. No new third-person reload claim.',
       'Partial/empty/full/no-reserve reload, fire/reload spam and completion once; preserve 11 rounds and 52tick base clock. Cancel/swap/equip/unequip/death/disconnect clear progress and restore canonical state.',
       'Master actual sound listening and brief 10-20 display observation. Native pack bake, framing, performance and sound unverified by offline evidence.'],
      canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Expected exact 90 deterministic outputs')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w181-officer-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    scope=Path('/private/tmp/w181-manifest.json')
    if scope.exists():
        owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w181-officer'))
        if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+' 90 deterministic outputs; 87 pack assets; 111+10=121 assembled cubes; native pending')
if __name__=='__main__':main()
