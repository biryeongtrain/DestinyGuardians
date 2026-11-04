#!/usr/bin/env python3
"""Hollow Words W185 whole-cell reload. W184 matrix/graph/renderer infrastructure;
independently authored trajectory from inspected original Hollow Words gameplay.
--verify needs only repository outputs; external media is used only by --render.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w185/hollow_words')
KEY='weapon_reload_w185_hollow_words/hollow_words'
SOURCE=A/'models/weapon_surface_w123/hollow_words.json'
TWOHAND=A/'models/weapon/fusion_rifle/hollow_words_twohand.json'
ITEM=A/'items/weapon/hollow_words.json'
TEXTURE=A/'textures/item/weapon/w123/hollow_words.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,7.17,2.55)  # fixed front grip origin, not heel46
MAGAZINE_ANCHOR=(8.,4.35,3.70)  # canonical under_grip_cell53 center
MAGAZINE_NAMES=('under_grip_cell',)
KEYS=((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.08, (18, -3, -7), (0.12, -0.06, 0.03), (0, 0, 0)), (0.18, (60, -8, -22), (0.34, 0.15, 0.16), (0, 0, 0)), (0.26, (66, -9, -24), (0.38, 0.24, 0.2), (0, -1.65, -0.685)), (0.38, (65, -8, -25), (0.4, 0.23, 0.21), (-0.3, -4.8, -1.99)), (0.48, (64, -8, -24), (0.39, 0.2, 0.2), (-0.5, -4.8, -1.99)), (0.58, (63, -7, -23), (0.36, 0.16, 0.18), (-0.1, -1.55, -0.643)), (0.64, (61, -7, -22), (0.34, 0.12, 0.16), (0, 0, 0)), (0.72, (48, -3, -30), (0.27, 0.03, 0.12), (0, 0, 0)), (0.8, (20, 3, -18), (0.16, -0.1, 0.06), (0, 0, 0)), (0.88, (-4, 2, -4), (0.05, -0.15, 0.01), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/hollow_words.json': '328eed84bf275da019d40d25e3306d48bd00473cf4f64c19d088e6fec91d330a', 'src/main/resources/assets/destiny/textures/item/weapon/w123/hollow_words.png': '6d1ddd0c20a29f7415d9915ccf5dc1137ff3cc0b8539165327ab012a2a5329cf', 'src/main/resources/assets/destiny/items/weapon/hollow_words.json': 'ab5a2dab42d81d8d5fd412f49a0fff5f9759fb8b6659f015ac770ed70683bf31', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_twohand.json': 'a0cea3376e63fc39ead3af6218963483f124e1eab2ac29fac170812c86b53a4f', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_ads.json': 'c56abca4a30e460bc86f069b89b213c5ab5754e07ba5c3e849f1dddc39f48fcf', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_inspect.json': 'd645952f47c92417069075bd00b11b97e1c801f845b56dc0a10a605f67a7519b', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words.json': 'eaf326afdc1711f6ae642c178398f39ef75038b83f705128e11963636a267fb5', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_inspect_twohand.json': '35afc5f4b17f51c1189c446232696ff8611efc61cc00b50505ed638ddf5107c2', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/hollow_words_ads_twohand.json': '9254ade2b2599a3cf98c46696fca5b3c4ae4c5a284536bb002a04caa4e644a77'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=ozOSAOr5T4c', 'title': 'HOLLOW WORDS Destiny 2 PvP Weapon Review!  A Solid Precision Frame Fusion for the Crucible!?', 'creator': 'Ironworker Gaming', 'uploadDate': '20200708', 'fpsNumerator': 60, 'fpsDenominator': 1, 'sourceTimebase': '1/15360', 'actionFrameRange': [11204, 11348], 'actionSeconds': [186.73333333333332, 189.13333333333333], 'sourceVideoFile': '/private/tmp/w185-hollow-report/original.mp4', 'sourceMetadataFile': '/private/tmp/w185-hollow-report/original.info.json', 'sourceVideoSha256': 'ee05a6b627ae2a7353d036972fb6b6efd27d31665c2c2bdf79a2a959fa8967b4', 'sourceMetadataSha256': 'b97cc58732e0ba79472e1ac6df729db5c5b28d28b65244be43fe271ce52c5c1e', 'inspectedActualFrames': True, 'shaderPolicy': 'Reference matches teal/gold and silver identity; canonical atlas is unchanged. HUD5 reflects available reserve, not local capacity6.', 'frames': [{'path': '/private/tmp/w185-hollow-report/reference-01.png', 'sha256': '89391402f3363cb1c33c0f876189f05381ee5a16dacbdf0edb4aef67c97888d1', 'sourceFrameIndex': 6900, 'pts': 1766400, 'timestampSeconds': 115.0, 'nearestAuthoredProgress': 0, 'observation': 'Inventory explicitly HOLLOW WORDS; default teal/gold top, bright silver shoulder, open triangular grip and lower cell establish identity.'}, {'path': '/private/tmp/w185-hollow-report/reference-02.png', 'sha256': '6a129934d046c73219654967de63917ffdcbcd4b73f0c8858f44128d9c0cf992', 'sourceFrameIndex': 11204, 'pts': 2868224, 'timestampSeconds': 186.73333333333332, 'nearestAuthoredProgress': 0, 'observation': 'Last hip pose before lift; HUD1 with4 reserve.'}, {'path': '/private/tmp/w185-hollow-report/reference-03.png', 'sha256': '29fcfc596d3ec0c1c6ed777334e024094101d6675c59c65f688fba4e7f997234', 'sourceFrameIndex': 11210, 'pts': 2869760, 'timestampSeconds': 186.83333333333334, 'nearestAuthoredProgress': 0.05, 'observation': 'Muzzle lifts steeply at right edge; support hand reaches toward lower frame.'}, {'path': '/private/tmp/w185-hollow-report/reference-04.png', 'sha256': '86130d48665f0498e2e835209352f69700bb4e1917739e336779a1f186324506', 'sourceFrameIndex': 11216, 'pts': 2871296, 'timestampSeconds': 186.93333333333334, 'nearestAuthoredProgress': 0.1, 'observation': 'Carrier turns side toward viewer, fixed grip and rear strut remain attached.'}, {'path': '/private/tmp/w185-hollow-report/reference-05.png', 'sha256': '0e1df1bc74b48040cdc4562c2de02b7fd8f5ff6058202c1a9a493ea10a8670f5', 'sourceFrameIndex': 11224, 'pts': 2873344, 'timestampSeconds': 187.06666666666666, 'nearestAuthoredProgress': 0.16, 'observation': 'Steep muzzle-up right-edge presentation, fingers descend toward underside.'}, {'path': '/private/tmp/w185-hollow-report/reference-06.png', 'sha256': 'ec187c5a2c41190d9a0a42cc2076a61a2ba2282bfcd228e4867324099c2b3fc5', 'sourceFrameIndex': 11232, 'pts': 2875392, 'timestampSeconds': 187.2, 'nearestAuthoredProgress': 0.24, 'observation': 'Right hand stays through triangular grip; support hand reaches lower cell, release partly outside frame.'}, {'path': '/private/tmp/w185-hollow-report/reference-07.png', 'sha256': 'bec6524527c5da3945cbaf21a2443f05cac0d6a8c7fc3606660cea5fba84c6a6', 'sourceFrameIndex': 11244, 'pts': 2878464, 'timestampSeconds': 187.4, 'nearestAuthoredProgress': 0.32, 'observation': 'Raised fixed grip/brace visible; lower cell exchange drops below bottom edge.'}, {'path': '/private/tmp/w185-hollow-report/reference-08.png', 'sha256': '2db8095f5180c0f46a13bd122ac926840be39b705ad91d4f72d2a8143a34b79b', 'sourceFrameIndex': 11256, 'pts': 2881536, 'timestampSeconds': 187.6, 'nearestAuthoredProgress': 0.4, 'observation': 'Carrier holds high, hand and screen edge conceal outgoing cell; exact hidden path authored.'}, {'path': '/private/tmp/w185-hollow-report/reference-09.png', 'sha256': '26f53f8e528718f768e6f7c848d43cec4fb2abeb6ad207a1b8a8c405348ddd53', 'sourceFrameIndex': 11268, 'pts': 2884608, 'timestampSeconds': 187.8, 'nearestAuthoredProgress': 0.48, 'observation': 'Support hand remains low/offscreen; fixed grip silhouette unchanged.'}, {'path': '/private/tmp/w185-hollow-report/reference-10.png', 'sha256': 'b5a10bd1ff75f45d9d070fbdc9f16dc4cec77d5e9261c2ce736e4858253a3799', 'sourceFrameIndex': 11280, 'pts': 2887680, 'timestampSeconds': 188.0, 'nearestAuthoredProgress': 0.56, 'observation': 'Support hand returns underneath; incoming cell silhouette partly concealed by wrist and edge.'}, {'path': '/private/tmp/w185-hollow-report/reference-11.png', 'sha256': '29064d725bb1cdc531a60146281bd83eba032a4020701a6e053586e03a7a935d', 'sourceFrameIndex': 11292, 'pts': 2890752, 'timestampSeconds': 188.2, 'nearestAuthoredProgress': 0.64, 'observation': 'Support palm contacts lower grip area; HUD1 becomes5, confirming whole reload with4 reserve.'}, {'path': '/private/tmp/w185-hollow-report/reference-12.png', 'sha256': '69a0c2aefd5d70eb45e5e045cff04fa03c484e4448e457af3f945ac92f5080e5', 'sourceFrameIndex': 11304, 'pts': 2893824, 'timestampSeconds': 188.4, 'nearestAuthoredProgress': 0.72, 'observation': 'Support hand opens/releases; weapon starts rotating down and toward hip.'}, {'path': '/private/tmp/w185-hollow-report/reference-13.png', 'sha256': '8bfafa2761dec07d7b77bc3a6ef03fede488c6aba066193cbdf93e7d17ed1cd2', 'sourceFrameIndex': 11312, 'pts': 2895872, 'timestampSeconds': 188.53333333333333, 'nearestAuthoredProgress': 0.78, 'observation': 'Carrier lowers quickly, support hand passes beneath body.'}, {'path': '/private/tmp/w185-hollow-report/reference-14.png', 'sha256': '858f5b158103228297d61a71fd1a48555a84b98a6a2012483b6b0cd65a90a32b', 'sourceFrameIndex': 11320, 'pts': 2897920, 'timestampSeconds': 188.66666666666666, 'nearestAuthoredProgress': 0.84, 'observation': 'Fast downward recovery with support fore-end reach.'}, {'path': '/private/tmp/w185-hollow-report/reference-15.png', 'sha256': '6f36b83d2de5b946c96a46dac0eb9aeae1bd60f833472df08006116466693955', 'sourceFrameIndex': 11332, 'pts': 2900992, 'timestampSeconds': 188.86666666666667, 'nearestAuthoredProgress': 0.92, 'observation': 'Hip presentation recovered with player view motion; no independent bolt stroke resolved.'}, {'path': '/private/tmp/w185-hollow-report/reference-16.png', 'sha256': '857aef29782d97979c25e02a3943f5d72262dda251485421d78ed6d32e0f5ed2', 'sourceFrameIndex': 11348, 'pts': 2905088, 'timestampSeconds': 189.13333333333333, 'nearestAuthoredProgress': 1, 'observation': 'Recovered weapon bobs with movement; canonical exact endpoint authored.'}]}

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
    # Reference n11244..11292: underside exchange, fixed open grip intact.
    # A single narrow insert follows the existing front-grip axis; hidden proportions authored.
    shaft=copy.deepcopy(source['elements'][53])
    shaft.update(name='magazine_shaft_upper', **{'from':[7.65,6.25,-.35],'to':[8.35,6.85,1.9]})
    shaft['rotation']=copy.deepcopy(source['elements'][43]['rotation'])
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
                model['elements']=[e for e in model['elements'] if e['name'].startswith(('grip','under_grip_cell','magazine','rear_guard'))]
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
    draw.text((14,12),'W185 HOLLOW WORDS | reference-led canonical JSON motion | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.55,-.7],[-1,.45,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,310),(col*400,70))
        draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.35,.55];groups=[posed(i) for i in (0,7,13,20)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,350)
    for col,(i,g) in enumerate(zip((0,7,13,20),groups)):
        sheet.paste(raster(g,cam,400,350,extent),(col*400,420))
        draw.text((col*400+10,396),f'p={i/20:.2f} / fixed camera + common scale',fill='white')
    draw.text((14,794),'97 active elements = 95 fixed canonical + cell53 + 1 narrow insert; endpoints =96. Fixed grip heel46 stays attached.',fill='white')
    details=[posed(i,detail=True) for i in (0,7,10,13)]
    detail_cam=[1,.25,.25]
    detail_extent=helper['frame'](np.concatenate([t[0] for group in details for t in group]),detail_cam,400,350)
    for col,(i,group) in enumerate(zip((0,7,10,13),details)):
        sheet.paste(raster(group,detail_cam,400,350,detail_extent),(col*400,855))
        draw.text((col*400+10,828),f'RIGID MAGAZINE DETAIL p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(7,grip=grip,hand=hand),[1,.35,-.5],400,410),(col*400,1270))
        draw.text((col*400+10,1244),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((14,1710),'Observed: right-edge lift -> underside cell withdraw -> low exchange -> return/seat -> wrist roll -> rapid lower. Numeric poses authored.',fill='white')
    draw.text((14,1740),'Reload-only insert uses original cell UV; grip heel/frame, brace and optic fixed. Exact0/1 dispatch canonical full graph.',fill='white')
    draw.text((14,1770),'Actual footage and hashes: SOURCE.md + manifest. Native screen, hand contact, audio and performance remain pending.',fill='white')
    story=Image.new('RGB',(1600,2520),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL HOLLOW WORDS: Ironworker Gaming / ozOSAOr5T4c / 2020-07-08 | independent authored normalized reload below',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225))
        x=j%4*400;y=55+j//4*605;story.paste(im,(x,y))
        draw.text((x+8,y+232),f"ACTUAL n={f['sourceFrameIndex']} / {f['timestampSeconds']:.5f}s",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.35,.55],400,295),(x,y+263))
        draw.text((x+8,y+567),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((14,2490),'OFFLINE / NO HANDS / NOT NATIVE. 60fps; exact retained source PNGs. Source HUD5 is reserve-limited; product capacity6 unchanged.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w185-hollow-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=96:raise ValueError('Canonical element drift')
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w185_hollow_words.py'),Path('scripts/qa/test_reload_w185_hollow_words.py'),Path('src/test/java/kim/biryeong/destiny/weapon/ReloadW185HollowTest.java'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W185',weapon='hollow_words',revision=1,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=96,bodyElements=95,movingElements=2,maxAssembledElements=97,endpointAssembledElements=96,elementLimit=1000,addedElements=1,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,
        geometryPolicy='All96 canonical geometry/576faces/rotations/UV/default paint preserved. Only under_grip_cell53 moves. Fixed grip_heel46 and entire brace remain on95-element carrier.',
        payloadPolicy='Canonical under_grip_cell plus one narrow hidden insert move as one rigid whole energy cell. One assembly proxies outgoing/incoming; constant scale, no ammunition or invented bolt.',
        sourceLimitation=dict(canonicalHiddenNeckAbsent=True,fullMagazineFidelityBlocked=False,exactOriginalShaftFidelityVerified=False,canonicalMovingNames=list(MAGAZINE_NAMES),canonicalMovingIndices=[53],resolution='Actual same-weapon underside exchange inspected; hand/frame conceal full insert. One small coherent reload-only insert follows fixed front-grip axis. Exact hidden shaft profile and hand clearance are authored/unverified.'),
        reloadOnlyGeometry=dict(elements=reload_shaft(source),count=1,sourceFrameIndex=11280,sourceTimestampSeconds=188.,coreDimensions=[.7,.6,2.25],uvPolicy='All six original cell53 face UV reused; no atlas changes.',rigidAnchor=list(MAGAZINE_ANCHOR),sourceAxisDegrees=-67.5149801),
        semanticGroups=dict(body=95,originalEnergyCell=1,reloadOnlyHiddenInsert=1,fixed=['grip_front_solid','grip_front_bevel','grip_inner_bevel','grip_heel','grip_lower_brace','grip_lower_inner_rail','rear_guard_strut','rear_guard_inner_edge']),
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineExtractionAxis=[0,-.9238795,-.3826834],hipEndpoints=[0,20],
        endpointPolicy='Exact0/1 and overshoot use full original item graph. Negative/nonFP/ADS/inspect preserve canonical. Children0/20 retain exact accepted displays; added insert lies inside original solids when seated.',
        normalizedPhases=dict(lift=[0,.18],reachWithdraw=[.18,.38],lowerExchange=[.38,.48],incoming=[.48,.58],seat=[.58,.64],wristRoll=[.64,.72],rapidLower=[.72,.88],recover=[.88,1]),
        reference=REFERENCE,
        referencePolicy='Actual Hollow Words inventory plus continuous same-weapon Ironworker Gaming n11204..11348; source PNG/MP4/metadata hashes and exact PTS. Inspected before authoring. HUD5 reflects1+4 reserve; preserve local capacity6.',
        authoredPolicy='Individually authored Hollow Words steep right-edge muzzle lift, lower-cell reach/withdraw/hidden exchange, palm seating, short inward wrist roll and fast lower. W184 matrices/guards/renderer only; no reused trajectory.',
        authoredHiddenDetails='Support hand and bottom edge conceal cell shaft and exchange. Added insert dimensions and exact path approximate occluded surfaces; no extracted bones/animation, independent bolt, thrown cell, support-hand geometry or IK.',
        timingPolicy='Unchanged local capacity6, reload50ticks, charge800ms/16ticks, burst7/sharedBurstAmmo=true, cadence13ticks and existing audio/ammo transfer.21 samples every2.5ticks; source perks/reserve do not set gameplay.',
        rotationConvention='JOML Rx Ry Rz; constant accepted uniform scale; native carrier transported into twohand; left ItemTransform applies F*T*F. Original axis/angle rotations remain exact.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration=dict(workerRuntimeEdited=False,masterOwnsRegistryRuntime=True,requiredMasterModel='destiny:'+KEY,catalogId='hollow_words',assetInputs='float[1] progress; boolean[0] grip; string[0] ads/inspect; master route/admission/lifecycle.'),
        nativeQueue=['Master route/admit hollow_words; preserve50tick/6round/800ms charge clock and audio/ammo.', 'Both FP hands/grips whole-cell clearance, support-hand fit, insert proportions and endpoint recovery.', 'ADS/inspect/negative/nonFP guards; cancellation/equip/switch/death/disconnect; partial/empty/no reserve.', 'Native pack load, audio listening and10-20 simultaneous display observation remain pending.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w185-hollow-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs;87 pack assets;95+2=97 active elements,96 canonical endpoints;native pending')
if __name__=='__main__':main()
