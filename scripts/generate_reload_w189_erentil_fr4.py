#!/usr/bin/env python3
"""Erentil FR4 W189 lower-grip cell exchange. Independent same-weapon mechanism.
W188 supplies only matrix, item-graph, parser and raster scaffolding; no motion keys.
--verify is deterministic stdlib-only; --render needs Pillow/numpy and external footage.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w189/erentil_fr4')
KEY='weapon_reload_w189_erentil_fr4/erentil_fr4'
SOURCE=A/'models/weapon_surface_w123/erentil_fr4.json'
TWOHAND=A/'models/weapon/fusion_rifle/erentil_fr4_twohand.json'
ITEM=A/'items/weapon/erentil_fr4.json'
TEXTURE=A/'textures/item/weapon/w123/erentil_fr4.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.15,2.88)
MAGAZINE_ANCHOR=(8.,4.37,3.115)
BATTERY_INDICES=(16,)
KEYS=((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.12, (48, -7, -9), (-0.8, 1.7, -0.45), (0, 0, 0)), (0.2, (69, -13, -15), (-1.5, 3.0, -0.9), (0, -0.38, -0.116)), (0.28, (73, -15, -17), (-1.7, 3.4, -1.1), (0, -2.1, -0.64)), (0.36, (72, -14, -17), (-1.8, 3.6, -1.2), (-1.2, -3.9, 1.6)), (0.44, (70, -13, -16), (-1.9, 3.7, -1.2), (-2.6, -4.6, 3.5)), (0.54, (63, -11, -15), (-1.8, 3.7, -1.1), (-2.8, -4.0, 2.7)), (0.62, (65, -12, -15), (-1.65, 3.5, -1.05), (-0.65, -2.65, -0.81)), (0.69, (70, -13, -16), (-1.6, 3.3, -1.0), (0, -0.55, -0.168)), (0.74, (72, -13, -15), (-1.6, 3.2, -0.95), (0, 0.09, 0.027)), (0.8, (68, -11, -13), (-1.4, 2.9, -0.8), (0, 0, 0)), (0.88, (46, -6, -8), (-0.9, 1.9, -0.5), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/erentil_fr4.json': '13f46cf7d380bfa2d9b1e7adcd365e5a6e6dca8818f857d0148860fa7041ccfa', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_twohand.json': 'b0b7689f38f608cc51b49e60977c4bfdef7e40c9ebaabc640264babc02dade78', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4.json': '10649eb8b62d80ad7837f7bfa3595e7be1dc338db60bcd333a7c289a130642e2', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_inspect_twohand.json': '2f56ff08e92a303e681a33d038343f1cd89a5e11ed692fb8c19b03150dbbde11', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_ads.json': '5020950f7dfca5df6baa82493cb10c7cceeba017993515b1753c24764ade370a', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_ads_twohand.json': '58eed4e067722d3c3b27e320161e359601e8769b08d89d56076b621a1cbdc369', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/erentil_fr4_inspect.json': 'b2784931617bc42abf9578e291cab7dc2cbc41b3feb8c74916d62902ffca93c0', 'src/main/resources/assets/destiny/textures/item/weapon/w123/erentil_fr4.png': '03f0cc1d18ecf3eb92e83938404951ccca40a149e934b15c55d7ba6d0919536c', 'src/main/resources/assets/destiny/items/weapon/erentil_fr4.json': '106baf4e03246a040ee619b2bd053daee4008b5765b6994fb4adc72485cf1a74', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=539XTHi69Pg', 'title': 'Destiny 2: PERFECT ERENTIL!!!! | Erentil FR4 PVP Gameplay Review', 'creator': 'ThatUnknown', 'uploadDate': '20190715', 'fpsNumerator': 30000, 'fpsDenominator': 1001, 'sourceTimebase': '1/30000', 'actionFrameRange': [8088, 8166], 'actionSeconds': [269.8696, 272.4722], 'sourceVideoFile': '/private/tmp/w189-erentil-report/review.mp4', 'sourceMetadataFile': '/private/tmp/w189-erentil-report/review.info.json', 'sourceVideoSha256': 'fc99c4d06bab6e3b51c2b8fe7ecb5fc43f0d89043e79bdf3ae08422062fb50ae', 'sourceMetadataSha256': 'dc2b573ddc4db56cec70f805c9ce1a4c1e52814623ee6ac8e890b4616de4a002', 'inspectedActualFrames': True, 'frames': [{'path': '/private/tmp/w189-erentil-report/reference-600.png', 'sha256': '9582125023323cb2fac7e4ef2b51b93905959e20161a5ef408082938e554c15a', 'sourceFrameIndex': 600, 'pts': 600600, 'timestampSeconds': 20.02, 'nearestAuthoredProgress': 0, 'observation': 'Inventory explicitly ERENTIL FR4; triangular grip frame, parallel cylinders, bottom grip cell. Alternate round optic and silver shader are mechanism evidence only.'}, {'path': '/private/tmp/w189-erentil-report/reference-8088.png', 'sha256': '3c60bfa39d3356fc25dfb2bc440596908972adf124f506d8dcb180e2e30e6d66', 'sourceFrameIndex': 8088, 'pts': 8096088, 'timestampSeconds': 269.8696, 'nearestAuthoredProgress': 0, 'observation': 'Final hip shot and ability flash precede reload; authored zero returns exact canonical hip.'}, {'path': '/private/tmp/w189-erentil-report/reference-8097.png', 'sha256': '8e5abbf909d6f45778a86e0198ab897e7f1ca143927f3132234a89fd615344ad', 'sourceFrameIndex': 8097, 'pts': 8105097, 'timestampSeconds': 270.1699, 'nearestAuthoredProgress': 0.115385, 'observation': 'Weapon rises and rolls muzzle-up at screen right; support hand leaves forward hold.'}, {'path': '/private/tmp/w189-erentil-report/reference-8100.png', 'sha256': 'b39369e168f4a62e1c1a6a37600ef5e144bf7b2cd68979bd6a94c924d96c20f5', 'sourceFrameIndex': 8100, 'pts': 8108100, 'timestampSeconds': 270.27, 'nearestAuthoredProgress': 0.153846, 'observation': 'Steep rifle with triangular grip opening exposed; support hand reaches heel cell.'}, {'path': '/private/tmp/w189-erentil-report/reference-8106.png', 'sha256': 'bf4a3f632831080342faa28eb6b68f16ec35a4ccb7768e6da9d5e42cf168ce5f', 'sourceFrameIndex': 8106, 'pts': 8114106, 'timestampSeconds': 270.4702, 'nearestAuthoredProgress': 0.230769, 'observation': 'Support fingers draw cell from lower grip; receiver, cylinders, hoses and triangular brace remain together.'}, {'path': '/private/tmp/w189-erentil-report/reference-8109.png', 'sha256': '625d03fadf3abe3cdf6d63b71f27c9ed1a4f701b876efb0f53c043d75c42c7ab', 'sourceFrameIndex': 8109, 'pts': 8117109, 'timestampSeconds': 270.5703, 'nearestAuthoredProgress': 0.269231, 'observation': 'Outgoing cell withdrawal continues along lower grip direction; fixed grip remains intact.'}, {'path': '/private/tmp/w189-erentil-report/reference-8112.png', 'sha256': '624ce92612ce468374c4b3b3473b1c2bc12b71ae3f0031b0d9b8d062819d349a', 'sourceFrameIndex': 8112, 'pts': 8120112, 'timestampSeconds': 270.6704, 'nearestAuthoredProgress': 0.307692, 'observation': 'Lower cell has cleared the grip seat; support hand and payload travel below-left.'}, {'path': '/private/tmp/w189-erentil-report/reference-8118.png', 'sha256': 'fcd53ff7796a95b540b3eb52b9fac45cbe9057421b23c67c8220636f14f9dd15', 'sourceFrameIndex': 8118, 'pts': 8126118, 'timestampSeconds': 270.8706, 'nearestAuthoredProgress': 0.384615, 'observation': 'Empty-seat dwell, steep weapon; no receiver, rail or cylinder becomes ammunition.'}, {'path': '/private/tmp/w189-erentil-report/reference-8124.png', 'sha256': '3a34278d6d3af1c08ccf58d40b650bf95870d927fe3556c0e18e56d09d779ec7', 'sourceFrameIndex': 8124, 'pts': 8132124, 'timestampSeconds': 271.0708, 'nearestAuthoredProgress': 0.461538, 'observation': 'Exchange dwell; support hand begins returning from below.'}, {'path': '/private/tmp/w189-erentil-report/reference-8130.png', 'sha256': 'bf718d7f78aad60947e1971ca2939d5a3c9b0c137bcd7711ba4eccc1cd7b18c5', 'sourceFrameIndex': 8130, 'pts': 8138130, 'timestampSeconds': 271.271, 'nearestAuthoredProgress': 0.538462, 'observation': 'Incoming hand/cell below-left of heel; rifle briefly relaxes its steep pitch.'}, {'path': '/private/tmp/w189-erentil-report/reference-8136.png', 'sha256': '5278ed946438b3506127fe6f6d33d79c728a96c56b71c4abf60009b684124a03', 'sourceFrameIndex': 8136, 'pts': 8144136, 'timestampSeconds': 271.4712, 'nearestAuthoredProgress': 0.615385, 'observation': 'Support hand raises replacement into lower grip, slender cell follows grip insertion axis.'}, {'path': '/private/tmp/w189-erentil-report/reference-8142.png', 'sha256': '80d7f0ac0459c9bdfe822595c630bd0a47db45e19f841c562d78c6e89cdfdbd5', 'sourceFrameIndex': 8142, 'pts': 8150142, 'timestampSeconds': 271.6714, 'nearestAuthoredProgress': 0.692308, 'observation': 'Palm seats cell upward at heel; HUD now shows2 because reserve was2, not local capacity.'}, {'path': '/private/tmp/w189-erentil-report/reference-8148.png', 'sha256': 'cdca9999644fc28ab581f08a1e80d11b127db8b77197d16c183f52066ede1b1f', 'sourceFrameIndex': 8148, 'pts': 8156148, 'timestampSeconds': 271.8716, 'nearestAuthoredProgress': 0.769231, 'observation': 'Support fingers release the seated heel; rifle still muzzle-up.'}, {'path': '/private/tmp/w189-erentil-report/reference-8154.png', 'sha256': 'a4fb81ed247c4d1b3d22faba11a89494a6066dd9ee45e58c68ba8f938f05a2b1', 'sourceFrameIndex': 8154, 'pts': 8162154, 'timestampSeconds': 272.0718, 'nearestAuthoredProgress': 0.846154, 'observation': 'Support hand reaches forward while rifle lowers; no separate bolt/coil cycle.'}, {'path': '/private/tmp/w189-erentil-report/reference-8160.png', 'sha256': 'f4c4260ff453ca3d44a82a76ba024c68cf007366e1a2dc97a4f9562e92a81921', 'sourceFrameIndex': 8160, 'pts': 8168160, 'timestampSeconds': 272.272, 'nearestAuthoredProgress': 0.923077, 'observation': 'Return to held posture; authored endpoint restores original hip transform.'}, {'path': '/private/tmp/w189-erentil-report/reference-8166.png', 'sha256': '4370f624fd67c060ec719c9916d51d59abd4f8d390e0cb2e778fdcb9daf7014d', 'sourceFrameIndex': 8166, 'pts': 8174166, 'timestampSeconds': 272.4722, 'nearestAuthoredProgress': 1.0, 'observation': 'Reload recovery boundary. Later sprint/ADS is excluded from the authored endpoint.'}], 'shaderPolicy': 'Source silver shader and alternative round optic not imported; canonical blue Omolon atlas/open reflex preserved.'}
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

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Both grips transport identical rigid weapon-space battery offsets.
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

def payload_visible(i):return i<=7 or i>=11

def cell_core(source):
    # Independently authored inserted sleeve. Canonical heel remains exact.
    # Extends from the heel into the grip; dimensions are not recovered source animation.
    e=copy.deepcopy(source['elements'][16])
    e.update(name='Reload_cell_inner_sleeve',**{'from':[7.62,4.45,2.02],'to':[8.38,7.55,2.66]})
    e['rotation']={'origin':[8.,6.,2.34],'x':16.970743,'y':0,'z':0}
    return [e]

def partition(source):
    models={part:copy.deepcopy(source) for part in PARTS}
    models['body']['elements']=[copy.deepcopy(e) for i,e in enumerate(source['elements']) if i not in BATTERY_INDICES]
    models['magazine']['elements']=[copy.deepcopy(source['elements'][16])]+cell_core(source)
    return models

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
    def posed(i,grip='native',hand=FP[0],canonical=False,cell_only=False):
        ts=[]
        for part in PARTS:
            if part=='magazine' and not canonical and not payload_visible(i):continue
            if cell_only and part!='magazine':continue
            model=json.loads(output[A/f'models/{KEY}_{part}.json'])
            if canonical:model['elements']=[e for e in model['elements'] if not e.get('name','').startswith('Reload_')]
            child=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json']);d=child['display'][hand]
            rr=np.array(xyz(d['rotation']));ss=np.array(d['scale']);tt=np.array(d['translation'])
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
    cam=[1,.22,.18];groups=[posed(i) for i in range(21)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,310)
    panels=[raster(g,cam,400,310,extent) for g in groups]
    all21=Image.new('RGB',(7*400,3*340+40),'#111925');label=ImageDraw.Draw(all21)
    label.text((12,8),'ERENTIL FR4 |21 emitted samples |OFFLINE / NO HANDS / NOT NATIVE |same camera+extent',fill='white')
    for i,panel in enumerate(panels):
        x=i%7*400;y=40+i//7*340;all21.paste(panel,(x,y));label.text((x+8,y+313),f'p={i/20:.2f}',fill='white')
    all21.save(evidence/'authored21.png')
    sheet=Image.new('RGB',(1600,1900),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((14,12),'ERENTIL FR4 W189 | OFFLINE / NO HANDS / NOT NATIVE | exact emitted JSON + authored display transforms',fill='white')
    for col,camera in enumerate(([1,0,0],[1,.4,-.5],[-1,.35,.6],[.25,.5,1])):
        sheet.paste(raster(posed(0,canonical=True),camera,400,300),(col*400,70));draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    for row,indices in enumerate(((3,5,7,9),(11,13,15,20))):
        for col,i in enumerate(indices):
            y=420+row*360;sheet.paste(panels[i],(col*400,y));draw.text((col*400+10,y-24),f'p={i/20:.2f} / shared camera + extent',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        # Each grip uses one fixed framing across all21; no per-frame recenter.
        gg=[posed(i,grip,hand) for i in range(21)]
        ee=helper['frame'](np.concatenate([t[0] for g in gg for t in g]),cam,400,310)
        sheet.paste(raster(gg[13],cam,400,310,ee),(col*400,1150));draw.text((col*400+10,1126),grip+' / '+hand.replace('firstperson_',''),fill='white')
    sheet.paste(raster(posed(7,cell_only=True),[1,.25,.4],460,260),(10,1530))
    raw=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_erentil_fr4.py'))
    ms,_,_=raw['source_meshes']();cell=next(m for m in ms if m['name']=='8D2EEB80_Group0_Index0_0_GripStock0')
    neutral=np.array([[[155.,165.,175.,255.]]]);rawts=[]
    for face in cell['faces']:
        ps=cell['vertices'][face];normal=np.cross(ps[1]-ps[0],ps[2]-ps[0]);norm=np.linalg.norm(normal)
        if norm:rawts.append((ps,np.zeros((3,2)),neutral,normal/norm))
    sheet.paste(raster(rawts,[1,.25,.4],460,260),(510,1530))
    draw.text((14,1500),'AUTHORED whole cell: canonical heel + inserted sleeve',fill='white');draw.text((520,1500),'INERT RAW lower GripStock /336 triangles /neutral',fill='white')
    for y,line in enumerate(('134 fixed +1 canonical heel +1 inner sleeve =136 max','135 canonical endpoints /810 original face UVs unchanged','Source silver shader/round optic are NOT imported','Sleeve profile and trajectory authored; hidden core not verified','Capacity5 /50ticks /all combat and audio unchanged')):
        draw.text((990,1540+y*37),line,fill='white')
    draw.text((14,1840),'Ortho inspection only. Fixed practical-screen clearance measurements are in manifest. Native hand fit, exact framing/audio/performance pending master.',fill='white')
    story=Image.new('RGB',(1600,2480),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL Erentil FR4 /ThatUnknown /539XTHi69Pg | authored emitted output below / not a recovered animation',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225));x=j%4*400;y=55+j//4*595;story.paste(im,(x,y))
        draw.text((x+8,y+231),f"ACTUAL n={f['sourceFrameIndex']} PTS={f['pts']} t={f['timestampSeconds']:.3f}",fill='white')
        i=round(f['nearestAuthoredProgress']*20);story.paste(panels[i],(x,y+260));draw.text((x+8,y+573),f'AUTHORED p={i/20:.2f} / common framing',fill='white')
    draw.text((14,2450),'OFFLINE / NO HANDS / NOT NATIVE.16 unaltered source frames /30000:1001fps /1:30000 PTS. Authored hip endpoints, blue shader, reflex remain canonical.',fill='white')
    return png(sheet),png(story)

def practical_clearance(source,two):
    # Bounded conventional held-camera proxy, not the server two_hand carrier.
    # Normalize each accepted grip into native hand space before this measurement.
    # Assumptions: held offset(+/-.56,-.52,-.72),70deg vertical FOV,16:9.
    rows=[]
    for hand in FP:
        for i in range(4,17):
            for part in PARTS:
                if part=='magazine' and not payload_visible(i):continue
                d=pose_display(source['display'],two,i/20,part,'native')[hand]
                v=[(q-8)*s for q,s in zip(MAGAZINE_ANCHOR,d['scale'])]
                point=add(vec(xyz(d['rotation']),v),d['translation'])
                if hand==FP[1]:point[0]*=-1
                point=add(point,[-8.96 if hand==FP[1] else 8.96,-8.32,-11.52])
                depth=-point[2];factor=math.tan(math.radians(35))
                uv=[.5+point[0]/(depth*factor*16/9)/2,.5-point[1]/(depth*factor)/2]
                if not (depth>1 and .06<=uv[0]<=.94 and .06<=uv[1]<=.94):raise ValueError(('Proxy seat/cell out of practical frame',hand,i,part,uv))
                rows.append(dict(hand=hand,sample=i,part=part,screenUV=uv,depth=depth))
    return dict(kind='Conventional held-camera proxy; both accepted grips normalized to native before comparison',assumptions=dict(handOffsetUnits=[.56,-.52,-.72],verticalFovDegrees=70,aspect=[16,9],safeMargin=.06),nativeVerified=False,points=rows)

def generate(render=False,evidence=Path('/private/tmp/w189-erentil-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=135:raise ValueError('Canonical element drift')
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w189_erentil_fr4.py'),Path('scripts/qa/test_reload_w189_erentil_fr4.py'),Path('src/test/java/kim/biryeong/destiny/weapon/ReloadW189ErentilTest.java'),ART/'SOURCE.md']
    raw=Path('/tmp/destiny-weapons-w30/raw/erentil_fr4/extracted/Erentil FR4/Erentil FR4.fbx')
    # Persist original rip provenance, without requiring external media for --verify.
    raw_hash='0de5493a15cc3fb9a1bc7862ab40c846ca142aaea1d563b7f10ed915f380b7b0'
    emit(ART/'manifest.json',dict(stage='W189',weapon='erentil_fr4',revision=1,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=135,bodyElements=134,movingElements=2,maxAssembledElements=136,endpointAssembledElements=135,elementLimit=1000,addedElements=1,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=dict(body=[i for i in range(135) if i not in BATTERY_INDICES],magazine=list(BATTERY_INDICES)),
        geometryPolicy='All135 canonical elements/810faces/rotations/UV/default blue paint unchanged. Only Cartridge_base index16 separates; fixed grip/brace/receiver/cylinders/hoses/sight never impersonate ammunition.',
        payloadPolicy='Complete reload cell represented by original heel plus1 authored rigid inner sleeve. Constant scale; omitted samples8..10 for below-frame exchange. Added sleeve never appears at canonical endpoints.',
        sourceLimitation=dict(fullPayloadSourceFidelityVerified=False,resolution='Lower-grip exchange and separate raw heel assembly verified; concealed sleeve exact profile, hand fit and absolute animation dimensions authored/unverified.'),
        originalRip=dict(path=str(raw),sha256=raw_hash,parser='Inert binary FBX7500; embedded Erentil FR4.py was never executed',partName='8D2EEB80_Group0_Index0_0_GripStock0',vertices=328,triangles=336,bounds=[[7.304581729,3.700629008,.827771290],[8.695420265,5.609437122,5.470086335]],canonicalMapping='index16 Cartridge_base is heel; index14 Grip_heel and13 Triangle_lower_brace stay fixed. Inner sleeve added from observed exchange, not mesh conversion.'),
        reloadOnlyGeometry=dict(elements=cell_core(source),count=1,visibleSampleIndices=[i for i in range(21) if payload_visible(i)],uvPolicy='Sleeve uses unchanged existing Cartridge_base face UVs; no atlas modification.'),
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineExtractionAxis=[0,-.95646,-.29189],hipEndpoints=[0,20],
        endpointPolicy='Exact0/1 and overshoot original graph; negative/nonFP/ADS/inspect canonical; child0/20 accepted display.',
        normalizedPhases=dict(rise=[0,.20],withdraw=[.20,.36],belowFrameExchange=[.36,.54],incoming=[.54,.69],seat=[.69,.74],release=[.74,.80],lower=[.80,1]),
        reference=REFERENCE,referencePolicy='Actual same-weapon identity and continuous n8088..8166,30000/1001fps.16 exact source PNGs, decoded PTS and hashes. No internet mechanism text or W188 motion copied.',
        authoredPolicy='Independent Erentil grip-axis extraction with below-left hand-transfer arc, replacement alignment, upward compression, hand release and lowering. Positive common FP lift protects practical screen clearance.',
        practicalViewport=practical_clearance(source,two),
        authoredHiddenDetails='Grip pivot, angles, displacements, inner sleeve and durations normalized to50ticks. No imported hands/bones/animation/bolt/coil motion.',
        timingPolicy='Capacity5,reload50ticks,charge20ticks,cadence11.666666666667,burst5/spacing.666666666667/sharedBurstAmmo=true; shellReload=false. All gameplay/audio unchanged.21normalized samples at2.5tick spacing; footage HUD2 is reserve, not capacity.',
        numericAuthority=dict(url='https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4',policy='Numeric priority; basic/enhanced/PvE/PvP separate, preserve ? uncertainty. No numeric gameplay changes or retroactive DDC audit claimed.'),
        rotationConvention='JOML Rx Ry Rz; accepted uniform scales; native motion transported into twohand; left ItemTransform F*T*F.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration=dict(workerRuntimeEdited=False,masterOwnsRegistryRuntime=True,requiredMasterModel='destiny:'+KEY,catalogId='erentil_fr4',assetInputs='float[1]progress;boolean[0]grip;string[0]ads/inspect',capacity=5,reloadTicks=50),
        nativeQueue=['Master admit erentil_fr4 route to this item; no shared route edited by worker.', 'Both grips/FP hands:21samples, especially.20,.35,.55,.65,.75; lower-grip seat and cell visibly inside viewport; hand fit.', 'Negative/zero/one/overshoot/nonFP/ADS/inspect guards; partial/empty/no-reserve/cancel/switch/equip/death/disconnect.', 'Native pack load; unchanged charge/burst/reload audio listening;10-20 displays.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Expected exact90 paths')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w189-erentil-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+' 90 deterministic outputs;87 pack assets;134+2=136 max;135 canonical endpoints;native pending')
if __name__=='__main__':main()
