#!/usr/bin/env python3
"""W189 Coriolis Force central battery exchange. Offline assets, no gameplay changes.
W188 supplies matrix/graph infrastructure only; no W188 geometry or trajectory reused.
"""
import argparse,copy,hashlib,io,json,math,runpy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
A=Path('src/main/resources/assets/destiny')
ART=Path('art/weapons/w189/coriolis_force')
KEY='weapon_reload_w189_coriolis_force/coriolis_force'
SOURCE=A/'models/weapon_surface_w123/coriolis_force.json'
TWOHAND=A/'models/weapon/fusion_rifle/coriolis_force_twohand.json'
ITEM=A/'items/weapon/coriolis_force.json'
TEXTURE=A/'textures/item/weapon/w123/coriolis_force.png'
FP=('firstperson_righthand','firstperson_lefthand')
PARTS=('body','magazine')
GRIPS=('native','twohand')
GRIP=(8.,10.5,7.05)
MAGAZINE_ANCHOR=(8.,10.95,-.52)
MAGAZINE_NAMES=('cartridge_solid','cartridge_upper')
# p, carrier XYZ, common FP shift, central cell offset, cell-local XYZ, twohand view correction.
# n772..856: central cartridge grab -> downward release -> daylight opening -> broad cell up-seat.
# Source viewpoint motion/perk speed is not copied. Rear pistol grip and red surround never detach.
KEYS=(
 (0,(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)),
 (.07,(15,-2,-5),(-.4,.4,-1.1),(0,0,0),(0,0,0),(-1.2,0,0)),
 (.18,(48,-6,-15),(-2,2,-5),(0,0,0),(0,0,0),(-6,0,0)),
 (.25,(47,-7,-16),(-2,2,-5),(0,-.8,0),(-2,0,0),(-6,0,0)),
 (.36,(45,-8,-17),(-2,2,-5),(-1.4,-5.9,.45),(-10,9,-8),(-6,0,0)),
 (.47,(43,-7,-16),(-2,2,-5),(-2.7,-6.6,.7),(-16,18,-12),(-6,0,0)),
 (.56,(44,-6,-15),(-2,2,-5),(-2.1,-5.5,.6),(-12,14,-9),(-6,0,0)),
 (.65,(49,-5,-14),(-2,2,-5),(-.65,-2.8,.2),(-5,5,-3),(-6,0,0)),
 (.74,(55,-4,-13),(-2,2,-5),(0,0,0),(0,0,0),(-6,0,0)),
 (.80,(45,-3,-11),(-1.8,1.8,-4.6),(0,0,0),(0,0,0),(-5.5,0,0)),
 (.90,(17,-1,-5),(-.7,.7,-1.8),(0,0,0),(0,0,0),(-2,0,0)),
 (.97,(2,0,-.5),(-.1,.1,-.2),(0,0,0),(0,0,0),(-.2,0,0)),
 (1,(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)))
PINS={'src/main/resources/assets/destiny/models/weapon_surface_w123/coriolis_force.json': '886a4e969b810a7963f88306446b0fef62355ea3213fcf2feb011a59a6f4c848', 'src/main/resources/assets/destiny/items/weapon/coriolis_force.json': 'bb6752800536cb6ce9dd374eeb274c9880837773600d989c1c7f3330085ffbeb', 'src/main/resources/assets/destiny/textures/item/weapon/w123/coriolis_force.png': '0af64ab784c105af310da00feae21a73d57c76de8bf57e8d2d5e30573e700a8d', 'src/main/resources/destiny/weapons/w46-timing.json': 'e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07', 'src/main/resources/destiny/sounds/w63-reload.json': 'e89b09c8d1402239fa65873b5e96fc7f55d1b3107b753aab8c8d5474bcbb750b', 'src/main/resources/assets/destiny/sounds/w63/reload/weapon_fusion_rifle_reload_45.ogg': '2f57dc824720837b3171fce240df54967365b11b404e62e9258b71deb5440184', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force.json': '70c6f30447cbae2a42dd7c6a3553e352aa6c6d7b61bd900180e8e8e37eaa2eac', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_twohand.json': 'e006c486d92ec92d6508ac2f481ca133df1c4a1623dbc685cdd6ddece1ab2338', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_ads.json': '487cc7d90baefe72288034c5d65b1e332b40bf565ddf001889741fe45e19acc9', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_ads_twohand.json': '451ca2219efc95737966b764a807c4b8fbe13a41e3d1ade1808974f278c787e6', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_inspect.json': '2d0d4c29857c840582d13bb32ad5d092980b3145f90aa7d56bf648d99be04285', 'src/main/resources/assets/destiny/models/weapon/fusion_rifle/coriolis_force_inspect_twohand.json': 'c5da1cefa49b1656e5693135cdbf09ea16c8103c63c05d11e83884eea1072800'}
REFERENCE={'url': 'https://www.youtube.com/watch?v=67wv69MomYQ', 'title': 'CORIOLIS FORCE [Destiny 2 Beyond Light] Full PvP / PvE Weapon Review', 'creator': 'Ironworker Gaming', 'uploadDate': '20201230', 'fpsNumerator': 60, 'fpsDenominator': 1, 'sourceTimebase': '1/15360', 'actionFrameRange': [772, 856], 'actionSeconds': [12.866666666666667, 14.266666666666667], 'sourceVideoFile': '/private/tmp/w189-coriolis-report/original.mp4', 'sourceMetadataFile': '/private/tmp/w189-coriolis-report/original.info.json', 'sourceVideoSha256': '901cd748402a30d0994c8b3d30c3d58c45d6fbbf9b4f23514c1573629f81ebec', 'sourceMetadataSha256': 'b606100d5db6a5e098ec1206b1a88629dba0aecbf098d0c3aed6f9d40e24a74d', 'inspectedActualFrames': True, 'shaderPolicy': 'Basic red/blue/silver identity in inventory and gameplay. No source paint or numeric values imported.', 'frames': [{'path': '/private/tmp/w189-coriolis-report/reference-01.png', 'sha256': '59585b38ff69ade1b9c5e97cebe3b8a9885a32558fa02141060c0cf6eb87c91e', 'sourceFrameIndex': 772, 'pts': 197632, 'timestampSeconds': 12.866666666666667, 'nearestAuthoredProgress': 0, 'observation': 'Hip hold before reload; red cage, blue coupling, twin sight ears and skeletal stock identify Coriolis Force. HUD4.'}, {'path': '/private/tmp/w189-coriolis-report/reference-02.png', 'sha256': '16f2ac0b0dbad2e08e9db7597bfe2ed49c26f144e4f0502d5e3536886ebc355b', 'sourceFrameIndex': 778, 'pts': 199168, 'timestampSeconds': 12.966666666666667, 'nearestAuthoredProgress': 0.07142857142857142, 'observation': 'Muzzle-up presentation starts; support hand opens beneath central cartridge, rear grip retained.'}, {'path': '/private/tmp/w189-coriolis-report/reference-03.png', 'sha256': '5b2d50ba3e2d7d7d6be8bfa46e8f25162c88bc1f082f2d24916c50b54e1d6922', 'sourceFrameIndex': 784, 'pts': 200704, 'timestampSeconds': 13.066666666666666, 'nearestAuthoredProgress': 0.14285714285714285, 'observation': 'Support hand closes around dark central cell inside triangular red surround.'}, {'path': '/private/tmp/w189-coriolis-report/reference-04.png', 'sha256': 'f8b553c6019aa742d06b8fd3d5b2c81e0be02cfdf4f6808d628bb8bd93e8733e', 'sourceFrameIndex': 790, 'pts': 202240, 'timestampSeconds': 13.166666666666666, 'nearestAuthoredProgress': 0.21428571428571427, 'observation': 'Whole dark cartridge withdraws downward from central socket; red structural outline stays attached.'}, {'path': '/private/tmp/w189-coriolis-report/reference-05.png', 'sha256': '934738baccca60f02ca67a91fa0f6a84390af23cd53d63fd0fb92b4c5ba3b8b8', 'sourceFrameIndex': 796, 'pts': 203776, 'timestampSeconds': 13.266666666666667, 'nearestAuthoredProgress': 0.2857142857142857, 'observation': 'Dark cell leaves opening; receiver, side clamp, rear grip and skeletal stock remain fixed.'}, {'path': '/private/tmp/w189-coriolis-report/reference-06.png', 'sha256': '0531949f0f2e7f0155661ed0715db77a6631ecab2f4af9df530d1637c408ecc0', 'sourceFrameIndex': 802, 'pts': 205312, 'timestampSeconds': 13.366666666666667, 'nearestAuthoredProgress': 0.35714285714285715, 'observation': 'Central rectangular daylight opening is exposed; outgoing cell passes below support hand.'}, {'path': '/private/tmp/w189-coriolis-report/reference-07.png', 'sha256': '07a0c86eaf29314c3bc1eb756ef6b86039983a88f9fb66fa93ba492af1a23a03', 'sourceFrameIndex': 808, 'pts': 206848, 'timestampSeconds': 13.466666666666667, 'nearestAuthoredProgress': 0.42857142857142855, 'observation': 'Empty red-surrounded central opening; slight whole-weapon rock while held muzzle-up.'}, {'path': '/private/tmp/w189-coriolis-report/reference-08.png', 'sha256': '1414f0b9fd72e8bebd43639c5da5f49be5a3a0468ebaadd0d6284546c83d7dd0', 'sourceFrameIndex': 814, 'pts': 208384, 'timestampSeconds': 13.566666666666666, 'nearestAuthoredProgress': 0.5, 'observation': 'Empty socket held at right; support hand below frame prepares replacement.'}, {'path': '/private/tmp/w189-coriolis-report/reference-09.png', 'sha256': 'cc762e89d175b88c0816a6557990122ae50a1b9fa0be5b51dca8d7c648e5d8be', 'sourceFrameIndex': 820, 'pts': 209920, 'timestampSeconds': 13.666666666666666, 'nearestAuthoredProgress': 0.5714285714285714, 'observation': 'Clear empty central opening, fixed upper red triangle and bottom surround visible.'}, {'path': '/private/tmp/w189-coriolis-report/reference-10.png', 'sha256': '61f785fba085a2ed0fbe0b6944f0cc5585868ff5b7917015f4503fbc998ed3e9', 'sourceFrameIndex': 826, 'pts': 211456, 'timestampSeconds': 13.766666666666667, 'nearestAuthoredProgress': 0.6428571428571429, 'observation': 'Broad dark replacement rises from below left, supported by left palm; insertion is into central bay, not grip heel.'}, {'path': '/private/tmp/w189-coriolis-report/reference-11.png', 'sha256': '545a7f3cde93af15886761b6fe73bc0083cd19d30371302d31d91026332954cb', 'sourceFrameIndex': 832, 'pts': 212992, 'timestampSeconds': 13.866666666666667, 'nearestAuthoredProgress': 0.7142857142857143, 'observation': 'Replacement nearly fills opening as palm drives it upward; fixed red surround remains visible.'}, {'path': '/private/tmp/w189-coriolis-report/reference-12.png', 'sha256': 'ad228792672ce3f0e74b41377b6d640420e41c36966d0926f118178605ec3b5f', 'sourceFrameIndex': 838, 'pts': 214528, 'timestampSeconds': 13.966666666666667, 'nearestAuthoredProgress': 0.7857142857142857, 'observation': 'Dark cartridge seated; HUD4 becomes7 in perked source footage.'}, {'path': '/private/tmp/w189-coriolis-report/reference-13.png', 'sha256': 'f2390dfcf73733623ab97cb4d8f44db4cb7fde6a81079a55000a67ff409cb9f8', 'sourceFrameIndex': 844, 'pts': 216064, 'timestampSeconds': 14.066666666666666, 'nearestAuthoredProgress': 0.8571428571428571, 'observation': 'Weapon lowers and support hand returns forward after seating.'}, {'path': '/private/tmp/w189-coriolis-report/reference-14.png', 'sha256': 'b2b2ba0a477a3c1e8bef5574f719d80270b31147ce5cda456cf34c4fda632ae8', 'sourceFrameIndex': 850, 'pts': 217600, 'timestampSeconds': 14.166666666666666, 'nearestAuthoredProgress': 0.9285714285714286, 'observation': 'Recovery toward horizontal hip hold, complete red silhouette restored.'}, {'path': '/private/tmp/w189-coriolis-report/reference-15.png', 'sha256': '7e39650131819e4bfbfc9bdafa4f27f257a6bec3186daca63e0c20970eb54edf', 'sourceFrameIndex': 856, 'pts': 219136, 'timestampSeconds': 14.266666666666667, 'nearestAuthoredProgress': 1, 'observation': 'Recovered hip hold with HUD7; subsequent sprint excluded from authored motion.'}, {'path': '/private/tmp/w189-coriolis-report/reference-16.png', 'sha256': '2db2bb2b58aaec346481c77bc459dda88593f3bc53779a399932751595f7841c', 'sourceFrameIndex': 6300, 'pts': 1612800, 'timestampSeconds': 105.0, 'nearestAuthoredProgress': 0, 'observation': 'Inventory explicitly CORIOLIS FORCE in basic red/blue/silver appearance; used solely for identity.'}]}
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
    if not math.isfinite(p) or not 0 <= p <= 1:raise ValueError(p)
    for a,b in zip(KEYS,KEYS[1:]):
        if p<=b[0]:
            t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple([a[k][i]+(b[k][i]-a[k][i])*t for i in range(3)] for k in range(1,6))
    raise ValueError(p)

def is_payload(e):return e['name'] in MAGAZINE_NAMES

def partition(source):
    return {part:{**{k:copy.deepcopy(v) for k,v in source.items() if k!='elements'},
                  'elements':[copy.deepcopy(e) for e in source['elements'] if is_payload(e)==(part=='magazine')]}
            for part in PARTS}

def pose_display(original,twohand,p,part,grip):
    if part not in PARTS or grip not in GRIPS:raise ValueError((part,grip))
    accepted=original if grip=='native' else twohand
    if p in (0,1):return copy.deepcopy(accepted)
    angles,shift,offset,cell_angles,correction=sample(p)
    motion=xyz(angles);pivot=sub(GRIP,(8,8,8));anchor=sub(MAGAZINE_ANCHOR,(8,8,8))
    local=sub(pivot,vec(motion,pivot));part_motion=motion
    if part=='magazine':
        cell=xyz(cell_angles)
        local=add(local,vec(motion,add(offset,sub(anchor,vec(cell,anchor)))))
        part_motion=mul(motion,cell)
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);scale=idle['scale']
        if twohand[context]['scale']!=scale or len(set(scale))!=1:raise ValueError('Expected equal uniform canonical scales')
        rotation=mul(base,part_motion)
        position=add(add(idle['translation'],shift),vec(base,[scale[0]*v for v in local]))
        if grip=='twohand':
            carrier=mul(xyz(twohand[context]['rotation']),transpose(base))
            position=add(add(vec(carrier,position),sub(twohand[context]['translation'],vec(carrier,idle['translation']))),correction)
            rotation=mul(carrier,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in PARTS}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(21) for part in PARTS for grip in GRIPS)
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}

def geometry_points(model):
    import itertools
    points=[]
    for e in model['elements']:
        rr=e.get('rotation',{});angles=[rr.get(a,0) for a in 'xyz']
        if 'axis' in rr:angles['xyz'.index(rr['axis'])]=rr['angle']
        matrix=np.asarray(xyz(angles));origin=np.asarray(rr.get('origin',[8]*3))
        corners=np.asarray(list(itertools.product(*zip(e['from'],e['to']))))
        points.extend((corners-origin)@matrix.T+origin)
    return np.asarray(points)

def viewport_proxy(output):
    # Conservative perspective check of the ACTUAL emitted cell points. Vanilla-like arm base,
    # 70-degree vertical FOV / 16:9. This is an offline proxy, not the GCB hand/camera pipeline.
    cell=json.loads(output[A/f'models/{KEY}_magazine.json']);points=geometry_points(cell)
    rows=[]
    for i in range(4,16):
        for grip in GRIPS:
            for hand in FP:
                d=json.loads(output[A/f'models/{KEY}_{i:02}_magazine_{grip}.json'])['display'][hand]
                q=points-8
                if hand==FP[1]:q=q.copy();q[:,0]*=-1
                q=(q*np.asarray(d['scale']))@np.asarray(xyz(d['rotation'])).T+np.asarray(d['translation'])
                if hand==FP[1]:q[:,0]*=-1
                q=q/16+np.array([.56 if hand==FP[0] else -.56,-.52,-.72])
                ndc=q[:,:2]/(-q[:,2,None]*math.tan(math.radians(35)))
                ndc[:,0]/=16/9
                inside=(np.abs(ndc[:,0])<1)&(np.abs(ndc[:,1])<1)&(q[:,2]<0)
                rows.append(dict(frame=i,grip=grip,hand=hand,visibleCorners=int(sum(inside)),corners=len(inside),ndcBounds=[ndc.min(0).tolist(),ndc.max(0).tolist()]))
    return dict(policy='Offline perspective proxy only: arm base +/-0.56,-0.52,-0.72; vertical70 FOV;16:9. Native GCB transforms/hand occlusion pending.',samples=rows,minVisibleCornerFraction=min(r['visibleCorners']/r['corners'] for r in rows))

def previews(output,evidence):
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    def posed(i,grip='native',hand=FP[0],canonical=False,detail=False):
        ts=[]
        for part in PARTS:
            model=json.loads(output[A/f'models/{KEY}_{part}.json'])
            if detail:model['elements']=[e for e in model['elements'] if e['name'] in MAGAZINE_NAMES+('triangle_front','triangle_upper','triangle_rear','triangle_bottom','cartridge_floor','cartridge_front_toe')]
            d=json.loads(output[A/f'models/{KEY}_{i:02}_{part}_{grip}.json'])['display'][hand]
            for pts,uv,tex,n in helper['model_triangles']({'part':model},texture):
                points=np.asarray(pts).copy();n=np.asarray(n).copy()
                if not canonical:
                    points-=8
                    if hand==FP[1]:points[:,0]*=-1;n[0]*=-1
                    rr=np.asarray(xyz(d['rotation']));points=(points*np.asarray(d['scale']))@rr.T+np.asarray(d['translation']);n=rr@n
                    if hand==FP[1]:points[:,0]*=-1;n[0]*=-1
                ts.append((points,uv,tex,n))
        return ts
    def extent(gs,cam,w,h):return helper['frame'](np.concatenate([t[0] for g in gs for t in g]),cam,w,h)
    def raster(g,cam,w,h,ext=None):return helper['render'](g,cam,ext if ext is not None else extent([g],cam,w,h),(w,h))[0]
    sheet=Image.new('RGB',(1600,1860),'#111925');dr=ImageDraw.Draw(sheet)
    dr.text((14,12),'W189 CORIOLIS FORCE | emitted textured JSON | OFFLINE / NO HANDS / NOT NATIVE',fill='white')
    for col,cam in enumerate(([1,0,0],[.9,.5,-.7],[-1,.4,.6],[.2,.45,1])):
        sheet.paste(raster(posed(0,canonical=True),cam,400,280),(col*400,60));dr.text((col*400+8,40),('side','front oblique','reverse oblique','rear')[col],fill='white')
    cam=[1,.25,.5];gs=[posed(i) for i in (0,8,13,20)];ext=extent(gs,cam,400,320)
    for col,(i,g) in enumerate(zip((0,8,13,20),gs)):
        sheet.paste(raster(g,cam,400,320,ext),(col*400,390));dr.text((col*400+8,367),f'p={i/20:.2f} / fixed camera + scale',fill='white')
    gs=[posed(i,detail=True) for i in (0,7,10,15)];cam=[1,.2,.1];ext=extent(gs,cam,400,320)
    for col,(i,g) in enumerate(zip((0,7,10,15),gs)):
        sheet.paste(raster(g,cam,400,320,ext),(col*400,760));dr.text((col*400+8,735),f'CENTRAL CELL / RED SURROUND FIXED p={i/20:.2f}',fill='white')
    configs=[('native',FP[0]),('native',FP[1]),('twohand',FP[0]),('twohand',FP[1])]
    gs=[posed(10,g,h) for g,h in configs];cam=[0,0,1];ext=extent(gs,cam,400,400)
    for col,((grip,hand),g) in enumerate(zip(configs,gs)):
        sheet.paste(raster(g,cam,400,400,ext),(col*400,1130));dr.text((col*400+8,1105),grip+' / '+hand.replace('firstperson_',''),fill='white')
    lines=['104 original elements = 102 fixed + 2 central cell solids. No added stem, geometry/UV/base paint edits or shrinking.',
           'Source: Ironworker Gaming / 67wv69MomYQ / n772..856 / 60fps /12.86667..14.26667s. Source perks do not change local timings.',
           'Observed: grasp central black cartridge, pull down, expose daylight opening, broad replacement rises from below-left, palm seat, lower.',
           'Authored: pivot, angles, cell roll/yaw, pull distance and near-camera framing. Whole red triangle/floor, grip, stock and U clamp stay fixed.',
           'Common FP shift (-2,+2,-5) during exchange; twohand correction(-6,0,0). Constant accepted scale; same carrier in both hands.',
           'Perspective viewport proxy retained in manifest; actual camera/hand fit, audio and pack load remain master-owned.',
           'Exact0/1, negative/overshoot/nonFP/ADS/inspect use canonical graph. Local45ticks/6rounds/667ms/7bolt volley/audio unchanged.']
    for j,line in enumerate(lines):dr.text((14,1560+36*j),line,fill='white')
    story=Image.new('RGB',(1600,3380),'#111925');dr=ImageDraw.Draw(story)
    dr.text((14,12),'ACTUAL CORIOLIS FORCE / source frames above; independently authored emitted samples below / OFFLINE',fill='white')
    cam=[1,.25,.5];allgs=[posed(i) for i in range(21)];ext=extent(allgs,cam,400,310)
    for j,f in enumerate(REFERENCE['frames']):
        path=evidence/Path(f['path']).name
        if sha(path.read_bytes())!=f['sha256']:raise ValueError('Reference drift: '+str(path))
        im=Image.open(path).convert('RGB');im.thumbnail((400,225));x=j%4*400;y=55+j//4*640
        story.paste(im,(x,y));dr.text((x+8,y+230),f"SOURCE n{f['sourceFrameIndex']} PTS{f['pts']} / {f['timestampSeconds']:.5f}s",fill='white')
        # Wrap observed notes, no invented source directions hidden in a caption.
        import textwrap
        for k,line in enumerate(textwrap.wrap(f['observation'],62)):dr.text((x+8,y+248+14*k),line,fill='white')
        i=round(f['nearestAuthoredProgress']*20)
        story.paste(raster(allgs[i],cam,400,310,ext),(x,y+320));dr.text((x+8,y+610),f'AUTHORED p={i/20:.2f} / same camera+extent',fill='white')
    dr.text((14,2640),'No animation/bones extracted. Source Feeding Frenzy/enhanced battery timing normalized only; local45tick reload unchanged. Native pending.',fill='white')
    dr.text((14,2690),'ALL21 EMITTED SAMPLES / native-right representative / fixed camera+extent / other hand+grip transforms checked separately',fill='white')
    ext=extent(allgs,cam,228,192)
    for i,g in enumerate(allgs):
        x=i%7*228;y=2730+i//7*212
        story.paste(raster(g,cam,228,192,ext),(x,y));dr.text((x+8,y+193),f'{i:02d} / p={i/20:.2f}',fill='white')
    return png(sheet),png(story)

def generate(render=False,evidence=Path('/private/tmp/w189-coriolis-report')):
    for path,digest in PINS.items():
        if sha((ROOT/path).read_bytes())!=digest:raise ValueError('Canonical drift: '+path)
    source=json.loads((ROOT/SOURCE).read_bytes());two=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if len(source['elements'])!=104:raise ValueError('Canonical element drift')
    parts=partition(source);output={}
    def emit(p,v):output[p]=encode(v)
    for part,model in parts.items():emit(A/f'models/{KEY}_{part}.json',model)
    entries=[]
    for i in range(21):
        p=i/20
        for part in PARTS:
            for grip in GRIPS:emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],two,p,part,grip)))
        def composite(grip):return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in PARTS])
        model=copy.deepcopy(item['model']) if i in (0,20) else dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))
        entries.append(dict(threshold=p,model=model))
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
    inputs=[SOURCE,TWOHAND,ITEM,TEXTURE,Path('scripts/generate_reload_w189_coriolis_force.py'),Path('scripts/qa/test_reload_w189_coriolis_force.py'),Path('src/test/java/kim/biryeong/destiny/weapon/ReloadW189CoriolisTest.java'),ART/'SOURCE.md']
    emit(ART/'manifest.json',dict(stage='W189',weapon='coriolis_force',revision=1,itemModel='destiny:'+KEY,
        ownedFiles=94,generatedFiles=90,packFiles=87,staticParts=2,parentDisplayChildren=84,frames=21,progressFloatIndex=1,gripFlagIndex=0,firstPersonContexts=list(FP),
        sourceElements=104,bodyElements=102,movingElements=2,maxAssembledElements=104,endpointAssembledElements=104,elementLimit=1000,addedElements=0,triangleAdapterElements=0,
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),partitionIndices=indices,
        geometryPolicy='All104 canonical cuboids/624faces/rotations/UV/basic dye preserved exactly. Central cartridge_solid60 and cartridge_upper61 move; all red surround/floor/toe, rear grip, stock and U clamp fixed.',
        payloadPolicy='Two original dark central cell solids, rotating rigidly around their upper anchor; no invented grip battery or hidden shaft. One cell proxies outgoing and incoming, no duplicate simultaneous cell.',
        sourceLimitation=dict(exactOriginalCellPathVerified=False,canonicalMovingNames=list(MAGAZINE_NAMES),canonicalMovingIndices=[60,61],resolution='Actual source n772..856 exposes daylight central opening and broad incoming black cell. Static rip stores this region in broad main mesh, not a named moving bone; hidden path and upper cell/socket boundary authored.'),
        semanticGroups=dict(body=102,centralCell=2,fixed=['cartridge_floor','cartridge_front_toe','triangle_front','triangle_upper','triangle_rear','triangle_bottom','rear_grip','grip_heel','rear_receiver','u_clamp_floor']),
        keyframes=KEYS,gripPivot=GRIP,magazineAnchor=MAGAZINE_ANCHOR,hipEndpoints=[0,20],
        normalizedPhases=dict(lift=[0,.18],grasp=[.18,.25],withdraw=[.25,.36],exchange=[.36,.56],incoming=[.56,.74],seat=[.74,.80],lower=[.80,.97],recover=[.97,1]),
        endpointPolicy='Exact0/1 and overshoot use original full item graph. Negative/nonFP/ADS/inspect preserve canonical. Children0/20 use exact accepted displays.',
        framingPolicy='Authored common FP(-2,+2,-5), plus twohand(-6,0,0), blends in/out. Constant scale, steep-pose central exchange pulled inward/farther/up. Perspective proxy is not native acceptance.',
        viewportProxy=viewport_proxy(output),reference=REFERENCE,
        ripProvenance=dict(sourceFiles={'Coriolis Force.blend':'0dae83591d8befbd1ef35b2bb56f4f2212bab88989646515a1e55b9a4c3b7abf'},mapping='native=[world.X,world.Z,world.Y]*41.469411629369226+[8,8,8]',acceptedTriangles=13801,texturedTriangles=13799,inertBlendRead=True,mainObject='Coriolis-Force.00.001',cellStoredAsSeparateObject=False,animationExtracted=False),
        referencePolicy='Actual same-weapon Ironworker Gaming continuous reload n772..856 plus basic-dye inventory n6300; decoded PTS/frame hashes. Internet text was discovery only, never mechanism evidence.',
        authoredPolicy='Independent central-cell geometry partition, carrier pivot, lower-left withdrawal, local cell turn and palm-seat presentation. W188 codec/matrix/graph and W123 raster scaffolding only; W188 trajectory not reused.',
        timingPolicy='Existing6rounds/45ticks/667ms charge/14charge ticks/7bolt shared-ammo volley and reload audio unchanged.21samples normalized to existing clock. Source Feeding Frenzy x2 and enhanced battery not imported. DDC numeric priority; no numeric delta and no basic/enhanced/PvE/PvP inference or ? replacement.',
        rotationConvention='JOML Rx Ry Rz. Cell local rotation around magazineAnchor precedes carrier motion around gripPivot; left ItemTransform F*T*F; constant canonical scale.',
        nativeGameplayVerified=False,thirdPersonReloadClaimed=False,handIK=False,extractedAnimation=False,extractedBones=False,mechanicsOrAudioChanged=False,
        integration=dict(workerRuntimeEdited=False,masterOwnsRegistryRuntime=True,requiredMasterModel='destiny:'+KEY,catalogId='coriolis_force',assetInputs='float[1] progress; boolean[0] grip; string[0] ads/inspect; master admission/lifecycle.'),
        nativeQueue=['Master route/admit coriolis_force to itemModel; retain45tick/6round/667ms/7bolt shared-ammo clock and audio.', 'Both FP hands/native+two_hand at p0,.15,.35,.50,.65,.75,.90,1: central cell on-screen; red surround stays fixed; socket/palm alignment; no floor/stock/grip detachment.', 'Exact0/1 negative/overshoot/nonFP ADS/inspect fallback; partial/empty/no-reserve; cancel/equip/switch/death/disconnect.', 'One native pack load, audio listening, representative1p/3p and10-20display observation pending master.'],
        canonicalSha256=PINS,sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths() or len(output)!=90:raise ValueError('Output set must be exact90')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');ap.add_argument('--render',action='store_true');ap.add_argument('--evidence',type=Path,default=Path('/private/tmp/w189-coriolis-report'));args=ap.parse_args()
    output=generate(args.render,args.evidence)
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b:raise SystemExit('Asset differs: '+str(p))
        else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs;87 pack assets;102+2=104 original elements;native pending')
if __name__=='__main__':main()
