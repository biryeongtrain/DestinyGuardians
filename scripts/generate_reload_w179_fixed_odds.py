#!/usr/bin/env python3
"""W179 Fixed Odds FP reload. Canonical solids/UV/paint; authored cover + connected box/belt.
Only owned pack/art outputs. Shared runtime, admission and clocks belong to master.
Use bundled numpy/Pillow Python. --render needs retained actual frames in --evidence.
--verify regenerates JSON and verifies existing preview hashes without downloading media.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w179/fixed_odds')
KEY='weapon_reload_w179_fixed_odds/fixed_odds'
SOURCE=A/'models/weapon_surface_w123/fixed_odds.json'
TWOHAND=A/'models/weapon/machine_gun/fixed_odds_twohand.json'
ITEM=A/'items/weapon/fixed_odds.json'
TEXTURE=A/'textures/item/weapon/w123/fixed_odds.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.7,8.3)
HINGE=(8.,11.91,3.17)
COVER_NAMES=('feed_roof','rear_action','rear_cheek_inlay_-1','rear_cheek_inlay_1','rear_purple_pin_-1','rear_purple_pin_1','rear_sight_pedestal','rear_sight_base','rear_sight_arch_-1','rear_sight_arch_1')
BOLT_NAMES=('charging_shaft','charging_knob')
# p, carrier XYZ degrees, display translation, source-local box/belt translation,
# cover X degrees about forward hinge, charging handle source-local Z travel.
# Fixed Odds default panel: presentation -> open -> box/feed -> lay belt -> close -> charge.
# Hidden box clearance and all numeric values are authored, not recovered animation.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0),0,0),
 (.08,(-5,-9,-12),(-.1,-.35,.15),(0,0,0),0,0),
 (.20,(-9,-16,-24),(-.15,-.55,.25),(0,0,0),-103,0),
 (.28,(-9,-16,-24),(-.15,-.55,.25),(1.1,-.15,0),-103,0),
 (.40,(-9,-16,-24),(-.15,-.55,.25),(4.0,-3.2,.5),-103,0),
 (.48,(-9,-16,-24),(-.15,-.55,.25),(4.0,-3.2,.5),-103,0),
 (.60,(-8,-15,-23),(-.15,-.50,.25),(1.2,-.15,0),-103,0),
 (.68,(-8,-15,-23),(-.15,-.50,.25),(0,0,0),-103,0),
 (.74,(-8,-15,-23),(-.15,-.50,.25),(0,0,0),-103,0),
 (.82,(-5,-10,-15),(-.10,-.30,.15),(0,0,0),0,0),
 (.89,(13,-6,-9),(-.05,-.15,.10),(0,0,0),0,1.1),
 (.94,(16,-4,-5),(0,-.10,.05),(0,0,0),0,0),
 (1.,(0,0,0),(0,0,0),(0,0,0),0,0),
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/fixed_odds.json': '593ade9e46dae518f28588890ce6e5f8a6b343113b419515c5b47f608b431761', 'src/main/resources/assets/destiny/textures/item/weapon/w123/fixed_odds.png': 'a4f5a08c0e74e565f8174505e361b7409ad35e3129e00cd8d514411a0fdfd769', 'src/main/resources/assets/destiny/items/weapon/fixed_odds.json': '4c62589daf0642d5ea3147eb01c273e5d891f47b0028c1d92ac9c0e8d957c921', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/machine_gun/fixed_odds.json': 'dd60ee6cb61a0911bdd984b0d61fae42c326a4e79306f25584a76038baea84d7', 'src/main/resources/assets/destiny/models/weapon/machine_gun/fixed_odds_ads.json': '4f5af172642861e91ac3cee07266b6fb517140b099ddf79359e5b9baf5687339', 'src/main/resources/assets/destiny/models/weapon/machine_gun/fixed_odds_ads_twohand.json': 'a7313b1fb66a791066fbe86c0ac6b722251626d2eaba03cefc2f0453e30d1ca7', 'src/main/resources/assets/destiny/models/weapon/machine_gun/fixed_odds_inspect.json': 'b7567ff0086b1ef604d6b619daf1e95f94bb7301448a918d3cf48137090e065f', 'src/main/resources/assets/destiny/models/weapon/machine_gun/fixed_odds_inspect_twohand.json': '181b4b4733658aa985e89dbc6f6f86be2ac921d18916a74991ca863627362693', 'src/main/resources/assets/destiny/models/weapon/machine_gun/fixed_odds_twohand.json': '6ad4aec1b27e112be239c80b6beac81962448b582dca1bd30b6517e2e8ba2038'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=cy3DRqtgKC8', 'creator': 'Ultraclocked', 'title': 'Destiny 2 - Unseeing, to Be Shown - Weapon Ornament for Fixed Odds (Legendary Machine Gun)', 'fps': 60, 'frames': [{'path': '/private/tmp/w179-fixed-odds-report/reference-01.png', 'sha256': '397225e6b7c3672bd3662167f27d495c41864b0c1e288d410e68bf00a1cb6806', 'timestampSeconds': 0.5, 'sourceFrameIndex': 30, 'observation': 'Inventory title FIXED ODDS and gold/purple default weapon; identity frame.', 'nearestAuthoredProgress': 0, 'defaultPanel': 'identity full frame'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-02.png', 'sha256': '29231920165e9a6ed4930624c0270a1fa6be3732c0f54f9f54a2da58844cb145', 'timestampSeconds': 10.25, 'sourceFrameIndex': 615, 'observation': 'DEFAULT left: closed top cover, triangular sight, linked belt into side box.', 'nearestAuthoredProgress': 0, 'defaultPanel': 'left'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-03.png', 'sha256': '72b628a7b65790b3854f266668ccf13b40d461a355afbeaeb10be405176d6484', 'timestampSeconds': 10.75, 'sourceFrameIndex': 645, 'observation': 'DEFAULT left: receiver presentation begins, cover still closed.', 'nearestAuthoredProgress': 0.05, 'defaultPanel': 'left'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-04.png', 'sha256': 'a1df4e1db18707642f2a65d1ef0ad5cec64988389cda19a40922d147f97a4937', 'timestampSeconds': 11.5, 'sourceFrameIndex': 690, 'observation': 'DEFAULT left: cover raised about forward hinge, sight travels with cover; exposed feed tray.', 'nearestAuthoredProgress': 0.2, 'defaultPanel': 'left'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-05.png', 'sha256': 'd9e9d5453cbe7ac3435685ea603d89592dca0fc58759987cdf17af60beb1b751', 'timestampSeconds': 12.25, 'sourceFrameIndex': 735, 'observation': 'DEFAULT top: support hand holds box below exposed feed, cover remains raised; exact outgoing path occluded.', 'nearestAuthoredProgress': 0.35, 'defaultPanel': 'top'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-06.png', 'sha256': 'ac5fd7082383952bdf1257b203a6d9789d0cd6372de2e53fb63b49c43e059579', 'timestampSeconds': 12.75, 'sourceFrameIndex': 765, 'observation': 'DEFAULT top: support hand returns toward exposed feed area; payload partly hidden.', 'nearestAuthoredProgress': 0.5, 'defaultPanel': 'top'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-07.png', 'sha256': 'b73b604835b798438ad4eaa00cc50ef0e915dea6fab9730ca32bb9efad856bc9', 'timestampSeconds': 13.25, 'sourceFrameIndex': 795, 'observation': 'DEFAULT top: hand places connected belt at feed tray, descending linked rounds visible.', 'nearestAuthoredProgress': 0.62, 'defaultPanel': 'top'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-08.png', 'sha256': '50cdfa54b0ddfd22e6cc401cab4c41536ce7994c3cfcd644e058ba742d278692', 'timestampSeconds': 13.75, 'sourceFrameIndex': 825, 'observation': 'DEFAULT top: palm presses over belt/feed area under raised cover.', 'nearestAuthoredProgress': 0.68, 'defaultPanel': 'top'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-09.png', 'sha256': '3e753dfad6ed33357c74d806e1de5facd956edf93f207840313be7bd5e60c1dd', 'timestampSeconds': 14.25, 'sourceFrameIndex': 855, 'observation': 'DEFAULT top: cover now closed; support hand near receiver.', 'nearestAuthoredProgress': 0.8, 'defaultPanel': 'top'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-10.png', 'sha256': 'ccd95a57d1cfdb83b9e228e3533f5a525acffd6a4c8fdfd371ddd85fa374fd13', 'timestampSeconds': 14.75, 'sourceFrameIndex': 885, 'observation': 'DEFAULT top: closed receiver raised toward charging/settling hand action; exact handle travel partly obscured.', 'nearestAuthoredProgress': 0.86, 'defaultPanel': 'top'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-11.png', 'sha256': '7f3df400b263bea6391022dc41029aaaa144891bc4aa651f94a9ec16cc732a05', 'timestampSeconds': 15.25, 'sourceFrameIndex': 915, 'observation': 'DEFAULT top: charging/settling hand action with muzzle raised; exact latch travel obscured.', 'nearestAuthoredProgress': 0.92, 'defaultPanel': 'top'}, {'path': '/private/tmp/w179-fixed-odds-report/reference-12.png', 'sha256': 'd4a80bec23723996b62b0b0ece52fb1222a9254750d3cd8c8628c2b05a601c9c', 'timestampSeconds': 16.0, 'sourceFrameIndex': 960, 'observation': 'DEFAULT left: ready hip view restored, belt and box assembled.', 'nearestAuthoredProgress': 1, 'defaultPanel': 'left'}], 'sourceVideoSha256': '080a6e24152b29927bc6f3d2041ef49c526c1fda9e9a4eb89ed24f6ec36eeb4f', 'sourceMetadataSha256': '9afe0e33953155eaf44196ef6f4d97dda5d6e7b7da1eb4fb7a8b2adcbfc93d28'}

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
            return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in (1,2,3)) + tuple(a[k]+(b[k]-a[k])*t for k in (4,5))
    raise ValueError(p)



def is_payload(e):
    return e['name'].startswith(('ammo_box_','belt_','feed_join_'))


def partition(source):
    parts={}
    for part in PARTS:
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for e in source['elements'] if is_payload(e)==(part=='magazine')]
        parts[part]=model
    return parts


def articulated_elements(elements,p):
    """Rigid canonical cover assembly and handle. No new faces, cubes, UV or scale.
    Element rotations use Rz Ry Rx; display transforms below use JOML Rx Ry Rz.
    Non-moving elements and both endpoint assemblies retain exact original records.
    """
    _,_,_,cover,bolt=sample(p)
    result=copy.deepcopy(elements)
    for e in result:
        if e['name'] in COVER_NAMES and cover:
            turn=xyz((cover,0,0));center=[(a+b)/2 for a,b in zip(e['from'],e['to'])]
            old=e.get('rotation',{});origin=old.get('origin',center)
            old_angles=[old.get(axis,0) for axis in 'xyz']
            old_r=transpose(xyz([-v for v in old_angles]))
            actual_center=add(origin,vec(old_r,sub(center,origin)))
            new_center=add(HINGE,vec(turn,sub(actual_center,HINGE)))
            delta=sub(new_center,center)
            e['from']=add(e['from'],delta);e['to']=add(e['to'],delta)
            angles=[-v for v in euler(transpose(mul(turn,old_r)))]
            e['rotation']=dict(origin=new_center,**dict(zip('xyz',angles)))
        if e['name'] in BOLT_NAMES and bolt:
            e['from'][2]+=bolt;e['to'][2]+=bolt
            if 'rotation' in e:e['rotation']['origin'][2]+=bolt
    return result


def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset,_,_=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8))
    # Box, all rounds, links and connectors share exactly one rigid local transform.
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
    # Reuse only CPU raster/UV utility; no Hammerhead footage or motion is used.
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    def rotation(a):
        x,y,z=np.radians(a)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i,parts=PARTS,grip='native',hand=FP[0],detail=False):
        triangles=[]
        for part in parts:
            model=json.loads(output[A/f'models/{KEY}_{part}.json'])
            child=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])
            if 'elements' in child:model['elements']=child['elements']
            if detail:model['elements']=[e for e in model['elements'] if is_payload(e) or e['name'] in COVER_NAMES or e['name'].startswith('feed_')]
            d=child['display'][hand];rr=rotation(d['rotation']);ss=np.array(d['scale']);tt=np.array(d['translation'])
            for pts,uv,tex,normal in helper['model_triangles']({'part':model},texture):
                triangles.append(((np.asarray(pts)-8)*ss@rr.T+tt,uv,tex,rr@normal))
        return triangles
    def raster(ts,cam,w,h,extent=None):
        if extent is None:extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    sheet=Image.new('RGB',(1600,1800),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,12),'W179 FIXED ODDS | emitted cuboids + display reconstructed | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    cams=([1,.45,-.55],[-1,.3,.6],[.3,.5,1])
    for row,cam in enumerate(cams):
        groups=[posed(i) for i in (0,8,14,20)]
        extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,280)
        for col,(i,g) in enumerate(zip((0,8,14,20),groups)):
            sheet.paste(raster(g,cam,400,280,extent),(col*400,55+row*315))
            draw.text((col*400+10,35+row*315),f'p={i/20:.2f} / common framing',fill='white')
    draw.text((12,1010),'153 existing cubes = 114 body (10 cover + 2 handle) + 39 box/belt. No triangle adapter output or added solids.',fill='white')
    for col,i in enumerate((0,4,8,14)):
        sheet.paste(raster(posed(i,detail=True),[1,.65,.5],400,330),(col*400,1060))
        draw.text((col*400+10,1038),f'FEED DETAIL p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(10,grip=grip,hand=hand),[1,.35,-.5],400,300),(col*400,1450))
        draw.text((col*400+10,1420),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((12,1770),'Canonical endpoints; box + complete linked belt travel together; cover opens before extraction and closes after feed seating.',fill='white')
    story=Image.new('RGB',(1600,1900),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL Fixed Odds DEFAULT panels only | cy3DRqtgKC8 | authored emitted asset below | OFFLINE, NO HAND IK',fill='white')
    for i,f in enumerate(REFERENCE['frames']):
        p=evidence/Path(f['path']).name
        if sha(p.read_bytes())!=f['sha256']:raise ValueError('Reference hash drift: '+str(p))
        im=Image.open(p).convert('RGB')
        panel=f['defaultPanel']
        if panel=='left':im=im.crop((0,0,640,720))
        elif panel=='top':im=im.crop((0,0,1280,360))
        im.thumbnail((400,245))
        x=i%4*400;y=50+i//4*600
        story.paste(im,(x+(400-im.width)//2,y+(245-im.height)//2))
        draw.text((x+8,y+250),f"ACTUAL {f['timestampSeconds']:.2f}s / DEFAULT {panel}",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.45,.6],400,280),(x,y+280))
        draw.text((x+8,y+565),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((12,1872),'Exact pivots, angles, hidden box clearance and phase normalization authored. Original raw 1280x720 frames retained outside product.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w179-fixed-odds-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=153:raise ValueError('Canonical element drift')
    parts=partition(source);output={}
    def emit(p,v):output[p]=encode(v)
    for part,model in parts.items():emit(A/f'models/{KEY}_{part}.json',model)
    entries=[]
    for i in range(21):
        p=i/20
        for part in PARTS:
            elements=articulated_elements(parts['body']['elements'],p) if part=='body' else None
            for grip in GRIPS:
                child=dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],two,p,part,grip))
                if part=='body' and elements!=parts['body']['elements']:child['elements']=elements
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',child)
        def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in PARTS])
        entries.append(dict(threshold=p,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    reload=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model']))
    guard=copy.deepcopy(item['model']);guard['fallback']=reload
    wrapper=copy.deepcopy(item);wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=guard)],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    if render:
        output[ART/'comparison.png'],output[ART/'storyboard.png']=previews(output,evidence)
    else:
        # Media can be absent from a checkout: core asset regeneration needs no downloads.
        manifest=json.loads((ROOT/ART/'manifest.json').read_bytes())
        for name in ('comparison.png','storyboard.png'):
            path=ART/name;data=(ROOT/path).read_bytes()
            if sha(data)!=manifest['sha256'][str(path)]:raise ValueError('Preview drift: '+str(path))
            output[path]=data
    indices={part:[i for i,e in enumerate(source['elements']) if is_payload(e)==(part=='magazine')] for part in PARTS}
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w179_fixed_odds.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W179',weapon='fixed_odds',revision=1,itemModel='destiny:'+KEY,ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),sourceElements=153,bodyElements=114,movingElements=39,coverElements=10,chargingHandleElements=2,maxAssembledElements=153,elementLimit=1000,addedElements=0,triangleAdapterElements=0,
      sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,coverNames=COVER_NAMES,chargingHandleNames=BOLT_NAMES,
      geometryPolicy='Canonical parent partition is exact. Ten original cover solids articulate together in body child overrides; two original handle solids translate after closure. Every face, UV, texture and cube dimension is preserved. Endpoint geometry/display exact.',
      payloadPolicy='Five box walls/bottom + seven rounds with case/shoulder/tip/link + six feed connectors share one rigid transform. No isolated rounds, belt scaling or detached connector. Belt tail stays in box; lead reconnects to feed before cover closes.',
      authoredHiddenDetails='Exact hinge, grip pivot, cover membership, hidden box departure/replacement clearance, numerical timing and charging handle travel are authored. Hands occlude parts of source. Same asset represents outgoing and incoming box; no duplication or shrink-to-hide.',
      keyframes=KEYS,gripPivot=GRIP,coverHinge=HINGE,hipEndpoints=[0,20],endpointPolicy='Exact accepted displays for both parts, both FP hands and both grips. Non-FP and ADS/inspect graph fallback exactly canonical.',
      normalizedPhases={'present':[0,.08],'openCover':[.08,.20],'boxAndConnectedBeltOut':[.20,.40],'holdClear':[.40,.48],'returnBoxLayBelt':[.48,.68],'pressFeed':[.68,.74],'closeCover':[.74,.82],'chargeAndRelease':[.82,.94],'recover':[.94,1]},
      reference=REFERENCE,referencePolicy='Use labeled DEFAULT panel only. Ornament appearance and unrelated Hammerhead footage are not Fixed Odds evidence. Raw exact frames, source video and metadata retained outside product.',
      motionAuthorship='Fixed Odds top-cover/feed handling with modest muzzle dip and roll to expose box, cover-first opening, rigid box/belt clearance, feed seating, cover closure and short charging action. All numeric animation keys authored. W178 rigid matrix convention reused only.',
      timingPolicy='Normalized visual progression only. Existing magazine44/reload106ticks/cadence3.333333333333ticks/burst1 and all audio/data remain unchanged.',
      rotationConvention='Element Rz Ry Rx; display JOML Rx Ry Rz. Equal-scale grip carriers; left reflection is applied by Minecraft ItemTransform. No arbitrary element rotation schema.',
      nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
      integration={'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'fixed_odds','assetInputs':'float1 normalized progress; boolean0 existing twohand grip; negative inactive fallback. Master owns admission, route, lifecycle, clocks and native session.'},
      nativeQueue=['Both FP contexts and grips: cover opening/frame, attached box/belt clearance and feed seating, closure, charge, exact endpoints.','ADS/inspect and non-FP fallback; completion, cancel, swap, equip/unequip, death/disconnect cleanup.','Existing sound and brief 10-20 displays: master-only, unverified by worker.'],
      canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact 90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w179-fixed-odds-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w179-manifest.json').read_bytes())['features'] if f['name']=='w179-fixed-odds'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic core outputs/media hashes; 87 pack assets; 114+39=153 assembled elements; native pending')
if __name__=='__main__':main()
