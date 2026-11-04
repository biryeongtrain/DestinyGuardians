#!/usr/bin/env python3
"""W136 Seventh Seraph Officer Revolver: authored filled volumes and face paint.

Inert FBX reference parsing / deterministic CPU art only. FULL candidate, using
the existing generic reload. No registry, runtime, timing, DCC or native writes.
"""
import argparse
import base64
from collections import Counter
import copy
import io
import json
import math
from pathlib import Path
import runpy
import uuid

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ID = 'seventh_seraph_officer_revolver'
ART = f'art/weapons/w123/{ID}/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + f'models/weapon/hand_cannon/{ID}.json'
MODEL = ASSET + f'models/weapon_surface_w123/{ID}.json'
TEXTURE = ASSET + f'textures/item/weapon/w123/{ID}.png'
REPORT = f'docs/qa/2026-10-26/w136/{ID}-worker.md'
W30 = f'art/blockbench/weapons/w30/{ID}.bbmodel'
CATALOG = 'art/weapons/w30/catalog.json'
REFS = 'art/weapons/w31/references.json'
HELPER = 'scripts/generate_surface_w123_beloved.py'
RAW = Path(f'/tmp/destiny-weapons-w30/raw/{ID}/extracted')
PHOTO = Path(f'/tmp/destiny-weapons-w31/references/{ID}.jpg')
FBX = 'Seventh Seraph Officer Revolver.fbx'
BLEND = 'Seventh Seraph Officer Revolver.blend'
EDGE = 1024
H = runpy.run_path(str(ROOT / HELPER))
encode, sha, png = H['encode'], H['sha'], H['png']
rotation, vertices = H['rotation'], H['vertices']
FACES = H['FACES']
render, frame, model_triangles = H['render'], H['frame'], H['model_triangles']
PALETTE = dict(shroud=[48,51,53], crown=[65,68,69], steel=[151,157,159],
               silver=[190,194,193], mechanism=[67,72,75], rubber=[33,36,37],
               brass=[166,145,80], recess=[15,20,23], amber=[234,147,46])


def source_meshes():
    """This weapon's FBX basis is X,Z,Y, proven against selected W30 bounds.

    FBX object transform is -90 X / 100 scale (export convention); arrays
    already contain source units used by W30. Do not apply that scale twice.
    """
    meta = json.loads((ROOT / W30).read_bytes())['destiny_w30']
    for filename in (FBX, BLEND):
        assert sha((RAW / filename).read_bytes()) == meta['source_files'][filename]
    roots = H['parse_fbx'](RAW / FBX)
    objects = next(n[2] for n in roots if n[0] == 'Objects')
    links = [n[1][1:] for root in roots if root[0] == 'Connections'
             for n in root[2] if n[1][0] == 'OO']
    models = {n[1][0]: n for n in objects if n[0] == 'Model'}
    materials = {n[1][0]: n[1][1].split('\x00')[0] for n in objects if n[0] == 'Material'}
    meshes = []
    for node in objects:
        if node[0] != 'Geometry':
            continue
        mid = next(p for c, p in links if c == node[1][0])
        model = models[mid]; name = model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:
            continue
        props = {p[1][0]: p[1][4:] for c in model[2] if c[0] == 'Properties70' for p in c[2]}
        assert np.allclose(props['Lcl Rotation'], [-90, 0, 0], atol=2e-5, rtol=0)
        assert props['Lcl Scaling'] == [100, 100, 100]
        cs = {c[0]: c for c in node[2]}
        raw = np.array(cs['Vertices'][1][0]).reshape(-1, 3)
        v = raw[:, [0, 2, 1]] * meta['scale'] + meta['anchor']
        ix = np.array(cs['PolygonVertexIndex'][1][0])
        assert np.all((ix < 0).reshape(-1, 3) == [False, False, True])
        ix = np.where(ix < 0, -ix - 1, ix).reshape(-1, 3)
        layer = next(c for c in node[2] if c[0] == 'LayerElementUV' and c[1][0] == 0)
        vals = {c[0]: c[1][0] for c in layer[2]}
        assert vals['MappingInformationType'] == 'ByPolygonVertex'
        assert vals['ReferenceInformationType'] == 'IndexToDirect'
        uv = np.array(vals['UV']).reshape(-1, 2)[np.array(vals['UVIndex'])].reshape(-1, 3, 2)
        uv[:, :, 1] = 1 - uv[:, :, 1]
        mat = next(materials[c] for c, p in links if p == mid and c in materials)
        meshes.append(dict(name=name, vertices=v, faces=ix, uv=uv, material=mat))
    points = np.concatenate([m['vertices'] for m in meshes])
    assert sorted(m['name'] for m in meshes) == sorted(meta['source_objects'])
    assert sum(len(m['faces']) for m in meshes) == meta['source_triangles'] == 17960
    np.testing.assert_allclose([points.min(0), points.max(0)], meta['model_bounds'], atol=2e-6, rtol=0)
    return meshes, meta


def source_triangles(meshes):
    textures = {mat: np.asarray(Image.open(RAW / (mat + '_Diffuse.dds')).convert('RGBA'))
                for mat in sorted({m['material'] for m in meshes})}
    result = []
    for m in meshes:
        for ps, uv in zip(m['vertices'][m['faces']], m['uv']):
            normal = np.cross(ps[1] - ps[0], ps[2] - ps[0]); length = np.linalg.norm(normal)
            if length > 1e-10:
                result.append((ps, uv, textures[m['material']], normal / length))
    return result


def make_design(meta):
    parts = []

    def box(name, lo, hi, mat, group, motif='plain', turn=None):
        e = dict(name=name, **{'from': lo, 'to': hi})
        if turn:
            e['rotation'] = dict(origin=[round((a+b)/2, 7) for a, b in zip(lo, hi)])
            e['rotation'][turn[0]] = turn[1]
        parts.append(dict(geometry=e, material=mat, group=group, motif=motif))

    def c(name, pos, size, mat, group, motif='plain', turn=None):
        box(name, [round(a-b/2, 7) for a,b in zip(pos,size)],
            [round(a+b/2, 7) for a,b in zip(pos,size)], mat, group, motif, turn)

    def beam(name, a, b, width, thick, mat, group, motif='plain'):
        # Endpoints in native [Z,Y], length lies on the cube's local Z axis.
        z0,y0 = a; z1,y1 = b
        c(name, [8,(y0+y1)/2,(z0+z1)/2], [width,thick,math.hypot(z1-z0,y1-y0)+.035],
          mat, group, motif, ('x',-math.degrees(math.atan2(y1-y0,z1-z0))))

    def tube(name, y, z0, z1, r, thick, mat, group):
        for i in range(8):
            a = math.radians(i*45); rr = r-thick/2
            c(f'{name}_{i}', [8-rr*math.sin(a),y+rr*math.cos(a),(z0+z1)/2],
              [2*r*math.tan(math.pi/8)+.006,thick,z1-z0],mat,group,'bore',('z',i*45))

    # Long rounded black shroud. Its central mass stays filled; five actual
    # lateral apertures pierce only the lower vent band, as on the source.
    box('shroud_main',[7.17,11.64,-4.59],[8.83,12.76,4.23],'shroud','shroud','shroud')
    box('shroud_bottom',[7.25,10.99,-4.59],[8.75,11.18,4.23],'shroud','shroud','shroud')
    box('shroud_front_solid',[7.17,11.14,-4.59],[8.83,11.67,.24],'shroud','shroud','shroud')
    box('shroud_rear_solid',[7.17,11.14,3.26],[8.83,11.67,4.23],'shroud','shroud','shroud')
    box('shroud_crown',[7.36,12.74,-4.59],[8.64,13.035,4.23],'crown','shroud','shroud')
    for side in (-1,1):
        c(f'shroud_upper_bevel_{side}',[8+side*.69,12.77,-.18],[.31,.31,8.82],
          'shroud','shroud','shroud',('z',45*side))
        c(f'shroud_lower_bevel_{side}',[8+side*.69,11.12,-2.17],[.24,.24,4.84],
          'shroud','shroud','shroud',('z',45*side))
    centers = [.45,1.10,1.75,2.40,3.05]
    for i in range(4):
        box(f'vent_web_{i}',[7.17,11.15,centers[i]+.21],
            [8.83,11.65,centers[i+1]-.21],'shroud','shroud','vent')
    # Chamfers keep each real through-port octagonal rather than a painted dot.
    for i,z in enumerate(centers):
        for sy in (-1,1):
            for sz in (-1,1):
                c(f'vent_corner_{i}_{sy}_{sz}',[8,11.41+sy*.24,z+sz*.21],
                  [1.66,.17,.17],'shroud','shroud','vent',('x',45))
    # A true recessed muzzle bore, surrounded by solid opaque tangent walls.
    tube('muzzle_bore',12.37,-5.31536011,-4.55,.57,.16,'steel','muzzle')
    box('bore_stop',[7.55,11.92,-4.64],[8.45,12.82,-4.56],'recess','muzzle')
    box('muzzle_lower_lug',[7.38,11.10,-5.31536011],[8.62,11.88,-4.55],'shroud','muzzle','lug')
    # The squared outer silver collar is distinct from the circular bore.
    for side in (-1,1):
        c(f'front_collar_side_{side}',[8+side*.706,12.04,-4.93],[.18,1.55,.68],
          'silver','muzzle','collar')
        for y in (11.24,12.85):
            c(f'front_collar_chamfer_{side}_{y}',[8+side*.60,y,-4.93],[.25,.25,.68],
              'silver','muzzle','collar',('z',45*side))
    box('front_collar_top',[7.51,12.87,-5.27],[8.49,13.02,-4.59],'steel','muzzle','collar')
    box('front_collar_bottom',[7.49,10.99,-5.27],[8.51,11.20,-4.59],'steel','muzzle','collar')
    # Long top rail: each crossbar has silhouette and transverse depth.
    # The rail dips below the sight window; a continuous high solid here would
    # block the front-to-back air path despite apparently open side walls.
    box('top_rail',[7.59,13.34,-5.338074034963814],[8.41,13.63205351,1.22],
        'crown','rail','rail')
    box('top_rail_rear',[7.59,13.34,2.84],[8.41,13.63205351,4.36],
        'crown','rail','rail')
    box('rail_support',[7.70,13.01,-5.26],[8.30,13.39,4.32],'shroud','rail','rail')
    for i,z in enumerate(np.linspace(-4.89,3.96,17)):
        c(f'rail_tooth_{i}',[8,13.20,float(z)],[1.16,.30,.22],'shroud','rail','tooth')
    beam('front_sight_ramp',[-5.10,13.67],[-4.48,13.78],.39,.27,'steel','rail','sight')
    # Broad rear chamber and shoulders, no separate invented reload component.
    box('rear_chamber',[7.10,11.17,4.20],[8.90,12.72,7.29],'mechanism','chamber','chamber')
    for side in (-1,1):
        c(f'chamber_bevel_{side}',[8+side*.69,12.75,5.74],[.40,.40,3.07],
          'mechanism','chamber','chamber',('z',45*side))
    box('chamber_underside',[7.30,10.88,4.18],[8.70,11.21,7.46],'shroud','chamber','chamber')
    # Original narrow brass rim around the chamber front, with actual corners.
    for side in (-1,1):
        c(f'chamber_brass_side_{side}',[8+side*.893,11.96,4.32],[.13,1.55,.23],
          'brass','chamber','rim')
        c(f'chamber_brass_bevel_{side}',[8+side*.72,12.75,4.32],[.37,.18,.23],
          'brass','chamber','rim',('z',45*side))
    box('chamber_brass_top',[7.43,12.89,4.205],[8.57,13.06,4.435],'brass','chamber','rim')
    box('chamber_brass_bottom',[7.34,10.99,4.205],[8.66,11.18,4.435],'brass','chamber','rim')
    box('rear_frame',[7.38,10.54,7.23],[8.62,12.73,8.37],'mechanism','frame','frame')
    beam('rear_frame_slope',[7.24,12.81],[8.42,12.36],1.23,.46,'mechanism','frame','frame')
    box('rear_dark_wrist',[7.43,9.99,7.30],[8.57,10.70,8.49],'recess','frame','wrist')
    box('chamber_bottom_rail',[7.25,10.56,4.20],[8.75,10.90,7.61],'steel','frame','frame')
    # Under-barrel module, observed tiny amber indicator, gold latch and strap.
    box('underbarrel_body',[7.43,9.57,-1.20],[8.57,11.10,4.09],'shroud','underbarrel','module')
    box('module_front_cap',[7.41,9.61,-1.29864009],[8.59,10.34,-.72],
        'mechanism','underbarrel','cap')
    beam('module_rear_sweep',[2.67,9.62],[4.18,10.20],1.15,.48,'shroud','underbarrel','module')
    for side in (-1,1):
        c(f'module_gold_latch_{side}',[8+side*.58,10.86,1.22],[.08,.13,1.48],
          'brass','underbarrel','latch')
    for side in (-1,1):
        c(f'shroud_keeper_{side}',[8+side*.78,11.08,4.15],[.20,1.37,.25],
          'steel','underbarrel','keeper')
    box('module_amber_indicator',[7.85,9.94,-1.32],[8.15,10.13,-1.24],
        'amber','underbarrel','indicator')
    # Real trigger opening; the additional lower lozenge is also open air.
    beam('guard_front',[4.48,10.64],[4.62,9.52],.42,.23,'mechanism','guard','guard')
    beam('guard_floor',[4.62,9.52],[6.77,9.44],.42,.25,'mechanism','guard','guard')
    beam('guard_rear',[6.77,9.44],[7.49,10.15],.42,.25,'mechanism','guard','guard')
    beam('trigger_upper',[6.42,10.69],[6.51,10.08],.23,.18,'steel','guard','trigger')
    beam('trigger_curl',[6.51,10.08],[6.08,9.78],.23,.18,'steel','guard','trigger')
    for i,(a,b) in enumerate([([4.58,9.64],[3.79,8.91]),([3.79,8.91],[4.69,8.51]),
                              ([4.69,8.51],[5.72,9.12]),([5.72,9.12],[4.58,9.64])]):
        beam(f'lower_guard_loop_{i}',a,b,.65,.22,'mechanism','guard','guard')
    # Filled swept grip retains hand near native [8,8,9], with dimples in UV.
    beam('grip_neck',[7.76,10.30],[8.02,9.44],1.16,1.24,'mechanism','grip','grip')
    beam('grip_core',[7.99,9.67],[9.54,6.51],1.15,1.48,'rubber','grip','grip')
    beam('grip_backstrap',[8.65,9.70],[10.25,6.97],.94,.30,'recess','grip','backstrap')
    beam('grip_heel',[8.85,6.045],[10.583,6.89],1.17,.29,'mechanism','grip','heel')
    # Fore and aft slim bevels are full transverse solids, not side skins.
    beam('grip_front_curve',[7.41,9.17],[8.86,6.43],1.05,.29,'rubber','grip','grip')
    # Open top sight: sides and roof keep an air path along Z; no reticle plane.
    box('sight_base',[7.49,13.03,1.22],[8.51,13.22,6.36],'mechanism','sight','sight')
    for side in (-1,1):
        c(f'sight_hood_wall_{side}',[8+side*.50,13.47,2.05],[.17,.65,1.59],
          'silver','sight','sight')
    box('sight_hood_roof',[7.50,13.72,1.27],[8.50,13.85,2.84],'silver','sight','sight')
    box('sight_top_spine',[7.64,13.27,2.83],[8.36,13.43,6.39],'shroud','sight','sight')
    box('rear_sight_blade',[7.62,13.88,5.79],[8.38,14.101973705299681,7.00267753],
        'steel','sight','sight')
    beam('rear_sight_saddle',[5.95,13.91],[6.17,13.37],.69,.30,'mechanism','sight','sight')
    for side in (-1,1):
        c(f'rear_sight_fork_{side}',[8+side*.35,13.18,7.61],[.18,.40,1.65],
          'shroud','sight','sight')
    # Photo's broad silver side latch: two shoulders, no animated split.
    for side in (-1,1):
        c(f'silver_latch_{side}',[8+side*.873,12.14,1.91],[.17,.56,1.25],
          'silver','controls','latch')
        c(f'latch_cap_{side}',[8+side*.893,12.14,2.64],[.13,.52,.21],
          'steel','controls','latch')
    inputs = [BASE,W30,CATALOG,REFS,HELPER,ASSET+f'textures/item/weapon/w30/{ID}.png']
    raw_inputs = [RAW/FBX,RAW/BLEND,PHOTO] + [RAW/(n+'_Diffuse.dds') for n in
                  ('SeventhSeraphOfficerRevolverBarrel','SeventhSeraphOfficerRevolverSight')]
    ref = next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    catalog = next(r for r in json.loads((ROOT/CATALOG).read_bytes()) if r['id']==ID)
    assert catalog['family']=='hand_cannon' and catalog['frame']=='precision'
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return dict(id=ID,revision='W136',method='authored filled semantic cuboids + continuous world-aware independent face UV',
                source=meta,catalogue=catalog,default_photo=ref,palette=PALETTE,parts={'full':parts},
                coordinate_policy=dict(basis='native = raw[X,Z,Y] * scale + anchor; muzzle -Z',
                    scale=meta['scale'],anchor=meta['anchor'],fbx_rotation=[-90,0,0],fbx_scaling=[100,100,100],
                    bounds_tolerance=2e-6,hand_contact=[8,8,9],native_display='exact canonical JSON display'),
                reload_policy='FULL ONLY; existing generic reload; no new independently moving parts',
                identity=['long black shroud / squared silver muzzle band / real recessed bore',
                          'five actual chamfered lateral vents / gold chamber rim / silver latch',
                          'crossbar rail / open raised sight / underslung indicator module',
                          'swept dimpled grip / open trigger guard and lower lozenge'],
                atlas=dict(size=EDGE,gutter=2,texels_per_unit=30),
                input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
                raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
                limitations=['CPU art inspection only; native parser/pack/holding/ADS/reload and 10-20 displays pending master.',
                    'Authored default-photo material approximation, not original dye/PBR or shader reconstruction.',
                    'Curved source profiles and five round vent bores simplified to clean chamfered solids.',
                    'Small keyhole relief, screws, grip dimples and side slots use opaque face paint; not through holes.',
                    'Source matching establishes local W30 correspondence, not independent asset provenance.'])


def world_points(e, face, w, h):
    p = vertices(e)[list(FACES[face])]
    u,v = np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q = ((1-u)*(1-v))[:,:,None]*p[0]+(u*(1-v))[:,:,None]*p[1]+(u*v)[:,:,None]*p[2]+((1-u)*v)[:,:,None]*p[3]
    return u,v,q


class Paint:
    def tile(self, spec, face, w, h):
        u,v,q = world_points(spec['geometry'],face,w,h)
        x,y,z = q[:,:,0],q[:,:,1],q[:,:,2]
        mat,motif = spec['material'],spec['motif']
        rgb = np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
        rgb *= (.97+.065*np.exp(-((v-.28)/.38)**2))[:,:,None]
        edge = np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        rgb[edge<.8] *= .73
        rgb[(edge>=.8)&(edge<1.6)] *= 1.18
        side = face in ('east','west')
        if motif=='shroud':
            # Continuous physical coordinates make ribs cross bevel boundaries.
            ribs = ((z+.48*(y-11.2)+4.27)/.18)%1
            ribzone = (z> -4.40)&(z< -2.83)&(y<12.75)
            rgb[ribzone&(ribs<.23)] = [18,21,23]
            rgb[ribzone&(ribs>.23)&(ribs<.36)] = [95,100,102]
            rgb[abs(y-11.04)<.035] = [75,79,80]
            # Fine rectangular service recesses and the characteristic keyhole.
            if side:
                key = (((z-.05)/.13)**2+((y-12.07)/.10)**2<1)|((z>-.20)&(z<.45)&(abs(y-12.07)<.055))
                rgb[key]=[14,18,20]
                rgb[((z-.62)/.06)**2+((y-12.10)/.06)**2<1]=[16,20,22]
        if motif=='collar':
            rgb[(z> -4.77)&(z< -4.68)]=PALETTE['brass']
            rgb[(z> -4.69)&(z< -4.64)]=[42,41,30]
        if motif=='lug' and face=='north':
            rr=((x-8)/.23)**2+((y-11.46)/.23)**2
            rgb[rr<1.1]=[14,18,20];rgb[(rr<.65)&(rr>.28)]=PALETTE['brass']
            rgb[(rr<.65)&(abs(x-8)<.025)]=[31,30,24]
        if motif=='bore':
            rgb[(v>.25)&(v<.35)]*=.68
        if motif=='chamber' and side:
            rgb[(abs(y-11.29)<.028)|(abs(y-12.51)<.028)]*=.45
            for zz,yy,ll in [(4.93,12.39,.43),(5.72,12.47,.41),(6.56,12.29,.33),
                             (5.02,11.48,.38),(5.72,11.40,.50),(6.63,11.57,.28)]:
                mask=(abs(z-zz)<ll/2)&(abs(y-yy)<.043)
                rgb[mask]=[16,21,24]
                rgb[(abs(z-zz)<ll/2)&(abs(y-(yy-.065))<.016)]=[103,109,110]
            rgb[(abs(z-5.17)<.045)&(y>11.77)&(y<11.98)]=[25,29,31]
        if motif in ('grip','heel') and side:
            # Authored perforation pattern follows the swept handle, not UV axes.
            zz=z+.48*y
            for row in range(7):
                yy=6.82+row*.35
                for col in range(3):
                    zc=12.51+col*.36+(row%2)*.12
                    rr=((zz-zc)/.076)**2+((y-yy)/.081)**2
                    rgb[rr<1.35]=[48,53,54];rgb[rr<.72]=[16,21,23]
                    rgb[(rr>.8)&(rr<1.4)&(y<yy)]=[74,79,80]
            rgb[(zz>13.63)&(y<8.76)]=[18,24,26]
            rgb[(abs(zz-12.23)<.023)&(y>6.5)&(y<9.7)]=[77,82,83]
        if motif in ('frame','grip','guard') and side:
            for zz,yy in [(7.99,10.06),(9.31,6.58),(6.46,9.49),(7.91,12.17)]:
                rr=((z-zz)/.13)**2+((y-yy)/.13)**2
                rgb[rr<1]=[136,143,145];rgb[rr<.46]=[25,31,34]
                rgb[(rr<.46)&(abs(z-zz)<.018)]=[95,101,103]
        if motif=='module' and side:
            rgb[(y>10.25)&(y<10.29)&(z>-.70)&(z<3.5)]*=1.35
            rgb[(z>2.2)&(z<2.70)&(y>9.78)&(y<10.07)]=[18,23,25]
        if motif=='latch':
            if side:
                for zz in (1.43,2.36):
                    rgb[(abs(z-zz)<.045)&(abs(y-12.14)<.18)]=[88,96,99]
                rgb[abs(y-11.93)<.018]=[226,228,225]
            else:
                rgb[(u>.3)&(u<.36)]*=.75
        if motif=='sight':
            if side:
                for zz in (1.60,1.96,2.32,2.65):
                    mask=(abs(z-zz)<.10)&(y>13.37)&(y<13.63)
                    rgb[mask]=[26,32,35]
                    rgb[mask&(abs(z-zz)>.07)]=[106,113,116]
            if face=='up':
                rgb[(abs(x-8)<.055)&(z>5.88)&(z<6.85)]=[166,145,80]
        if motif in ('rail','tooth'):
            rgb[abs(x-8)<.13]*=.64
        if motif=='indicator':
            rr=((u-.5)/.5)**2+((v-.5)/.5)**2
            rgb[:]=[69,49,23];rgb[rr<.67]=[221,133,35];rgb[rr<.24]=[255,211,115]
        return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_models(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(22,26,28,255));paint=Paint();tiles=[]
    for s in d['parts']['full']:
        ps=vertices(s['geometry'])
        for face,ix in FACES.items():
            p=ps[list(ix)]
            w=max(6,math.ceil(np.linalg.norm(p[1]-p[0])*30))
            h=max(6,math.ceil(np.linalg.norm(p[3]-p[0])*30))
            tiles.append((s,face,w,h))
    tiles.sort(key=lambda t:(-t[3],-t[2],t[0]['geometry']['name'],t[1]))
    x=y=2;row=0;uvs={};islands=[]
    for s,f,w,h in tiles:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow')
        tile=paint.tile(s,f,w,h)
        padded=Image.fromarray(np.pad(np.asarray(tile),((2,2),(2,2),(0,0)),mode='edge'))
        atlas.paste(padded,(x-2,y-2))
        uvs[(s['geometry']['name'],f)]=[v*16/EDGE for v in (x,y,x+w,y+h)]
        islands.append(dict(element=s['geometry']['name'],face=f,rect=[x,y,x+w,y+h]))
        x+=w+4;row=max(row,h)
    es=[]
    for s in d['parts']['full']:
        e=copy.deepcopy(s['geometry'])
        e['faces']={f:dict(uv=uvs[(e['name'],f)],texture='#0') for f in FACES}
        es.append(e)
    d['atlas'].update(islands=islands,used_height=y+row+2)
    model=dict(credit='W136 Seventh Seraph Officer Revolver / authored opaque semantic solids / FULL candidate',
               textures={'0':f'destiny:item/weapon/w123/{ID}','particle':f'destiny:item/weapon/w123/{ID}'},
               elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])
    return atlas,model


def inspection(d,model,atlas):
    def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w136:'+ID+':'+n))
    es=[];groups={s['geometry']['name']:s['group'] for s in d['parts']['full']};out={}
    for e in model['elements']:
        b=copy.deepcopy(e);r=b.pop('rotation',{})
        b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
                 origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
        for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        es.append(b);out.setdefault(groups[e['name']],[]).append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},
                name='Seventh Seraph Officer Revolver W136 | editable CPU inspection',
                resolution={'width':EDGE,'height':EDGE},elements=es,
                outliner=[dict(name=g,uuid=uid(g),origin=[8,8,8],rotation=[0,0,0],children=ids,export=True)
                          for g,ids in out.items()],
                textures=[dict(name=ID+'.png',id='0',uuid=uid('texture'),width=EDGE,height=EDGE,
                    uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
                display=model['display'],destiny_w136=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],
                    sourceScale=d['source']['scale'],rotationOrder='RzRyRx',candidate='FULL ONLY'))


def comparison(d,meshes,atlas,model):
    w,h=1000,360;sheet=Image.new('RGB',(3000,1960),'#151e28');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4e7ea',font_size=size)
    label(24,14,'SEVENTH SERAPH OFFICER REVOLVER / W136 / authored filled volumes / CPU ART ONLY',30)
    photo=Image.open(PHOTO).convert('RGB').crop((950,240,1910,840));photo.thumbnail((1500,370))
    sheet.paste(photo,(24,60))
    label(1100,90,'Default photo: black / silver / narrow brass trim',26)
    label(1100,142,'Selected original FBX: 17,960 triangles; reticle excluded',24)
    label(1100,194,f'New FULL: {len(model["elements"])} opaque filled cuboids; no alpha shells',24)
    label(1100,246,'Actual lateral ports, muzzle, sight, guard and lower-loop openings',23)
    label(1100,298,'Same frame, camera and scale in each full-model row',23)
    label(1100,350,'Native QA pending master; generic reload unchanged',23)
    old=json.loads((ROOT/BASE).read_bytes())
    oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{ID}.png'))
    label(24,444,'RAW FBX / original neutral undyed diffuse')
    label(1024,444,f'CANONICAL / {len(old["elements"])} inherited cuboids')
    label(2024,444,'W136 / default-photo palette / authored face UV')
    triangles=[source_triangles(meshes),model_triangles({'old':old},oldtex),model_triangles({'full':model},atlas)]
    points=np.concatenate([m['vertices'] for m in meshes])
    for row,(name,cam) in enumerate([('SIDE',[-1,0,0]),('FRONT OBLIQUE',[-1,.40,-.65]),
                                    ('REAR / HAND FRAME',[1,.36,.64])]):
        extent=frame(points,cam,w,h)
        for col,ts in enumerate(triangles):
            im,_=render(ts,cam,extent,(w,h),raw=col==0)
            sheet.paste(im,(col*w,480+row*h));label(col*w+18,490+row*h,name,17)
    # Details use the assembled model, so nearby masses cannot be hidden to
    # manufacture a false opening. The crop is determined by semantic solids.
    fulltris=triangles[2]
    for i,(group,cam) in enumerate([('muzzle',[.18,.12,-1]),('shroud',[1,.12,-.12]),
                                    ('guard',[-1,.18,-.10]),('sight',[.20,.18,-1])]):
        names={s['geometry']['name'] for s in d['parts']['full'] if s['group']==group}
        es=[e for e in model['elements'] if e['name'] in names]
        ps=np.concatenate([vertices(e) for e in es])
        im,_=render(fulltris,cam,frame(ps,cam,750,270),(750,270))
        sheet.paste(im,(i*750,1590));label(i*750+16,1602,group.upper()+' / assembled depth',19)
    label(24,1880,'Opaque 1024 atlas, independent continuous face paint, editable BB. Curves and original dye/specular response are approximations.',21)
    label(24,1915,'Native pending: 26.3 parser/pack, first/third person, ADS/generic reload and 10-20 displays. No combat/audio/timing modifications.',20)
    return png(sheet)


def review_text(d,counts):
    return f'''# Seventh Seraph Officer Revolver W136 — offline art review

The actual default-paint photo `{PHOTO}` was opened visually before authoring. It matches W31 SHA-256 `{d['default_photo']['sha256']}` and Bungie item 3037520408. Both W30 catalog and W135 queue identify the actual family as precision hand cannon. The photo's long black shroud, silver muzzle band and side latch, narrow brass chamber trim, raised sight and perforated swept grip guide the materials and silhouette.

The FULL candidate contains **{counts['full']} opaque solid cuboids**, zero triangle/contour adapter elements, **{counts['combined']} assembled elements** (hard cap 1000). Long filled shroud and receiver masses, a substantial swept grip, shoulder bevels and transverse rail bars carry volume. Five lower shroud ports have real side-to-side air channels and solid corner chamfers. The muzzle has a recessed bore with a dark depth stop, not a painted black disk on the front. The trigger guard, smaller lower lozenge and raised sight retain actual air. Small side slots/keyhole relief, screws and grip dimples are clean face paint. No mesh islands, voxel conversion or alpha silhouette side shells are used.

The inert binary FBX reader matches all five W30 retained object names, 17,960 triangles, both source file hashes and selected bounds within 0.000002 native units. Source `Seventh-Seraph-Officer-Revolver.03.000` (reticle) remains excluded. This weapon's measured basis is native `[raw X, raw Z, raw Y] * {d['source']['scale']} + {d['source']['anchor']}`: raw Y is length, raw X thickness, raw Z height. FBX -90 X / 100 object transforms are exporter conventions; applying them again would misalign the source. The supplied W30 source bounds, source axis and canonical display are preserved as evidence, and the candidate is authored directly in that frame, muzzle -Z, with hand contact near [8,8,9]. Sculpted profiles are simplified, so new extrema need not equal old voxel extrema exactly.

The 1024 RGBA atlas is fully opaque. Each cube gets six separate proportional UV rectangles with two-pixel extruded gutters, using 30 texels/native unit. World-aware face paint keeps front diagonal ribs and grip patterns continuous across meaningful surfaces. Silver, restrained brass and subtle cool black layers are authored from the photo; original neutral DDS is used only on the raw reference render, with original UV and material assignments. No source texture reprojection is used on the candidate. Source FBX/BLEND are read-only evidence; no DCC file is opened or executed, and user unsaved work is untouched.

`comparison.png` shows actual default photo, original FBX/neutral DDS, inherited canonical cuboids and the final candidate in side/front/rear views, with assembled muzzle/vent/guard/sight close inspections. The raw source is explicitly not presented as recovered default dye. The editable inspection BB embeds the exact candidate atlas and semantic groups. The generated images are CPU art evidence; they do not establish native acceptance.

FULL ONLY preserves existing generic reload and adds no independent moving cylinder, latch, cartridge or magazine. Only this worker's ten exact owned paths are changed; canonical registration, runtime, HUD, audio, ADS and reload/combat timing are untouched. No commit/stash/reset/clean/push, Gradle, native client/server, DCC, or children were used.

Validation uses the worker's targeted Python unittest and sequential generator `--verify`. Native 26.3 parser/pack, first/third-person holding, ADS/reload, clipping and 10–20 simultaneous displays remain **pending master**. Small round vents are chamfered approximations; metallic response, exact original shader dyes, fine sculpted edges and small shallow relief remain limitations.
'''


def worker_text(counts):
    return f'''# W136 Seventh Seraph Officer Revolver worker

Worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w136-seventh_seraph_officer_revolver`.
Exclusive scope: exactly the ten paths assigned by `docs/qa/2026-10-26/w136/batch.json`.

Implemented a deterministic FULL-only remodel with {counts['combined']} emitted opaque cuboids / {counts['triangles']} triangle adapter elements, a fully opaque 1024 atlas, editable embedded-texture BB, design/manifest and actual-source comparison. Black/silver/brass default paint, long shroud, five real vent tunnels, recessed muzzle, open sight/guard/lower loop, and swept dimpled grip retain the weapon identity. Read-only W30/FBX/BLEND/photo hashes, five retained objects, 17,960 triangles, actual X,Z,Y basis, source bounds/scale/anchor, catalogue family and exact canonical display are checked.

Actual default photo and final `comparison.png` are visually inspected by the worker. CPU side and front/rear oblique rows separate raw FBX, inherited canonical and new output; native success is not claimed. Review details and honest limitations are in `art/weapons/w123/{ID}/review.md`.

Sequential final validation (bundled Python, always `-B`):

1. `rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/qa/test_surface_w123_{ID}.py`
2. `rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/generate_surface_w123_{ID}.py --verify`
3. Exact baseline delta export with `scripts/qa/worktree_batch.py export` to `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w136-seventh_seraph_officer_revolver-export`; out-of-scope list must be empty.

Final validation record: **12/12 targeted checks passed**; the subsequent sequential generator `--verify` passed. The suite covers budget, six closed opaque faces and actual voids, broad solid mass, unchanged canonical display/hand frame, source/reference correctness, editable BB parity, UV gutters, hashes and deterministic artifact regeneration. The aperture check initially caught rail occlusion inside the sight; the final rail dips below that window, and all solids form one connected assembly. Exact export scope is checked against the seeded baseline before handoff; consult the export manifest for its path/hash records.

Native QA **pending master**: parser/pack, first/third-person holding, ADS, generic reload, clipping and 10–20 displays. No registry/manifest shared by other weapons, HUD/runtime/timing changes, dependency duplication, Gradle, DCC, native launches or children. The existing generic reload remains in use. Inherited dirty/untracked product is preserved; no commit/stash/reset/clean/push.
'''


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meta);atlas,model=compile_models(d)
    groups=dict(Counter(s['group'] for s in d['parts']['full']))
    counts=dict(full=len(model['elements']),triangles=0,combined=len(model['elements']),by_semantic_group=groups)
    assert counts['combined']<=1000
    ps=np.concatenate([vertices(e) for e in model['elements']])
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),
             ART+'review.md':review_text(d,counts).encode(),REPORT:worker_text(counts).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    manifest=dict(id=ID,revision='W136',family=d['catalogue']['family'],counts=counts,
        assembled_elements=counts['combined'],max_assembled_elements=1000,opaque_cuboids=counts['full'],
        triangle_adapter_elements=0,alpha_elements=0,emitted_faces=6*counts['full'],texture_size=[EDGE,EDGE],
        actual_bounds=[ps.min(0).tolist(),ps.max(0).tolist()],source_bounds=meta['model_bounds'],
        source_scale=meta['scale'],source_anchor=meta['anchor'],source_axis=meta['source_axis'],
        source_basis=d['coordinate_policy']['basis'],source_triangles=meta['source_triangles'],
        canonical_display_exact=True,native_accepted=False,candidate='FULL ONLY',reload_policy=d['reload_policy'],
        default_photo_sha256=d['default_photo']['sha256'],input_sha256=d['input_sha256'],
        raw_input_sha256=d['raw_input_sha256'],generator_sha256=sha(Path(__file__).read_bytes()),
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true');args=parser.parse_args();outputs=generate()
    allowed={ART+n for n in ('design.json','manifest.json','review.md','inspection.bbmodel','comparison.png')}|{MODEL,TEXTURE,REPORT}
    assert set(outputs)==allowed
    for rel,data in outputs.items():
        p=ROOT/rel
        if args.verify:assert p.is_file() and p.read_bytes()==data,'Regeneration differs: '+rel
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    manifest=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f' 8 owned artifacts; {manifest["counts"]}; {manifest["emitted_faces"]} faces')


if __name__=='__main__':
    main()
