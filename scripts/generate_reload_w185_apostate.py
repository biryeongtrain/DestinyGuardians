#!/usr/bin/env python3
"""Apostate W185: same-weapon original gameplay-led FP whole-magazine reload.
W184 rigid matrix/guard/renderer infrastructure only; independently authored poses.
--verify uses retained output image hashes, never requires external source media.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w185/apostate')
KEY='weapon_reload_w185_apostate/apostate'
SOURCE=A/'models/weapon_surface_w123/apostate.json'
TWOHAND=A/'models/weapon/sniper_rifle/apostate_twohand.json'
ITEM=A/'items/weapon/apostate.json'
TEXTURE=A/'textures/item/weapon/w123/apostate.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.6,8.4)
MAGAZINE_ANCHOR=(8.,8.6,3.1)
MAGAZINE_NAMES=('magazine/main','magazine/toe','magazine/heel','magazine/base')
# Independently authored from Aztecross n9888..9966: near-vertical right-edge
# lift, front-underbody downward withdrawal and palm-up whole-magazine seating.
# Source recovery is interrupted by rift; final lowering is explicitly authored.
KEYS=(
 (0,(0,0,0),(0,0,0),(0,0,0)),
 (.10,(10,-3,-4),(.10,-.05,.05),(0,0,0)),
 (.22,(78,-6,-7),(.40,.05,.20),(0,0,0)),
 (.34,(88,-7,-9),(.55,.10,.22),(-.10,-3.90,.15)),
 (.46,(87,-6,-8),(.55,.10,.22),(-.45,-4.30,-.40)),
 (.58,(86,-5,-7),(.50,.08,.20),(.10,-1.55,.12)),
 (.68,(84,-4,-6),(.45,.06,.18),(0,.06,0)),
 (.74,(83,-4,-6),(.42,.04,.16),(0,0,0)),
 (.84,(48,-2,-3),(.22,-.03,.08),(0,0,0)),
 (.94,(11,-1,-1),(.04,-.04,.01),(0,0,0)),
 (1,(0,0,0),(0,0,0),(0,0,0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/apostate.json': '846daf98a5efa055722fcac68d6020636aa1ed3f8c428c4870ada7eee8bd4f99', 'src/main/resources/assets/destiny/textures/item/weapon/w123/apostate.png': 'aa888e15fe0f9e4cb0a858971fade9cb60689fec40acb1fcfdead6cc6bd59b9e', 'src/main/resources/assets/destiny/items/weapon/apostate.json': 'dfc64a7c51cbd2a4a11065858a9127a92585b6f7702cab4240611933441c73f3', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_inspect_twohand.json': '1d8230f62d97728f2167b50d54909a183f499a930212a070646f39e4162a4a0f', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_inspect.json': 'ce797223b0d95370e770042bdf38172d2b2d46aa4fba277251a59773e1f63fc8', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate.json': 'b5a2400a8cbe5d281783dd5f4850ac6d3f5847aa84db16b029288ec9c0b63923', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_ads.json': '283bd4a366dacf7853636881febca94454176e14c5397720ac5704cffb6465d4', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_twohand.json': 'a715871885be1b1c0a9e55aa512c16a70a0308dc426134a9cc9e9028cd1ced72', 'src/main/resources/assets/destiny/models/weapon/sniper_rifle/apostate_ads_twohand.json': '1bb68509bf972213fd6f9e7bcd652d80d1b3d01f095731b4f2ebb36d3098b339'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=h835sF3Ouvo', 'title': 'Apostate is the Best Sniper in the current Sandbox (Apostate Sniper Review) | Destiny 2 Shadowkeep', 'creator': 'Aztecross', 'uploadDate': '20191107', 'fpsNumerator': 60, 'fpsDenominator': 1, 'sourceTimebase': '1/15360', 'actionFrameRange': [9888, 9966], 'actionSeconds': [164.8, 166.1], 'sourceVideoFile': '/private/tmp/w185-apostate-report/original.mp4', 'sourceMetadataFile': '/private/tmp/w185-apostate-report/original.info.json', 'sourceVideoSha256': '495d4bc60eae5144350194f43408d59f645574e21a3a97caf5856264f4c31189', 'sourceMetadataSha256': 'f1c41bfc5c9914574fda5c0355474d1c42064877bd66f5ac5c481c709be54d2d', 'inspectedActualFrames': True, 'shaderPolicy': 'Matching red chitin default appearance; canonical atlas unchanged. Source HUD7/perks do not set local6 capacity or54tick clock.', 'frames': [{'path': '/private/tmp/w185-apostate-report/action-01.png', 'sha256': '98d42b98d910f9f4efd6ca0c2e44501e7898b5f0af05a145b85ed242461a4fd0', 'sourceFrameIndex': 4500, 'pts': 1152000, 'timestampSeconds': 75.0, 'nearestAuthoredProgress': 0, 'observation': 'Inventory explicitly APOSTATE; matching red chitin, silver braces, teal bindings and green optic.'}, {'path': '/private/tmp/w185-apostate-report/action-02.png', 'sha256': '776dbf18489aee3c5d38aaa4e3913ac6f96461f320f60d697193166cff41eb09', 'sourceFrameIndex': 9876, 'pts': 2528256, 'timestampSeconds': 164.6, 'nearestAuthoredProgress': 0, 'observation': 'Hip presentation after ability; matching rifle.'}, {'path': '/private/tmp/w185-apostate-report/action-03.png', 'sha256': 'ec23e7251d489f90699e23048420b8f4c520d539789f69d0ff3bbb129ae37121', 'sourceFrameIndex': 9888, 'pts': 2531328, 'timestampSeconds': 164.8, 'nearestAuthoredProgress': 0, 'observation': 'Last hip hold before reload; source HUD2, reserve6.'}, {'path': '/private/tmp/w185-apostate-report/action-04.png', 'sha256': 'cfdddd331756ee48013f8af12e1cc9a3b011c9be45eceaee8b6ad59f886970b6', 'sourceFrameIndex': 9894, 'pts': 2532864, 'timestampSeconds': 164.9, 'nearestAuthoredProgress': 0.08, 'observation': 'Support hand opens while rifle begins lifting.'}, {'path': '/private/tmp/w185-apostate-report/action-05.png', 'sha256': '5102b4a399354fc9ff4520f7de0f5d0abca0c7735116640e8c7d769626f68963', 'sourceFrameIndex': 9900, 'pts': 2534400, 'timestampSeconds': 165.0, 'nearestAuthoredProgress': 0.18, 'observation': 'Muzzle lifts steeply at right; support hand leaves fore-end.'}, {'path': '/private/tmp/w185-apostate-report/action-06.png', 'sha256': '0744d1a1e01a2a40b05e5bda187f2f0c5f81946112ca3ea459adb81f7a40a811', 'sourceFrameIndex': 9906, 'pts': 2535936, 'timestampSeconds': 165.1, 'nearestAuthoredProgress': 0.23, 'observation': 'Receiver rises; underside magazine becomes accessible.'}, {'path': '/private/tmp/w185-apostate-report/action-07.png', 'sha256': '8f61429627ae062adfa363a19bafdd391b4b55ccac085d38800df9de8e1e4a6b', 'sourceFrameIndex': 9912, 'pts': 2537472, 'timestampSeconds': 165.2, 'nearestAuthoredProgress': 0.32, 'observation': 'Near-vertical receiver at right; support hand descends toward magazine.'}, {'path': '/private/tmp/w185-apostate-report/action-08.png', 'sha256': '3f33f825ec4c07d6ef041592e9bf166260e0a47b1dcdde22136ae50d6d10cb41', 'sourceFrameIndex': 9921, 'pts': 2539776, 'timestampSeconds': 165.35, 'nearestAuthoredProgress': 0.4, 'observation': 'Intact outgoing dark magazine below exposed seat; upper shaft visible.'}, {'path': '/private/tmp/w185-apostate-report/action-09.png', 'sha256': '4505f5672311eb2d7f3eb025e2f2c6d0f965390f9ea1d816a482296a0557ccca', 'sourceFrameIndex': 9930, 'pts': 2542080, 'timestampSeconds': 165.5, 'nearestAuthoredProgress': 0.48, 'observation': 'Exchange low in frame; hand/edge obscure lower path.'}, {'path': '/private/tmp/w185-apostate-report/action-10.png', 'sha256': 'e305513d6aee373585075c53eeec5ad1c4db4da36027a38df9d9ecd227ee19eb', 'sourceFrameIndex': 9939, 'pts': 2544384, 'timestampSeconds': 165.65, 'nearestAuthoredProgress': 0.56, 'observation': 'Incoming complete long dark magazine rises in support hand.'}, {'path': '/private/tmp/w185-apostate-report/action-11.png', 'sha256': '91fdd9244dc001d7a1cdfab0e6d7bb5e8b35bbe7e898719697121b5e5ea29c94', 'sourceFrameIndex': 9948, 'pts': 2546688, 'timestampSeconds': 165.8, 'nearestAuthoredProgress': 0.66, 'observation': 'Support palm drives magazine toward underside socket.'}, {'path': '/private/tmp/w185-apostate-report/action-12.png', 'sha256': 'a79dd5b57d74965f0c75cb553fec1314a3cec4d40598e8d45b408f6657c44eb5', 'sourceFrameIndex': 9957, 'pts': 2548992, 'timestampSeconds': 165.95, 'nearestAuthoredProgress': 0.72, 'observation': 'Magazine seated; source ammo refreshed to7, which does not change local6 capacity.'}, {'path': '/private/tmp/w185-apostate-report/action-13.png', 'sha256': '5fc91bbf28b8e72263bc0fddeaf5822856f861b69f829ce79458918335e5003f', 'sourceFrameIndex': 9963, 'pts': 2550528, 'timestampSeconds': 166.05, 'nearestAuthoredProgress': 0.76, 'observation': 'Receiver remains lifted; hand releases magazine.'}, {'path': '/private/tmp/w185-apostate-report/action-14.png', 'sha256': '28bbd13a124074561fca564b71991593f73c5481a74502b3ec47b8a2ded72b01', 'sourceFrameIndex': 9966, 'pts': 2551296, 'timestampSeconds': 166.1, 'nearestAuthoredProgress': 0.78, 'observation': 'Last reload hold before ability cancels presentation recovery.'}, {'path': '/private/tmp/w185-apostate-report/action-15.png', 'sha256': '39059e8359d1bfc5641757183915fb14d87d94cd5927beb0d091ee8225014d92', 'sourceFrameIndex': 9972, 'pts': 2552832, 'timestampSeconds': 166.2, 'nearestAuthoredProgress': 0.8, 'observation': 'Rift cast begins; NOT a reload recovery reference.'}, {'path': '/private/tmp/w185-apostate-report/action-16.png', 'sha256': '1a91f3dc3f244b3996f39b6d80f6b0b398d6c50ff124892b675196eed90d2ef8', 'sourceFrameIndex': 9984, 'pts': 2555904, 'timestampSeconds': 166.4, 'nearestAuthoredProgress': 1, 'observation': 'Rift cast, third-person transition; NOT a reload reference.'}]}

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

def is_payload(e):return e['name'] in MAGAZINE_NAMES

def reload_shaft(source):
    # The full dark incoming magazine/upper neck is visible n9939. Add only
    # the short seated portion hidden in socket28, retaining the original atlas.
    shaft=copy.deepcopy(source['elements'][29])
    shaft.update(name='magazine_shaft_upper',**{'from':[7.57,8.55,1.30],'to':[8.43,9.10,4.90]})
    return [shaft]


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
    # Four canonical magazine solids and small upper shaft move as one rigid payload.
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
                model['elements']=[e for e in model['elements'] if e['name'].startswith(('receiver/','foreend/filled-core','magazine/','magazine_shaft_'))]
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
    draw.text((14,12),'W185 APOSTATE | reference-led canonical JSON motion | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.55,-.7],[-1,.45,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,310),(col*400,70))
        draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.35,.55];groups=[posed(i) for i in (0,7,13,20)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,350)
    for col,(i,g) in enumerate(zip((0,7,13,20),groups)):
        sheet.paste(raster(g,cam,400,350,extent),(col*400,420))
        draw.text((col*400+10,396),f'p={i/20:.2f} / fixed camera + common scale',fill='white')
    draw.text((14,794),'115 active elements = 110 fixed body + 4 whole-magazine solids + 1 hidden upper shaft. Canonical endpoints =114.',fill='white')
    details=[posed(i,detail=True) for i in (0,7,10,13)]
    detail_cam=[1,.25,.25]
    detail_extent=helper['frame'](np.concatenate([t[0] for group in details for t in group]),detail_cam,400,350)
    for col,(i,group) in enumerate(zip((0,7,10,13),details)):
        sheet.paste(raster(group,detail_cam,400,350,detail_extent),(col*400,855))
        draw.text((col*400+10,828),f'RIGID MAGAZINE DETAIL p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(7,grip=grip,hand=hand),[1,.35,-.5],400,410),(col*400,1270))
        draw.text((col*400+10,1244),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((14,1710),'Observed: near-vertical right-edge lift -> front-underbody withdraw -> incoming full magazine -> palm seat. Recovery authored.',fill='white')
    draw.text((14,1740),'Reload-only hidden neck uses original magazine UV; socket28, stock, trigger, optic and fore-end fixed. Exact0/1 dispatch canonical full graph.',fill='white')
    draw.text((14,1770),'Actual footage and hashes: SOURCE.md + manifest. Native screen, hand contact, audio and performance remain pending.',fill='white')
    story=Image.new('RGB',(1600,2520),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL APOSTATE: Aztecross / h835sF3Ouvo / 2019-11-07 | independent authored normalized reload below',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225))
        x=j%4*400;y=55+j//4*605;story.paste(im,(x,y))
        draw.text((x+8,y+232),f"ACTUAL n={f['sourceFrameIndex']} / {f['timestampSeconds']:.5f}s",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.35,.55],400,295),(x,y+263))
        draw.text((x+8,y+567),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((14,2490),'OFFLINE / NO HANDS / NOT NATIVE. 60fps; exact retained source PNGs. Rift interrupts recovery; authored lowering. Product paint unchanged.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w185-apostate-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=114:raise ValueError('Canonical element drift')
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
    authored={Path('scripts/generate_reload_w185_apostate.py'),Path('scripts/qa/test_reload_w185_apostate.py'),Path('src/test/java/kim/biryeong/destiny/weapon/ReloadW185ApostateTest.java'),ART/'SOURCE.md'}
    owned=expected_output_paths()|authored
    if len(owned)!=94:raise ValueError('Owned set must be exact94')
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_surface_w123_hammerhead.py'),*sorted(authored)]
    emit(ART/'manifest.json',dict(stage='W185',weapon='apostate',revision=1,itemModel='destiny:'+KEY,
        ownedPaths=sorted(map(str,owned)),ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=114,bodyElements=110,movingElements=5,maxAssembledElements=115,endpointAssembledElements=114,elementLimit=1000,addedElements=1,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,
        geometryPolicy='All114 W123 canonical solids, faces, rotations, UV and default paint retained verbatim. Moving29/30/31/32 main/toe/heel/base; fixed socket28 and remaining110. Canonical files untouched.',
        payloadPolicy='Complete original four-solid magazine plus one small upper shaft move rigidly together. One assembly proxies outgoing/incoming; no scale hiding, bullets, invented bolt stroke or hand IK.',
        sourceLimitation=dict(canonicalHiddenNeckAbsent=True,fullMagazineFidelityBlocked=False,exactOriginalShaftFidelityVerified=False,resolution='Source incoming full magazine visible n9939. Small authored upper shaft fills only hidden seated portion inside socket28; exact occluded interface and native hand clearance unverified.',canonicalMovingNames=list(MAGAZINE_NAMES),canonicalMovingIndices=[29,30,31,32]),
        reloadOnlyGeometry=dict(elements=reload_shaft(source),count=1,sourceFrameIndex=9939,sourceTimestampSeconds=165.65,coreDimensions=[.86,.55,3.60],uvPolicy='Existing magazine/main faces copied unchanged; original atlas only.',rigidAnchor=list(MAGAZINE_ANCHOR)),
        semanticGroups={'body':110,'originalWholeMagazine':4,'reloadOnlyHiddenShaft':1,'fixed':['magazine/socket','receiver','foreend','stock','trigger','optic','bindings','thorns']},
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineExtractionAxis=[0,-1,0],hipEndpoints=[0,20],
        endpointPolicy='Exact0/1 and overshoot select complete canonical graph; children0/20 exact accepted display. Negative/nonFP/ADS/inspect canonical guards. Added shaft seated entirely inside fixed socket28.',
        normalizedPhases={'lift':[0,.22],'withdraw':[.22,.34],'lowerExchange':[.34,.46],'incoming':[.46,.58],'seat':[.58,.68],'release':[.68,.74],'authoredRecovery':[.74,1]},
        reference=REFERENCE,
        referencePolicy='Actual same-weapon Aztecross review. Inventory75s identifies APOSTATE; continuous near-vertical reload164.8..166.1s shows full-magazine exchange and ammo2->7. Rift starts166.2s; recovery is authored, not measured. Original source frames, PTS/fps and hashes retained outside repo.',
        authoredPolicy='Individually authored Apostate near-vertical right-edge lift, front-underbody vertical withdrawal, low exchange, palm-up whole-magazine insertion and small seat overtravel. W184 infrastructure reused only; trajectory, pivot, extraction axis and phases independently authored.',
        authoredHiddenDetails='Occluded lower exchange, exact angles/offsets, shaft proportions, normalized timings and post-seat recovery are authored. Source player casts rift after seat; rift frames are context only. No extracted bones or measured animation fidelity claim.',
        timingPolicy='Preserve local6 rounds,140RPM,cadence8.571428571429ticks,burst1,reload54ticks,shellReloadfalse, all ammo and sound.21 samples every2.7ticks; source HUD7/RapidHit does not set product clock or capacity.',
        rotationConvention='JOML Rx Ry Rz; unchanged uniform canonical scale; rigid motion carried to twohand; left apply F*T*F. Original XYZ element rotations retained.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration=dict(workerRuntimeEdited=False,masterOwnsRegistryRuntime=True,requiredMasterModel='destiny:'+KEY,catalogId='apostate',assetInputs='float1 progress0..1; boolean0 grip; string0 ads/inspect guard. Master owns route/admission/lifecycle.'),
        nativeQueue=['Master route/admit apostate with54tick/6round/140RPM unchanged timing, ammo and sound.',
        'Both FP hands/grips: complete main/toe/heel/base/shaft withdrawal, socket28 fixed, hand fit and seat/recovery.',
        'ADS/inspect/negative/nonFP guards; cancellation/equip/switch/death/disconnect and partial/empty/no-reserve lifecycle.',
        'Actual pack/framebuffer, unchanged audio listening and10-20weapon stability remain pending master; locked CU is not native verification.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w185-apostate-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs/media hashes;87 pack assets;110+5=115 active elements,114 canonical endpoints;native pending')
if __name__=='__main__':main()
