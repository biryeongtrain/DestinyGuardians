#!/usr/bin/env python3
"""W127 Duke Mk.44: authored solid revolver, face UVs, original W64 frame.

Bundled numpy/Pillow only; no DCC, subprocess, build, network, or shared writes.
Historical parser/rasterizer are read-only helpers; source islands do not drive
the new geometry. --verify deterministically compares every generated artifact.
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
ID = 'duke_mk_44'
ART = 'art/weapons/w123/duke_mk_44/'
ASSET = 'src/main/resources/assets/destiny/'
MODEL = ASSET + 'models/weapon_surface_w123/duke_mk_44'
TEXTURE = ASSET + 'textures/item/weapon/w123/duke_mk_44.png'
BASE = ASSET + 'models/weapon/hand_cannon/duke_mk_44.json'
RELOAD = ASSET + 'models/weapon_reload_w64/duke_mk_44'
BB = 'art/blockbench/weapons/w30/duke_mk_44.bbmodel'
GENERATOR = 'scripts/generate_surface_w123_duke_mk_44.py'
TEST = 'scripts/qa/test_surface_w123_duke_mk_44.py'
WORKER = 'docs/qa/2026-10-26/w127/duke_mk_44-worker.md'
RAW = Path('/tmp/destiny-weapons-w30/raw/duke_mk_44/extracted')
FBX = RAW / 'DukeMk44.fbx'
PHOTO = Path('/tmp/destiny-weapons-w31/references/duke_mk_44.jpg')
PARSER = 'scripts/generate_reload_models_w100.py'
RASTER = 'scripts/generate_surface_w115_hammerhead.py'
EDGE = 1024
PIVOT = [8, 10.2, 5.17]
CYLINDER_CENTER = [8.00596, 12.80, 3.766]
FACES = {'north': (3,2,0,1), 'south': (6,7,5,4), 'west': (2,6,4,0),
         'east': (7,3,1,5), 'up': (2,3,7,6), 'down': (4,5,1,0)}
PALETTE = {
    'yellow': [103, 135, 192], 'gold_edge': [122, 151, 207],
    'ochre': [78, 106, 155], 'graphite': [60, 63, 64],
    'steel': [100, 104, 103], 'black': [27, 30, 32],
    'wood': [34, 39, 47], 'rubber': [37, 39, 39],
}
# Legacy material keys keep the worker's geometry/UUIDs stable. Colors now follow
# the actual W31 blue-lacquer / dark-grip photo, not its unrequested gold variant.


def sha(data): return hashlib.sha256(data).hexdigest()
def encode(v): return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()
def png(im):
    b=io.BytesIO(); im.save(b, format='PNG'); return b.getvalue()
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'destiny:w127:duke_mk_44:'+s))


_HELPER = None
def renderer():
    global _HELPER
    if _HELPER is None: _HELPER = runpy.run_path(str(ROOT / RASTER))
    return _HELPER


def source_meshes():
    metadata=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha(FBX.read_bytes()) == metadata['source_files']['DukeMk44.fbx']
    parse=runpy.run_path(str(ROOT/PARSER))['parse_fbx']
    roots=parse(FBX); objects=next(n[2] for n in roots if n[0]=='Objects')
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    models={n[1][0]:n for n in objects if n[0]=='Model'}
    meshes=[]
    for node in objects:
        if node[0]!='Geometry': continue
        model=models[next(parent for child,parent in links if child==node[1][0])]
        name=model[1][1].split('\x00')[0]
        if name not in metadata['source_objects']: continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        assert props['Lcl Scaling']==[100,100,100]
        assert props.get('Lcl Translation',[0,0,0])==[0,0,0]
        children={c[0]:c for c in node[2]}
        raw=np.array(children['Vertices'][1][0]).reshape(-1,3)
        # Measured Duke W30 basis, deliberately different from Ammit/Recluse.
        vertices=raw[:,[1,2,0]]*[-metadata['scale'],metadata['scale'],-metadata['scale']]+metadata['anchor']
        faces=[]; face=[]
        for i in children['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3
                faces.append(face); face=[]
        meshes.append(dict(name=name,vertices=vertices,faces=np.array(faces)))
    points=np.concatenate([m['vertices'] for m in meshes])
    assert sum(len(m['faces']) for m in meshes)==7960
    assert np.allclose([points.min(0),points.max(0)],metadata['model_bounds'],atol=1e-5)
    return meshes,metadata


def make_design(meshes, metadata):
    parts={'body':[], 'cylinder':[]}
    def box(group,name,center,size,material,angles=(0,0,0),motif='',part='body'):
        c=np.array(center,float); size=np.array(size,float)
        e=dict(name=name,**{'from':(c-size/2).round(6).tolist(),'to':(c+size/2).round(6).tolist()},
               rotation=dict(origin=c.round(6).tolist(),**dict(zip('xyz',angles))))
        parts[part].append(dict(kind='solid_cuboid',group=group,material=material,motif=motif,geometry=e))
    def beam(group,name,a,b,width,depth,material,motif='',part='body'):
        a=np.array(a,float); b=np.array(b,float); d=b-a
        assert abs(d[0])<1e-8
        angle=round(math.degrees(math.atan2(d[2],d[1])),6)
        box(group,name,(a+b)/2,[width,np.linalg.norm(d),depth],material,(angle,0,0),motif,part)
    def ring(group,name,center,apothem,thickness,depth,material,n=8,part='body',motif=''):
        # N solid longitudinal staves form a real annular cross-section.
        # Used only for mechanical bores/collars; broad body is solid cuboids.
        x,y,z=center
        for i in range(n):
            a=360*i/n; t=math.radians(a)
            box(group,f'{name}_{i}',[x+apothem*math.cos(t),y+apothem*math.sin(t),z],
                [thickness,2*apothem*math.tan(math.pi/n)+.008,depth],
                material,(0,0,a),motif,part)

    # The tall shroud is a solid stepped section, not two alpha silhouette skins.
    # Long lower receiver, upper shoulder and raked nose carry the main mass.
    box('shroud','Shroud_lower',[8,12.16,-1.52],[1.64,1.83,5.95],'yellow',motif='shroud')
    box('shroud','Shroud_upper',[8,13.47,-1.74],[1.68,.83,6.47],'yellow',motif='upper_panel')
    # Paired structural nose flanks leave the front housing's central aperture
    # open; a full-width crossbar here would undesirably fill the recess.
    for s in (-1,1):
        beam('shroud',f'Nose_chamfer_{s}',[8+s*.71,11.34,-4.55],[8+s*.71,13.92,-5.03],.25,.32,'ochre')
        box('shroud',f'Upper_shoulder_{s}',[8+s*.72,13.93,-1.75],[.28,.29,6.44],'gold_edge',(0,0,s*31))
    box('shroud','Lower_dark_sill',[8,11.20,-1.48],[1.50,.20,5.99],'graphite')
    beam('shroud','Rear_raked_shroud',[8,11.32,1.40],[8,13.70,1.77],1.68,.37,'yellow',motif='rear_edge')

    # Continuous top strap bridges the cylinder window and terminates at hammer.
    box('strap','Top_strap',[8,14.48,.09],[1.64,.64,10.84],'yellow',motif='strap')
    box('strap','Top_crown',[8,14.84,.10],[1.20,.15,10.66],'gold_edge',motif='top_rail')
    for s in (-1,1):
        box('strap',f'Top_chamfer_{s}',[8+s*.73,14.73,.10],[.23,.23,10.74],'gold_edge',(0,0,s*35))
        box('strap',f'Slot_shadow_{s}',[8+s*.68,14.02,-.74],[.13,.15,5.93],'black',motif='slot')
    box('strap','Breech_rear',[8,12.94,5.68],[1.54,2.45,.51],'graphite',motif='breech')
    box('strap','Breech_crown',[8,14.14,5.68],[1.44,.30,.60],'yellow')
    box('frame','Cylinder_bottom_rail',[8,11.17,3.69],[1.18,.28,4.70],'graphite',motif='frame')
    beam('frame','Breech_to_grip',[8,11.30,5.82],[8,12.40,6.75],1.47,.70,'graphite',motif='frame')
    box('frame','Cylinder_front_mount',[8,11.49,1.94],[1.12,.50,.49],'graphite')

    # Rectangular front sight housing has an actual deep aperture above the bore.
    # Its rear is the raked shroud, so both opening and recess are measurable.
    for s in (-1,1):
        box('front_window',f'Front_window_pillar_{s}',[8+s*.68,13.37,-5.17],[.26,1.69,.37],'graphite')
    box('front_window','Front_window_lintel',[8,14.22,-5.17],[1.48,.25,.37],'graphite')
    box('front_window','Front_window_sill',[8,12.52,-5.17],[1.45,.21,.37],'graphite')

    # Low exposed barrel: octagonal metal collar + >1 unit of genuine bore depth.
    ring('muzzle','Muzzle_lip',[8,11.94,-6.00],.427,.145,.34,'steel')
    ring('muzzle','Muzzle_bore',[8,11.94,-5.43],.376,.102,.94,'graphite')
    box('muzzle','Muzzle_recess',[8,11.94,-4.91],[.66,.66,.08],'black')

    # Open underbarrel lug. Surface vent perforations remain UV; this big slot
    # is real geometry, separate from the barrel shell in oblique views.
    box('lug','Underlug_top',[8,10.96,-1.55],[1.13,.18,4.60],'graphite')
    box('lug','Underlug_bottom',[8,10.41,-1.55],[1.13,.22,4.49],'graphite',motif='frame')
    for z,name in ((-3.77,'front'),(.67,'rear')):
        box('lug','Underlug_'+name,[8,10.69,z],[1.13,.53,.27],'graphite',motif='lug_end')

    # Open trigger guard, hooked trigger and sloped wood/black grip in the old
    # hand frame. Curved grip is three broad masses with a dark backstrap.
    box('guard','Guard_roof',[8,11.02,4.38],[.91,.28,2.87],'graphite')
    beam('guard','Guard_front',[8,10.94,2.99],[8,9.75,3.03],.72,.24,'graphite')
    beam('guard','Guard_front_corner',[8,9.75,3.03],[8,9.39,3.60],.72,.24,'graphite')
    beam('guard','Guard_bottom',[8,9.39,3.60],[8,9.19,4.97],.72,.24,'graphite')
    beam('guard','Guard_rear_corner',[8,9.19,4.97],[8,9.52,5.60],.72,.25,'graphite')
    beam('guard','Guard_rear',[8,9.52,5.60],[8,10.77,5.94],.72,.25,'graphite')
    box('trigger','Trigger_pivot',[8,10.83,4.92],[.40,.32,.42],'steel')
    beam('trigger','Trigger_curve',[8,10.73,4.86],[8,9.99,4.99],.25,.16,'steel')
    beam('trigger','Trigger_tip',[8,9.99,4.99],[8,9.65,4.74],.25,.17,'steel')
    beam('grip','Grip_tang',[8,12.20,6.66],[8,10.26,6.31],1.60,.96,'graphite',motif='frame')
    beam('grip','Grip_upper_wood',[8,11.87,6.91],[8,10.05,7.15],1.45,1.75,'wood',motif='wood_upper')
    beam('grip','Grip_palm_wood',[8,10.40,7.55],[8,8.65,8.20],1.48,2.00,'wood',motif='wood')
    beam('grip','Grip_lower_wood',[8,9.10,8.13],[8,6.85,8.48],1.46,1.76,'wood',motif='wood')
    beam('grip','Backstrap_upper',[8,11.89,7.59],[8,9.61,8.76],1.59,.32,'graphite')
    beam('grip','Backstrap_lower',[8,9.65,8.88],[8,6.61,9.46],1.61,.31,'graphite')
    beam('grip','Frontstrap_lower',[8,8.81,7.39],[8,6.82,7.57],1.52,.22,'rubber',motif='rubber')
    beam('grip','Grip_heel',[8,6.48,7.63],[8,6.78,9.61],1.72,.31,'graphite',motif='heel')

    # Release knob, hammer with a genuine loop, and open rear notch.
    beam('controls','Release_arm',[6.91,13.43,-.77],[6.91,13.70,-2.00],.34,.33,'graphite',motif='release')
    box('controls','Release_knob',[6.65,13.65,-2.05],[.45,.56,.78],'graphite',motif='knob')
    box('controls','Release_end',[6.41,13.65,-2.05],[.07,.36,.51],'black',motif='screw')
    beam('hammer','Hammer_stem',[8,12.40,6.25],[8,13.85,6.40],.56,.51,'graphite')
    beam('hammer','Hammer_spur',[8,13.71,6.21],[8,14.32,6.80],.48,.45,'graphite')
    # Hammer loop axis X; four bars provide the tiny reference loop without alpha.
    for i in range(8):
        a=i*45; t=math.radians(a)
        box('hammer',f'Hammer_loop_{i}',[8,14.32+.225*math.cos(t),6.80+.225*math.sin(t)],
            [.48,.105,2*.225*math.tan(math.pi/8)+.008],'steel',(a,0,0))
    box('sights','Front_sight',[8,15.005,-4.98],[.61,.15,.51],'graphite')
    for s in (-1,1):
        box('sights',f'Rear_sight_ear_{s}',[8+s*.235,15.005,5.04],[.17,.15,.48],'graphite')
    box('sights','Rear_sight_base',[8,14.92,5.04],[.66,.08,.48],'graphite')

    # Moving cylinder: twelve broad longitudinal exterior facets plus six actual
    # full-depth chamber tubes, webs and spindle. The camera can see down all six
    # holes from either end. This is a mechanical annular volume, not an alpha cap.
    cx,cy,cz=CYLINDER_CENTER
    ring('cylinder_shell','Cylinder_shell',[cx,cy,cz],1.145,.215,2.94,'yellow',n=12,part='cylinder',motif='cylinder')
    centers=[]
    for i in range(6):
        a=math.radians(90+i*60); x=cx+.731*math.cos(a); y=cy+.731*math.sin(a)
        centers.append([round(x,6),round(y,6)])
        ring('chambers',f'Chamber_{i}',[x,y,cz],.277,.104,2.94,'steel',part='cylinder',motif='chamber')
        # Inter-chamber solid radial web closes the interior between the bores.
        t=a+math.pi/6
        box('cylinder_webs',f'Cylinder_web_{i}',[cx+.59*math.cos(t),cy+.59*math.sin(t),cz],
            [.91,.14,2.94],'ochre',(0,0,math.degrees(t)),part='cylinder')
    box('cylinder_webs','Cylinder_spindle',[cx,cy,cz],[.57,.57,3.02],'graphite',part='cylinder',motif='spindle')
    # W64's links keep the lower pivot attachment and Z frame. Their upper joint
    # now meets the new shell BELOW the bottom chamber instead of plugging it.
    box('yoke','Yoke_vertical',[8,10.96,5.17],[.44,1.52,.40],'graphite',part='cylinder',motif='frame')
    box('yoke','Yoke_arm',[8,11.65,4.535],[.44,.30,1.67],'graphite',part='cylinder',motif='frame')

    inputs=[BASE,RELOAD+'_body.json',RELOAD+'_cylinder.json',BB,
            'scripts/generate_reload_models_w64.py',PARSER,RASTER,
            'art/weapons/w31/palette-overrides.json','art/weapons/w31/references.json',
            ASSET+'textures/item/weapon/w30/duke_mk_44.png']
    raw_inputs=[FBX,PHOTO,RAW/'PNG/Dukemk44Barrel_Diffuse.png',RAW/'PNG/Dukemk44Cylinder_Diffuse.png']
    return dict(stage='W127',schema_version=2,id=ID,family='hand_cannon',revision='semantic-r3-blue-photo',
        generator=GENERATOR,source=metadata,
        method='Authored broad solid shroud, strap, curved dark grip, open frame, deep muzzle and six drilled cylinder chambers; no source-island conversion, alpha side plates, meshes or triangle adapters.',
        source_mapping='[8-source.Y*scale,8+source.Z*scale,8-source.X*scale]; muzzle -Z; thin X; up Y',
        rotation_order='Rz*Ry*Rx',anchor=[8,8,8],cylinder_pivot=PIVOT,cylinder_center=CYLINDER_CENTER,
        moving_semantics='Cylinder + chamber walls + spindle + two reauthored yoke links move together around original [8,10.2,5.17]; geometry never recentered; body fixed.',
        yoke_shape_delta='Original vertical [7.78,10.2,4.97]..[8.22,12.25,5.37] shortened to top Y=11.72; original arm Y=12.05..12.45 lowered to 11.50..11.80. Same pivot/base/Z frame; upper joint follows new shell below bottom chamber instead of occluding it.',
        canonical_reload_delta=dict(canonical=232,reload_body=211,reload_cylinder=23,reload_total=234,
            reason='W64 partitions 211 body + 21 original cylinder elements and adds 2 moving yoke links. New canonical deliberately includes its own yoke and equals its new body+cylinder exactly.'),
        max_assembled_elements=1000,palette=PALETTE,parts=parts,
        groups=dict(collections.Counter(s['group'] for ss in parts.values() for s in ss)),
        paint_evidence={'photo':str(PHOTO),'photo_variant':'Blue lacquer exterior / dark grip; supplied W31 light.gg screenshot used for geometry and painted color target.',
            'local_palette_record':'art/weapons/w31/palette-overrides.json: Duke barrel/cylinder dye [0.12,0.22,0.65,1] linear and dark dye [0.012,0.015,0.022,1], explicitly blue/dark light.gg reference.',
            'local_default_record':'art/weapons/w31/references.json: Duke hash 2112909414, screenshot hash 6b0aafe4f3abda9cacc7eee0a0f8106218813c0a427ab02b6fae3f8c1c572067. Existing W30 atlas also visibly blue/black.',
            'paint_correction':'Master rejected unsupported yellow/wood alternate and restored the actual W31 blue/black reference. Legacy internal material keys do not describe output colors.',
            'raw_diffuse':'Neutral/undyed metal sheets with shallow seams/vents; not evidence of finished default RGB. Reverse-side paint and dynamic PBR remain uncertain.'},
        uv_policy='Independent physically proportioned opaque face islands, 2px dilation; material fields, side seams, two barrel vents, dark grip checkering, flutes and fasteners authored in UV. No whole-photo or diffuse projection.',
        source_landmarks={m['name']:[m['vertices'].min(0).round(6).tolist(),m['vertices'].max(0).round(6).tolist()] for m in meshes},
        chamber_centers=centers,chamber_air_z=[2.34,2.55,3.20,4.40,5.17],
        required_air_probes={'guard':[8,10.1,3.9],'underlug':[8,10.70,-1.5],
            'front_frame':[8,13.30,-5.17],'rear_sight':[8,15.02,5.04],
            'above_cylinder':[8,14.10,3.4],'muzzle_entry':[8,11.94,-6.03],
            'muzzle_depth':[8,11.94,-5.12]},
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['Blue lacquer and dark grip follow the supplied W31 screenshot and previous dye record; reverse-side paint is conservative, not separately photo-verified.',
            'Faceted reinterpretation simplifies source bevels; shallow side vents/flutes and fasteners are UV detail.',
            'Opaque static paint; no PBR or exact source reflections. Six chambers are empty bores; no cartridges or ejector animation added.',
            'Offline CPU evidence only. Native parsing, first/third person, ADS, reload and 10-20 display observations belong to master.'])


def face_points(e,face): return renderer()['vertices'](e)[list(FACES[face])]


def make_tile(spec,face,w,h):
    role=spec['material']; base=np.array(PALETTE[role],float)
    yy,xx=np.mgrid[:h,:w]; u=(xx+.5)/w; v=(yy+.5)/h
    # Broad quiet light field, restrained edge wear, no random dirt.
    shade=.97+.035*np.exp(-((v-.24)/.42)**2)
    a=np.zeros((h,w,4),dtype=np.uint8); a[:,:,:3]=np.clip(base*shade[:,:,None],0,255); a[:,:,3]=255
    if role not in ('rubber','black','wood'):
        a[0,:,:3]=np.minimum(255,base+12); a[-1,:,:3]=base*.80
    pts=face_points(spec['geometry'],face)
    world=pts[0]+u[:,:,None]*(pts[1]-pts[0])+v[:,:,None]*(pts[3]-pts[0])
    tile=Image.fromarray(a); dr=ImageDraw.Draw(tile); motif=spec['motif']; side=face in ('east','west')
    if motif in ('shroud','upper_panel','strap') and side and min(w,h)>10:
        dr.line([(3,3),(w-4,3)],fill=tuple(np.minimum(base+21,255).astype(int))+(255,),width=1)
        dr.line([(3,h-4),(w-4,h-4)],fill=tuple((base*.72).astype(int))+(255,),width=1)
    if motif=='shroud' and side:
        # Two shallow recessed vents match the source diffuse and supplied photo.
        # Rasterized in world Y/Z, separately authored for each face orientation.
        a=np.array(tile); Y=world[:,:,1]; Z=world[:,:,2]
        for center in (-3.01,-1.55):
            rr=np.sqrt(np.maximum(abs(Z-center)-.27,0)**2+(Y-11.83)**2)
            rim=rr<.115; hole=rr<.078
            a[rim,:3]=[64,85,121]; a[hole,:3]=[24,28,29]
            edge=rim&~hole&(Y>11.83); a[edge,:3]=[142,167,213]
        tile=Image.fromarray(a); dr=ImageDraw.Draw(tile)
    if motif in ('wood','wood_upper'):
        a=np.array(tile);Y=world[:,:,1];Z=world[:,:,2]
        # Subtle dark grip surface, not brown wood grain; checkering stays UV.
        grain=1+.018*np.sin(Y*48)*np.sin(Z*48)
        a[:,:,:3]=np.clip(np.array(PALETTE['wood'])*grain[:,:,None],0,255)
        if side and motif=='wood':
            # Shallow dark diamond checkering follows the grip material, not cubes.
            region=(Y>7.38)&(Y<9.38)&(Z>7.5)&(Z<9.0)
            lines=(np.mod(Y*1.15+Z,.22)<.021)|(np.mod(Y*1.15-Z,.22)<.021)
            a[region&lines,:3]=[24,28,35]
        if side and motif=='wood_upper':
            r=np.hypot(Y-11.18,Z-6.96)
            a[(r<.13)&(r>.095),:3]=[147,139,111]
            a[r<.092,:3]=[54,53,47]
            a[(r<.08)&(abs(Z-6.96)<.014),:3]=[155,150,130]
        tile=Image.fromarray(a); dr=ImageDraw.Draw(tile)
    if motif=='cylinder':
        # Broad continuous painted flutes on the shell, recessed by shading in UV;
        # the cylinder/chamber cross section itself is fully three dimensional.
        a=np.array(tile); p=world-np.array(CYLINDER_CENTER)
        theta=np.arctan2(p[:,:,1],p[:,:,0]); Z=world[:,:,2]
        band=(Z>2.43)&(Z<3.43)&(np.cos(6*theta)>.72)
        inner=(Z>2.49)&(Z<3.37)&(np.cos(6*theta)>.83)
        a[band,:3]=[65,88,131];a[inner,:3]=[81,111,164]
        seam=(abs(Z-2.39)<.018)|(abs(Z-5.14)<.018)
        a[seam,:3]=[66,88,128]
        tile=Image.fromarray(a);dr=ImageDraw.Draw(tile)
    if motif=='chamber':
        a=np.array(tile)
        if face in ('north','south'):
            a[:,:,:3]=[122,121,103]; a[0,:,:3]=[173,162,120]
        else:
            a[:,:,:3]=np.array([67,69,66])*(.93+.07*np.sin(v*math.pi))[:,:,None]
            a[(world[:,:,2]<2.44)|(world[:,:,2]>5.11),:3]=[100,103,97]
        tile=Image.fromarray(a);dr=ImageDraw.Draw(tile)
    if motif in ('frame','breech') and side and min(w,h)>14:
        dr.line([(2,h-3),(w-3,h-3)],fill='#262b2c')
    if motif=='knob' and face in ('north','south','up'):
        for x in range(3,w-2,5):dr.line([(x,2),(x,h-3)],fill='#272c2e')
    if motif in ('screw','lug_end') and side and min(w,h)>8:
        r=min(w,h)*.24; x=w/2; y=h/2
        dr.ellipse((x-r,y-r,x+r,y+r),fill='#343a3b',outline='#74766c')
        dr.line([(x-r*.55,y),(x+r*.55,y)],fill='#23282a')
    if motif=='rubber':
        for y in range(3,h-2,5):dr.line([(2,y),(w-3,y)],fill='#1b1e1f')
    return tile


def compile_models(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0)); requests=[]
    for part,specs in d['parts'].items():
        for spec in specs:
            spec['geometry']['faces']={}
            for face in FACES:
                p=face_points(spec['geometry'],face)
                density=25 if spec['motif'] in ('shroud','wood','wood_upper','cylinder') else 18
                w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density))
                h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
                requests.append((h,w,spec['geometry']['name'],face,spec))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]))
    x=y=2; row=0; ledger=[]
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE: x=2; y+=row+4; row=0
        if y+h+2>EDGE: raise ValueError(f'Atlas overflow: {name} {face} {y+h}')
        tile=make_tile(spec,face,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(tile),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        spec['geometry']['faces'][face]=dict(uv=[v*16/EDGE for v in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h],texels=w*h))
        x+=w+4;row=max(row,h)
    d['atlas']=dict(size=EDGE,gutter=2,face_islands=len(ledger),used_texels=sum(v['texels'] for v in ledger),islands=ledger)
    models={part:dict(credit='W127 Duke Mk.44 authored solid revolver / face UV',
        textures={'0':'destiny:item/weapon/w123/duke_mk_44','particle':'destiny:item/weapon/w123/duke_mk_44'},
        elements=[copy.deepcopy(s['geometry']) for s in specs]) for part,specs in d['parts'].items()}
    full=copy.deepcopy(models['body']);full['elements']+=copy.deepcopy(models['cylinder']['elements'])
    full['display']=json.loads((ROOT/BASE).read_bytes())['display'];models['full']=full
    assert len(full['elements'])<=1000
    return atlas,models


def inspection(d,atlas,models):
    elements=[]; groups=[]
    for part in ('body','cylinder'):
        children=[]
        for e in models[part]['elements']:
            b=copy.deepcopy(e);r=b.pop('rotation')
            b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values(): f['texture']=0; f['uv']=[q*EDGE/16 for q in f['uv']]
            elements.append(b);children.append(b['uuid'])
        groups.append(dict(name=part,uuid=uid('group:'+part),origin=PIVOT if part=='cylinder' else [8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},
        name='Duke Mk.44 W127 solid revolver',resolution={'width':EDGE,'height':EDGE},elements=elements,outliner=groups,
        textures=[dict(name=ID+'.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        display=models['full']['display'],destiny_w123={'stage':'W127','anchor':[8,8,8],
            'cylinderPivot':PIVOT,'rotationOrder':'RzRyRx','nativeAccepted':False})


def raw_triangles(meshes):
    triangles=[]
    for mesh in meshes:
        index=int(mesh['name'][5:9]);role='steel'
        if index in (0,1,8,10,12): role='yellow'
        if index==2: role='graphite'
        if index in (3,4,6,7,9,11): role='graphite'
        if index==5: role='wood'
        tex=np.array([[PALETTE[role]+[255]]],dtype=np.uint8)
        for t in mesh['vertices'][mesh['faces']]:
            n=np.cross(t[1]-t[0],t[2]-t[0]);n/=max(np.linalg.norm(n),1e-20)
            triangles.append((t,np.zeros((3,2)),tex,n))
    return triangles


def comparison(d,meshes,atlas,models):
    helper=renderer();w,h=900,390
    sheet=Image.new('RGB',(w*2,2320),'#151d26');dr=ImageDraw.Draw(sheet)
    dr.text((20,12),'DUKE MK.44 | W127 AUTHORED SOLID REVOLVER | OFFLINE ONLY',fill='#f1e8cd',font_size=26)
    ref=Image.open(PHOTO).convert('RGB').crop((1000,230,1760,750));ref.thumbnail((620,310));sheet.paste(ref,(18,53))
    count=len(models['full']['elements'])
    lines=[f'{count} solids = {len(models["body"]["elements"])} body + {len(models["cylinder"]["elements"])} cylinder',
        '6 drilled chambers / deep muzzle / open guard and underlug',
        'Blue lacquer / dark grip from supplied W31 light.gg reference',
        '1024 authored opaque face atlas; no alpha body skins',
        'Exact canonical display + W64 [8,10.2,5.17] cylinder pivot',
        'RAW FBX below is reference recolored, not original paint rendering']
    for i,line in enumerate(lines):dr.text((680,65+39*i),line,fill='#dce3e7',font_size=19)
    dr.text((20,344),'UNCHANGED RAW FBX / 7,960 triangles / reference recolor',fill='#e2e8ed',font_size=20)
    dr.text((w+20,344),f'NEW / {count} solid cuboids / independent face UV',fill='#e2e8ed',font_size=20)
    arrays=[raw_triangles(meshes),helper['model_triangles']({'full':models['full']},atlas,{})]
    points=np.concatenate([m['vertices'] for m in meshes])
    views=[('SIDE',[-1,0,0]),('FRONT THREE-QUARTER',[-1,.42,-.75]),
           ('REAR THREE-QUARTER',[1,.42,.65]),('FRONT / BORE AXIS',[.14,.04,-1])]
    for row,(label,cam) in enumerate(views):
        cam=np.array(cam,float);cam/=np.linalg.norm(cam);right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right)
        proj=np.c_[points@right,points@up];lo,hi=proj.min(0),proj.max(0)
        extent=((lo+hi)/2,min((w-70)/(hi[0]-lo[0]),(h-60)/(hi[1]-lo[1])))
        for col,tris in enumerate(arrays):
            im,_=helper['render'](tris,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,380+row*h))
            dr.text((col*w+16,386+row*h),label,fill='#dce6ee',font_size=17)
    # Detached inspection uses exactly the same unrecentered cylinder vertices.
    # It is a local geometry inspection, not a fake screenshot of a reload frame.
    cylinder=helper['model_triangles']({'cylinder':models['cylinder']},atlas,{})
    pts=np.concatenate([t[0] for t in cylinder])
    for col,cam in enumerate(([.05,.04,1],[-.52,.28,-1])):
        cam=np.array(cam,float);cam/=np.linalg.norm(cam);right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right)
        proj=np.c_[pts@right,pts@up];lo,hi=proj.min(0),proj.max(0)
        extent=((lo+hi)/2,min((w-120)/(hi[0]-lo[0]),300/(hi[1]-lo[1])))
        im,_=helper['render'](cylinder,cam,extent,(w,350));sheet.paste(im,(col*w,1940))
        dr.text((col*w+16,1946),'DETACHED CYLINDER / '+('REAR SIX CHAMBERS' if col==0 else 'FRONT OBLIQUE / BORE DEPTH'),fill='#e2e8ed',font_size=18)
    dr.text((20,2296),'Matched orthographic comparison + detached detail. Native pack/held/ADS/reload/performance pending master.',fill='#b7c9d5',font_size=17)
    return png(sheet)


def review_text(d,counts):
    return f'''# Duke Mk.44 W127 implemented art

{counts['full']} actual emitted solid cuboids = {counts['body']} fixed body +
{counts['cylinder']} moving cylinder/yoke. Full is exactly body+cylinder, alternative
representations counted once. All {counts['full']*6} faces have independent opaque
UV islands. Zero alpha side plates, triangle adapters, arbitrary meshes or source
component extrusion. Atlas: 1024 RGBA, {d['atlas']['face_islands']} face islands,
{d['atlas']['used_texels']} face texels, 2px dilation.

The tall stepped shroud is made from broad solid volumes with a raked nose and
continuous top strap. Muzzle, front housing aperture, underbarrel lug, trigger
guard, rear notch and hammer loop have real air/depth. The grip curves through
three solid grip masses and a separate dark backstrap/heel. Metal panel seams,
two shallow barrel vents, grip grain/checkering, fasteners and cylinder flutes
belong to UV. Fine original bevels are simplified.

The twelve exterior cylinder staves surround six full-length octagonal chamber
tubes, six solid inter-chamber webs and a spindle. Both end faces show six actual
empty drilled bores; no painted black chamber dots or alpha cap. Outer facets
carry the blue lacquer; inside bores are dark steel. Two reauthored W64 yoke
links remain in the moving group with the original lower pivot attachment and
Z frame. The vertical link's top is shortened from Y=12.25 to 11.72; the arm is
lowered from Y=12.05..12.45 to 11.50..11.80 to meet the new shell below the bottom
chamber. This shape adjustment keeps all six bores open without changing pivot.

Coordinate mapping is [8-source.Y*s, 8+source.Z*s, 8-source.X*s], s =
{d['source']['scale']}. Length/muzzle -Z, thickness X, up Y. Original [8,8,8]
anchor, held frame and canonical display are preserved; parts have no display.
Cylinder is not recentered. The W64 swing pivot remains [8,10.2,5.17]. No reload
timings, wrappers, animation graphs or shared manifests are edited.

Historical reconciliation: canonical 232; W64 211 body + 21 original cylinder +
2 added yoke = 234. This is an existing reload feature delta. New canonical full
deliberately includes the new yoke and equals its own body+cylinder, so the shared
migration has one coherent assembly. It does not pretend 232 equals 234.

Source evidence actually inspected: supplied /tmp/destiny-weapons-w31/references/
duke_mk_44.jpg (blue exterior/black grip variant), extracted neutral barrel/cylinder
diffuse sheets, original 7,960-triangle FBX in the W30 coordinate mapping.

Paint evidence correction: `art/weapons/w31/palette-overrides.json` explicitly
sets Duke barrel/cylinder dye to linear [0.12,0.22,0.65,1] for blue lacquer and
[0.012,0.015,0.022,1] for dark steel. `art/weapons/w31/references.json` identifies
the blue/black screenshot for item 2112909414 (SHA-256
6b0aafe4f3abda9cacc7eee0a0f8106218813c0a427ab02b6fae3f8c1c572067).
The existing W30 Duke atlas was also viewed and is visibly blue/dark. The master
rejected the initial unsupported yellow/wood alternate and repainted the actual
final atlas blue/dark to match this evidence. Legacy material keys in the
source generator remain for stable geometry/UV identifiers, not as color claims.
Neutral raw diffuse cannot establish finished RGB; reverse-side markings and
dynamic PBR are not recovered. No invented lettering was added.

comparison.png shows the original photo, unchanged reference-recolored raw FBX
beside new face-textured solids in side, front/rear oblique and bore-axis views,
plus detached cylinder end/oblique details. inspection.bbmodel embeds the atlas,
body/cylinder groups and original group pivot. The renderer is a CPU rasterizer;
these images are not native gameplay screenshots and do not certify performance.

Master native follow-up: migrate the three model references; pack/parser check;
representative first/third person, ADS and twohand; swing-out W64 reload and return
to full; 10-20 simultaneous display observation. No GUI, client, Blender process,
Gradle or native inputs were used by this worker.
'''


def generate(include_review=True):
    meshes,metadata=source_meshes();d=make_design(meshes,metadata);atlas,models=compile_models(d)
    counts={p:len(models[p]['elements']) for p in ('body','cylinder','full')}
    points=np.concatenate([renderer()['vertices'](e) for e in models['full']['elements']])
    outputs={ART+'design.json':encode(d),TEXTURE:png(atlas),
        MODEL+'.json':encode(models['full']),MODEL+'_body.json':encode(models['body']),MODEL+'_cylinder.json':encode(models['cylinder']),
        ART+'inspection.bbmodel':encode(inspection(d,atlas,models)),ART+'review.md':review_text(d,counts).encode()}
    if include_review: outputs[ART+'comparison.png']=comparison(d,meshes,atlas,models)
    manifest=dict(stage='W127',revision=d['revision'],id=ID,family='hand_cannon',counts=counts,
        native_elements=counts['full'],max_assembled_elements=1000,opaque_cuboids=counts['full'],
        alpha_contour_elements=0,triangle_adapter_elements=0,emitted_faces=6*counts['full'],
        source_triangles=7960,canonical_reload_delta=d['canonical_reload_delta'],full_is_body_plus_cylinder=True,
        canonical_display_exact=True,part_display_absent=True,anchor=[8,8,8],scale=metadata['scale'],cylinder_pivot=PIVOT,
        cylinder_center=CYLINDER_CENTER,rotation_order='RzRyRx',semantic_groups=d['groups'],
        texture_size=[EDGE,EDGE],atlas_face_islands=d['atlas']['face_islands'],atlas_face_texels=d['atlas']['used_texels'],
        actual_bounds=[points.min(0).round(6).tolist(),points.max(0).round(6).tolist()],
        generator_sha256=sha((ROOT/GENERATOR).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(v) for p,v in sorted(outputs.items())},
        validation={'targeted_python':TEST,'native_parser':'pending master','gameplay':'pending master','performance':'not measured; offline only'},
        native_accepted=False,limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args()
    outputs=generate();batch=json.loads((ROOT/'docs/qa/2026-10-26/w127/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w127-duke_mk_44'))
    assert len(owned)==12 and set(outputs)<=owned
    for path,data in outputs.items():
        target=ROOT/path
        if args.verify: assert target.is_file() and target.read_bytes()==data,'Generated drift: '+path
        else: target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} artifacts; {m["counts"]}; {m["emitted_faces"]} faces; offline only')


if __name__=='__main__': main()
