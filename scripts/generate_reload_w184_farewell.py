#!/usr/bin/env python3
"""W184 Farewell same-weapon reference-led FP carrier/grip-magazine motion.
Preserves all115 canonical solids/UV/default paint. Adds three reload-only
shaft solids from actual Farewell frame1472, reusing the unchanged atlas.
Endpoint item dispatch bypasses added geometry and selects exact canonical graph.
W182 matrix, guard and CPU renderer infrastructure only; independent source poses.
--render requires retained actual frames; --verify is read-only.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w184/farewell')
KEY='weapon_reload_w184_farewell/farewell'
SOURCE=A/'models/weapon_surface_w123/farewell.json'
TWOHAND=A/'models/weapon/sidearm/farewell_twohand.json'
ITEM=A/'items/weapon/farewell.json'
TEXTURE=A/'textures/item/weapon/w123/farewell.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,9.305,8.175)  # canonical grip_core78 origin; fixed carrier
MAGAZINE_ANCHOR=(8.,7.05,8.83)  # heel81 center; whole heel/loop/shaft payload
# Independently authored after examining Farewell n1456..1524. W183 infrastructure only.
KEYS=((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.1, (12, -4, -6), (0.1, -0.08, 0.03), (0, 0, 0)), (0.2, (31, -6, -24), (0.28, 0.2, 0.1), (0, 0, 0)), (0.3, (37, -5, -27), (0.32, 0.27, 0.15), (-0.1, -1.7, 0.424)), (0.4, (38, -7, -25), (0.34, 0.26, 0.12), (-0.6, -4.6, 1.147)), (0.5, (36, -8, -24), (0.34, 0.21, 0.1), (-0.8, -5.4, 1.346)), (0.6, (35, -8, -23), (0.32, 0.15, 0.08), (-0.3, -3.4, 0.848)), (0.72, (29, -6, -20), (0.28, 0.04, 0.05), (0, 0, 0)), (0.8, (11, 3, -43), (0.18, -0.12, 0.04), (0, 0, 0)), (0.86, (5, 9, -55), (0.1, -0.18, 0.02), (0, 0, 0)), (0.93, (13, 5, -22), (0.06, -0.05, 0.01), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/farewell.json': 'bd92efd7fe5f77e6571a5c526039cde59d0f619e7d5e3f9ffa4af53da3be37b1', 'src/main/resources/assets/destiny/textures/item/weapon/w123/farewell.png': '7cabfcb0ef9a88311fb7508f736d29812cfcc9dd363ed8c86e3c7783d8f77645', 'src/main/resources/assets/destiny/items/weapon/farewell.json': 'cb6503a2fdd1c0185a41ab6cf4d13d86f06c0df9071ceefa6d74e5022836afac', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/sidearm/farewell.json': '020ec70acfbeca358e00418b8c7b666f7983b2627c65af41ced43cc52cced3bc', 'src/main/resources/assets/destiny/models/weapon/sidearm/farewell_ads.json': 'b76f5181689c2a16d27c7cf8d4a637a01db195856072aa3695d088c7662ff490', 'src/main/resources/assets/destiny/models/weapon/sidearm/farewell_ads_twohand.json': 'b3775512d7725b0de93423f57cf92049f15ddd5bbd16799c691ef8d088aaf7f8', 'src/main/resources/assets/destiny/models/weapon/sidearm/farewell_inspect.json': '42b7e101e4a79a964530edd2cc7c9342d4c30db1682996e40436809c079eef6c', 'src/main/resources/assets/destiny/models/weapon/sidearm/farewell_inspect_twohand.json': '3204329097a7dcaa8f196091e9f56e222a1c800106c1d3c1febf00e5d7c5a13e', 'src/main/resources/assets/destiny/models/weapon/sidearm/farewell_twohand.json': '53d76188461f13ed01be2b1c6347c0dae3e5668ff4aa400615806a8eed8740c3'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=2VaZGMrEfjQ', 'title': 'The Sidearm with No Competition - Farewell Legendary Review', 'creator': 'True Vanguard', 'uploadDate': '20210514', 'fpsNumerator': 60000, 'fpsDenominator': 1001, 'sourceTimebase': '1/60000', 'actionFrameRange': [1456, 1524], 'actionSeconds': [24.290933333333335, 25.4254], 'sourceVideoFile': '/private/tmp/w184-farewell-report/farewell-reference.mp4', 'sourceMetadataFile': '/private/tmp/w184-farewell-report/farewell-reference.info.json', 'sourceVideoSha256': '8fafe0a686a8706dcbbc07d99127927a4bf5fef17f9290abd9995b80e2c307ca', 'sourceMetadataSha256': 'bf3555ff87589a275eaf48afbd7f96609de383f855d791abbd51febb33b4b72d', 'frames': [{'path': '/private/tmp/w184-farewell-report/reference-01.png', 'sha256': 'cd49e9fd789ebf27396fd9512d050dbe4008c093c5f47e3024d083cb0239ce5d', 'sourceFrameIndex': 1456, 'timestampSeconds': 24.290933333333335, 'nearestAuthoredProgress': 0, 'observation': 'Hip presentation before reload; green bound cables, magenta stencil, finned front, blue receiver and hanging blade establish Farewell silhouette.'}, {'path': '/private/tmp/w184-farewell-report/reference-02.png', 'sha256': '088294db57d52391405d2355603d37b51a5d3e1999e1d6bec69e002e0cd8ddab', 'sourceFrameIndex': 1460, 'timestampSeconds': 24.357666666666667, 'nearestAuthoredProgress': 0.1, 'observation': 'Muzzle begins rising and left side turns toward camera.'}, {'path': '/private/tmp/w184-farewell-report/reference-03.png', 'sha256': '738dfbbbe8a270c036c2f514c86bdcd16b5f33d15d8729df772546f1b0fc153a', 'sourceFrameIndex': 1464, 'timestampSeconds': 24.4244, 'nearestAuthoredProgress': 0.2, 'observation': 'Raised diagonal carrier; right hand stays on grip; left hand comes to grip base.'}, {'path': '/private/tmp/w184-farewell-report/reference-04.png', 'sha256': '3823239b724f690957e1590074be7a35e17b24d9482501122f609e64b3c908ee', 'sourceFrameIndex': 1468, 'timestampSeconds': 24.491133333333334, 'nearestAuthoredProgress': 0.25, 'observation': 'Support fingers cup grip base; heel release partly hidden.'}, {'path': '/private/tmp/w184-farewell-report/reference-05.png', 'sha256': 'a24a6a3501968a4ebdee304dfffa87c08ef50f9aa027e08afaed962847cc1f4b', 'sourceFrameIndex': 1472, 'timestampSeconds': 24.557866666666666, 'nearestAuthoredProgress': 0.3, 'observation': 'Rectangular grey magazine with parallel broad-face lines visible down-left in support hand; shaft is separate from fixed pistol grip.'}, {'path': '/private/tmp/w184-farewell-report/reference-06.png', 'sha256': '0241bfc085e9961cf63e2c3e3b259b1bba3fcd801a5034a467c40e1e4f849df0', 'sourceFrameIndex': 1480, 'timestampSeconds': 24.691333333333333, 'nearestAuthoredProgress': 0.4, 'observation': 'Outgoing magazine lowers below screen; fixed rear receiver and trigger guard remain attached.'}, {'path': '/private/tmp/w184-farewell-report/reference-07.png', 'sha256': 'b109b9366546119786c1593cf2edc2b18547fd786fd1d609d558dbb4ad30f679', 'sourceFrameIndex': 1488, 'timestampSeconds': 24.8248, 'nearestAuthoredProgress': 0.55, 'observation': 'Carrier remains raised while support hand is below screen; exchange hidden.'}, {'path': '/private/tmp/w184-farewell-report/reference-08.png', 'sha256': 'ee983c306acb682123eec019cca3b7e1fa6699bb8d432cd0804f88931c2762da', 'sourceFrameIndex': 1496, 'timestampSeconds': 24.958266666666667, 'nearestAuthoredProgress': 0.65, 'observation': 'Support hand returns from below toward grip, top/seat boundary hand occluded.'}, {'path': '/private/tmp/w184-farewell-report/reference-09.png', 'sha256': 'dc57c570a6f8b17667bc8fe7df4df251a17bb5e19e87c56035a7066612138524', 'sourceFrameIndex': 1500, 'timestampSeconds': 25.025, 'nearestAuthoredProgress': 0.72, 'observation': 'Magazine seated, HUD changes from8 to15; carrier rolls inward/down. HUD timing is not local reload clock.'}, {'path': '/private/tmp/w184-farewell-report/reference-10.png', 'sha256': '8292d0f17ca6f2fe8f16491c855e0460720671ca58c61730f5c5a7d721614d15', 'sourceFrameIndex': 1504, 'timestampSeconds': 25.091733333333334, 'nearestAuthoredProgress': 0.8, 'observation': 'Left hand leaves grip and moves upward as wrist rolls; no independently resolved bolt stroke.'}, {'path': '/private/tmp/w184-farewell-report/reference-11.png', 'sha256': 'f9450cc4edd8fb6eefc3a6902a0a6be09cc943dba7a864bd019cd8997201ecdb', 'sourceFrameIndex': 1512, 'timestampSeconds': 25.2252, 'nearestAuthoredProgress': 0.9, 'observation': 'Weapon turns toward forward presentation; support-hand contact is partly hidden.'}, {'path': '/private/tmp/w184-farewell-report/reference-12.png', 'sha256': '2d5ed1380dae60caa366b7cda118e389f27116bf7f9ebf3bbd290db6bab08f36', 'sourceFrameIndex': 1524, 'timestampSeconds': 25.4254, 'nearestAuthoredProgress': 1, 'observation': 'Forward recovery follows; camera/player motion continues. Canonical hip endpoint is authored.'}]}

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
    # Actual canonical heel and open heel loop; NOT grip_shoulder77 or grip_core78.
    return e['name']=='heel' or e['name'].startswith('open_heel_loop_')

def reload_shaft(source):
    """Three reload-only solids: shaft and two narrow broad-face seam strips.
    Visible rectangular magazine backed by n1472; exact hidden proportions authored.
    Shaft extends .070443 below grip78 local Y to overlap original heel81.
    Existing heel face UV only; canonical endpoints bypass reload geometry.
    """
    faces=copy.deepcopy(source['elements'][81]['faces'])
    rot=copy.deepcopy(source['elements'][78]['rotation'])
    def box(name,lo,hi):
        return dict(name='magazine_shaft_'+name,**{'from':lo,'to':hi},rotation=copy.deepcopy(rot),faces=copy.deepcopy(faces))
    return [box('core',[7.58,7.23,7.57],[8.42,10.95,8.85]),
            box('left_seam',[7.56,7.36,7.72],[7.585,10.87,7.78]),
            box('right_seam',[8.415,7.36,7.72],[8.44,10.87,7.78])]


def partition(source):
    return {part:{**{k:copy.deepcopy(v) for k,v in source.items() if k!='elements'},
                  'elements':[copy.deepcopy(e) for e in source['elements']
                              if is_payload(e)==(part=='magazine')]+(reload_shaft(source) if part=='magazine' else [])}
            for part in PARTS}


def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Original baseplate and reference-backed reload-only shaft move as one rigid payload.
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
            if canonical or i in (0,20):
                model['elements']=[e for e in model['elements'] if not e['name'].startswith('magazine_shaft_')]
            if detail:
                model['elements']=[e for e in model['elements'] if e['name'].startswith(('grip_','magazine','heel','open_heel_loop','palm_panel','backstrap'))]
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
    draw.text((14,12),'W184 FAREWELL | reference-led canonical JSON motion | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.55,-.7],[-1,.45,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,310),(col*400,70))
        draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.35,.55];groups=[posed(i) for i in (0,8,14,20)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,350)
    for col,(i,g) in enumerate(zip((0,8,14,20),groups)):
        sheet.paste(raster(g,cam,400,350,extent),(col*400,420))
        draw.text((col*400+10,396),f'p={i/20:.2f} / fixed camera + common scale',fill='white')
    draw.text((14,794),'118 reload elements = 106 canonical body + 9 heel/loop + 3 reference-backed shaft solids. Canonical endpoints =115.',fill='white')
    for col,i in enumerate((0,8,12,16)):
        sheet.paste(raster(posed(i,detail=True),[1,.25,.25],400,350),(col*400,855))
        draw.text((col*400+10,828),f'GRIP / PAYLOAD DETAIL p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(8,grip=grip,hand=hand),[1,.35,-.5],400,410),(col*400,1270))
        draw.text((col*400+10,1244),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((14,1710),'Observed Farewell: raised presentation -> down-left grip exchange -> insert -> inward wrist roll -> recover. Numeric poses authored.',fill='white')
    draw.text((14,1740),'Reload-only rectangular shaft uses existing atlas; grip/cables/receiver/bayonet fixed. Exact0/1 dispatch canonical graph.',fill='white')
    draw.text((14,1770),'Actual footage and hashes: SOURCE.md + manifest. Native screen, hand contact, audio and performance remain pending.',fill='white')
    story=Image.new('RGB',(1600,1900),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL FAREWELL: True Vanguard / 2VaZGMrEfjQ / 2021-05-14 | independent authored normalized reload below',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225))
        x=j%4*400;y=55+j//4*605;story.paste(im,(x,y))
        draw.text((x+8,y+232),f"ACTUAL n={f['sourceFrameIndex']} / {f['timestampSeconds']:.5f}s",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.35,.55],400,295),(x,y+263))
        draw.text((x+8,y+567),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((14,1876),'60000/1001 fps; timebase1/60000; exact PNGs retained. Rectangular shaft from n1472; hidden poses/proportions authored.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w184-farewell-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=115:raise ValueError('Canonical element drift')
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
        entry_model=copy.deepcopy(item['model']) if i in (0,20) else dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))
        entries.append(dict(threshold=p,model=entry_model))
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w184_farewell.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W184',weapon='farewell',revision=1,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=115,bodyElements=106,movingElements=12,maxAssembledElements=118,endpointAssembledElements=115,elementLimit=1000,addedElements=3,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,
        geometryPolicy='All115 canonical elements/faces/UV/default paint retained. Body indices0..80,90..114. Heel81 and loop82..89 move with three reload-only shaft cuboids. Grip77/78, palm panels, backstrap, bayonet, cables, sights fixed.',
        payloadPolicy='One rigid intact represented magazine: heel/loop plus source-backed rectangular shaft. No scale animation, duplicate magazine, bullets or arbitrary mechanism.',
        sourceLimitation={'fullMagazineFidelityBlocked':False,'wholeMagazineRepresented':True,'exactOriginalShaftFidelityVerified':False,'canonicalShaftAbsent':True,'resolution':'Reload-only rectangular shaft authored from visible magazine in n1472, existing atlas only. Hidden dimensions/backface authored; exact original shaft fidelity and native contact remain unverified.','canonicalMovingNames':['heel']+['open_heel_loop_'+str(i) for i in range(8)],'canonicalMovingIndices':list(range(81,90))},
        reloadOnlyGeometry=dict(elements=reload_shaft(source),count=3,sourceFrameIndex=1472,sourceTimestampSeconds=1472*1001/60000,coreDimensions=[.84,3.72,1.28],heelJointLocalExtension=.070443,heelJointOverlapPoint=[8,7.20,8.30],uvPolicy='Exact canonical heel81 face UV rectangles; no atlas edits. Narrow seam strips use same heel UV; source parallel line detail, no invented bolts.',rigidAnchor=list(MAGAZINE_ANCHOR),sourceAxisDegrees=-14.00158177855961),
        semanticGroups={'body':106,'originalMagazineHeelAndLoop':9,'reloadOnlyShaft':3,'fixed':['grip_shoulder','grip_core','palm_panel_-1','palm_panel_1','backstrap','blade_body','rear_sight_floor']},
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineExtractionAxis=[0,-.970289,.241949],hipEndpoints=[0,20],
        endpointPolicy='Exact canonical item graph at progress0/1 and beyond1; negative/nonFP/ADS/inspect canonical. Seated shaft inside grip78 except .070443 local-Y heel joint extension; overlaps heel81 to keep payload intact.',
        normalizedPhases={'raiseCant':[0,.2],'heelRelease':[.2,.3],'downLeftWithdraw':[.3,.5],'incomingInsert':[.5,.72],'wristRoll':[.72,.86],'recover':[.86,1]},
        reference=REFERENCE,
        referencePolicy='Same Farewell identified by review title and continuous gameplay silhouette: bound green cables, magenta marks, finned front, blue rear, blade. No inventory name or item roll asserted. Lighting/shader appearance is not repainted into canonical.',
        motionAuthorship='Observed raised muzzle/cant, down-left whole-magazine grip exchange, insertion, inward wrist roll and recovery. Exact numeric poses, pivot, offsets, hidden hand movement and phase ratios authored interpretations. W183 matrix/guard/renderer/tests reused; no copied W183 trajectory.',
        authoredHiddenDetails='Magazine seat and exchange partly hand/screen occluded. Three shaft solids approximate visible rectangular shaft/parallel lines in n1472. Exact dimensions and unseen backface authored; no original mesh/bone extraction. No independently resolved bolt motion animated.',
        timingPolicy='Preserve local magazine15/RPM360/reload32ticks/cadence3.333333333333/burst1/shellReloadfalse and existing ammo/sound. Source duration and HUD8to15 are visual evidence only.',
        rotationConvention='JOML Rx Ry Rz; native motion converted by complete twohand carrier. Left F*T*F. Canonical element rotation retained.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration={'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'farewell','assetInputs':'float[1] normalized0..1; boolean[0] grip; string[0] ads/inspect guard; master owns route/admission/lifecycle'},
        nativeQueue=['Master route Farewell and validate 32tick clock/ammo/sound unchanged.','Both FP hands/grips: heel/shaft withdrawal, seat/contact, wrist roll, canonical recovery.','ADS/inspect/negative/nonFP fallback; cancel/equip/switch/death/disconnect and partial/empty/no-reserve.','Native pack load, audio listening, handIK and10-20weapon stability pending.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w184-farewell-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic core outputs/media hashes; 87 pack assets; 106+12=118 reload elements, canonical endpoints115; native pending')
if __name__=='__main__':main()
