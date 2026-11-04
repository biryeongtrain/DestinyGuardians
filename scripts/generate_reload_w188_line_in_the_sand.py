#!/usr/bin/env python3
"""W188 Line in the Sand underside battery exchange; independent same-weapon footage.
W185/W187 matrix/graph/raster infrastructure only. --verify is stdlib/media-free.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w188/line_in_the_sand')
KEY='weapon_reload_w188_line_in_the_sand/line_in_the_sand'
SOURCE=A/'models/weapon_surface_w123/line_in_the_sand.json'
TWOHAND=A/'models/weapon/linear_fusion_rifle/line_in_the_sand_twohand.json'
ITEM=A/'items/weapon/line_in_the_sand.json'
TEXTURE=A/'textures/item/weapon/w123/line_in_the_sand.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.2,8.2)
MAGAZINE_ANCHOR=(8.,5.6,6.83)
BATTERY_INDICES=tuple(range(56,64))
# Independently framed n3365..3417. Common FP shift retains the lower seat.
KEYS=(
 (0,(0,0,0),(0,0,0),(0,0,0)),
 (.10,(50,-5,-10),(-1.1,-1.0,-2.1),(0,0,0)),
 (.20,(70,-9,-15),(-1.8,-2.7,-3.8),(0,-.35,0)),
 (.30,(74,-10,-16),(-1.9,-3.1,-4.3),(0,-2.0,0)),
 (.38,(73,-9,-16),(-1.9,-3.1,-4.3),(-.45,-4.6,.1)),
 (.48,(73,-9,-15),(-1.9,-3.1,-4.3),(-1.0,-6.4,.2)),
 (.60,(70,-8,-15),(-1.8,-3.0,-4.1),(-2.1,-4.8,.3)),
 (.68,(66,-7,-14),(-1.6,-2.8,-3.8),(-.5,-2.6,0)),
 (.76,(65,-7,-13),(-1.5,-2.6,-3.7),(0,-.25,0)),
 (.80,(63,-6,-12),(-1.5,-2.5,-3.5),(0,.10,0)),
 (.84,(58,-5,-10),(-1.3,-2.2,-3.2),(0,0,0)),
 (.92,(24,-2,-4),(-.5,-.8,-1.2),(0,0,0)),
 (1,(0,0,0),(0,0,0),(0,0,0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/line_in_the_sand.json': 'b5a5319fdacf4f759fb5b682c8d4c6ffbb83cc7e5c992fee6f5a70345f385eff', 'src/main/resources/assets/destiny/textures/item/weapon/w123/line_in_the_sand.png': '3d23d635215fbb69c8ddd4ce1b27f58a36869013932bcc85f40d958bcece81f3', 'src/main/resources/assets/destiny/items/weapon/line_in_the_sand.json': '554a5be4af5bd63e0c31e2b7784ce33225c62ff59cf7ba550cc172653731550f', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand.json': 'b77783d88d521fa77e58269f38c86a073fd7953c00b55425cb133750c3bcf09b', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_twohand.json': '7697a6a142002b2b8a33e4bf419393a708f513be8daa7f6bbaf981bbfbf09a62', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_inspect_twohand.json': 'c6d824bb4218e3a92b489801bb50ccefbfd2f01992c53fa78be9590a5cab52ac', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_ads.json': '6a461b6a4bfe86234504b23b392234cebefa840a9663c079fdd442744312de9d', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_inspect.json': '8da76eca201833d6cb31b0f67191a1628b89502d052ba782a02f251b1301223f', 'src/main/resources/assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand_ads_twohand.json': 'cbfec2400ef8f7385608f9f57daf59f42952468f9d047d65c7f2d53cceb5cad9'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=hu_LOERnF6o', 'title': 'Destiny 2: LINE IN THE SAND IS BACK! PVE REVIEW!', 'creator': 'Plasma Alchemist', 'uploadDate': '20240705', 'fpsNumerator': 25, 'fpsDenominator': 1, 'sourceTimebase': '1/12800', 'actionFrameRange': [3365, 3417], 'actionSeconds': [134.6, 136.68], 'sourceVideoFile': '/private/tmp/w188-line-report/review.mp4', 'sourceMetadataFile': '/private/tmp/w188-line-report/review.info.json', 'sourceVideoSha256': '19385be4715c0eeeca0af1808cf1fcf86ce929105410a340bd033a3f6f47bbac', 'sourceMetadataSha256': 'a597f726bd01a51735917882b3589aba81cf286e5e9a2a20027bbee531923b6d', 'inspectedActualFrames': True, 'shaderPolicy': 'Source mint paint demonstrates mechanism only. Existing silver/gold/black W150 canonical atlas unchanged.', 'frames': [{'path': '/private/tmp/w188-line-report/reference-250.png', 'sha256': 'e75003f777e7c07a2074dba9e2fcdfedeb2829fb2a460f1e8d06d46ca276d5fa', 'sourceFrameIndex': 250, 'pts': 128000, 'timestampSeconds': 10.0, 'nearestAuthoredProgress': 0, 'observation': 'Inventory explicitly LINE IN THE SAND; matching open fork, gold coils, lower battery; source mint shader not copied.'}, {'path': '/private/tmp/w188-line-report/reference-3365.png', 'sha256': '4a94b25035aff5afe4d65c5cc3b6e2765ab8057de4dd54c657a81d83b3790ac6', 'sourceFrameIndex': 3365, 'pts': 1722880, 'timestampSeconds': 134.6, 'nearestAuthoredProgress': 0.0, 'observation': 'Final shot/ADS exit; authored start returns to canonical hip instead of importing ADS.'}, {'path': '/private/tmp/w188-line-report/reference-3370.png', 'sha256': 'c38953c2c555a6375650c73c03a1aa640d22e60ea62fcff0422bf532e38d4ef4', 'sourceFrameIndex': 3370, 'pts': 1725440, 'timestampSeconds': 134.8, 'nearestAuthoredProgress': 0.096154, 'observation': 'Rifle rises muzzle-up at screen right; support hand reaches lower battery.'}, {'path': '/private/tmp/w188-line-report/reference-3375.png', 'sha256': '2bc07c379cbfdf369d02a6f91d96fc627952509b08ef1491c9c426ebf687d07e', 'sourceFrameIndex': 3375, 'pts': 1728000, 'timestampSeconds': 135.0, 'nearestAuthoredProgress': 0.192308, 'observation': 'Support hand grips complete lower battery beneath fixed receiver.'}, {'path': '/private/tmp/w188-line-report/reference-3380.png', 'sha256': '17025f39e5372fd7a2e07eb9bd87c9c6fdae63e481e43935a57a5a11938cad33', 'sourceFrameIndex': 3380, 'pts': 1730560, 'timestampSeconds': 135.2, 'nearestAuthoredProgress': 0.288462, 'observation': 'Downward withdrawal exposes paired narrow metallic guide/contact stems; fixed coils stay with rifle.'}, {'path': '/private/tmp/w188-line-report/reference-3385.png', 'sha256': 'a20dca19112e101a1a44486bb6717393d3398804e9190fc67be90bc26a1f93dd', 'sourceFrameIndex': 3385, 'pts': 1733120, 'timestampSeconds': 135.4, 'nearestAuthoredProgress': 0.384615, 'observation': 'Lower battery clears its seat; rifle remains steep with open lower gap.'}, {'path': '/private/tmp/w188-line-report/reference-3390.png', 'sha256': '139f01f4d4d6ec49915f381a77c9760b63df58705a4503ae323a4d8f264376c5', 'sourceFrameIndex': 3390, 'pts': 1735680, 'timestampSeconds': 135.6, 'nearestAuthoredProgress': 0.480769, 'observation': 'Outgoing battery/hand moves below frame; stationary weapon still held upright.'}, {'path': '/private/tmp/w188-line-report/reference-3395.png', 'sha256': 'dbb99f88a3082860f0918c53dbf48a0cf145cc8a325a8f9269a3a34adc4fb2ca', 'sourceFrameIndex': 3395, 'pts': 1738240, 'timestampSeconds': 135.8, 'nearestAuthoredProgress': 0.576923, 'observation': 'Exchange dwell; receiver, coils, sight and grip remain fixed together.'}, {'path': '/private/tmp/w188-line-report/reference-3400.png', 'sha256': 'cade7bb6a36708709289b97f356f9f40c128ce654789fa2be7e907ad005e3f02', 'sourceFrameIndex': 3400, 'pts': 1740800, 'timestampSeconds': 136.0, 'nearestAuthoredProgress': 0.673077, 'observation': 'Rifle begins shallow relaxation while replacement is still below frame.'}, {'path': '/private/tmp/w188-line-report/reference-3403.png', 'sha256': '9aed002458403484834b6b6875458912b364686b8d02aa9e385dac4e56052ba0', 'sourceFrameIndex': 3403, 'pts': 1742336, 'timestampSeconds': 136.12, 'nearestAuthoredProgress': 0.730769, 'observation': 'Incoming support hand begins entering from below-left.'}, {'path': '/private/tmp/w188-line-report/reference-3405.png', 'sha256': '7a1ebe787e03c712e05a37bb30021ed1ab3f93d2b43ba4b2edca937a7e96118f', 'sourceFrameIndex': 3405, 'pts': 1743360, 'timestampSeconds': 136.2, 'nearestAuthoredProgress': 0.769231, 'observation': 'Complete incoming lower battery visible below-left; aligns beneath lower opening.'}, {'path': '/private/tmp/w188-line-report/reference-3408.png', 'sha256': '8c51a0745d768fd7eed7dd922385b60d5e37c29f86ef5aedd183a5aa25e8f589', 'sourceFrameIndex': 3408, 'pts': 1744896, 'timestampSeconds': 136.32, 'nearestAuthoredProgress': 0.826923, 'observation': 'Support hand raises battery along underside insertion direction.'}, {'path': '/private/tmp/w188-line-report/reference-3410.png', 'sha256': '494f9dd1df0b67d7aeeb32cbd9bcd91ec2207d0aa24de998cc86b50270c85314', 'sourceFrameIndex': 3410, 'pts': 1745920, 'timestampSeconds': 136.4, 'nearestAuthoredProgress': 0.865385, 'observation': 'Battery seats upward; HUD refills to9 due to source perks, not local capacity.'}, {'path': '/private/tmp/w188-line-report/reference-3412.png', 'sha256': '29417ee32f65db2945f9335eeb201effc30ad579061e4f8677e7794d44ffce2a', 'sourceFrameIndex': 3412, 'pts': 1746944, 'timestampSeconds': 136.48, 'nearestAuthoredProgress': 0.903846, 'observation': 'Palm finishes seating; steep rifle pose begins lowering.'}, {'path': '/private/tmp/w188-line-report/reference-3415.png', 'sha256': 'b2436ff3c8c920cfef6930f782e2d91c5f571d61c56fd9a3a5968417e398cbee', 'sourceFrameIndex': 3415, 'pts': 1748480, 'timestampSeconds': 136.6, 'nearestAuthoredProgress': 0.961538, 'observation': 'Rapid rifle lowering follows completed seating; subsequent weapon swap is not part of reload.'}, {'path': '/private/tmp/w188-line-report/reference-3417.png', 'sha256': '2de96fc9723d5039f4353e6202850a2db6723cb7c1450cb6c67e8601f5006fd4', 'sourceFrameIndex': 3417, 'pts': 1749504, 'timestampSeconds': 136.68, 'nearestAuthoredProgress': 1.0, 'observation': 'Recovery boundary before weapon-switch footage; canonical authored hip endpoint.'}]}

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

def payload_visible(i):return i<=7 or i>=12

def contacts(source):
    # Source Battery maxY6.194; contact profile/hidden seating are authored.
    result=[]
    for side,x in enumerate((7.65,8.14)):
        e=copy.deepcopy(source['elements'][57]);e.update(name=f'Reload_battery_contact_{side}',**{'from':[x,5.88,4.18],'to':[x+.21,6.17,4.50]});e.pop('rotation',None);result.append(e)
    return result

def partition(source):
    models={part:copy.deepcopy(source) for part in PARTS}
    models['body']['elements']=[copy.deepcopy(e) for i,e in enumerate(source['elements']) if i not in BATTERY_INDICES]
    models['magazine']['elements']=[copy.deepcopy(source['elements'][i]) for i in BATTERY_INDICES]+contacts(source)
    return models

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
            if part=='magazine' and not canonical and not payload_visible(i):continue
            if payload_only and part!='magazine':continue
            model=json.loads(output[A/f'models/{KEY}_{part}.json'])
            if canonical:model['elements']=[e for e in model['elements'] if not e.get('name','').startswith('Reload_')]
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
    cam=[1,.25,.4];groups=[posed(i) for i in range(21)]
    extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,310)
    panels=[raster(g,cam,400,310,extent) for g in groups]
    sheet=Image.new('RGB',(1600,1840),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((14,12),'LINE IN THE SAND W188 | OFFLINE / NO HANDS / NOT NATIVE | emitted JSON and display transforms',fill='white')
    for col,camera in enumerate(([1,0,0],[1,.4,-.5],[-1,.35,.6],[.25,.5,1])):
        sheet.paste(raster(posed(0,canonical=True),camera,400,300),(col*400,70));draw.text((col*400+10,46),'CANONICAL '+('side','front oblique','reverse oblique','rear')[col],fill='white')
    for row,indices in enumerate(((4,6,9,12),(13,15,17,20))):
        for col,i in enumerate(indices):
            y=420+row*360;sheet.paste(panels[i],(col*400,y));draw.text((col*400+10,y-24),f'p={i/20:.2f} / fixed camera + shared extent',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(13,grip,hand),cam,400,320),(col*400,1150));draw.text((col*400+10,1126),grip+' / '+hand.replace('firstperson_',''),fill='white')
    sheet.paste(raster(posed(6,payload_only=True),[1,.4,.5],460,240),(10,1530))
    raw=runpy.run_path(str(ROOT/'scripts/generate_surface_w150_master.py'))
    ms,_,_,_,_=raw['source_meshes']('line_in_the_sand');battery=next(m for m in ms if m['name']=='Battery')
    neutral=np.array([[[155.,165.,175.,255.]]]);rawts=[]
    for face in battery['faces']:
        ps=battery['vertices'][face];normal=np.cross(ps[1]-ps[0],ps[2]-ps[0]);norm=np.linalg.norm(normal)
        if norm:rawts.append((ps,np.zeros((3,2)),neutral,normal/norm))
    sheet.paste(raster(rawts,[1,.4,.5],460,240),(510,1530));draw.text((14,1500),'EMITTED complete battery +2 contacts',fill='white');draw.text((520,1500),'RAW Battery /2154 triangles /neutral',fill='white')
    draw.text((990,1550),'71 fixed +8 canonical battery +2 contacts =81 max',fill='white')
    draw.text((990,1580),'79 canonical endpoints;474 unchanged face UVs',fill='white')
    draw.text((990,1610),'Source mint shader and perk capacity9 not copied',fill='white')
    draw.text((990,1640),'Local capacity5 /49ticks /audio unchanged',fill='white')
    draw.text((14,1790),'Orthographic offline views; source and authored cameras differ. Native framing/hand contact/audio/performance pending master.',fill='white')
    story=Image.new('RGB',(1600,2480),'#111925');draw=ImageDraw.Draw(story)
    draw.text((14,12),'ACTUAL Line in the Sand / Plasma Alchemist /hu_LOERnF6o | emitted authored output underneath',fill='white')
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225));x=j%4*400;y=55+j//4*595;story.paste(im,(x,y))
        draw.text((x+8,y+231),f"ACTUAL n={f['sourceFrameIndex']} PTS={f['pts']} t={f['timestampSeconds']:.2f}",fill='white')
        i=round(f['nearestAuthoredProgress']*20);story.paste(panels[i],(x,y+260));draw.text((x+8,y+573),f'AUTHORED p={i/20:.2f} / fixed extent',fill='white')
    draw.text((14,2450),'OFFLINE / NO HANDS / NOT NATIVE.16 unaltered source PNGs,25fps,1/12800 timebase. Authored endpoints restore hip, not ADS/swap.',fill='white')
    return png(sheet),png(story)

def generate(render=False,evidence=Path('/private/tmp/w188-line-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=79:raise ValueError('Canonical element drift')
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w188_line_in_the_sand.py'),Path('scripts/qa/test_reload_w188_line_in_the_sand.py'),Path('src/test/java/kim/biryeong/destiny/weapon/ReloadW188LineTest.java'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W188',weapon='line_in_the_sand',revision=1,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=79,bodyElements=71,movingElements=10,maxAssembledElements=81,endpointAssembledElements=79,elementLimit=1000,addedElements=2,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=dict(body=[i for i in range(79) if i not in BATTERY_INDICES],magazine=list(BATTERY_INDICES)),
        geometryPolicy='All79 canonical elements/474faces/rotations/UV/default paint unchanged across71fixed +8battery. No receiver/coil/fork/sight impersonates ammunition.',
        payloadPolicy='Whole8-element lower battery plus2 small connected metallic contacts. Constant rigid scale; absent during below-frame exchange samples8..11.',
        sourceLimitation=dict(fullPayloadSourceFidelityVerified=False,resolution='Same-weapon battery removal/replacement and narrow metallic stems observed. Absolute pose, hidden seating/contact profile and native hand fit authored/unverified.'),
        reloadOnlyGeometry=dict(elements=contacts(source),count=2,visibleSampleIndices=[i for i in range(21) if payload_visible(i)],uvPolicy='Unchanged silver battery-floor UV for metallic contacts.'),
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,magazineExtractionAxis=[0,-1,0],hipEndpoints=[0,20],
        endpointPolicy='Exact0/1 and overshoot full original graph; negative/nonFP/ADS/inspect canonical; child0/20 accepted displays.',
        normalizedPhases=dict(rise=[0,.20],withdraw=[.20,.38],belowFrameExchange=[.38,.60],incoming=[.60,.68],upwardSeat=[.68,.80],release=[.80,.84],lower=[.84,1]),
        reference=REFERENCE,referencePolicy='Same weapon inventory plus continuous n3365..3417,25fps.16 exact source PNGs, hashes and PTS. No W185/W187 motion copied.',
        authoredPolicy='Independent steep rise, underside withdrawal, below-frame exchange, below-left incoming, upward seat/compression, palm release and lowering. Common FP shift keeps seat near held area.',
        authoredHiddenDetails='Numeric pivot/rotation/displacement/contact profile; source mint shader not copied. No imported bones/animation/hands/bolt/coil motion.',
        timingPolicy='Capacity5,reload49ticks,charge11ticks,cadence19ticks,burst1/sharedBurstAmmo=true,no shell reload/audio change.21 normalized samples at2.45tick spacing. Source perk capacity9 not copied.',
        rotationConvention='JOML Rx Ry Rz; accepted uniform scales; native motion transported into twohand; left ItemTransform F*T*F.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration=dict(workerRuntimeEdited=False,masterOwnsRegistryRuntime=True,requiredMasterModel='destiny:'+KEY,catalogId='line_in_the_sand',assetInputs='float[1]progress;boolean[0]grip;string[0]ads/inspect',capacity=5,reloadTicks=49),
        nativeQueue=['Both grips/FP hands: socket/exchange on-screen, support-hand/contact fit, endpoints.', 'Negative/nonFP/ADS/inspect; partial/empty/no-reserve/cancel/switch/equip/death/disconnect via master route.', 'Native pack load/audio listening/10-20display observation pending master.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Expected exact90 paths')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w188-line-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs;87 pack assets;71+10=81 active max,79 canonical endpoints;native pending')
if __name__=='__main__':main()
