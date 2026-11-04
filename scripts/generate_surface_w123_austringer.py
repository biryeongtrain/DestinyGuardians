#!/usr/bin/env python3
"""W129 Austringer: deterministic solid-volume design, full model only.

Read-only FBX parser and CPU raster helper; numpy/Pillow, no DCC or native use.
Run with bundled Python -B. --verify compares all seven generated artifacts.
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
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/austringer/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET+'models/weapon/hand_cannon/austringer.json'
MODEL = ASSET+'models/weapon_surface_w123/austringer.json'
TEXTURE = ASSET+'textures/item/weapon/w123/austringer.png'
GENERATOR = 'scripts/generate_surface_w123_austringer.py'
TEST = 'scripts/qa/test_surface_w123_austringer.py'
WORKER = 'docs/qa/2026-10-26/w129/austringer-worker.md'
BB = 'art/blockbench/weapons/w30/austringer.bbmodel'
PARSER = 'scripts/generate_reload_models_w100.py'
RASTER = 'scripts/generate_surface_w115_hammerhead.py'
RAW = Path('/tmp/destiny-weapons-w30/raw/austringer/extracted/Austringer')
PHOTO = Path('/tmp/destiny-weapons-w31/references/austringer.jpg')
EDGE = 1024
FACES = {'north':(3,2,0,1),'south':(6,7,5,4),'west':(2,6,4,0),
         'east':(7,3,1,5),'up':(2,3,7,6),'down':(4,5,1,0)}
PALETTE = {'gold':[202,187,130], 'gold_edge':[225,212,163],
           'gold_shadow':[141,122,73], 'black':[34,37,37],
           'steel':[126,130,125], 'grip':[40,42,41], 'bore':[39,36,31],
           'purple':[90,46,125]}
_HELPER = None

def sha(b): return hashlib.sha256(b).hexdigest()
def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
    b=io.BytesIO(); im.save(b,format='PNG'); return b.getvalue()
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w129:austringer:'+s))
def helper():
    global _HELPER
    if _HELPER is None: _HELPER=runpy.run_path(str(ROOT/RASTER))
    return _HELPER

def source():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha((RAW/'Austringer.fbx').read_bytes())==meta['source_files']['Austringer/Austringer.fbx']
    nodes=runpy.run_path(str(ROOT/PARSER))['parse_fbx'](RAW/'Austringer.fbx')
    objects=next(n[2] for n in nodes if n[0]=='Objects')
    meshes=[]
    for n in objects:
        if n[0]!='Geometry': continue
        name=n[1][1].split('\0')[0]
        if name not in meta['source_objects']: continue
        c={v[0]:v for v in n[2]}
        # Austringer's measured W30 frame, not another weapon's basis.
        v=np.array(c['Vertices'][1][0]).reshape(-1,3)[:,[0,2,1]]*meta['scale']+meta['anchor']
        indices=np.array(c['PolygonVertexIndex'][1][0]); assert np.all(indices[2::3]<0)
        indices=np.where(indices<0,-indices-1,indices).reshape(-1,3)
        layer=next(x for x in n[2] if x[0]=='LayerElementUV' and any(k[0]=='Name' and k[1]==['uv0'] for k in x[2]))
        u={x[0]:x for x in layer[2]}
        uv=np.array(u['UV'][1][0]).reshape(-1,2)[list(u['UVIndex'][1][0])].reshape(-1,3,2)
        uv[:,:,1]=1-uv[:,:,1]
        image='ACrystal_Diffuse.png' if '.01.' in name else 'ASight_Diffuse.png' if '.03.' in name else 'AFrame_Diffuse.png'
        meshes.append(dict(name=name,vertices=v,faces=indices,uv=uv,image=image))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert np.allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=1e-5)
    assert sum(len(m['faces']) for m in meshes)==15680
    return meshes,meta


def design(meta):
    specs=[]
    def box(group,name,center,size,material,angles=(0,0,0),motif=''):
        c=np.array(center,float);s=np.array(size,float)
        specs.append(dict(group=group,material=material,motif=motif,geometry=dict(name=name,
            **{'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist()},
            rotation=dict(origin=c.round(6).tolist(),**dict(zip('xyz',angles))))))
    def beam(group,name,a,b,width,depth,material,motif=''):
        a=np.array(a,float);b=np.array(b,float);d=b-a;assert abs(d[0])<1e-8
        box(group,name,(a+b)/2,[width,np.linalg.norm(d),depth],material,
            (round(math.degrees(math.atan2(d[2],d[1])),6),0,0),motif)
    def ring(group,name,center,apothem,thickness,depth,material):
        # Eight solid staves; center is genuine air, not a transparent cap.
        x,y,z=center
        for i in range(8):
            a=i*45;t=math.radians(a)
            box(group,f'{name}_{i}',[x+apothem*math.cos(t),y+apothem*math.sin(t),z],
                [thickness,2*apothem*math.tan(math.pi/8)+.012,depth],material,(0,0,a))
    def prism(group,name,center,apothem,depth,material,motif=''):
        # Four intersecting solid bars fill a convex octagonal cross-section.
        for i in range(4):
            box(group,f'{name}_{i}',center,[2*apothem,2*apothem*math.tan(math.pi/8),depth],material,(0,0,i*45),motif)

    # Broad continuous shroud; deep annular nose only where the bore is.
    box('shroud','Shroud_mass',[8,12.72,-.94],[1.73,1.85,7.52],'gold',motif='shroud')
    box('shroud','Shroud_crown',[8,13.68,-1.68],[1.55,.18,9.05],'gold_edge',motif='crown')
    box('shroud','Shroud_lower_sill',[8,11.74,-1.72],[1.82,.22,9.12],'gold_shadow',motif='sill')
    for side in (-1,1):
        box('shroud',f'Crown_chamfer_{side}',[8+side*.80,13.57,-1.67],[.25,.27,9.05],'gold_edge',(0,0,side*33))
        box('shroud',f'Nose_flank_{side}',[8+side*.73,12.72,-5.50],[.43,1.57,1.64],'gold',motif='shroud')
    box('shroud','Nose_upper',[8,13.49,-5.50],[1.70,.38,1.64],'gold_edge')
    box('shroud','Nose_lower',[8,11.99,-5.50],[1.81,.40,1.64],'gold_shadow')
    ring('muzzle','Muzzle_rim',[8,12.77,-6.16],.56,.19,.32,'gold_shadow')
    ring('muzzle','Muzzle_wall',[8,12.77,-5.50],.51,.13,1.02,'bore')
    box('muzzle','Muzzle_back',[8,12.77,-4.80],[.88,.88,.12],'black')

    # Open long underlug, with discrete structural end supports.
    box('underlug','Underlug_lower',[8,10.79,-1.62],[1.55,.28,8.65],'gold',motif='lug')
    for side in (-1,1):
        box('underlug',f'Underlug_edge_{side}',[8+side*.67,10.99,-1.62],[.25,.19,8.62],'gold_edge',(0,0,side*28))
    beam('underlug','Underlug_front',[8,10.85,-5.92],[8,11.58,-6.17],1.44,.26,'gold_shadow')
    box('underlug','Underlug_rear',[8,11.16,2.61],[1.46,.71,.32],'gold_shadow')
    box('clamp','Black_clamp',[8,11.25,.43],[1.81,1.12,.69],'black',motif='clamp')

    # Filled dark cylinder/receiver. No separate reload output for this graph.
    prism('receiver','Cylinder',[8,12.43,4.34],1.045,3.04,'black','cylinder')
    prism('receiver','Cylinder_front_band',[8,12.43,2.91],1.085,.15,'black','cylinder_band')
    prism('receiver','Cylinder_rear_band',[8,12.43,5.79],1.085,.15,'black','cylinder_band')
    box('receiver','Cylinder_lower_frame',[8,11.06,4.31],[1.16,.31,3.71],'black',motif='frame')
    box('receiver','Breech',[8,12.13,6.02],[1.39,2.40,.47],'black',motif='frame')
    box('receiver','Top_frame',[8,13.71,4.33],[1.25,.25,3.26],'black',motif='rail')
    box('receiver','Top_gold_rod',[8,13.67,4.35],[.66,.20,2.72],'gold_edge',motif='rail')
    beam('frame','Grip_tang',[8,11.62,6.08],[8,10.71,6.72],1.35,.88,'black',motif='frame')
    beam('frame','Rear_tang',[8,11.86,6.10],[8,11.37,8.15],1.25,.35,'black')

    # Gold mounts are actual shallow relief; solid octagonal purple insets.
    for side in (-1,1):
        for j,z in enumerate((-3.56,-.16)):
            box('insets',f'Bezel_{side}_{j}',[8+side*.895,12.92,z],[.18,1.35,1.42],'gold_shadow',motif='bezel')
            for i in range(4):
                box('insets',f'Crystal_{side}_{j}_{i}',[8+side*.998,12.92,z],
                    [.14,.96,.96*math.tan(math.pi/8)],'purple',(i*45,0,0),f'crystal:{z}')

    # Black grip follows W30 hand frame, widening into a wrapped heel.
    beam('grip','Grip_neck',[8,11.42,6.75],[8,10.70,6.93],1.32,1.83,'grip','grip_upper')
    beam('grip','Grip_upper',[8,11.05,6.87],[8,9.98,7.10],1.23,1.62,'grip','grip_upper')
    beam('grip','Grip_palm',[8,10.02,7.18],[8,8.74,7.85],1.39,1.78,'grip','wrap')
    beam('grip','Grip_heel',[8,8.76,7.93],[8,7.39,8.52],1.40,1.92,'grip','grip_lower')
    beam('grip','Backstrap_upper',[8,10.62,7.98],[8,8.73,9.13],1.40,.22,'black','wrap')
    beam('grip','Backstrap_lower',[8,8.73,9.13],[8,7.61,9.54],1.40,.22,'black')
    beam('grip','Butt_rim',[8,6.98,7.63],[8,7.57,9.51],1.41,.27,'black','heel')
    beam('grip','Frontstrap',[8,9.99,6.28],[8,7.02,7.56],1.26,.24,'black')

    # Guard perimeter and curved trigger leave genuine through space.
    beam('guard','Guard_front',[8,10.54,3.60],[8,9.56,3.94],.57,.22,'black')
    beam('guard','Guard_front_curve',[8,9.56,3.94],[8,9.15,4.64],.57,.22,'black')
    beam('guard','Guard_bottom',[8,9.15,4.64],[8,9.15,5.45],.57,.22,'black')
    beam('guard','Guard_rear_curve',[8,9.15,5.45],[8,9.60,6.18],.57,.22,'black')
    beam('guard','Guard_rear',[8,9.60,6.18],[8,10.56,6.41],.57,.22,'black')
    beam('trigger','Trigger_upper',[8,10.68,5.87],[8,10.02,5.86],.26,.16,'gold')
    beam('trigger','Trigger_tip',[8,10.02,5.86],[8,9.61,5.60],.26,.17,'gold_shadow')
    beam('hammer','Hammer_stem',[8,12.49,6.18],[8,13.18,6.51],.46,.40,'black')
    beam('hammer','Hammer_spur',[8,13.18,6.51],[8,13.72,7.20],.46,.31,'gold',motif='hammer')

    # Underbarrel optical module with actual aperture and recessed dark lens.
    prism('optic','Optic_body',[8,9.94,.39],.44,3.52,'black','optic')
    for j,z in enumerate((-.62,1.38)):
        prism('optic',f'Optic_band_{j}',[8,9.94,z],.49,.18,'steel','optic_band')
    ring('optic','Optic_front_rim',[8,9.94,-1.86],.40,.13,.41,'steel')
    ring('optic','Optic_tunnel',[8,9.94,-1.61],.35,.10,.32,'black')
    box('optic','Optic_lens',[8,9.94,-1.41],[.59,.59,.07],'bore',motif='lens')
    box('optic','Optic_mount',[8,10.44,.47],[.73,.45,1.63],'black')
    for side in (-1,1):
        box('optic',f'Optic_control_{side}',[8+side*.51,9.93,-.38],[.16,.55,.55],'steel',motif='control')
    for j,(a,b) in enumerate((([8,9.93,2.17],[8,9.67,2.53]),
                              ([8,9.67,2.53],[8,9.74,2.99]),
                              ([8,9.74,2.99],[8,10.18,3.39]))):
        beam('hose',f'Optic_hose_{j}',a,b,.22,.20,'steel','hose')

    # Actual rear notch, no floating reticle plate.
    box('sights','Rear_sight_base',[8,13.90,5.22],[.65,.10,.94],'black')
    for side in (-1,1):
        box('sights',f'Rear_sight_ear_{side}',[8+side*.23,13.99,5.24],[.17,.12,.57],'gold_shadow')
    box('sights','Front_sight',[8,13.86,2.26],[.25,.18,.36],'black')

    inputs=[BASE,BB,PARSER,RASTER,'art/weapons/w31/palette-overrides.json','art/weapons/w31/references.json',
            ASSET+'items/weapon/austringer.json',ASSET+'items/weapon_aim_w70/austringer.json']
    # Pin existing pose/reload assets without modifying their graph.
    for folder in ('models/weapon/hand_cannon','models/weapon_aim_w70','models/weapon_reload','items/weapon_reload'):
        inputs.extend(p.relative_to(ROOT).as_posix() for p in sorted((ROOT/ASSET/folder).glob('austringer*.json')))
    inputs=sorted(set(inputs))
    raw_inputs=[RAW/'Austringer.fbx',PHOTO]+[RAW/n for n in ('AFrame_Diffuse.png','ACrystal_Diffuse.png','ASight_Diffuse.png')]
    return dict(stage='W129',revision='solid-default-gold-purple-r1',id='austringer',family='hand_cannon',
        source=meta,anchor=[8,8,8],mapping='[8+source.X*s,8+source.Z*s,8+source.Y*s]; thin X, up Y, muzzle -Z',
        method='Authored broad opaque solid cuboids, per-face UVs; no source islands, voxel extrusion, alpha shell or arbitrary triangles.',
        output_policy='Full only. Canonical model read-only; generic reload/ADS graph unchanged; master owns integration.',
        draft_target='80-120 starting solids, not a cap. Extra solids serve bores, inset relief, guard and optic.',
        palette=PALETTE,parts=specs,groups=dict(collections.Counter(s['group'] for s in specs)),
        paint_evidence=dict(photo=str(PHOTO),photo_sha256=sha(PHOTO.read_bytes()),
            reference='W31 references.json Austringer 3055790362 / Bungie screenshot; gold, black and paired purple insets.',
            palette_override='W31 has no Austringer palette override. Neutral diffuse is not finished default dye.',
            interpretation='Clean pale gold / black receiver and wrapped grip / purple relief; conservative reverse side from raw diffuse.'),
        air_probes={'guard':[8,9.85,4.90],'underlug':[8,11.31,-3.0],
                    'rear_notch':[8,14.0,5.24],'muzzle_entry':[8,12.77,-6.30],
                    'muzzle_depth':[8,12.77,-4.99],'optic_entry':[8,9.94,-2.04],
                    'optic_depth':[8,9.94,-1.49]},
        solid_probes={'shroud':[8,12.7,-1.5],'receiver':[8,12.43,4.3], 'grip':[8,8.0,8.2]},
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['Fine source bevels and reflections simplified. Static opaque paint is not original PBR.',
            'Purple swirl is an authored material interpretation; not an exact shader reconstruction.',
            'Reverse side repeats photo/raw-supported motifs; no separate reverse photo.',
            'Offline only; native pack parsing, held views, ADS, generic reload and 10-20 display QA pending master.'])


def face_points(e,face): return helper()['vertices'](e)[list(FACES[face])]

def tile(spec,face,w,h):
    base=np.array(PALETTE[spec['material']],float)
    yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
    a=np.zeros((h,w,4),np.uint8);a[:,:,3]=255
    a[:,:,:3]=np.clip(base[None,None,:]*(.98+.025*np.sin(v*np.pi))[:,:,None],0,255)
    p=face_points(spec['geometry'],face)
    world=p[0]+u[:,:,None]*(p[1]-p[0])+v[:,:,None]*(p[3]-p[0])
    X,Y,Z=(world[:,:,i] for i in range(3));motif=spec['motif'];side=face in ('east','west')
    if spec['material'] in ('gold','gold_edge','gold_shadow','steel'):
        a[0,:,:3]=np.minimum(base+15,255);a[-1,:,:3]=base*.83
    if motif=='shroud' and side:
        for z in (-5.30,-1.86,1.58):
            dy=Y-12.56;half=.25+.42*np.clip(dy/.80,0,1)
            field=(dy>0)&(dy<.82)&(abs(Z-z)<half)
            a[field,:3]=[29,32,31]
            r=np.hypot(Z-z,Y-12.99)
            a[(r<.142)&(r>.109),:3]=[169,153,101]
            a[(r<.085)&(r>.055),:3]=[112,115,105]
            a[r<.045,:3]=[42,43,38]
        a[abs(Y-11.94)<.018,:3]=[116,99,59]
    if motif=='bezel' and side:
        im=Image.fromarray(a);dr=ImageDraw.Draw(im)
        dr.rectangle((1,1,w-2,h-2),outline='#d9c890',width=1)
        for x in (.14*w,.86*w):
            for y in (.14*h,.86*h):
                r=max(1,min(w,h)*.072);dr.ellipse((x-r,y-r,x+r,y+r),fill='#b6a66d',outline='#60583a')
        a=np.array(im)
    if motif.startswith('crystal:'):
        center=float(motif.split(':')[1]);dy=Y-12.92;dz=Z-center
        r=np.hypot(dy,dz)/.51;angle=np.arctan2(dy,dz)
        swirl=np.sin(3*angle+17*r+1.4*np.sin(2*angle-8*r))
        bands=.50+.16*swirl+.12*np.cos(27*r+2*angle)
        color=np.array([71,34,94])[None,None,:]+bands[:,:,None]*np.array([59,36,79])
        sheen=np.exp(-((dy-.17)**2+(dz+.16)**2)/.016)
        color+=sheen[:,:,None]*np.array([58,56,61])
        a[:,:,:3]=np.clip(color,0,255)
        a[r>.83,:3]=[56,39,64];a[r>.94,:3]=[176,158,98]
    if motif in ('grip_upper','grip_lower','wrap') and side:
        if motif=='wrap':
            stripe=np.mod(Y+.47*Z,.56)
            a[stripe<.055,:3]=[17,19,19];a[(stripe>.055)&(stripe<.080),:3]=[52,53,50]
        if motif=='grip_lower':
            cells=np.hypot(np.mod(Y*1.07+.20,.18)-.09,np.mod(Z,.18)-.09)
            a[(cells<.023)&(Y<8.1),:3]=[15,17,17]
        z,y=(6.99,10.65) if motif=='grip_upper' else (8.65,7.60)
        r=np.hypot(Z-z,Y-y)
        a[(r<.12)&(r>.085),:3]=[104,102,88];a[r<.062,:3]=[27,29,28]
    if motif=='cylinder':
        if side:
            a[(Y>12.6)&(Y<12.91)&(Z>3.10)&(Z<5.61),:3]=[18,21,21]
            a[(abs(Y-12.93)<.025)&(Z>3.10)&(Z<5.60),:3]=[65,67,61]
        if face=='up':a[abs(X-8)>.60,:3]=[20,23,23]
    if motif in ('rail','frame','clamp','lug') and side and min(w,h)>8:a[-3,:,:3]=base*.65
    if motif in ('control','lens'):
        r=np.hypot(u-.5,v-.5)
        a[r<.38,:3]=[36,40,39];a[(r<.38)&(r>.28),:3]=[119,122,112]
        if motif=='lens':
            a[r<.27,:3]=[24,30,28];a[(r<.24)&(r>.21),:3]=[65,68,53]
    if motif in ('hose','optic_band','hammer'):a[np.mod(v*max(h,4),5)<1.1,:3]=base*.55
    return Image.fromarray(a)


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE));requests=[]
    for spec in d['parts']:
        e=spec['geometry'];e['faces']={}
        for face in FACES:
            p=face_points(e,face);density=25 if spec['group'] in ('shroud','insets','grip') else 18
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,e['name'],face,spec))
    requests.sort(key=lambda q:(-q[0],-q[1],q[2],q[3]));x=y=2;row=0;ledger=[]
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow')
        im=tile(spec,face,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        spec['geometry']['faces'][face]=dict(uv=[q*16/EDGE for q in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    d['atlas']=dict(size=EDGE,gutter=2,islands=ledger,used_texels=sum((q['pixels'][2]-q['pixels'][0])*(q['pixels'][3]-q['pixels'][1]) for q in ledger))
    model=dict(credit='W129 Austringer / authored solid volumes and opaque per-face UV / offline candidate',
        textures={'0':'destiny:item/weapon/w123/austringer','particle':'destiny:item/weapon/w123/austringer'},
        elements=[copy.deepcopy(s['geometry']) for s in d['parts']],display=json.loads((ROOT/BASE).read_bytes())['display'])
    assert len(model['elements'])<=1000
    return atlas,model


def inspection(d,atlas,model):
    elements=[];groups=collections.defaultdict(list)
    for spec,e in zip(d['parts'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation')
        b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
        for f in b['faces'].values(): f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        elements.append(b);groups[spec['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Austringer W129 solid default finish',
        resolution={'width':EDGE,'height':EDGE},elements=elements,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],rotation=[0,0,0],children=v,export=True) for g,v in groups.items()],
        textures=[dict(name='austringer.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=model['display'],
        destiny_w129={'nativeAccepted':False,'anchor':[8,8,8],'scale':d['source']['scale'],'fullOnly':True})


def raw_triangles(meshes):
    result=[]
    for mesh in meshes:
        tex=np.array(Image.open(RAW/mesh['image']).convert('RGBA'))
        for p,uv in zip(mesh['vertices'][mesh['faces']],mesh['uv']):
            n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((p,uv,tex,n))
    return result


def comparison(meshes,atlas,model):
    w,h=900,350;sheet=Image.new('RGB',(1800,1900),'#151e27');dr=ImageDraw.Draw(sheet)
    dr.text((20,12),'AUSTRINGER / W129 SOLID VOLUMES / ACTUAL DEFAULT GOLD + BLACK + PURPLE',fill='#f2e8cb',font_size=24)
    ref=Image.open(PHOTO).convert('RGB').crop((860,260,1830,780));ref.thumbnail((620,280));sheet.paste(ref,(18,48))
    count=len(model['elements'])
    lines=[f'{count} emitted solid cuboids / {count*6} authored opaque faces',
        'Full model only; canonical and generic reload/ADS untouched',
        'Gold long shroud / black frame and grip / two purple insets',
        'Actual muzzle depth, optic recess, open guard and sight notch',
        'RAW column: neutral diffuse with original UV; not default dye',
        'Native parsing, held/ADS/reload and 10-20 display QA: pending master']
    for i,line in enumerate(lines):dr.text((662,66+i*35),line,fill='#d9e3eb',font_size=18)
    dr.text((20,335),'ORIGINAL RAW FBX / 15,680 triangles / neutral diffuse',fill='#d9e3eb',font_size=19)
    dr.text((920,335),f'NEW AUTHORED SOLIDS / {count} cuboids / independent face UV',fill='#d9e3eb',font_size=19)
    arrays=[raw_triangles(meshes),helper()['model_triangles']({'full':model},atlas,{})]
    points=np.concatenate([m['vertices'] for m in meshes])
    views=[('SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.38,-.70]),('REAR THREE-QUARTER',[1,.32,.64]),('MUZZLE / OPTIC OPENINGS',[.16,.04,-1])]
    for row,(label,cam) in enumerate(views):
        cam=np.array(cam,float);cam/=np.linalg.norm(cam);right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right)
        proj=np.c_[points@right,points@up];lo,hi=proj.min(0),proj.max(0)
        extent=((lo+hi)/2,min((w-90)/(hi[0]-lo[0]),(h-45)/(hi[1]-lo[1])))
        for col,tris in enumerate(arrays):
            im,_=helper()['render'](tris,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,365+row*h))
            dr.text((col*w+14,371+row*h),label,fill='#e0e7eb',font_size=17)
    dr.text((20,1790),'Matched orthographic CPU renders. No source-island transplantation, alpha shell, split resource or native screenshot.',fill='#b7cbd7',font_size=18)
    dr.text((20,1825),'Broad solids keep the hand frame; surface ornament uses world-oriented face paint. Rear paint follows source motifs.',fill='#b7cbd7',font_size=18)
    return png(sheet)


def review(d,model):
    n=len(model['elements'])
    return f'''# Austringer W129 art review

{n} actual emitted solid cuboids; {n*6} explicitly UV-mapped opaque faces;
0 alpha body skins, meshes, triangle adapters, source-island transplants or split
models. 1024 RGBA atlas, {d['atlas']['used_texels']} used face texels, 2px dilated
gutters. Starting 80-120 draft was a guide; bores, relief and optical hardware
justify the final count. Count one full assembly, limit 1000.

Actual source inspection: W31 default screenshot Austringer 3055790362 (gold
shroud, black cylinder/frame/grip, two purple insets), AFrame_Diffuse neutral
sheet, and FBX 15,680 source triangles in the unchanged W30 frame. W31 references
pins the screenshot SHA-256 {sha(PHOTO.read_bytes())}. W31 has no Austringer dye
palette override. Neutral diffuse is detail evidence, not finished default dye.
No invented alternate palette, text or emblems. Purple swirls are an authored
static interpretation, not recovered dynamic shader behavior. Reverse-side
motifs follow raw UV evidence and are not independently photo verified.

Large shroud and grip are filled solid volumes. Front nose uses broad structural
flanks and a real annular barrel with >1 unit bore depth. Long underlug has actual
space above it; optic has a recessed dark lens and deep front tunnel; trigger
guard and low rear sight notch remain open from multiple angles. The rounded
receiver and optic use filled octagonal solid cross-sections. Four side reliefs
carry purple radial UV paint and gold corner detail. Triangle recesses, small
fasteners, shallow flutes and grip wrapping/stippling are UV. Surface wear is
restrained compared with the noisy raw diffuse.

Coordinates: [8+source.X*s,8+source.Z*s,8+source.Y*s], s={d['source']['scale']}.
Anchor [8,8,8], muzzle -Z, up Y, thin X. No recentering, pose/hand changes or scale
normalization. Canonical display copied exactly. Existing generic reload/ADS,
all canonical/W30/W31 resources, registries, Java, timing and sound are read-only.
Only the full candidate JSON is emitted; master owns integration.

inspection.bbmodel embeds atlas, semantic groups and all solid elements.
comparison.png includes actual photo and unchanged raw FBX neutral diffuse versus
new solid/UV result in side, front/rear three-quarter and front bore/optic views.
CPU imagery is offline evidence only. Worker visually inspected photo, raw
frame diffuse and final comparison using view_image.

Pending master: native model parser/pack loading; representative first/third
person and hand position; ADS/notch clearance; generic reload return; 10-20
simultaneous displayed weapons. Native success and performance are not claimed.
'''


def generate():
    meshes,meta=source();d=design(meta);atlas,model=compile_model(d)
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),
        ART+'inspection.bbmodel':encode(inspection(d,atlas,model)),ART+'comparison.png':comparison(meshes,atlas,model),
        ART+'review.md':review(d,model).encode()}
    points=np.concatenate([helper()['vertices'](e) for e in model['elements']]);n=len(model['elements'])
    manifest=dict(stage='W129',id='austringer',revision=d['revision'],native_elements=n,counts={'full':n},
        max_assembled_elements=1000,opaque_cuboids=n,emitted_faces=n*6,alpha_contour_elements=0,triangle_adapter_elements=0,
        source_triangles=15680,semantic_groups=d['groups'],full_only=True,canonical_read_only=True,canonical_display_exact=True,
        anchor=d['anchor'],scale=meta['scale'],rotation_order='RzRyRx',actual_bounds=[points.min(0).round(6).tolist(),points.max(0).round(6).tolist()],
        texture_size=[EDGE,EDGE],atlas_face_islands=n*6,atlas_face_texels=d['atlas']['used_texels'],
        generator_sha256=sha((ROOT/GENERATOR).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())},native_accepted=False,
        validation={'targeted_python':TEST,'native_parser':'pending master','gameplay':'pending master','performance':'not measured; offline only'},
        limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    batch=json.loads((ROOT/'docs/qa/2026-10-26/w129/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w129-austringer'))
    outputs=generate();assert set(outputs)|{GENERATOR,TEST,WORKER}==owned and len(owned)==10
    for path,data in outputs.items():
        target=ROOT/path
        if args.verify:assert target.is_file() and target.read_bytes()==data,'Generated drift: '+path
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts; {m["native_elements"]} solids; {m["emitted_faces"]} faces; full only; native pending')

if __name__=='__main__':main()
