#!/usr/bin/env python3
"""W134 Bygones: full-only semantic solids and authored face UV, offline CPU QA.
Run with bundled numpy/Pillow Python -B. No DCC, game or shared writes.
"""
import argparse
import base64
from collections import Counter
import copy
import json
import math
from pathlib import Path
import runpy
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ART = 'art/weapons/w123/bygones/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + 'models/weapon/pulse_rifle/bygones.json'
MODEL = ASSET + 'models/weapon_surface_w123/bygones.json'
TEXTURE = ASSET + 'textures/item/weapon/w123/bygones.png'
REPORT = 'docs/qa/2026-10-26/w134/bygones-worker.md'
SOURCE = 'art/blockbench/weapons/w30/bygones.bbmodel'
HELPER = 'scripts/generate_surface_w123_beloved.py'
REFS = 'art/weapons/w31/references.json'
TEST = 'scripts/qa/test_surface_w123_bygones.py'
RAW = Path('/tmp/destiny-weapons-w30/raw/bygones/extracted/Bygones')
PHOTO = Path('/tmp/destiny-weapons-w31/references/bygones.jpg')
EDGE = 1024
H = runpy.run_path(str(ROOT / HELPER))
FACES, NORMALS = H['FACES'], H['NORMALS']
sha, encode, png = H['sha'], H['encode'], H['png']
PALETTE = dict(frame=[46,74,70], steel=[76,104,99], edge=[105,133,124],
               dark=[29,43,41], recess=[16,25,24], rubber=[24,31,29],
               walnut=[101,61,39], forewood=[87,50,31], gripwood=[83,48,31])
OWNED = {'scripts/generate_surface_w123_bygones.py', TEST, REPORT, TEXTURE, MODEL,
         *(ART + n for n in ('design.json','manifest.json','review.md','inspection.bbmodel','comparison.png'))}


def native_element(e):
    e = copy.deepcopy(e)
    if 'rotation' in e:
        r = e['rotation']; e['rotation'] = dict(origin=r['origin'], **{r['axis']: r['angle']})
    return e


def vertices(e):
    return H['vertices'](native_element(e))


def model_triangles(model, atlas):
    m = copy.deepcopy(model); m['elements'] = [native_element(e) for e in m['elements']]
    return H['model_triangles']({'full': m}, atlas)


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'destiny:w134:bygones:' + name))


def source_meshes():
    """FBX geometry is read-only evidence, never the new construction unit.

    W30 loaded .blend. This FBX independently matches all six retained names,
    19,052 triangles and bounds within 2e-6 native units (float export drift).
    Its basis is X,Z,Y, unlike Beloved's basis. Never execute source shaders.
    """
    meta = json.loads((ROOT / SOURCE).read_bytes())['destiny_w30']
    assert sha((RAW/'Bygones.fbx').read_bytes()) == meta['source_files']['Bygones/Bygones.fbx']
    assert sha((RAW/'Bygones.blend').read_bytes()) == meta['source_files']['Bygones/Bygones.blend']
    roots = H['parse_fbx'](RAW/'Bygones.fbx')
    objects = next(n[2] for n in roots if n[0] == 'Objects')
    links = [n[1][1:] for root in roots if root[0] == 'Connections' for n in root[2] if n[1][0] == 'OO']
    models = {n[1][0]: n for n in objects if n[0] == 'Model'}
    materials = {n[1][0]: n[1][1].split('\x00')[0] for n in objects if n[0] == 'Material'}
    meshes = []
    for node in objects:
        if node[0] != 'Geometry': continue
        mid = next(p for c,p in links if c == node[1][0]); model = models[mid]
        name = model[1][1].split('\x00')[0]
        if name not in meta['source_objects']: continue
        props = {p[1][0]:p[1][4:] for c in model[2] if c[0] == 'Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'], [-90,0,0], atol=2e-5)
        assert np.allclose(props['Lcl Scaling'], [100,100,100], atol=2e-5)
        cs = {c[0]:c for c in node[2]}
        raw = np.array(cs['Vertices'][1][0]).reshape(-1,3)
        v = raw[:,[0,2,1]] * meta['scale'] + meta['anchor']
        ix = np.array(cs['PolygonVertexIndex'][1][0])
        assert np.all((ix < 0).reshape(-1,3) == [False,False,True])
        ix = np.where(ix < 0, -ix-1, ix).reshape(-1,3)
        layer = next(c for c in node[2] if c[0] == 'LayerElementUV' and c[1][0] == 0)
        vals = {c[0]:c[1][0] for c in layer[2]}
        assert vals['MappingInformationType'] == 'ByPolygonVertex'
        assert vals['ReferenceInformationType'] == 'IndexToDirect'
        uv = np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])].reshape(-1,3,2)
        uv[:,:,1] = 1 - uv[:,:,1]
        material = next(materials[c] for c,p in links if p == mid and c in materials)
        meshes.append(dict(name=name,vertices=v,faces=ix,uv=uv,material=material))
    pts = np.concatenate([m['vertices'] for m in meshes])
    assert sorted(m['name'] for m in meshes) == sorted(meta['source_objects'])
    assert sum(len(m['faces']) for m in meshes) == meta['source_triangles']
    assert np.allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=2e-6,rtol=0)
    return meshes, meta


def make_design(meta, meshes):
    parts = []
    def box(name, lo, hi, mat, group, motif='plain', turn=None):
        e = dict(name=name, **{'from':lo,'to':hi})
        if turn:
            e['rotation'] = dict(origin=[round((a+b)/2,7) for a,b in zip(lo,hi)],axis=turn[0],angle=turn[1])
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def c(name, pos, size, mat, group, motif='plain', turn=None):
        box(name,[round(a-b/2,7) for a,b in zip(pos,size)],
            [round(a+b/2,7) for a,b in zip(pos,size)],mat,group,motif,turn)
    def beam(name, a, b, width, depth, mat, group, motif='plain'):
        dy=b[1]-a[1]; dz=b[2]-a[2]; angle=-math.degrees(math.atan2(dy,dz))
        if angle > 90: angle -= 180
        if angle < -90: angle += 180
        c(name,[(p+q)/2 for p,q in zip(a,b)], [width,depth,math.hypot(dy,dz)],mat,group,motif,('x',angle))
    def tube(name, x, y, z0, z1, radius, thick, mat, group, motif='rim'):
        for i in range(8):
            a=i*45; q=math.radians(a); rr=radius-thick/2
            size=[2*radius*math.tan(math.pi/8)+.006,thick,z1-z0]; turn=None
            if a%90 == 0:
                if a%180: size=[size[1],size[0],size[2]]
            else: turn=('z',45 if i%4 == 1 else -45)
            c(f'{name}_{i}',[x-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],size,mat,group,motif,turn)

    # Exact source/native longitudinal endpoints; the bore is never an alpha spot.
    muzzle_z = meta['model_bounds'][0][2]; butt_z = meta['model_bounds'][1][2]
    source_points=np.concatenate([m['vertices'] for m in meshes])
    terminal=source_points[np.isclose(source_points[:,2],source_points[:,2].min(),atol=1e-7,rtol=0)]
    mx,my=((terminal.min(0)+terminal.max(0))/2)[:2].tolist()
    tube('muzzle',mx,my,muzzle_z,-7.30,.435,.135,'steel','muzzle','ported')
    tube('barrel',mx,my,-7.32,-5.16,.325,.14,'frame','barrel','barrel')
    tube('barrel_collar',mx,my,-6.02,-5.62,.39,.13,'steel','barrel')
    c('bore_deep_back',[mx,my,-5.12],[.40,.40,.09],'recess','barrel')
    # Lower wooden handguard is a filled mass with long continuous grain islands.
    box('forewood_core',[7.40,9.43,-4.93],[8.60,10.64,1.00],'forewood','forearm','wood')
    for side in (-1,1):
        c(f'forewood_lower_bevel_{side}',[8+side*.49,9.49,-1.96],[.28,.28,5.88],
          'forewood','forearm','wood',('z',45*side))
        c(f'forewood_top_round_{side}',[8+side*.52,10.58,-1.96],[.25,.25,5.91],
          'walnut','forearm','wood',('z',45*side))
    c('forewood_rear_shoulder',[8,9.71,.79],[1.12,.49,.76],'forewood','forearm','wood',('x',-12))
    box('nose_clamp',[7.31,9.97,-5.35],[8.69,10.97,-4.99],'frame','nose','clamp')
    c('nose_clamp_lug',[8,9.93,-5.18],[.68,.20,.54],'dark','nose')
    # Front sight is a genuinely open low hood, not an alpha ring.
    box('front_sight_foot',[7.63,11.46,-5.85],[8.37,11.64,-5.22],'frame','sight')
    for side in (-1,1):
        c(f'front_sight_wing_{side}',[8+side*.29,11.79,-5.51],[.12,.31,.40],'steel','sight')
    c('front_sight_bridge',[8,11.97,-5.51],[.65,.12,.40],'frame','sight')
    # Six real side vents. Substantial cross posts, upper/lower beams and an
    # inset bore replace a mesh/voxel transplant. Small port edge rounding is UV.
    box('vent_lower_spine',[7.43,10.68,-4.91],[8.57,10.99,4.08],'frame','vent','lower')
    box('vent_upper_spine',[7.43,11.56,-4.91],[8.57,11.82,4.08],'frame','vent','upper')
    box('vent_front_block',[7.43,10.97,-4.91],[8.57,11.57,-2.72],'frame','vent','front_panel')
    box('vent_rear_block',[7.43,10.97,3.18],[8.57,11.57,4.08],'frame','vent','rear_panel')
    for i,z in enumerate(np.linspace(-2.62,3.08,7)):
        c(f'vent_crosspost_{i}',[8,11.28,float(z)],[1.14,.61,.48],'frame','vent','vent_edge')
    for i,zc in enumerate(np.linspace(-2.145,2.605,6)):
        for top in (-1,1):
            for end in (-1,1):
                c(f'vent_corner_{i}_{top}_{end}',[8,11.275+top*.285,float(zc)+end*.235],
                  [1.14,.17,.17],'frame','vent','vent_edge',('x',45))
    c('vent_inset_barrel',[8,11.16,.23],[.36,.33,5.75],'dark','vent','barrel')
    # Thick roof shoulders and discrete bridges leave three longitudinal slots.
    for side in (-1,1):
        c(f'roof_rail_{side}',[8+side*.42,11.87,-.415],[.30,.24,8.99],'steel','roof','upper')
    for i,z in enumerate([-4.76,-2.34,.08,2.50,3.93]):
        c(f'roof_bridge_{i}',[8,11.86,z],[.76,.23,.31],'frame','roof')
    # Broad rear receiver and lower junction: six opaque authored faces each.
    box('receiver_main',[7.36,10.28,4.08],[8.64,11.78,8.14],'frame','receiver','receiver')
    box('receiver_crown',[7.49,11.78,4.12],[8.51,11.94,7.96],'steel','receiver','upper')
    box('receiver_keel',[7.43,9.99,4.20],[8.57,10.32,7.96],'frame','receiver','lower')
    c('lower_front_ramp',[8,9.89,3.60],[1.14,.63,1.29],'frame','receiver','panel',('x',-29))
    c('receiver_wrist',[8,10.18,7.88],[1.12,.87,1.16],'frame','receiver','panel',('x',19))
    # Filled front action reduces the source trigger aperture to its proper rear half.
    box('lower_action_cheek',[7.40,9.13,3.95],[8.60,10.33,5.78],'frame','receiver','panel')
    c('lower_action_chamfer',[8,9.22,4.48],[1.13,.34,1.15],'frame','receiver','lower',('x',-26))
    # Actual trigger aperture, shaped in a few thick facets with a separate trigger.
    beam('guard_front',[8,10.31,3.91],[8,9.29,3.42],.71,.24,'frame','guard','rim')
    beam('guard_front_curve',[8,9.29,3.42],[8,8.76,3.94],.71,.25,'frame','guard','rim')
    beam('guard_floor',[8,8.76,3.94],[8,8.68,5.65],.71,.28,'frame','guard','rim')
    beam('guard_rear_curve',[8,8.68,5.65],[8,8.92,6.59],.71,.27,'frame','guard','rim')
    beam('guard_rear',[8,8.92,6.59],[8,10.17,7.01],.71,.27,'frame','guard','rim')
    beam('trigger_stem',[8,10.13,6.60],[8,9.55,6.40],.18,.15,'steel','trigger')
    beam('trigger_hook',[8,9.55,6.40],[8,9.34,6.08],.18,.15,'steel','trigger')
    # Grip at the original hand frame; source origin/anchor is not re-centered.
    c('walnut_grip',[8,8.61,8.43],[1.06,3.98,1.28],'gripwood','grip','wood',('x',-25))
    c('grip_backstrap',[8,8.69,9.05],[.96,3.71,.18],'dark','grip','strap',('x',-25))
    heel_halfheight=.13*math.cos(math.radians(25))+.685*math.sin(math.radians(25))
    c('grip_heel',[8,meta['model_bounds'][0][1]+heel_halfheight,9.29],[1.09,.26,1.37],
      'gripwood','grip','wood',('x',-25))
    # Filled walnut comb and a broad rotated toe preserve the characteristic
    # stock cutaway above the rear magazine and behind the slanted grip.
    box('stock_comb',[7.43,10.27,8.12],[8.57,11.88,16.06],'walnut','stock','wood')
    box('stock_belly_join',[7.45,9.94,10.67],[8.55,10.64,15.55],'walnut','stock','wood')
    c('stock_toe',[8,9.72,13.27],[1.12,1.90,3.20],'walnut','stock','wood',('x',29))
    for side in (-1,1):
        c(f'stock_upper_round_{side}',[8+side*.44,11.83,12.08],[.32,.32,7.96],
          'walnut','stock','wood',('z',45*side))
    box('buttpad',[7.39,8.49,16.06],[8.61,11.91,butt_z],'rubber','stock','butt')
    for side in (-1,1):
        c(f'stock_pivot_{side}',[8+side*.65,11.30,8.13],[.23,.59,.59],
          'steel','controls','pivot',('x',45))
    c('charging_latch',[8.77,10.46,7.36],[.36,.30,.75],'dark','controls','latch',('y',-12))
    # Rear box magazine remains in the full-only generic reload assembly.
    c('magazine',[8,7.90,12.20],[1.04,2.50,2.45],'frame','magazine','magazine',('x',11))
    for side in (-1,1):
        c(f'magazine_shoulder_{side}',[8+side*.46,7.90,12.20],[.22,2.44,.22],
          'steel','magazine','magazine',('x',11))
    c('magazine_front_spine',[8,7.91,10.98],[1.00,2.46,.18],'dark','magazine','strap',('x',11))
    c('magazine_floorplate',[8,6.75,11.98],[1.17,.25,2.55],'steel','magazine','base',('x',11))
    # Compact octagonal optic with a true open optical channel, not alpha glass.
    # The back lens/refraction of the source shader is intentionally not claimed.
    box('optic_base',[7.40,11.95,4.95],[8.60,12.16,7.39],'frame','optic','mount')
    box('optic_riser',[7.72,12.13,5.60],[8.28,12.39,6.64],'dark','optic','mount')
    tube('optic_tube',8,12.80,5.18,6.77,.597941143263306,.14,'frame','optic','optic')
    c('optic_side_dial',[8.69,12.80,6.34],[.25,.49,.49],'steel','optic','dial',('x',45))
    c('optic_top_band',[8,13.34,6.38],[.43,.09,.59],'dark','optic','strap')
    # Visible sling eyes are genuine three-sided loops below solid attachments.
    for tag,y,z in [('front',9.32,-3.76),('rear',10.12,15.02)]:
        c(tag+'_sling_floor',[8,y-.30,z],[.60,.11,.18],'dark','sling')
        for side in (-1,1):
            c(f'{tag}_sling_wing_{side}',[8+side*.25,y-.15,z],[.10,.30,.18],'dark','sling')

    ref = next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']=='bygones')
    assert sha(PHOTO.read_bytes()) == ref['sha256']
    inputs = [BASE,SOURCE,REFS,HELPER,ASSET+'textures/item/weapon/w30/bygones.png']
    raw_inputs = [PHOTO,RAW/'Bygones.fbx',RAW/'Bygones.blend',RAW/'BFrame_Diffuse.png',RAW/'BSight_Diffuse.png',RAW/'Decals.png']
    return dict(id='bygones',revision='W134',family='pulse_rifle',source=meta,parts=parts,palette=PALETTE,
        method='Hand-authored filled cuboids and functional hollow frames; no source island/voxel/data transfer',
        reference=ref,default_photo_sha256=sha(PHOTO.read_bytes()),
        frame=dict(mapping='[8+raw.X*s,8+raw.Z*s,8+raw.Y*s]',anchor=meta['anchor'],scale=meta['scale'],
                   muzzle_axis='-Z',muzzle_tip_z=muzzle_z,muzzle_bore_center=[mx,my],muzzle_center_provenance='FBX terminal ring extrema midpoint in retained W30 frame',butt_tip_z=butt_z,
                   display_policy='canonical exact',hand_origin=[8,8,8],full_only=True),
        source_matching=dict(retained_objects_exact=True,triangles=19052,fbx_bounds_tolerance=2e-6,
            note='W30 .blend metadata and original FBX hashes match; FBX float export drifts up to 1.6e-6 native units. Reticle object remains excluded.'),
        holes=[dict(name='muzzle bore',point=[mx,my,-7.9],ray_axis='z',range=[muzzle_z,-5.2]),
               dict(name='trigger aperture',point=[8,9.50,5.98],ray_axis='x',range=[6.8,9.2]),
               dict(name='optic optical channel',point=[8,12.80,6],ray_axis='z',range=[5.18,6.77]),
               dict(name='stock cutaway',point=[8,8.95,10.42],ray_axis='x',range=[6.8,9.2]),
               dict(name='front sight hood',point=[8,11.79,-5.5],ray_axis='z',range=[-5.72,-5.3]),
               dict(name='side vent',point=[8,11.42,-2.14],ray_axis='x',range=[6.8,9.2])],
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['Offline CPU art views are not native/game acceptance.',
            'Default photo paint is authored walnut/green reinterpretation, not recovered original shader/PBR.',
            'Six vents are faceted octagons; tiny muzzle ports and screws are opaque recess UV.',
            'Optic has a true open channel; optical glass, source reticle and refraction are not reproduced.',
            'Full-only candidate; held/ADS/generic reload/20-display checks pending master.'])


def world_points(e,face,w,h):
    p=vertices(e)[list(FACES[face])]
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q=((1-u)*(1-v))[:,:,None]*p[0]+(u*(1-v))[:,:,None]*p[1]+(u*v)[:,:,None]*p[2]+((1-u)*v)[:,:,None]*p[3]
    return u,v,q


class Paint:
    def __init__(self):
        raw=Image.open(RAW/'BFrame_Diffuse.png').convert('RGB')
        # Only selected grayscale wood relief is reused, not original UV shells.
        self.wood=np.asarray(raw.crop((1350,430,1920,650)).filter(ImageFilter.MedianFilter(3))).mean(2)/255
        self.forewood=np.asarray(raw.crop((250,1380,860,1510)).filter(ImageFilter.MedianFilter(3))).mean(2)/255

    def tile(self,spec,face,w,h):
        e=spec['geometry']; role=spec['material']; motif=spec['motif']; u,v,q=world_points(e,face,w,h)
        rgb=np.broadcast_to(np.array(PALETTE[role],float),(h,w,3)).copy()
        rgb*=(.97+.055*np.exp(-((v-.28)/.38)**2))[:,:,None]
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        if motif!='vent_edge':
            rgb[edge<.65]*=.81;rgb[(edge>=.65)&(edge<1.30)]*=1.10
        side=face in ('east','west')
        if motif=='wood':
            group=spec['group']; tex=self.forewood if group=='forearm' else self.wood
            if group=='forearm': a=(q[:,:,2]+5)/6.1; b=(10.8-q[:,:,1])/1.5
            elif group=='grip': a=(q[:,:,1]-6.3)/4.6; b=(q[:,:,2]-7)/3
            else: a=(q[:,:,2]-8)/8.3; b=(11.95-q[:,:,1])/4.0
            a=np.clip(a,0,1);b=np.clip(b,0,1)
            detail=tex[np.minimum((b*tex.shape[0]).astype(int),tex.shape[0]-1),np.minimum((a*tex.shape[1]).astype(int),tex.shape[1]-1)]
            detail=np.clip(1+(detail-tex.mean())*2.2,.76,1.24)
            rgb*=detail[:,:,None]
            # Long varnish sheen is restrained, independent of runtime light.
            rgb+=(3*np.exp(-((b-.18)/.16)**2))[:,:,None]*[1.0,.75,.47]
            if group=='forearm' and side:
                # Three photo-supported screws, painted continuously over bevels.
                for zc,yc in [(-4.45,9.95),(-1.55,10.03),(.48,10.17)]:
                    rr=np.hypot(q[:,:,2]-zc,q[:,:,1]-yc)
                    rgb[rr<.115]=[23,27,24];rgb[(rr>.083)&(rr<.115)]=[58,62,53]
                    rgb[(rr<.07)&(abs(q[:,:,1]-yc)<.014)]=[11,17,16]
            if group=='grip' and side:
                # The longitudinal inlaid grip slit is shallow opaque artwork.
                slit=(abs(q[:,:,2]-(8.41-(q[:,:,1]-8.7)*.46))<.035)&(q[:,:,1]>7.4)&(q[:,:,1]<9.4)
                rgb[slit]*=.36
        if motif in ('receiver','panel','front_panel','rear_panel') and side:
            rgb[(v>.18)&(v<.21)&(u>.08)&(u<.92)]*=.64
            if motif=='receiver':
                # Continuous action cover, restrained machined seam and two pins.
                panel=(u>.14)&(u<.82)&(v>.38)&(v<.74)
                rgb[panel]*=.88
                rgb[(abs(v-.73)<.018)&(u>.14)&(u<.82)]*=1.35
                for a,b in [(.10,.25),(.88,.76)]:
                    r=np.hypot((u-a)*w,(v-b)*h);r0=min(w,h)*.055
                    rgb[r<r0]=PALETTE['recess'];rgb[(r>r0*.68)&(r<r0)]=PALETTE['steel']
        if motif=='magazine' and side:
            # Wide inset plate and a single long seam, no random industrial clutter.
            panel=(u>.18)&(u<.84)&(v>.10)&(v<.91);rgb[panel]*=.86
            rgb[(abs(u-.19)<.018)&(v>.16)&(v<.84)]*=1.30
            rgb[(v>.87)&(v<.90)&(u>.13)&(u<.87)]*=.54
        if motif=='ported' and side:
            # These small photo ports are relief paint. Only the axial bore is open.
            for zc,yc,r in [(-8.12,11.18,.14),(-7.65,11.07,.055),(-7.65,11.26,.055),(-7.48,11.12,.055)]:
                rr=np.hypot(q[:,:,2]-zc,q[:,:,1]-yc)
                rgb[rr<r]=PALETTE['recess'];rgb[(rr>r*.87)&(rr<r*1.18)]*=1.20
        if motif in ('optic','barrel','upper'):
            if motif=='optic':
                band=(abs(q[:,:,2]-5.38)<.035)|(abs(q[:,:,2]-6.56)<.035)
                rgb[band]*=.51
            else: rgb[(v>.45)&(v<.49)]*=.91
        if motif in ('pivot','dial') and side:
            rr=np.hypot((u-.5)*w,(v-.5)*h)/min(w,h)
            rgb[rr<.23]=PALETTE['dark'];rgb[(rr>.34)&(rr<.40)]*=1.23
            rgb[(rr>.23)&(rr<.27)]*=.50
        if motif=='clamp' and side:
            rr=np.hypot(u-.5,v-.5);rgb[rr<.27]=PALETTE['dark'];rgb[(rr>.27)&(rr<.32)]*=1.4
        if motif in ('butt','strap','latch'):
            ribs=(np.mod(q[:,:,1]*6.5,1)<.20)&(u>.10)&(u<.90)
            rgb[ribs]*=.63
        return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
    paint=Paint(); atlas=Image.new('RGBA',(EDGE,EDGE),(0,0,0,0));requests=[]
    for s in d['parts']:
        for f in FACES:
            p=vertices(s['geometry'])[list(FACES[f])];density=32 if s['motif'] in ('wood','receiver','ported') else 28
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,s['geometry']['name'],f,s))
    requests.sort(key=lambda a:(-a[0],-a[1],a[2],a[3]));x=y=2;row=0;islands=[];uvmap={}
    for h,w,name,f,s in requests:
        if x+w+2>EDGE: x=2;y+=row+4;row=0
        if y+h+2>EDGE: raise ValueError('Atlas overflow: '+name)
        tile=paint.tile(s,f,w,h)
        atlas.paste(Image.fromarray(np.pad(np.asarray(tile),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvmap[(name,f)]=[a*16/EDGE for a in (x,y,x+w,y+h)]
        islands.append(dict(element=name,face=f,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    elements=[]
    for s in d['parts']:
        e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uvmap[(e['name'],f)],texture='#0') for f in FACES};elements.append(e)
    d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(islands),islands=islands,
                    wood_relief_crops=[[1350,430,1920,650],[250,1380,860,1510]],
                    paint_policy='Opaque per-face UV; authored panels and default-photo colors; selected neutral wood relief only')
    return atlas,dict(credit='Bygones W134 / semantic solids and authored default-photo face UV / full only',
        textures={'0':'destiny:item/weapon/w123/bygones','particle':'destiny:item/weapon/w123/bygones'},
        display=copy.deepcopy(json.loads((ROOT/BASE).read_bytes())['display']),elements=elements)


def inspection(d,model,atlas):
    elements=[];groups=[]
    for group in sorted({s['group'] for s in d['parts']}):
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group};children=[]
        for e in model['elements']:
            if e['name'] not in names:continue
            b=copy.deepcopy(e);r=b.pop('rotation',None)
            b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],
                rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
            elements.append(b);children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Bygones W134 / editable offline inspection',
        resolution={'width':EDGE,'height':EDGE},elements=elements,outliner=groups,display=copy.deepcopy(model['display']),
        textures=[dict(name='bygones.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
             source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        destiny_w134=dict(nativeAccepted=False,fullOnly=True,sourceAnchor=d['source']['anchor'],sourceScale=d['source']['scale']))


def source_triangles(meshes):
    texmap={'Frame':'BFrame_Diffuse.png','Sight':'BSight_Diffuse.png','Decals':'Decals.png'}
    textures={m:np.asarray(Image.open(RAW/p).convert('RGBA')) for m,p in texmap.items()};result=[]
    for m in meshes:
        for p,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20)
            result.append((p,uv,textures[m['material']],n))
    return result


def comparison(d,meshes,atlas,model):
    w,h=900,370;sheet=Image.new('RGB',(2700,2070),'#19212a');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4ebed',font_size=size)
    label(20,12,'BYGONES / W134 / FILLED SEMANTIC VOLUMES + AUTHORED FACE UV / OFFLINE CPU ART',29)
    photo=Image.open(PHOTO).convert('RGB').crop((570,230,1880,740));photo.thumbnail((1250,470));sheet.paste(photo,(20,62))
    for i,line in enumerate([f'{len(model["elements"])} opaque cuboids / 0 triangle adapters / full only',
        'Photo default: walnut furniture + deep green metal',
        'True bore / guard / sight / optic channel / stock cutaway',
        'Large side vents and roof channels are actual geometry',
        'Small ports, screws and seams = opaque authored face UV',
        'Original [X,Z,Y] basis, scale and [8,8,8] anchor retained',
        'Original display and gameplay graph retained; native pending']):label(1320,85+i*47,line,23)
    label(20,560,'ACTUAL FBX / 19,052 TRIANGLES / NEUTRAL DIFFUSE',20)
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/bygones.png'))
    label(w+20,560,f'CANONICAL / {len(old["elements"])} CUBOIDS / READ ONLY',20)
    label(2*w+20,560,f'W134 / {len(model["elements"])} AUTHOR-PLACED SOLID CUBOIDS',20)
    ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE / SAME SCALE',[-1,0,0]),('FRONT OBLIQUE / SAME SCALE',[-1,.42,-.63]),('REAR OBLIQUE / SAME SCALE',[1,.32,.62])]):
        ext=H['frame'](points,cam,w,h)
        for col,tris in enumerate(ts):
            im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,600+row*h));label(col*w+15,610+row*h,name,18)
    for i,(group,title,cam) in enumerate([('muzzle','BORE / OPAQUE WALLS',[.25,.2,-1]),
        ('guard','TRIGGER BOW / REAL SPACE',[-1,.3,-.3]),('optic','OPTIC / OPEN CHANNEL',[.18,.10,-1]),
        ('stock','WALNUT / SOLID COMB + TOE',[-1,.35,-.6])]):
        names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        if group=='guard': names|={'lower_action_cheek','lower_action_chamfer','trigger_stem','trigger_hook'}
        es=[e for e in model['elements'] if e['name'] in names]
        pts=np.concatenate([vertices(e) for e in es]);im,_=H['render'](model_triangles(dict(elements=es),atlas),cam,H['frame'](pts,cam,675,255),(675,255))
        sheet.paste(im,(i*675,1740));label(i*675+15,1748,title,18)
    label(20,2025,'Neutral raw diffuse is not default dye. Canonical is the existing W30 cuboid model, not raw FBX. CPU art views are not native Minecraft evidence.',19)
    return png(sheet)


def review_text(d,counts):
    return f"""# Bygones W134 — offline art review

**{len(d['parts'])} opaque authored cuboids**, full-only candidate, zero triangle/contour adapters and zero alpha body cards. Broad filled walnut comb/toe, forearm, grip, receiver and rear magazine define the weapon. A few thick rails/posts provide functional hollow geometry; screws, panel borders, small muzzle ports and grip slits are opaque UV artwork. Six side vents are deliberately faceted octagons rather than exact circular source bores.

The actual default-paint photo was inspected: walnut brown furniture, green-black machined metal, ported short muzzle, raised compact tube optic and rear magazine. Photo SHA-256: `{d['default_photo_sha256']}`; Bungie item {d['reference']['bungie_hash']}, matching `art/weapons/w31/references.json`. The atlas reconstructs this paint; it does not call the largely neutral BFrame diffuse a recovered default shader. Selected grayscale wood-relief rectangles are cleaned/recolored and placed using world-aligned continuous face coordinates. Metal panels, fasteners, collars and shallow grooves are authored. Each of {len(d['parts'])*6} faces has a separate opaque rectangle, with 2-pixel edge-extruded gutters in one 1024 atlas. No source UV-shell or triangle transplant is used for the new model.

Original source: read-only `Bygones/Bygones.fbx` and `.blend` both match the W30 metadata hashes. The inert FBX parser matches all six retained source objects and 19,052 triangles; source bounds match within 0.000002 native units (FBX float export drift). Reticle object Bygones.02.000 remains excluded. The raw comparison renders Frame/Sight/Decals diffuse and original source UV; the decal texture is evidence only. We did not open Blender or execute the supplied shader script. This proves local source matching, not independent Bungie asset authenticity.

Coordinates retain the actual Bygones basis `[raw X, raw Z, raw Y]`, scale {d['source']['scale']}, anchor {d['source']['anchor']}, original hand origin and muzzle -Z. The authored muzzle tip is exactly {d['frame']['muzzle_tip_z']} and butt tip {d['frame']['butt_tip_z']}. Canonical display data is copied exactly. The canonical comparison is the existing 242-cuboid W30 reconstruction and its W30 texture, clearly separate from raw FBX and the W134 candidate. No item registration, ADS, generic reload, combat, audio or timing files are changed. No invented body/magazine split is emitted.

`comparison.png` contains the default photo, side/front/rear CPU views at the same camera and scale per row, and focused muzzle/guard/optic/stock views. `inspection.bbmodel` embeds the final atlas and editable cube groups with matching face UVs. Real openings include the deep muzzle bore, trigger bow, front sight, optic optical channel, side vents and stock cutaway. The optic omits physical glass/refraction/source reticle; the original photo's smooth curves, patina and dynamic metallic reflections are simplified.

Targeted Python QA covers valid schema/budget, frame/display, representative real empty channels and filled depth, opaque UV/gutters, current input/output hashes, editable inspection parity and deterministic regeneration. These checks are intentionally not an all-angle aesthetic gate. Native resource-pack/parser/registration, first/third-person holding, ADS, generic reload and 10–20 simultaneous weapons remain **pending master**. CPU art inspection is not native acceptance or a performance measurement.

Group counts: {json.dumps(counts, sort_keys=True)}.
"""


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta,meshes);atlas,model=compile_model(d)
    counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()));points=np.concatenate([vertices(e) for e in model['elements']])
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),
             ART+'review.md':review_text(d,counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    manifest=dict(id='bygones',revision='W134',family='pulse_rifle',assembled_elements=len(model['elements']),
        opaque_cuboids=len(model['elements']),triangle_adapter_elements=0,contour_elements=0,alpha_body_elements=0,
        max_assembled_elements=1000,groups=counts,emitted_faces=len(model['elements'])*6,full_only=True,
        texture_size=[EDGE,EDGE],face_uv_islands=d['atlas']['face_islands'],atlas_used_height=d['atlas']['used_height'],
        actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],
        default_photo_sha256=d['default_photo_sha256'],source_matching=d['source_matching'],
        canonical_display_exact=True,generic_reload_ADS_combat_audio_timing_unchanged=True,native_accepted=False,
        generator_sha256=sha(Path(__file__).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()),
        input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(data) for p,data in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    assert set(outputs)<=OWNED and len(outputs)==(7 if include_comparison else 6)
    assert manifest['assembled_elements']<=1000
    assert sum(len(b) for b in outputs.values())<25*1024*1024
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    outputs=generate()
    for rel,data in outputs.items():
        p=ROOT/rel
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+rel
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} owned artifacts; {m["assembled_elements"]} opaque cuboids; {m["emitted_faces"]} faces; 0 triangle adapters; full only')
    print(f'1024 atlas, used height {m["atlas_used_height"]}; payload {sum(len(b) for b in outputs.values())} bytes; native pending')

if __name__=='__main__':main()
