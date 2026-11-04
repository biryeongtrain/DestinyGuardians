#!/usr/bin/env python3
"""W130 Patron of Lost Causes: hand-authored solid volumes and opaque per-face paint.
Read-only reference parsing/raster helpers; writes only this worker's batch files.
"""
import argparse
import base64
import collections
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
ART='art/weapons/w123/patron_of_lost_causes/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+'models/weapon/scout_rifle/patron_of_lost_causes.json'
MODEL=ASSET+'models/weapon_surface_w123/patron_of_lost_causes.json'
TEXTURE=ASSET+'textures/item/weapon/w123/patron_of_lost_causes.png'
BB='art/blockbench/weapons/w30/patron_of_lost_causes.bbmodel'
RAW=Path('/tmp/destiny-weapons-w30/raw/patron_of_lost_causes/extracted/Patron of Lost Causes')
PHOTO=Path('/tmp/destiny-weapons-w31/references/patron_of_lost_causes.jpg')
REPORT='docs/qa/2026-10-26/w130/patron_of_lost_causes-worker.md'
EDGE=1024
FACES={'north':(3,2,0,1),'south':(6,7,5,4),'west':(2,6,4,0),'east':(7,3,1,5),'up':(2,3,7,6),'down':(4,5,1,0)}
PALETTE={'silver':[187,192,194],'bright':[211,214,215],'steel':[94,103,110], 'black':[30,34,39],'rubber':[22,25,28],'gold':[178,133,66],'gold_edge':[208,168,94],'lens':[25,29,48]}
_HELPER=None

def helper():
    global _HELPER
    if _HELPER is None:_HELPER=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_beloved.py'))
    return _HELPER

def sha(b):return hashlib.sha256(b).hexdigest()
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w130:patron_of_lost_causes:'+s))
def vertices(e):return helper()['vertices'](e)

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha((RAW/'Patron of Lost Causes.fbx').read_bytes())==meta['source_files']['Patron of Lost Causes/Patron of Lost Causes.fbx']
    roots=helper()['parse_fbx'](RAW/'Patron of Lost Causes.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    mats={n[1][0]:n[1][1].split('\x00')[0] for n in objects if n[0]=='Material'}
    meshes=[]
    for n in objects:
        if n[0]!='Geometry':continue
        model=models[next(p for c,p in links if c==n[1][0])];name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=1e-4)
        assert np.allclose(props.get('Lcl Translation',[0,0,0]),[0,0,0],atol=1e-6)
        assert props['Lcl Scaling']==[100,100,100]
        ch={c[0]:c for c in n[2]};raw=np.array(ch['Vertices'][1][0]).reshape(-1,3)
        points=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
        fs=[];face=[]
        for i in ch['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3
                fs.append(face);face=[]
        layer=next(c for c in n[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        uvdata={c[0]:c[1][0] for c in layer[2]}
        assert uvdata['MappingInformationType']=='ByPolygonVertex'
        uv=np.array(uvdata['UV']).reshape(-1,2)[np.array(uvdata['UVIndex'])].reshape(-1,3,2)
        material=next(mats[c] for c,p in links if p==model[1][0] and c in mats)
        meshes.append(dict(name=name,vertices=points,faces=np.array(fs),uv=uv,material=material))
    p=np.concatenate([m['vertices'] for m in meshes])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==29158
    assert np.allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=1e-5)
    return meshes,meta

def make_design(meta):
    """Weapon-specific authored solids; source vertices are reference only."""
    specs=[]
    def box(group,name,c,size,material,angles=(0,0,0),motif='panel'):
        c=np.array(c,float);s=np.array(size,float)
        specs.append(dict(group=group,material=material,motif=motif,kind='opaque_solid_cuboid',geometry={
            'name':name,'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist(),
            'rotation':dict(origin=c.tolist(),**dict(zip('xyz',angles)))}))
    def beam(group,name,a,b,width,depth,material,motif='panel'):
        a=np.array(a,float);b=np.array(b,float);v=b-a;assert v[0]==0
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],material,
            (round(math.degrees(math.atan2(v[2],v[1])),6),0,0),motif)
    def tube(group,name,z0,z1,y,r,t,material,motif='tube'):
        # Eight thick, individually editable tangent solids; center remains open.
        for i in range(8):
            a=i*45;q=math.radians(a);rc=r-t/2
            box(group,f'{name}_{i}',[8-rc*math.sin(q),y+rc*math.cos(q),(z0+z1)/2],
                [2*r*math.tan(math.pi/8)+.008,t,z1-z0],material,(0,0,a),motif)
    # Long exposed gold barrel. The muzzle is an actual deep octagonal bore.
    tube('barrel','exposed_barrel',-8.53,-2.30,10.52,.31,.13,'gold','barrel')
    tube('muzzle','threaded_muzzle',-8.93233,-8.48,10.52,.35,.13,'gold','threads')
    box('muzzle','bore_backstop',[8,10.52,-7.58],[.35,.35,.08],'black',motif='bore')
    box('barrel','chamber_collar',[8,10.52,-2.12],[1.03,1.02,.52],'black',motif='collar')
    for side in (-1,1):
        box('barrel',f'collar_shoulder_{side}',[8+side*.48,10.57,-2.10],[.23,.74,.44],'silver',(0,0,side*22.5),'collar')
    # Long upper silver casing: a filled broad core with continuous bevel shoulders.
    box('shroud','long_silver_upper',[8,11.64,1.47],[1.18,.60,7.50],'silver',motif='upper')
    box('shroud','upper_crown',[8,11.99,1.50],[.76,.22,7.45],'bright',motif='upper_top')
    for side in (-1,1):
        box('shroud',f'upper_shoulder_{side}',[8+side*.50,11.92,1.48],[.34,.34,7.48],'silver',(0,0,side*45),'upper')
    box('shroud','front_cap',[8,11.51,-2.25],[1.30,.79,.45],'silver',motif='cap')
    box('shroud','nose_recess',[8,11.51,-2.489],[.47,.43,.035],'black',motif='nose')
    # The internal gold tube is seen through a real open-sided receiver cradle.
    box('internal_tube','gold_internal_core',[8,10.98,1.59],[.55,.42,6.63],'gold',motif='tube')
    for side in (-1,1):
        box('internal_tube',f'gold_internal_bevel_{side}',[8+side*.23,11.00,1.59],[.23,.23,6.63],'gold_edge',(0,0,45*side),'tube')
    box('forearm','black_lower_chassis',[8,10.10,1.25],[1.36,.51,6.50],'black',motif='vents')
    box('forearm','chassis_upper_rail',[8,10.46,1.14],[1.32,.21,6.55],'black',motif='rail')
    for z,tag in ((-1.87,'nose'),(1.40,'middle'),(4.55,'rear')):
        box('forearm','cradle_bridge_'+tag,[8,10.98,z],[1.30,1.15,.28],'black',motif='collar')
    box('forearm','lower_silver_forearm',[8,9.46,.90],[1.14,.66,5.83],'silver',motif='forearm')
    for side in (-1,1):
        box('forearm',f'forearm_edge_{side}',[8+side*.49,9.79,.90],[.22,.24,5.83],'steel',(0,0,45*side),'panel')
    # Top receiver has a physical trough below the scope, not a dark painted oval.
    box('receiver','scope_well_floor',[8,11.48,6.73],[1.38,.32,3.08],'steel',motif='well')
    for side in (-1,1):
        box('receiver',f'scope_well_wall_{side}',[8+side*.61,11.72,6.73],[.25,.47,3.08],'silver',motif='receiver')
    box('receiver','rear_silver_shell',[8,11.45,10.19],[1.49,1.13,3.88],'silver',motif='receiver')
    box('receiver','rear_crown',[8,12.02,10.00],[1.06,.19,3.52],'bright',motif='crown')
    box('receiver','action_underside',[8,10.06,5.96],[1.32,.47,3.43],'black',motif='action')
    box('receiver','port_sill',[8,10.49,7.12],[1.47,.18,2.40],'steel',motif='sill')
    box('receiver','exposed_bolt',[8,10.88,7.18],[.69,.20,2.16],'gold',motif='bolt')
    # The port above the sill is actual air. A charging handle projects on its source side.
    box('receiver','charging_stem',[8.83,10.87,7.72],[.72,.17,.22],'gold',motif='bolt')
    box('receiver','charging_knob',[9.25,10.88,7.72],[.49,.25,.39],'black',motif='knob')
    # Recessed optic. Continuous octagonal walls, independent dark rear eyecup.
    tube('scope','silver_scope',4.724,7.54,12.80,.48,.105,'silver','scope')
    tube('scope','rear_eyecup',7.50,7.991,12.80,.49,.12,'black','eyecup')
    box('scope','front_recessed_glass',[8,12.80,5.17],[.76,.76,.055],'lens',motif='lens')
    box('scope','rear_recessed_glass',[8,12.80,7.63],[.75,.75,.055],'lens',motif='lens')
    box('scope','scope_mount_front',[8,12.10,5.67],[.63,.64,.39],'black',motif='mount')
    box('scope','scope_mount_rear',[8,12.10,7.08],[.63,.64,.39],'black',motif='mount')
    for side in (-1,1):
        box('scope',f'optic_control_block_{side}',[8+side*.40,12.38,6.40],[.15,.29,1.40],'black',motif='optic_controls')
    # Rear stock. Wide structural solids enclose a large through-opening.
    box('stock','stock_silver_comb',[8,11.20,13.86],[1.28,.76,3.66],'silver',(-5,0,0),'comb')
    box('stock','stock_rear_web',[8,9.85,14.19],[1.14,1.91,2.76],'black',(-18,0,0),'stock_web')
    beam('stock','aperture_rear_post',[8,7.66,11.37],[8,10.80,12.02],1.13,.54,'black','stock_ribs')
    beam('stock','lower_diagonal_brace',[8,6.71,9.14],[8,8.88,15.77],1.19,.48,'black','stock_lower')
    beam('stock','butt_spine',[8,7.93,15.66],[8,12.17,15.88],1.25,.36,'black','butt')
    box('stock','butt_heel',[8,7.94,15.86],[1.30,.37,.48],'rubber',(-10,0,0),'butt')
    box('stock','butt_crown',[8,12.03,15.84],[1.28,.49,.43],'black',(-15,0,0),'butt')
    for side in (-1,1):
        box('stock',f'rear_silver_cheek_{side}',[8+side*.64,10.45,14.07],[.20,.91,3.18],'silver',(-18,0,0),'rear_cheek')
    # Sloped solid grip is in the existing hand-contact region (no recenter).
    beam('grip','pistol_grip',[8,6.86,9.18],[8,8.16,8.555],1.12,1.05,'rubber','grip')
    beam('grip','silver_grip_shoulder',[8,8.16,8.555],[8,9.98,7.68],1.12,1.05,'silver','grip_shoulder')
    box('grip','grip_heel',[8,6.86,9.18],[1.15,.37,.92],'black',(-26,0,0),'grip')
    beam('grip','grip_backstrap',[8,7.00,9.56],[8,10.16,8.07],1.19,.19,'silver','stock_ribs')
    # Magazine remains part of the full representation, exactly one resource.
    box('magazine','magazine_body',[8,6.97,12.14],[1.31,2.75,2.53],'black',(-8,0,0),'magazine')
    box('magazine','magazine_floor',[8,5.64,11.95],[1.39,.22,2.71],'steel',(-8,0,0),'magazine_floor')
    # Trigger and guard are solids around an empty finger space.
    beam('guard','guard_front',[8,8.58,5.87],[8,9.94,5.78],.38,.19,'steel','guard')
    beam('guard','guard_bottom',[8,8.53,6.05],[8,8.40,6.89],.38,.20,'steel','guard')
    beam('guard','guard_rear',[8,8.40,6.89],[8,9.72,7.60],.38,.20,'steel','guard')
    beam('guard','guard_toe',[8,8.56,5.42],[8,8.53,6.05],.42,.17,'black','guard')
    beam('guard','trigger',[8,8.88,6.70],[8,9.95,6.63],.20,.16,'black','trigger')
    # Underslung forward rod, clamp, and the signature inward-curved hook.
    box('hook','underbarrel_rod',[8,9.62,-2.47],[.31,.31,2.42],'steel',motif='rod')
    box('hook','rod_clamp',[8,9.62,-3.64],[.79,.83,.48],'black',motif='hook_mount')
    box('hook','gold_clamp_axle',[8,9.62,-3.90],[.37,.39,.08],'gold',motif='axle')
    beam('hook','hook_root',[8,9.24,-3.65],[8,8.79,-3.57],.29,.36,'steel','hook')
    beam('hook','hook_belly',[8,8.86,-3.57],[8,8.24,-3.48],.24,.30,'black','hook')
    beam('hook','hook_curve',[8,8.28,-3.48],[8,7.64,-3.57],.19,.23,'black','hook')
    beam('hook','hook_tip',[8,7.70,-3.56],[8,7.29,-3.82],.11,.12,'steel','hook')
    for side in (-1,1):
        box('hook',f'rod_saddle_{side}',[8+side*.40,10.03,-3.61],[.14,.88,.19],'steel',motif='saddle')
    groups=dict(collections.Counter(s['group'] for s in specs))
    return dict(id='patron_of_lost_causes',stage='W130',family='scout_rifle',revision='semantic-solids-default-silver-gold-v1',
        coordinate_mapping='[8+raw.X*s,8+raw.Z*s,8+raw.Y*s]; muzzle -Z, width X, up Y',anchor=meta['anchor'],scale=meta['scale'],
        source_metadata=meta,solids=specs,groups=groups,full_only=True,
        identity=['silver long upper casing and optic','black triangular open stock','gold barrel and internal tube','small gold XIV','forward curved underside hook'],
        openings={'stock_aperture':{'probe':[8,9.25,10.45],'direction':'X'},
                  'scope_front_recess':{'probe':[8,12.8,4.91],'direction':'Z','backstop_z':5.1425},
                  'scope_rear_recess':{'probe':[8,12.8,7.85],'direction':'Z','backstop_z':7.6575},
                  'muzzle_bore':{'probe':[8,10.52,-8.80],'direction':'Z','backstop_z':-7.62},
                  'trigger_space':{'probe':[8,9.08,6.20],'direction':'X'},
                  'scope_well':{'probe':[8.40,12.02,7.85],'direction':'X'}},
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in [BB,BASE,'art/weapons/w31/references.json','src/main/resources/assets/destiny/textures/item/weapon/w30/patron_of_lost_causes.png','scripts/generate_surface_w123_beloved.py']},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in [RAW/'Patron of Lost Causes.fbx',RAW/'46a6eb80_Diffuse.png',PHOTO]},
        limitations=['Faceted tube cross sections and hook; shallow vents, fasteners and ribs are UV paint.',
            'Default photo guides opaque albedo; no dynamic metal/PBR/glass recreation.',
            'Full only; native substitution, parser, first/third person, ADS, generic reload, audio and 10-20 displays pending master.'])


def tile(spec,face,w,h):
    role=spec['material'];base=np.array(PALETTE[role],float)
    yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
    arr=np.broadcast_to(base,(h,w,3)).copy()*(.97+.045*(1-v))[:,:,None]
    pts=vertices(spec['geometry'])[list(FACES[face])]
    world=pts[0]+u[:,:,None]*(pts[1]-pts[0])+v[:,:,None]*(pts[3]-pts[0])
    wy,wz=world[:,:,1],world[:,:,2];side=face in ('west','east');motif=spec['motif']
    def paint(mask,c):arr[mask]=c
    # Restrained edge seams and material variation, not a noisy source reprojection.
    if role in ('silver','bright','gold','gold_edge','steel'):
        paint((xx==0)|(yy==0)|(xx==w-1)|(yy==h-1),np.minimum(base+13,255))
    if motif=='upper' and side:
        paint(abs(wy-11.45)<.022,[74,82,88])
        paint((abs(wz+.55)<.018)|(abs(wz-3.37)<.018),[95,103,108])
        for z in (-1.70,1.88,2.28):
            q=(wz-z)**2+(wy-11.65)**2
            paint(q<.052**2,[56,62,67]);paint((q<.071**2)&(q>.056**2),[215,219,219])
    if motif=='receiver' and side:
        # Long inset on the silver upper receiver, source-supported seam/screws.
        paint((wz>8.85)&(wz<10.40)&(abs(wy-11.66)<.09),[80,89,94])
        paint(abs(wy-11.01)<.024,[83,91,97])
        for z,y in ((8.65,11.02),(10.9,11.90),(11.53,11.16)):
            q=(wz-z)**2+(wy-y)**2;paint(q<.06**2,[48,52,57]);paint((q<.08**2)&(q>.061**2),[215,218,219])
    if motif=='forearm' and side:
        paint((abs(wy-9.36)<.022)&(wz>-1.6)&(wz<3.2),[92,100,104])
        for z in (-1.55,2.75,3.25):
            q=(wz-z)**2+(wy-9.61)**2;paint(q<.058**2,[49,55,60])
    if motif=='vents' and side:
        for z in (-1.4,-.98,-.56,-.14,.28,.70):
            curve=wz-z+.28*(wy-10.10)**2
            paint((abs(curve)<.093)&(abs(wy-10.10)<.17),[11,15,19])
            paint((curve>.068)&(curve<.09)&(abs(wy-10.10)<.17),[74,83,87])
    if motif in ('tube','barrel','threads'):
        paint(abs(world[:,:,0]-8)<.035,base*.88)
        if motif=='threads':paint(np.mod(wz+8.93233,.075)<.022,[94,67,34])
        if motif=='barrel':paint((wz>-4.10)&(wz<-4.02),[72,64,47])
    if motif=='scope':
        paint(abs(wz-5.36)<.021,[68,74,80]);paint(abs(wz-7.15)<.02,[83,91,97])
        if side:
            paint((abs(wy-12.73)<.032)&(wz>5.51)&(wz<5.79),[27,32,37])
            for z in (6.70,7.12):paint((wz-z)**2+(wy-12.72)**2<.051**2,[54,61,68])
    if motif=='optic_controls' and side:
        paint((wy>12.37)&(wy<12.47)&(wz>6.12)&(wz<6.34),[211,126,180])
        paint((wy>12.37)&(wy<12.47)&(wz>6.39)&(wz<6.57),[226,106,88])
    if motif=='lens':
        a=(u-.5)**2+(v-.5)**2
        paint(a<.20,[32,35,57]);paint((a>.18)&(a<.23),[59,63,91]);paint((u<.22)&(v<.40),[57,63,82])
    if motif=='rear_cheek' and side:
        paint(abs(v-.15)<.025,[111,120,124])
        for cu,cv in ((.15,.50),(.85,.65)):
            q=(u-cu)**2+(v-cv)**2;paint(q<.0017,[48,54,59]);paint((q<.0025)&(q>.0018),[215,219,220])
    if motif=='grip_shoulder' and side:
        paint((u>.20)&(u<.26),[83,93,99])
    if motif in ('stock_ribs','grip') and side:
        ribs=np.mod(wy*.93+wz*.28,.14)<.035
        paint(ribs,base*.60)
    if motif=='stock_web' and side:
        paint(abs(wy-9.02-.36*(wz-12.4))<.035,[69,77,83])
    if motif=='stock_lower' and side:paint(abs(v-.22)<.045,[64,72,78])
    if motif=='magazine' and side:
        for z in (11.43,12.11,12.78):paint(abs(wz-z)<.026,[79,88,92])
        paint(abs(wy-5.90)<.025,[103,111,114])
    if motif=='butt':paint(np.mod(wy,.14)<.036,[48,53,57])
    if motif in ('collar','cap','mount','hook_mount','comb') and side:
        q=(u-.25)**2+(v-.5)**2;paint(q<.006,[33,39,44]);paint((q>.004)&(q<.006),[146,152,154])
    im=Image.fromarray(np.dstack((np.clip(arr,0,255).astype('uint8'),np.full((h,w),255,'uint8'))))
    if spec['geometry']['name']=='long_silver_upper' and face=='west':
        # Small identity marking, oriented independently on the evidenced side.
        dr=ImageDraw.Draw(im);font=ImageFont.load_default(size=max(9,round(h*.33)))
        x=int((3.95-pts[0,2])/(pts[1,2]-pts[0,2])*w);y=int(h*.38)
        dr.text((x,y),'XIV',font=font,fill=(164,119,52,255))
        dr.line([(x+6,y-5),(x+6,y-1)],fill=(164,119,52,255),width=2)
        dr.line([(x+3,y-4),(x+9,y-4)],fill=(164,119,52,255),width=2)
    return im

def compile_model(d):
    requests=[]
    for s in d['solids']:
        e=s['geometry'];e['faces']={}
        for f in FACES:
            p=vertices(e)[list(FACES[f])];a=np.linalg.norm(p[1]-p[0]);b=np.linalg.norm(p[3]-p[0])
            density=26 if s['motif'] in ('receiver','upper','scope','magazine') else 17
            requests.append((max(5,math.ceil(b*density)),max(5,math.ceil(a*density)),e['name'],f,s))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0))
    x=y=2;row=0;ledger=[]
    for h,w,name,f,s in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        assert y+h+2<=EDGE,('atlas overflow',name,y+h)
        patch=tile(s,f,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(patch),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        s['geometry']['faces'][f]=dict(uv=[q*16/EDGE for q in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=f,pixels=[x,y,x+w,y+h]))
        x+=w+4;row=max(row,h)
    d['atlas']={'size':EDGE,'gutter':2,'face_islands':len(ledger),'islands':ledger}
    model=dict(credit='W130 Patron of Lost Causes: authored semantic solid cuboids / default-photo paint',
        textures={'0':'destiny:item/weapon/w123/patron_of_lost_causes','particle':'destiny:item/weapon/w123/patron_of_lost_causes'},
        elements=[copy.deepcopy(s['geometry']) for s in d['solids']],display=json.loads((ROOT/BASE).read_bytes())['display'])
    return atlas,model

def inspection(d,atlas,model):
    cubes=[];groups=collections.defaultdict(list)
    for s,e in zip(d['solids'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation');b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
        for f in b['faces'].values():f.update(texture=0,uv=[q*EDGE/16 for q in f['uv']])
        cubes.append(b);groups[s['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='W130 Patron of Lost Causes solid inspection',
        resolution={'width':EDGE,'height':EDGE},elements=cubes,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],children=c,export=True) for g,c in groups.items()],
        textures=[dict(name='patron_of_lost_causes.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=model['display'],destiny_w130={'anchor':[8,8,8],'scale':d['scale'],'native_accepted':False,'rotation_order':'RzRyRx'})

def comparison(d,atlas,model):
    raster=helper()
    canonical=json.loads((ROOT/BASE).read_bytes())
    old_texture=Image.open(ROOT/'src/main/resources/assets/destiny/textures/item/weapon/w30/patron_of_lost_causes.png')
    tris=[raster['model_triangles']({'full':canonical},old_texture),raster['model_triangles']({'full':model},atlas)]
    points=np.concatenate([vertices(e) for e in canonical['elements']+model['elements']])
    w,h=1050,360;sheet=Image.new('RGB',(2*w,1980),'#161e27');draw=ImageDraw.Draw(sheet)
    draw.text((22,14),'PATRON OF LOST CAUSES | W130 | SEMANTIC SOLIDS / DEFAULT PHOTO PAINT | OFFLINE',fill='#eef1ed',font_size=25)
    photo=Image.open(PHOTO).convert('RGB').crop((430,190,1900,815));photo.thumbnail((820,350));sheet.paste(photo,(12,65))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / {len(model["elements"])*6} authored face UVs',
        'Silver long shell + scope / black open stock / gold tubes',
        'Real stock air / guard / recessed scope glass / deep bore',
        'LEFT = unchanged canonical W30 full + existing texture',
        'Actual default photo above establishes silver/gold dye',
        'Native parser / held / ADS / generic reload: pending master']):
        draw.text((850,70+i*47),line,fill='#dbe4e7',font_size=20)
    draw.text((20,429),'CANONICAL W30 FULL (241 CUBOIDS) / EXISTING TEXTURE / CPU',fill='#e4e9ee',font_size=21)
    draw.text((w+20,429),'NEW MEANINGFUL SOLIDS / AUTHORED 1024 FACE ATLAS / CPU',fill='#e4e9ee',font_size=21)
    views=[('SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.45,-.55]),('REAR THREE-QUARTER',[1,.35,.60]),('BORE / OPTIC RECESS / DEPTH',[-.28,.14,-1])]
    for row,(label,cam) in enumerate(views):
        extent=raster['frame'](points,cam,w,h)
        for col,t in enumerate(tris):
            im,_=raster['render'](t,cam,extent,(w,h));sheet.paste(im,(col*w,470+row*h))
            draw.text((col*w+18,478+row*h),label,fill='#e1ebed',font_size=19)
    draw.text((22,1946),'Matched axes, scale and framing. Canonical comparison is not original FBX and not a native screenshot. Native QA remains pending.',fill='#c5d0d9',font_size=19)
    return png(sheet)


def review_text(d,model):
    n=len(model['elements'])
    return f'''# Patron of Lost Causes W130 art review

Reference: actual Bungie default photo `{PHOTO}`, item 2723241847, sha256
`{sha(PHOTO.read_bytes())}`; W31 references.json entry verified.
Photo and raw neutral 46a6eb80_Diffuse.png actually opened with view_image.
The default has a long silver upper shell and silver optic, black lower and triangular
stock around a large aperture, exposed gold barrel and internal tube, small gold XIV,
and the forward underside curved hook. No alternate ornament or foreign identity.
The neutral diffuse is structural evidence, not finished default dye.

{n} emitted filled solid cuboids, {n*6} individually authored face UV rectangles,
0 triangle adapters, 0 alpha body/contour elements. One full resource only.
Long opaque casing, receiver, grip, forearm, magazine and stock volumes carry clean
broad panels. Octagonal barrel and optic walls are actual thick solids around bores;
stock, trigger guard, ejection port and scope saddle contain physical air.
Scope glass is recessed inside both ends; the muzzle has a backstop 1.31 units behind
its tip. Vents, fasteners, ribs, seams and the small photo-side XIV use face paint.
No connected-component conversion, source polygon transplant, voxel transplant or
flat silhouette panels. Functional barrel/optic cross sections justify the tube walls.

Frame: {d['coordinate_mapping']}. Source scale {d['scale']}, anchor [8,8,8].
All existing canonical full display transforms copied verbatim; original hand-region
and muzzle axis retained without recenter or rescale. Grip follows original wrist region.
Full only: existing ADS, generic reload graph, timing, sounds and registries unchanged.
Native substitution and master GUI integration have not run.

1024 RGBA atlas, aspect-proportional independent face islands, 2-pixel edge dilation.
Every face samples opaque texels. XIV only on the photo-evidenced side with its own UV.
Editable inspection.bbmodel embeds exact final solids, rotations, face UV and texture,
semantic groups with [8,8,8] origins and canonical display. No app was opened.

comparison.png includes the actual default photo plus clearly labeled, unchanged
canonical W30 full (241 cuboids) and existing W30 texture next to the new full model,
at matched side, front/rear oblique and axial depth cameras. Canonical is not the raw
FBX and neither comparison column is native evidence. Raw FBX was parsed read-only;
its source object set, original 29,158 triangles, scale and bounds are verified.
Read-only Beloved parser/vertices/raster and Halfdan UV packing/editable export
infrastructure are reused; this weapon's geometry and paint are authored here.

Practical limitations: faceted circular cross sections, simplified hook curve and local
wear; shallow vents/ribs/fasteners are painted. Opaque lens shading approximates albedo,
not refractive/PBR optics. Opposite-side decal detail is deliberately restrained.
Master still owns model-parser/pack loading, first/third-person hand contact, ADS
visibility, generic reload seating/timing/audio, ground/GUI placement and a brief
10-20 displayed-weapon observation. No native success or performance claim.
'''


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_model(d)
    ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']=='patron_of_lost_causes')
    assert ref==next(r for r in json.loads(Path('/tmp/destiny-weapons-w31/references.json').read_bytes()) if r['id']==d['id'])
    assert sha(PHOTO.read_bytes())==ref['sha256']
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
        ART+'inspection.bbmodel':encode(inspection(d,atlas,model)),ART+'review.md':review_text(d,model).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,atlas,model)
    p=np.concatenate([vertices(e) for e in model['elements']]);n=len(model['elements'])
    manifest=dict(stage='W130',id=d['id'],assembled_elements=n,counts={'full':n},
        opaque_cuboids=n,emitted_faces=n*6,alpha_contour_elements=0,triangle_adapter_elements=0,
        max_assembled_elements=1000,source_triangles=meta['source_triangles'],canonical_elements=241,semantic_groups=d['groups'],
        actual_bounds=[p.min(0).round(6).tolist(),p.max(0).round(6).tolist()],anchor=meta['anchor'],scale=meta['scale'],
        canonical_display_exact=True,full_only=True,native_accepted=False,texture_size=[EDGE,EDGE],face_islands=d['atlas']['face_islands'],
        comparison_reference='Unchanged canonical W30 full + existing texture; actual default photo; all renders CPU only',
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={k:sha(v) for k,v in sorted(outputs.items())},
        validation={'targeted_test':'scripts/qa/test_surface_w123_patron_of_lost_causes.py','determinism':'generator --verify',
            'native':'pending master','gameplay':'pending master','performance':'not measured'},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w130/batch.json').read_bytes())
    scope=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w130-patron_of_lost_causes'))
    assert len(scope)==10 and set(outputs)<=scope
    for path,data in outputs.items():
        dest=ROOT/path
        if args.verify:assert dest.read_bytes()==data,'Regeneration differs: '+path
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} assets; {m["assembled_elements"]} solids / {m["emitted_faces"]} faces; full only')

if __name__=='__main__':main()
