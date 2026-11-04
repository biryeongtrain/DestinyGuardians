#!/usr/bin/env python3
"""Code Duello W187: same-weapon original gameplay-led FP whole ribbed-canister reload.
W185 rigid matrix/guard/renderer infrastructure only; independently authored poses.
--verify uses retained output image hashes, never requires external source media.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w187/code_duello')
KEY='weapon_reload_w187_code_duello/code_duello'
SOURCE=A/'models/weapon_surface_w123/code_duello.json'
TWOHAND=A/'models/weapon/rocket_launcher/code_duello_twohand.json'
ITEM=A/'items/weapon/code_duello.json'
TEXTURE=A/'textures/item/weapon/w123/code_duello.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,7.4,16.)
MAGAZINE_ANCHOR=(8.,12.,10.9)
CANISTER_INDICES=tuple(range(26))+tuple(range(35,46))+tuple(range(53,64))+tuple(range(71,79))
# Independently authored Code Duello: right-edge rise, whole spiral canister
# axial withdrawal, offscreen exchange, connector-first seat, short release.
ORIGINAL_KEYS=(
 (0,(0,0,0),(0,0,0),(0,0,0)),
 (.08,(12,-2,-5),(.15,-.35,.10),(0,0,0)),
 (.18,(78,-8,-12),(.90,-.40,.60),(0,0,0)),
 (.27,(82,-10,-12),(1.,-.60,.70),(0,0,-.45)),
 (.36,(80,-10,-12),(1.10,-.65,.70),(.15,0,-18.)),
 (.44,(78,-9,-11),(1.05,-.60,.65),(3.40,1.,-25.)),
 (.53,(78,-9,-11),(1.05,-.60,.65),(3.,1.,-25.)),
 (.60,(80,-9,-11),(1.,-.60,.65),(.10,0,-5.)),
 (.68,(82,-9,-11),(.95,-.55,.60),(0,0,0)),
 (.74,(82,-8,-10),(.95,-.50,.60),(0,0,.08)),
 (.80,(77,-7,-9),(.80,-.45,.50),(0,0,0)),
 (.90,(38,-4,-7),(.40,-.30,.25),(0,0,0)),
 (.97,(6,-1,-1),(.04,-.06,.03),(0,0,0)),
 (1,(0,0,0),(0,0,0),(0,0,0)))
# Revision2: authored framing correction after supplied native socket-offscreen defect.
# Same rotations/relative canister path, common display-space shift only.
# C1 smoothstep interpolation and zero endpoint weights preserve exact idle graph.
FRAMING_DELTA=(-2.,-3.5,-6.5)
FRAMING_WEIGHTS=(0.,.18,1.,1.,1.,1.,1.,1.,1.,1.,1.,.45,.05,0.)
KEYS=tuple((k[0],k[1],tuple(v+w*d for v,d in zip(k[2],FRAMING_DELTA)),k[3])
           for k,w in zip(ORIGINAL_KEYS,FRAMING_WEIGHTS))

PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/code_duello.json': '3976bf8a35213f5cf6978b1f325f9e2ab75b83cd9adf307d8abb00be2ce11781', 'src/main/resources/assets/destiny/items/weapon/code_duello.json': '57f2ed10aa31f67012981dee0786c71e53aadea317b198c5951ad75e76474c12', 'src/main/resources/assets/destiny/textures/item/weapon/w123/code_duello.png': '97fee43c3c6247f4b19c48e52835ef7b840bb5f26333684fafa9fd946cf5572a', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello.json': 'cb749df662d293747c44124ceb010554b4664a49d3d36bd9be9e3d16ddcae5ba', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_ads.json': '1612334d558b341fe9a49b565b9e1714e5d93232ef033039c5fcfad948ca7a02', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_ads_twohand.json': 'c28a0afe1c8108e8f465215a27bd9a4940e3e3e0b75b9efc3e1e4e41416041b7', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_inspect.json': '5dad0f5f508a938851d39fd110809b861481630bd1c48ab2dcf49eead3cffdff', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_inspect_twohand.json': '986615dd7b0605721621fc77a54a64c42b0e3fe3ed995f20f65140f541b0c641', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/code_duello_twohand.json': '28086257edd779e6a264be610e06851120f4723ba3b86bd2183fcedbecad355b', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=tXfSro7b6y0', 'title': 'How to get Code Duello Rocket Launcher and God Roll opinions | Destiny 2 Season of the Chosen', 'creator': 'Marcusbgaming', 'uploadDate': '20210218', 'fpsNumerator': 30000, 'fpsDenominator': 1001, 'sourceTimebase': '1/30000', 'actionFrameRange': [774, 858], 'actionSeconds': [25.8258, 28.6286], 'sourceVideoFile': '/private/tmp/w187-code-report/original.mp4', 'sourceMetadataFile': '/private/tmp/w187-code-report/original.info.json', 'sourceVideoSha256': '72d345e7589331fe1559e5ab009f6992ad1ca18e303f614b2c9de3b7eccbd7d9', 'sourceMetadataSha256': 'e8f688f15078fc9bd7e2744bd49fec65aa415318d339b265e9eeecd44ad9ceab', 'inspectedActualFrames': True, 'shaderPolicy': 'Source blue shader used only for mechanism; canonical teal/gold W123 paint unchanged.', 'frames': [{'path': '/private/tmp/w187-code-report/action-01.png', 'sha256': 'b8a01fac09184e3cf03b72635afb96ec29471b715bf4f794039b417fa980e9d2', 'sourceFrameIndex': 774, 'pts': 774774, 'timestampSeconds': 25.8258, 'nearestAuthoredProgress': 0, 'observation': 'Empty hip hold after shot; reload begins.'}, {'path': '/private/tmp/w187-code-report/action-02.png', 'sha256': '18710e0373c2ba8d03a4dd6b389fc38d42cb4fd5df71dd03ec7a228f2531b410', 'sourceFrameIndex': 780, 'pts': 780780, 'timestampSeconds': 26.026, 'nearestAuthoredProgress': 0.08, 'observation': 'Launcher dips before right-edge rise.'}, {'path': '/private/tmp/w187-code-report/action-03.png', 'sha256': 'd8f05d94d31b5b8444d23f0d3f25198072caab714c43f82daa5bb30221d69f2c', 'sourceFrameIndex': 786, 'pts': 786786, 'timestampSeconds': 26.2262, 'nearestAuthoredProgress': 0.16, 'observation': 'Long ribbed canister rises nearly vertical; hand encloses it.'}, {'path': '/private/tmp/w187-code-report/action-04.png', 'sha256': 'd07a9d5701bbd1040babdde3f095ac634eb133c040c4e592c0b3b41d8fc7a9ad', 'sourceFrameIndex': 792, 'pts': 792792, 'timestampSeconds': 26.4264, 'nearestAuthoredProgress': 0.24, 'observation': 'Support grip stays on complete ribbed canister.'}, {'path': '/private/tmp/w187-code-report/action-05.png', 'sha256': 'd9e87d311293fa6a579ea6e47a5397739909335152ac4ae84bf4df48ab6f1f98', 'sourceFrameIndex': 798, 'pts': 798798, 'timestampSeconds': 26.6266, 'nearestAuthoredProgress': 0.3, 'observation': 'Canister begins axial lift from rear socket.'}, {'path': '/private/tmp/w187-code-report/action-06.png', 'sha256': '8d8e64f6598305d51395f7051fed2abd7d8a2fc48758fa1e69432952968a46a2', 'sourceFrameIndex': 802, 'pts': 802802, 'timestampSeconds': 26.760066666666667, 'nearestAuthoredProgress': 0.34, 'observation': 'Brass connector exposed between canister and socket.'}, {'path': '/private/tmp/w187-code-report/action-07.png', 'sha256': '735584d0bace814e7a8e3c8e25510d4cd4d613cbd17a1ee94feee73cf5765157', 'sourceFrameIndex': 806, 'pts': 806806, 'timestampSeconds': 26.893533333333334, 'nearestAuthoredProgress': 0.4, 'observation': 'Whole canister clears socket, moving upward beyond screen.'}, {'path': '/private/tmp/w187-code-report/action-08.png', 'sha256': 'b974e72520f3b490c6aef208a8635fbaf05827859b7b6f4d247487cb2c03fef0', 'sourceFrameIndex': 814, 'pts': 814814, 'timestampSeconds': 27.160466666666668, 'nearestAuthoredProgress': 0.48, 'observation': 'Rear circular socket remains with long side rail fixed.'}, {'path': '/private/tmp/w187-code-report/action-09.png', 'sha256': 'ba34c307c6d80a8dba529dd8d38a7ece95d42a998bc2eec947d987409d0dd2eb', 'sourceFrameIndex': 822, 'pts': 822822, 'timestampSeconds': 27.4274, 'nearestAuthoredProgress': 0.56, 'observation': 'Empty socket at low right; incoming canister is above screen.'}, {'path': '/private/tmp/w187-code-report/action-10.png', 'sha256': '12f68dfb54f779316bf2f912d7d4732522a7c688ba33d582269eff96d0bbb2a3', 'sourceFrameIndex': 826, 'pts': 826826, 'timestampSeconds': 27.560866666666666, 'nearestAuthoredProgress': 0.6, 'observation': 'Incoming complete canister connector enters at upper right.'}, {'path': '/private/tmp/w187-code-report/action-11.png', 'sha256': 'f9f7e45cd52f2b17394ff3c3d63485b7136d3888680b572973e96d458b8435ba', 'sourceFrameIndex': 830, 'pts': 830830, 'timestampSeconds': 27.694333333333333, 'nearestAuthoredProgress': 0.66, 'observation': 'Long ribbed canister aligns with socket, hand supports its length.'}, {'path': '/private/tmp/w187-code-report/action-12.png', 'sha256': 'd4e3c56cd97e689161f86c333a04e53c87d526a9f208a63ba7ac5c97e8719bc0', 'sourceFrameIndex': 834, 'pts': 834834, 'timestampSeconds': 27.8278, 'nearestAuthoredProgress': 0.7, 'observation': 'Canister seated; source HUD updates0->1.'}, {'path': '/private/tmp/w187-code-report/action-13.png', 'sha256': '5191fcde93541b3f810aa90538df5a24a641d5ba0525916cb65816f95b7ad46c', 'sourceFrameIndex': 840, 'pts': 840840, 'timestampSeconds': 28.028, 'nearestAuthoredProgress': 0.76, 'observation': 'Support hand releases seated canister.'}, {'path': '/private/tmp/w187-code-report/action-14.png', 'sha256': '1ec6ae722c0cedeed7d460bf960ab63660ff8f70c3070e7e0d252077ded943fb', 'sourceFrameIndex': 850, 'pts': 850850, 'timestampSeconds': 28.361666666666668, 'nearestAuthoredProgress': 0.9, 'observation': 'Launcher lowering toward hip.'}, {'path': '/private/tmp/w187-code-report/action-15.png', 'sha256': '0f4c76a5f2dc250956ec37b5d2a73d615d5770a145cf10ca0e2e06e2c4d4af0b', 'sourceFrameIndex': 858, 'pts': 858858, 'timestampSeconds': 28.6286, 'nearestAuthoredProgress': 1, 'observation': 'Return near hip orientation.'}, {'path': '/private/tmp/w187-code-report/action-16.png', 'sha256': '86eb5796ac788be29b636d501f4e736674c50ff6ac71ccedeed03c69c22726ec', 'sourceFrameIndex': 900, 'pts': 900900, 'timestampSeconds': 30.03, 'nearestAuthoredProgress': 0, 'observation': 'Inventory overlay explicitly identifies CODE DUELLO.'}]}

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
def interpolate(keys,p):
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError(p)
    for a,b in zip(keys,keys[1:]):
        if p <= b[0]:
            t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3))
    raise ValueError(p)

def sample(p):return interpolate(KEYS,p)
def framing_delta(p):return sub(sample(p)[1],interpolate(ORIGINAL_KEYS,p)[1])

def is_payload(e):
    return e['name'] in PAYLOAD_NAMES

PAYLOAD_NAMES=tuple(json.loads((ROOT/SOURCE).read_bytes())['elements'][i]['name'] for i in CANISTER_INDICES)

def reload_shaft(source):
    # n802/826 show the brass connector at the detached long canister's rear.
    # Two intersecting prisms form one connected short octagonal connector.
    # Dimensions are authored; seated connector lies inside Rear_solid_heart.
    core=copy.deepcopy(source['elements'][71]);core.pop('rotation',None)
    core.update(name='reload_connector_core',**{'from':[7.68,11.68,11.10],'to':[8.32,12.32,12.40]})
    diagonal=copy.deepcopy(core);diagonal['name']='reload_connector_diagonal'
    diagonal['rotation']={'origin':[8.,12.,11.75],'axis':'z','angle':45}
    return [core,diagonal]

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
    # All56 canister solids and2 connector prisms move as one rigid payload.
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
    def posed(i,grip='native',hand=FP[0],detail=False,canonical=False,before=False):
        ts=[]
        for part in PARTS:
            model=json.loads(output[A/f'models/{KEY}_{part}.json'])
            if canonical or i in (0,20):
                model['elements']=[e for e in model['elements'] if not e['name'].startswith('reload_connector_')]
            if detail:
                model['elements']=[e for e in model['elements'] if e['name'].startswith(('Tube_','Breech_','Rear_tube_','Rear_solid_heart','reload_connector_'))]
            child=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])
            d=copy.deepcopy(child['display'][hand])
            if before and i not in (0,20):
                delta=framing_delta(i/20)
                if grip=='twohand':
                    original=json.loads((ROOT/SOURCE).read_bytes())['display'][hand]
                    accepted=json.loads((ROOT/TWOHAND).read_bytes())['display'][hand]
                    delta=vec(mul(xyz(accepted['rotation']),transpose(xyz(original['rotation']))),delta)
                d['translation']=sub(d['translation'],delta)
            rr=np.asarray(xyz(d['rotation']));ss=np.array(d['scale']);tt=np.array(d['translation'])
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
    sheet=Image.new('RGB',(1600,2220),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((14,12),'W187 CODE DUELLO r2 | authored lower/farther framing correction | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.55,-.7],[-1,.45,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,310),(col*400,70))
        draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.35,.55];groups=[posed(i) for i in (0,7,13,20)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,350)
    for col,(i,g) in enumerate(zip((0,7,13,20),groups)):
        sheet.paste(raster(g,cam,400,350,extent),(col*400,420))
        draw.text((col*400+10,396),f'p={i/20:.2f} / fixed camera + common scale',fill='white')
    draw.text((14,794),'219 active elements = 161 fixed body + 56 whole ribbed canister + 2 seated connector prisms. Canonical endpoints =217.',fill='white')
    details=[posed(i,detail=True) for i in (0,7,10,13)]
    detail_cam=[1,.25,.25]
    detail_extent=helper['frame'](np.concatenate([t[0] for group in details for t in group]),detail_cam,400,350)
    for col,(i,group) in enumerate(zip((0,7,10,13),details)):
        sheet.paste(raster(group,detail_cam,400,350,detail_extent),(col*400,855))
        draw.text((col*400+10,828),f'RIGID MAGAZINE DETAIL p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(7,grip=grip,hand=hand),[1,.35,-.5],400,410),(col*400,1270))
        draw.text((col*400+10,1244),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((14,1710),'Observed: right-edge rise -> axial whole-canister removal -> offscreen exchange -> connector-first insertion -> release and lower.',fill='white')
    draw.text((14,1740),'Short connector uses existing gold UV; rear socket, side rails, fins, grip and optic fixed. Exact0/1 dispatch original full canonical graph.',fill='white')
    draw.text((14,1770),'Actual footage and hashes: SOURCE.md + manifest. Native screen, hand contact, audio and performance remain pending.',fill='white')
    # Representative fixed-camera study, shared extent for every before/after
    # panel. No per-pose auto framing, no native camera/hand calibration claim.
    correction_groups=[posed(9,grip=g,before=b) for g in GRIPS for b in (True,False)]
    camera=[0,0,1]
    extent=helper['frame'](np.concatenate([t[0] for group in correction_groups for t in group]),camera,400,350)
    draw.text((14,1810),'r2 p=.45 | fixed orthographic camera + shared extent | authored shift (-2,-3.5,-6.5); NOT native calibration',fill='white')
    for col,(group,label) in enumerate(zip(correction_groups,('native BEFORE','native CORRECTED','twohand BEFORE','twohand CORRECTED'))):
        sheet.paste(raster(group,camera,400,350,extent),(col*400,1870))
        draw.text((col*400+10,1842),label,fill='white')
    story=Image.new('RGB',(1600,2520),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL CODE DUELLO: Marcusbgaming / tXfSro7b6y0 / 2021-02-18 | independent authored normalized reload below',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225))
        x=j%4*400;y=55+j//4*605;story.paste(im,(x,y))
        draw.text((x+8,y+232),f"ACTUAL n={f['sourceFrameIndex']} / {f['timestampSeconds']:.5f}s",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.35,.55],400,295),(x,y+263))
        draw.text((x+8,y+567),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((14,2490),'r2 authored lower/farther raised-body framing. OFFLINE / NO HANDS / NOT NATIVE. 30000/1001fps; exact retained source PNGs. Blue source shader only for mechanism; canonical teal/gold paint unchanged.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w187-code_duello-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=217:raise ValueError('Canonical element drift')
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
    authored={Path('scripts/generate_reload_w187_code_duello.py'),Path('scripts/qa/test_reload_w187_code_duello.py'),Path('src/test/java/kim/biryeong/destiny/weapon/ReloadW187CodeTest.java'),ART/'SOURCE.md'}
    owned=expected_output_paths()|authored
    if len(owned)!=94:raise ValueError('Owned set must be exact94')
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_surface_w123_hammerhead.py'),*sorted(authored)]
    emit(ART/'manifest.json',dict(stage='W187',weapon='code_duello',revision=2,itemModel='destiny:'+KEY,
        ownedPaths=sorted(map(str,owned)),ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=217,bodyElements=161,movingElements=58,maxAssembledElements=219,endpointAssembledElements=217,elementLimit=1000,addedElements=2,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,
        geometryPolicy='All217 W123 canonical solids, faces, rotations, UV and teal/gold default paint retained verbatim. Complete56-solid forward ribbed canister moves; rear tube/socket, rails/fins, grip, trigger and optic remain fixed in body. Canonical files untouched.',
        payloadPolicy='Complete long ribbed forward canister including Tube0..25, both main-ridge rows35..45/53..63, gold connector band71..78 and two small hidden connector prisms. One rigid assembly proxies outgoing/incoming; no baseplate-only or random-band ammunition, scale hiding, invented hand IK or bone extraction.',
        sourceLimitation=dict(canonicalHiddenNeckAbsent=True,fullMagazineFidelityBlocked=False,exactOriginalShaftFidelityVerified=False,resolution='n802 shows detached brass connector; n826 incoming full canister. Authored short hidden connector preserves canonical exterior. Canonical Rear_solid_heart remains filled, so exact open-socket interior and hand clearance are not reproduced or verified.',canonicalMovingNames=list(PAYLOAD_NAMES),canonicalMovingIndices=list(CANISTER_INDICES)),
        reloadOnlyGeometry=dict(elements=reload_shaft(source),count=2,sourceFrameIndices=[802,826],sourceTimestampSeconds=[802*1001/30000,826*1001/30000],coreDimensions=[.64,.64,1.30],uvPolicy='Existing Breech_gold_band0 faces copied unchanged; original atlas only.',rigidAnchor=list(MAGAZINE_ANCHOR)),
        semanticGroups={'body':161,'originalWholeCanister':56,'reloadOnlyHiddenConnector':2,'fixed':['Rear_tube','Rear_solid_heart','Breech_teal_collar','rails','fins','grip','trigger','optic']},
        framingCorrection=dict(revision=2,reason='Supplied initial native frames show high-pitch body/socket offscreen; source n806/814 keeps socket lower-right.',
            commonDisplayDelta=list(FRAMING_DELTA),weights=list(FRAMING_WEIGHTS),originalKeys=ORIGINAL_KEYS,
            policy='Only common display-space shift changed; same rotations, pivot, axis, relative canister path, geometry/scales and exact0/1 guards. Smoothstep weights ramp at entry/exit.',
            originalRepresentativeBodyDisplay=[3.63,5.51,4.44],expectedRepresentativeDisplayDelta=list(FRAMING_DELTA),
            correctionNativeVerified=False,masterOwnsCalibrationRetest=True),
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineExtractionAxis=[0,0,-1],hipEndpoints=[0,20],
        endpointPolicy='Exact0/1 and overshoot select complete original canonical graph. Children0/20 exact accepted displays. Negative/nonFP/ADS/inspect canonical guards. Added connector seated entirely inside Rear_solid_heart.',
        normalizedPhases={'rise':[0,.18],'withdraw':[.18,.36],'offscreenExchange':[.36,.53],'incoming':[.53,.60],'seat':[.60,.68],'release':[.68,.80],'recover':[.80,1]},
        reference=REFERENCE,
        referencePolicy='Actual same-weapon Marcusbgaming review. Inventory n900 identifies CODE DUELLO; continuous reload n774..858 shows near-vertical complete ribbed canister removal/replacement and HUD0->1.16 exact unscaled frames with PTS/timebase/SHA256 retained outside repo.',
        authoredPolicy='Individually authored Code Duello right-edge steep rise, long-canister forward axial removal, offscreen exchange, aligned brass-connector insertion, small seating overtravel, support release and lowering. W185 generator/matrix/renderer/test infrastructure reused only; trajectory, pivot, axis and phases authored independently.',
        authoredHiddenDetails='Occluded exchange, exact angles/offsets, short connector dimensions and normalized timing are authored. Footage shows one long ribbed canister entering same socket; no extracted bones, numeric poses or exact measured animation fidelity claim.',
        timingPolicy='Preserve local1 rocket,15RPM,cadence80ticks,burst1,reload67ticks,shellReloadfalse, ammo and audio unchanged.21 samples every3.35ticks; source perks do not set product timing.',
        rotationConvention='JOML Rx Ry Rz; unchanged uniform canonical scale; rigid motion carried to twohand; left apply F*T*F. Original element rotations retained.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration=dict(workerRuntimeEdited=False,masterOwnsRegistryRuntime=True,requiredMasterModel='destiny:'+KEY,catalogId='code_duello',assetInputs='float[1] progress0..1; boolean[0] grip; string[0] ads/inspect guard. Master owns route/admission/lifecycle.'),
        nativeQueue=['Master route/admit code_duello with67ticks/1rocket/15RPM unchanged timing, ammo and sound.',
        'Both FP hands/grips: whole56-solid ribbed canister/connector extraction and seat; rear socket/rails fixed; hand fit and recovery.',
        'ADS/inspect/negative/nonFP/endpoints; cancellation/equip/switch/death/disconnect and partial/empty/no-reserve lifecycle.',
        'Actual pack/framebuffer, audio listening and10-20weapon stability pending master. Offline images are not native proof.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w187-code_duello-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs/media hashes;87 pack assets;161+58=219 active elements,217 canonical endpoints;native pending')
if __name__=='__main__':main()
