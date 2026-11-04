#!/usr/bin/env python3
"""W126 Recluse: authored semantic solid volumes and independently packed face UVs.

No DCC, subprocess, network, item-graph or historical-asset writes. Run using the
bundled numpy/Pillow Python. --verify regenerates deterministically in memory.
"""
import argparse
import base64
import collections
import hashlib
import importlib.util
import io
import itertools
import json
import math
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ART = Path('art/weapons/w123/the_recluse')
ASSETS = Path('src/main/resources/assets/destiny')
MODEL = ASSETS / 'models/weapon_surface_w123'
TEXTURE = ASSETS / 'textures/item/weapon/w123/the_recluse.png'
CANON = ASSETS / 'models/weapon/submachine_gun/the_recluse.json'
BB = Path('art/blockbench/weapons/w30/the_recluse.bbmodel')
CACHE = Path('/tmp/destiny-weapons-w30/raw/the_recluse/extracted')
REFERENCE = Path('/tmp/destiny-weapons-w31/references/the_recluse.jpg')
W31_SCREEN = Path('/tmp/destiny-weapons-w31/renders/the_recluse-after.png')
MAX_ASSEMBLED_ELEMENTS = 1000
FACES = ('north', 'south', 'west', 'east', 'up', 'down')
CORNERS = {'north':(6,2,0,4), 'south':(3,7,5,1), 'west':(2,3,1,0),
           'east':(7,6,4,5), 'up':(2,6,7,3), 'down':(1,5,4,0)}
NORMALS = {'north':(0,0,-1), 'south':(0,0,1), 'west':(-1,0,0),
           'east':(1,0,0), 'up':(0,1,0), 'down':(0,-1,0)}


def encode(j):
    return (json.dumps(j, indent=2, allow_nan=False) + '\n').encode()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def png(im):
    s = io.BytesIO()
    im.save(s, 'PNG', compress_level=9)
    return s.getvalue()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def rotation(e):
    r = e.get('rotation', {})
    result = np.eye(3)
    for axis in 'xyz':
        a = math.radians(r.get(axis, r.get('angle', 0) if r.get('axis') == axis else 0))
        c, s = math.cos(a), math.sin(a)
        result = np.array({'x':[[1,0,0],[0,c,-s],[0,s,c]],
                           'y':[[c,0,s],[0,1,0],[-s,0,c]],
                           'z':[[c,-s,0],[s,c,0],[0,0,1]]}[axis]) @ result
    return result


def vertices(e):
    v = np.array(list(itertools.product(*zip(e['from'], e['to']))))
    o = np.array(e.get('rotation', {}).get('origin', [0,0,0]))
    return (v-o) @ rotation(e).T + o


class LegacyPaint:
    """Backproject the accepted W31 default-painted coarse atlas onto new faces."""
    def __init__(self, canonical):
        path=ASSETS/'textures'/(canonical['textures']['0'].split(':')[1]+'.png')
        self.path=path
        self.image=Image.open(ROOT/path).convert('RGBA').filter(ImageFilter.MedianFilter(3))
        self.tex=np.array(self.image)
        self.faces={}
        for face in FACES:
            ids=CORNERS[face];rows=[]
            for e in canonical['elements']:
                if face not in e['faces']:continue
                q=vertices(e)[list(ids)]
                rows.append((q,e['faces'][face]['uv']))
            self.faces[face]=rows

    def sample(self,points,normal,mesh=None):
        points=np.array(points);shape=points.shape[:-1];p=points.reshape(-1,3)
        axis=int(np.argmax(abs(normal)))
        face={(0,False):'west',(0,True):'east',(1,False):'down',(1,True):'up',
              (2,False):'north',(2,True):'south'}[axis,normal[axis]>=0]
        best=np.full(len(p),np.inf);uv=np.zeros((len(p),2))
        for q,rect in self.faces[face]:
            origin=q[0];u=q[1]-origin;v=q[3]-origin
            su=np.clip((p-origin)@u/max(float(u@u),1e-12),0,1)
            sv=np.clip((p-origin)@v/max(float(v@v),1e-12),0,1)
            nearest=origin+su[:,None]*u+sv[:,None]*v
            dist=np.sum((nearest-p)**2,axis=1)
            use=dist<best
            best[use]=dist[use]
            uv[use,0]=rect[0]+su[use]*(rect[2]-rect[0])
            uv[use,1]=rect[1]+sv[use]*(rect[3]-rect[1])
        tx=np.clip((uv[:,0]/16*self.tex.shape[1]).astype(int),0,self.tex.shape[1]-1)
        ty=np.clip((uv[:,1]/16*self.tex.shape[0]).astype(int),0,self.tex.shape[0]-1)
        color=self.tex[ty,tx].copy();color[:,3]=255
        # Preserve the default white/burgundy/black fields. W31's albedo bake
        # lacks the reference's metal response; tidy its overly bright red and
        # neutral rubber without changing decal placement or adding raw diffuse.
        red=(color[:,0]>color[:,1]*1.45)&(color[:,0]>color[:,2]*1.35)
        color[red,:3]=(color[red,:3]*[.64,.68,.70]).astype(np.uint8)
        if mesh=='Mesh_0007.rip':
            neutral=~red
            color[neutral,:3]=(color[neutral,:3]*.32).astype(np.uint8)
        barrel=(p[:,2]<3.35)&(p[:,1]>10.7)
        color[barrel,:3]=(color[barrel,:3]*.42).astype(np.uint8)
        return color.reshape(shape+(4,))

    def sample_normals(self,points,normals,mesh=None):
        axes=np.argmax(abs(normals),axis=1);colors=np.empty((len(points),4),np.uint8)
        for axis in range(3):
            for sign in (-1,1):
                use=(axes==axis)&(normals[:,axis]*sign>=0)
                n=np.zeros(3);n[axis]=sign
                colors[use]=self.sample(points[use],n,mesh)
        return colors


class SourceUV:
    """Inert FBX UV projection, scoped to the same connected source component.

    DDS diffuse/occlusion/normal detail is sampled in its original UV frame.
    Directional maps transfer those authored features to the existing cap/wall
    UVs; they never emit geometry or determine alpha. No shader is executed.
    """
    DENSITY = 96

    def __init__(self, parser, meshes):
        objects = next(n[2] for n in parser.parse_fbx(CACHE/'Recluse.fbx') if n[0]=='Objects')
        geometries = {n[1][0]:n for n in objects if n[0]=='Geometry'}
        self.meshes = {m['name']:m for m in meshes}
        self.uvs = {}
        for m in meshes:
            layer = next(c for c in geometries[m['geometryId']][2] if c[0]=='LayerElementUV')
            fields = {c[0]:c[1][0] for c in layer[2]}
            assert fields['MappingInformationType']=='ByPolygonVertex'
            assert fields['ReferenceInformationType']=='IndexToDirect'
            self.uvs[m['name']] = np.array(fields['UV']).reshape(-1,2)[np.array(fields['UVIndex'])].reshape(-1,3,2)
        self.textures = {}
        for material in ('RecluseBarrel','RecluseStock'):
            # Remove isolated DDS pixel noise before transfer, not after decal
            # composition. The independent W31 bird/color mask is never blurred.
            diffuse = Image.open(CACHE/(material+'_Diffuse.dds')).convert('RGB').filter(ImageFilter.MedianFilter(3))
            ao = Image.open(CACHE/(material+'_Gstack.dds')).convert('RGBA').getchannel('R')
            normal = Image.open(CACHE/(material+'_Normal.dds')).convert('RGB')
            luma=np.array(diffuse)@np.array([.2126,.7152,.0722])
            self.textures[material] = np.dstack((luma,np.array(ao),
                                                np.array(normal)[:,:,:2])).astype(np.float32)/255
        self.cache = {}

    @staticmethod
    def bilinear(tex, xy):
        xy=np.asarray(xy); x=xy[...,0];y=xy[...,1]
        x=np.clip(x,0,tex.shape[1]-1);y=np.clip(y,0,tex.shape[0]-1)
        a=x.astype(int);b=y.astype(int);c=np.minimum(a+1,tex.shape[1]-1);d=np.minimum(b+1,tex.shape[0]-1)
        u=(x-a)[...,None];v=(y-b)[...,None]
        return (tex[b,a]*(1-u)+tex[b,c]*u)*(1-v)+(tex[d,a]*(1-u)+tex[d,c]*u)*v

    def projection(self, mesh, component, axis, positive):
        key=(mesh,component,axis,positive)
        if key in self.cache:return self.cache[key]
        m=self.meshes[mesh];fs=np.array(m['faces']);selected=m['components'][component]
        indices={tuple(f):i for i,f in enumerate(fs.tolist())}
        ids=[indices[tuple(f)] for f in selected]
        tri=np.array(m['vertices'])[np.array(selected)];uvs=self.uvs[mesh][ids]
        axes=[a for a in range(3) if a!=axis];lo=tri.reshape(-1,3).min(0)[axes]-.04
        hi=tri.reshape(-1,3).max(0)[axes]+.04
        w,h=np.ceil((hi-lo)*self.DENSITY).astype(int)+1
        field=np.zeros((h,w,4),np.float32);depth=np.full((h,w),-np.inf)
        material='RecluseStock' if int(mesh[5:9])<=5 else 'RecluseBarrel'
        tex=self.textures[material]
        for t,uv in zip(tri,uvs):
            q=(t[:,axes]-lo)*self.DENSITY
            a,b=q[1]-q[0],q[2]-q[0]
            den=a[0]*b[1]-a[1]*b[0]
            if abs(den)<1e-9:continue
            x0,y0=np.maximum(np.floor(q.min(0)).astype(int),0)
            x1,y1=np.minimum(np.ceil(q.max(0)).astype(int),[w-1,h-1])
            xx,yy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
            a=((q[1,0]-xx)*(q[2,1]-yy)-(q[1,1]-yy)*(q[2,0]-xx))/den
            b=((q[2,0]-xx)*(q[0,1]-yy)-(q[2,1]-yy)*(q[0,0]-xx))/den
            c=1-a-b;z=(a*t[0,axis]+b*t[1,axis]+c*t[2,axis])*(1 if positive else -1)
            region=np.s_[y0:y1+1,x0:x1+1]
            use=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)&(z>depth[region])
            if not use.any():continue
            st=a[use,None]*uv[0]+b[use,None]*uv[1]+c[use,None]*uv[2]
            xy=np.stack(((st[:,0]%1)*(tex.shape[1]-1),(1-st[:,1]%1)*(tex.shape[0]-1)),axis=-1)
            field[region][use]=self.bilinear(tex,xy);depth[region][use]=z[use]
        valid=np.isfinite(depth)
        # Bounded edge extension avoids black seams on contour-wall centers.
        # It extends RGB/detail only; new solid model faces are opaque.
        for _ in range(5):
            old=valid.copy()
            for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
                shifted=np.roll(old,(dy,dx),(0,1));use=~valid&shifted
                if dy==1:use[0]=False
                if dy==-1:use[-1]=False
                if dx==1:use[:,0]=False
                if dx==-1:use[:,-1]=False
                field[use]=np.roll(field,(dy,dx),(0,1))[use];valid[use]=True
        field[~valid]=[.5,1,.5,.5]
        result=(field,lo,axes)
        self.cache[key]=result
        return result

    def sample(self,points,normal,mesh,component):
        axis=int(np.argmax(abs(normal)))
        field,lo,axes=self.projection(mesh,component,axis,normal[axis]>=0)
        return self.bilinear(field,(np.array(points)[:,axes]-lo)*self.DENSITY)


def raster_triangle(canvas,zbuffer,points,uv,texture,shade):
    h,w=canvas.shape[:2]
    x0=max(0,int(np.floor(points[:,0].min())));x1=min(w-1,int(np.ceil(points[:,0].max())))
    y0=max(0,int(np.floor(points[:,1].min())));y1=min(h-1,int(np.ceil(points[:,1].max())))
    if x0>x1 or y0>y1:return
    p=points
    den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
    if abs(den)<1e-10:return
    xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
    a=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/den
    b=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/den
    c=1-a-b;z=a*p[0,2]+b*p[1,2]+c*p[2,2]
    region=np.s_[y0:y1+1,x0:x1+1]
    valid=(a>=-1e-7)&(b>=-1e-7)&(c>=-1e-7)&(z>zbuffer[region])
    if texture is not None:
        st=a[:,:,None]*uv[0]+b[:,:,None]*uv[1]+c[:,:,None]*uv[2]
        tx=np.clip((st[:,:,0]*texture.shape[1]).astype(int),0,texture.shape[1]-1)
        ty=np.clip((st[:,:,1]*texture.shape[0]).astype(int),0,texture.shape[0]-1)
        colors=texture[ty,tx];valid &= colors[:,:,3]>127
        canvas[region][valid]=np.clip(colors[:,:,:3]*shade,0,255).astype(np.uint8)[valid]
    else:
        canvas[region][valid]=np.array(uv)*shade
    zbuffer[region][valid]=z[valid]


def camera(yaw,elevation):
    a,b=np.radians([yaw,elevation])
    depth=np.array([-math.cos(a)*math.cos(b),math.sin(b),math.sin(a)*math.cos(b)])
    right=np.array([-math.sin(a),0,-math.cos(a)])
    up=np.cross(right,depth)
    return right,up,depth


def render(elements,texture,view,width=680,height=350,meshes=None,paint=None):
    right,up,depth=view
    canvas=np.full((height,width,3),[29,34,42],np.uint8);zbuffer=np.full((height,width),-np.inf)
    center=np.array([8,10.056,7.419135]);scale=30
    def screen(v):
        v=v-center
        return np.stack((v@right*scale+width/2,-v@up*scale+height/2,v@depth),axis=-1)
    light=np.array([-.65,.75,-.2]);light/=np.linalg.norm(light)
    if meshes is not None:
        for m in meshes:
            t=np.array(m['vertices'])[np.array(m['faces'])]
            cr=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);norm=cr/np.maximum(np.linalg.norm(cr,axis=1)[:,None],1e-12)
            colors=paint.sample_normals(t.mean(1),norm,m['name'])
            for tri,n,color in zip(t,norm,colors[:,:3]):
                if n@depth<=0:continue
                raster_triangle(canvas,zbuffer,screen(tri),color,None,.68+.32*max(0,n@light))
    else:
        tex=np.array(texture.convert('RGBA'))
        for e in elements:
            q=screen(vertices(e));R=rotation(e)
            for face,f in e['faces'].items():
                n=R@np.array(NORMALS[face])
                if n@depth<=0:continue
                u,v,U,V=f['uv'];uv=np.array([[u,v],[U,v],[U,V],[u,V]])/16
                quad=q[list(CORNERS[face])]
                for ids in ((0,1,2),(0,2,3)):
                    raster_triangle(canvas,zbuffer,quad[list(ids)],uv[list(ids)],tex,.68+.32*max(0,n@light))
    return Image.fromarray(canvas)


def semantic_geometry():
    """Authored functional blockout in the unchanged W30 model coordinate frame.

    No source components determine the number, topology or thickness of boxes.
    Source identifiers below select *paint evidence* only.
    """
    result = []
    def solid(name, lo, hi, material='white', mesh='Mesh_0006.rip', component=1,
              part='body', angle=0, axis='x', origin=None, art=False):
        center = ((np.array(lo)+hi)/2).tolist() if origin is None else origin
        result.append(dict(name=name, **{'from':lo, 'to':hi},
            rotation=dict(origin=center, **{a:angle if a==axis else 0 for a in 'xyz'}),
            material=material, source_mesh=mesh, source_component=component,
            part=part, kind='semantic_solid', artwork=art))
    def yz(name, a, b, width, thick, material='white', **kw):
        # a,b are [y,z], local long axis z. A structural member, not contour tracing.
        a,b=np.array(a),np.array(b); c=(a+b)/2; length=float(np.linalg.norm(b-a))
        angle=-math.degrees(math.atan2(*(b-a)[[0,1]]))
        solid(name,[8-width/2,c[0]-thick/2,c[1]-length/2],
              [8+width/2,c[0]+thick/2,c[1]+length/2],material,
              angle=angle,**kw)
    # Continuous solid receiver, stepped top rail and front optic housing.
    solid('receiver/main', [7.35,10.35,4.0],[8.65,11.86,16.22],art=True)
    solid('receiver/lower-keel',[7.46,10.05,4.0],[8.54,10.42,13.35],art=True)
    solid('receiver/rear-shoulder',[7.36,9.85,13.7],[8.64,10.45,16.25],art=True)
    yz('receiver/under-shoulder',[9.93,13.6],[10.28,11.2],1.18,.40,art=True)
    solid('receiver/top-seam',[7.30,11.86,6.1],[8.70,12.00,16.28],'steel')
    solid('power-rail/burgundy-core',[7.45,12.0,8.35],[8.55,12.58,16.35],'burgundy',art=True)
    solid('power-rail/top-spine',[7.52,12.58,8.5],[8.48,12.70,16.35],'rubber')
    for z in (9.0,12.5):
        solid(f'power-rail/bridge-{z}',[7.32,11.98,z],[8.68,12.70,z+.20],'steel')
    solid('receiver/rear-top',[7.36,12.0,13.0],[8.64,12.93,16.50],art=True)
    solid('optic/hood-main',[7.20,11.88,4.45],[8.80,13.04,8.55],mesh='Mesh_0003.rip',component=0,art=True)
    yz('optic/front-ramp',[12.28,3.50],[13.00,4.65],1.46,.59,mesh='Mesh_0003.rip',component=0)
    solid('optic/front-cheek',[7.25,11.94,3.64],[8.75,12.54,4.74],mesh='Mesh_0003.rip',component=0)
    solid('optic/lower-lip',[7.16,11.72,3.44],[8.84,11.94,6.8],mesh='Mesh_0005.rip',component=2)
    yz('optic/rear-ramp',[13.01,8.45],[12.65,9.25],1.30,.22,mesh='Mesh_0002.rip',component=0,art=True)
    solid('optic/crown',[7.42,13.04,4.85],[8.58,13.30,7.65],mesh='Mesh_0003.rip',component=0)
    # Side locking blocks have visible depth; screws and slots are painted.
    for side,x in (('left',7.00),('right',8.61)):
        solid(f'optic/{side}-lock',[x,10.67,5.12],[x+.39,11.92,6.70],mesh='Mesh_0003.rip',component=1 if side=='left' else 2)
    # Short stock/pad and lower open triangular frame: large, solid volumes.
    solid('stock/pad',[7.32,6.75,16.48],[8.68,12.90,17.30],'rubber',mesh='Mesh_0012.rip',component=0)
    solid('stock/painted-spine',[7.36,7.05,15.90],[8.64,12.78,16.51],art=True)
    solid('stock/bird-field',[7.34,9.45,13.95],[8.66,12.18,16.28],art=True)
    solid('stock/bird-body',[7.37,8.25,14.85],[8.63,9.65,16.25],art=True)
    yz('stock/bird-shoulder',[9.25,15.9],[10.7,13.6],1.27,.95,art=True)
    yz('stock/lower-brace',[5.90,5.10],[8.30,15.90],.94,.45,art=True)
    yz('stock/heel-brace',[8.30,15.70],[7.60,16.12],.94,.48,art=True)
    solid('stock/front-heel',[7.50,5.56,4.0],[8.50,6.13,5.90],mesh='Mesh_0004.rip',component=2)
    # Foregrip is tilted solid rubber, with its source red diagonal liner in UV.
    yz('foregrip/core',[6.22,4.65],[10.18,3.10],1.35,1.43,'rubber',mesh='Mesh_0007.rip',component=0)
    yz('foregrip/backstrap',[6.20,5.28],[9.83,4.10],1.12,.43,'rubber',mesh='Mesh_0007.rip',component=0)
    yz('foregrip/white-beavertail',[10.55,4.82],[9.90,1.95],1.42,.29)
    # Independent reload part stays in source coordinates and at source anchor.
    yz('magazine/core',[6.72,8.35],[9.47,9.29],1.12,1.32,'rubber',
       mesh='Mesh_0007.rip',component=1,part='magazine')
    yz('magazine/front-round',[6.78,7.85],[9.25,8.71],.85,.43,'rubber',
       mesh='Mesh_0007.rip',component=1,part='magazine')
    solid('magazine/feed-neck',[7.55,9.35,8.76],[8.45,9.86,9.61],'rubber',
          mesh='Mesh_0007.rip',component=1,part='magazine')
    yz('magazine/floorplate',[6.40,7.75],[6.63,8.98],1.20,.25,'rubber',
       mesh='Mesh_0007.rip',component=1,part='magazine')
    # Trigger and guard: empty space is actual unoccupied model volume.
    yz('trigger/upper',[10.02,7.50],[9.43,7.15],.32,.16,'burgundy',mesh='Mesh_0000.rip',component=0)
    yz('trigger/hook',[9.43,7.15],[8.91,7.40],.32,.15,'burgundy',mesh='Mesh_0000.rip',component=0)
    yz('trigger-guard/front',[9.93,5.72],[8.55,6.03],.68,.19)
    yz('trigger-guard/bottom',[8.55,6.03],[8.50,7.86],.68,.19)
    yz('trigger-guard/rear',[8.50,7.86],[9.78,8.30],.68,.19)
    # Octagonal open sight, with a through aperture along the firing axis.
    ring=[(7.46,13.35),(7.46,14.18),(7.73,14.53),(8.27,14.53),
          (8.54,14.18),(8.54,13.35),(8.28,13.13),(7.72,13.13)]
    for i,((x,y),(X,Y)) in enumerate(zip(ring,ring[1:]+ring[:1])):
        c=[(x+X)/2,(y+Y)/2,7.45]; length=math.hypot(X-x,Y-y)
        solid(f'sight/hoop-{i}',[c[0]-length/2,c[1]-.045,c[2]-.09],
              [c[0]+length/2,c[1]+.045,c[2]+.09],axis='z',
              angle=math.degrees(math.atan2(Y-y,X-x)),mesh='Mesh_0011.rip',component=0)
    for x in (7.47,8.37):
        solid(f'sight/foot-{x}',[x,12.93,7.15],[x+.16,13.34,7.77],'steel',mesh='Mesh_0011.rip',component=0)
    # Barrel: broad solid shaft/collar; perforations stay in source-derived UV.
    for name,z,Z,r in [('barrel/shaft',.35,4.25,.54),('barrel/collar',2.6,3.45,.64),
                        ('muzzle/shroud',-2.34,.70,.64)]:
        for k,(w,h) in enumerate(((2*r,1.40*r),(1.40*r,2*r))):
            solid(name+f'-{k}',[8-w/2,11.51-h/2,z],[8+w/2,11.51+h/2,Z],
                  'steel',mesh='Mesh_0006.rip',component=0)
    # Eight crown staves surround an actual recessed bore, no painted black dot.
    for i in range(8):
        a=math.radians(22.5+i*45); x=8+math.cos(a)*.52;y=11.51+math.sin(a)*.52
        solid(f'muzzle/crown-{i}',[x-.225,y-.105,-2.58],[x+.225,y+.105,-2.12],
              'steel',axis='z',angle=math.degrees(a)+90,mesh='Mesh_0006.rip',component=0)
    solid('muzzle/bore-recess',[7.59,11.10,-2.10],[8.41,11.92,-2.04],'bore')
    # Three raised ribs cast the visible top silhouette; their slots remain UV.
    for i,z in enumerate((-1.63,-.72,.18)):
        yz(f'muzzle/top-vent-{i}',[12.10,z],[12.22,z+.42],.60,.10,'steel',mesh='Mesh_0006.rip',component=0)
    return result


class SemanticPaint(LegacyPaint):
    """Quiet material fields; selective source structural detail and bird masks.

    W125's FBX UV sampling is retained as evidence for perforations and seams,
    not as a full diffuse projection or geometry algorithm. Color is authored.
    """
    PALETTE={'white':(224,226,222),'burgundy':(124,21,37),
             'rubber':(29,35,40),'steel':(76,85,94),'bore':(10,13,17)}
    def __init__(self,canonical,parser,meshes):
        super().__init__(canonical)
        self.source_uv=SourceUV(parser,meshes)

    def tile(self,s,face,w,h,q):
        u=q[1]-q[0];v=q[3]-q[0]
        uu,vv=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
        points=q[0]+uu[:,:,None]*u+vv[:,:,None]*v
        p=points.reshape(-1,3); n=rotation(s)@np.array(NORMALS[face])
        material=s['material'];colors=np.tile(self.PALETTE[material],(len(p),1)).astype(float)
        detail=self.source_uv.sample(p,n,s['source_mesh'],s['source_component'])
        diffuse,ao,nx,ny=detail.T
        # Restrained normal/AO relief. White receiver gets seams but no full
        # source diffuse modulation; muzzle source perforations get more depth.
        relief=np.clip((nx-.5)*.20-(ny-.5)*.16,-.065,.065)
        amount=.30 if s['name'].startswith('muzzle/') else .13
        response=1-amount*(1-ao)+relief
        if material=='steel' and s['name'].startswith('muzzle/shroud'):
            response=.40+.60*ao+relief
        colors*=response[:,None]
        # Artwork only: the accepted default-painted masks, individually
        # sampled in the new face frame on physical receiver/stock surfaces.
        if s['artwork'] and abs(n[0])>.65 and not s['name'].startswith('optic/'):
            old=super().sample(p,n).reshape(-1,4).astype(float)
            red=(old[:,0]>old[:,1]*1.45)&(old[:,0]>old[:,2]*1.35)
            # The reference's front receiver and optic are quiet white, not
            # random fragments of the coarse W31 bird projection. Preserve
            # those source masks only where the rear bird field belongs.
            if s['name'].startswith('receiver/'):
                red &= p[:,2]>12.5
            pale=np.clip((old[:,1]/np.maximum(old[:,0],1)-.32)*2.6,0,1)
            colors[red]=np.array(self.PALETTE['burgundy'])+pale[red,None]*[65,58,52]
        if s['name']=='optic/hood-main' and abs(n[0])>.65:
            # Reference-backed charge window: one red surround with four
            # pale cells, painted on the white housing (no extra geometry).
            z,y=p[:,2],p[:,1]
            border=(z>5.05)&(z<7.45)&(y>12.40)&(y<12.91)
            window=(z>5.14)&(z<7.36)&(y>12.46)&(y<12.85)
            colors[border]=[98,105,108]
            colors[window]=[151,26,44]
            for a,b in ((5.25,6.02),(6.11,6.42),(6.51,6.82),(6.91,7.25)):
                colors[(z>a)&(z<b)&(y>12.54)&(y<12.77)]=[238,231,223]
        if s['name'].startswith('foregrip/') and abs(n[0])>.65:
            # Reference's four diagonal red liner reveals, on flat grip faces.
            stripe=np.zeros(len(p),bool)
            for y,z in ((6.60,4.3),(7.45,4.0),(8.30,3.7),(9.15,3.4)):
                stripe |= (abs(p[:,1]-y-.33*(p[:,2]-z))<.065)&(abs(p[:,2]-z)<.56)
            colors[stripe]=[126,22,36]
        # A sub-pixel edge highlight helps read broad solids without extra cubes.
        edge=(uu.reshape(-1)<.014)|(uu.reshape(-1)>.986)|(vv.reshape(-1)<.014)|(vv.reshape(-1)>.986)
        if material not in ('bore','rubber'):colors[edge]=colors[edge]*.90+np.array([244,245,239])*.10
        return Image.fromarray(np.column_stack((np.clip(colors,0,255).astype(np.uint8),
            np.full(len(p),255,np.uint8))).reshape(h,w,4))


def atlas_models(specs,paint):
    """Allocate independent, padded face rectangles at useful physical density."""
    edge=1024; density=26; pad=2
    atlas=Image.new('RGBA',(edge,edge),(0,0,0,0));requests=[];parts={'body':[],'magazine':[]}
    for s in specs:
        e={k:s[k] for k in ('name','from','to','rotation')};e['faces']={}
        parts[s['part']].append(e)
        vs=vertices(s)
        for face,ids in CORNERS.items():
            q=vs[list(ids)]
            # Broad identity-bearing sides get more texels than underside edges.
            d=density*(1.28 if s['artwork'] and face in ('west','east') else 1)
            w=max(3,math.ceil(np.linalg.norm(q[1]-q[0])*d))
            h=max(3,math.ceil(np.linalg.norm(q[3]-q[0])*d))
            requests.append((e,s,face,w,h,q))
    x=y=pad;row=0;islands=[];used=0
    for e,s,face,w,h,q in sorted(requests,key=lambda r:(-r[4],-r[3],r[0]['name'],r[2])):
        if x+w+pad>edge:x=pad;y+=row+pad*2;row=0
        if y+h+pad>edge:raise ValueError(f'1024 atlas overflow: {y+h}')
        tile=paint.tile(s,face,w,h,q)
        padded=np.pad(np.array(tile),((pad,pad),(pad,pad),(0,0)),mode='edge')
        atlas.paste(Image.fromarray(padded),(x-pad,y-pad))
        uv=[x/edge*16,y/edge*16,(x+w)/edge*16,(y+h)/edge*16]
        e['faces'][face]={'uv':uv,'texture':'#0'}
        islands.append(dict(element=e['name'],face=face,pixels=[x,y,x+w,y+h]))
        used+=w*h;x+=w+pad*2;row=max(row,h)
    return atlas,parts,dict(resolution=edge,density=density,padding=pad,
        used_pixels=used,fill=round(used/edge**2,4),islands=islands)


def comparison(meshes,canonical,parts,atlas):
    sheet=Image.new('RGB',(2100,1510),(19,24,32));d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',23)
    small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
    es=parts['body']+parts['magazine']
    d.text((25,14),'THE RECLUSE / W126 / semantic solids + packed face UV',font=font,fill='#f1e7dc')
    ref=Image.open(REFERENCE).convert('RGB');ref.thumbnail((780,400));sheet.paste(ref,(20,54))
    d.text((830,65),f'{len(es)} opaque solid cuboids / 1024 atlas / no alpha side shells',font=font,fill='#f1e7dc')
    for i,t in enumerate(['Receiver, optic housing, short stock, open lower frame and grips are authored volumes.',
        'Open sight, trigger guard and recessed muzzle bore remain physical holes.',
        'Burgundy bird masks from accepted default paint; selective source-UV perforation detail.',
        'RAW column = actual FBX triangles with W31 color lookup (not original shader).',
        'Same coordinate frame, camera and offline light. Native held / ADS / reload: master.']):
        d.text((830,120+i*35),t,font=small,fill='#bbc6d3')
    labels=('RAW SOURCE / 20,369 FBX triangles','W126 / solid semantic parts','W126 / opposite side or front')
    for col,label in enumerate(labels):d.text((20+col*700,456),label,font=font,fill='#dedbd4')
    for row,(yaw,elev) in enumerate(((0,0),(-27,14),(35,20))):
        v=camera(yaw,elev);y=500+row*325
        raw=render([],None,v,meshes=meshes,paint=LegacyPaint(canonical))
        new=render(es,atlas,v)
        other=render(es,atlas,camera(180-yaw,elev))
        if row==2:
            front=render(es,atlas,camera(-90,0))
            other=Image.new('RGB',(680,350),(29,34,42))
            detail=front.crop((290,15,390,305)).resize((100,290),Image.Resampling.NEAREST)
            other.paste(detail,(100,25))
            muzzle=front.crop((310,105,370,175)).resize((245,245),Image.Resampling.NEAREST)
            other.paste(muzzle,(340,40))
            ImageDraw.Draw(other).text((35,320),'FRONT / sight aperture + recessed muzzle bore',font=small,fill='#bbc6d3')
        for col,im in enumerate((raw,new,other)):sheet.paste(im,(10+col*700,y))
    d.text((25,1481),'Offline evidence only. No original material shader, live pack load, ADS alignment or animation claim.',font=small,fill='#bbc6d3')
    return png(sheet)


def assert_assembled_budget(elements):
    assert len(elements)<=MAX_ASSEMBLED_ELEMENTS, f'Recluse assembled element cap exceeded: {len(elements)} > {MAX_ASSEMBLED_ELEMENTS}'


def generate():
    canonical=json.loads((ROOT/CANON).read_bytes())
    parser=load_module('scripts/generate_reload_models_w100.py','w126_source')
    meshes=parser.source_meshes()  # pins original archive and source files
    meta=json.loads((ROOT/BB).read_bytes())['destiny_w30']
    specs=semantic_geometry();assert_assembled_budget(specs)
    paint=SemanticPaint(canonical,parser,meshes);atlas,parts,uvplan=atlas_models(specs,paint)
    outputs={TEXTURE:png(atlas)}
    for suffix,es in [('',parts['body']+parts['magazine']),('_body',parts['body']),('_magazine',parts['magazine'])]:
        j=dict(credit='W126 Recluse semantic solid redesign / default bird paint / source-informed face UV',
            ambientocclusion=False,textures={'0':'destiny:item/weapon/w123/the_recluse','particle':'destiny:item/weapon/w123/the_recluse'},elements=es)
        if not suffix:j['display']=canonical['display']
        outputs[MODEL/f'the_recluse{suffix}.json']=encode(j)
    limitations=['Offline renderer approximates diffuse lighting, not original Bungie shader or native client.',
        'Bird masks retain W31 coarse painted boundaries; higher atlas density does not invent missing bird detail.',
        'Curved source bevels are simplified into broad functional solids; live ADS/hand clearance remains master QA.',
        'Magazine remains the established lower-cartridge proxy, semantically unlabelled in source; no anchor rebase.']
    source=dict(reference=str(REFERENCE),reference_sha256=sha(REFERENCE.read_bytes()),
        archive_sha256=parser.ARCHIVE_SHA256,source_files=meta['source_files'],
        canonical_sha256=sha((ROOT/CANON).read_bytes()),paint_atlas=str(paint.path),
        paint_atlas_sha256=sha((ROOT/paint.path).read_bytes()),
        source_uv_materials={p.name:sha(p.read_bytes()) for p in sorted(CACHE.glob('*.dds'))
                            if p.stem.startswith(('RecluseStock_','RecluseBarrel_'))})
    design=dict(schema='destiny.weapon-surface.w126.v1',id='the_recluse',
        method='authored semantic solid cuboids, rotated structural members and independent opaque face UV islands',
        frame=dict(mapping=['8 - source_y * scale','8 + source_z * scale','8 - source_x * scale'],
            scale=meta['scale'],anchor=meta['anchor'],source_bounds=meta['model_bounds']),
        magazine=dict(mesh=parser.MAGAZINE_COMPONENT[0],component=parser.MAGAZINE_COMPONENT[1],
            coordinate_rebase=False,anchor=[8,8,8]),
        identity=['short stock and open lower frame','two grips and open trigger guard','octagonal open sight',
            'long perforated muzzle and actual bore','default burgundy / white bird paint'],
        construction=dict(alpha_shells=0,source_component_extrusion=False,solid_faces=6,
            geometry='semantic_geometry() contains deliberate receiver/stock/grip/sight/muzzle blocks',
            palette=SemanticPaint.PALETTE,uv='independent face frames with 2px bleed; sides receive 1.28x density',
            detail='W125 source-UV technique reused only for source seams/vents; no whole diffuse projection'),
        parts={part:[s for s in specs if s['part']==part] for part in parts},uv_layout=uvplan,
        provenance=source,limitations=limitations)
    outputs[ART/'design.json']=encode(design)
    ids={p:[] for p in parts};bbes=[]
    for part,es in parts.items():
        for e in es:
            uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w126/the_recluse/'+e['name']));ids[part].append(uid)
            bbes.append(dict(name=e['name'],uuid=uid,type='cube',**{'from':e['from'],'to':e['to']},
                origin=e['rotation']['origin'],rotation=[e['rotation'][a] for a in 'xyz'],autouv=0,box_uv=False,
                faces={f:{'uv':[v*atlas.width/16 for v in face['uv']],'texture':0} for f,face in e['faces'].items()}))
    bb=dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='W126 The Recluse semantic solids',
        resolution={'width':atlas.width,'height':atlas.height},elements=bbes,
        outliner=[{'name':p,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'w126/'+p)),'origin':[8,8,8],'children':ids[p]} for p in parts],
        textures=[dict(name='the_recluse.png',id='0',uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'w126/recluse-atlas')),
            width=atlas.width,height=atlas.height,uv_width=atlas.width,uv_height=atlas.height,
            source='data:image/png;base64,'+base64.b64encode(outputs[TEXTURE]).decode())])
    outputs[ART/'inspection.bbmodel']=encode(bb)
    outputs[ART/'comparison.png']=comparison(meshes,canonical,parts,atlas)
    counts={p:len(es) for p,es in parts.items()}
    manifest=dict(stage='W126',id='the_recluse',generator='scripts/generate_surface_w123_the_recluse.py',
        source_triangles=sum(len(m['faces']) for m in meshes),elements=sum(counts.values()),parts=counts,
        emitted_faces=sum(counts.values())*6,cuboids=sum(counts.values()),source_plane_skins=0,
        profile_caps=0,profile_wall_cuboids=0,alpha_triangles=0,
        semantic_groups=dict(collections.Counter(s['name'].split('/')[0] for s in specs)),
        max_assembled_elements=1000,atlas=list(atlas.size),uv_islands=len(uvplan['islands']),
        uv_fill=uvplan['fill'],native_rotated_cuboids=sum(any(abs(s['rotation'][a])>.001 for a in 'xyz') for s in specs),
        full_display_exact=True,part_models_have_display=False,canonical_anchor_preserved=True,
        trajectory_files_changed=False,source=source,limitations=limitations,
        sha256={str(p):sha(b) for p,b in outputs.items()})
    outputs[ART/'manifest.json']=encode(manifest)
    outputs[ART/'review.md']=(
        '# W126 The Recluse semantic redesign\n\n'
        f"{manifest['elements']} solid cuboids: body {counts['body']}, magazine {counts['magazine']}; "
        f"{manifest['emitted_faces']} opaque faces, {manifest['uv_islands']} independent UV islands on 1024² "
        f"({manifest['uv_fill']:.1%} content occupancy before padding). No source cap/wall extrusion or alpha receiver skins.\n\n"
        'The receiver, optic hood, short stock, lower diagonal frame, grips and power rail are deliberately sized functional solids. '
        'Eight sight bars and eight muzzle crown staves keep real apertures; the trigger guard is three structural bars. '
        'The white optic hood has a reference-backed red four-cell charge window; inherited bird paint is restricted to the rear fields. '
        'Small source perforations, seams and fasteners use selective FBX source-UV relief; clean default paint and burgundy bird masks '
        'are repacked into each new face frame. Surface detail does not create additional cubes.\n\n'
        'Raw FBX triangles vs new side and oblique views are rendered with matching offline cameras in comparison.png. '
        'The raw column uses W31 color lookup and is not a source-shader restoration. The full model display, source frame, scale and '
        'anchor remain unchanged; separate magazine vertices stay in the existing frame. Past W124/W125 QA is retained.\n\n'
        'Live pack substitution, first/third person, ADS, detached magazine reload and 10–20 simultaneous displays belong to master. '
        'No native success or performance result is claimed here.\n').encode()
    return outputs


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true')
    args=ap.parse_args();outputs=generate()
    batch=json.loads((ROOT/'docs/qa/2026-10-25/w126/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w126-the_recluse'))
    for p,data in outputs.items():
        assert str(p) in owned,p
        path=ROOT/p
        if args.verify:assert path.is_file() and path.read_bytes()==data,'Regeneration drift: '+str(p)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    m=json.loads(outputs[ART/'manifest.json'])
    print(('Verified' if args.verify else 'Generated')+f" {len(outputs)} outputs: {m['elements']} solid cuboids, parts {m['parts']}, {m['uv_islands']} face UVs")


if __name__=='__main__':main()


