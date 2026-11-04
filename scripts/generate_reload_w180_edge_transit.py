#!/usr/bin/env python3
"""W180 original Edge Transit: steep presentation, cradle release, rigid drum out/in,
securing/action and recovery. Canonical 96 cubes/UV/paint remain untouched.
No runtime, admission, timing or audio edits. --render uses retained actual frames;
--verify checks deterministic JSON and retained comparison/storyboard hashes offline.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w180/edge_transit')
KEY='weapon_reload_w180_edge_transit/edge_transit'
SOURCE=A/'models/weapon_surface_w123/edge_transit.json'
TWOHAND=A/'models/weapon/heavy_grenade_launcher/edge_transit_twohand.json'
ITEM=A/'items/weapon/edge_transit.json'
TEXTURE=A/'textures/item/weapon/w123/edge_transit.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,8.8,8.5)
DRUM_ANCHOR=(8.53,10.22,3.11)
HINGE=(8.53,9.67,.85)
CRADLE_NAMES=('drum_latch_-1','drum_latch_1','drum_cradle_-1','drum_cradle_1')
BOLT_NAMES=('charging_lug',)
# p, carrier XYZ deg, display shift, rigid source-local drum shift,
# cradle X deg about transverse front pivot, charging lug source Z travel.
# Action order observed. Every numerical key and obscured mechanical detail authored.
KEYS=(
 (0.,(0,0,0),(0,0,0),(0,0,0),0,0),
 (.10,(12,-8,-10),(.15,-.25,0),(0,0,0),0,0),
 (.20,(40,-14,-17),(.25,-.55,.15),(0,0,0),38,0),
 (.30,(64,-14,-19),(.35,-.65,.2),(-6.4,0,0),38,0),
 (.42,(68,-14,-19),(.35,-.65,.2),(-6.4,-5.,.2),38,0),
 (.52,(68,-14,-19),(.35,-.65,.2),(-6.4,-5.,.2),38,0),
 (.64,(64,-14,-19),(.35,-.65,.2),(-6.4,0,0),38,0),
 (.74,(60,-13,-18),(.3,-.55,.15),(0,0,0),38,0),
 (.81,(55,-12,-16),(.25,-.45,.1),(0,0,0),0,0),
 (.89,(39,-9,-12),(.2,-.3,.05),(0,0,0),0,.85),
 (.94,(27,-6,-7),(.1,-.2,0),(0,0,0),0,0),
 (1.,(0,0,0),(0,0,0),(0,0,0),0,0),
)
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/edge_transit.json': '956b63c38db50b3b127dda9848c640fb65c4d61711bf8856304da6c29d4b3729', 'src/main/resources/assets/destiny/textures/item/weapon/w123/edge_transit.png': '2168e104d3458d0148ac28994ac281b742f41289e36f8bb260c0f2d156d96fb8', 'src/main/resources/assets/destiny/items/weapon/edge_transit.json': 'f0143e85d43e17a6b70839009de4690544565da02db434d6e60431ece2db540a', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/models/weapon/heavy_grenade_launcher/edge_transit.json': '36a302124a0c4ab1cc88b1caad77d07fb1a021e150d6118a9656ea3cee2509f9', 'src/main/resources/assets/destiny/models/weapon/heavy_grenade_launcher/edge_transit_ads_twohand.json': 'f3cffe09bca5ff0709ac59fb4e0f3d5277e62cbafdda149f78b2d19adf662e8e', 'src/main/resources/assets/destiny/models/weapon/heavy_grenade_launcher/edge_transit_inspect.json': 'ccf1051705ddd2cd9759c892e36aba08704a9d25e8c7c53a1746f0f11f58aacc', 'src/main/resources/assets/destiny/models/weapon/heavy_grenade_launcher/edge_transit_inspect_twohand.json': '7a3a1fa94398cca7eb40fc1f6f398592581d57faf9f1fa7c7f77f565eafdc7d6', 'src/main/resources/assets/destiny/models/weapon/heavy_grenade_launcher/edge_transit_ads.json': '9760e2fb6911d07ff96ae5bf7249862e1e5d629fad28f0b7225043c1e3723af4', 'src/main/resources/assets/destiny/models/weapon/heavy_grenade_launcher/edge_transit_twohand.json': '578a4c349ea3cc04c468525f84cf7192b8658f1e60ec38b753e43c0f60e6168b'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=afQnPfb4ZK4', 'creator': 'Quan Slow', 'title': 'Destiny 2 | Normal Reload - Field Prep Reload (일반리로드 - 야전준비 리로드)', 'uploadDate': '20181014', 'retrieved': '2026-10-27', 'fps': 60, 'frames': [{'path': '/private/tmp/w180-edge-transit-report/reference-01.png', 'sha256': '9e8cd44eea0d84045af2257d03609cb57af30460bde62185e2596eb709488aad', 'timestampSeconds': 3.0, 'sourceFrameIndex': 180, 'nearestAuthoredProgress': 0, 'observation': 'Ready hip view; ribbed drum, frame and sight correspond to original Edge Transit silhouette.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-02.png', 'sha256': '919187f6800111ba752783211b8ddf8ccf38df2a8c27b90cbcca932c6d573000', 'timestampSeconds': 3.8, 'sourceFrameIndex': 228, 'nearestAuthoredProgress': 0.15, 'observation': 'Support hand reaches drum while muzzle begins to rise.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-03.png', 'sha256': '94ac9d88accd9a7b53a3510805a8bd3e199bad3e0f28ba73d79d67aaaf29cf41', 'timestampSeconds': 4.0, 'sourceFrameIndex': 240, 'nearestAuthoredProgress': 0.22, 'observation': 'Launcher presented sideways; support hand grasps drum.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-04.png', 'sha256': '85babb11f0d5a0fab4b3ef645b4027de81902dac0b9a01c6f9ec11b392d4bf42', 'timestampSeconds': 4.2, 'sourceFrameIndex': 252, 'nearestAuthoredProgress': 0.3, 'observation': 'Muzzle now steeply raised; hand working around drum/cradle.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-05.png', 'sha256': '333a96a014aac7923d6430a0fb0355c432f7eb8c176171745085be0337028909', 'timestampSeconds': 4.4, 'sourceFrameIndex': 264, 'nearestAuthoredProgress': 0.36, 'observation': 'Support hand covers drum; outward separation partly occluded.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-06.png', 'sha256': '65e19b15d4ff482398ffd46437fc251af3adcfcdde6fe783dc02295c9346022a', 'timestampSeconds': 4.8, 'sourceFrameIndex': 288, 'nearestAuthoredProgress': 0.44, 'observation': 'Open rectangular frame gap below raised barrel; drum absent from its seat.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-07.png', 'sha256': '5d5a08e0ffc40ab79d442da17f2286a2392c87f41f1ffdb0c973ef39355dcf8d', 'timestampSeconds': 5.0, 'sourceFrameIndex': 300, 'nearestAuthoredProgress': 0.5, 'observation': 'Empty frame remains visible; no individual shell insertion.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-08.png', 'sha256': '9679fdb4e08aad4735876513ae78a382840435857359dea2bc2bc8a0c981de55', 'timestampSeconds': 5.2, 'sourceFrameIndex': 312, 'nearestAuthoredProgress': 0.62, 'observation': 'Support hand and incoming drum enter lower frame area.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-09.png', 'sha256': '110df96a59c0db013c0a1d41fe8c5d84acd7d1bd179c2e78c88066c6250a8773', 'timestampSeconds': 5.4, 'sourceFrameIndex': 324, 'nearestAuthoredProgress': 0.74, 'observation': 'Drum back at frame; HUD now reads six; this is only a recorded HUD observation.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-10.png', 'sha256': '578a71f6977e7ded41e17cb9bd17131c7891481892776603041e6a97193c3b59', 'timestampSeconds': 5.6, 'sourceFrameIndex': 336, 'nearestAuthoredProgress': 0.84, 'observation': 'Support hand stays on seated drum/receiver during final securing action.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-11.png', 'sha256': '93393d81bb8f3f46556b6c62d2b24fa432dc3d7cf7283e21c34e6fc53f0d7bef', 'timestampSeconds': 5.8, 'sourceFrameIndex': 348, 'nearestAuthoredProgress': 0.92, 'observation': 'Launcher lowers toward ready; exact charging lug travel not visible.'}, {'path': '/private/tmp/w180-edge-transit-report/reference-12.png', 'sha256': '9f7f7bd3ee5bf0cd20b220ec437263724faafd38bf3705cd291eca7da81507e9', 'timestampSeconds': 6.2, 'sourceFrameIndex': 372, 'nearestAuthoredProgress': 1, 'observation': 'Ready hip view restored with drum seated.'}], 'sourceVideoSha256': 'c82d982b77c3c953ee8d9ea9cf1836e1b46d02cd21fe596f47ca320367c77eb6', 'sourceMetadataSha256': '239e3ac9b9c58de34f79cf26cdd32e3036f22a9a2978293e949692c810caaa48', 'identity': {'url': 'https://www.youtube.com/watch?v=AtnnHxiwWg8', 'timestampSeconds': 51.051, 'sourceFrameIndex': 1530, 'fps': '30000/1001', 'path': '/private/tmp/w180-edge-transit-report/identity.png', 'sha256': '01db92c4adb2e74a5b54b5ee7103ce91e82d6ced31e6cb198bdede246f76da9d', 'observation': 'Labeled EDGE TRANSIT original green/seafoam model in inventory; identity and geometry reference, not reload footage.'}, 'model': {'url': 'https://www.bungie.net/common/destiny2_content/screenshots/218335759.jpg', 'localPath': '/private/tmp/destiny-weapons-w31/references/edge_transit.jpg', 'sha256': '76ae0e6f799a201cc83c725e43f37dbe33eebf1fa6d0957e2d76025f1ff7a085'}, 'identification': 'Reload footage is visually identified by original Edge Transit barrel/drum/cradle/frame/sight versus official original and labeled inventory; it has a dark shader. Reload clip does not expose an API hash or title; this is visual identity, not API telemetry.', 'authorship': 'Observed action order only. Numeric angles, pivots, cradle release, hidden extraction path, charge-lug movement and normalized phase mapping are authored local adaptation; no recovered bones, hand IK or clock measurement.', 'limitations': ['2018 historical footage with uncontrolled perks/Field Prep; no timing calibration.', 'Support hand obscures exact latch and drum extraction path.', 'Final hand action visible, exact charging mechanism not visible.', 'Reference shader differs; current canonical green/seafoam paint is preserved.', 'Offline renders are not native QA.']}

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
    return e['name'].startswith(('drum_core_','drum_bay_','drum_front_rim_','drum_rear_rim_'))

def partition(source):
    parts={}
    for part in PARTS:
        model={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        model['elements']=[copy.deepcopy(e) for e in source['elements'] if is_payload(e)==(part=='magazine')]
        parts[part]=model
    return parts


def articulated_elements(elements,p):
    """Rigid authored cradle release and action of existing solids only.
    The front pivot remains on body; the four original bracket solids open together.
    This mechanism is an adaptation of occluded handling, not extracted animation.
    """
    _,_,_,opening,bolt=sample(p)
    result=copy.deepcopy(elements)
    for e in result:
        if e['name'] in CRADLE_NAMES and opening:
            turn=xyz((opening,0,0));center=[(a+b)/2 for a,b in zip(e['from'],e['to'])]
            old=e.get('rotation',{});origin=old.get('origin',center)
            old_angles=[old.get(axis,0) if 'axis' not in old else (old['angle'] if old['axis']==axis else 0) for axis in 'xyz']
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
    # Complete drum, both rims and all bays share exactly one rigid local transform.
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
    # Shared CPU raster/UV helper only; no other weapon motion or reference imported.
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    def rotation(a):
        x,y,z=np.radians(a)
        rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
        ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
        rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
        return rx@ry@rz
    def posed(i,grip='native',hand=FP[0],detail=False):
        ts=[]
        for part in PARTS:
            model=json.loads(output[A/f'models/{KEY}_{part}.json'])
            child=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])
            if 'elements' in child:model['elements']=child['elements']
            if detail:model['elements']=[e for e in model['elements'] if is_payload(e) or e['name'] in CRADLE_NAMES or e['name'].startswith('drum_pivot')]
            # The shared helper accepts XYZ only. Normalize this private render copy;
            # emitted canonical axis/angle records remain byte-for-byte unchanged.
            for e in model['elements']:
                er=e.get('rotation',{})
                if 'axis' in er:e['rotation']=dict(origin=er['origin'],**{er['axis']:er['angle']})
            d=child['display'][hand];rr=rotation(d['rotation']);ss=np.array(d['scale']);tt=np.array(d['translation'])
            for pts,uv,tex,normal in helper['model_triangles']({'part':model},texture):
                pts=np.asarray(pts).copy();normal=normal.copy()
                if hand==FP[1]:pts[:,0]=16-pts[:,0];normal[0]*=-1
                world=(pts-8)*ss@rr.T+tt;normal=rr@normal
                if hand==FP[1]:world[:,0]*=-1;normal[0]*=-1
                ts.append((world,uv,tex,normal))
        return ts
    def raster(ts,cam,w,h,extent=None):
        if extent is None:extent=helper['frame'](np.concatenate([t[0] for t in ts]),cam,w,h)
        return helper['render'](ts,cam,extent,(w,h))[0]
    sheet=Image.new('RGB',(1600,2100),'#111925');draw=ImageDraw.Draw(sheet)
    draw.text((12,10),'W180 EDGE TRANSIT | emitted canonical cubes + display reconstruction | OFFLINE, NO HANDS / NOT NATIVE',fill='white')
    photo=Image.open(evidence/'identity.png').convert('RGB');photo.thumbnail((780,420));sheet.paste(photo,(0,40))
    sheet.paste(raster(posed(0),[1,.4,-.65],800,420),(800,40))
    draw.text((12,464),'ACTUAL labeled Edge Transit 51.051s / AtnnHxiwWg8                 AUTHORED canonical green/seafoam HIP / 96 existing cubes',fill='white')
    for row,cam in enumerate(([1,.45,-.55],[-1,.3,.6],[.3,.5,1])):
        groups=[posed(i) for i in (0,9,15,20)]
        extent=helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,400,280)
        for col,(i,g) in enumerate(zip((0,9,15,20),groups)):
            sheet.paste(raster(g,cam,400,280,extent),(col*400,520+row*310))
            draw.text((col*400+10,500+row*310),f'p={i/20:.2f} / common framing',fill='white')
    for col,i in enumerate((0,4,9,15)):
        sheet.paste(raster(posed(i,detail=True),[1,.65,.5],400,260),(col*400,1480))
        draw.text((col*400+10,1458),f'DRUM + CRADLE detail p={i/20:.2f}',fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(9,grip=grip,hand=hand),[1,.35,-.5],400,280),(col*400,1790))
        draw.text((col*400+10,1760),grip+' / '+hand.replace('firstperson_',''),fill='white')
    draw.text((12,2075),'68 body + 28 rigid drum. 4 body bracket solids articulate; 1 existing lug acts after reseat. No added geometry, textures or scale fade.',fill='white')
    story=Image.new('RGB',(1600,1940),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL original-style Edge Transit (dark shader) / afQnPfb4ZK4 | AUTHORED local progression below | OFFLINE',fill='white')
    for i,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,245))
        x=i%4*400;y=50+i//4*620
        story.paste(im,(x+(400-im.width)//2,y+(245-im.height)//2))
        draw.text((x+8,y+250),f"ACTUAL {f['timestampSeconds']:.2f}s / frame {f['sourceFrameIndex']}",fill='white')
        index=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(posed(index),[1,.45,.6],400,300),(x,y+280))
        draw.text((x+8,y+585),f'AUTHORED p={index/20:.2f} / independent framing',fill='white')
    draw.text((12,1910),'Observed: raise, drum out, empty frame, drum return, final securing hand action, settle. Exact pivots/path/action travel authored.',fill='white')
    return png(sheet),png(story)

def generate(render=False,evidence=Path('/private/tmp/w180-edge-transit-report')):
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w180_edge_transit.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W180',weapon='edge_transit',revision=1,itemModel='destiny:'+KEY,ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),sourceElements=96,bodyElements=68,movingElements=28,cradleElements=4,chargingHandleElements=1,maxAssembledElements=96,elementLimit=1000,addedElements=0,triangleAdapterElements=0,
      sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,cradleNames=CRADLE_NAMES,chargingHandleNames=BOLT_NAMES,
      geometryPolicy='Exact canonical parent partition. Four existing cradle/latch solids open in body overrides; existing charging lug translates after seating. Every face/UV/texture and cube dimension retained; endpoints exact.',
      payloadPolicy='All 28 original drum solids (4 core, 8 bays, 16 rim segments) form one rigid payload. No individual grenades, rifle box, scale-fade, duplicate drum or disassembled rim.',
      authoredHiddenDetails='Numeric grip/pivots, bracket membership/opening, sideways clearance around lower rail, hidden outgoing/incoming path and charging-lug travel authored. Same drum asset proxies outgoing/incoming; hand occludes original exchange. No original skeleton extracted.',
      keyframes=KEYS,gripPivot=GRIP,drumAnchor=DRUM_ANCHOR,cradleHinge=HINGE,hipEndpoints=[0,20],endpointPolicy='Both parts, both FP hands and both grips exactly accepted at 0/1. All non-FP and ADS/inspect select exact canonical graph even during progress.',
      normalizedPhases={'present':[0,.10],'releaseCradle':[.10,.20],'withdrawDrumSideways':[.20,.30],'lowerClearOfFrame':[.30,.42],'emptyCradleHold':[.42,.52],'raiseReplacement':[.52,.64],'reseatDrum':[.64,.74],'secureCradle':[.74,.81],'actionAndRelease':[.81,.94],'recover':[.94,1]},
      reference=REFERENCE,referencePolicy='Same original Edge Transit geometry visually identified against Bungie hash218335759 photo and labeled inventory. Reload clip is dark shader, original paint never copied from footage. No API hash/controlled roll exposed in action clip. Raw frames retained privately.',
      motionAuthorship='Edge Transit steep muzzle-up carrier and complete drum exchange, empty rectangular frame interval, cradle securing and short final action. Matrix/display/graph conventions reused; no other weapon keyframes or action source used.',
      timingPolicy='Normalized visual presentation only. Existing magazine5/reload66ticks/cadence10ticks/RPM120/burst1/whole-mag transfer and all funding/ammo/audio/data unchanged. Recorded HUD6 is not adopted as local magazine size.',
      rotationConvention='Element Rz Ry Rx; display JOML Rx Ry Rz; rigid equal-scale grip carriers; native ItemTransform applies left reflection.',
      nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
      integration={'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'edge_transit','assetInputs':'float1 normalized progress; boolean0 existing twohand grip; negative inactive selects canonical. Existing 21-sample whole-mag graph. Master owns route/admission/lifecycle/clocks/native session.'},
      nativeQueue=['Admit edge_transit to existing whole-mag route; verify model destiny:'+KEY+' with float1 and boolean0. No new third-person reload or hand IK.',
      'Both FP hands and grips: ready endpoints; steep presentation, bracket release, complete rigid drum departure, empty cradle, replacement reseat, secure and final action. Check muzzle/framing, lower rail clearance, grip/contact and mirrored left hand.',
      'ADS/inspect during progress and GUI/ground/fixed/head/third-person observer keep canonical model; inactive float1=-1 canonical; no residual split after completion.',
      'Partial/empty/full/no-reserve reload and fire/reload spam; existing 66tick clock and funding/ammo transfer once. Switch/equip/unequip/cancel/death/disconnect restore and clear progress without delayed transfer.',
      'Listen to unchanged reload sound; brief 10-20 displayed weapons for obvious artifacts or stalls. Master only; all native rows pending.'],
      canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact 90')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w180-edge-transit-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w180-manifest.json').read_bytes())['features'] if f['name']=='w180-edge-transit'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic core outputs/media hashes; 87 pack assets; 68+28=96 assembled elements; native pending')
if __name__=='__main__':main()
