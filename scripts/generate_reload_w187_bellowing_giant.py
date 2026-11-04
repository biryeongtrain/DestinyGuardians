#!/usr/bin/env python3
"""Bellowing Giant W187 front-loaded whole-rocket reload.
W185 graph/matrix infrastructure only; source-inspected independently authored motion.
--verify is stdlib/media-free: no source MP4/frames or /tmp ownership manifest required.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w187/bellowing_giant')
KEY='weapon_reload_w187_bellowing_giant/bellowing_giant'
SOURCE=A/'models/weapon_surface_w123/bellowing_giant.json'
TWOHAND=A/'models/weapon/rocket_launcher/bellowing_giant_twohand.json'
ITEM=A/'items/weapon/bellowing_giant.json'
TEXTURE=A/'textures/item/weapon/w123/bellowing_giant.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.65,7.8)  # fixed pistol grip, not a breech or loose band
MAGAZINE_ANCHOR=(8.,12.05,.4)
KEYS=((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.1, (14, 2, -6), (0.1, -0.12, 0.06), (0, 0, 0)), (0.2, (64, -6, -16), (0.32, -0.45, 0.22), (0, 0, 0)), (0.3, (104, -12, -22), (0.55, -0.68, 0.4), (4, -1.5, -10.5)), (0.35, (108, -12, -22), (0.57, -0.7, 0.42), (3, -0.8, -10.3)), (0.43, (110, -10, -20), (0.55, -0.65, 0.4), (1.4, -0.2, -9.4)), (0.5, (109, -9, -19), (0.54, -0.6, 0.4), (0, 0, -8.9)), (0.55, (107, -8, -18), (0.52, -0.57, 0.38), (0, 0, -5.7)), (0.6, (104, -7, -16), (0.48, -0.51, 0.35), (0, 0, -2.8)), (0.65, (100, -6, -15), (0.43, -0.44, 0.3), (0, 0, 0)), (0.72, (90, -3, -13), (0.36, -0.35, 0.23), (0, 0, 0)), (0.82, (42, 4, -6), (0.16, -0.2, 0.1), (0, 0, 0)), (0.9, (-3, 2, 2), (0.03, -0.06, 0.02), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/bellowing_giant.json': 'c5bc85213c3daec0d188f396429a2f4c314888fb5d28d63e24233ac358de4e13', 'src/main/resources/assets/destiny/textures/item/weapon/w123/bellowing_giant.png': 'dba7cd9234e29158b6d7ce6d68dad6950b7802ee9f1aa94a9944083114d6e457', 'src/main/resources/assets/destiny/items/weapon/bellowing_giant.json': '6549576c026f913148d0e2bd6753d91f931fc4632597e08916d1be8c604b5eb5', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_twohand.json': '1c4a1cc6ffc83ed87698d5dc5a87c75a9c2852e4e7384451fdf78d14a7944fa3', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_ads_twohand.json': '86852d66c497dc5b8364f8b1c28fbcb2b87a4fe1f24f0c33eab05f9bd549222f', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant.json': 'e7a12634a512901893865bc41d5e23218741d03c2b0e3b8455a567358fb37a8b', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_ads.json': 'd00d5396cde90b8dab6d56e072af30a33c1cfc6cc539d2ff9e8f6b569052a43e', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_inspect.json': '8abbd6154b4486ac191ba8388910b37a7fd3ddf5ae9b71959c0125cddcebb99c', 'src/main/resources/assets/destiny/models/weapon/rocket_launcher/bellowing_giant_inspect_twohand.json': '0e6575324c7483f1c139f9288284a8abfb111816a29cd8d12904d777300b9236'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=DemrVvcFFjI', 'title': 'Destiny 2 Forsaken : Black Armory Rocket Launcher Bellowing Giant curated roll', 'creator': 'The Silent Noob', 'uploadDate': '20181223', 'fpsNumerator': 60000, 'fpsDenominator': 1001, 'sourceTimebase': '1/60000', 'actionFrameRange': [2940, 3130], 'actionSeconds': [49.049, 52.218833333333336], 'sourceVideoFile': '/private/tmp/w187-bellowing-report/original.mp4', 'sourceMetadataFile': '/private/tmp/w187-bellowing-report/original.info.json', 'sourceVideoSha256': '11f99557b571d1d98435142d86d64eb8d3dfba1316c6c0e3aaa6f4bb7428d728', 'sourceMetadataSha256': '593eddece0e2ec0598944ddd66d7d32996a46af9f44a1aec4b2aa5d604527490', 'inspectedActualFrames': True, 'shaderPolicy': '2018 matching red/graphite basic identity; unchanged W123 atlas. Combat light obscures payload detail, authored hidden dimensions.', 'frames': [{'path': '/private/tmp/w187-bellowing-report/reference-01.png', 'sha256': 'd1bc9c3bf545f717d19e867c7a39b694535b08e73b4ae1a3ba0d98b3566cc20e', 'sourceFrameIndex': 600, 'pts': 600600, 'timestampSeconds': 10.01, 'nearestAuthoredProgress': 0, 'observation': 'Inventory explicitly BELLOWING GIANT, matching red launch jacket, silver longitudinal stripes, graphite stock and open side ring. Magazine1.'}, {'path': '/private/tmp/w187-bellowing-report/reference-02.png', 'sha256': '072ebe39fcdef1efafd67deb110986d000ac6d86052ce40f14d5070231cad089', 'sourceFrameIndex': 2940, 'pts': 2942940, 'timestampSeconds': 49.049, 'nearestAuthoredProgress': 0, 'observation': 'Hip launcher after shot, HUD0; view movement and outgoing flash are gameplay, not reload geometry.'}, {'path': '/private/tmp/w187-bellowing-report/reference-03.png', 'sha256': 'cef7ce857494c8e3b6d622262192581a8243eab6db89001c12fe45946b37b41c', 'sourceFrameIndex': 2960, 'pts': 2962960, 'timestampSeconds': 49.382666666666665, 'nearestAuthoredProgress': 0.10526, 'observation': 'Support hand sweeps across foreground as launcher begins inward/upward presentation.'}, {'path': '/private/tmp/w187-bellowing-report/reference-04.png', 'sha256': '30616c8488fa19eaacbd2e4f0dde66fdab7812e919a9eb26aa7cc4f58b398c60', 'sourceFrameIndex': 2990, 'pts': 2992990, 'timestampSeconds': 49.88316666666667, 'nearestAuthoredProgress': 0.26316, 'observation': 'Launcher rolls; round open muzzle rises from lower right and presents toward camera.'}, {'path': '/private/tmp/w187-bellowing-report/reference-05.png', 'sha256': '29f208bbcb994eda98a4632dcda7bcc3d219eb1519fe2227ff98cb32eb68fb28', 'sourceFrameIndex': 3010, 'pts': 3013010, 'timestampSeconds': 50.216833333333334, 'nearestAuthoredProgress': 0.36842, 'observation': 'Muzzle front ring fully exposed at lower right; red jacket and fixed foregrip stay with tube.'}, {'path': '/private/tmp/w187-bellowing-report/reference-06.png', 'sha256': '67dc45b562aeaa97d6b2c9bc002f36b9719fb370e181aae8dc048abfbce1eee1', 'sourceFrameIndex': 3020, 'pts': 3023020, 'timestampSeconds': 50.38366666666667, 'nearestAuthoredProgress': 0.42105, 'observation': 'Incoming dark rocket/cartridge begins entering from screen right beside open muzzle; hand partly conceals its body.'}, {'path': '/private/tmp/w187-bellowing-report/reference-07.png', 'sha256': '8c23b18ae5d516bf5dc7b02aa818be23e939616fa22f33a842347b1e8d0ebec8', 'sourceFrameIndex': 3030, 'pts': 3033030, 'timestampSeconds': 50.5505, 'nearestAuthoredProgress': 0.47368, 'observation': 'Whole incoming payload is held above/right of tube; long axis distinct from launcher, no detachable breech band.'}, {'path': '/private/tmp/w187-bellowing-report/reference-08.png', 'sha256': 'b2e83db75c20646d1e7305f485f4c93dd6ca41c31ae187e665346d4b9aacaacc', 'sourceFrameIndex': 3040, 'pts': 3043040, 'timestampSeconds': 50.717333333333336, 'nearestAuthoredProgress': 0.52632, 'observation': 'Payload aligns over front muzzle. Tail/hand silhouette visible right; bright combat effects obscure small surfaces.'}, {'path': '/private/tmp/w187-bellowing-report/reference-09.png', 'sha256': '4af465aa46a42295ba311fe7c90f4a9cba91f159b29e50e187edc45ef2cd44fd', 'sourceFrameIndex': 3050, 'pts': 3053050, 'timestampSeconds': 50.884166666666665, 'nearestAuthoredProgress': 0.57895, 'observation': 'Hand moves payload down into open muzzle; rocket front/neck occluded by tube. HUD becomes1.'}, {'path': '/private/tmp/w187-bellowing-report/reference-10.png', 'sha256': '680cd827ca6a07f0a24f22e64cce7cfdb12133d1dfa681dd44fb6bf0fbe9d0c0', 'sourceFrameIndex': 3060, 'pts': 3063060, 'timestampSeconds': 51.051, 'nearestAuthoredProgress': 0.63158, 'observation': 'Support palm pushes down along muzzle axis; full rocket progressively disappears into tube.'}, {'path': '/private/tmp/w187-bellowing-report/reference-11.png', 'sha256': 'cf4e2c516dac271ce34e85f2c0dc635af3f3e97a6fedcdf52f7db8ee1c80b778', 'sourceFrameIndex': 3070, 'pts': 3073070, 'timestampSeconds': 51.21783333333333, 'nearestAuthoredProgress': 0.68421, 'observation': 'Palm remains above front opening; launcher held steeply, insertion completes.'}, {'path': '/private/tmp/w187-bellowing-report/reference-12.png', 'sha256': '5895e8dc481aed17a57d8981150e5e30bf999e6f644b2f860fec8cfc3afd17f7', 'sourceFrameIndex': 3080, 'pts': 3083080, 'timestampSeconds': 51.38466666666667, 'nearestAuthoredProgress': 0.73684, 'observation': 'Support hand releases; long fixed barrel remains intact. No independently observed bolt/latch stroke.'}, {'path': '/private/tmp/w187-bellowing-report/reference-13.png', 'sha256': '090b382dec34f38cb8110649f703a317d536420c6f0d6edd2f753d5cb8800fea', 'sourceFrameIndex': 3090, 'pts': 3093090, 'timestampSeconds': 51.5515, 'nearestAuthoredProgress': 0.78947, 'observation': 'Launcher begins rapid forward/down roll; hand moves away from muzzle.'}, {'path': '/private/tmp/w187-bellowing-report/reference-14.png', 'sha256': '0c9800ff6a7974bf1e5cc7396a79b3a6135c27e857b47a8200a15b12e14f273e', 'sourceFrameIndex': 3100, 'pts': 3103100, 'timestampSeconds': 51.718333333333334, 'nearestAuthoredProgress': 0.84211, 'observation': 'Muzzle points forward again, stock returns to shoulder line.'}, {'path': '/private/tmp/w187-bellowing-report/reference-15.png', 'sha256': '52cb2a333db96e2b1bcb7169035702e9d4e9988d8f6111e94b6fc3216f5455b6', 'sourceFrameIndex': 3110, 'pts': 3113110, 'timestampSeconds': 51.88516666666667, 'nearestAuthoredProgress': 0.89474, 'observation': 'Hip pose nearly recovered while camera pans right.'}, {'path': '/private/tmp/w187-bellowing-report/reference-16.png', 'sha256': '402044f2e594c6912ade634f6a3b0c662d390150ba2a6cc3da317db600307a70', 'sourceFrameIndex': 3130, 'pts': 3133130, 'timestampSeconds': 52.218833333333336, 'nearestAuthoredProgress': 1, 'observation': 'Recovered hip presentation; HUD1, canonical authored endpoint.'}]}

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

def payload_visible(i):return 7 <= i <= 13

def reload_rocket(source):
    # Observed front-loaded incoming dark cylinder and tail silhouette n3020..3060.
    # Exact hidden dimensions/UV are authored; no extracted animation/bones.
    # One connected solid assembly fits entirely within original chamber when seated.
    template=source['elements'][64]  # graphite material; NOT movable stock geometry
    elements=[]
    def cube(name,lo,hi,rotation=None):
        el=copy.deepcopy(template);el.update(name=name,**{'from':lo,'to':hi});el.pop('rotation',None)
        if rotation:el['rotation']=rotation
        elements.append(el)
    cube('Reload_rocket_core',[7.65,11.70,-1.8],[8.35,12.40,2.25])
    for i in range(8):
        angle=i*45
        # Eight continuous jacket faces overlap the core, producing one long octagonal payload.
        cube(f'Reload_rocket_jacket_{i}',[7.80,12.35,-1.8],[8.20,12.51,2.25],
             {'origin':[8,12.05,.4],'z':angle})
    cube('Reload_rocket_nose',[7.72,11.77,2.15],[8.28,12.33,2.85])
    cube('Reload_rocket_nose_tip',[7.84,11.89,2.8],[8.16,12.21,3.2])
    cube('Reload_rocket_tail_neck',[7.73,11.78,-2.4],[8.27,12.32,-1.65])
    # Four shallow connected stabilizers; silhouettes source-backed, occluded profile authored.
    cube('Reload_rocket_fin_left',[7.46,11.99,-2.3],[7.8,12.11,-1.6])
    cube('Reload_rocket_fin_right',[8.2,11.99,-2.3],[8.54,12.11,-1.6])
    cube('Reload_rocket_fin_top',[7.94,12.25,-2.3],[8.06,12.59,-1.6])
    cube('Reload_rocket_fin_bottom',[7.94,11.51,-2.3],[8.06,11.85,-1.6])
    return elements

def partition(source):
    models={part:copy.deepcopy(source) for part in PARTS}
    models['magazine']['elements']=reload_rocket(source)
    return models

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
    import numpy as np
    from PIL import Image,ImageDraw
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    def triangles(model):
        model=copy.deepcopy(model)
        for e in model['elements']:
            rr=e.get('rotation',{})
            if 'axis' in rr:e['rotation']={'origin':rr['origin'],rr['axis']:rr['angle']}
        return helper['model_triangles']({'part':model},texture)
    def posed(i,grip='native',hand=FP[0],canonical=False,payload_only=False):
        ts=[]
        for part in PARTS:
            if part=='magazine' and (canonical or not payload_visible(i)):continue
            if payload_only and part!='magazine':continue
            model=json.loads(output[A/f'models/{KEY}_{part}.json'])
            child=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])
            d=child['display'][hand];rr=np.array(xyz(d['rotation']));ss=np.array(d['scale']);tt=np.array(d['translation'])
            for pts,uv,tex,n in triangles(model):
                points=np.array(pts).copy();n=np.array(n).copy()
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
    draw.text((14,12),'W187 BELLOWING GIANT | OFFLINE / NO HANDS / NOT NATIVE | source-led front-loaded whole rocket',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.55,-.7],[-1,.45,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,310),(col*400,70))
        draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.35,.55];indices=(0,7,10,17);groups=[posed(i) for i in indices]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,350)
    for col,(i,g) in enumerate(zip(indices,groups)):
        sheet.paste(raster(g,cam,400,350,extent),(col*400,420));draw.text((col*400+10,396),f'p={i/20:.2f} / common camera + scale',fill='white')
    draw.text((14,794),'114 canonical fixed elements +16 connected rocket elements =130 active max. No breech/stock band used as ammunition.',fill='white')
    cam=[1,.2,-.4];indices=(7,9,11,13);groups=[posed(i) for i in indices]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,350)
    for col,(i,g) in enumerate(zip(indices,groups)):
        sheet.paste(raster(g,cam,400,350,extent),(col*400,855));draw.text((col*400+10,828),f'FRONT INSERTION p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(9,grip,hand),[1,.35,-.5],400,410),(col*400,1270));draw.text((col*400+10,1244),grip+' / '+hand.replace('firstperson_',''),fill='white')
    for y,line in zip((1710,1740,1770),('Observed: inward lift -> exposed front muzzle -> incoming rocket -> axial palm seat -> release -> rapid forward roll.', 'One rigid rocket appears only p=.35..65; hidden seated inside unchanged launch chamber; exact0/1 use full original graph.', 'Authored numeric poses and hidden payload profile. Native hand contact, screen framing, audio and performance remain pending.')):draw.text((14,y),line,fill='white')
    story=Image.new('RGB',(1600,2520),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL BELLOWING GIANT / The Silent Noob / DemrVvcFFjI /2018-12-23 | OFFLINE / NO HANDS authored panels',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225));x=j%4*400;y=55+j//4*605;story.paste(im,(x,y))
        draw.text((x+8,y+232),f"ACTUAL n={f['sourceFrameIndex']} / PTS={f['pts']}",fill='white')
        index=round(f['nearestAuthoredProgress']*20);story.paste(raster(posed(index),[1,.35,.55],400,295),(x,y+263))
        draw.text((x+8,y+567),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((14,2490),'OFFLINE / NO HANDS / NOT NATIVE. Exact unaltered source frames:60000/1001fps,1/60000 timebase. Local64ticks/capacity1 unchanged.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w187-bellowing-report')):
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
            for grip in GRIPS:emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],two,p,part,grip)))
        def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in PARTS if part=='body' or payload_visible(i)])
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w187_bellowing_giant.py'),Path('scripts/qa/test_reload_w187_bellowing_giant.py'),Path('src/test/java/kim/biryeong/destiny/weapon/ReloadW187BellowingTest.java'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W187',weapon='bellowing_giant',revision=1,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=114,bodyElements=114,movingElements=16,maxAssembledElements=130,endpointAssembledElements=114,elementLimit=1000,addedElements=16,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=dict(body=list(range(114)),magazine=[]),
        geometryPolicy='All114 canonical elements/684faces/rotations/UV/default paint/display preserved exactly on fixed carrier. No canonical breech band, stock, heel or baseplate impersonates ammunition.',
        payloadPolicy='One connected reload-only dark rocket: long octagonal jacket+core, stepped nose, tail neck and4 stabilizers. One rigid insertion, constant scale. Appears only samples7..13; no extraction of a spent/live rocket.',
        sourceLimitation=dict(canonicalPayloadAbsent=True,fullPayloadSourceFidelityVerified=False,resolution='Actual same-weapon front-muzzle reload inspected. Incoming body/tail silhouette resolves but hand/bright effects conceal nose, exact profile and seating. Small16-element whole rocket authored; hidden dimensions and native fit unverified.'),
        reloadOnlyGeometry=dict(elements=reload_rocket(source),count=16,sourceFrameIndices=[3020,3030,3040,3050,3060],uvPolicy='Reuse graphite Stock_filled_heart64 face UV for dark reload-only material; canonical atlas unchanged.',rigidAnchor=list(MAGAZINE_ANCHOR),seatedEnvelope=[7.46,11.51,-2.4,8.54,12.59,3.2],seatInsideCanonicalElement=8,visibleSampleIndices=list(range(7,14))),
        semanticGroups=dict(body=114,reloadOnlyWholeRocket=16,fixed=['Red_breech','Steel_lock_band','Rear_sleeve','Stock_filled_heart','Foregrip','Pistol','Action_closed_housing','Open_ring_sight']),
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineInsertionAxis=[0,0,1],hipEndpoints=[0,20],
        endpointPolicy='Exact0/1 and overshoot use full original item graph. Negative/nonFP/ADS/inspect preserve canonical. Children0/20 retain exact accepted displays. Payload absent before incoming and after seating.',
        normalizedPhases=dict(inwardLift=[0,.3],incoming=[.35,.5],axialSeat=[.5,.65],release=[.65,.72],forwardRoll=[.72,.9],settle=[.9,1]),
        reference=REFERENCE,referencePolicy='Same Bellowing Giant inventory and continuous2018 The Silent Noob n2940..3130.16 exact unaltered source PNGs, MP4/metadata hashes and PTS retained outside repo; inspected before authoring.',
        authoredPolicy='Individually authored front-opening camera presentation, right-side incoming rocket, aligned axial push, palm-release dwell, rapid forward/down roll and short settle. W185 graph/matrices/renderer only, no reused trajectory.',
        authoredHiddenDetails='Dark rocket body/tail inferred from visible silhouette; nose/profile/UV/absolute displacement/pivot and hand clearance authored. No bone extraction, imported animation, separate bolt or moving breech invented.',
        timingPolicy='Unchanged capacity1, reload64ticks, cadence60ticks, burst1/sharedBurstAmmo=false, no shell reload, existing audio/ammo transfer.21 normalized samples every3.2ticks; footage clock does not set gameplay.',
        rotationConvention='JOML Rx Ry Rz; constant accepted uniform scale; native carrier transported into twohand; left ItemTransform applies F*T*F. Canonical element rotations unchanged.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration=dict(workerRuntimeEdited=False,masterOwnsRegistryRuntime=True,requiredMasterModel='destiny:'+KEY,catalogId='bellowing_giant',assetInputs='float[1] progress; boolean[0] grip; string[0] ads/inspect; master route/admission/lifecycle.',capacity=1,reloadTicks=64),
        nativeQueue=['Master route/admit bellowing_giant; preserve64ticks/capacity1/audio/ammo.', 'Both FP hands/grips whole-rocket front insertion, support-hand contact, screen clearance and endpoint recovery.', 'ADS/inspect/negative/nonFP guards; cancellation/equip/switch/death/disconnect; partial/empty/no reserve.', 'Native pack load/audio listening/10-20 simultaneous display observation remain master-owned pending.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w187-bellowing-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs;87 pack assets;114+16=130 active max,114 canonical endpoints;native pending')
if __name__=='__main__':main()
