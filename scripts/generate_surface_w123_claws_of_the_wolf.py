#!/usr/bin/env python3
"""W138 Claws of the Wolf: authored filled volumes and face paint.

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
ID = 'claws_of_the_wolf'
ART = f'art/weapons/w123/{ID}/'
ASSET = 'src/main/resources/assets/destiny/'
BASE = ASSET + f'models/weapon/pulse_rifle/{ID}.json'
MODEL = ASSET + f'models/weapon_surface_w123/{ID}.json'
TEXTURE = ASSET + f'textures/item/weapon/w123/{ID}.png'
REPORT = f'docs/qa/2026-10-26/w138/{ID}-worker.md'
W30 = f'art/blockbench/weapons/w30/{ID}.bbmodel'
CATALOG = 'art/weapons/w30/catalog.json'
REFS = 'art/weapons/w31/references.json'
HELPER = 'scripts/generate_surface_w123_beloved.py'
RAW = Path(f'/tmp/destiny-weapons-w30/raw/{ID}/extracted/Claws of the Wolf')
PHOTO = Path(f'/tmp/destiny-weapons-w31/references/{ID}.jpg')
FBX = 'Claws of the Wolf.fbx'
BLEND = 'Claws of the Wolf.blend'
EDGE = 1024
H = runpy.run_path(str(ROOT / HELPER))
encode, sha, png = H['encode'], H['sha'], H['png']
rotation, vertices = H['rotation'], H['vertices']
FACES = H['FACES']
render, frame, model_triangles = H['render'], H['frame'], H['model_triangles']
PALETTE = dict(teal=[46,64,62], stock=[51,69,67], burgundy=[88,53,48],
               steel=[91,99,100], black=[27,33,35], brass=[184,143,65],
               edge=[132,116,108], recess=[12,17,19], lens=[23,34,38])


def source_meshes():
    """This weapon's FBX basis is X,Z,Y, proven against selected W30 bounds.

    FBX object transform is -90 X / 100 scale (export convention); arrays
    already contain source units used by W30. Do not apply that scale twice.
    """
    meta = json.loads((ROOT / W30).read_bytes())['destiny_w30']
    for filename in (FBX, BLEND):
        assert sha((RAW / filename).read_bytes()) == meta['source_files']['Claws of the Wolf/'+filename]
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
        assert np.allclose(props['Lcl Scaling'], [100,100,100], atol=2e-5, rtol=0)
        assert np.allclose(props['Lcl Translation'], [0,0,0], atol=1e-6, rtol=0)
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
    assert sum(len(m['faces']) for m in meshes) == meta['source_triangles'] == 28292
    np.testing.assert_allclose([points.min(0), points.max(0)], meta['model_bounds'], atol=2e-6, rtol=0)
    return meshes, meta


def source_triangles(meshes):
    textures = {mat: np.asarray(Image.open(RAW / ('COTW'+mat+'_Diffuse.png')).convert('RGBA'))
                for mat in sorted({m['material'] for m in meshes})}
    result = []
    for m in meshes:
        for ps, uv in zip(m['vertices'][m['faces']], m['uv']):
            normal = np.cross(ps[1] - ps[0], ps[2] - ps[0]); length = np.linalg.norm(normal)
            if length > 1e-10:
                result.append((ps, uv, textures[m['material']], normal / length))
    return result


def make_design(meta):
    # Deliberately authored functional volumes; raw triangles are reference only.
    parts=[]
    def box(name,lo,hi,mat,group,motif='plain',turn=None):
        e=dict(name=name,**{'from':lo,'to':hi})
        if turn:e['rotation']=dict(origin=[(a+b)/2 for a,b in zip(lo,hi)],**{turn[0]:turn[1]})
        parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
    def c(name,pos,size,mat,group,motif='plain',turn=None):
        box(name,[round(a-b/2,8) for a,b in zip(pos,size)],
            [round(a+b/2,8) for a,b in zip(pos,size)],mat,group,motif,turn)
    def beam(name,a,b,width,thick,mat,group,motif='plain'):
        z0,y0=a;z1,y1=b
        c(name,[8,(y0+y1)/2,(z0+z1)/2],[width,thick,math.hypot(z1-z0,y1-y0)+.035],
          mat,group,motif,('x',-math.degrees(math.atan2(y1-y0,z1-z0))))
    def tube(name,y,z0,z1,r,thick,mat,group,motif='plain'):
        for i in range(8):
            a=math.radians(i*45);rr=r-thick/2
            c(f'{name}_{i}',[8-rr*math.sin(a),y+rr*math.cos(a),(z0+z1)/2],
              [2*r*math.tan(math.pi/8)+.006,thick,z1-z0],mat,group,motif,('z',i*45))
    # Forked two-claw flash hider. Air passes between the jaws, around a short
    # recessed barrel. These are substantial solid tines, not alpha side cards.
    box('upper_claw',[7.64,11.40,-8.366611317313862],[8.36,11.61,-5.65],'burgundy','muzzle','claw')
    box('lower_claw',[7.64,10.63,-8.366611317313862],[8.36,10.84,-5.65],'burgundy','muzzle','claw')
    for name,y in [('upper',11.505),('lower',10.735)]:
        c(name+'_claw_tip',[8,y,-8.366611317313862],[.48,.21,.48],
          'burgundy','muzzle','claw',('y',45))
    box('upper_claw_root',[7.62,11.30,-6.15],[8.38,11.48,-5.56],'steel','muzzle','claw')
    box('lower_claw_root',[7.62,10.77,-6.15],[8.38,10.95,-5.56],'steel','muzzle','claw')
    tube('inner_barrel',11.12,-7.05,-5.49,.235,.09,'steel','muzzle','bore')
    box('bore_stop',[7.83,10.95,-5.59],[8.17,11.29,-5.49],'recess','muzzle')
    tube('muzzle_collar',11.12,-5.65,-4.93,.50,.25,'black','muzzle','collar')
    # Functional front trunnion with a real transverse cross-section.
    box('front_trunnion',[7.46,10.45,-4.98],[8.54,11.63,-3.60],'black','trunnion','mechanism')
    for side in (-1,1):
        c(f'trunnion_shoulder_{side}',[8+side*.45,11.52,-4.28],[.34,.34,1.40],
          'steel','trunnion','mechanism',('z',45*side))
    for i,z in enumerate((-4.70,-4.20,-3.70)):
        c(f'trunnion_rail_{i}',[8,11.73,z],[1.08,.18,.18],'black','trunnion','rail')
    # Two long filled masses, top burgundy forging, and continuous lower claw
    # sweep. Face paint supplies fine ribs; no body built from thin side walls.
    box('receiver_core',[7.32,10.27,-3.67],[8.68,11.49,6.50],'teal','receiver','receiver')
    box('receiver_lower',[7.46,9.89,-3.62],[8.54,10.36,4.10],'black','receiver','receiver')
    box('upper_forging',[7.34,11.48,-3.72],[8.66,11.72,6.50],'burgundy','receiver','forging')
    for side in (-1,1):
        c(f'upper_bevel_{side}',[8+side*.59,11.48,1.37],[.29,.29,10.10],
          'burgundy','receiver','forging',('z',45*side))
    box('lower_forging',[7.49,9.46,-4.55],[8.51,9.82,3.60],'burgundy','underframe','forging')
    beam('lower_forging_rise',[3.40,9.64],[4.55,9.94],1.02,.34,'burgundy','underframe','forging')
    beam('front_underbrace',[-4.25,9.72],[-3.55,10.68],.63,.25,'black','underframe')
    box('underbrace_tip',[7.69,9.69,-4.78],[8.31,10.03,-4.42],'steel','underframe','cap')
    # Five diamond-backed golden wolf studs per side, deliberately kept proud
    # of the receiver. Their shallow snout/ear relief is paint on each boss.
    for side in (-1,1):
        for i,z in enumerate((-2.69,-.95,.662,2.234,3.834)):
            c(f'wolf_setting_{side}_{i}',[8+side*.735,10.83,z],[.22,.60,.60],
              'burgundy','wolf_studs','setting',('x',45))
            c(f'wolf_boss_{side}_{i}',[8+side*.956,10.83,z],[.292,.26,.30],
              'brass','wolf_studs','wolf')
            c(f'wolf_snout_{side}_{i}',[8+side*1.063,10.77,z-.04],[.08,.13,.16],
              'brass','wolf_studs','snout',('y',side*12))
    for i,z in enumerate((-2.0,-.70,.61,1.92)):
        c(f'top_setting_{i}',[8,11.78,z],[.51,.12,.51],'burgundy','wolf_studs','setting',('y',45))
        c(f'top_stud_{i}',[8,11.94,z],[.18,.28,.18],'brass','wolf_studs','stud')
    for i,z in enumerate((-3.60,-2.52)):
        c(f'under_stud_{i}',[8,9.28,z],[.18,.38,.18],'brass','wolf_studs','stud')
    # Swept U-shaped front guard; centre remains true air, including from front.
    beam('guard_front',[3.63,9.78],[4.65,8.72],1.05,.43,'burgundy','guard','forging')
    beam('guard_floor',[4.65,8.72],[5.57,8.52],1.05,.43,'burgundy','guard','forging')
    beam('guard_rear',[5.57,8.52],[6.94,9.14],1.05,.36,'burgundy','guard','forging')
    beam('guard_wrist',[6.87,9.10],[7.48,9.68],1.07,.42,'teal','guard','receiver')
    beam('trigger_stem',[6.26,10.27],[6.26,9.46],.20,.17,'steel','guard','trigger')
    beam('trigger_hook',[6.26,9.46],[5.97,9.17],.20,.17,'steel','guard','trigger')
    # Original hand position stays around [8,8,8]; no global recenter/scale.
    beam('grip_core',[7.49,9.77],[8.43,6.66],.97,1.17,'teal','grip','grip')
    beam('grip_backstrap',[8.04,9.52],[8.98,6.83],.88,.22,'black','grip','grip')
    beam('grip_heel',[7.75,6.42],[9.19,6.96],1.05,.30,'black','grip','grip')
    box('rear_action',[7.40,10.04,6.43],[8.60,11.56,9.42],'stock','action','action')
    box('receiver_wrist',[7.47,9.69,6.78],[8.53,10.38,8.15],'teal','action','action')
    for side in (-1,1):
        c(f'action_dial_{side}',[8+side*.63,11.06,8.43],[.20,.47,.47],
          'black','action','dial',('x',45))
    # Stock is a filled tapered mass, not a perimeter shell. Its cut-out ahead
    # of the bullpup magazine remains open. The original wolf/stripe stencil
    # is isolated from neutral raw albedo and painted only on these surfaces.
    box('stock_core',[7.40,9.91,9.42],[8.60,11.35,15.53],'stock','stock','stock')
    box('stock_upper',[7.43,11.32,9.36],[8.57,11.60,15.91],'burgundy','stock','forging')
    beam('stock_cheek_sweep',[9.48,11.52],[10.88,11.39],1.20,.34,'burgundy','stock','forging')
    box('stock_lower',[7.43,8.39,11.30],[8.57,10.07,14.14],'stock','stock','stock')
    beam('stock_lower_rear',[14.02,8.57],[15.57,9.77],1.14,.48,'stock','stock','stock')
    beam('stock_butt',[15.49,8.73],[15.84,10.94],1.12,.32,'black','stock','butt')
    beam('stock_toe',[15.12,8.81],[15.70,8.55],.97,.23,'burgundy','stock','forging')
    box('stock_tail',[7.59,11.09,15.78],[8.41,11.53,16.293977427716595],'burgundy','stock','forging')
    for i,z in enumerate((10.24,11.71,13.23)):
        c(f'stock_top_setting_{i}',[8,11.62,z],[.48,.10,.48],'burgundy','wolf_studs','setting',('y',45))
        c(f'stock_top_boss_{i}',[8,11.73,z],[.24,.15,.24],'brass','wolf_studs','stud')
    for side in (-1,1):
        c(f'stock_wolf_setting_{side}',[8+side*.67,10.84,12.42],[.30,.70,.70],
          'burgundy','wolf_studs','setting',('x',45))
        c(f'stock_wolf_boss_{side}',[8+side*.976,10.84,12.42],[.324,.28,.32],
          'brass','wolf_studs','wolf')
        c(f'stock_wolf_snout_{side}',[8+side*1.098,10.78,12.38],[.08,.13,.16],
          'brass','wolf_studs','snout')
    # Bullpup magazine remains part of FULL; no invented moving reload split.
    beam('magazine_core',[11.65,9.64],[11.02,6.55],1.03,1.69,'black','magazine','magazine')
    beam('magazine_floor',[10.16,6.70],[11.89,6.39],1.07,.22,'steel','magazine','magazine')
    # Short original tube optic with a recessed opaque lens and proud dial.
    box('optic_foot',[7.61,11.58,4.72],[8.39,11.83,6.73],'black','optic','mount')
    box('optic_pedestal',[7.68,11.79,5.25],[8.32,12.12,6.40],'black','optic','mount')
    tube('optic_shell',12.53,4.07,7.22,.64,.17,'burgundy','optic','optic')
    box('optic_rear',[7.56,12.08,7.08],[8.44,12.98,7.46972291],'black','optic','optic')
    box('optic_lens',[7.57,12.10,4.53],[8.43,12.96,4.61],'lens','optic','lens')
    box('optic_top_plate',[7.68,13.09,5.23],[8.32,13.25863796315062,6.75],'burgundy','optic','optic')
    for side in (-1,1):
        c(f'optic_dial_{side}',[8+side*.57,12.59,4.92],[.15,.39,.39],
          'brass','optic','dial',('x',45))
    inputs=[BASE,W30,CATALOG,REFS,HELPER,ASSET+f'textures/item/weapon/w30/{ID}.png']
    raw_inputs=[RAW/FBX,RAW/BLEND,PHOTO]+[RAW/('COTW'+mat+suffix+'.png')
        for mat in ('Frame','Sight') for suffix in ('_Diffuse','_Normal','_GStack')]
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    cat=next(r for r in json.loads((ROOT/CATALOG).read_bytes()) if r['id']==ID)
    assert cat['family']=='pulse_rifle' and cat['frame']=='rapid_fire'
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return dict(id=ID,revision='W138',method='authored filled semantic cuboids + independent world-aware face UV',
        source=meta,catalogue=cat,default_photo=ref,palette=PALETTE,parts={'full':parts},
        coordinate_policy=dict(basis='native = raw[X,Z,Y] * scale + anchor; muzzle -Z',
            scale=meta['scale'],anchor=meta['anchor'],fbx_rotation=[-90.00000933466734,0,0],
            fbx_scaling=[99.99998474121094]*3,fbx_translation=[0,-7.450580596923828e-7,-3.725290298461914e-7],
            bounds_tolerance=2e-6,hand_contact=[8,8,8],native_display='exact canonical JSON display'),
        reload_policy='FULL ONLY; existing generic reload; no new independently moving parts',
        identity=['two-claw forked muzzle with recessed barrel','dark teal ribbed long body / burgundy forging',
                  'five brass wolf studs on each side / four upper studs / three stock studs',
                  'original wolf and striped stock stencil / compact short optic',
                  'open swept guard / filled sloped grip / bullpup magazine'],
        atlas=dict(size=EDGE,gutter=2,texels_per_unit=25,
            stencil='Only original black wolf/stripe ink, side-specific CPU UV evidence; no source geometry conversion'),
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw_inputs},
        limitations=['CPU art inspection only; native parser/pack/holding/ADS/reload and 10-20 displays pending master.',
            'Authored default-photo palette, not original dye/PBR or shader reconstruction.',
            'Smooth source claw tips, rounded grip, stock taper and optic simplified to rotated filled solids.',
            'Wolf ear/eye relief, body ribs, small screws and subtle engraving use opaque face paint.',
            'Source matching establishes local W30 correspondence, not independent asset provenance.'])


def world_points(e, face, w, h):
    p = vertices(e)[list(FACES[face])]
    u,v = np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    q = ((1-u)*(1-v))[:,:,None]*p[0]+(u*(1-v))[:,:,None]*p[1]+(u*v)[:,:,None]*p[2]+((1-u)*v)[:,:,None]*p[3]
    return u,v,q


class Paint:
    def __init__(self):
        # A motif-only stencil: recover only the supplied black ink from original
        # UV evidence. Never reuse the source noisy material or mesh islands.
        meshes,_=source_meshes();ps=np.concatenate([m['vertices'] for m in meshes])
        ts=source_triangles(meshes);self.masks={}
        for face,cam in [('west',[-1,0,0]),('east',[1,0,0])]:
            ex=frame(ps,cam,2400,760);im,valid=render(ts,cam,ex,(2400,760),raw=True)
            ink=(np.asarray(im).mean(2)<38)&valid
            self.masks[face]=(ink,ex,1 if face=='west' else -1)
    def tile(self,spec,face,w,h):
        u,v,q=world_points(spec['geometry'],face,w,h);x,y,z=q[:,:,0],q[:,:,1],q[:,:,2]
        mat,motif=spec['material'],spec['motif'];side=face in ('east','west')
        rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
        rgb*=(.96+.07*np.exp(-((v-.30)/.37)**2))[:,:,None]
        edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h])
        rgb[edge<.8]*=.74;rgb[(edge>=.8)&(edge<1.6)]*=1.20
        if mat=='burgundy':
            # Broad hammered facets rather than noisy source-material baking.
            hammer=np.sin(z*10.1+y*5.7+x*8)*np.sin(z*7.3-y*9.1)
            rgb+=hammer[:,:,None]*7
            rgb[(edge>1.2)&(edge<2.4)]=[142,126,115]
        if mat in ('teal','stock'):
            # Source's tightly stacked horizontal lamination, authored in world
            # coordinates so ribs continue across structural shoulder faces.
            ribs=(y*31)%1
            rgb[ribs<.20]*=.66;rgb[(ribs>.20)&(ribs<.36)]*=1.15
        if side and motif in ('stock','receiver','action','grip'):
            ink,ex,sign=self.masks[face];center,scale=ex
            tx=np.clip(((sign*z-center[0])*scale+1200).astype(int),0,2399)
            ty=np.clip((380-(y-center[1])*scale).astype(int),0,759)
            allowed=(z>4.3)&(y<11.57)
            rgb[ink[ty,tx]&allowed]=[12,20,21]
        if motif in ('receiver','action') and side:
            rgb[(abs(y-10.34)<.022)&(z<4.0)]=[87,100,97]
            # Restrained ejection/service-port seam; original body remains long.
            port=(z>7.0)&(z<7.93)&(y>10.65)&(y<11.15)
            rgb[port]*=.62
            rgb[(abs(y-11.15)<.025)&(z>7)&(z<7.93)]=[105,118,115]
        if motif=='setting':
            rgb[(edge>1.1)&(edge<2.2)]=[129,107,92]
            rgb[(edge>2.2)&(edge<3.5)]*=.6
        if motif=='wolf' and side:
            # Recognizable raised golden wolf head: pointed ears, eye, snout.
            # Its boss has actual transverse depth; shallow relief stays UV.
            px=(u-.5)*2;py=(v-.5)*2
            rgb*=.94
            ear=(abs(px)>.43)&(py<-.06)&(py>-.70)&(abs(px)<.72)
            rgb[ear]=[113,75,31]
            rr=((px-.12)/.40)**2+((py-.22)/.34)**2
            rgb[rr<1]=[224,177,84]
            rgb[((px+.32)/.13)**2+((py+.18)/.13)**2<1]=[57,43,24]
            rgb[(px>.36)&(py>.16)&(py<.44)]=[109,75,29]
        if motif=='dial' and side:
            rr=((u-.5)*2)**2+((v-.5)*2)**2
            rgb[(rr>.40)&(rr<.74)]*=.52
            rgb[rr<.13]*=1.3
        if motif=='magazine' and side:
            rgb[(abs(z-10.65-.22*(y-8))<.055)|(abs(z-11.32-.22*(y-8))<.055)]*=.55
            rgb[(abs(y-6.87)<.035)]=[99,108,105]
        if motif=='grip':
            lines=(y*11+z*3.4)%1
            rgb[lines<.12]*=.66
        if motif=='collar':
            rgb[(z>-5.30)&(z<-5.20)]*=.50
            rgb[(z>-5.18)&(z<-5.10)]*=1.35
        if motif=='claw':
            rgb[(edge>1.4)&(edge<3)]=[167,163,151]
        if motif=='optic' and side:
            rgb[(abs(y-12.82)<.025)&(z>5.3)&(z<6.92)]*=.5
        if motif=='lens' and face in ('north','south'):
            rr=((x-8)/.44)**2+((y-12.53)/.44)**2
            rgb[:]=[12,20,23]
            rgb+=np.clip(1-rr,0,1)[:,:,None]*[10,18,23]
            glint=np.exp(-(((x-7.83)/.10)**2+((y-12.70)/.07)**2))
            rgb+=glint[:,:,None]*[84,98,101]
        return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_models(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(22,26,28,255));paint=Paint();tiles=[]
    for s in d['parts']['full']:
        ps=vertices(s['geometry'])
        for face,ix in FACES.items():
            p=ps[list(ix)]
            w=max(6,math.ceil(np.linalg.norm(p[1]-p[0])*d['atlas']['texels_per_unit']))
            h=max(6,math.ceil(np.linalg.norm(p[3]-p[0])*d['atlas']['texels_per_unit']))
            if s['motif']=='wolf' and face in ('east','west'):
                w=h=32  # Face-authored hero motif receives extra texels.
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
    model=dict(credit='W138 Claws of the Wolf / authored opaque semantic solids / FULL candidate',
               textures={'0':f'destiny:item/weapon/w123/{ID}','particle':f'destiny:item/weapon/w123/{ID}'},
               elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])
    return atlas,model


def inspection(d,model,atlas):
    def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w138:'+ID+':'+n))
    es=[];groups={s['geometry']['name']:s['group'] for s in d['parts']['full']};out={}
    for e in model['elements']:
        b=copy.deepcopy(e);r=b.pop('rotation',{})
        b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
                 origin=r.get('origin',[8,8,8]),rotation=[r.get(a,0) for a in 'xyz'])
        for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        es.append(b);out.setdefault(groups[e['name']],[]).append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},
                name='Claws of the Wolf W138 | editable CPU inspection',
                resolution={'width':EDGE,'height':EDGE},elements=es,
                outliner=[dict(name=g,uuid=uid(g),origin=[8,8,8],rotation=[0,0,0],children=ids,export=True)
                          for g,ids in out.items()],
                textures=[dict(name=ID+'.png',id='0',uuid=uid('texture'),width=EDGE,height=EDGE,
                    uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
                display=model['display'],destiny_w138=dict(nativeAccepted=False,sourceAnchor=d['source']['anchor'],
                    sourceScale=d['source']['scale'],rotationOrder='RzRyRx',candidate='FULL ONLY'))


def comparison(d,meshes,atlas,model):
    w,h=1000,360;sheet=Image.new('RGB',(3000,1960),'#151e28');draw=ImageDraw.Draw(sheet)
    def label(x,y,s,size=21):draw.text((x,y),s,fill='#e4e7ea',font_size=size)
    label(24,14,'CLAWS OF THE WOLF / W138 / authored filled volumes / CPU ART ONLY',30)
    photo=Image.open(PHOTO).convert('RGB').crop((540,245,1880,735));photo.thumbnail((1500,370))
    sheet.paste(photo,(24,60))
    label(1100,90,'Default photo: dark teal / burgundy / brass wolves',26)
    label(1100,142,'Selected original FBX: 28,292 triangles; reticle excluded',24)
    label(1100,194,f'New FULL: {len(model["elements"])} opaque filled cuboids; no alpha shells',24)
    label(1100,246,'Forked claws / recessed bore / solid stock / open swept guard',23)
    label(1100,298,'Same frame, camera and scale in each full-model row',23)
    label(1100,350,'Native QA pending master; generic reload unchanged',23)
    old=json.loads((ROOT/BASE).read_bytes())
    oldtex=Image.open(ROOT/(ASSET+f'textures/item/weapon/w30/{ID}.png'))
    label(24,444,'RAW FBX / original neutral undyed diffuse')
    label(1024,444,f'CANONICAL / {len(old["elements"])} inherited cuboids')
    label(2024,444,'W138 / default-photo palette / authored face UV')
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
    for i,(group,cam) in enumerate([('muzzle',[.18,.12,-1]),('stock',[1,.22,.35]),
                                    ('guard',[-1,.18,-.10]),('optic',[.25,.12,-1])]):
        names={s['geometry']['name'] for s in d['parts']['full'] if s['group']==group}
        es=[e for e in model['elements'] if e['name'] in names]
        ps=np.concatenate([vertices(e) for e in es])
        im,_=render(fulltris,cam,frame(ps,cam,750,270),(750,270))
        sheet.paste(im,(i*750,1590));label(i*750+16,1602,group.upper()+' / assembled depth',19)
    label(24,1880,'Opaque 1024 atlas, independent continuous face paint, editable BB. Curves and original dye/specular response are approximations.',21)
    label(24,1915,'Native pending: 26.3 parser/pack, first/third person, ADS/generic reload and 10-20 displays. No combat/audio/timing modifications.',20)
    return png(sheet)


def review_text(d,counts):
    return f'''# Claws of the Wolf W138 — offline art review

Reference: actual default photo `{PHOTO}` (Bungie 1280933460, SHA-256 `{d['default_photo']['sha256']}`), opened with local view_image before authoring. W30 catalog confirms rapid-fire pulse rifle. The distinguishing features are the two-claw flash hider, black/teal laminated body, long burgundy forging, five proud brass wolf studs per side, four on the top body, three on the stock, a compact burgundy optic and the black wolf/stripe stock stencil.

The FULL-only candidate has **{counts['combined']} assembled opaque cuboids**, **0 triangle adapter elements**, **{6*counts['full']} explicitly UV'd faces**, against the 1000-element ceiling. The first semantic draft used 114 solids within the 80–120-cube reference range. Two tapered claw tips and twelve small proud wolf snouts justify the final additional solids. Receiver, grip, stock, magazine and long trunnion have filled cross-sections. Two substantial solid claws surround an actual air slot and recessed barrel bore. The swept guard has genuine air; the short optic has a recessed opaque lens. No alpha side shells, mesh-island transplantation, voxel conversion or invented native triangles are emitted.

The CPU binary FBX parser independently matches the two W30 retained names, 28,292 triangles, source FBX/BLEND hashes and selected bounds within 0.000002 native units. Reticle object Claws-of-the-Wolf.02.000 remains excluded. Measured native basis is `[raw X, raw Z, raw Y] * {d['source']['scale']} + {d['source']['anchor']}`. Raw X is thickness, Y length and Z height; this was verified for Claws rather than assumed from Beloved. FBX local -90.000009 X rotation, 99.999985 object scale and sub-microunit translation are inspected exporter conventions and are not applied twice. Geometry is authored in the existing native frame, muzzle -Z, hand near [8,8,8], with the original muzzle and butt Z endpoints. Display dictionary is copied exactly; no global recenter, scale or grip adjustment occurs.

The opaque 1024 atlas assigns six independent proportional rectangles to every solid at 25 texels/native unit (32px hero wolf-head faces), with 2px edge-extruded gutters. Paint is authored in physical coordinates: continuous fine body lamination, narrow mechanism seams, limited hammered burgundy variation, bright worn edges, shallow stud head relief, grip lines and magazine flutes. Original diffuse is neutral, so it is explicitly labeled undyed in the raw reference render. Only the black wolf/stripe ink is isolated using original side-specific source UV evidence onto the new action, stock and grip. New geometry and UV islands are authored independently; the source material noise is discarded. Wolf snouts project from genuinely protruding gold bosses and diamond settings; shallow ear/eye relief uses paint. Palette and static shading approximate the photo; they do not recover original dyes, PBR, metallic reflections or shader graphs.

`comparison.png` distinguishes actual photo, original raw FBX with neutral diffuse, existing 239-cuboid canonical and the candidate in matched side/front/rear views. Detail crops render the whole assembly around muzzle, stock, guard and optic so occluding neighbours are retained. `inspection.bbmodel` is editable, uses semantic groups, exact geometry and embedded candidate atlas. The worker opens the final comparison with local view_image and records observations in the report. CPU images are art evidence, not native acceptance.

FULL ONLY leaves existing generic reload, gameplay, audio, timings, item registration, HUD and shared registry to the master. The worker changes exactly the ten assigned paths. No commits/stash/reset/clean/push, dependencies, build/run copies, Gradle, server/client, GUI, Blender, Blockbench or other workers are used.

Limitations: smooth pointed claw tips, curved stock taper and rounded grip/optic are simplified; the stock wolf stencil stretches slightly around authored planar shoulders; brass relief is stylized and tiny engravings are paint. Native 26.3 parser/resource pack, first/third-person holding, ADS, reload/clipping and 10–20 simultaneous displays remain **pending master**.
'''


def worker_text(counts):
    return f'''# W138 Claws of the Wolf worker

Worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w138-claws_of_the_wolf`.
Scope: exactly the ten owned paths in `docs/qa/2026-10-26/w138/batch.json`. Main is not edited. The inherited dirty/untracked baseline and provenance are preserved.

Implemented FULL-only **{counts['combined']} opaque semantic cuboids / 0 triangle adapter elements / {6*counts['full']} faces**, with a fully opaque authored 1024 face atlas and two-pixel gutters. Forked claws, recessed barrel bore, teal laminated body, burgundy forging, five brass wolf bosses per side, top/stock studs, original wolf stripes, compact optic, open swept guard, substantial grip and bullpup magazine preserve identity. Source basis independently checked: X,Z,Y times W30 scale plus original [8,8,8] anchor; 28,292 retained raw triangles, two exact source object names, source hashes, canonical display and native axis are preserved.

Visual inspection: actual default-paint photo and generated comparison opened with local view_image. Matched side/front/rear views separate raw FBX neutral diffuse, inherited canonical and authored output. The final sheet visibly retains the forked muzzle, real guard air, substantial teal body/grip/magazine, burgundy trim and the original wolf stencil on both sides. Brass snouts project at oblique angles. An initial structural check caught disconnected stock bosses, stock toe and magazine floor; their contacts were corrected. Smooth curves and micro relief remain stylized. CPU images do not establish native appearance.

Sequential validation uses `/Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B`:

1. `scripts/generate_surface_w123_claws_of_the_wolf.py` generation.
2. `scripts/qa/test_surface_w123_claws_of_the_wolf.py` — 12 targeted checks, including regenerated byte parity, closed solids/budget, actual assembled voids, material/UV/gutters, source alignment and provenance, hand/display frame, BB parity and export integration portability.
3. `scripts/generate_surface_w123_claws_of_the_wolf.py --verify` — deterministic complete artifact check, run after tests without a race.
4. `scripts/qa/worktree_batch.py export --worktree /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w138-claws_of_the_wolf --output /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w138-claws_of_the_wolf-export` — exact baseline delta and hash provenance. Export metadata is authoritative for delivered file hashes and scope.

Final validation: **12/12 targeted tests PASS**, then sequential generator **--verify PASS**.

The test accepts its designated worktree directly; after integration into main it verifies the master's `claws_of_the_wolf-integration.json` (baseline matched, integrated status, exact source/export and all ten delivered path hashes). It never asserts a worker-only cwd as a global condition.

Native **pending master**: parser/pack and shared registration, first/third person, ADS/generic reload, clipping and 10–20 displays. Existing gameplay, reload, audio, timings, shared registry and HUD are untouched. No DCC/GUI/native/Gradle launches, other workers, dependency duplication, commit/stash/reset/clean/push. Rounded profiles, original shader/PBR and microscopic relief remain approximations. New outputs are under 25MiB.
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
    manifest=dict(id=ID,revision='W138',family=d['catalogue']['family'],counts=counts,
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
