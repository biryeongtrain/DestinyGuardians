#!/usr/bin/env python3
"""W183 High Albedo same-weapon reference-led FP carrier/grip-magazine motion.
Preserves all 100 canonical solids/UV/default dye. Revision2 adds an authorized
reload-only ribbed shaft from actual frame1998, reusing the unchanged atlas.
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
ART=Path('art/weapons/w183/high_albedo')
KEY='weapon_reload_w183_high_albedo/high_albedo'
SOURCE=A/'models/weapon_surface_w123/high_albedo.json'
TWOHAND=A/'models/weapon/sidearm/high_albedo_twohand.json'
ITEM=A/'items/weapon/high_albedo.json'
TEXTURE=A/'textures/item/weapon/w123/high_albedo.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.65,7.85)  # canonical grip_core origin, retained right-hand carrier
MAGAZINE_ANCHOR=(8.,5.97,8.67)  # canonical magazine_base origin, X=-17deg
# High Albedo footage: lift/cant -> grip release -> low incoming magazine ->
# insertion -> inward roll and occluded upper/rear support-hand sweep -> recover.
# Numeric angles/offsets/phase ratios are authored, not tracked bones/camera.
KEYS=((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.08, (18, 2, -3), (0.12, -0.12, 0), (0, 0, 0)), (0.2, (42, 10, -16), (0.35, 0.18, 0.12), (0, 0, 0)), (0.3, (46, 16, -29), (0.45, 0.25, 0.15), (0, -2.8, 0.856)), (0.4, (44, 17, -31), (0.45, 0.25, 0.15), (-0.5, -5.2, 1.59)), (0.5, (43, 17, -30), (0.45, 0.23, 0.15), (-0.16, -2.3, 0.703)), (0.6, (41, 18, -27), (0.45, 0.2, 0.15), (0, 0, 0)), (0.7, (33, 22, -33), (0.38, 0.1, 0.1), (0, 0, 0)), (0.8, (22, 25, -40), (0.3, 0, 0.1), (0, 0, 0)), (0.86, (26, 16, -24), (0.22, 0.06, 0.05), (0, 0, 0)), (0.92, (9, 5, -7), (0.1, -0.02, 0), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/high_albedo.json': '0d024cb48ff2179ebfd9dffefb16a2674cff40842e5d16561f7e0c17e8b88d85', 'src/main/resources/assets/destiny/textures/item/weapon/w123/high_albedo.png': '1f6356f5fcfc4a62ba7cc8deef45b3ff2fbf841287d634e17d2a496af4d95b1a', 'src/main/resources/assets/destiny/items/weapon/high_albedo.json': '9362eb55bf73fc5276cd42f3fa5298bf1e3ed4e02c2ad81e41eb69f3677d6672', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/sidearm/high_albedo_ads_twohand.json': '88dcfa332a400ee329597911af736798629072246d939575b8d2ba7d582b7fa1', 'src/main/resources/assets/destiny/models/weapon/sidearm/high_albedo_inspect.json': 'fcc677f8b5ca28245b0f418f57121623550c47cfd9fb739bb971ca8935d5ed21', 'src/main/resources/assets/destiny/models/weapon/sidearm/high_albedo.json': '8a8b8f38c8332ce63bf953c29de7c4e651a17c12549670bfb336ca9885ec412d', 'src/main/resources/assets/destiny/models/weapon/sidearm/high_albedo_ads.json': '9455363f2bd087739c8d4873471ac84daf257091fc7a7958f6211aee6fc932f8', 'src/main/resources/assets/destiny/models/weapon/sidearm/high_albedo_inspect_twohand.json': '1395bab1725350d2b0ab9e36e6cabbbed5eeb82fb90083050cb54eaa68e3a228', 'src/main/resources/assets/destiny/models/weapon/sidearm/high_albedo_twohand.json': '5165fd6a6159aab9978939e7a1d02fc1615328d1b8a2ca71aa81c6b550940e6b'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=vBiSPlhfkMI', 'title': 'Is The High Albedo Good?  (Destiny 2: Beyond Light)', 'creator': 'DrDestiny', 'uploadDate': '20201122', 'fpsNumerator': 60, 'fpsDenominator': 1, 'sourceTimebase': '1/15360', 'actionFrameRange': [1960, 2052], 'actionSeconds': [32.666666666666664, 34.2], 'sourceVideoFile': '/private/tmp/w183-albedo-report/review.mp4', 'sourceMetadataFile': '/private/tmp/w183-albedo-report/review.info.json', 'sourceVideoSha256': '0a894c2cc8bf481aa97f7690b8b82c9900e8135256f643ef12eac3b460ec50ff', 'sourceMetadataSha256': 'bc2f114a1b1464802028e95551545b850c99279bd7e2dc64e58f1ebdb32d054b', 'frames': [{'path': '/private/tmp/w183-albedo-report/reference-01.png', 'sha256': '7e4c044b5c9d46b1c492d25c9fe00a7422ccc75a2fef8a7c4327cd749ad1d6da', 'sourceFrameIndex': 240, 'timestampSeconds': 4.0, 'nearestAuthoredProgress': 0, 'observation': 'Inventory explicitly HIGH ALBEDO; orange muzzle brace, open red cage, blue receiver, orange reservoir and lower silver cylinder match canonical base appearance.'}, {'path': '/private/tmp/w183-albedo-report/reference-02.png', 'sha256': '39a87145f90deaa6b6f344e7f5fb5987fdd06dd00fca064c23f20f2bd86b9411', 'sourceFrameIndex': 1956, 'timestampSeconds': 32.6, 'nearestAuthoredProgress': 0, 'observation': 'Before reload: one remaining round in HUD; exact phase boundary is authored at32.6667s.'}, {'path': '/private/tmp/w183-albedo-report/reference-03.png', 'sha256': 'ce583d0f568c7178b626672bef9f2232fd64cdf4561497ccca03b3e7e6f36932', 'sourceFrameIndex': 1968, 'timestampSeconds': 32.8, 'nearestAuthoredProgress': 0.1, 'observation': 'Muzzle lift begins while right hand keeps pistol grip. Under-barrel cylinder and carry bridge remain attached.'}, {'path': '/private/tmp/w183-albedo-report/reference-04.png', 'sha256': '8803bdbc3f95a3c02102d6f4b27d9fb09c9e04b8cf6f4053c268a5444eb9df9a', 'sourceFrameIndex': 1980, 'timestampSeconds': 33.0, 'nearestAuthoredProgress': 0.2, 'observation': 'Strong diagonal muzzle-up presentation; support forearm reaches toward pistol grip base.'}, {'path': '/private/tmp/w183-albedo-report/reference-05.png', 'sha256': '9ca1a019682304e90db325ebc16425c683ccb774463fe86fd5e978ff12895bfc', 'sourceFrameIndex': 1986, 'timestampSeconds': 33.1, 'nearestAuthoredProgress': 0.3, 'observation': 'Support hand covers grip-base release; no separate cylinder opening or barrel break.'}, {'path': '/private/tmp/w183-albedo-report/reference-06.png', 'sha256': '91673de105c33e45b906f9c8ce01446dc941b5a385d87fda2eb16e75dc6648a2', 'sourceFrameIndex': 1992, 'timestampSeconds': 33.2, 'nearestAuthoredProgress': 0.35, 'observation': 'Support hand drops below grip; outgoing path partly hand/screen occluded.'}, {'path': '/private/tmp/w183-albedo-report/reference-07.png', 'sha256': '4769377f6914eb026bb0228dc552af404b4d379a6d555ea07042fc2a526c15e8', 'sourceFrameIndex': 1998, 'timestampSeconds': 33.3, 'nearestAuthoredProgress': 0.4, 'observation': 'Incoming long rectangular magazine is visible below grip in support hand. Canonical asset lacks this shaft and contains only magazine_base.'}, {'path': '/private/tmp/w183-albedo-report/reference-08.png', 'sha256': 'e32ad71c36c0da67dec7937c8d36e6eda7560326157a95a762c736a4f32e27f5', 'sourceFrameIndex': 2004, 'timestampSeconds': 33.4, 'nearestAuthoredProgress': 0.5, 'observation': 'Magazine insertion toward grip; tip/seat boundary occluded behind fingers. Carrier remains canted up.'}, {'path': '/private/tmp/w183-albedo-report/reference-09.png', 'sha256': '227ee7e34f512bcb2541a43f95531e4e828a4ad0dc9a92e17174ef7d69ad654d', 'sourceFrameIndex': 2016, 'timestampSeconds': 33.6, 'nearestAuthoredProgress': 0.6, 'observation': 'Support hand has left grip; canted receiver held briefly. No moving bolt visible.'}, {'path': '/private/tmp/w183-albedo-report/reference-10.png', 'sha256': 'efda12c9dd9631d92757d547b0879eb31e675871d4ca3df4964cb81228e6e1f6', 'sourceFrameIndex': 2028, 'timestampSeconds': 33.8, 'nearestAuthoredProgress': 0.75, 'observation': 'Carrier rolls/lowers inward; HUD now30. Source capacity/perk is not a gameplay input.'}, {'path': '/private/tmp/w183-albedo-report/reference-11.png', 'sha256': 'beade491c3e4b170b0742c2cdf6a3632317d07ff3d1fa95895392d6b89f7f6af', 'sourceFrameIndex': 2040, 'timestampSeconds': 34.0, 'nearestAuthoredProgress': 0.85, 'observation': 'Support hand sweeps across upper/rear receiver, obscuring exact manipulation. No individually resolved bolt travel is animated.'}, {'path': '/private/tmp/w183-albedo-report/reference-12.png', 'sha256': '4ddc5fe55ea97c32cd2492fc01a3ff651aadb9dbdc00e03e289e00817c729c22', 'sourceFrameIndex': 2052, 'timestampSeconds': 34.2, 'nearestAuthoredProgress': 1, 'observation': 'Weapon returns to aiming presentation. Canonical hip endpoint authored to local product transform; source continues aiming.'}]}

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
    # The only existing magazine geometry is the exposed baseplate, not a shaft.
    # Grip heel/backstrap, lower cylinder, selector, cage and sight remain fixed.
    return e['name'] == 'magazine_base'


def reload_shaft(source):
    """Authored shaft from frame1998: elongated rectangular core + ribbed broad sides.
    Whole assembly shares the original baseplate anchor and -17deg grip axis.
    Existing dark baseplate/steel atlas regions only. No texture file modification.
    """
    dark=copy.deepcopy(source['elements'][91]['faces']['up'])
    metal=copy.deepcopy(source['elements'][16]['faces']['up'])
    # Restrict metal UV to an interior patch of the existing steel barrel region;
    # avoid stretching a border or repeating its unrelated long barrel bands.
    metal['uv']=[.3125,.25,.4375,.375]
    def box(name,lo,hi,face):
        return dict(name='magazine_shaft_'+name,**{'from':lo,'to':hi},
            rotation=dict(origin=list(MAGAZINE_ANCHOR),axis='x',angle=-17),
            faces={f:copy.deepcopy(face) for f in ('north','south','east','west','up','down')})
    result=[box('core',[7.50,6.08,8.09],[8.50,10.12,9.25],dark)]
    # Source broad face has three longitudinal reinforcing bars and two cross bars.
    # Mirror its structural ribs on both broad faces; fine dimensions are authored.
    for side,x0,x1 in [('left',7.474,7.505),('right',8.495,8.526)]:
        for i,z in enumerate((8.18,8.67,9.16)):
            result.append(box(f'{side}_longrib_{i}',[x0,6.18,z-.022],[x1,10.02,z+.022],metal))
        for i,y in enumerate((7.18,9.12)):
            result.append(box(f'{side}_crossrib_{i}',[x0-.002,y-.025,8.11],[x1+.002,y+.025,9.23],metal))
    return result


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
                model['elements']=[e for e in model['elements'] if e['name'].startswith(('grip_','magazine','blue_backstrap','red_finger_spine'))]
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
    draw.text((14,12),'W183 HIGH ALBEDO | reference-led canonical JSON motion | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.55,-.7],[-1,.45,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,310),(col*400,70))
        draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.35,.55];groups=[posed(i) for i in (0,8,14,20)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,350)
    for col,(i,g) in enumerate(zip((0,8,14,20),groups)):
        sheet.paste(raster(g,cam,400,350,extent),(col*400,420))
        draw.text((col*400+10,396),f'p={i/20:.2f} / fixed camera + common scale',fill='white')
    draw.text((14,794),'111 reload elements = 99 canonical body + original baseplate + 11 reference-backed shaft/rib elements. Canonical endpoints =100.',fill='white')
    for col,i in enumerate((0,8,12,16)):
        sheet.paste(raster(posed(i,detail=True),[1,.25,.25],400,350),(col*400,855))
        draw.text((col*400+10,828),f'GRIP / PAYLOAD DETAIL p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(8,grip=grip,hand=hand),[1,.35,-.5],400,410),(col*400,1270))
        draw.text((col*400+10,1244),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((14,1710),'Observed: diagonal lift -> grip exchange -> inward roll + upper/rear hand sweep -> recover. Exact numeric poses authored.',fill='white')
    draw.text((14,1740),'Authorized reload-only ribbed shaft uses existing atlas; cylinder/grip/sight/cage fixed. Exact0/1 dispatch canonical full graph.',fill='white')
    draw.text((14,1770),'Actual footage and hashes: SOURCE.md + manifest. Native screen, hand contact, audio and performance remain pending.',fill='white')
    story=Image.new('RGB',(1600,1900),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL HIGH ALBEDO: DrDestiny / vBiSPlhfkMI / 2020-11-22 | independent authored normalized reload below',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225))
        x=j%4*400;y=55+j//4*605;story.paste(im,(x,y))
        draw.text((x+8,y+232),f"ACTUAL n={f['sourceFrameIndex']} / {f['timestampSeconds']:.5f}s",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.35,.55],400,295),(x,y+263))
        draw.text((x+8,y+567),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((14,1876),'60/1 fps, timebase 1/15360; frame-exact PNGs retained externally. Shaft geometry from n1998; exact hidden poses/proportions authored.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w183-albedo-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=100:raise ValueError('Canonical element drift')
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w183_high_albedo.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W183',weapon='high_albedo',revision=2,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=100,bodyElements=99,movingElements=12,maxAssembledElements=111,endpointAssembledElements=100,elementLimit=1000,addedElements=11,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,
        geometryPolicy='All100 canonical W143 solids/faces/UV/default dye unchanged. Body=indices0..90,92..99. Magazine=canonical91 magazine_base plus11 authorized reload-only shaft/rib cuboids. Grip/cylinder/sight/cage fixed. Endpoints route canonical full geometry; no shaft in canonical files.',
        payloadPolicy='One rigid complete represented magazine: original baseplate plus source-backed long shaft/ribs. Core1+longitudinal ribs6+cross ribs4. Same original anchor/-17deg grip axis, original dark/steel UVs. No separate bullets, casing, duplication or scaling.',
        sourceLimitation={'fullMagazineFidelityBlocked':False,'canonicalShaftAbsent':True,'resolution':'Master explicitly authorized reload-only source-backed shaft addition without canonical/atlas edits. Revision1 baseplate-only rejected and preserved externally. Exact shaft dimensions/rib thickness/hidden back face remain authored from visible evidence.','canonicalMovingNames':['magazine_base'],'canonicalMovingIndices':[91]},
        reloadOnlyGeometry=dict(elements=reload_shaft(source),count=11,sourceFrameIndex=1998,sourceTimestampSeconds=33.3,coreDimensions=[1,4.04,1.16],broadSideAspectRatio=4.04/1.16,uvPolicy='Core uses exact existing magazine_base up-face UV. Ribs use interior steel barrel UV [.3125,.25,.4375,.375]. Atlas file unchanged.',rigidAnchor=list(MAGAZINE_ANCHOR),sourceAxisDegrees=-17),
        semanticGroups={'body':99,'originalMagazineBaseplate':1,'reloadOnlyShaftCore':1,'reloadOnlyShaftRibs':10,'fixed':['grip_core','grip_heel','blue_backstrap','blue_cylinder_mount','rear_sight_blade']},
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineExtractionAxis=[0,-.956304756,.292371705],hipEndpoints=[0,20],
        endpointPolicy='Progress samples0/20 select exact canonical full item graph (100 elements), never shaft parents. Child0/20 displays retained canonical but unreachable from item graph. NonFP/negative/ADS/inspect canonical. Intermediate shaft occluded inside fixed grip when seated.',
        normalizedPhases={'liftCant':[0,.20],'gripRelease':[.20,.30],'lowerExchange':[.30,.40],'insert':[.40,.60],'inwardRoll':[.60,.80],'occludedRearHandSweep':[.80,.86],'canonicalRecover':[.86,1]},
        reference=REFERENCE,
        referencePolicy='Same High Albedo release-era review: inventory name, default orange muzzle brace/red cage/blue rear housing/orange reservoir/silver lower cylinder, then matching FP silhouette. Inventory shown at4.0s. No API item hash or perk roll inferred from pixels. Alternate shader clip is excluded from product paint/sight input.',
        motionAuthorship='Observed diagonal muzzle lift/cant, support-hand grip-base release, incoming rectangular magazine, insertion, inward roll and upper/rear hand sweep. Exact angles, offsets, pivot, normalized phase boundaries and canonical hip recovery are authored interpretations. No separately resolved bolt movement in footage; no bolt articulation added. W182 reused only graph/matrix/CPU renderer infrastructure; trajectory independently authored from this source.',
        authoredHiddenDetails='Grip release and magazine seat partly hand/screen occluded. Source magazine shaft added only to reload parent under explicit master authorization; numeric shaft dimensions and hidden backside authored from visible ribbed rectangle. Support hand upper/rear sweep hides mechanism; carrier accent only, never an invented bolt stroke. No hand mesh or IK.',
        timingPolicy='Visual normalized progression only. Preserve magazine27, reload36ticks, RPM491, cadence7.333333333333ticks, burst3, burstSpacing1.333333333333ticks, shellReloadfalse and all original ammo transfer/sound. Source32.666667..34.2s and HUD30 are observation only, not gameplay timing/capacity.',
        rotationConvention='Display JOML Rx Ry Rz. Equal uniform canonical scale; twohand carrier transforms complete native motion. Left apply F*T*F; offline renderer mirrors independently. Canonical element axis/angle retained.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration={'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'high_albedo','assetInputs':'float1 normalized0..1; boolean0 grip; negative float1 inactive; string0 ads/inspect canonical guard. Master owns route/admission/lifecycle.'},
        nativeQueue=['Verify source-backed reload-only whole magazine shaft proportions and hand clearance in native; no exact original mesh/animation claim.',
        'Master route/admit high_albedo, keep36tick clock and unchanged ammo/sound.',
        'Both FP hands/grips: check hand contact, diagonal cant, baseplate clearance/seat, rear-sweep carrier and exact endpoint recovery.',
        'ADS/inspect/negative/nonFP canonical fallback; cancellation/equip/switch/death/disconnect and partial/empty/no-reserve reload lifecycle.',
        'Native pack load, unchanged audio listening and10-20weapon visual stability remain pending.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w183-albedo-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w183-manifest.json').read_bytes())['features'] if f['name']=='w183-albedo'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic core outputs/media hashes; 87 pack assets; 99+12=111 reload elements, canonical endpoints100; native pending')
if __name__=='__main__':main()
