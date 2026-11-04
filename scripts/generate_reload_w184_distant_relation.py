#!/usr/bin/env python3
"""Distant Relation W184: same-weapon original gameplay-led FP whole-magazine reload.
W183 rigid matrix/guard/renderer infrastructure only; independently authored poses.
--verify uses retained output image hashes, never requires external source media.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w184/distant_relation')
KEY='weapon_reload_w184_distant_relation/distant_relation'
SOURCE=A/'models/weapon_surface_w123/distant_relation.json'
TWOHAND=A/'models/weapon/scout_rifle/distant_relation_twohand.json'
ITEM=A/'items/weapon/distant_relation.json'
TEXTURE=A/'textures/item/weapon/w123/distant_relation.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.55,8.30)
MAGAZINE_ANCHOR=(8.,6.69,10.72)
MAGAZINE_NAMES=('magazine_body','magazine_floor')
# DFP n20070..20184: steep right-edge lift, rear-understock exchange, quick lower/dip.
# Numeric trajectory and occluded exchange are authored, not tracked bones.
KEYS=(
 (0,(0,0,0),(0,0,0),(0,0,0)),
 (.08,(16,-2,-2),(.08,-.10,0),(0,0,0)),
 (.20,(70,7,-10),(.30,.15,.18),(0,0,0)),
 (.32,(75,9,-12),(.38,.23,.22),(.20,-4.50,-3.10)),
 (.44,(73,8,-13),(.38,.23,.22),(-.35,-4.50,-3.10)),
 (.60,(71,9,-12),(.35,.20,.20),(-.04,-.60,-.42)),
 (.66,(68,8,-10),(.32,.17,.17),(0,0,0)),
 (.74,(35,4,-5),(.18,.04,.08),(0,0,0)),
 (.82,(4,1,-1),(.04,-.08,.02),(0,0,0)),
 (.90,(-6,-1,1),(0,-.16,0),(0,0,0)),
 (1,(0,0,0),(0,0,0),(0,0,0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/distant_relation.json': 'd10b3875818623b552230fa53bfa26625e3faf86db450ec964aaabd1bb59f8e5', 'src/main/resources/assets/destiny/textures/item/weapon/w123/distant_relation.png': '693ded07b8b1f398bf9a9d9791ce49af945a4e524d11a200f9239943d64a161a', 'src/main/resources/assets/destiny/items/weapon/distant_relation.json': 'f27c06fa03339ee11092a836cf078cf3d114a078c3e66a1ebd0d1ab1799fd473', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_inspect_twohand.json': '22615532c09371ff3e0a8b4a3d944d5cfef5f3c852d70acec959016ae274d69d', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_ads_twohand.json': 'b08764a5018b4e6c20e50ec381ffe9742e32a7dad936a32c8cfc9cb44f2cb15f', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_inspect.json': 'da1f721a14d5d231aba7c9ee25adeed051b91a6ccdc42438f53f4c6c1ed9de6a', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation.json': '126bd1a3aea23bbbb77ae010441e102a751a281defd4e59f6aa6f46ba2ae4801', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_ads.json': '30444a73329e00d1b7d006ef82777fc58357cbc1d2416a59bb52d7ada81b82bf', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/distant_relation_twohand.json': '844668f0dbc31731c018e736f25ae4a1720ce18b9f1c4ab5846c41898fa898fb'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=4SvDoK8HidQ', 'title': 'The Gambit Scout Rifle! Distant Relation - Destiny 2 Forsaken', 'creator': 'DFP', 'uploadDate': '20180922', 'fpsNumerator': 60, 'fpsDenominator': 1, 'sourceTimebase': '1/15360', 'actionFrameRange': [20070, 20184], 'actionSeconds': [334.5, 336.4], 'sourceVideoFile': '/private/tmp/w184-distant-report/original.mp4', 'sourceMetadataFile': '/private/tmp/w184-distant-report/original.info.json', 'sourceVideoSha256': '31e1cd1ac852620de4bab761a6ffa86b35eb429bbb40bd4082859dec643f88ea', 'sourceMetadataSha256': 'c38a003682c88d3f320e895a57683fa4c20fa5994e82c6d3540134b06dae6965', 'inspectedActualFrames': True, 'shaderPolicy': 'White shader used only for silhouette/motion evidence; unchanged canonical dark teal/walnut atlas supplies product paint. Source HUD17 does not change local16 capacity.', 'frames': [{'path': '/private/tmp/w184-distant-report/reference-01.png', 'sha256': '5982f184a9b772e2e687b891583f31397c292ecce77bd970cc96b7cc387a94ae', 'sourceFrameIndex': 300, 'pts': 76800, 'timestampSeconds': 5.0, 'nearestAuthoredProgress': 0, 'observation': 'Inventory explicitly DISTANT RELATION; same thumb-loop stock, open lower hand loop, exposed action and short box optic. White shader differs from canonical default paint.'}, {'path': '/private/tmp/w184-distant-report/reference-02.png', 'sha256': 'a43ce6efd9166a9c97d0de568fcf4de73d0f8f226d6e834ece62905cdf133226', 'sourceFrameIndex': 20064, 'pts': 5136384, 'timestampSeconds': 334.4, 'nearestAuthoredProgress': 0, 'observation': 'Pre-reload hip presentation after firing; HUD7.'}, {'path': '/private/tmp/w184-distant-report/reference-03.png', 'sha256': '74029a1f3281bfe2a36d2fe92439a8f5227097de26b347bea3068130af71bee3', 'sourceFrameIndex': 20070, 'pts': 5137920, 'timestampSeconds': 334.5, 'nearestAuthoredProgress': 0, 'observation': 'Last pre-lift hip pose.'}, {'path': '/private/tmp/w184-distant-report/reference-04.png', 'sha256': 'd59e4681802c38cca8b54aaee17bb8ef723acb126ff5433854dd3b707dfe1136', 'sourceFrameIndex': 20076, 'pts': 5139456, 'timestampSeconds': 334.6, 'nearestAuthoredProgress': 0.1, 'observation': 'Rapid lift/cant, receiver at right; support hand leaves fore-end.'}, {'path': '/private/tmp/w184-distant-report/reference-05.png', 'sha256': '437868db7257f0e6a59f9e11f094fb426ec3de618319cbb1cee51623ade815cb', 'sourceFrameIndex': 20082, 'pts': 5140992, 'timestampSeconds': 334.7, 'nearestAuthoredProgress': 0.2, 'observation': 'Steep muzzle-up hold; rear-understock magazine access, right hand remains at grip.'}, {'path': '/private/tmp/w184-distant-report/reference-06.png', 'sha256': '775f471c4bae8854635bcfa083d66ffc6af49903f474c5f8657cc37797dad005', 'sourceFrameIndex': 20094, 'pts': 5144064, 'timestampSeconds': 334.9, 'nearestAuthoredProgress': 0.3, 'observation': 'Outgoing intact dark box magazine visible below stock; support hand/edge conceal extraction origin.'}, {'path': '/private/tmp/w184-distant-report/reference-07.png', 'sha256': 'd5d94977e03c2b15ea5745d4ad738c84cb1cc6c454249a92d207d534f6d07e11', 'sourceFrameIndex': 20106, 'pts': 5147136, 'timestampSeconds': 335.1, 'nearestAuthoredProgress': 0.4, 'observation': 'Rifle held up; exchange below frame, exact hidden path authored.'}, {'path': '/private/tmp/w184-distant-report/reference-08.png', 'sha256': 'dd6b4ad4ec8b179b019b671459b316992d3c17e5fa8f9ca317a7e488649cc3df', 'sourceFrameIndex': 20118, 'pts': 5150208, 'timestampSeconds': 335.3, 'nearestAuthoredProgress': 0.5, 'observation': 'Incoming long rectangular magazine with fluted broad face rises from below-left in support hand.'}, {'path': '/private/tmp/w184-distant-report/reference-09.png', 'sha256': '529b1659a61f794cebd478e5946f22e221571c87480f6ee3b601a7f7b78b3836', 'sourceFrameIndex': 20124, 'pts': 5151744, 'timestampSeconds': 335.4, 'nearestAuthoredProgress': 0.6, 'observation': 'Incoming magazine approaches rear-understock seat; upper tip and final lock occluded by hand/stock; HUD17.'}, {'path': '/private/tmp/w184-distant-report/reference-10.png', 'sha256': '628879edfe3c6360223d38008df8f79731d3e2ccd7b7d5506251d2d14cfb9f42', 'sourceFrameIndex': 20130, 'pts': 5153280, 'timestampSeconds': 335.5, 'nearestAuthoredProgress': 0.65, 'observation': 'Support palm covers seating area; entire magazine returns to stock.'}, {'path': '/private/tmp/w184-distant-report/reference-11.png', 'sha256': 'a66b6232a40204071df98d00c87ac9468e7f29e679ca5ab27d68dd1bea6d853f', 'sourceFrameIndex': 20136, 'pts': 5154816, 'timestampSeconds': 335.6, 'nearestAuthoredProgress': 0.7, 'observation': 'Carrier begins lowering; support hand obscures rear underside.'}, {'path': '/private/tmp/w184-distant-report/reference-12.png', 'sha256': 'b0e5f490e85ab446f6e6ada3b00f683b057e4e2049519ddc1ac9a119c713d082', 'sourceFrameIndex': 20148, 'pts': 5157888, 'timestampSeconds': 335.8, 'nearestAuthoredProgress': 0.8, 'observation': 'Fast lower from upright presentation; support hand moves forward.'}, {'path': '/private/tmp/w184-distant-report/reference-13.png', 'sha256': '01eb8dd009154b2a522490030ff40799386e3a7b7ccad7a23d9b948cd55dc588', 'sourceFrameIndex': 20160, 'pts': 5160960, 'timestampSeconds': 336.0, 'nearestAuthoredProgress': 0.85, 'observation': 'Support hand advances; receiver settles.'}, {'path': '/private/tmp/w184-distant-report/reference-14.png', 'sha256': '712593a492b727f7e00699bfe5fdf942d0450175a9413d8f2097fa4ecd28432d', 'sourceFrameIndex': 20172, 'pts': 5164032, 'timestampSeconds': 336.2, 'nearestAuthoredProgress': 0.9, 'observation': 'Further small downward settling motion.'}, {'path': '/private/tmp/w184-distant-report/reference-15.png', 'sha256': '548fa648b8766c8987c1bebd97aca8509f159c069882d841f077943458d9042e', 'sourceFrameIndex': 20184, 'pts': 5167104, 'timestampSeconds': 336.4, 'nearestAuthoredProgress': 0.95, 'observation': 'Small settling dip; source player also moves view downward.'}, {'path': '/private/tmp/w184-distant-report/reference-16.png', 'sha256': 'b5af7321a27e7704954aaad1afc34baf449f7b033b0d3dcc028b6c51342fa0e0', 'sourceFrameIndex': 20208, 'pts': 5173248, 'timestampSeconds': 336.8, 'nearestAuthoredProgress': 1, 'observation': 'Recovered hip presentation before switching weapon; exact local endpoint authored.'}]}

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
    # Incoming full box visible n20118. Only hidden upper neck is added;
    # original body/floor and existing fluted face paint remain exact.
    neck=copy.deepcopy(source['elements'][58])
    neck.update(name='magazine_shaft_upper',**{'from':[7.73,6.80,11.50],'to':[8.27,7.00,13.00]})
    return [neck]

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
    # Original body/floor and reference-backed reload-only upper neck move as one rigid payload.
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
                model['elements']=[e for e in model['elements'] if e['name'].startswith(('stock_lower','stock_main','magazine','sling_mount'))]
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
    draw.text((14,12),'W184 DISTANT RELATION | reference-led canonical JSON motion | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.55,-.7],[-1,.45,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,310),(col*400,70))
        draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.35,.55];groups=[posed(i) for i in (0,7,13,20)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,350)
    for col,(i,g) in enumerate(zip((0,7,13,20),groups)):
        sheet.paste(raster(g,cam,400,350,extent),(col*400,420))
        draw.text((col*400+10,396),f'p={i/20:.2f} / fixed camera + common scale',fill='white')
    draw.text((14,794),'89 active elements = 86 canonical body + body/floor magazine + 1 hidden upper neck. Canonical endpoints =88.',fill='white')
    details=[posed(i,detail=True) for i in (0,7,10,13)]
    detail_cam=[1,.25,.25]
    detail_extent=helper['frame'](np.concatenate([t[0] for group in details for t in group]),detail_cam,400,350)
    for col,(i,group) in enumerate(zip((0,7,10,13),details)):
        sheet.paste(raster(group,detail_cam,400,350,detail_extent),(col*400,855))
        draw.text((col*400+10,828),f'RIGID MAGAZINE DETAIL p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(7,grip=grip,hand=hand),[1,.35,-.5],400,410),(col*400,1270))
        draw.text((col*400+10,1244),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((14,1710),'Observed: steep lift -> rear-understock withdraw -> lower-left incoming box -> seat -> quick lower + settling dip. Numeric poses authored.',fill='white')
    draw.text((14,1740),'Reload-only hidden neck uses original magazine UV; stock/loop/bolt/optic fixed. Exact0/1 dispatch canonical full graph.',fill='white')
    draw.text((14,1770),'Actual footage and hashes: SOURCE.md + manifest. Native screen, hand contact, audio and performance remain pending.',fill='white')
    story=Image.new('RGB',(1600,2520),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL DISTANT RELATION: DFP / 4SvDoK8HidQ / 2018-09-22 | independent authored normalized reload below',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225))
        x=j%4*400;y=55+j//4*605;story.paste(im,(x,y))
        draw.text((x+8,y+232),f"ACTUAL n={f['sourceFrameIndex']} / {f['timestampSeconds']:.5f}s",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.35,.55],400,295),(x,y+263))
        draw.text((x+8,y+567),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((14,2490),'OFFLINE / NO HANDS / NOT NATIVE. 60fps; exact retained source PNGs. White source shader does not change product default paint.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w184-distant-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=88:raise ValueError('Canonical element drift')
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w184_distant_relation.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W184',weapon='distant_relation',revision=1,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=88,bodyElements=86,movingElements=3,maxAssembledElements=89,endpointAssembledElements=88,elementLimit=1000,addedElements=1,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,
        geometryPolicy='All88 canonical W132 solids/faces/rotations/UV/default dye unchanged. Magazine indices58/59 plus1 reload-only hidden upper neck; remaining86 body fixed. Canonical files untouched.',
        payloadPolicy='Original magazine_body and magazine_floor plus narrow upper neck move as one rigid payload. Existing fluted face UV retained. One assembly proxies outgoing/incoming; no scale hiding, bullets or invented mechanism.',
        sourceLimitation=dict(canonicalHiddenNeckAbsent=True,fullMagazineFidelityBlocked=False,exactOriginalShaftFidelityVerified=False,resolution='Complete represented original body+floor with authored narrow upper neck. Exact occluded feed interface/neck proportions and native hand clearance remain unverified; no exact shaft fidelity completion claim.',canonicalMovingNames=list(MAGAZINE_NAMES),canonicalMovingIndices=[58,59]),
        reloadOnlyGeometry=dict(elements=reload_shaft(source),count=1,sourceFrameIndex=20118,sourceTimestampSeconds=335.3,coreDimensions=[.54,.20,1.50],uvPolicy='All existing magazine_body face UV unchanged. No new atlas.',rigidAnchor=list(MAGAZINE_ANCHOR),sourceAxisDegrees=-54.39546601956689),
        semanticGroups={'body':86,'originalMagazineBodyAndFloor':2,'reloadOnlyHiddenNeck':1,'fixed':['stock_grip','stock_main_solid','loop_front','loop_bottom','loop_back','bolt_slide','bolt_stem','bolt_knob','optic_housing_core']},
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineExtractionAxis=[0,-.813054693,-.582187312],hipEndpoints=[0,20],
        endpointPolicy='Progress0/1 and overshoot select exact original canonical item graph; children0/20 exact canonical displays. Negative/nonFP/ADS/inspect canonical guard. Added upper neck fully hidden inside original magazine/stock when seated.',
        normalizedPhases={'reachLift':[0,.20],'withdraw':[.20,.32],'lowerExchange':[.32,.44],'incoming':[.44,.60],'seat':[.60,.66],'fastLower':[.66,.82],'settlingDip':[.82,.92],'canonicalRecover':[.92,1]},
        reference=REFERENCE,
        referencePolicy='Actual same-weapon DFP release-era video: inventory DISTANT RELATION at5s and continuous matching rifle sequence334.5..336.4s. White shader is not adopted; canonical teal/walnut paint remains exact. Frame indices/PTS/hashes retained; viewed actual frames before authoring.',
        authoredPolicy='Unique Distant Relation steep right-edge lift, rear-understock withdrawal, lower-left incoming box, seated quick lowering and settling dip. W183 reused graph/matrix/renderer/tests only, not trajectory. Exact angles/offsets/pivot/normalized times are authored from visible evidence.',
        authoredHiddenDetails='Hands and screen edge conceal release/seat and lower exchange. Narrow upper neck proportions and hidden feed interface are authored; no measured bones, extracted animation, separate bolt stroke, spent magazine or hand IK.',
        timingPolicy='Preserve local16 rounds,180RPM,cadence6.666666666667ticks,burst1,reload44ticks,shellReloadfalse, all ammo transfer and sound.21 visual samples every2.2ticks; source HUD17/perks/reload speed do not set gameplay.',
        rotationConvention='JOML Rx Ry Rz display rotation, unchanged uniform canonical scale; complete native motion carried into twohand; left apply F*T*F. Original XYZ element rotations retained.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration=dict(workerRuntimeEdited=False,masterOwnsRegistryRuntime=True,requiredMasterModel='destiny:'+KEY,catalogId='distant_relation',assetInputs='float1 progress0..1; boolean0 grip; string0 ads/inspect guard. Master owns route/admission/lifecycle.'),
        nativeQueue=['Master admit/route distant_relation; retain44tick clock/16round/180RPM and existing sound/ammo behavior.',
        'Both FP hands/grips: whole magazine extraction, source-backed hidden neck proportions, support-hand fit, clearance/seat, quick lowering and endpoint recovery.',
        'ADS/inspect/negative/nonFP fallback; cancellation/equip/switch/death/disconnect; partial/empty/no-reserve lifecycle.',
        'Native pack load, hand contact, unchanged audio listening and10-20weapon stability pending.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w184-distant-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs/media hashes;87 pack assets;86+3=89 active elements,88 canonical endpoints;native pending')
if __name__=='__main__':main()
