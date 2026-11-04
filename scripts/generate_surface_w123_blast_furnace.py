#!/usr/bin/env python3
"""W127 Blast Furnace: authored semantic solids and deliberate face UV islands.

Only this feature's exact batch-owned paths may be written. No DCC, subprocess,
network, historical edits, animation/graph rewrites, or shared build directory.
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
ART = 'art/weapons/w123/blast_furnace/'
ASSET = 'src/main/resources/assets/destiny/'
TEXTURE = ASSET + 'textures/item/weapon/w123/blast_furnace.png'
MODEL = ASSET + 'models/weapon_surface_w123/blast_furnace'
BASE = ASSET + 'models/weapon/pulse_rifle/blast_furnace.json'
BB = 'art/blockbench/weapons/w30/blast_furnace.bbmodel'
RAW = Path('/tmp/destiny-weapons-w30/raw/blast_furnace/extracted')
FBX = RAW / 'Blast Furnace/Blast Furnace.fbx'
W31 = Path('/tmp/destiny-weapons-w31')
FACES = {'north':(3,2,0,1), 'south':(6,7,5,4), 'west':(2,6,4,0),
         'east':(7,3,1,5), 'up':(2,3,7,6), 'down':(4,5,1,0)}
NORMALS = {'north':(0,0,-1), 'south':(0,0,1), 'west':(-1,0,0),
           'east':(1,0,0), 'up':(0,1,0), 'down':(0,-1,0)}

def sha(b): return hashlib.sha256(b).hexdigest()
def encode(v): return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()
def png(im):
    out = io.BytesIO(); im.save(out, format='PNG'); return out.getvalue()
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'destiny:w123:blast_furnace:'+s))

def source_meshes():
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha(FBX.read_bytes())==meta['source_files']['Blast Furnace/Blast Furnace.fbx']
    meshes=runpy.run_path(str(ROOT/'scripts/generate_reload_w114_blast_furnace.py'))['source_meshes']()
    for mesh in meshes:
        mesh['vertices']=np.asarray(mesh['vertices']);mesh['faces']=np.asarray(mesh['faces'])
    return meshes,meta

# Geometry is authored below by functional part. The FBX parser above is used
# only for anchors, source evidence, glyph stencils, and offline comparison.
EDGE = 1024
MAX_ELEMENTS = 1000
PALETTE = {
    'frame':[60,64,68], 'crown':[76,81,85], 'recess':[18,21,26],
    'red':[188,40,36], 'red_edge':[219,62,47], 'steel':[159,165,170],
    'olive':[71,74,61], 'rubber':[31,34,36], 'violet':[92,76,136],
}


def renderer():
    # Inert, read-only raster/rotation helpers, never the historical design.
    return runpy.run_path(str(ROOT/'scripts/generate_surface_w115_hammerhead.py'))


def make_design(meshes,metadata):
    parts={'body':[], 'magazine':[]}
    def box(group,name,c,size,mat,angles=(0,0,0),motif='',part='body'):
        c=np.array(c,float);sz=np.array(size,float)
        e=dict(name=name,**{'from':(c-sz/2).round(6).tolist(),'to':(c+sz/2).round(6).tolist()},
            rotation=dict(origin=c.round(6).tolist(),**dict(zip('xyz',angles))))
        parts[part].append(dict(kind='solid_cuboid',group=group,material=mat,motif=motif,geometry=e))
    def beam(group,name,a,b,width,depth,mat,motif='',part='body'):
        a=np.array(a,float);b=np.array(b,float);v=b-a
        assert abs(v[0])<1e-8
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],mat,
            (round(math.degrees(math.atan2(v[2],v[1])),6),0,0),motif,part)
    def ring(group,name,z,y,r,thick,depth,mat):
        for i in range(8):
            a=i*45;t=math.radians(a)
            box(group,f'{name}_{i}',[8+r*math.cos(t),y+r*math.sin(t),z],
                [2*r*math.tan(math.pi/8)+.015,thick,depth],mat,(0,0,a-90))

    # Closed, thick main receiver. No thin side plates standing in for the body.
    box('receiver','Lower_receiver_frame',[8,10.88,8.00],[1.48,.90,10.70],'olive',motif='receiver')
    box('receiver','Receiver_main',[8,11.76,6.20],[1.86,1.08,7.05],'frame',motif='receiver')
    box('receiver','Receiver_rear',[8,11.45,10.70],[1.66,.38,2.20],'frame',motif='rear_panel')
    box('receiver','Receiver_crown_front',[8,13.40,4.64],[1.40,.55,3.80],'crown',motif='crown')
    box('receiver','Receiver_bridge',[8,12.84,5.00],[1.87,1.00,3.90],'frame',motif='receiver')
    box('receiver','Rear_mechanism_floor',[8,12.44,11.58],[1.50,.24,4.35],'frame')
    box('receiver','Rear_mechanism_back',[8,12.96,14.08],[1.69,1.25,.55],'frame')
    for side in (-1,1):
        box('receiver',f'Upper_shoulder_{side}',[8+side*.78,13.46,4.64],[.27,.41,3.8],
            'crown',(0,0,side*29))
    box('receiver','Well_socket',[8,10.47,11.94],[1.50,1.03,3.10],'olive',motif='well')
    box('receiver','Well_front_tang',[8,10.26,10.10],[1.12,1.16,.44],'olive')
    box('receiver','Well_rear_tang',[8,10.40,13.53],[1.35,1.00,.42],'olive')

    # Full-section long barrel spine, red insert seen in a true top-side opening.
    box('foreend','Front_crown',[8,13.49,-1.59],[1.46,.34,9.02],'crown',motif='crown')
    for side in (-1,1):
        box('foreend',f'Front_roof_chamfer_{side}',[8+side*.77,13.38,-1.59],[.30,.38,9.02],
            'frame',(0,0,side*28))
    box('foreend','Front_nose_block',[8,12.55,-4.62],[1.86,1.48,2.82],'frame',motif='nose')
    box('foreend','Front_lower_core',[8,12.155,0],[1.86,1.11,5.50],'frame',motif='armory_vents')
    beam('foreend','Front_panel_notch',[8,11.95,-3.23],[8,12.40,-2.74],1.86,.45,'frame')
    box('foreend','Red_barrel_core',[8,12.73,-.60],[1.40,.68,6.24],'red',motif='barrel')
    for side in (-1,1):
        beam('foreend',f'Red_upper_edge_{side}',[8+side*.58,13.02,-2.80],[8+side*.58,13.02,2.61],.19,.17,'red_edge','barrel')
    box('foreend','Barrel_front_seat',[8,12.68,-3.58],[1.46,.94,.36],'red')
    box('foreend','Barrel_rear_seat',[8,12.65,2.73],[1.58,1.12,.40],'frame')
    box('foreend','Foregrip_saddle',[8,11.24,-.15],[1.50,.72,6.95],'frame')
    beam('foreend','Lower_foregrip',[8,11.10,-3.42],[8,9.70,2.52],1.47,.85,'rubber','foregrip')
    beam('foreend','Foregrip_backstop',[8,9.12,2.72],[8,11.40,2.88],1.64,.39,'rubber','foregrip')

    # Red breech, visible lock and a gap before cheek rest. Four broad barrel
    # segments are justified by actual cross-section, no source-island copies.
    box('breech','Red_breech',[8,13.02,7.88],[1.16,1.16,2.05],'red',motif='breech')
    for side in (-1,1):
        box('breech',f'Breech_bevel_{side}',[8+side*.48,13.47,7.88],[.28,.24,2.05],'red_edge',(0,0,side*40))
    ring('breech','Lock_ring',9.10,12.91,.43,.14,.30,'steel')
    box('breech','Lock_bolt',[8,12.91,9.74],[.53,.52,1.15],'recess')
    box('breech','Lock_energy_band',[8,12.91,9.35],[.62,.62,.16],'violet')
    for side in (-1,1):
        box('breech',f'Charge_handle_{side}',[8+side*.77,12.59,10.00],[.25,.42,.44],'recess')

    # Original stock upper pad and lower rectangular machinery window. Body
    # window rails have real air across X; inner rod sits behind each opening.
    box('stock','Cheek_red_bedding',[8,13.15,13.14],[1.79,.12,5.09],'red',motif='redline')
    box('stock','Cheek_pad',[8,13.35,13.14],[1.69,.36,4.99],'rubber',motif='pad')
    for side in (-1,1):
        box('stock',f'Cheek_shoulder_{side}',[8+side*.70,13.42,13.14],[.26,.25,4.99],'rubber',(0,0,side*25),'pad')
    box('stock','Window_top',[8,12.37,13.91],[1.61,.19,3.93],'frame',motif='window')
    box('stock','Window_bottom',[8,11.53,13.91],[1.61,.21,3.93],'frame',motif='window')
    box('stock','Window_front',[8,11.95,12.00],[1.61,.69,.20],'frame')
    box('stock','Window_rear',[8,11.95,15.82],[1.61,.69,.20],'frame')
    box('stock','Window_internal_rod',[8,11.95,13.88],[.50,.30,3.48],'steel',motif='rod')
    beam('stock','Stock_upper_spine',[8,13.32,15.74],[8,12.89,17.38],1.43,.70,'frame')
    beam('stock','Stock_lower_strut',[8,11.38,14.75],[8,9.89,17.70],.95,.40,'frame')
    beam('stock','Stock_buttpad',[8,13.46,17.55],[8,9.94,17.87],1.43,.65,'rubber','pad')
    box('stock','Stock_heel_red',[8,9.94,17.70],[1.95,.17,.91],'red')
    box('stock','Stock_heel_metal',[8,9.83,17.70],[2.09,.13,.98],'steel')
    box('stock','Stock_top_cap',[8,13.55,17.50],[1.54,.27,.66],'red')
    for side in (-1,1):
        beam('stock',f'Rear_sight_ear_{side}',[8+side*.60,13.57,17.39],[8+side*.60,13.93,17.20],.18,.18,'steel')

    # Low wrist and open trigger guard: retained hand contact frame.
    beam('grip','Grip_core',[8,9.66,7.56],[8,6.97,9.06],1.02,1.13,'rubber','grip')
    beam('grip','Grip_backstrap',[8,9.57,8.01],[8,7.03,9.51],.91,.23,'frame','grip')
    beam('grip','Grip_heel',[8,6.86,8.92],[8,7.08,9.52],1.08,.25,'olive')
    box('grip','Grip_root',[8,10.16,7.65],[1.04,.84,1.35],'olive')
    beam('trigger','Guard_front',[8,11.27,3.26],[8,9.12,3.66],1.06,.32,'olive')
    beam('trigger','Guard_bottom',[8,9.14,3.64],[8,9.29,7.12],.75,.25,'olive')
    beam('trigger','Guard_rear',[8,9.29,7.12],[8,10.79,8.13],.75,.28,'olive')
    beam('trigger','Red_trigger',[8,11.02,5.75],[8,9.96,5.55],.23,.20,'red')
    beam('trigger','Trigger_hook',[8,9.96,5.55],[8,9.91,5.19],.23,.19,'red')

    # Genuine open muzzle: front octagonal rim, continuous inner walls, backstop.
    # Body nose begins at -6.03, behind the -6.38 end of bore: no hidden blockage.
    ring('muzzle','Muzzle_rim',-6.66,12.78,.43,.17,.28,'steel')
    ring('muzzle','Bore_wall',-6.25,12.78,.32,.11,.60,'recess')
    box('muzzle','Bore_backstop',[8,12.78,-5.91],[.51,.51,.10],'recess')

    # Keep the original compact pair of optic bases and rear open hood. No scope.
    box('optic','Sight_rail',[8,13.78,6.85],[.68,.19,3.52],'frame',motif='rail')
    box('optic','Forward_sight_base',[8,13.94,5.50],[.62,.19,.73],'frame',motif='rail')
    box('optic','Optic_lower',[8,14.10,7.82],[.78,.30,1.50],'frame',motif='optic')
    for side in (-1,1):
        box('optic',f'Optic_post_{side}',[8+side*.38,14.62,7.90],[.17,1.13,.30],'frame',motif='optic')
    box('optic','Optic_hood',[8,15.12,7.90],[.73,.18,.30],'crown')
    box('optic','Optic_sill',[8,14.35,7.90],[.63,.15,.33],'recess')
    box('optic','Optic_rear_adjuster',[8,14.24,8.56],[.53,.14,.31],'steel',motif='optic')

    # Magazine only: original W114 exposed carrier in unmodified world frame.
    # The source-bone upper collar remains on the fixed receiver, as W114 did.
    box('magazine','Magazine_core',[8.00624,8.24,11.77],[.94,2.94,2.45],'olive',(-8,0,0),'magazine','magazine')
    box('magazine','Magazine_neck',[8.00624,9.91,11.80],[.96,.63,2.42],'olive',motif='magazine',part='magazine')
    box('magazine','Magazine_floorplate',[8.00624,6.72,11.71],[1.05,.27,2.70],'olive',motif='floorplate',part='magazine')
    beam('magazine','Magazine_red_latch',[8.00624,9.70,10.72],[8.00624,9.15,10.03],1.25,.17,'red','redline','magazine')
    box('magazine','Magazine_rear_insert',[8.00624,10.70,12.53],[1.05,2.12,.37],'olive',part='magazine')

    groups=collections.Counter(s['group'] for ss in parts.values() for s in ss)
    historical=[BASE,BB,'scripts/generate_reload_w114_blast_furnace.py','scripts/generate_reload_models_w100.py',
        'scripts/generate_surface_w115_hammerhead.py',
        ASSET+'models/weapon_reload_w114_blast_furnace/blast_furnace_body.json',
        ASSET+'models/weapon_reload_w114_blast_furnace/blast_furnace_magazine.json']
    raw=[FBX,W31/'references/blast_furnace.jpg',FBX.parent/'BFFrame_Diffuse.png']
    return dict(stage='W127',revision='semantic-r2',id='blast_furnace',schema_version=2,
        generator='scripts/generate_surface_w123_blast_furnace.py',source=metadata,
        method='Authored meaningful opaque volumes, open mechanical windows, bore and optic hood; no component-to-element mapping, alpha cards, or triangle adapters.',
        source_mapping='[8+X*scale,8+Z*scale,8+Y*scale]; muzzle -Z, original axis/scale and [8,8,8] carrier; no recentering',
        rotation_order='Rz*Ry*Rx',max_assembled_elements=1000,palette=PALETTE,groups=dict(groups),parts=parts,
        partition='Moving W114 magazine carrier only. Original insertion coordinates, no separate part recenter or display. Fixed well retains upper collar; geometry reauthored.',
        canonical_reload_delta='249 = 237 body + 12 magazine; no canonical/reload count delta. New full is exact new body+magazine union.',
        uv_policy='1024 RGBA, unique aspect-proportional face islands with 2px dilation. Clean alloy fields, source-derived panel motifs, vents, stipple and red pinstripes. No noisy diffuse reprojection.',
        required_air_probes={'trigger_guard':[8,10.0,4.5],'stock_triangle':[8,11.0,16.4],
            'optic_aperture':[8,14.75,7.90],'muzzle_entry':[8,12.78,-6.70],
            'left_barrel_slot':[7.12,13.05,0],'right_barrel_slot':[8.88,13.05,0],
            'stock_window_left':[7.30,11.95,14.50],'stock_window_right':[8.70,11.95,14.50]},
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in historical},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
        limitations=['Faceted reinterpretation; small compound curves and fasteners simplified.',
            'Single source photo establishes supplied-side paint only; reverse markings inferred from diffuse.',
            'Static opaque paint and highlights; no PBR, live optics or source shader recreation.',
            'Offline evidence only; native parsing, held/ADS/reload and 10-20 displays pending master.'])


def face_points(e,face):
    # Same UV corner order as the existing native offline renderer.
    return renderer_vertices(e)[list(FACES[face])]


_RENDER=None

def renderer_vertices(e):
    global _RENDER
    if _RENDER is None:_RENDER=renderer()
    return _RENDER['vertices'](e)


def make_tile(spec,face,w,h,meshes):
    role=spec['material'];base=np.array(PALETTE[role],float)
    yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
    light=.96+.065*np.exp(-((v-.28)/.40)**2)
    col=np.broadcast_to(base,(h,w,3)).copy()*light[:,:,None]
    rim=(xx==0)|(yy==0)|(xx==w-1)|(yy==h-1)
    if role not in ('rubber','recess'):col[rim]=np.minimum(255,base+12)
    tile=Image.fromarray(np.dstack((np.clip(col,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8'))))
    dr=ImageDraw.Draw(tile);motif=spec['motif'];side=face in ('west','east')
    pts=face_points(spec['geometry'],face)
    world=pts[0]+u[:,:,None]*(pts[1]-pts[0])+v[:,:,None]*(pts[3]-pts[0])
    wy,wz=world[:,:,1],world[:,:,2]
    def line(points,color,width=1):dr.line(points,fill=color,width=width)
    def paint(mask,color):
        nonlocal tile,dr
        a=np.array(tile);a[mask,:3]=color;tile=Image.fromarray(a);dr=ImageDraw.Draw(tile)
    def seam(points,color='#292d31'):
        line([(int(x*w),int(y*h)) for x,y in points],color,max(1,round(h/100)))
    if motif in ('receiver','rear_panel','nose','well','armory_vents') and side:
        # Source panel borders: continuous recessed lines, no protruding sheets.
        seam([(.05,.13),(.34,.13),(.34,.23),(.55,.23),(.58,.12),(.94,.12),(.96,.80),(.75,.80),(.73,.90),(.06,.90),(.05,.13)])
        seam([(.07,.10),(.33,.10)],'#777d80')
        for fx,fy in ((.07,.20),(.92,.75)):
            cx=int(w*fx);cy=int(h*fy);r=max(1,round(min(w,h)*.035))
            dr.ellipse((cx-r,cy-r,cx+r,cy+r),fill='#24282b',outline='#899093')
            line([(cx-r+1,cy),(cx+r-1,cy)],'#444c52')
    if motif=='armory_vents' and side:
        # Two rows of four original vent glyphs and the lower fine rectangular grid.
        for j in range(2):
            for i in range(4):
                z=.75+i*.42;y=12.03+j*.17
                mask=(abs(wz-z)<.075)&(abs(wy-y)<.055)
                edge=mask&((abs(wz-z)>.044)|(abs(wy-y)>.033))
                paint(mask,[24,28,31]);paint(edge,[84,88,89])
        grid=(wz>-.40)&(wz<1.35)&(wy<11.81)
        paint(grid&((np.mod(wz+.40,.19)<.018)|(np.mod(wy,.14)<.014)),[112,113,109])
    if motif=='nose' and side:
        mask=(wy>11.97)&(wy<12.26)&(wz>-5.65)&(wz<-4.05)
        paint(mask&(np.mod(wy,.065)<.022),[24,28,32])
    if motif=='breech' and side:
        mask=(abs(wy-13.15)<.17)&(wz>7.18)&(wz<7.70)
        paint(mask,[30,32,36])
        mask=(abs(wy-12.77)<.15)&(wz>8.05)&(wz<8.65)
        paint(mask,[99,25,27])
    if motif in ('barrel','redline'):
        if side:paint((np.mod(wz,.17)<.02)&(wy>12.94),[240,89,64])
    if motif=='crown' and face=='up':
        for fx in (.14,.86):line([(int(fx*w),1),(int(fx*w),h-2)],'#a3a6a4')
        if spec['geometry']['name']=='Receiver_crown_front':
            for y in range(3,h-2,9):line([(2,y),(w-3,y)],'#292f34',2)
    if motif in ('grip','foregrip','pad'):
        # Fine crossed fabric / raised ribs based on the supplied original.
        if motif=='foregrip':
            paint((np.mod(wz+2,.11)<.025),[19,23,26])
        else:
            paint((np.mod(xx+yy,9)==0)|(np.mod(xx-yy,9)==0),[39,42,44])
    if motif=='magazine' and side:
        # Narrow long channels and a sweeping embossed diagonal, all on solid core.
        for q in (.24,.52,.80):
            line([(int(w*q),2),(int(w*q),h-3)],'#292e29',max(1,w//60))
            line([(int(w*q)+2,3),(int(w*q)+2,h-3)],'#626657')
        seam([(.06,.72),(.51,.51),(.93,.15)],'#242b29')
        seam([(.07,.75),(.52,.54),(.94,.18)],'#858676')
    if motif=='well' and side:
        cx=int(w*.72);cy=int(h*.36);r=max(2,int(h*.12))
        dr.ellipse((cx-r,cy-r,cx+r,cy+r),fill='#242b29',outline='#4d5247')
        # Tall stamped U-shaped mark visible beside original magazine well.
        line([(int(w*.24),int(h*.80)),(int(w*.24),int(h*.28)),(int(w*.31),int(h*.22)),(int(w*.38),int(h*.28)),(int(w*.38),int(h*.80))],'#92917b')
    if motif in ('rod','window') and side:
        line([(2,max(1,h//3)),(w-3,max(1,h//3))],'#a5adb2' if role=='steel' else '#777c7b')
    if motif=='rail' and face in ('up','west','east'):
        for y in range(3,h-2,7):line([(1,y),(w-2,y)],'#1c2227',2)
    if motif=='optic' and side:
        dr.rectangle((max(1,w//4),max(1,h//4),max(2,w*3//4),max(2,h*3//4)),outline='#929795')
    return tile


def compile_models(d,meshes):
    # Atlas allocation is by physical face area, with extra texels for identity.
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for part,ss in d['parts'].items():
        for spec in ss:
            e=spec['geometry'];e['faces']={}
            for f in FACES:
                p=face_points(e,f);width=np.linalg.norm(p[1]-p[0]);height=np.linalg.norm(p[3]-p[0])
                density=28 if spec['motif'] in ('armory_vents','receiver','magazine','well','breech') else 20
                w=max(5,int(math.ceil(width*density)));h=max(5,int(math.ceil(height*density)))
                requests.append((h,w,e['name'],f,spec))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]))
    x=y=2;row=0;ledger=[]
    for h,w,name,f,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError(f'Atlas overflow at {name}/{f} {y+h}')
        tile=make_tile(spec,f,w,h,meshes)
        atlas.paste(Image.fromarray(np.pad(np.array(tile),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uv=[v*16/EDGE for v in (x,y,x+w,y+h)]
        spec['geometry']['faces'][f]=dict(uv=uv,texture='#0')
        ledger.append(dict(element=name,face=f,pixels=[x,y,x+w,y+h],texels=w*h))
        x+=w+4;row=max(row,h)
    d['atlas']=dict(size=EDGE,gutter=2,face_islands=len(ledger),used_texels=sum(v['texels'] for v in ledger),islands=ledger)
    models={p:dict(credit='W127 Blast Furnace semantic solids / deliberate face UV',
        textures={'0':'destiny:item/weapon/w123/blast_furnace','particle':'destiny:item/weapon/w123/blast_furnace'},
        elements=[copy.deepcopy(s['geometry']) for s in ss]) for p,ss in d['parts'].items()}
    full=copy.deepcopy(models['body']);full['elements']+=copy.deepcopy(models['magazine']['elements'])
    full['display']=json.loads((ROOT/BASE).read_bytes())['display'];models['full']=full
    assert len(full['elements'])<=MAX_ELEMENTS
    return atlas,models

def inspection(d,atlas,models):
    elements=[];groups=[]
    for part in ('body','magazine'):
        children=[]
        for e in models[part]['elements']:
            b=copy.deepcopy(e);r=b.pop('rotation');b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[q*EDGE/16 for q in f['uv']]
            for f in FACES:b['faces'].setdefault(f,dict(uv=[0,0,0,0],texture=None))
            elements.append(b);children.append(b['uuid'])
        groups.append(dict(name=part,uuid=uid(part),origin=[8,8,8],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='W127 Blast Furnace semantic solids',
        resolution={'width':EDGE,'height':EDGE},elements=elements,outliner=groups,
        textures=[dict(name='blast_furnace.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=models['full']['display'],destiny_w123={'rotationOrder':'RzRyRx','anchor':[8,8,8],'nativeAccepted':False})


def source_triangles(meshes):
    # Original untouched FBX topology and positions, uniformly reference recolored
    # by functional region. This is not a recovered original PBR/source shader.
    out=[]
    for mesh in meshes:
        for tri,mag in zip(mesh['vertices'][mesh['faces']],mesh['faceMagazine']):
            x,y,z=tri.mean(0);role='frame'
            if mag:role='olive'
            elif mesh['material']!='Frame':role='frame'
            elif z<-5.95:role='steel'
            elif z<3 and y>12.25 and y<13.35 and x>7.22 and x<8.78:role='red'
            elif z>6.8 and z<8.9 and y>12.4:role='red'
            elif z>9.1 and z<9.5 and y>12.4:role='violet'
            elif z>10.5 and z<15.7 and y>13:role='rubber'
            elif y<9.85 and z<9.8:role='rubber'
            elif z<3 and y<11.7:role='rubber'
            elif y<11.3 and z>3:role='olive'
            n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=max(np.linalg.norm(n),1e-20)
            out.append((tri,np.zeros((3,2)),np.array([[PALETTE[role]+[255]]],np.uint8),n))
    return out


def comparison(d,meshes,atlas,models):
    helper=renderer();arrays=[source_triangles(meshes),helper['model_triangles']({'full':models['full']},atlas,{})]
    w,h=1000,335;sheet=Image.new('RGB',(2*w,1780),'#151d27');dr=ImageDraw.Draw(sheet)
    dr.text((20,12),'BLAST FURNACE | W127 SEMANTIC SOLIDS + FACE UV | OFFLINE',fill='#eef2f6',font_size=25)
    ref=Image.open(W31/'references/blast_furnace.jpg').convert('RGB').crop((840,195,1920,710));ref.thumbnail((730,330));sheet.paste(ref,(15,50))
    count=len(models['full']['elements'])
    for i,line in enumerate([f'{count} solid cuboids = {len(models["body"]["elements"])} body + {len(models["magazine"]["elements"])} magazine',
        '0 alpha shells / 0 triangle adapters / 1024 face atlas',
        'Left: unchanged 29,124-triangle FBX / reference recolor',
        'Open barrel slots / stock window / optic / trigger guard',
        'Deep muzzle / broad black receiver / red barrel + lock',
        'Exact display + carrier frame / native pending master']):
        dr.text((780,65+i*43),line,fill='#d9e4eb',font_size=21)
    dr.text((20,377),'RAW FBX / functional reference recolor (not PBR)',fill='#f2f4f6',font_size=21)
    dr.text((w+20,377),f'NEW / {count} authored solids / painted face atlas',fill='#f2f4f6',font_size=21)
    points=np.concatenate([m['vertices'] for m in meshes])
    views=[('SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.50,-.60]),('REAR THREE-QUARTER',[1,.40,.60]),('ALONG BORE / DEPTH',[.32,.13,-1])]
    for row,(label,cam) in enumerate(views):
        camera=np.array(cam,float);camera/=np.linalg.norm(camera);right=np.cross([0,1,0],camera);right/=np.linalg.norm(right);up=np.cross(camera,right)
        proj=np.c_[points@right,points@up];lo,hi=proj.min(0),proj.max(0)
        extent=((lo+hi)/2,min((w-85)/(hi[0]-lo[0]),(h-65)/(hi[1]-lo[1])))
        for col,tris in enumerate(arrays):
            im,_=helper['render'](tris,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,414+row*335))
            dr.text((col*w+18,420+row*335),label,fill='#e4edf5',font_size=19)
    dr.text((20,1752),'Matched framing. Raw recolor is schematic. Native/held/ADS/reload/performance remain unverified.',fill='#c9d6e0',font_size=18)
    return png(sheet)


def review_text(d,counts):
    return f"""# Blast Furnace W127 semantic art

Original reference photo: `/tmp/destiny-weapons-w31/references/blast_furnace.jpg`.
Original FBX: `{FBX}`; original undyed BFFrame Diffuse inspected for panel
structure, vents, well stamp and magazine ribs. Paint rebuilt as Black Armory
black/graphite, red barrel+breech, subdued olive lower receiver and silver muzzle.
W115 highpatch artwork is reference only, not used as new design geometry.
Read-only shared helpers provide FBX parsing and offline cuboid rasterization.
No Blender process, game, GUI or native input used.

{counts['body']} body + {counts['magazine']} moving magazine = {counts['full']}
actual emitted opaque cuboids ({counts['full']*6} explicit faces), no alpha shells,
no triangle-adapter expansion. Full is exactly body+magazine. Canonical 249 equals
W114 237+12; no canonical/reload delta. New geometry intentionally differs.

Large solid receiver, long fore-end roof with actual bilateral red-barrel slots,
red breech/metal lock, open stock window with inset rod, broad upper cheek pad,
sloped foregrip/grip and open trigger guard replace source-component patchwork.
Muzzle octagonal rim and bore walls retain about 0.6 model units of open depth
before the solid nose; original paired optic bases and hood retain an air aperture.
Clean continuous per-face islands carry panel seams, twin four-vent rows, lower
grid, fabric, well stamping, breech recesses, magazine channels and diagonal line.
{d['atlas']['face_islands']} independent islands, {d['atlas']['used_texels']} texels,
1024 RGBA, 2px edge dilation. Every emitted face samples fully opaque texels.

Canonical display is copied verbatim. X thin / -Z muzzle / Y up, source scale
30.010419887180735 and [8,8,8] carrier preserved. Magazine is never recentered.
Its exposed carrier occupies the W114 insertion envelope. Upper well collar stays
fixed; this retains W114 semantics rather than claiming a new perfect source-bone
partition. Independent bbmodel groups retain [8,8,8] origins and zero group rotation.

`comparison.png`: original photo + unchanged raw FBX reference recolor and new
textured geometry at matched side/front-quarter/rear-quarter/along-bore cameras.
Raw recolor is schematic region color, not recovered shader/paint evidence. Actual
photo establishes paint. `inspection.bbmodel` embeds UV/texture and split groups.

Known limits: faceted contours and small compound curves are approximations;
reverse-side markings inferred from grayscale source. No dynamic PBR/optical
refraction. Offline inspection only; master must verify native parsing/substitution,
first/third-person, ADS/inspect, twohand reload/seat, and 10-20 displays. No native
success, exact source silhouette match or performance acceptance is claimed.
"""


def generate(include_review=True):
    meshes,metadata=source_meshes();d=make_design(meshes,metadata);atlas,models=compile_models(d,meshes)
    counts={p:len(models[p]['elements']) for p in ('body','magazine','full')}
    points=np.concatenate([renderer_vertices(e) for e in models['full']['elements']])
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),
        MODEL+'.json':encode(models['full']),MODEL+'_body.json':encode(models['body']),MODEL+'_magazine.json':encode(models['magazine']),
        ART+'inspection.bbmodel':encode(inspection(d,atlas,models)),ART+'review.md':review_text(d,counts).encode()}
    if include_review:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,models)
    manifest=dict(stage='W127',revision=d['revision'],id='blast_furnace',counts=counts,
        max_assembled_elements=MAX_ELEMENTS,assembled_elements=counts['full'],native_accepted=False,
        actual_bounds=[points.min(0).round(7).tolist(),points.max(0).round(7).tolist()],
        canonical_reload_counts={'canonical':249,'body':237,'magazine':12,'delta':0},
        opaque_cuboids=counts['full'],alpha_contour_elements=0,triangle_adapter_elements=0,
        emitted_faces=counts['full']*6,source_triangles=metadata['source_triangles'],semantic_groups=d['groups'],
        texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],anchor=metadata['anchor'],scale=metadata['scale'],
        canonical_display_exact=True,part_display_absent=True,full_is_body_plus_magazine=True,
        worst_two_magazines=counts['body']+2*counts['magazine'],
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(v) for p,v in sorted(outputs.items())},
        validation={'targeted_python':'run scripts/qa/test_surface_w123_blast_furnace.py',
            'native_parser':'pending master','gameplay':'pending master','performance':'not measured; offline only'},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w127/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w127-blast_furnace'))
    assert len(owned)==12 and set(outputs)<=owned
    for p,data in outputs.items():
        dest=ROOT/p
        if args.verify:assert dest.is_file() and dest.read_bytes()==data,'Regenerated asset differs: '+p
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} files; {m["counts"]}; opaque cuboids only; {m["emitted_faces"]} faces')

if __name__=='__main__':main()
