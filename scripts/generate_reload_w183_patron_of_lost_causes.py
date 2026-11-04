#!/usr/bin/env python3
"""W183 Patron of Lost Causes FP reload from inspected same-weapon gameplay.
Canonical 98 solids/UV/dye and gameplay retained. Only owned pack/art writes.
--render reads retained actual frames in external --evidence; --verify is media-free.
W182 supplies rigid algebra/graph/layout infrastructure only, never motion evidence.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w183/patron_of_lost_causes')
KEY='weapon_reload_w183_patron_of_lost_causes/patron_of_lost_causes'
SOURCE=A/'models/weapon_surface_w123/patron_of_lost_causes.json'
TWOHAND=A/'models/weapon/scout_rifle/patron_of_lost_causes_twohand.json'
ITEM=A/'items/weapon/patron_of_lost_causes.json'
TEXTURE=A/'textures/item/weapon/w123/patron_of_lost_causes.png'
FP=('firstperson_righthand','firstperson_lefthand')
MAGAZINE_NAMES=('magazine_body','magazine_floor')
GRIP=(8.,7.65,8.80)
MAG_ANCHOR=(8.,8.25,12.14)
# Inspected Patron bullpup reload: steep muzzle-up lift, rear magazine exchange,
# brief seating rock, fast lowering and small settling dip. XYZ display motion;
# magazine withdrawal follows its canonical -8deg X slant. Hidden path authored.
KEYS=((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.08, (3, -1, -2), (0.02, -0.03, 0), (0, 0, 0)), (0.2, (72, -14, -10), (0.35, 0.05, 0.15), (0, -4.8, 0.675)), (0.3, (82, -17, -13), (0.55, 0.1, 0.25), (-0.25, -5.8, 0.815)), (0.42, (78, -16, -11), (0.55, 0.1, 0.25), (-0.25, -5.8, 0.815)), (0.5, (70, -13, -8), (0.4, 0.05, 0.2), (-0.12, -2.9, 0.4075)), (0.6, (73, -12, -7), (0.35, 0.12, 0.15), (0, 0, 0)), (0.7, (25, -4, -3), (0.15, -0.05, 0.05), (0, 0, 0)), (0.8, (-4, 1, 1), (0.02, -0.15, 0), (0, 0, 0)), (0.9, (2, 0, 0), (0, -0.03, 0), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))

PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/patron_of_lost_causes.json': 'e0afa39e288ca3fee279ea49237ae5233ea7747775b601f67fec2b94b3d5609e', 'src/main/resources/assets/destiny/textures/item/weapon/w123/patron_of_lost_causes.png': 'c2fde451365efd21ab1c3940695eff5a254fae8ea3188c31b8af69e1d42ac0d8', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/items/weapon/patron_of_lost_causes.json': 'cfcc2f992c8119ac461d9f1baf943a5e0d38edf23e4c6b1f0f6a58e832cdd900', 'src/main/resources/assets/destiny/items/weapon_aim_w70/patron_of_lost_causes.json': '7ddfdd4b14a76cd956bc459df795e130a012a8212f079d1c65f8e600ef12841d', 'src/main/resources/assets/destiny/items/weapon_sight_w153/patron_of_lost_causes.json': '581f32398c3bef161f566edb543f3711ae35c9e1979b58dca565dd78556be0da', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes.json': 'd1086431cad2a610031c46f4c6990c3ae9680b605a44990b3cd9adf428bfdae8', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_twohand.json': 'bfb7d23f17b16b5d483318d57b6b651a1dd3fd273f6de7336e0fa12ac137205c', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_ads.json': 'dd79a321166e00ba61041285bde6ceb9ea5275777fc59479cb61b2260cdd289b', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_ads_twohand.json': 'b6c25873acac25023ca96b9906926660473122ff02f3db47e15ac1b3b22cea5f', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_inspect.json': 'e4acc2572ab9d9bca32651518e07c5cde85d454008921ac76e576c0206e10c0d', 'src/main/resources/assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes_inspect_twohand.json': 'c667780295c146b87706f1dae23da46e39d0cda5c621e042bee8336b07dab331'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=SLB49l1oUmA', 'creator': 'TheGamesEntertainer', 'title': 'Destiny 2 Season of Dawn Unlock Fast Rifle Reload Mod Use on New Scout Patron of Lost Causes', 'published': '2019-12-20', 'fpsNumerator': 60000, 'fpsDenominator': 1001, 'timeBase': '1/60000', 'frameDurationPts': 1001, 'dimensions': [1280, 720], 'selectedSeconds': [211.7115, 212.7125], 'identitySeconds': 18.018, 'inspectedActualFrames': True, 'frames': [{'file': 'reference-01.png', 'sha256': 'e796c5d1ac1531212e6d2e73e74e0486b882879d4ea2098c1e8b4fe11a41d189', 'timestampSeconds': 18.018, 'sourceFrameIndex': 1080, 'pts': 1081080, 'nearestAuthoredProgress': 0, 'observation': 'Inventory PATRON OF LOST CAUSES nameplate, long silver casing, narrow optic, gold barrel/internal tube, black open triangular stock and forward underside hook. Identity only.'}, {'file': 'reference-02.png', 'sha256': '6a90b084fb64e7d1df3a1b61b726a8a5877248c4947105948e9b8e84fc0cf29e', 'timestampSeconds': 211.5113, 'sourceFrameIndex': 12678, 'pts': 12690678, 'nearestAuthoredProgress': 0, 'observation': 'Empty HUD0 after firing; receiver near hip before reload.'}, {'file': 'reference-03.png', 'sha256': 'f08b499bb3740524fb1985d8a6424d033b6e4f9f44593f5c15be535c96cc19d3', 'timestampSeconds': 211.6114, 'sourceFrameIndex': 12684, 'pts': 12696684, 'nearestAuthoredProgress': 0, 'observation': 'Empty HUD0, support hand still forward; pre-lift.'}, {'file': 'reference-04.png', 'sha256': '22cb1aa4115079ae7b9a47a85589b40398a3b7271903170162a5b4f64e63b7bf', 'timestampSeconds': 211.7115, 'sourceFrameIndex': 12690, 'pts': 12702690, 'nearestAuthoredProgress': 0, 'observation': 'Reload onset: support hand leaves forward contact toward rear magazine.'}, {'file': 'reference-05.png', 'sha256': '280d208459f5373b9a9a798631e00b943c7b9147cc07a83922465108fd13abb3', 'timestampSeconds': 211.8116, 'sourceFrameIndex': 12696, 'pts': 12708696, 'nearestAuthoredProgress': 0.1, 'observation': 'Support hand reaches toward bullpup rear underside as receiver begins rising.'}, {'file': 'reference-06.png', 'sha256': 'ff8276c766e9e76124f4e9c7f0e9e2ac91e9829347f2671da9c68d0d2ab0966c', 'timestampSeconds': 211.9117, 'sourceFrameIndex': 12702, 'pts': 12714702, 'nearestAuthoredProgress': 0.2, 'observation': 'Steep muzzle-up lift at right edge; rear stock and rear magazine region presented.'}, {'file': 'reference-07.png', 'sha256': '4cd5b608f6e445c847bd602180541dddfb34bf439444b112acded9123447538e', 'timestampSeconds': 212.0118, 'sourceFrameIndex': 12708, 'pts': 12720708, 'nearestAuthoredProgress': 0.3, 'observation': 'Near-vertical receiver hold; hand/screen edge occludes outgoing magazine exchange.'}, {'file': 'reference-08.png', 'sha256': 'dbf8402c564b9f13c06e1039f7308704472f2214027ff586ec3307b472fd8313', 'timestampSeconds': 212.1119, 'sourceFrameIndex': 12714, 'pts': 12726714, 'nearestAuthoredProgress': 0.4, 'observation': 'Steep hold continues; support hand returning beneath rear magazine socket.'}, {'file': 'reference-09.png', 'sha256': 'ea40db67c0b6f7fc290b63c2a9e03d9c1b9461659d5bb7921c311310ce24b0d7', 'timestampSeconds': 212.212, 'sourceFrameIndex': 12720, 'pts': 12732720, 'nearestAuthoredProgress': 0.5, 'observation': 'Replacement approach at rear underside; hand partly covers magazine body.'}, {'file': 'reference-10.png', 'sha256': '545e8d5a75e2fb57a4ed9406ed84615dc795b082a9343fc31ef56bdf6364fc10', 'timestampSeconds': 212.3121, 'sourceFrameIndex': 12726, 'pts': 12738726, 'nearestAuthoredProgress': 0.6, 'observation': 'Magazine seated: HUD15/reserve94; support hand begins opening under stock.'}, {'file': 'reference-11.png', 'sha256': 'ee9ddaf9c06ac74b1f5c48ed6e6710340d640cc8502b0c5b80233d36886149e0', 'timestampSeconds': 212.4122, 'sourceFrameIndex': 12732, 'pts': 12744732, 'nearestAuthoredProgress': 0.7, 'observation': 'Receiver lowers sharply; support hand moves forward along body. No isolated bolt stroke measurable.'}, {'file': 'reference-12.png', 'sha256': 'f1f0a56cae76a3fce5ced77a208347eea1cf0669ec0576a7e50b290ee4c2f6ef', 'timestampSeconds': 212.5123, 'sourceFrameIndex': 12738, 'pts': 12750738, 'nearestAuthoredProgress': 0.8, 'observation': 'Receiver near hip; support palm continues forward recovery.'}, {'file': 'reference-13.png', 'sha256': '9dc1e95c2f098480b509d1c0ac7e5204eea6aba1c4bbba105f59715c6b6261d6', 'timestampSeconds': 212.6124, 'sourceFrameIndex': 12744, 'pts': 12756744, 'nearestAuthoredProgress': 0.9, 'observation': 'Small low overshoot after rapid lowering; magazine seated.'}, {'file': 'reference-14.png', 'sha256': '97c41c456b1b5a505deed980ce859964631792b946cde22e0432ad3b3a7d6daf', 'timestampSeconds': 212.7125, 'sourceFrameIndex': 12750, 'pts': 12762750, 'nearestAuthoredProgress': 1, 'observation': 'Hip recovery with open support fingers leaving sight line.'}, {'file': 'reference-15.png', 'sha256': 'aefbdf5c0d094476e01dfdd245c379f3250db7d8734d2543b68bdfbcf12c0a41', 'timestampSeconds': 212.8126, 'sourceFrameIndex': 12756, 'pts': 12768756, 'nearestAuthoredProgress': 1, 'observation': 'Ready hip silhouette recovered, complete magazine seated.'}, {'file': 'reference-16.png', 'sha256': '9f9024473ee720b4e63f92581145b647b1e351503477a741149930d87f563532', 'timestampSeconds': 212.9127, 'sourceFrameIndex': 12762, 'pts': 12774762, 'nearestAuthoredProgress': 1, 'observation': 'Post-reload ready hip; same scope and receiver.'}], 'sourceVideoSha256': '9787ea62b2df878e8f83cd80e2fc8532611d9b97f3fe72d9a114f79fba33629e', 'sourceMetadataSha256': '945823edc26d8e03ccf4d2cc1f289dab8e9324da8a87456a61519d18b1d6d0a4', 'timeBasis': 'Exact sequential decoded select(n), PTS=n*1001 with time_base1/60000 and frame_rate60000/1001 confirmed by showinfo; no seek approximation.', 'chargingObservation': 'Empty reload: steep lift, rear magazine exchange, quick lower and open support-hand recovery. No separately measurable bolt/charging stroke; exposed_bolt, charging_stem and charging_knob stay fixed.', 'limitations': ['Source gameplay is backlit and dark; retain canonical silver/gold default dye and original local scope, never transfer gameplay lighting/shader.', 'Source enhanced rifle-loader/perks make observed timing faster; normalized sequence only, local15round/200RPM/39tick timing unchanged.', 'Exact hidden magazine exchange, grip pivot, translation and angles authored; one intact rear magazine proxies outgoing/incoming.', 'No extracted animation/bones, hand IK, new third-person reload, native pixels, audio/listening or performance claim.']}

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
    """Two canonical rear magazine solids; pistol grip/stock/charging components stay fixed.
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
    raster_helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles={part:raster_helper['model_triangles']({'full':json.loads(output[A/f'models/{KEY}_{part}.json'])},texture) for part in ('body','magazine')}
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
    draw.text((12,10),'W183 PATRON OF LOST CAUSES | emitted JSON reconstructed independently | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for row,cam in enumerate(cams):
        groups=[posed(i) for i in (0,7,20)]
        extent=raster_helper['frame'](np.concatenate([t[0] for g in groups for t in g]),cam,500,300)
        for col,(i,g) in enumerate(zip((0,7,20),groups)):
            sheet.paste(raster(g,cam,500,300,extent),(col*500,55+row*340))
            draw.text((col*500+12,35+row*340),f'p={i/20:.2f} / {labels[row]} / common framing',fill='white')
    draw.text((12,1060),'96 body + 2 whole rear-magazine solids = 98 cubes / 0 adapters. Canonical geometry, UV and dye retained.',fill='white')
    for col,cam in enumerate(cams):
        sheet.paste(raster(posed(7,('magazine',)),cam,500,240),(col*500,1110))
        draw.text((col*500+12,1088),'WHOLE MAG: rear bullpup body + floor | '+labels[col],fill='white')
    for col,(grip,hand) in enumerate((('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1]))):
        sheet.paste(raster(posed(15,grip=grip,hand=hand),[1,.2,-.45],375,240),(col*375,1380))
        draw.text((col*375+8,1357),f'Recovery p=.75 | {grip} / {hand}',fill='white')
    draw.text((12,1620),'Exact hip endpoints; hidden stroke and seat rock authored. No independent bolt motion. Native framing/sound pending master QA.',fill='white')
    story=Image.new('RGB',(2000,2210),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL TheGamesEntertainer / SLB49l1oUmA | Patron of Lost Causes identity + reload frames paired with AUTHORED sample | OFFLINE / NO HAND IK',fill='white')
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
    draw.text((420,1650),'One complete rear bullpup magazine; no scattered rounds.',fill='white')
    draw.text((420,1680),'Exact pivot/angles/stroke authored; hands absent in asset render.',fill='white')
    draw.text((420,1710),'Actual frames above; offline textured JSON reconstruction below.',fill='white')
    draw.text((420,1740),'No isolated bolt stroke established; canonical bolt/handle fixed.',fill='white')
    draw.text((12,2180),'Source lighting/shader NOT transferred. Canonical silver/gold dye + scope retained. Hidden stroke/pivot authored; bolt/handle fixed.',fill='white')
    return png(sheet),png(story)

def generate(render=False,evidence=Path('/private/tmp/w183-patron-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=98:raise ValueError('Canonical element drift')
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w183_patron_of_lost_causes.py'),Path('scripts/generate_surface_w123_patron_of_lost_causes.py'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W183',weapon='patron_of_lost_causes',revision=1,itemModel='destiny:'+KEY,
      ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,
      progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
      sourceElements=98,bodyElements=96,movingElements=2,maxAssembledElements=98,cubeElements=98,triangleAdapterElements=0,elementLimit=1000,addedElements=0,
      sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),sourceRevision='W130 semantic 98-solid Patron model, canonical weapon_surface_w123',geometryAndUVPreserved=True,
      partitionIndices={part:[i for i,e in enumerate(source['elements']) if (e['name'] in MAGAZINE_NAMES)==(part=='magazine')] for part in ('body','magazine')},magazineNames=MAGAZINE_NAMES,
      partitionRationale='Canonical indices82 magazine_body and83 magazine_floor form the broad rear bullpup magazine behind pistol grip, under rear action. Move both as ONE rigid part. All96 other elements, including open triangular stock, pistol grip, scope, gold tubes, forward hook and exposed bolt/handle, stay body. Every canonical field/rotation/UV appears exactly once.',
      authoredHiddenDetails='Hand and right screen edge conceal outgoing/replacement exchange. Peak local displacement[-.25,-5.8,.815], grip pivot[8,7.65,8.8], numeric angles and normalized knots authored. Withdrawal approximately follows the canonical -8deg X magazine slant. One intact magazine proxies outgoing/incoming; no scale hiding, duplicates or loose rounds. Existing stock aperture is preserved; no invented hollow magwell.',
      keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAG_ANCHOR,hipEndpoints=[0,20],
      normalizedPhases={'supportReach':[0,.08],'steepLiftAndRearWithdraw':[.08,.30],'verticalExchangeHold':[.30,.42],'rearReplacementAndSeat':[.42,.60],'rapidLower':[.60,.70],'settlingDip':[.70,.80],'hipRecovery':[.80,1]},
      endpointPolicy='Both parts at0/1 use exact canonical display for both hands/grips. Exact canonical ADS/inspect precedence, negative inactive fallback and non-FP graph.',
      reference=REFERENCE,
      motionAuthorship='Inspected SAME Patron: pronounced near-vertical muzzle lift exposes bullpup rear underside, magazine exchange, seating by HUD15, rapid lower, open support-hand forward recovery and small settling dip. Dedicated authored key times, pivot and numeric poses; W182 reused for rigid algebra, graph guard and raster infrastructure only.',
      sourceChronology=[{'stage':'W130','evidence':'scripts/generate_surface_w123_patron_of_lost_causes.py','role':'Canonical98 semantic solids/588 face UVs/default silver-gold dye.'},{'stage':'W182','evidence':'scripts/generate_reload_w182_antiope_d.py','role':'Rigid matrix algebra/graph guards/offline layout infrastructure only; NO trajectory copied.'},{'stage':'W183','evidence':REFERENCE['url'],'role':'Actual named Patron inventory18.018s and continuous reload211.7115-212.7125s.'}],
      timingPolicy='Normalized visuals only. Preserve local magazine15/reload39ticks/rpm200/cadence6ticks/burst1, whole-mag ammo transfer, funding and existing audio. Source HUD/perks/speed do not change local mechanics.',
      rotationConvention='Display JOML Rx Ry Rz; receiver-local rigid magazine translation; constant uniform scale; twohand rigid carrier. Left native ItemTransform reflection F*T*F. Canonical XYZ element rotations decoded by existing Beloved raster helper.',
      nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
      integration={'requiresMasterRouting':True,'workerRuntimeEdited':False,'masterOwnsRegistryRuntime':True,'requiredMasterModel':'destiny:'+KEY,'catalogId':'patron_of_lost_causes',
        'progress':'float1 normalized; boolean0 true=twohand; negative inactive; strings0 ads/inspect take precedence. Master owns admission/routing/lifecycle/ammo/clocks/native.'},
      nativeQueue=['Both FP contexts x both grips: grip contact, steep near-vertical lift, intact rear magazine withdrawal, exchange hold, insertion, seat rock, support recovery, exact endpoints; near-plane and receiver/magazine clearance.',
        'ADS/inspect while progressing; negative inactive; GUI/ground/fixed/head/third-person observer exact canonical graph. No new3P reload or handIK claim.',
        'Partial/empty/full/no-reserve, fire/reload spam, switch/cancel/equip/unequip/death/disconnect; master validates one unchanged ammo transfer and39tick lifecycle.',
        'Master single native session: listen to unchanged reload audio; briefly observe10-20 displays for artifacts/stalls. All native/input/audio/performance rows pending.'],
      canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Expected exact90 outputs')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w183-patron-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w183-manifest.json').read_bytes())['features'] if f['name']=='w183-patron'))
    if not {str(p) for p in output}<=owned:raise SystemExit('Outside exact ownership')
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs/media hashes;87 pack assets;96+2=98 assembled elements; native pending')
if __name__=='__main__':main()
