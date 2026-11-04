#!/usr/bin/env python3
"""W182 Antiope-D FP reload from inspected same-weapon gameplay.
Canonical 118 solids/UV/dye and gameplay retained. Only owned pack/art writes.
--render reads retained actual frames in external --evidence; --verify is media-free.
W180 supplies rigid algebra/graph conventions only, never motion evidence.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w182/antiope_d')
KEY='weapon_reload_w182_antiope_d/antiope_d'
SOURCE=A/'models/weapon_surface_w123/antiope_d.json'
TWOHAND=A/'models/weapon/submachine_gun/antiope_d_twohand.json'
ITEM=A/'items/weapon/antiope_d.json'
TEXTURE=A/'textures/item/weapon/w123/antiope_d.png'
FP=('firstperson_righthand','firstperson_lefthand')
MAGAZINE_NAMES=('magazine_core','magazine_front_spine','magazine_back_spine','magazine_floor','magazine_pull_front')
GRIP=(8.,9.35,9.45)
MAG_ANCHOR=(8.,8.16,8.675)
# Antiope source: sharp upward extraction -> rolled grip socket hold ->
# replacement into pistol grip -> seating impulse -> support hand forward -> hip.
# p, carrier XYZ degrees, display translation, whole-magazine local translation.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0)),
 (.08,(14,-5,18),(.15,-.10,.1),(0,-1.5,0)),
 (.16,(33,-9,43),(.40,.10,.2),(-.6,-7.4,.25)),
 (.27,(19,-9,32),(.30,-.10,.2),(-.6,-7.4,.25)),
 (.40,(20,-9,32),(.30,-.10,.2),(-.6,-7.4,.25)),
 (.50,(24,-8,35),(.25,-.05,.15),(-.2,-3.2,.05)),
 (.60,(28,-7,38),(.20,.05,.15),(0,0,0)),
 (.68,(29,-7,36),(.20,.10,.15),(0,0,0)),
 (.77,(14,-3,19),(.10,-.05,.1),(0,0,0)),
 (.90,(4,-1,5),(.03,-.03,.03),(0,0,0)),
 (1.,(0,0,0),(0,0,0),(0,0,0)),
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/antiope_d.json': 'eeecb773b29a06cd84b6b2e101ca29139e1327c397e520d2ffa4799b3b54b674', 'src/main/resources/assets/destiny/textures/item/weapon/w123/antiope_d.png': 'e70ceed542f988785e03d8785284be11a0743e536ffa2a4f7ee357566fa5c124', 'src/main/resources/assets/destiny/items/weapon/antiope_d.json': 'c1fb96d9b2104c36e6569f491dd7e1b273c0b110df4027e3a0f79a8f3ced8b9a', 'src/main/resources/assets/destiny/items/weapon_aim_w70/antiope_d.json': '5ec557f2dcce358dd6a50cc84736af3278b90314b9b62b65d4306b6183acdf6b', 'src/main/resources/assets/destiny/items/weapon_sight_w153/antiope_d.json': '49740e3c49dbd3c5ed6c217aef42fc9b2646c16314f026dab66f5fdfd801fde2', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/antiope_d.json': 'c3154796e5b5dc0605f6ba385b6d8b703e755b71498135ecf6b5a5470bd8469a', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/antiope_d_twohand.json': '16d0e5c8d86999fcee754d52a3844c4fb1267c87663e7ee5526776ae0f4953cd', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/antiope_d_ads.json': '4b354e39d7081c5284ca221c3757f5793dab37214b42bbee5a492969c45b4010', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/antiope_d_ads_twohand.json': '10218de82b52b24dbc1272badd4faf29184f1193945ea7afd1da12af137a010b', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/antiope_d_inspect.json': '17b9451dd1c5d47757667704081146da0acc485df8917645136c6214f4cd6c37', 'src/main/resources/assets/destiny/models/weapon/submachine_gun/antiope_d_inspect_twohand.json': 'fe7e4ac45df55faf7b294756d0a9a61ddc89a02843029f3948dbf1b7da166920'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=M3tC-IkkFRU', 'creator': 'CammyCakes Gaming', 'title': 'The Perfect Antiope-D does exist!', 'published': '2019-08-04', 'fps': 60, 'dimensions': [1280, 720], 'selectedSeconds': [99.65, 101.0], 'identitySeconds': 10.0, 'inspectedActualFrames': True, 'frames': [{'file': 'reference-01.png', 'sha256': 'c6d8387fff1f1063111a1f18e591ed69c31151e8f4e8e48342174a496e8dc9ff', 'timestampSeconds': 10.0, 'sourceFrameIndex': 600, 'nearestAuthoredProgress': 0, 'observation': 'ANTIOPE-D nameplate, Hakke branding, pale receiver, orange rear cap, vertical foregrip, narrow grip-fed magazine; inventory identity only.'}, {'file': 'reference-02.png', 'sha256': '81f304aa1db62aa4f6e0defeb1792beef2e8b393e6b69c6d0b156f35c391d82e', 'timestampSeconds': 99.6, 'sourceFrameIndex': 5976, 'nearestAuthoredProgress': 0, 'observation': 'Final ADS shots before reload; HUD16; same narrow barrel and side optic visible.'}, {'file': 'reference-03.png', 'sha256': 'f94e8bf6ea5aca6ccdbdb09dcfc1b35f0c5ea926ed27a50f64bfb98ac31bf000', 'timestampSeconds': 99.7, 'sourceFrameIndex': 5982, 'nearestAuthoredProgress': 0.03703703703703493, 'observation': 'Leaves ADS and lifts/rolls receiver to expose underside of pistol grip.'}, {'file': 'reference-04.png', 'sha256': 'e35e6b6bee649e2e1d35e8af0691c18d475adae0f4bf925f6cf6d983ca27bd4d', 'timestampSeconds': 99.8, 'sourceFrameIndex': 5988, 'nearestAuthoredProgress': 0.11111111111110479, 'observation': 'Sharp upward presentation; support hand carries withdrawn magazine below grip; receiver partly exits upper right.'}, {'file': 'reference-05.png', 'sha256': '3c52630000a38a76ed935eabd332ed76930e1099406f1695b31622b5ee0c242e', 'timestampSeconds': 99.9, 'sourceFrameIndex': 5994, 'nearestAuthoredProgress': 0.18518518518518517, 'observation': 'Receiver settles into rolled presentation; grip socket exposed, magazine out of view.'}, {'file': 'reference-06.png', 'sha256': '3c41fdc862dd0a903fd410147237f8007b2acc88ac5fa707dca84e434229d0bf', 'timestampSeconds': 100.0, 'sourceFrameIndex': 6000, 'nearestAuthoredProgress': 0.259259259259255, 'observation': 'Clear magazine socket held; support hand out of view.'}, {'file': 'reference-07.png', 'sha256': '3ea2aebe378b2e61c7c169700991f94cd9fbed385323c327d17e4ba8bce5f9e6', 'timestampSeconds': 100.1, 'sourceFrameIndex': 6006, 'nearestAuthoredProgress': 0.3333333333333249, 'observation': 'Rolled receiver holds; grip-fed socket still exposed.'}, {'file': 'reference-08.png', 'sha256': 'bb92114a29ec7245c021c8a5976b3c9efdda3986efb6ea1dec89983437fac887', 'timestampSeconds': 100.2, 'sourceFrameIndex': 6012, 'nearestAuthoredProgress': 0.4074074074074053, 'observation': 'Support hand starts returning below pistol grip; replacement approach begins.'}, {'file': 'reference-09.png', 'sha256': 'b42ab229eefcb88c1c280c490115a252bc4c7c2e7d50175da0c2d9f6efa9a648', 'timestampSeconds': 100.3, 'sourceFrameIndex': 6018, 'nearestAuthoredProgress': 0.4814814814814751, 'observation': 'Replacement magazine rises toward bottom of grip; top of magazine enters socket.'}, {'file': 'reference-10.png', 'sha256': 'f3381c696c748c3915dd4d07cf2caec3adab944f7257802678a34d69c8629799', 'timestampSeconds': 100.4, 'sourceFrameIndex': 6024, 'nearestAuthoredProgress': 0.5555555555555555, 'observation': 'Support hand presses magazine into pistol grip; receiver lifts with seating impulse.'}, {'file': 'reference-11.png', 'sha256': '0b0f40cb6147596f32ef47f0b67eeee4b850be7a520627fa6ed97686d53cebe0', 'timestampSeconds': 100.5, 'sourceFrameIndex': 6030, 'nearestAuthoredProgress': 0.6296296296296254, 'observation': 'Magazine seated; HUD26 and Kill Clip appear; support hand releases below grip.'}, {'file': 'reference-12.png', 'sha256': '4876e7f6e4cc9fb409909ac47e204f6bd3cf3c66c21b43fd90e1d828b58cd0b3', 'timestampSeconds': 100.6, 'sourceFrameIndex': 6036, 'nearestAuthoredProgress': 0.7037037037036953, 'observation': 'Open support hand moves forward away from magazine toward foregrip.'}, {'file': 'reference-13.png', 'sha256': '7833be02ab03c5f0e38235f601e077d3530a34ea699bcb75801196f072c212e6', 'timestampSeconds': 100.7, 'sourceFrameIndex': 6042, 'nearestAuthoredProgress': 0.7777777777777756, 'observation': 'Support hand passes forward as muzzle lowers; no separately measurable charging-lug stroke.'}, {'file': 'reference-14.png', 'sha256': 'b37ed72658d5cca759ddc24b058230c1e584ebfc3e4e3427d42dac57cd521d14', 'timestampSeconds': 100.8, 'sourceFrameIndex': 6048, 'nearestAuthoredProgress': 0.8518518518518455, 'observation': 'Foregrip recovery and receiver lowering toward hip.'}, {'file': 'reference-15.png', 'sha256': '861439475ee1cfed331bb82342d1fb525f1077ab99f85e08cb49104632308d71', 'timestampSeconds': 100.9, 'sourceFrameIndex': 6054, 'nearestAuthoredProgress': 0.9259259259259258, 'observation': 'Receiver settles; complete magazine remains seated.'}, {'file': 'reference-16.png', 'sha256': 'fb5a81ac0665e61f4d3274a808d05756d22d2c831523ad9a3e6900edf958a957', 'timestampSeconds': 101.0, 'sourceFrameIndex': 6060, 'nearestAuthoredProgress': 0.9999999999999957, 'observation': 'Ready hip view recovered with complete magazine and same Hakke receiver.'}], 'sourceVideoSha256': 'b0949a310d8791e978b47fc46a8347c5c893693ef02c161618a27fe5307c28e8', 'sourceMetadataSha256': 'df24dca45363d90d4deeccbfea169f0a61532d6e079ed3bc610cee94e8338665', 'timeBasis': 'Sequential decoded frame n/60 from first frame; exact select(n), no seek-time approximation.', 'chargingObservation': 'Partial reload; source support hand returns forward, but no independently measurable charging-lug travel. Canonical charging_handle stays fixed.', 'limitations': ['Source holo sight and gold/red shader differ from canonical iron sights and pale/orange dye; retain local canonical appearance.', 'Source HUD16 to26 and speed/perks do not determine local capacity30 or reload46ticks.', 'Exact hidden magazine exchange path and numeric poses authored; one intact magazine proxies outgoing/incoming.', 'No extracted bones, hand IK, new third-person reload, native pixels, audio or performance claim.']}

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
    """Five connected canonical magazine solids; pistol grip and charging handle stay fixed.
    Each original element appears exactly once, with every field/UV value retained.
    """
    parts={}
    for part in ('body','magazine'):
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for e in source['elements'] if (e['name'] in MAGAZINE_NAMES)==(part=='magazine')]
        parts[part]=model
    return parts

def pose_display(original,twohand,p,part,grip):
    if part not in ('body','magazine') or grip not in ('native','twohand'):raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset=sample(p)
    body=xyz(angles);h=sub(GRIP,(8,8,8));anchor=sub(MAG_ANCHOR,(8,8,8))
    # Rotate both intact canonical parts around pistol contact. Magazine receives only
    # authored source-local withdrawal/clearance; no artificial scaling or generic spin.
    local=(sub(add(h,vec(body,add(sub(anchor,h),offset))),vec(body,anchor))
           if part=='magazine' else sub(h,vec(body,h)))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);s=idle['scale']
        if twohand[context]['scale']!=s or len(set(s))!=1:raise ValueError('Rigid carrier requires equal uniform grip scales')
        rotation=mul(base,body)
        position=add(add(idle['translation'],shift),vec(base,[s[0]*v for v in local]))
        if grip=='twohand':
            carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation'])))
            rotation=mul(carrier,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in ('body','magazine')}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in ('body','magazine') for grip in ('native','twohand'))
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}

def previews(output,evidence):
    """Independent NumPy reconstruction of emitted display JSON; offline/no hands."""
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_antiope_d.py'))
    raster_helper=helper['H']
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles={part:helper['model_triangles'](json.loads(output[A/f'models/{KEY}_{part}.json']),texture) for part in ('body','magazine')}
    def rotation(a):
        x,y,z=np.radians(a)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i,parts=('body','magazine'),grip='native',hand='firstperson_righthand'):
        ts=[]
        for part in parts:
            d=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])['display'][hand]
            rr=rotation(d['rotation']);ss=np.array(d['scale']);tt=np.array(d['translation'])
            for points,uv,tex,normal in triangles[part]:
                flip=np.diag([-1,1,1]) if hand==FP[1] else np.eye(3)
                ps=((np.asarray(points)-8)@flip)*ss@rr.T+tt
                ts.append((ps@flip,uv,tex,flip@rr@flip@normal))
        return ts
    def raster(ts,cam,w,h,extent=None):
        if extent is None:extent=raster_helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return raster_helper['render'](ts,cam,extent,(w,h))[0]
    cams=([1,.2,-.45],[-1,.35,.6],[.4,.4,1]);labels=('muzzle oblique','receiver oblique','stock oblique')
    sheet=Image.new('RGB',(1500,1640),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'W182 ANTIOPE-D | emitted JSON reconstructed independently | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for row,cam in enumerate(cams):
        groups=[posed(i) for i in (0,7,20)]
        extent=raster_helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,500,300)
        for col,(i,g) in enumerate(zip((0,7,20),groups)):
            sheet.paste(raster(g,cam,500,300,extent),(col*500,55+row*340))
            draw.text((col*500+12,35+row*340),f'p={i/20:.2f} / {labels[row]} / common framing',fill='white')
    draw.text((12,1060),'113 body + 5 whole magazine solids = 118 cubes / 0 adapters. Canonical geometry, UV and dye retained.',fill='white')
    for col,cam in enumerate(cams):
        sheet.paste(raster(posed(7,('magazine',)),cam,500,240),(col*500,1110))
        draw.text((col*500+12,1088),'WHOLE MAG: core + front/back spines + floor + pull | '+labels[col],fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(15,grip=grip,hand=hand),[1,.2,-.45],375,240),(col*375,1380))
        draw.text((col*375+8,1357),f'Recovery p=.75 | {grip} / {hand}',fill='white')
    draw.text((12,1620),'Exact hip endpoints; hidden stroke and seat rock authored. No independent bolt motion. Native framing/sound pending master QA.',fill='white')
    story=Image.new('RGB',(2000,2210),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL CammyCakes / M3tC-IkkFRU | Antiope-D identity + reload frames paired with AUTHORED sample | OFFLINE / NO HAND IK',fill='white')
    story_extent=raster_helper['frame'](np.concatenate([t[0] for i in range(21) for t in posed(i)]),[-1,.35,.6],400,225)
    for i,f in enumerate(REFERENCE['frames']):
        x=i%5*400;y=42+i//5*530
        p=evidence/f['file']
        if sha(p.read_bytes())!=f['sha256']:raise ValueError('Reference frame drift: '+str(p))
        im=Image.open(p).convert('RGB');im.thumbnail((400,225));story.paste(im,(x,y))
        draw.text((x+8,y+228),f"ACTUAL {f['timestampSeconds']:.2f}s / n={f['sourceFrameIndex']}",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[-1,.35,.6],400,225,story_extent),(x,y+260))
        draw.text((x+8,y+488),f'AUTHORED p={index/20:.2f} / '+('identity only' if i==0 else 'reload sequence'),fill='white')
    draw.text((420,1650),'One complete grip-fed magazine; no scattered rounds.',fill='white')
    draw.text((420,1680),'Exact pivot/angles/stroke authored; hands absent in asset render.',fill='white')
    draw.text((420,1710),'Actual frames above; offline textured JSON reconstruction below.',fill='white')
    draw.text((420,1740),'Partial reload reference: charging lug stays fixed.',fill='white')
    draw.text((12,2180),'Source gold/red paint + holo sight NOT transferred. Local pale/orange dye + iron sights retained. Hidden stroke/pivot authored; charging handle fixed.',fill='white')
    return png(sheet),png(story)

def generate(render=False,evidence=Path('/private/tmp/w182-antiope-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=118:raise ValueError('Canonical element drift')
    output={}
    def emit(p,v):output[p]=encode(v)
    parts=partition(source)
    for part,model in parts.items():emit(A/f'models/{KEY}_{part}.json',model)
    entries=[]
    for i in range(21):
        for part in ('body','magazine'):
            for grip in ('native','twohand'):emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],two,i/20,part,grip)))
        def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in ('body','magazine')])
        entries.append(dict(threshold=i/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    reload=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model']))
    # Retain the exact accepted ADS/inspect branches even if stale positive reload
    # progress coexists with a mode string. Non-FP and negative inactive are canonical.
    mode_guard=copy.deepcopy(item['model']);mode_guard['fallback']=reload
    wrapper=copy.deepcopy(item);wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=mode_guard)],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)

    if render:
        output[ART/'comparison.png'],output[ART/'storyboard.png']=previews(output,evidence)
    else:
        previous=json.loads((ROOT/ART/'manifest.json').read_bytes())
        for name in ('comparison.png','storyboard.png'):
            p=ART/name;output[p]=(ROOT/p).read_bytes()
            if sha(output[p])!=previous['sha256'][str(p)]:raise ValueError('Preview drift: '+str(p))
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w182_antiope_d.py'),Path('scripts/generate_surface_w123_antiope_d.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W182',weapon='antiope_d',revision=1,itemModel='destiny:'+KEY,
      ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,
      progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
      sourceElements=118,bodyElements=113,movingElements=5,maxAssembledElements=118,cubeElements=118,triangleAdapterElements=0,elementLimit=1000,addedElements=0,
      sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceRevision='W129 semantic 118-solid Hakke model, canonical weapon_surface_w123',geometryAndUVPreserved=True,
      partitionIndices={part:[i for i,e in enumerate(source['elements']) if (e['name'] in MAGAZINE_NAMES)==(part=='magazine')] for part in ('body','magazine')},magazineNames=MAGAZINE_NAMES,
      partitionRationale='All five overlapping magazine core/front spine/back spine/floor/pull solids move as ONE rigid part from bottom of pistol grip. Receiver/grip/foregrip/stock/side optic/sights/guard/charging handle remain rigid body. Every canonical field and UV face appears once.',
      authoredHiddenDetails='Hand and screen edge conceal the exchange. Exact downward clearance7.4, lateral.6, forward.25, grip pivot and numeric poses are authored. One magazine proxies outgoing/incoming. Never scale-hide, duplicate or spin small rounds.',
      keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,hipEndpoints=[0,20],
      normalizedPhases={'liftAndWithdraw':[0,.16],'settleRolledGripSocket':[.16,.27],'emptyGripSocketHold':[.27,.40],'replacementApproachAndSeat':[.40,.60],'seatingRock':[.60,.68],'supportForwardRecovery':[.68,.90],'hipReturn':[.90,1]},
      endpointPolicy='Both parts at0/1 use exact canonical display for both hands/grips. Exact canonical ADS/inspect precedence, negative inactive fallback and non-FP graph.',
      reference=REFERENCE,
      motionAuthorship='Same Antiope-D frame sequence: pronounced upward extraction, rolled presentation of empty pistol-grip socket, replacement rises into grip, seating impulse, open support hand moves forward, receiver returns to hip. Numeric path authored independently; W180/W181 motion not reused.',
      sourceChronology=[{'stage':'W129','evidence':'scripts/generate_surface_w123_antiope_d.py','role':'Canonical118 semantic solids, 708 explicit face UVs and pale/orange dye.'},
        {'stage':'W180','evidence':'scripts/generate_reload_w180_halfdan_d.py','role':'Rigid matrix composition, graph guards and offline raster conventions only; NOT motion reference.'},
        {'stage':'W182','evidence':REFERENCE['url'],'role':'Actual Antiope-D identity10s and reload99.65-101s; dedicated authored keys and grip-fed partition.'}],
      timingPolicy='Normalized visuals only. Preserve local magazine30/reload46ticks/rpm600/cadence2ticks/burst1, whole-mag ammo transfer, funding and existing audio. Source HUD/perks/speed do not change local mechanics.',
      rotationConvention='Display JOML Rx Ry Rz; receiver-local rigid magazine translation; constant uniform scale; twohand rigid carrier. Left native ItemTransform reflection F*T*F. Existing axis/angle element rotations interpreted by canonical Antiope raster helper.',
      nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
      integration={'requiresMasterRouting':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'antiope_d',
        'progress':'float1 normalized; boolean0 true=twohand; negative inactive; strings0 ads/inspect take precedence. Master owns admission/routing/lifecycle/ammo/clocks/native.'},
      nativeQueue=['Both FP contexts x both grips: grip contact, pronounced lift, intact magazine withdrawal, socket hold, insertion, seat impulse, support recovery, exact endpoints; near-plane and receiver/magazine clearance.',
        'ADS/inspect while progressing; negative inactive; GUI/ground/fixed/head/third-person observer exact canonical graph. No new3P reload or handIK claim.',
        'Partial/empty/full/no-reserve, fire/reload spam, switch/cancel/equip/unequip/death/disconnect; master validates one unchanged ammo transfer and46tick lifecycle.',
        'Master single native session: listen to unchanged reload audio; briefly observe10-20 displays for artifacts/stalls. All native/input/audio/performance rows pending.'],
      canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Expected exact90 outputs')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w182-antiope-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w182-manifest.json').read_bytes())['features'] if f['name']=='w182-antiope'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs/media hashes;87 pack assets;113+5=118 assembled elements; native pending')
if __name__=='__main__':main()
