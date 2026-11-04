#!/usr/bin/env python3
"""W181 Retrofit Escapade FP reload. Canonical solids/UV/paint; authored cover/optic + connected drum/belt.
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
ART=Path('art/weapons/w181/retrofit_escapade')
KEY='weapon_reload_w181_retrofit_escapade/retrofit_escapade'
SOURCE=A/'models/weapon_surface_w123/retrofit_escapade.json'
TWOHAND=A/'models/weapon/machine_gun/retrofit_escapade_twohand.json'
ITEM=A/'items/weapon/retrofit_escapade.json'
TEXTURE=A/'textures/item/weapon/w123/retrofit_escapade.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.54,8.49)
HINGE=(8.,12.4,-.1)
COVER_NAMES=('receiver_upper_rail', 'receiver_rear_shoulder', 'optic_saddle', 'optic_hood_0', 'optic_hood_1', 'optic_hood_2', 'optic_hood_3', 'optic_hood_4', 'optic_hood_5', 'optic_hood_6', 'optic_hood_7', 'objective_lens', 'ocular_lens', 'ocular_rim_0', 'ocular_rim_1', 'ocular_rim_2', 'ocular_rim_3', 'ocular_rim_4', 'ocular_rim_5', 'ocular_rim_6', 'ocular_rim_7', 'optic_loop_ear_-1', 'optic_loop_ear_1', 'optic_loop_top')
BOLT_NAMES=('charging_handle',)
# p, carrier XYZ degrees, display translation, complete drum/belt local translation,
# cover X angle, charging lug local Z displacement. Numerical keys are authored.
# Retrofit footage: cover with optic -> feed exchange -> lay belt -> close -> side action.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0),0,0),
 (.08,(-6,8,10),(-.15,-.25,.10),(0,0,0),0,0),
 (.18,(-9,13,19),(-.25,-.45,.20),(0,0,0),-96,0),
 (.26,(-9,13,19),(-.25,-.45,.20),(-3.4,-3.8,.3),-96,0),
 (.30,(-9,13,19),(-.25,-.45,.20),(-3.4,-3.8,.3),-96,0),
 (.42,(-9,13,19),(-.25,-.45,.20),(-1.0,-.7,.1),-96,0),
 (.50,(-9,13,19),(-.25,-.45,.20),(0,0,0),-96,0),
 (.58,(-8,12,18),(-.20,-.40,.20),(0,0,0),-96,0),
 (.66,(-6,9,12),(-.15,-.25,.15),(0,0,0),0,0),
 (.80,(17,5,7),(-.10,-.15,.10),(0,0,0),0,1.05),
 (.88,(18,4,5),(-.05,-.10,.05),(0,0,0),0,0),
 (1.,(0,0,0),(0,0,0),(0,0,0),0,0),
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/retrofit_escapade.json': 'd7cc409964d15f6e7ed52298d944fb468c3d47e1f1c5f70ee9981977cbe0daba', 'src/main/resources/assets/destiny/textures/item/weapon/w123/retrofit_escapade.png': 'cb6c3cc93635c979139c5b7eb30125577d8a680c1c4df5acb0a65c4f39e517aa', 'src/main/resources/assets/destiny/items/weapon/retrofit_escapade.json': '4dfa252864e0972e7dbbf0f7e3507e9a6676604360146ec5e8d1b19aea16e3d5', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/machine_gun/retrofit_escapade_twohand.json': '5e18e97eca8acf40343bb45358667f65b442a8cdf7ee3a91b0c78c80d84d647b', 'src/main/resources/assets/destiny/models/weapon/machine_gun/retrofit_escapade_inspect_twohand.json': '1addc569c198598c07c7e08822de659a1b0e877c1e25ca94651f96d78992d2bc', 'src/main/resources/assets/destiny/models/weapon/machine_gun/retrofit_escapade.json': '5487264f6226b82d50fdab909ebfdc32376ccb88a66c7609bc4e736aceaf7490', 'src/main/resources/assets/destiny/models/weapon/machine_gun/retrofit_escapade_inspect.json': '3cca9bbf78a6367b4436abad0f24fa9a4118bc7fc9026cf37ea69ebd3fa3771b', 'src/main/resources/assets/destiny/models/weapon/machine_gun/retrofit_escapade_ads.json': 'c5595dbf4c8c4a8b64ed21deb3532bec398361d06c79da83d5335b804f89cd6a', 'src/main/resources/assets/destiny/models/weapon/machine_gun/retrofit_escapade_ads_twohand.json': '5f43265f0d607e9a0f7ce278ebcc51801810fe7e3c988cbd4f7e90a6befda59d'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=z7MW1pAbSxM', 'creator': 'Boosh Ninja', 'title': 'Season of the Seraph | Legendary Weapon Sound and Visual Showcase (Destiny 2)', 'fps': 60, 'chapterSeconds': [453, 571], 'actionSeconds': [472.3, 476.3], 'frames': [{'path': '/private/tmp/w181-retrofit-report/reference-01.png', 'sha256': 'b72cbe9dc7662fae38a7a7a028db577ba876b684e3dd6ea7981e4ccba888dc5b', 'timestampSeconds': 5.0, 'sourceFrameIndex': 300, 'observation': 'Inventory visibly labels RETROFIT ESCAPADE; teal body, quilt wrap, fork, side drum, linked feed and hooded optic.', 'nearestAuthoredProgress': 0, 'source': 'identity'}, {'path': '/private/tmp/w181-retrofit-report/reference-02.png', 'sha256': 'ae86dc34c33259e0bda125971d38692f83fa0eaba955b9461c6dd461716befc7', 'timestampSeconds': 472.3, 'sourceFrameIndex': 28338, 'observation': 'HUD empty, optic and cover closed; reload begins.', 'nearestAuthoredProgress': 0, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-03.png', 'sha256': '0fe5c56c8c7096aa1aa6417bc211a12d407a654588eea1eac31bcc889f4febcd', 'timestampSeconds': 472.6, 'sourceFrameIndex': 28356, 'observation': 'Support hand reaches receiver; carrier dips and presents feed side.', 'nearestAuthoredProgress': 0.08, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-04.png', 'sha256': 'baf51c11a30a3bd5b66d25243cc827f98fc1b2c4624bbbcfa3478b08648e1d0b', 'timestampSeconds': 472.9, 'sourceFrameIndex': 28374, 'observation': 'Long top cover lifts with optic; forward hinge region visible.', 'nearestAuthoredProgress': 0.17, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-05.png', 'sha256': 'bb6e600e622e8623ea55957c90f0d05811fb2a2d83a17ba4217c01c55ac89805', 'timestampSeconds': 473.2, 'sourceFrameIndex': 28392, 'observation': 'Cover and optic upright; exposed feed receiver. Outgoing drum path partly occluded.', 'nearestAuthoredProgress': 0.22, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-06.png', 'sha256': 'b1da49182fa1758a6c2c1d65a3ba7b080c81a8c7497491c8774c9a16230e7a38', 'timestampSeconds': 473.4, 'sourceFrameIndex': 28404, 'observation': 'Hand brings cylindrical feed container toward underside; exact exchange boundary occluded.', 'nearestAuthoredProgress': 0.28, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-07.png', 'sha256': '8dc90b6c5283a3367e3ff6d396dced2da00ee7fbb717f2d5d39c6fede6ca8411', 'timestampSeconds': 473.8, 'sourceFrameIndex': 28428, 'observation': 'Raised cover remains open while support hand returns to feed.', 'nearestAuthoredProgress': 0.37, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-08.png', 'sha256': '4b6a3828a38742cc66275d44eaac1babd4d8de8b98f6fa34a2d539e54eec5bd0', 'timestampSeconds': 474.2, 'sourceFrameIndex': 28452, 'observation': 'Linked cartridges visible beside hand as belt is laid into exposed receiver.', 'nearestAuthoredProgress': 0.47, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-09.png', 'sha256': '9042acc4d27f1764941826f486bf819e43c2b7e84b08fa91e3b23b62c4d359dd', 'timestampSeconds': 474.4, 'sourceFrameIndex': 28464, 'observation': 'Palm presses over exposed belt/feed under raised cover.', 'nearestAuthoredProgress': 0.53, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-10.png', 'sha256': '74f3b628c7e0aee52e2f87a2d3ad0b686673e314347b42020993acd238cc6275', 'timestampSeconds': 474.8, 'sourceFrameIndex': 28488, 'observation': 'Cover closes with optic returning to sight line.', 'nearestAuthoredProgress': 0.63, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-11.png', 'sha256': 'bef330faa2232acff48262ce364f68fdce3605a1221562451d652c5bd4e3e9d9', 'timestampSeconds': 475.4, 'sourceFrameIndex': 28524, 'observation': 'Muzzle rises and support hand performs side charging/settling action; exact lug travel obscured.', 'nearestAuthoredProgress': 0.78, 'source': 'showcase'}, {'path': '/private/tmp/w181-retrofit-report/reference-12.png', 'sha256': 'd152b997ee079f324332a08b763ee3df5a4ff6e1c3f1adc45bb4f9fdaee4474d', 'timestampSeconds': 476.3, 'sourceFrameIndex': 28578, 'observation': 'Hand released; HUD loaded and ready hip view restored.', 'nearestAuthoredProgress': 1, 'source': 'showcase'}], 'sourceVideoSha256': '067ee9f888e7c7ec9bab6317f88d2a4502af575366cc3b603e5a4edf0ae6a1cf', 'sourceMetadataSha256': '06ae8ea313053ee7c651cb29c7fdc703c32cb29b758c2a98f43534fe56c89313', 'identity': {'url': 'https://www.youtube.com/watch?v=oiqZXmyL2Ao', 'creator': 'DeathFr0mAboveX', 'title': 'Retrofit Escapade Machine Gun First Look - Destiny 2 Season of the Seraph', 'fps': 60, 'sourceVideoSha256': '6d4518ac393bb663446bd09b3f3d164866bb92ae756bab8a33f3313ac2365ece', 'sourceMetadataSha256': '1c3365cc52e9d7b649f3964d659d4413aeb8b1780d596775228e9d7098c1f42d'}}

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
    return e['name'].startswith(('drum_','round_','feed_join_'))


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
    # Drum, all rounds, links and connectors share exactly one rigid local transform.
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
    # Only CPU raster/UV utility reused; no Hammerhead footage or animation keys.
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
                points=(np.asarray(pts)-8).copy();n=np.asarray(normal).copy()
                if hand==FP[1]:points[:,0]*=-1;n[0]*=-1
                points=points*ss@rr.T+tt;n=rr@n
                if hand==FP[1]:points[:,0]*=-1;n[0]*=-1
                triangles.append((points,uv,tex,n))
        return triangles
    def raster(ts,cam,w,h,extent=None):
        if extent is None:extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    sheet=Image.new('RGB',(1600,1800),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,12),'W181 RETROFIT ESCAPADE | emitted cuboids + display reconstructed | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    cams=([1,.45,-.55],[-1,.3,.6],[.3,.5,1])
    for row,cam in enumerate(cams):
        groups=[posed(i) for i in (0,6,11,20)]
        extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,280)
        for col,(i,g) in enumerate(zip((0,6,11,20),groups)):
            sheet.paste(raster(g,cam,400,280,extent),(col*400,55+row*315))
            draw.text((col*400+10,35+row*315),f'p={i/20:.2f} / common framing',fill='white')
    draw.text((12,1010),'134 existing cubes = 83 body (24 cover/optic + 1 lug) + 51 drum/belt. No added solids or mesh fields.',fill='white')
    for col,i in enumerate((0,4,6,11)):
        sheet.paste(raster(posed(i,detail=True),[1,.65,.5],400,330),(col*400,1060))
        draw.text((col*400+10,1038),f'FEED DETAIL p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(6,grip=grip,hand=hand),[1,.35,-.5],400,300),(col*400,1450))
        draw.text((col*400+10,1420),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((12,1770),'Canonical endpoints; whole drum + complete linked belt move together; optic travels with cover; feed seats before closure.',fill='white')
    story=Image.new('RGB',(1600,1900),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL Retrofit Escapade | z7MW1pAbSxM + labeled oiqZXmyL2Ao identity | AUTHORED asset below | OFFLINE',fill='white')
    for i,f in enumerate(REFERENCE['frames']):
        p=evidence/Path(f['path']).name
        if sha(p.read_bytes())!=f['sha256']:raise ValueError('Reference hash drift: '+str(p))
        im=Image.open(p).convert('RGB')
        im.thumbnail((400,245))
        x=i%4*400;y=50+i//4*600
        story.paste(im,(x+(400-im.width)//2,y+(245-im.height)//2))
        draw.text((x+8,y+250),f"ACTUAL {f['timestampSeconds']:.2f}s / {f['source']}",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.45,.6],400,280),(x,y+280))
        draw.text((x+8,y+565),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((12,1872),'Exact pivots, angles, hidden drum clearance and phase normalization authored. Original raw 1280x720 frames retained outside product.',fill='white')
    return png(sheet),png(story)


def generate(render=False,evidence=Path('/private/tmp/w181-retrofit-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=134:raise ValueError('Canonical element drift')
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w181_retrofit_escapade.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W181',weapon='retrofit_escapade',revision=1,itemModel='destiny:'+KEY,ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),sourceElements=134,bodyElements=83,movingElements=51,coverElements=24,chargingHandleElements=1,maxAssembledElements=134,elementLimit=1000,addedElements=0,triangleAdapterElements=0,
      sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,coverNames=COVER_NAMES,chargingHandleNames=BOLT_NAMES,
      geometryPolicy='Exact canonical parent partition. Existing upper rail/rear shoulder and complete optic articulate rigidly in body child overrides; original charging lug translates after closure. Every original face/UV/material/solid dimension retained; endpoint geometry/display exact.',
      payloadPolicy='All 10 existing drum/neck solids, 35 cartridge solids (7 rounds with case/facet/shoulder/tip/link) and 6 belt connectors share ONE rigid transform. Belt tail enters existing drum neck. No isolated bullets, exploded rim, shrink-to-hide, duplicate payload, new interior faces or arbitrary mesh triangles.',
      authoredHiddenDetails='Exact hinge/grip, canonical cover membership, opening96deg, drum clearance path, timing normalization and lug travel are authored interpretations. Exchange is partly hand-occluded in source. One complete drum/belt asset proxies outgoing/incoming; no source bones or animation extracted.',
      keyframes=KEYS,gripPivot=GRIP,coverHinge=HINGE,drumAnchor=[6.52,8.47,3.92],hipEndpoints=[0,20],endpointPolicy='Both parts, both FP hands and both grips exactly canonical at 0/1. Non-FP and ADS/inspect use exact canonical graph at every progress.',
      normalizedPhases={'present':[0,.08],'openCoverAndOptic':[.08,.18],'withdrawCompleteFeed':[.18,.26],'occludedExchange':[.26,.30],'returnDrumAndBelt':[.30,.50],'seatFeed':[.50,.58],'closeCoverAndOptic':[.58,.66],'sideAction':[.66,.80],'release':[.80,.88],'recover':[.88,1]},
      reference=REFERENCE,referencePolicy='Inventory visibly names Retrofit Escapade in oiqZXmyL2Ao at5s. Action identified by same distinctive fork/wrap, hood/loop optic, side drum and exposed linked feed plus dedicated labeled chapter in z7MW1pAbSxM. No API hash/roll read from action frames. Showcase dark/red shader is not default dye; retain canonical teal/cloth/copper atlas. Raw footage/frames retained privately outside source.',
      motionAuthorship='Reference-observed long cover and optic raising together, feed container/belt handling, palm at feed, closure with optic, muzzle-up final side hand action and ready recovery. Numeric carrier/path/hinge/lug travel authored. W179/W114/W180 informed graph/matrix conventions only; their motion and frames are not Retrofit evidence.',
      timingPolicy='Normalized visual progression only. Preserve local magazine77, reload90ticks, RPM900, cadence1.333333333333ticks, burst1, whole-mag ammo transfer, funding and audio. Video HUD87 and clip speed are not local timing or capacity inputs.',
      rotationConvention='Element Rz Ry Rx; display JOML Rx Ry Rz; uniform equal-scale grip carrier. Native left reflection F*T*F; offline preview applies it too.',
      nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
      integration={'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'retrofit_escapade','assetInputs':'float1 normalized progress; boolean0 existing twohand grip; negative progress canonical fallback. Master owns admission, route, lifecycle, ammo, clocks and native session.'},
      nativeQueue=['Master route/admit retrofit_escapade to destiny:'+KEY+' with float1 progress and boolean0 grip. No new 3P reload or handIK.',
      'Both FP hands/grips: exact idle/recovery; optic/cover open, complete drum/belt clearance, feed seating, cover/optic close, final lug action. Check mirrored hand, muzzle/framing, grip contact, receiver/drum/cover clearance.',
      'ADS/inspect while progressing, GUI/ground/fixed/head/third-person observer and inactive float1=-1 retain canonical model; no residual split.',
      'Partial/empty/full/no-reserve reload, fire/reload spam; preserve90tick clock and one ammo transfer. Switch/cancel/equip/unequip/death/disconnect restore without delayed transfer.',
      'Listen to unchanged reload sound and briefly show10-20 weapons for visible artifacts/stalls. All native rows pending; worker never launches game/server or controls input.'],
      canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact 90')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w181-retrofit-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w181-manifest.json').read_bytes())['features'] if f['name']=='w181-retrofit'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic core outputs/media hashes; 87 pack assets; 83+51=134 assembled elements; native pending')
if __name__=='__main__':main()
