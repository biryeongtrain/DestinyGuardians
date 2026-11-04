#!/usr/bin/env python3
"""W138 Apostate semantic opaque remodel. CPU only; full representation only.

Geometry is hand-authored by functional volume, never fitted to mesh islands or
voxels. Beloved's inert FBX reader and CPU raster routines are read-only helpers.
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
ASSET = 'src/main/resources/assets/destiny/'
ART = 'art/weapons/w123/apostate/'
BASE = ASSET+'models/weapon/sniper_rifle/apostate.json'
BB = 'art/blockbench/weapons/w30/apostate.bbmodel'
MODEL = ASSET+'models/weapon_surface_w123/apostate.json'
TEXTURE = ASSET+'textures/item/weapon/w123/apostate.png'
BATCH = 'docs/qa/2026-10-26/w138/batch.json'
HELPER = 'scripts/generate_surface_w123_beloved.py'
RAW = Path('/tmp/destiny-weapons-w30/raw/apostate/extracted/Apostate')
PHOTO = Path('/tmp/destiny-weapons-w31/references/apostate.jpg')
EDGE = 1024
H = runpy.run_path(str(ROOT/HELPER))
FACES, NORMALS = H['FACES'], H['NORMALS']
rotation, vertices = H['rotation'], H['vertices']
render, frame, model_triangles = H['render'], H['frame'], H['model_triangles']
PALETTE = {'carapace':[98,31,33], 'ridge':[124,48,48], 'horn':[56,22,25],
           'steel':[133,163,172], 'steel_dark':[67,91,103], 'bone':[171,166,144],
           'frame':[47,48,46], 'cloth':[40,61,59], 'black':[24,28,28],
           'lens':[41,129,24], 'recess':[11,18,15]}

def sha(data): return hashlib.sha256(data).hexdigest()
def encode(obj): return (json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def png(im):
    buf=io.BytesIO();im.save(buf,format='PNG');return buf.getvalue()
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w138:apostate:'+s))


def source_meshes():
    """Inspect Apostate's LOCAL basis; do not inherit Beloved's axis transform.

    Mesh vertices already occupy W30's corrected source frame. FBX model nodes
    have an exporter world translation/centimeter scale; applying them again
    would offset the weapon. Validate the saved W30 bounds in BOTH frames.
    One included two-triangle Glow locator has no connected material; UV is optional.
    """
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    assert sha((RAW/'Apostate.fbx').read_bytes())==meta['source_files']['Apostate/Apostate.fbx']
    roots=H['parse_fbx'](RAW/'Apostate.fbx')
    objects=next(n[2] for n in roots if n[0]=='Objects')
    by={n[1][0]:n for n in objects if n[1]}
    links=[n[1][1:] for r in roots if r[0]=='Connections' for n in r[2] if n[1][0]=='OO']
    meshes=[];local=[]
    for g in objects:
        if g[0]!='Geometry':continue
        mid=next(p for c,p in links if c==g[1][0] and by[p][0]=='Model')
        model=by[mid];name=model[1][1].split('\x00')[0]
        if name not in meta['source_objects']:continue
        props={p[1][0]:p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        np.testing.assert_allclose(props['Lcl Rotation'],[-90,0,0],atol=.0001)
        np.testing.assert_allclose(props['Lcl Translation'],[-53.21094512939453,0,-79.95132446289062],atol=.00001)
        assert props['Lcl Scaling']==[100,100,100]
        cs={c[0]:c for c in g[2]};raw=np.array(cs['Vertices'][1][0]).reshape(-1,3)
        local.append(raw);v=raw[:,[0,2,1]]*meta['scale']+meta['anchor']
        indices=cs['PolygonVertexIndex'][1][0]
        ul=next((c for c in g[2] if c[0]=='LayerElementUV' and c[1][0]==0),None)
        if ul:
            vals={c[0]:c[1][0] for c in ul[2]}
            assert vals['MappingInformationType']=='ByPolygonVertex' and vals['ReferenceInformationType']=='IndexToDirect'
            uv=np.array(vals['UV']).reshape(-1,2)[np.array(vals['UVIndex'])];uv[:,1]=1-uv[:,1]
        else:
            assert name=='Apostate.03.004';uv=np.zeros((len(indices),2))
        faces=[];uvs=[];poly=[];puv=[]
        for k,i in enumerate(indices):
            poly.append(i if i>=0 else -i-1);puv.append(uv[k])
            if i<0:
                for j in range(1,len(poly)-1):
                    ix=[0,j,j+1];faces.append(np.array(poly)[ix]);uvs.append(np.array(puv)[ix])
                poly=[];puv=[]
        assert not poly
        mat=next((by[c][1][1].split('\x00')[0] for c,p in links if p==mid and by[c][0]=='Material'),'Glow')
        meshes.append(dict(name=name,vertices=v,faces=np.array(faces),uv=np.array(uvs),material=mat))
    pts=np.concatenate([m['vertices'] for m in meshes]);raw=np.concatenate(local)
    np.testing.assert_allclose([raw.min(0),raw.max(0)],meta['source_bounds'],atol=1e-6)
    np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-5)
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==37378
    return meshes,meta


def source_triangles(meshes):
    tex={k:np.array(Image.open(RAW/v).convert('RGBA')) for k,v in
         {'Sight':'Sight_Diffuse.dds','Barrel':'Barrel_Diffuse.dds','Glass':'990cce80.PNG'}.items()}
    tex['Glow']=np.array([[[45,110,30,255]]],dtype=np.uint8)
    result=[]
    for m in meshes:
        for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]);norm=np.linalg.norm(n)
            if norm>1e-10:result.append((ps,uv,tex[m['material']],n/norm))
    return result


def semantic_geometry():
    specs=[]
    def box(group,name,c,size,mat,motif='panel',angles=(0,0,0)):
        c=np.array(c,float);s=np.array(size,float)
        e=dict(name=group+'/'+name,**{'from':(c-s/2).round(6).tolist(),'to':(c+s/2).round(6).tolist()})
        if any(angles):e['rotation']=dict(origin=c.round(6).tolist(),**dict(zip('xyz',angles)))
        specs.append(dict(group=group,material=mat,motif=motif,geometry=e))
    def beam(group,name,a,b,width,depth,mat,motif='panel'):
        a=np.array(a,float);b=np.array(b,float);v=b-a
        assert abs(v[0])<1e-7
        box(group,name,(a+b)/2,[width,np.linalg.norm(v),depth],mat,motif,
            (round(math.degrees(math.atan2(v[2],v[1])),6),0,0))
    def ring(group,name,y,z0,z1,r,thick,mat,motif='rim'):
        for i in range(8):
            a=i*45;t=math.radians(a)
            box(group,f'{name}-{i}',[8-r*math.sin(t),y+r*math.cos(t),(z0+z1)/2],
                [2*r*math.tan(math.pi/8)+.018,thick,z1-z0],mat,motif,(0,0,a))

    # Receiver and mechanical action occupy the unchanged native hand frame.
    box('receiver','core',[8,9.74,6.20],[1.20,1.12,5.44],'carapace','receiver')
    box('receiver','action',[8,10.13,6.40],[1.23,.47,4.88],'frame','action')
    box('receiver','top-rail',[8,10.54,5.88],[.87,.23,4.30],'black','rail')
    box('receiver','pale-lower-frame',[8,9.05,6.10],[1.02,.48,5.13],'bone','bone')
    box('receiver','front-step',[8,9.22,3.65],[1.35,.70,.68],'carapace','chitin')
    box('receiver','bolt-slide',[8.65,10.08,6.35],[.18,.38,2.48],'steel_dark','bolt')
    box('receiver','bolt-edge',[8.75,10.30,6.35],[.14,.13,2.45],'steel','bolt')
    box('receiver','charge-stem',[8.77,10.01,7.63],[.54,.21,.26],'steel_dark')
    box('receiver','charge-knob',[9.02,9.98,7.63],[.16,.36,.48],'black','dial')

    # Skeleton stock / pale load-bearing frame, with a real thumbhole.
    box('stock','red-comb',[8,10.04,11.23],[1.02,.66,4.08],'carapace','stock')
    box('stock','comb-lower',[8,9.65,11.93],[1.03,.22,2.62],'bone','bone')
    beam('stock','heel-frame',[8,7.05,9.12],[8,6.99,13.19],1.06,.43,'bone','bone')
    box('stock','butt-frame',[8,8.45,13.19],[1.09,2.94,.37],'bone','bone')
    box('stock','butt-pad',[8,8.47,13.42],[1.13,3.10,.176805],'black','pad')
    beam('stock','rear-web',[8,7.35,11.12],[8,8.95,12.93],1.04,.75,'bone','bone')
    box('stock','mid-web',[8,7.42,10.13],[1.03,.68,2.38],'frame','stock')
    beam('stock','thumbhole-return',[8,9.28,9.00],[8,8.20,10.38],1.01,.45,'bone','bone')
    box('stock','heel-strap',[8,7.29,9.37],[1.15,.78,.30],'cloth','wrap',(-13,0,0))
    box('stock','comb-strap',[8,9.96,11.18],[1.15,.84,.40],'cloth','wrap',(26,0,0))
    beam('stock','side-binding', [8.57,10.21,10.60],[8.57,8.83,11.67],.14,.36,'cloth','wrap')

    # Solid grip raked to match the raw wrist, without recentering the full model.
    beam('grip','core',[8,9.10,7.86],[8,7.12,8.40],.99,1.12,'bone','grip')
    beam('grip','backstrap',[8,8.94,8.42],[8,7.16,8.96],1.04,.24,'frame','grip')
    box('grip','heel',[8,6.95,8.60],[1.08,.35860,1.22],'bone','bone')
    beam('grip','binding',[8,8.25,8.65],[8,7.15,8.98],1.12,.31,'cloth','wrap')
    # Trigger bow is a true through aperture, not black texture on a side sheet.
    beam('trigger','front-bow',[8,8.94,5.78],[8,7.91,6.02],.40,.17,'bone','bone')
    beam('trigger','bottom-bow',[8,7.91,6.02],[8,7.91,7.67],.40,.17,'bone','bone')
    beam('trigger','rear-bow',[8,7.91,7.67],[8,8.67,7.80],.40,.17,'bone','bone')
    beam('trigger','blade',[8,8.94,6.94],[8,8.38,6.72],.20,.17,'frame')

    # Broad curved black underbody magazine/fin. Full-only: no new reload split.
    box('magazine','socket',[8,8.82,3.27],[1.06,.64,4.26],'black','magazine')
    box('magazine','main',[8,8.11,3.11],[1.02,.98,3.85],'black','magazine')
    beam('magazine','toe',[8,8.04,1.40],[8,7.54,.05],1.01,.38,'black','magazine')
    beam('magazine','heel',[8,7.69,3.92],[8,7.29,5.08],1.01,.44,'black','magazine')
    box('magazine','base',[8,7.49,2.84],[1.03,.30,2.72],'frame','magazine')

    # Long filled carapace fore-end with substantial faceted shoulder volumes.
    box('foreend','filled-core',[8,9.92,-1.35],[1.28,1.12,10.45],'carapace','chitin')
    box('foreend','crown',[8,10.52,-1.32],[.94,.34,10.08],'ridge','chitin')
    box('foreend','lower-spine',[8,9.32,-1.28],[.97,.34,10.19],'carapace','chitin')
    for s in (-1,1):
        box('foreend',f'upper-shoulder-{s}',[8+s*.56,10.36,-1.32],[.39,.48,10.06],
            'carapace','chitin',(0,0,s*32))
        box('foreend',f'lower-shoulder-{s}',[8+s*.55,9.48,-1.32],[.37,.44,10.05],
            'carapace','chitin',(0,0,-s*31))
    # Three silver zigzag braces each side follow the visible mechanical cage.
    # They are actual raised struts; shallow scar relief remains in face UVs.
    for s in (-1,1):
        for i,z in enumerate((-5.56,-3.28,-1.00)):
            x=8+s*.76
            beam('braces',f'upper-chevron-{s}-{i}',[x,10.30,z-.62],[x,9.95,z+.56],.16,.16,'steel','metal')
            beam('braces',f'lower-chevron-{s}-{i}',[x,9.60,z-.62],[x,9.95,z+.56],.16,.16,'steel','metal')
    # Two full-section cloth collars around the filled carapace, not alpha wraps.
    for i,z in enumerate((-4.88,-.87)):
        box('bindings',f'top-{i}',[8,10.76,z],[1.67,.22,.53],'cloth','wrap')
        box('bindings',f'bottom-{i}',[8,9.12,z],[1.27,.17,.49],'cloth','wrap')
        for s in (-1,1):
            box('bindings',f'flank-{i}-{s}',[8+s*.78,9.97,z],[.18,1.65,.49],'cloth','wrap',(-8,0,0))

    # Exposed silver barrel and dark wrapped muzzle. Bore runs through eight
    # opaque staves into a recessed physical backstop, no alpha or plane cap.
    box('barrel','core',[8,9.94,-8.48],[.66,.66,3.85],'steel_dark','fluted')
    box('barrel','top-flute',[8,10.30,-8.48],[.48,.16,3.85],'steel','fluted')
    box('barrel','lower-flute',[8,9.60,-8.48],[.48,.16,3.85],'steel','fluted')
    ring('muzzle','wrapped-staves',9.96,-15.491597,-10.35,.49,.24,'cloth','wrap')
    ring('muzzle','metal-collar',9.96,-10.45,-10.20,.49,.19,'steel_dark','rim')
    box('muzzle','bore-stop',[8,9.96,-10.44],[.69,.69,.08],'recess','recess')

    # Optic is a filled red housing over two feet; the green lens is recessed.
    box('optic','housing',[8,11.54,4.15],[1.06,.98,4.34],'carapace','chitin')
    box('optic','crown',[8,12.08,3.95],[.74,.29,4.49],'ridge','chitin')
    for s in (-1,1):
        box('optic',f'shoulder-{s}',[8+s*.48,11.94,4.04],[.36,.39,4.54],'carapace','chitin',(0,0,s*35))
    for i,z in enumerate((2.62,5.35)):
        box('optic',f'mount-{i}',[8,10.91,z],[.72,.66,.49],'black','metal')
    ring('optic','objective-rim',11.56,1.36,2.10,.49,.20,'horn','chitin')
    box('optic','green-lens',[8,11.56,1.89],[.76,.76,.20],'lens','lens')
    box('optic','rear-eyepiece',[8,11.53,6.38],[.80,.77,.31],'black','metal')
    box('optic','dial-base',[8.62,11.49,4.72],[.25,.72,.72],'steel_dark','dial')
    box('optic','dial-cap',[8.81,11.49,4.72],[.16,.55,.55],'frame','dial')

    # Iconic thorns: deliberate horn roots with tapered secondary tips, not a
    # source triangle conversion. Widely spaced silhouette accents are enough.
    horns=[('foreend',-6.38,10.45,-.92,.54),('foreend',-5.80,9.39,-.72,-.55),
           ('foreend',-3.12,10.66,-.63,.42),('foreend',.18,10.57,-.91,.57),
           ('foreend',2.69,10.38,-.68,.49),('optic',1.69,12.03,-1.06,.57),
           ('optic',3.73,12.20,-.70,.43),('optic',5.67,12.13,.69,.44)]
    for i,(group,z,y,dz,dy) in enumerate(horns):
        x=8+(.14 if i%2 else -.17)
        beam('thorns',f'{group}-root-{i}',[x,y,z],[x,y+dy*.70,z+dz*.70],.25,.31,'carapace','chitin')
        beam('thorns',f'{group}-tip-{i}',[x,y+dy*.53,z+dz*.53],[x,y+dy,z+dz],.12,.15,'horn','horn')
    return specs


def make_design(meshes,meta):
    specs=semantic_geometry()
    inputs=[BASE,BB,HELPER,BATCH,ASSET+'textures/item/weapon/w30/apostate.png']
    raw=[RAW/'Apostate.fbx',RAW/'Sight_Diffuse.dds',RAW/'Barrel_Diffuse.dds',RAW/'990cce80.PNG',PHOTO]
    return dict(id='apostate',revision='W138',method='hand-authored meaningful opaque filled cuboids and face UV; full only',
        baseline_provenance=dict(name='w138-apostate',baseline_sha256='61d9f956c2c0b096efad4a646a84d6f7b308429d08ab2245e1e621419bc89f2f',head='bfd4b4573fd8651bf1ea850bf829622ccce5c3c2',owned_paths_initially_absent=True),
        source=meta,source_component_tessellation=False,source_voxel_conversion=False,parts={'full':specs},
        groups=dict(collections.Counter(s['group'] for s in specs)),palette=PALETTE,
        identity=['red thorned Hive carapace over long sniper fore-end and optic',
                  'silver exposed fluted barrel and lateral chevron braces',
                  'two dark teal cloth bindings and wrapped cylindrical muzzle',
                  'recessed green optic and ivory/charcoal skeleton stock'],
        frame=dict(scale=meta['scale'],anchor=meta['anchor'],muzzle='-Z',grip=[8,8.2,8.1],
                   mapping='native = [raw.X, raw.Z, raw.Y] * W30.scale + W30.anchor; local pre-node coordinates',
                   source_axis=meta['source_axis'],display='canonical byte-equivalent JSON value',recentered=False),
        source_landmarks={m['name']:[m['vertices'].min(0).round(7).tolist(),m['vertices'].max(0).round(7).tolist()] for m in meshes},
        required_air_probes={'trigger':[8,8.36,6.22],'thumbhole':[8,9.02,10.20],'muzzle':[8,9.96,-14.8]},
        required_solid_probes={'foreend_core':[8,9.92,-3],'receiver_core':[8,9.74,6],
                               'grip_contact':[8,8.2,8.1],'stock_heel':[8,7.05,11.5],
                               'optic_core':[8,11.54,4.04]},
        reload_policy='full only; no split/pivot/registry/gameplay/audio/timing edits',
        uv_policy='1024 opaque atlas; separate aspect-correct face islands, 2px extruded gutters; authored chitin facets, cloth weave and bone scars',
        input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},
        raw_input_sha256={str(p):sha(p.read_bytes()) for p in raw},
        limitations=['CPU inspection only; native parser/pack loading and live first/third-person, ADS, reload, audio, 10-20 display checks pending master.',
                     'Angular semantic reinterpretation; organic curves, tiny barbs and cloth folds are simplified.',
                     'Authored default colors and static relief; no source shader, PBR, emissive lighting or exact dye reconstruction.',
                     'Single appearance photograph limits reverse-side paint evidence; reverse UV faces are independently allocated.'])


def paint_tile(spec,face,w,h):
    u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
    pts=vertices(spec['geometry'])[list(FACES[face])]
    p=pts[0]+u[:,:,None]*(pts[1]-pts[0])+v[:,:,None]*(pts[3]-pts[0])
    role=spec['material'];motif=spec['motif'];base=np.array(PALETTE[role],float)
    rgb=np.broadcast_to(base,(h,w,3)).copy()
    rgb*=(.95+.065*np.exp(-((v-.28)/.4)**2))[:,:,None]
    edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<1]*=.77
    rgb[(edge>=1)&(edge<2)]*=1.08
    y,z=p[:,:,1],p[:,:,2];side=face in ('east','west')
    if motif in ('chitin','horn'):
        # Broad hand-designed angular lamellae. Shared world coordinates keep
        # the relief coherent across adjacent shoulders, never rip projection.
        phase=np.mod(z*1.07+np.abs(y-9.9)*1.65,.98)
        facets=(phase>.15)&(phase<.52)
        rgb[facets]*=1.14
        scars=(phase<.035)&(np.mod(y*2.1-z*.13,1)>.16)
        rgb[scars]*=.47
        branch=(abs(np.mod(z*1.07-y*2.2,2)-.9)<.032)&(phase<.48)
        rgb[branch]*=.66
        if side:rgb[(phase>.045)&(phase<.075)]*=1.35
    if motif=='wrap':
        # Cloth ribs, crossed fine weave and overlapping diagonal turns.
        zz=p[:,:,2];xx=p[:,:,0]
        rib=np.mod((zz+xx*.32)*5.2+v*.4,1)
        rgb[rib<.11]*=.70;rgb[(rib>=.11)&(rib<.18)]*=1.10
        weave=((np.floor(u*w/2)+np.floor(v*h/2))%2)==0
        rgb[weave]*=.96
        seam=abs(np.mod(zz*.68+y*.25,1)-.5)<.035
        rgb[seam]*=.66
    if motif in ('bone','grip','stock'):
        # Pale cracked polymer from photo; sparse large cracks and dark heel.
        seam=abs(np.mod(z*.82+y*.62,1.9)-.9)<.023
        rgb[seam]*=.63
        if motif=='grip':
            ribs=(np.mod(y*8,1)<.14)&(u>.14)&(u<.9)
            rgb[ribs]*=.81
        if side and motif=='bone':
            speck=(abs(np.mod(z*2.6,1)-.4)<.06)&(abs(np.mod(y*3.3,1)-.5)<.07)
            rgb[speck]*=.58
    if motif in ('receiver','action','bolt','metal','fluted','magazine'):
        if side:
            line=(abs(v-.17)<.017)|(abs(v-.80)<.017)
            rgb[line&(u>.06)&(u<.94)]*=.64
        if motif in ('fluted','bolt'):
            stripe=(np.mod(v*5,1)<.12)&(u>.03)&(u<.96)
            rgb[stripe]*=.68
        if motif=='receiver' and side:
            port=(u>.18)&(u<.78)&(v>.33)&(v<.62)
            rgb[port]*=.52
    if motif=='dial' and side:
        r=np.hypot((u-.5)*2,(v-.5)*2)
        rgb[(r>.64)&(r<.77)]*=1.7;rgb[(r>.40)&(r<.49)]*=.50
    if motif=='pad':rgb[np.mod(y*6,1)<.22]*=.61
    if motif=='lens' and face in ('north','south'):
        r=np.hypot((p[:,:,0]-8)/.40,(y-11.56)/.40)
        glow=np.exp(-((r/.72)**2))
        rgb[:]=[9,27,12];rgb+=glow[:,:,None]*[49,156,22]
        rgb+=np.exp(-(((p[:,:,0]-7.86)/.07)**2+((y-11.75)/.06)**2))[:,:,None]*[42,55,30]
    return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,dtype='uint8')]))


def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(19,25,25,255));requests=[];uvmap={};islands=[]
    for s in d['parts']['full']:
        for face,ix in FACES.items():
            ps=vertices(s['geometry'])[list(ix)]
            # Allocate on physical size. Continuous long fore-end islands are
            # never a mosaic of projected source components.
            density=26
            w=max(5,math.ceil(np.linalg.norm(ps[1]-ps[0])*density))
            h=max(5,math.ceil(np.linalg.norm(ps[3]-ps[0])*density))
            requests.append((s,face,w,h))
    requests.sort(key=lambda t:(-t[3],-t[2],t[0]['geometry']['name'],t[1]))
    x=y=2;row=0
    for s,f,w,h in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('1024 atlas overflow at '+s['geometry']['name'])
        tile=paint_tile(s,f,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(tile),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvmap[(s['geometry']['name'],f)]=[q/64 for q in (x,y,x+w,y+h)]
        islands.append(dict(element=s['geometry']['name'],face=f,pixels=[x,y,x+w,y+h]))
        x+=w+4;row=max(row,h)
    es=[]
    for s in d['parts']['full']:
        e=copy.deepcopy(s['geometry']);e['faces']={f:dict(texture='#0',uv=uvmap[(e['name'],f)]) for f in FACES};es.append(e)
    d['atlas']=dict(size=[EDGE,EDGE],gutter=2,texels_per_unit=26,islands=islands,used_height=y+row+2,
                    used_texels=sum((t[2]-t[0])*(t[3]-t[1]) for i in islands for t in [i['pixels']]))
    assert len(es)<=1000
    return atlas,dict(credit='W138 Apostate | authored opaque volumes / face UV | CPU review; native pending',
        textures={'0':'destiny:item/weapon/w123/apostate','particle':'destiny:item/weapon/w123/apostate'},
        elements=es,display=json.loads((ROOT/BASE).read_bytes())['display'])


def inspection(d,model,atlas):
    es=[];groups=[]
    for group in d['groups']:
        children=[]
        for e in model['elements']:
            if e['name'].split('/')[0]!=group:continue
            b=copy.deepcopy(e);r=b.pop('rotation',{})
            b.update(type='cube',uuid=uid(e['name']),origin=r.get('origin',[8,8,8]),
                     rotation=[r.get(a,0) for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[q*64 for q in f['uv']]
            es.append(b);children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Apostate W138 semantic solids / CPU inspection',
        resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,display=model['display'],
        textures=[dict(name='apostate.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
                       source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
        destiny_w138=dict(fullOnly=True,nativeAccepted=False,rotationOrder='RzRyRx',sourceScale=d['source']['scale'],sourceAnchor=d['source']['anchor']))


def comparison(d,meshes,atlas,model):
    w,h=880,310;sheet=Image.new('RGB',(2640,1770),'#151c25');dr=ImageDraw.Draw(sheet)
    def label(x,y,text,size=20):dr.text((x,y),text,fill='#e5edf1',font_size=size)
    label(20,14,'APOSTATE / W138 / SEMANTIC SOLIDS + AUTHORED FACE UV / CPU INSPECTION',28)
    photo=Image.open(PHOTO).convert('RGB').crop((0,230,1920,750));photo.thumbnail((1550,360));sheet.paste(photo,(20,60))
    for i,text in enumerate([f'{len(model["elements"])} opaque filled cuboids / full only',
        'Red chitin + silver cage + teal wraps + green optic',
        '1024 atlas / explicit UV for every face / no alpha',
        'Original scale, anchor, axis and display retained',
        'Native pack, holding, ADS and reload: pending master']):label(1610,75+i*45,text,20)
    label(20,395,'RAW FBX / 37,378 triangles / undyed DDS')
    old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/apostate.png'))
    label(w+20,395,f'CANONICAL / {len(old["elements"])} old cuboids')
    label(w*2+20,395,f'W138 / {len(model["elements"])} authored cuboids')
    triangles=[source_triangles(meshes),model_triangles({'old':old},oldtex),model_triangles({'new':model},atlas)]
    pts=np.concatenate([m['vertices'] for m in meshes])
    cameras=[('SIDE / native -Z muzzle',[1,0,0]),('FRONT OBLIQUE / thickness',[1,.52,-.62]),('REAR OBLIQUE / reverse faces',[-1,.40,.62])]
    for row,(name,cam) in enumerate(cameras):
        extent=frame(pts,cam,w,h)
        for col,tris in enumerate(triangles):
            im,_=render(tris,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,435+row*h))
            label(col*w+15,443+row*h,name,17)
    detailgroups=[('optic',[.38,.13,-1]),('muzzle',[.30,.16,-1]),('stock',[1,.32,.55]),('foreend',[-1,.48,-.50])]
    for col,(group,cam) in enumerate(detailgroups):
        names={s['geometry']['name'] for s in d['parts']['full'] if s['group']==group}
        if group=='foreend':names|={s['geometry']['name'] for s in d['parts']['full'] if s['group'] in ('bindings','braces','thorns') and s['geometry']['name'].startswith(('bindings/','braces/','thorns/foreend'))}
        es=[e for e in model['elements'] if e['name'] in names];p=np.concatenate([vertices(e) for e in es])
        im,_=render(model_triangles({'detail':dict(elements=es)},atlas),cam,frame(p,cam,660,300),(660,300))
        sheet.paste(im,(col*660,1380));label(col*660+15,1390,group.upper()+' / real depth',18)
    label(20,1705,'Matched orthographic camera and scale within each full-model row. Raw texture is undyed; palette follows the source appearance photograph.',19)
    label(20,1735,'Offline art evidence only. Master owns shared registry/HUD and native first/third person, ADS, reload/audio, and 10-20 display QA.',19)
    return png(sheet)


def review_text(d,n):
    return f'''# Apostate W138 semantic weapon remodel

Reference inspected: `/tmp/destiny-weapons-w31/references/apostate.jpg`, original Apostate FBX and raw Sight/Barrel DDS, canonical W30 model and W30 metadata. Ace87/Izanagi79 reference study informed continuous functional volumes and individual face UVs. No source polygons, islands or voxels were converted into the authored geometry.

The assembly is **{n} opaque filled cuboids**, {n*6} explicit faces, zero triangle adapters or alpha elements. Full-only representation; no body/magazine/reload split is introduced. Broad filled red forearm and optic housings retain cross-section from front/rear obliques. Raised silver chevron braces, full-depth cloth collars, eight authored paired root/tip thorns, pale grip/stock beams and black curved underbody magazine retain Apostate's identity. The stock thumbhole, trigger bow, recessed objective lens and deep muzzle throat use actual geometry. The 1,000-element cap is a ceiling; this starts in the requested 80-120 range.

A 1024 square fully opaque RGBA atlas uses independent aspect-correct face islands at 26 texels per unit, with 2px edge-extruded gutters. Red chitin facets and branching scars, silver flutes, cloth weave, pale stock scars, dial concentric grooves and green lens depth are authored face paint. No full-rip projection, random noise, invented letters, alpha shells or side silhouette plates. Organic microfolds and tapering points are deliberately stylized. The source reference supplies color/material evidence; this is static shading, without PBR or runtime emission.

Raw-basis inspection is explicit: FBX local bounds match W30 source bounds; mapping `[raw X, raw Z, raw Y] * 17.24631120450977 + [8,8,8]` reproduces the W30 native bounds within 1e-5. The FBX nodes have export translation `[-53.21094512939453, ~0, -79.95132446289062]`, rotation about X -90 degrees and scale 100; these are not blindly applied a second time. A material-less two-triangle Glow locator with valid UVs is handled in the reference reader, not copied into the remodel. Canonical full display values are copied exactly. Muzzle -Z, original grip contact region, scale and anchor are unchanged. Tiny silhouette deviations are recorded in manifest bounds; no fitted/recentered scale is applied.

`comparison.png` shows the original appearance, raw undyed FBX, canonical model, side/front/rear oblique remodels at matched framing, and optic/muzzle/stock/forearm depth views. `inspection.bbmodel` contains exactly the emitted geometry and embedded atlas in semantic groups. Both are CPU artifacts; no DCC or game was opened.

Baseline provenance is frozen from the supplied dirty-seeded `w138-apostate` worktree. Targeted tests operate from repository-relative paths and permit the main checkout after hash-checked integration; they do not require main to have this worker's private `.git/worktree-batch.json`. Main's shared registry, HUD, reload, gameplay and audio remain outside ownership. Native resource-pack loading/rotation parsing, first/third-person holding, ADS, reload/audio and 10-20 displayed weapons remain **pending master**; CPU images cannot certify those behaviors.
'''


def generate(include_comparison=True):
    meshes,meta=source_meshes();d=make_design(meshes,meta);atlas,model=compile_model(d)
    n=len(model['elements']);ps=np.concatenate([vertices(e) for e in model['elements']])
    outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),
             ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,n).encode()}
    if include_comparison:outputs[ART+'comparison.png']=comparison(d,meshes,atlas,model)
    manifest=dict(id='apostate',revision='W138',counts={'full':n},assembled_elements=n,opaque_cuboids=n,
        max_assembled_elements=1000,emitted_faces=n*6,triangle_adapter_elements=0,alpha_elements=0,alpha_body_plates=0,
        full_only=True,texture_size=[EDGE,EDGE],groups=d['groups'],canonical_display_exact=True,
        actual_bounds=[ps.min(0).round(7).tolist(),ps.max(0).round(7).tolist()],source_bounds=meta['model_bounds'],
        source_triangles=meta['source_triangles'],source_scale=meta['scale'],source_anchor=meta['anchor'],
        baseline_provenance=d['baseline_provenance'],generator_sha256=sha(Path(__file__).read_bytes()),
        input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())},native_accepted=False,
        validation={'cpu':'targeted test + deterministic --verify required','native':'pending master'},limitations=d['limitations'])
    outputs[ART+'manifest.json']=encode(manifest)
    return outputs


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    outputs=generate();batch=json.loads((ROOT/BATCH).read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w138-apostate'))
    assert len(owned)==10 and set(outputs)<=owned
    assert sum(len(b) for b in outputs.values())<25*1024*1024
    for rel,data in outputs.items():
        path=ROOT/rel
        if a.verify:assert path.is_file() and path.read_bytes()==data,'Regeneration mismatch: '+rel
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    m=json.loads(outputs[ART+'manifest.json'])
    print(('Verified' if a.verify else 'Generated')+f' {len(outputs)} owned artifacts; {m["counts"]}; {m["emitted_faces"]} faces; native pending master')

if __name__=='__main__':main()
