#!/usr/bin/env python3
"""Stormchaser W188: actual same-weapon video-led complete grip battery reload.
W185 matrices/graph and W123 rasterizer are infrastructure only; new Stormchaser poses.
--verify uses retained preview hashes and requires no external media.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w188/stormchaser')
KEY='weapon_reload_w188_stormchaser/stormchaser'
SOURCE=A/'models/weapon_surface_w123/stormchaser.json'
TWOHAND=A/'models/weapon/linear_fusion_rifle/stormchaser_twohand.json'
ITEM=A/'items/weapon/stormchaser.json'
TEXTURE=A/'textures/item/weapon/w123/stormchaser.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.26,8.015)
MAGAZINE_ANCHOR=(8.,6.78,7.61)
MAGAZINE_NAMES=('grip_floor','power_shoe','power_shoe_toe','power_shoe_rear_lip','power_green_inset_-1','power_green_inset_1')
# n26872..27000: dip -> steep lift -> grip-axis withdraw -> low exchange -> stem-first seat -> fast lower.
# Source camera/player movement is not copied; numeric poses are independently authored.
# The common FP translation brings both the heel socket and exchange inward/farther
# during the steep phase; no random receiver plate, shrinking, or endpoint drift.
KEYS=(
 (0,(0,0,0),(0,0,0),(0,0,0)),
 (.06,(-5,-1,-2),(-.15,-.18,-.15),(0,0,0)),
 (.13,(42,-5,-11),(-.65,-.55,-1.35),(0,0,0)),
 (.22,(73,-10,-15),(-1.4,-1.2,-2.8),(0,0,0)),
 (.29,(76,-11,-14),(-1.4,-1.2,-2.8),(0,-1.,.439)),
 (.39,(75,-11,-14),(-1.4,-1.2,-2.8),(-.6,-4.8,2.106)),
 (.49,(73,-10,-13),(-1.4,-1.2,-2.8),(-.9,-5.2,2.282)),
 (.58,(72,-9,-12),(-1.4,-1.2,-2.8),(-.25,-3.1,1.36)),
 (.68,(70,-8,-12),(-1.4,-1.2,-2.8),(0,-1.4,.614)),
 (.75,(68,-7,-11),(-1.4,-1.2,-2.8),(0,0,0)),
 (.79,(59,-5,-13),(-1.3,-1.1,-2.6),(0,0,0)),
 (.88,(25,-1,-8),(-.6,-.5,-1.25),(0,0,0)),
 (.95,(3,0,-1),(-.08,-.08,-.17),(0,0,0)),
 (1,(0,0,0),(0,0,0),(0,0,0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/stormchaser.json': '20d84ccbf4ceb5916023928f4c0f38ece8c97a2ae54f027cd4aed27005ac67ff', 'src/main/resources/assets/destiny/items/weapon/stormchaser.json': 'f2e90ea1eb2a05165057ab1d55bdbc31556ad4d88bbc07048cf363278a504fa4', 'src/main/resources/assets/destiny/textures/item/weapon/w123/stormchaser.png': '9df012783bc20706ac5659d5596d9bfa692417b79cd18f790cdfb13c80c13c0d', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_ads_twohand.json': 'a1e35e293fa9f54dfc66467cd67c666ec6da52e74cac1bf3213904eb99f1b97b', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_ads.json': '15d97d6e712a891966a6fe6042d454cea12bb41b9473d917dc6e46ce29d9f269', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_twohand.json': '7d67e07e5565cebc402090735fe77fa2e110ffc0f26d3f8aade0528803a92fdb', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_inspect.json': '48cff067c4d7905b27aef02348cf00eb071d4a6be32ac0d20995390ec135689d', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser.json': 'dae7be8060d539e03da89a2008862b2e5bd1a68bd7a4441bca1c57f4fb4bba25', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/stormchaser_inspect_twohand.json': 'bd07fb49b65a955cdeb729fea62a06bfbd9503a016a5d8eaf6dacaa0e926426b', 'src/main/resources/assets/destiny/sounds/w63/reload/weapon_stormchaser_reload_49.ogg': 'a40924cac0896dd8930677618c9fa42d2c446c01b7d2d2a48718b7dacec9a62d'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=Ev71jjG4JbQ', 'title': 'The New Burst Linear Fusion Is Insane! (Stormchaser)', 'creator': 'Ehroar', 'uploadDate': '20220529', 'fpsNumerator': 60000, 'fpsDenominator': 1001, 'sourceTimebase': '1/60000', 'actionFrameRange': [26872, 27000], 'actionSeconds': [448.3145333333333, 450.45], 'sourceVideoFile': '/private/tmp/w188-storm-report/original.mp4', 'sourceMetadataFile': '/private/tmp/w188-storm-report/original.info.json', 'sourceVideoSha256': '357954642f7931469b4ef0e7a9d5e44b4735111ef43c4b26272cb2f3e3fb3c9d', 'sourceMetadataSha256': 'db84af0fc9c5b578c1529882df09ee05520f6d783f7b4e1c95307adc0370c819', 'inspectedActualFrames': True, 'shaderPolicy': 'Inventory establishes basic silver/red-black Stormchaser. Continuous gameplay cycle uses a silver/white shader solely for mechanism; canonical basic-dye atlas stays unchanged.', 'frames': [{'path': '/private/tmp/w188-storm-report/reference-01.png', 'sha256': 'fb37a10be8c66041e3b2bb2517125d9d8462230005b3c3b6efc4b6c7f773e61e', 'sourceFrameIndex': 900, 'pts': 900900, 'timestampSeconds': 15.015, 'nearestAuthoredProgress': 0, 'observation': 'Inventory explicitly STORMCHASER: silver crest, red-black body, swept loop, hooked stock and green grip heel identify the weapon.'}, {'path': '/private/tmp/w188-storm-report/reference-02.png', 'sha256': '0533cd5c4bd9058298bd4e70f1527123893acabb4febd9ffea04ee2e0abe52d4', 'sourceFrameIndex': 26872, 'pts': 26898872, 'timestampSeconds': 448.3145333333333, 'nearestAuthoredProgress': 0.0, 'observation': 'Final ADS burst with HUD1; start of continuous reload window.'}, {'path': '/private/tmp/w188-storm-report/reference-03.png', 'sha256': 'c4e568f9f6ffa23637aae0c7ea89be00deaf93d760ba9a370f809256b610bd9e', 'sourceFrameIndex': 26880, 'pts': 26906880, 'timestampSeconds': 448.448, 'nearestAuthoredProgress': 0.0625, 'observation': 'Drops out of ADS before muzzle-up rise; player turns to the reload presentation.'}, {'path': '/private/tmp/w188-storm-report/reference-04.png', 'sha256': '55ad462d6438123a25bdee899eecc4f0341ecb51446290aa6e0ded877f1458cb', 'sourceFrameIndex': 26888, 'pts': 26914888, 'timestampSeconds': 448.58146666666664, 'nearestAuthoredProgress': 0.125, 'observation': 'Muzzle rises at right edge, broad cage and swept loop visible.'}, {'path': '/private/tmp/w188-storm-report/reference-05.png', 'sha256': '24641ca85c52fa4375b84048bd2f1a4a480e10d38fe5f89c1f7f71856c5f1f02', 'sourceFrameIndex': 26896, 'pts': 26922896, 'timestampSeconds': 448.7149333333333, 'nearestAuthoredProgress': 0.1875, 'observation': 'Steep muzzle-up hold; support hand reaches beneath pistol grip toward heel.'}, {'path': '/private/tmp/w188-storm-report/reference-06.png', 'sha256': '4abae023050ec64b2beb3bd255d33805f822959885d30176b1956a826a29fc83', 'sourceFrameIndex': 26904, 'pts': 26930904, 'timestampSeconds': 448.8484, 'nearestAuthoredProgress': 0.25, 'observation': 'Support hand encloses the full heel assembly; receiver and open frame remain attached.'}, {'path': '/private/tmp/w188-storm-report/reference-07.png', 'sha256': '0725b171f935bcc5f0f372eabe127c880c9f7dc6406b8670f7f5973c97b87c6d', 'sourceFrameIndex': 26916, 'pts': 26942916, 'timestampSeconds': 449.0486, 'nearestAuthoredProgress': 0.34375, 'observation': 'Support hand pulls down along the pistol-grip axis; outgoing battery partly occluded.'}, {'path': '/private/tmp/w188-storm-report/reference-08.png', 'sha256': 'cd420c6d98c3a635288e3f479aaf067cc2f512d41dec8cb750bcbc300d87234f', 'sourceFrameIndex': 26928, 'pts': 26954928, 'timestampSeconds': 449.2488, 'nearestAuthoredProgress': 0.4375, 'observation': 'Right hand retains pistol grip; outgoing battery and support hand descend below the edge.'}, {'path': '/private/tmp/w188-storm-report/reference-09.png', 'sha256': 'f75c805d18286c2d75fe0c54fb96481abe2a02cd18d780f8b2f3de7806c97f16', 'sourceFrameIndex': 26940, 'pts': 26966940, 'timestampSeconds': 449.449, 'nearestAuthoredProgress': 0.53125, 'observation': 'Empty heel area remains at lower right while carrier holds steep.'}, {'path': '/private/tmp/w188-storm-report/reference-10.png', 'sha256': 'd85cc2600b049e105c78fc60150c1647a4fd88a7937de353d3a4e5a0a05e48ac', 'sourceFrameIndex': 26952, 'pts': 26978952, 'timestampSeconds': 449.6492, 'nearestAuthoredProgress': 0.625, 'observation': 'Replacement long narrow stem and substantial foot enter from below left.'}, {'path': '/private/tmp/w188-storm-report/reference-11.png', 'sha256': '3f9f176762e2014b9833cc3b1d1d8bfa86bd20ba4b0148fc2825da98ec567335', 'sourceFrameIndex': 26960, 'pts': 26986960, 'timestampSeconds': 449.78266666666667, 'nearestAuthoredProgress': 0.6875, 'observation': 'Stem aligns into pistol-grip underside; shoe remains supported by left hand.'}, {'path': '/private/tmp/w188-storm-report/reference-12.png', 'sha256': '0b8b5d34b0e04f043b8bfceda04476a6796f4a87c74ccd95c256bf685be1e2b0', 'sourceFrameIndex': 26968, 'pts': 26994968, 'timestampSeconds': 449.91613333333333, 'nearestAuthoredProgress': 0.75, 'observation': 'Palm drives complete replacement upward; shaft is almost concealed.'}, {'path': '/private/tmp/w188-storm-report/reference-13.png', 'sha256': '266536dacdaec2ebbb78faa8cc8d2d7fdde15d6cfe98d61693e5657f9bb6e558', 'sourceFrameIndex': 26976, 'pts': 27002976, 'timestampSeconds': 450.0496, 'nearestAuthoredProgress': 0.8125, 'observation': 'Seated heel, support hand releases and HUD1 becomes5.'}, {'path': '/private/tmp/w188-storm-report/reference-14.png', 'sha256': 'dde13fabfa38966d58236faf3b6455826d083557fe70e6568bbb954d191aedeb', 'sourceFrameIndex': 26984, 'pts': 27010984, 'timestampSeconds': 450.18306666666666, 'nearestAuthoredProgress': 0.875, 'observation': 'Rapid muzzle-down recovery with support-hand fore-end reach.'}, {'path': '/private/tmp/w188-storm-report/reference-15.png', 'sha256': '788afc090aae823d4b36f9d8b326bf067c3c1bbbab535df9d832f504620737b1', 'sourceFrameIndex': 26992, 'pts': 27018992, 'timestampSeconds': 450.3165333333333, 'nearestAuthoredProgress': 0.9375, 'observation': 'Weapon returns toward hip; viewpoint motion remains in source.'}, {'path': '/private/tmp/w188-storm-report/reference-16.png', 'sha256': '713aafe624f016807518701e036f8fe80d4f96e2ed720d1da7b946187752a982', 'sourceFrameIndex': 27000, 'pts': 27027000, 'timestampSeconds': 450.45, 'nearestAuthoredProgress': 1.0, 'observation': 'Recovered hip hold with5 rounds, before following melee.'}]}
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
    # n26952..26968 resolve the incoming long stem above the broad battery foot.
    # Hidden stem dimensions are authored within original pistol_grip76 bounds.
    # This preserves the complete static silhouette and six original heel solids.
    stem=copy.deepcopy(source['elements'][76])
    stem.update(name='reload_battery_stem',**{'from':[7.73,8.02,6.55],'to':[8.27,8.50,9.62]})
    return [stem]

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
    # Full heel, green insets, crown plate and concealed stem share one rigid transform.
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
    # Inert textured raster of emitted JSON; never drives Blockbench/Blender/client.
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    def triangles(model):
        model=copy.deepcopy(model)
        for e in model['elements']:
            r=e.get('rotation',{})
            if 'axis' in r:e['rotation']={'origin':r['origin'],r['axis']:r['angle']}
        return helper['model_triangles']({'part':model},texture)
    def posed(i,grip='native',hand=FP[0],detail=False,canonical=False):
        ts=[]
        for part in PARTS:
            model=json.loads(output[A/f'models/{KEY}_{part}.json'])
            if canonical or i in (0,20):model['elements']=[e for e in model['elements'] if e['name']!='reload_battery_stem']
            if detail:model['elements']=[e for e in model['elements'] if e['name'] in MAGAZINE_NAMES+('reload_battery_stem','pistol_grip','trigger_front_web','guard_rear_upright')]
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
    sheet=Image.new('RGB',(1600,2040),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((14,12),'W188 STORMCHASER | emitted textured JSON | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.55,-.7],[-1,.45,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,290),(col*400,65))
        draw.text((col*400+10,43),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.35,.55];groups=[posed(i) for i in (0,8,14,20)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,330)
    for col,(i,g) in enumerate(zip((0,8,14,20),groups)):
        sheet.paste(raster(g,cam,400,330,extent),(col*400,410))
        draw.text((col*400+10,386),f'p={i/20:.2f} / fixed camera + common extent',fill='white')
    draw.text((14,760),'96 active elements = 89 fixed body + 6 original complete heel/shoe elements + 1 concealed stem. Canonical endpoints=95.',fill='white')
    details=[posed(i,detail=True) for i in (0,8,11,15)];cam=[1,.25,.25]
    extent=helper['frame'](np.concatenate([t[0] for g in details for t in g]),cam,400,340)
    for col,(i,g) in enumerate(zip((0,8,11,15),details)):
        sheet.paste(raster(g,cam,400,340,extent),(col*400,825))
        draw.text((col*400+10,800),f'WHOLE BATTERY + FIXED GRIP p={i/20:.2f}',fill='white')
    configs=[('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1])]
    groups=[posed(10,grip=g,hand=h) for g,h in configs];cam=[0,0,1]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,420)
    for col,((grip,hand),group) in enumerate(zip(configs,groups)):
        sheet.paste(raster(group,cam,400,420,extent),(col*400,1220))
        draw.text((col*400+10,1194),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((14,1660),'Common FP shift (-1.4,-1.2,-2.8) at steep presentation; constant accepted scale. Native screen/hand fit remains pending.',fill='white')
    draw.text((14,1690),'Observed sequence: steep lift, downward grip-axis removal, low exchange, long stem first insertion, palm seat, fast lower.',fill='white')
    draw.text((14,1720),'Original receiver, grip, swept loop, cooling cage, stock and sight stay on carrier. Only heel/crown/green insets plus stem move.',fill='white')
    draw.text((14,1750),'Comparison uses shared extents for sequences and hand/grip studies; source and emitted render cameras are independent.',fill='white')
    draw.text((14,1780),'Source inventory=basic red/black paint; gameplay=silver shader for mechanism. Canonical atlas, audio,49ticks and5 rounds unchanged.',fill='white')
    draw.text((14,1810),'Stem is authored inside original pistol grip, with original grip UV; full hidden profile/hand IK not extracted.',fill='white')
    draw.text((14,1840),'Exact0/1, negative, overshoot, ADS, inspect and nonFP resolve the original item graph. No third-person reload claim.',fill='white')
    draw.text((14,1870),'Source: Ehroar / Ev71jjG4JbQ / n26872..27000 / 60000:1001fps / 448.31453..450.45000s.',fill='white')
    story=Image.new('RGB',(1600,2520),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL STORMCHASER: Ehroar / Ev71jjG4JbQ / 2022-05-29 | emitted normalized samples below',fill='white')
    # All authored panels use the same camera and extent, not per-panel auto framing.
    cam=[1,.35,.55];groups=[posed(i) for i in range(21)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,295)
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225))
        x=j%4*400;y=55+j//4*605;story.paste(im,(x,y))
        draw.text((x+8,y+232),f"ACTUAL n={f['sourceFrameIndex']} / {f['timestampSeconds']:.5f}s",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(groups[index],cam,400,295,extent),(x,y+263))
        draw.text((x+8,y+567),f'AUTHORED p={index/20:.2f} / common extent',fill='white')
    draw.text((14,2490),'OFFLINE / NO HANDS / NOT NATIVE. Source actual PTS retained; player/camera motion not extracted. Local duration49ticks unchanged.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w188-storm-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=95:raise ValueError('Canonical element drift')
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
        model=copy.deepcopy(item['model']) if i in (0,20) else dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))
        entries.append(dict(threshold=p,model=model))
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w188_stormchaser.py'),Path('scripts/qa/test_reload_w188_stormchaser.py'),Path('src/test/java/kim/biryeong/destiny/weapon/ReloadW188StormTest.java'),ART/'SOURCE.md']
    rip=json.loads((ROOT/'art/weapons/w123/stormchaser/design.json').read_bytes())
    emit(ART/'manifest.json',dict(stage='W188',weapon='stormchaser',revision=1,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=95,bodyElements=89,movingElements=7,maxAssembledElements=96,endpointAssembledElements=95,elementLimit=1000,addedElements=1,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,
        geometryPolicy='All95 original cuboids/570faces/rotations/UV/basic dye preserved. Full grip_floor80/power_shoe81/toe82/rear_lip83/green_insets84,85 form the moving heel. Receiver, pistol grip, cage and swept loop fixed.',
        payloadPolicy='Six canonical heel/crown solids plus one concealed narrow stem move as one complete battery. One assembly proxies outgoing/incoming; constant scale and no bolt/ammunition invention.',
        sourceLimitation=dict(canonicalHiddenNeckAbsent=True,fullMagazineFidelityBlocked=False,exactOriginalShaftFidelityVerified=False,canonicalMovingNames=list(MAGAZINE_NAMES),canonicalMovingIndices=list(range(80,86)),resolution='Actual Stormchaser whole heel and long stem insertion inspected n26952..26968. One reload-only stem lies inside original pistol grip; exact hidden stem profile/hand clearance authored and unverified.'),
        reloadOnlyGeometry=dict(elements=reload_shaft(source),count=1,sourceFrameIndex=26960,sourceTimestampSeconds=26960*1001/60000,uvPolicy='Original pistol_grip76 six face UVs and rotation reused, no atlas changes.',rigidAnchor=list(MAGAZINE_ANCHOR),sourceAxisDegrees=66.309311),
        semanticGroups=dict(body=89,originalHeelAndCrown=6,reloadOnlyHiddenStem=1,fixed=['receiver_crossblock','receiver_upper_fairing','receiver_back','pistol_grip','grip_front_swell','trigger_front_web','guard_rear_upright','barrel_core','optic_base']),
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineExtractionAxis=[0,-.915733,.40179],hipEndpoints=[0,20],
        endpointPolicy='Exact0/1 and overshoot use full original item graph. Negative/nonFP/ADS/inspect preserve canonical. Children0/20 retain exact accepted displays; added stem is fully contained inside original grip when seated.',
        normalizedPhases=dict(dip=[0,.06],lift=[.06,.22],withdraw=[.22,.39],lowExchange=[.39,.49],incoming=[.49,.68],seat=[.68,.75],rapidLower=[.75,.95],recover=[.95,1]),
        framingPolicy='Common native FP translation plateau (-1.4,-1.2,-2.8) at p.22..75, transported to twohand. Shared fixed camera/scale offline studies; exact native viewport and hand contact remain master-owned.',
        reference=REFERENCE,ripProvenance=dict(sourceFiles=rip['source']['source_files'],mapping=rip['source_matching']['mapping'],acceptedTriangles=29718,greenHeelObject='Stormchaser.00.002',inertFbxBlendCompared=True,animationExtracted=False),
        referencePolicy='Inventory basic-dye identity plus continuous actual same-weapon Ehroar cycle n26872..27000. Exact source frame indices/PTS/hashes retained. Silver gameplay shader solely mechanism; base atlas untouched.',
        authoredPolicy='Independent Stormchaser dip/steep right presentation, grip-axis whole heel withdrawal, replacement long stem insertion, palm seat, rapid lower. W185 matrices/guards and W123 raster only; no borrowed motion.',
        authoredHiddenDetails='Hands and bottom edge conceal outgoing battery and part of incoming stem. Exact profile/path approximated; no extracted bones, animation, thrown battery or hand IK.',
        timingPolicy='Preserve actual product5rounds/49ticks reload/533ms charge/11charge ticks/3shot burst with shared ammo and existing audio.21samples every2.45ticks; source perks/timing normalized independently.',
        rotationConvention='JOML Rx Ry Rz; constant accepted uniform scale; native carrier transported into twohand; left ItemTransform applies F*T*F. Original element rotations unchanged.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration=dict(workerRuntimeEdited=False,masterOwnsRegistryRuntime=True,requiredMasterModel='destiny:'+KEY,catalogId='stormchaser',assetInputs='float[1] progress; boolean[0] grip; string[0] ads/inspect; master admission/lifecycle.'),
        nativeQueue=['Master route/admit stormchaser; preserve49tick/5round/533ms charge clock,3shot shared ammo and audio.', 'Both FP hands/grips whole battery stays on-screen, socket/hand fit, stem proportion, endpoint recovery.', 'ADS/inspect/negative/nonFP guards; cancellation/equip/switch/death/disconnect; partial/empty/no reserve.', 'Native pack load, listening and10-20 display observation remain pending.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w188-storm-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs;87 pack assets;89+7=96 active elements,95 canonical endpoints;native pending')
if __name__=='__main__':main()
