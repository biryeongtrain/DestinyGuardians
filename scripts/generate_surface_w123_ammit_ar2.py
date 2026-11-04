#!/usr/bin/env python3
"""W126 Ammit AR2: authored semantic solids and deliberate face UV islands.

Only this feature's exact batch-owned paths may be written. No DCC, subprocess,
network, historical edits, animation/graph rewrites, or shared build directory.
"""
import argparse
import base64
import collections
import copy
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import runpy
import uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/ammit_ar2/'
ASSET = 'src/main/resources/assets/destiny/'
TEXTURE = ASSET + 'textures/item/weapon/w123/ammit_ar2.png'
MODEL = ASSET + 'models/weapon_surface_w123/ammit_ar2'
BASE = ASSET + 'models/weapon/auto_rifle/ammit_ar2.json'
BB = 'art/blockbench/weapons/w30/ammit_ar2.bbmodel'
RAW = Path('/tmp/destiny-weapons-w30/raw/ammit_ar2/extracted')
FBX = RAW / 'Ammit AR2/Ammit AR2.fbx'
W31 = Path('/tmp/destiny-weapons-w31')
FACES = {'north':(3,2,0,1), 'south':(6,7,5,4), 'west':(2,6,4,0),
         'east':(7,3,1,5), 'up':(2,3,7,6), 'down':(4,5,1,0)}
NORMALS = {'north':(0,0,-1), 'south':(0,0,1), 'west':(-1,0,0),
           'east':(1,0,0), 'up':(0,1,0), 'down':(0,-1,0)}

def sha(b): return hashlib.sha256(b).hexdigest()
def encode(v): return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()
def png(im):
    out = io.BytesIO(); im.save(out, format='PNG'); return out.getvalue()
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'destiny:w123:ammit_ar2:'+s))

def source_meshes():
    metadata = json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha(FBX.read_bytes()) == metadata['source_files']['Ammit AR2/Ammit AR2.fbx']
    parse = runpy.run_path(str(ROOT/'scripts/generate_reload_models_w100.py'))['parse_fbx']
    roots = parse(FBX)
    objects = next(n[2] for n in roots if n[0]=='Objects')
    links = [n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models = {n[1][0]:n for n in objects if n[0]=='Model'}
    meshes = []
    for node in objects:
        if node[0]!='Geometry': continue
        model_id = next(parent for child,parent in links if child==node[1][0])
        model = models[model_id]; name = model[1][1].split('\x00')[0]
        if name not in metadata['source_objects']: continue
        properties = {p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(properties['Lcl Rotation'], [-90,0,0], atol=.0001)
        assert properties['Lcl Scaling']==[100,100,100]
        assert properties.get('Lcl Translation',[0,0,0])==[0,0,0]
        children = {c[0]:c for c in node[2]}
        raw = np.array(children['Vertices'][1][0]).reshape(-1,3)
        # Exact Ammit W30 basis: length=Y, thin=X, muzzle=-Y. No Recluse axis swap.
        vertices = raw[:,[0,2,1]] * metadata['scale'] + metadata['anchor']
        fs=[];face=[]
        for i in children['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3
                fs.append(face);face=[]
        layer=next(c for c in node[2] if c[0]=='LayerElementUV' and c[1][0]==0)
        values={c[0]:c[1][0] for c in layer[2]}
        assert values['MappingInformationType']=='ByPolygonVertex' and values['ReferenceInformationType']=='IndexToDirect'
        uv=np.array(values['UV']).reshape(-1,2)[np.array(values['UVIndex'])].reshape(-1,3,2)
        meshes.append(dict(name=name, vertices=vertices, faces=np.array(fs), uv0=uv, geometry_id=node[1][0]))
    assert sum(len(m['faces']) for m in meshes)==metadata['source_triangles']
    points=np.concatenate([m['vertices'] for m in meshes])
    assert np.allclose([points.min(0),points.max(0)],metadata['model_bounds'],atol=1e-5)
    return meshes,metadata

# Geometry is authored below by functional part. The FBX parser above is used
# only for anchors, source evidence, glyph stencils, and offline comparison.
EDGE = 1024
MAX_ELEMENTS = 1000
PALETTE = {
    'blue_alloy':[171,205,222], 'navy':[50,67,87], 'steel':[193,201,208],
    'graphite':[77,83,91], 'rubber':[43,47,54], 'teal':[64,140,151],
    'fluid':[218,89,49], 'black':[25,29,34], 'ivory':[224,226,231],
}


def renderer():
    return runpy.run_path(str(ROOT/'scripts/generate_surface_w115_hammerhead.py'))


def make_design(meshes,metadata):
    parts={'body':[], 'magazine':[]}
    def box(group,name,c,size,mat,angles=(0,0,0),motif='',part='body'):
        c=np.array(c,dtype=float); sz=np.array(size,dtype=float)
        e=dict(name=name,**{'from':(c-sz/2).round(6).tolist(),'to':(c+sz/2).round(6).tolist()},
               rotation=dict(origin=c.round(6).tolist(),**dict(zip('xyz',angles))))
        parts[part].append(dict(kind='solid_cuboid',group=group,material=mat,motif=motif,geometry=e))
    def beam(group,name,a,b,width,depth,mat,motif='',part='body'):
        a=np.array(a,dtype=float); b=np.array(b,dtype=float); d=b-a
        assert abs(d[0])<1e-8
        angle=round(math.degrees(math.atan2(d[2],d[1])),6)
        box(group,name,(a+b)/2,[width,np.linalg.norm(d),depth],mat,(angle,0,0),motif,part)
    def ring_x(group,name,x,y,z,r,thickness,depth,mat):
        for i in range(8):
            a=i*45; t=math.radians(a)
            box(group,f'{name}_{i}',[x,y+r*math.cos(t),z+r*math.sin(t)],
                [depth,thickness,2*r*math.tan(math.pi/8)+.018],mat,(a,0,0))
    def ring_z(group,name,x,y,z,r,thickness,depth,mat):
        for i in range(8):
            a=i*45; t=math.radians(a)
            box(group,f'{name}_{i}',[x+r*math.cos(t),y+r*math.sin(t),z],
                [2*r*math.tan(math.pi/8)+.012,thickness,depth],mat,(0,0,a-90))

    # Long receiver: closed thick nose + open teal tube channel + solid rear.
    # Crown, side sills, and lower shell are separate cross-section volumes.
    box('upper','Upper_crown',[8,13.22,-1.55],[1.02,.28,14.55],'blue_alloy')
    for s in (-1,1):
        box('upper',f'Upper_shoulder_{s}',[8+s*.60,13.08,-1.55],[.34,.36,14.55],
            'blue_alloy',(0,0,s*32))
        box('upper',f'Slot_sill_{s}',[8+s*.65,12.21,.87],[.25,.29,8.25],'blue_alloy')
    for side in (-1,1):
        box('upper',f'Nose_blue_wall_{side}',[8+side*.60,12.54,-6.13],[.25,1.13,5.25],'blue_alloy',motif='nose')
    box('upper','Nose_blue_floor',[8,12.03,-6.13],[1.20,.18,5.25],'blue_alloy')
    box('upper','Nose_navy_chin',[8,11.50,-6.13],[1.42,.94,5.25],'navy',motif='chin')
    box('upper','Upper_navy_breech',[8,11.53,.95],[1.39,1.02,8.25],'navy',motif='vents')
    box('upper','Tube_slot_front_socket',[8,12.66,-3.44],[1.07,1.00,.35],'steel')
    box('upper','Tube_slot_back_socket',[8,12.66,5.08],[1.05,1.00,.32],'steel')
    # Two crossed rectangular cores plus shoulders give the teal tube a faceted
    # section. It has volume across X and is visible through both slot mouths.
    box('tube','Teal_tube_core',[8,12.66,.82],[.62,.74,8.42],'teal',motif='tube')
    box('tube','Teal_tube_width',[8,12.66,.82],[.81,.48,8.42],'teal',motif='tube')
    box('upper','Rear_receiver',[8,12.43,9.90],[1.52,1.60,8.86],'blue_alloy',motif='receiver_logo')
    for s in (-1,1):
        box('upper',f'Rear_chamfer_{s}',[8+s*.67,13.21,9.95],[.28,.24,8.75],
            'blue_alloy',(0,0,s*32))
        beam('upper',f'Receiver_drop_{s}',[8+s*.75,12.75,5.54],[8+s*.75,9.88,5.16],.24,.43,'blue_alloy',motif='brace')
    box('upper','Rear_receiver_crown',[8,13.30,9.90],[1.12,.15,8.86],'blue_alloy')
    box('upper','Rear_end_transition',[8,12.68,14.43],[1.26,1.02,.42],'graphite',(9,0,0))

    # Lower long fore-end is physically separated from upper shroud by air.
    box('foreend','Lower_blue_beam',[8,9.35,-4.40],[1.28,.85,8.90],'blue_alloy',motif='lower_panel')
    box('foreend','Lower_navy_crown',[8,10.09,-6.15],[1.30,.70,5.40],'navy')
    for s in (-1,1):
        box('foreend',f'Lower_chamfer_{s}',[8+s*.56,8.99,-4.40],[.28,.25,8.90],
            'blue_alloy',(0,0,s*32))
    box('foreend','Lower_front_end',[8,9.53,-8.83],[1.25,1.21,.26],'navy',motif='lower_end')
    box('foreend','Rod_recess',[8,10.03,-1.62],[.92,.24,3.65],'graphite')
    box('foreend','Silver_operating_rod',[8,10.36,-1.42],[.60,.38,4.17],'steel',motif='rod')
    box('foreend','Rod_connector',[8,10.38,.72],[.88,.56,.45],'steel')
    box('foreend','Foreend_rear_seat',[8,9.55,.12],[1.47,1.02,.70],'blue_alloy',motif='brace')

    # Original hand and moving magazine remain in their original frame.
    beam('well','Forward_well_wall',[8,9.53,.36],[8,8.70,.80],1.48,.80,'blue_alloy',motif='well')
    beam('well','Rear_well_spine',[8,9.03,4.48],[8,6.36,5.08],1.08,1.05,'blue_alloy',motif='well')
    box('well','Fluid_mount',[8,9.58,2.75],[1.64,1.35,1.45],'blue_alloy')
    beam('well','Lower_well_bridge',[8,5.93,4.65],[8,6.45,5.55],1.13,.52,'steel')
    box('well','Well_receiver_saddle',[8,9.42,3.55],[1.44,.60,3.00],'blue_alloy')
    box('well','Well_throat',[8,8.48,2.59],[1.13,.40,2.47],'graphite')
    beam('well','Rear_well_lug',[8,6.47,4.78],[8,7.62,5.08],1.15,.65,'blue_alloy',motif='well_lug')

    # Sloped pistol grip + open trigger guard, no painted fake holes.
    box('grip','Grip_tang',[8,10.85,6.92],[1.00,.65,1.30],'graphite')
    beam('well','Well_rear_shoulder',[8,9.80,5.10],[8,10.80,6.00],.95,.64,'blue_alloy')
    beam('grip','Grip_backstrap',[8,10.61,7.43],[8,7.16,9.28],1.00,1.48,'graphite',motif='grip')
    for s in (-1,1):
        beam('grip',f'Grip_cheek_{s}',[8+s*.48,10.31,7.57],[8+s*.48,7.29,9.19],.18,.80,'rubber',motif='grip')
    beam('grip','Grip_heel',[8,7.10,8.87],[8,7.32,9.67],1.04,.32,'steel')
    beam('grip','Guard_bottom',[8,6.98,5.66],[8,7.13,9.32],.69,.28,'steel')
    beam('grip','Guard_front',[8,6.94,5.69],[8,9.23,4.92],.68,.28,'steel')
    box('grip','Trigger_pivot',[8,10.58,6.72],[.46,.38,.36],'steel')
    beam('grip','Trigger_hook',[8,10.40,6.76],[8,9.54,6.52],.23,.18,'graphite')
    beam('grip','Trigger_tip',[8,9.53,6.52],[8,9.54,6.19],.23,.16,'graphite')

    # Rear open stock arch: thin under-rail, sloped joint, full rubber pad.
    box('stock','Stock_under_rail',[8,11.88,11.05],[.98,.36,7.87],'steel',motif='rod')
    beam('stock','Stock_front_arch',[8,11.75,7.20],[8,10.85,8.05],.98,.47,'graphite')
    beam('stock','Stock_rear_arch',[8,11.82,14.39],[8,10.90,15.04],.98,.48,'graphite')
    beam('stock','Stock_rubber_pad',[8,12.67,15.20],[8,8.19,15.40],1.09,.97,'rubber',motif='pad')
    beam('stock','Stock_steel_rear',[8,12.72,15.55],[8,8.22,15.87],1.10,.15,'steel')

    # Central orange fluid windows on both sides, inset behind real rim bars.
    for s in (-1,1):
        x=8+s*1.04
        ring_x('fluid',f'Fluid_rim_{s}',x,9.64,2.75,.815,.13,.25,'steel')
        # Opaque overlapping cores under the surrounding ring; no alpha discs.
        box('fluid',f'Fluid_disk_square_{s}',[x,9.64,2.75],[.20,1.15,1.15],'fluid',motif='fluid')
        box('fluid',f'Fluid_disk_vertical_{s}',[x,9.64,2.75],[.20,1.50,.76],'fluid',motif='fluid')
        box('fluid',f'Fluid_disk_horizontal_{s}',[x,9.64,2.75],[.20,.76,1.50],'fluid',motif='fluid')
        box('fluid',f'Fluid_bridge_{s}',[8+s*.76,9.66,2.75],[.49,1.20,1.25],'graphite')

    # Major exposed hoses: deliberate 3-segment bends instead of tessellation.
    for s in (-1,1):
        x=8+s*.77
        beam('hoses',f'Hose_front_{s}',[x,10.58,.24],[x,10.12,1.03],.23,.23,'rubber')
        beam('hoses',f'Hose_middle_{s}',[x,10.12,1.03],[x,10.37,1.72],.23,.23,'rubber')
        beam('hoses',f'Hose_rise_{s}',[x,10.37,1.72],[x,11.01,2.00],.23,.23,'rubber')
        beam('hoses',f'Hose_rear_{s}',[x,10.12,3.51],[x,10.18,4.38],.24,.24,'rubber')
        beam('hoses',f'Hose_rear_rise_{s}',[x,10.18,4.38],[x,11.10,4.88],.24,.24,'rubber')
        box('hoses',f'Hose_coupling_{s}',[x,10.64,.26],[.41,.40,.46],'graphite')
    box('internal','Breech_lower',[8,11.40,6.87],[.81,.52,3.17],'steel',motif='internal_logo')
    box('internal','Breech_rod',[8,12.07,10.11],[.61,.52,3.16],'steel',motif='rod')
    box('internal','Breech_lock',[8,11.45,5.44],[.84,.66,.73],'graphite')

    # Open muzzle: octagonal collar with real bore wall and recessed backstop.
    ring_z('muzzle','Muzzle_collar',8,12.37,-8.91,.455,.13,.26,'steel')
    ring_z('muzzle','Muzzle_bore_wall',8,12.37,-8.48,.368,.10,.67,'graphite')
    box('muzzle','Muzzle_dark_recess',[8,12.37,-8.08],[.63,.63,.07],'black')
    box('muzzle','Muzzle_top',[8,13.04,-8.91],[1.43,.43,.27],'blue_alloy')
    box('muzzle','Muzzle_chin',[8,11.42,-8.91],[1.44,.73,.27],'navy',motif='chin')
    for s in (-1,1):
        box('muzzle',f'Muzzle_outer_flank_{s}',[8+s*.65,12.36,-8.91],[.15,1.46,.27],'navy')

    # Rear peep sight has a physical hole. Rail micro grooves belong to UV.
    box('sight','Sight_rail',[8,13.42,7.98],[.84,.15,5.92],'steel',motif='rail')
    for s in (-1,1):
        box('sight',f'Peep_post_{s}',[8+s*.27,13.95,7.54],[.18,.82,.29],'steel')
    box('sight','Peep_top',[8,14.30,7.54],[.54,.14,.29],'steel')
    box('sight','Peep_base',[8,13.60,7.54],[.66,.18,.34],'graphite')
    box('controls','Upper_indicator',[7.44,12.99,10.48],[.10,.17,.20],'graphite',motif='indicator')
    for s in (-1,1):
        box('controls',f'Charge_latch_{s}',[8+s*.73,11.61,3.34],[.18,.38,1.12],'navy',motif='indicator')

    # The five-piece independently moving magazine keeps FBX bounds and origin.
    # Its backward rake follows the measured FBX YZ hull, with horizontal neck/base
    # at the original insertion and bottom extents, never a recentered part.
    box('magazine','Magazine_body',[8,7.12,2.59],[.94,2.55,2.33],'teal',(-16.3,0,0),motif='magazine',part='magazine')
    box('magazine','Magazine_base',[8,5.70,3.04],[1.00,.24,2.49],'graphite',(0,0,0),part='magazine')
    box('magazine','Magazine_neck',[8,8.51,2.14],[.87,.30,2.49],'graphite',(0,0,0),part='magazine')
    for s in (-1,1):
        box('magazine',f'Magazine_edge_{s}',[8+s*.40,7.12,2.59],[.17,2.55,2.33],'teal',(-16.3,0,0),motif='magazine_edge',part='magazine')
    historical=[BB,BASE,'scripts/generate_reload_models_w100.py','scripts/generate_surface_w115_hammerhead.py']
    raw=[FBX,W31/'references/ammit_ar2.jpg',FBX.parent/'01b0eb80_Diffuse.png',FBX.parent/'1ba2eb80_Diffuse.png',FBX.parent/'c0b2eb80_GStack.png',FBX.parent/'Ammit AR2.blend']
    ledger=collections.Counter(s['group'] for ss in parts.values() for s in ss)
    return dict(stage='W126',revision='semantic-r2',id='ammit_ar2',schema_version=2,
        generator='scripts/generate_surface_w123_ammit_ar2.py',source=metadata,
        method='Authored semantic solid cuboids; functional beams, sloped grip/stock, open rails, deep muzzle and dual fluid rims. No component extrusion, alpha skins, triangle adapters, or whole diffuse projection.',
        source_mapping='[8+source.X*scale,8+source.Z*scale,8+source.Y*scale]; original anchor and scale; no recentering',
        rotation_order='Rz*Ry*Rx',max_assembled_elements=MAX_ELEMENTS,palette=PALETTE,
        groups=dict(ledger),parts=parts,
        partition='Only Magazine functional assembly, in FBX 907055937 original coordinates; body fluid windows/grip/trigger stay fixed.',
        uv_policy='1024 RGBA; authored continuous face islands, physical aspect ratio, 2px edge dilation. Raw OMOLON glyph triangles selectively rasterized to receiver face islands. Source grip dots/reference fluid three-arm motif redrawn. No whole diffuse texture reprojection.',
        paint_references={'default_paint':str(W31/'references/ammit_ar2.jpg'),'raw_fbx':str(FBX),
            'grip_pattern':str(FBX.parent/'01b0eb80_Diffuse.png'),'magazine_plain_undyed':str(FBX.parent/'1ba2eb80_Diffuse.png'),'inner_logo_mask':str(FBX.parent/'c0b2eb80_GStack.png')},
        source_landmarks={m['name']:[m['vertices'].min(0).round(6).tolist(),m['vertices'].max(0).round(6).tolist()] for m in meshes},
        required_air_probes={'long_frame':[8,10.70,-5.0],'rear_stock':[8,10.0,12.5],'trigger_guard':[8,8.15,6.65],'muzzle_entry':[8,12.37,-8.90]},
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in historical},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
        limitations=['Single original photo does not establish reverse-side paint or exact original ADS.',
            'Faceted cuboid reinterpretation; tiny source chamfers and screws intentionally simplified.',
            'Static opaque fluid and highlights; no PBR, refraction or animated liquid.',
            'Offline CPU render only; native parser, pack substitution, held views, ADS, reload and 10-20 display test belong to master.'])


def face_points(e,face):
    # Same UV corner order as the existing native offline renderer.
    return renderer_vertices(e)[list(FACES[face])]


_RENDER=None

def renderer_vertices(e):
    global _RENDER
    if _RENDER is None:_RENDER=renderer()
    return _RENDER['vertices'](e)


_INNER_MASK=None

def make_tile(spec,face,w,h,meshes):
    role=spec['material'];base=np.array(PALETTE[role],float)
    # Clean large material field with a modest broad highlight, no random dirt.
    yy,xx=np.mgrid[:h,:w]; u=(xx+.5)/w; v=(yy+.5)/h
    light=.96+.055*np.exp(-((v-.27)/.40)**2)
    color=np.broadcast_to(base,(h,w,3)).copy()*light[:,:,None]
    rim=(xx==0)|(yy==0)|(xx==w-1)|(yy==h-1)
    if role not in ('rubber','fluid','black'):color[rim]=np.minimum(255,base+9)
    tile=Image.fromarray(np.dstack((np.clip(color,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8'))))
    dr=ImageDraw.Draw(tile); motif=spec['motif']; side=face in ('west','east')
    pts=face_points(spec['geometry'],face)
    world=pts[0]+u[:,:,None]*(pts[1]-pts[0])+v[:,:,None]*(pts[3]-pts[0])
    def line(points,fill,width=1):dr.line(points,fill=fill,width=width)
    if motif in ('grip','pad') and role=='rubber':
        for y in range(4,h-2,7):
            for x in range(3+(y//7%2)*3,w-2,7):
                dr.ellipse((x,y,x+2,y+2),fill=(26,29,34,255))
                dr.point((x,y),fill=(57,62,69,255))
    if motif=='rail' and face in ('up','west','east'):
        for x in range(5,w-2,8):line([(x,1),(x,h-2)],(94,105,116,255))
    if side and motif in ('nose','lower_panel','chin','receiver_logo','well','magazine','rod'):
        line([(2,h-4),(w-3,h-4)],tuple((base*.80).astype(int))+(255,))
        if motif in ('nose','lower_panel','receiver_logo'):
            line([(3,3),(w-4,3)],tuple(np.minimum(255,base+15).astype(int))+(255,))
    if motif=='vents' and side:
        # The reference metal perforation insert is paint, not 30 tiny cubes.
        y=world[:,:,1];z=world[:,:,2]
        patch=(z>-.85)&(z<2.15)&(y>11.40)&(y<11.95)
        a=np.array(tile);a[patch,:3]=[158,170,178]
        dots=patch&(np.mod(z+.85,.28)<.085)&(np.mod(y-11.40,.20)<.075)
        a[dots,:3]=[43,50,59];tile=Image.fromarray(a);dr=ImageDraw.Draw(tile)
    if motif in ('indicator',) and side:
        dr.rounded_rectangle((max(1,w//5),max(1,h//3),max(2,w*4//5),max(2,h*2//3)),radius=1,fill='#b64b4c')
    if motif=='fluid' and side:
        # Three-arm orange motif is redrawn from the original reference image,
        # using shared world Y/Z coordinates across the overlapping opaque cores.
        a=np.array(tile);p=world-np.array([8,9.64,2.75]);r=np.hypot(p[:,:,1],p[:,:,2]);theta=np.arctan2(p[:,:,1],p[:,:,2])
        rings=(abs(r-.63)<.018)|(abs(r-.48)<.013)|(abs(r-.19)<.018)
        arms=(np.cos(3*theta+5.8*r)>.965)&(r>.23)&(r<.59)
        a[rings|arms,:3]=[241,174,135]
        a[(r>.67)&(r<.70),:3]=[171,65,37]
        tile=Image.fromarray(a);dr=ImageDraw.Draw(tile)
    if motif in ('receiver_logo','internal_logo') and side:
        glyphs=[('Main - Omolon Logo',.20),('Inner Omolon Logo',0)] if motif=='receiver_logo' else [('Inner Omolon Logo',0)]
        # Both original marks get visible receiver face space. Each source side
        # is independently rasterized, preserving the original stroke direction.
        q0=pts[0,[1,2]];A=np.column_stack((pts[1,[1,2]]-q0,pts[3,[1,2]]-q0))
        if abs(np.linalg.det(A))>1e-10:
            inv=np.linalg.inv(A)
            for meshname,drop in glyphs:
                mesh=next(m for m in meshes if m['name']==meshname)
                for tri,uv0 in zip(mesh['vertices'][mesh['faces']],mesh['uv0']):
                    if (tri[:,0].mean()<8)!=(face=='west'):continue
                    q=(tri[:,[1,2]]-np.array([drop,0])-q0)@inv.T*[w,h]
                    if meshname=='Main - Omolon Logo':
                        # W30's axis swap reverses the glyph reading direction.
                        # Reflect only the glyph stencil in its own face island.
                        center=(mesh['vertices'][:,[1,2]].min(0)+mesh['vertices'][:,[1,2]].max(0))/2-np.array([drop,0])
                        center=(center-q0)@inv.T*[w,h]
                        q[:,0]=2*center[0]-q[:,0]
                        dr.polygon([tuple(v) for v in q],fill=tuple(PALETTE['ivory'])+(255,))
                    else:
                        # This source object is TWO RECTANGULAR TRIANGLES, not
                        # glyph geometry. Its original GStack blue-channel mask
                        # holds the OMOLON letters. Selectively transfer that
                        # mask via the original UV0; never paint its full quad.
                        global _INNER_MASK
                        if _INNER_MASK is None:
                            _INNER_MASK=np.array(Image.open(FBX.parent/'c0b2eb80_GStack.png').convert('RGB'))[:,:,2]
                        a,b,c=q;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                        if abs(den)<1e-10:continue
                        wa=((b[1]-c[1])*(xx+.5-c[0])+(c[0]-b[0])*(yy+.5-c[1]))/den
                        wb=((c[1]-a[1])*(xx+.5-c[0])+(a[0]-c[0])*(yy+.5-c[1]))/den;wc=1-wa-wb
                        uv=wa[:,:,None]*uv0[0]+wb[:,:,None]*uv0[1]+wc[:,:,None]*uv0[2]
                        # Source decal V runs backwards relative to readable
                        # face-U on BOTH sides. Normalize the letter direction.
                        uv[:,:,1]=uv0[:,1].min()+uv0[:,1].max()-uv[:,:,1]
                        ih,iw=_INNER_MASK.shape
                        tx=np.clip((uv[:,:,0]*iw).astype(int),0,iw-1);ty=np.clip(((1-uv[:,:,1])*ih).astype(int),0,ih-1)
                        mark=(wa>=0)&(wb>=0)&(wc>=0)&(_INNER_MASK[ty,tx]>=16)
                        arr=np.array(tile);arr[mark,:3]=PALETTE['ivory'];tile=Image.fromarray(arr);dr=ImageDraw.Draw(tile)
    if motif=='well_lug' and side:
        # Source photograph shows the concentric fastener at the lower joint.
        d=min(w,h)*.52;cx=w*.52;cy=h*.58
        dr.ellipse((cx-d/2,cy-d/2,cx+d/2,cy+d/2),fill='#4a5660',outline='#b9c5cc',width=1)
    return tile


def compile_models(d,meshes):
    # Atlas allocation is by physical face area, with extra texels for identity.
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for part,ss in d['parts'].items():
        for spec in ss:
            e=spec['geometry'];e['faces']={}
            for f in FACES:
                p=face_points(e,f);width=np.linalg.norm(p[1]-p[0]);height=np.linalg.norm(p[3]-p[0])
                density=38 if spec['motif']=='fluid' else 28 if spec['motif'] in ('receiver_logo','internal_logo','magazine','grip') else 20
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
    models={p:dict(credit='W126 Ammit AR2 semantic solids / deliberate face UV',
        textures={'0':'destiny:item/weapon/w123/ammit_ar2','particle':'destiny:item/weapon/w123/ammit_ar2'},
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
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='W126 Ammit AR2 semantic solids',
        resolution={'width':EDGE,'height':EDGE},elements=elements,outliner=groups,
        textures=[dict(name='ammit_ar2.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=models['full']['display'],destiny_w123={'rotationOrder':'RzRyRx','anchor':[8,8,8],'nativeAccepted':False})


def source_triangles(meshes):
    # Raw triangle positions and topology are unmodified. Reference recolor is
    # labelled, so it is not confused with the undyed extracted diffuse.
    source=[]
    for mesh in meshes:
        for t in mesh['vertices'][mesh['faces']]:
            x,y,z=t.mean(0);name=mesh['name'];role='steel'
            if name=='Barrel Tube':role='teal'
            elif name.startswith('Fluid'):role='fluid'
            elif name=='Magazine':role='teal' if y>5.85 else 'graphite'
            elif 'Logo' in name:role='ivory'
            elif name=='Stock':role='rubber'
            elif name=='Main - Body':role='navy' if (z<5.4 and y<12 and y>10.8) or (z<.2 and y>9.8 and y<10.7) else 'blue_alloy'
            elif name=='Middle':role='rubber' if z>7 and y<10.8 else 'blue_alloy' if y<9.6 else 'steel'
            elif name=='Main - Spot':role='graphite'
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20)
            source.append((t,np.zeros((3,2)),np.array([[PALETTE[role]+[255]]],dtype=np.uint8),n))
    return source


def comparison(d,meshes,atlas,models):
    helper=renderer();arrays=[source_triangles(meshes),helper['model_triangles']({'full':models['full']},atlas,{})]
    w,h=1000,335;sheet=Image.new('RGB',(2*w,1780),'#151d27');dr=ImageDraw.Draw(sheet)
    dr.text((20,12),'AMMIT AR2 | W126 SEMANTIC VOLUMES + FACE UV | OFFLINE REVIEW',fill='#eef2f6',font_size=25)
    ref=Image.open(W31/'references/ammit_ar2.jpg').convert('RGB').crop((830,215,1920,900));ref.thumbnail((700,330));sheet.paste(ref,(15,50))
    count=len(models['full']['elements'])
    for i,line in enumerate([f'{count} solid cuboids = {len(models["body"]["elements"])} body + {len(models["magazine"]["elements"])} magazine',
        '0 alpha shells / 0 triangle adapters / 1024 face atlas',
        'Raw FBX geometry left: reference recolor, no simplification',
        'Open upper tube slot / fore-end gap / rear stock / peep',
        'Source glyph/mask stencils + orange three-arm motif',
        'Exact display; original anchor/scale; native pending master']):
        dr.text((780,65+i*43),line,fill='#d9e4eb',font_size=22)
    dr.text((20,377),'RAW FBX / 20,225 triangles / reference recolor',fill='#f2f4f6',font_size=22)
    dr.text((w+20,377),f'NEW / {count} solids / authored face atlas',fill='#f2f4f6',font_size=22)
    points=np.concatenate([m['vertices'] for m in meshes])
    views=[('SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.50,-.60]),('REAR THREE-QUARTER',[1,.40,.60]),('ALONG BORE / DEPTH',[.32,.13,-1])]
    for row,(label,cam) in enumerate(views):
        camera=np.array(cam,float);camera/=np.linalg.norm(camera);right=np.cross([0,1,0],camera);right/=np.linalg.norm(right);up=np.cross(camera,right)
        proj=np.c_[points@right,points@up];lo,hi=proj.min(0),proj.max(0)
        extent=((lo+hi)/2,min((w-85)/(hi[0]-lo[0]),(h-65)/(hi[1]-lo[1])))
        for col,tris in enumerate(arrays):
            im,_=helper['render'](tris,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,414+row*335))
            dr.text((col*w+18,420+row*335),label,fill='#e4edf5',font_size=19)
    dr.text((20,1752),'Matched orthographic framing. No native/held/ADS/reload/performance acceptance is implied.',fill='#c9d6e0',font_size=18)
    return png(sheet)


def review_text(d,counts):
    return f"""# Ammit AR2 W126 semantic redesign

Implemented in the isolated w126-ammit_ar2 worktree. Reference: original
`/tmp/destiny-weapons-w31/references/ammit_ar2.jpg`, raw Ammit FBX and its
original W30 basis/anchor, original Main/Inner OMOLON glyph meshes. Raw grip
Diffuse was inspected for dot texture and the unpainted magazine Diffuse was
inspected to avoid using it as finished paint. A separate Blender --background --factory-startup --disable-autoexec process
read the original .blend material links only; no GUI or source save was used.
The Inner Omolon Logo quad uses beb2eb80 Diffuse and c0b2eb80 GStack; the
actual letter mask is its GStack blue channel, not its rectangle geometry.

Body {counts['body']} + moving magazine {counts['magazine']} = {counts['full']}
actual emitted opaque cuboids, {counts['full']*6} faces, zero alpha elements,
zero triangle-adapter elements. Full and split are alternative representations.
Even two simultaneously displayed magazines total {counts['body']+2*counts['magazine']}.

The former 960-element component-profile caps/walls are replaced by authored
functional solids. Open upper channel surrounds a faceted teal tube; long
blue/navy fore-end and silver rod retain the real inter-frame gap. Sloped grip,
trigger guard and rear stock surround real air. A physical open peep and
muzzle collar preserve bore depth. The receiver logo is lowered 0.20 units within its new side face to stay clear
of the top chamfer; the original inner mark is visible on the lower receiver
face. Each fluid window has eight solid rim bars,
three filled opaque cores and a backing mount. No whole body side plates.

1024 RGBA face atlas: {d['atlas']['face_islands']} independent islands with 2px
edge dilation; {d['atlas']['used_texels']} face texels. Large continuous faces
use proportional UV; dots, vents, shallow seams and source glyphs use texture.
Main OMOLON strokes come from raw glyph triangles and inner letters from the
original GStack B mask via UV0, independently for both sides;
fluid rings/three-arm pattern are redrawn from the original photo. Paint uses
clean blue alloy/navy/steel/teal/orange, not undyed diffuse RGB or noisy full
surface reprojection. Static opaque fluid does not reproduce PBR/refraction.

`comparison.png` renders unchanged 20,225-triangle FBX versus new textured solids
in matched side/front-quarter/rear-quarter/along-bore views, with original photo.
Raw is explicitly reference recolored. `inspection.bbmodel` embeds the new atlas,
body/magazine groups and face UV. Offline inspection is separate from native QA.

Canonical display copied exactly; W30 scale, world basis, [8,8,8] anchor and
magazine insertion frame retained. Cuboid approximation is an intentional new
shape, not a promise of old W124 geometry hash equality. Shared packs, Java,
helpers, animation graphs, source assets and sealed historical QA are unchanged.

Master TODO: pack substitution and native parsing; first/third person + ADS,
inspect and twohand; detached magazine and re-insertion through existing reload
coordinates; 10-20 simultaneous display observations. Reverse-side original paint
and true source first-person references remain unavailable in the supplied photo.
"""


def generate(include_review=True):
    meshes,metadata=source_meshes();d=make_design(meshes,metadata);atlas,models=compile_models(d,meshes)
    counts={p:len(models[p]['elements']) for p in ('body','magazine','full')}
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),
        MODEL+'.json':encode(models['full']),MODEL+'_body.json':encode(models['body']),MODEL+'_magazine.json':encode(models['magazine']),
        ART+'inspection.bbmodel':encode(inspection(d,atlas,models)),ART+'review.md':review_text(d,counts).encode()}
    if include_review:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,models)
    manifest=dict(stage='W126',revision=d['revision'],id='ammit_ar2',counts=counts,
        max_assembled_elements=MAX_ELEMENTS,opaque_cuboids=counts['full'],alpha_contour_elements=0,triangle_adapter_elements=0,
        emitted_faces=counts['full']*6,source_triangles=metadata['source_triangles'],semantic_groups=d['groups'],
        texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],anchor=metadata['anchor'],scale=metadata['scale'],
        canonical_display_exact=True,part_display_absent=True,full_is_body_plus_magazine=True,
        worst_two_magazines=counts['body']+2*counts['magazine'],
        generator_sha256=sha(Path(__file__).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(v) for p,v in sorted(outputs.items())},
        validation={'targeted_python':'run scripts/qa/test_surface_w123_ammit_ar2.py',
            'native_parser':'pending master','gameplay':'pending master','performance':'not measured; offline only'},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-25/w126/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w126-ammit_ar2'))
    assert len(owned)==12 and set(outputs)<=owned
    for p,data in outputs.items():
        dest=ROOT/p
        if args.verify:assert dest.is_file() and dest.read_bytes()==data,'Regenerated asset differs: '+p
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} files; {m["counts"]}; opaque cuboids only; {m["emitted_faces"]} faces')

if __name__=='__main__':main()
