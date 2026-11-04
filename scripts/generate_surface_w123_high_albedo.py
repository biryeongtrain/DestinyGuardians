#!/usr/bin/env python3
"""W143 High Albedo: authored semantic solids, detailed opaque face UVs.
Reads accepted Blender data as inert SDNA arrays. No DCC, shader, source-script,
game or shared registry execution. Only the seven owned generated artifacts.
"""
import argparse, base64, copy, hashlib, io, json, math, re, runpy, struct, subprocess, uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='high_albedo'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/sidearm/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w123_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w143/{ID}-worker.md'
REFS='art/weapons/w31/references.json'
RAW=Path('/tmp/destiny-weapons-w30/raw/high_albedo/extracted')
PHOTO=Path('/tmp/destiny-weapons-w31/references/high_albedo.jpg')
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER))
FACES=H['FACES']; EDGE=1024
PALETTE=dict(blue=[74,137,168],blue_edge=[117,173,195],red=[169,37,27],red_edge=[203,52,34],orange=[232,100,25],steel=[59,64,67],black=[23,28,31],silver=[147,158,161])
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w143:high_albedo:'+n))
def render_element(e):
 e=copy.deepcopy(e)
 if 'rotation' in e:
  r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
 return e
def vertices(e):return H['vertices'](render_element(e))
def model_triangles(m,tex):
 m=copy.deepcopy(m);m['elements']=[render_element(e) for e in m['elements']]
 return H['model_triangles']({'full':m},tex)

class Blend:
    """Inert SDNA reader adapted from W138; reads Blender 2.91 data only. Never imports bpy or source code."""
    def __init__(self,path):
        data=path.read_bytes()
        if data[:4]==b'\x28\xb5\x2f\xfd':
            data=subprocess.check_output(['rtk','proxy','zstd','-dc',str(path)])
        assert data[:12]==b'BLENDER-v291',data[:12]
        self.blocks={};pos=12
        while pos+24<=len(data):
            code,size,addr,dna,count=struct.unpack_from('<4sIQII',data,pos);pos+=24
            raw=data[pos:pos+size];pos+=size
            self.blocks[addr]=(code,dna,count,raw)
            if code==b'DNA1': self.dna=raw
            if code==b'ENDB': break
        d=self.dna;pos=0
        def tag(s):
            nonlocal pos
            assert d[pos:pos+4]==s;(pos:=pos+4)
        def integer():
            nonlocal pos
            v=struct.unpack_from('<I',d,pos)[0];pos+=4;return v
        def strings(n):
            nonlocal pos
            a=[]
            for _ in range(n):
                end=d.index(0,pos);a.append(d[pos:end].decode());pos=end+1
            pos=(pos+3)//4*4;return a
        tag(b'SDNA');tag(b'NAME');names=strings(integer())
        tag(b'TYPE');types=strings(integer());tag(b'TLEN')
        sizes=struct.unpack_from('<'+str(len(types))+'H',d,pos);pos+=2*len(types);pos=(pos+3)//4*4
        tag(b'STRC');n=integer();self.structs=[];self.fields={};self.sizes=dict(zip(types,sizes))
        for _ in range(n):
            ti,nf=struct.unpack_from('<HH',d,pos);pos+=4;fields={};offset=0
            for _ in range(nf):
                ft,fn=struct.unpack_from('<HH',d,pos);pos+=4;name=names[fn]
                count=math.prod(int(x) for x in re.findall(r'\[(\d+)\]',name))
                size=(8 if '*' in name else sizes[ft])*count
                key=re.sub(r'\[.*','',name).lstrip('*')
                fields[key]=(offset,types[ft],count,'*' in name,size);offset+=size
            assert offset==sizes[ti],(types[ti],offset,sizes[ti])
            self.structs.append(types[ti]);self.fields[types[ti]]=fields
    def field(self,raw,kind,name):
        off,typ,count,ptr,size=self.fields[kind][name]
        if ptr:return struct.unpack_from('<Q',raw,off)[0]
        fmts={'int':'i','short':'h','float':'f','double':'d','char':'b','uchar':'B','uint':'I'}
        if typ=='char':return raw[off:off+size].split(b'\0')[0].decode(errors='replace')
        if typ not in fmts:return raw[off:off+size]
        v=struct.unpack_from('<'+str(count)+fmts[typ],raw,off);return v[0] if count==1 else v
    def records(self,kind):
        for addr,(code,dna,count,raw) in self.blocks.items():
            if self.structs[dna]==kind:
                size=self.sizes[kind]
                for i in range(count):yield addr+i*size,raw[i*size:(i+1)*size]
    def pointed(self,addr):return self.blocks[addr][3]

def source_meshes():
    """Exact W30 accepted object names, stored matrices, no executable Blender content."""
    meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
    path=RAW/'High Albedo.blend'
    assert sha(path.read_bytes())==meta['source_files'][path.name]
    b=Blend(path);meshes=[]
    for _,o in b.records('Object'):
        name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']:continue
        matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
        mesh=b.pointed(b.field(o,'Object','data'));n=b.field(mesh,'Mesh','totvert')
        v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
        world=(np.c_[v,np.ones(n)]@matrix)[:,:3]
        native=world[:,[0,2,1]]*meta['scale']+meta['anchor']
        nl=b.field(mesh,'Mesh','totloop')
        loops=np.ndarray((nl,),'<i4',b.pointed(b.field(mesh,'Mesh','mloop')),strides=(b.sizes['MLoop'],))
        uvs=np.ndarray((nl,2),'<f4',b.pointed(b.field(mesh,'Mesh','mloopuv')),strides=(b.sizes['MLoopUV'],4)).astype(float)
        uvs[:,1]=1-uvs[:,1];polys=b.pointed(b.field(mesh,'Mesh','mpoly'));faces=[];uv=[]
        for i in range(b.field(mesh,'Mesh','totpoly')):
            start,count=struct.unpack_from('<ii',polys,b.sizes['MPoly']*i)
            assert count==3,count
            ix=[start,start+1,start+2];faces.append(loops[ix]);uv.append(uvs[ix])
        ptr=struct.unpack_from('<Q',b.pointed(b.field(mesh,'Mesh','mat')))[0]
        material=b.field(b.field(b.pointed(ptr),'Material','id'),'ID','name')[2:]
        meshes.append(dict(name=name,vertices=native,faces=np.array(faces),uv=np.array(uv),material=material,world_bounds=[world.min(0).tolist(),world.max(0).tolist()],object_matrix=matrix.tolist()))
    pts=np.concatenate([m['vertices'] for m in meshes]);world=np.array([m['world_bounds'] for m in meshes])
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']
    np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=1e-6,rtol=0)
    np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta

def source_triangles(meshes):
 textures={m:np.asarray(Image.open(RAW/(m+'_Diffuse.dds')).convert('RGBA')) for m in {m['material'] for m in meshes}};result=[]
 for m in meshes:
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20)
   result.append((p,uv,textures[m['material']],n))
 return result

def make_design(meta,meshes):
 parts=[]
 def box(group,name,c,size,mat,motif='plain',turn=None):
  e=dict(name=name,**{'from':[round(v-s/2,7) for v,s in zip(c,size)],'to':[round(v+s/2,7) for v,s in zip(c,size)]})
  if turn:e['rotation']=dict(origin=list(c),axis=turn[0],angle=turn[1])
  parts.append(dict(group=group,material=mat,motif=motif,geometry=e))
 def beam(group,name,a,b,width,depth,mat,motif='plain',x=8):
  y,z=(np.array(a)+b)/2;dy,dz=np.array(b)-a
  box(group,name,[x,y,z],[width,math.hypot(dy,dz),depth],mat,motif,('x',math.degrees(math.atan2(dz,dy))))
 def tube(group,name,y,z0,z1,r,t,mat,motif='plain'):
  # Eight tangent walls, overlapping corners. A physical octagonal aperture.
  for i in range(8):
   a=i*math.pi/4;rr=r-t/2
   box(group,f'{name}_{i}',[8-rr*math.sin(a),y+rr*math.cos(a),(z0+z1)/2],
       [2*r*math.tan(math.pi/8)+.012,t,z1-z0],mat,motif,('z',i*45))
 # Rear upper receiver is an intersecting filled mass, with a stepped crown.
 box('receiver','blue_receiver',[8,12.92,8.23],[1.52,1.95,5.82],'blue','housing')
 box('receiver','blue_top_spine',[8,13.96,8.0],[1.22,.30,5.15],'blue_edge','housing')
 box('receiver','rear_heel',[8,12.66,11.13],[1.48,2.05,.38],'black','panel',('x',-14))
 box('receiver','rear_chamfer',[8,13.78,10.95],[1.30,.48,.65],'blue','housing',('x',-22.5))
 box('receiver','front_receiver_collar',[8,12.95,5.08],[1.92,2.15,.42],'blue','collar')
 box('receiver','collar_crown',[8,14.05,5.08],[1.53,.18,.42],'blue_edge')
 box('receiver','rear_sight_blade',[8,14.29,9.02],[.26,.3792186,.68],'blue_edge','sight')
 box('receiver','lower_blue_ledge',[8,12.05,8.2],[1.72,.25,5.62],'blue_edge','panel')
 # An orange reservoir is visible through the blue side housing, as in defaultphoto.
 for x in (7.22,8.78):
  box('receiver','reservoir_'+str(x),[x,13.31,6.57],[.12,.98,2.27],'orange','reservoir')
  box('receiver','reservoir_sill_'+str(x),[x,12.74,6.57],[.20,.20,2.55],'blue_edge')
 # Deep red filled lower frame: broad continuous receiver webs, not side cards.
 box('frame','red_lower_receiver',[8,11.56,7.97],[1.56,.83,5.82],'red','frame')
 box('frame','red_foreframe',[8,11.62,2.87],[1.48,.67,4.12],'red','frame')
 box('frame','red_frame_haunch',[8,11.0,5.48],[1.58,.62,1.47],'red','frame',('x',-17))
 box('frame','grip_saddle',[8,10.66,7.21],[1.46,.83,2.62],'red','frame')
 # Upper exposed barrel: real through-mouth, with solid breech recessed behind it.
 tube('barrel','black_barrel',13.16,-1.68,4.83,.57,.17,'steel','barrel')
 box('barrel','breech_core',[8,13.16,4.56],[.8,.8,.55],'black')
 tube('barrel','blue_barrel_sleeve',13.16,-.30,1.20,.69,.18,'blue','sleeve')
 tube('barrel','barrel_step_collar',13.16,2.56,3.10,.64,.14,'steel','collar')
 # Open red cage. The side windows expose the barrel instead of alpha cards.
 for x in (7.12,8.88):
  for y in (12.37,13.99):box('cage',f'cage_rail_{x}_{y}',[x,y,2.84],[.15,.15,4.12],'red_edge','rail')
  for z in (.80,3.78):box('cage',f'cage_post_{x}_{z}',[x,13.18,z],[.18,1.72,.17],'red','rail')
 # The blue top carry bridge encloses a real transverse slot above the barrel.
 beam('bridge','bridge_front', [14.36,-1.42],[14.36,.55],.40,.18,'blue_edge')
 beam('bridge','bridge_drop',[14.36,.55],[13.99,1.18],.40,.18,'blue')
 beam('bridge','bridge_rear',[13.99,1.18],[14.03,4.86],.40,.18,'blue')
 # Orange muzzle brace: a four-sided opening around the actual upper bore.
 box('brace','brace_top',[8,14.18,-1.45],[1.27,.36,.30],'orange','brace')
 box('brace','brace_bottom',[8,12.08,-1.45],[1.27,.37,.30],'orange','brace')
 for x in (7.36,8.64):
  box('brace','brace_side_'+str(x),[x,13.16,-1.45],[.26,1.87,.30],'orange','brace')
 for y in (12.62,13.70):
  for x in (6.98,9.02):box('brace',f'brace_lug_{x}_{y}',[x,y,-1.45],[.4173716,.24,.30],'orange','brace')
 box('brace','brace_lower_neck',[8,11.69,-1.45],[.59,.47,.30],'orange','brace')
 # Knurled lower cylinder has an open small forward nozzle and recessed end cap.
 tube('cylinder','knurled_cylinder',11.38,-3.05,2.43,.60,.18,'steel','knurl')
 tube('cylinder','silver_nozzle',11.38,-3.4793014,-3.01,.44,.22,'silver','nozzle')
 box('cylinder','cylinder_end_core',[8,11.38,.60],[.80,.80,.27],'black')
 tube('cylinder','orange_cylinder_band',11.38,-1.62,-1.24,.66,.14,'orange','brace')
 box('cylinder','blue_cylinder_mount',[8,11.28,3.03],[1.28,.85,1.36],'blue','label')
 # Filled slanted grip. Separate blue backstrap and red finger edge carry depth.
 box('grip','grip_core',[8,8.65,7.85],[1.24,4.35,1.68],'red','grip',('x',-17))
 box('grip','blue_backstrap',[8,8.48,8.64],[1.45,4.22,.76],'blue','backstrap',('x',-17))
 box('grip','red_finger_spine',[8,8.62,7.06],[1.12,3.90,.25],'red_edge','grip',('x',-17))
 box('grip','grip_heel',[8,6.18,8.59],[1.48,.52,1.69],'blue_edge','panel',('x',-17))
 box('grip','magazine_base',[8,5.97,8.67],[1.35,.32,1.56],'black','mag',('x',-17))
 # Open-bottom swept trigger guard follows the source, with free space to the grip.
 beam('guard','guard_root',[11.40,4.24],[10.28,3.76],.45,.32,'red')
 beam('guard','guard_elbow',[10.28,3.76],[9.72,3.30],.45,.32,'red')
 beam('guard','guard_free_tip',[9.72,3.30],[8.82,4.04],.48,.40,'red_edge','guard')
 beam('guard','trigger',[10.67,5.70],[9.57,5.64],.24,.20,'black')
 # A pair of actual controls; their screws and engraving stay in UV.
 for x in (7.10,8.90):
  box('controls','selector_hub_'+str(x),[x,11.19,5.39],[.22,.60,.60],'steel','control',('x',45))
  beam('controls','selector_lever_'+str(x),[11.18,5.39],[10.63,6.08],.23,.24,'steel','control',x=x)
 inputs=[SOURCE,BASE,REFS,HELPER]
 # Display derivatives are read only provenance, not a migration-manifest pin.
 inputs += [str(p.relative_to(ROOT)) for p in sorted((ROOT/(ASSET+'models/weapon/sidearm')).glob('high_albedo_*.json'))]
 return dict(id=ID,revision='W143',method='authored_semantic_filled_solids_face_uv',source=meta,
  source_matching=dict(objects=len(meshes),triangles=sum(len(m['faces']) for m in meshes),w30_triangles=meta['source_triangles'],triangle_difference=sum(len(m['faces']) for m in meshes)-meta['source_triangles'],basis='stored Blender object matrix; world X,Z,Y * source scale + anchor'),
  identity=['blue upper receiver and sloping carry bridge','red lower frame and substantial slanted grip','orange cruciform muzzle brace','exposed black upper barrel within red cage','knurled lower cylinder and original source decals'],
  geometry_rationale=dict(receiver='Broad filled masses preserve transverse depth and grip anchor.',barrel='Octagonal walls keep actual bores; solid breech closes their recessed rear.',cylinder='Eight knurled walls and eight nozzle walls model the forward cylinder, with a solid rear closure.',cage='Open rails/posts frame the exposed barrel in side and oblique views.',brace='Cross lugs and bridge preserve the distinctive orange/blue muzzle silhouette.',grip='Thick core, slanted backstrap and heel preserve hand frame; grooves are UV.',guard='Swept open-bottom guard as in source; no opaque panel crosses finger clearance.'),
  parts=parts,palette=PALETTE,full_only=True,source_frame_unchanged=True,
  openings=dict(guard=[8,9.9,4.8],carry_slot=[8,14.1,-.45],cage_window=[8,13.82,2.0]),
  bore_probes=[dict(name='upper_muzzle',center=[8,13.16],z_range=[-1.70,4.25],back=[8,13.16,4.55]),dict(name='lower_nozzle',center=[8,11.38],z_range=[-3.50,.40],back=[8,11.38,.60])],
  filled_probes=dict(receiver=[8,12.9,8.5],lower_frame=[8,11.6,7.5],grip=[8,8.65,7.85]),
  input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in [RAW/'High Albedo.blend',RAW/'High Albedo Main_Diffuse.dds',RAW/'High Albedo Decals_Diffuse.dds',PHOTO]},
  limitations=['Authored matte default paint is not original PBR reconstruction.','Minor screws, grip relief, housing channels and knurl are face UV, not perforations.','Octagonal barrel/cylinder and simplified brace approximate curved source surfaces.','Static full model retains generic reload; no new split reload or moving cylinder.','Offline orthographic comparisons do not certify native views, pack load, ADS or performance.'])

def world_points(e,face,w,h):
 p=vertices(e)[list(FACES[face])];u=(np.arange(w)+.5)/w;v=(np.arange(h)+.5)/h
 return p[0]+u[None,:,None]*(p[1]-p[0])+v[:,None,None]*(p[3]-p[0])

# Source decal graphics only; opaque main diffuse is not projected onto the solids.
_DECALS=None
def decal_paint(rgb,points,face):
 global _DECALS
 if face not in ('east','west'):return rgb
 if _DECALS is None:
  meshes,_=source_meshes();m=next(m for m in meshes if m['material']=='High Albedo Decals')
  _DECALS=(m,np.asarray(Image.open(RAW/'High Albedo Decals_Diffuse.dds').convert('RGB')))
 m,tex=_DECALS
 for ps,uv in zip(m['vertices'][m['faces']],m['uv']):
  # Decal cards must face the same side. Avoid reflected typography.
  side=np.mean(ps[:,0])-8
  if (face=='east' and side<.1) or (face=='west' and side>-.1):continue
  a,b,c=ps[:,1:];den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-8:continue
  py,pz=points[:,:,1],points[:,:,2]
  wa=((b[1]-c[1])*(py-c[0])+(c[0]-b[0])*(pz-c[1]))/den
  wb=((c[1]-a[1])*(py-c[0])+(a[0]-c[0])*(pz-c[1]))/den;wc=1-wa-wb
  mask=(wa>=0)&(wb>=0)&(wc>=0)
  q=wa[:,:,None]*uv[0]+wb[:,:,None]*uv[1]+wc[:,:,None]*uv[2]
  tx=np.clip((q[:,:,0]*tex.shape[1]).astype(int),0,tex.shape[1]-1);ty=np.clip((q[:,:,1]*tex.shape[0]).astype(int),0,tex.shape[0]-1)
  rgb[mask]=tex[ty,tx][mask]
 return rgb

def tile(s,face,w,h):
 p=world_points(s['geometry'],face,w,h);x,y,z=p[:,:,0],p[:,:,1],p[:,:,2]
 yy,xx=np.mgrid[:h,:w];edge=np.minimum.reduce([xx,yy,w-1-xx,h-1-yy])
 base=np.array(PALETTE[s['material']],float)
 # Restrained deterministic material grain, with broad paint rather than baked shadows.
 grain=(np.sin(x*73+y*89+z*43)+np.sin(x*121-y*97+z*29))*.65
 rgb=np.broadcast_to(base,(h,w,3)).copy()+grain[:,:,None]
 rgb+=np.where(edge<1,8,np.where(edge<2,-6,0))[:,:,None]
 motif=s['motif'];side=face in ('east','west')
 if motif=='knurl':
  # Cross-hatched knurl is UV detail across the octagonal facets.
  a=np.mod((x+y)*20+z*18,2);b=np.mod((x+y)*20-z*18,2)
  k=np.minimum(abs(a-1),abs(b-1));rgb+=np.where(k<.14,18,-3)[:,:,None]
 if motif in ('barrel','nozzle'):
  line=(np.abs(np.mod(z*2.5,1)-.5)<.055);rgb[line]-=13
 if side and motif=='housing':
  # Continuous stepped recessed channel and lower frame seam, both sides.
  bend=13.15+np.clip((9.74-z)*.75,0,.57)
  channel=(z>9.02)&(z<9.82)&(np.abs(y-bend)<.105)
  rgb[channel]=[33,69,89]
  rim=(z>9.02)&(z<9.82)&(np.abs(y-bend-.12)<.035);rgb[rim]=[103,161,187]
  slot=((z>10.30)&(z<10.46)&(y>12.99)&(y<13.64));rgb[slot]=[30,59,73]
 if side and motif=='reservoir':
  end=(z<5.95)|(z>7.20)
  bars=(np.mod(z*6+y*3,1)<.35)&end&(y<13.26);rgb[bars]=[43,44,39]
 if side and motif=='frame':
  seam=(y<11.32)&(y>11.24);rgb[seam]=[72,23,21]
  # Two shallow stamped diagonal pressings, no extra coplanar cubes.
  groove=(np.abs(y-(.32*(z-7)+11.27))<.045)&(z>7)&(z<9.7)
  rgb[groove]=[103,26,24]
 if side and motif in ('grip','backstrap'):
  # Contoured grip inset and lower longitudinal tool grooves from the reference.
  line=(np.abs(z-(8.58-.31*(y-8.1)))<.045)&(y>6.9)&(y<9.8)
  rgb[line]=np.array(PALETTE[s['material']])*.42
  for cy,cz in (((7.03,8.65),(8.91,8.10)) if motif=='backstrap' else ()):
   r=np.sqrt(((y-cy)/.34)**2+((z-cz)/.35)**2)
   ring=(r>.78)&(r<1.08);rgb[ring]=[27,36,40]
   inside=r<.75;rib=np.mod((z+y*.30)*15,1)<.23;rgb[inside]=[49,60,65];rgb[inside&rib]=[20,27,30]
 if motif in ('control','rail','brace','collar'):
  # Existing hardware accents, bounded to the broad face, not random wear.
  if w>10 and h>10:
   rr=((xx-w*.23)/2.0)**2+((yy-h*.5)/2.0)**2
   rgb[rr<1]=[32,35,34];rgb[(rr>=1)&(rr<2)]=base*.65
 if side and s['group'] in ('receiver','frame','cylinder'):
  rgb=decal_paint(rgb,p,face)
 return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(25,29,33,255));requests=[]
    for spec in d['parts']:
        e=spec['geometry']
        for face in FACES:
            p=vertices(e)[list(FACES[face])];density=24
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,e['name'],face,spec))
    requests.sort(key=lambda r:(-r[0],-r[1],r[2],r[3]));x=y=2;row=0;ledger=[];uvs={}
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow '+name)
        im=tile(spec,face,w,h);atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        uvs[(name,face)]=[v*16/EDGE for v in [x,y,x+w,y+h]];ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    elements=[]
    for spec in d['parts']:
        e=copy.deepcopy(spec['geometry']);e['faces']={f:dict(uv=uvs[(e['name'],f)],texture='#0') for f in FACES};elements.append(e)
    d['atlas']=dict(size=EDGE,gutter=2,used_height=y+row+2,face_islands=len(ledger),islands=ledger)
    return atlas,dict(credit='W143 High Albedo / authored solids / opaque default dye face atlas',
        textures={'0':'destiny:item/weapon/w123/high_albedo','particle':'destiny:item/weapon/w123/high_albedo'},
        elements=elements,display=json.loads((ROOT/BASE).read_bytes())['display'])

def model_triangles(model,atlas):
    m=copy.deepcopy(model)
    for e in m['elements']:
        if 'rotation' in e:
            r=e['rotation'];e['rotation']=dict(origin=r['origin'],**{r['axis']:r['angle']})
    return H['model_triangles']({'full':m},atlas)

def inspection(d,model,atlas):
    es=[];groups=[]
    for group in sorted({s['group'] for s in d['parts']}):
        children=[];names={s['geometry']['name'] for s in d['parts'] if s['group']==group}
        for e in model['elements']:
            if e['name'] not in names:continue
            b=copy.deepcopy(e);r=b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),origin=r['origin'] if r else [8,8,8],rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],box_uv=False,autouv=0)
            for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
            es.append(b);children.append(b['uuid'])
        groups.append(dict(name=group,uuid=uid(group),origin=[8,8,8],rotation=[0,0,0],children=children,export=True))
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='High Albedo W143 owned inspection',resolution={'width':EDGE,'height':EDGE},elements=es,outliner=groups,
        textures=[dict(name='high_albedo.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=copy.deepcopy(model['display']))

def comparison(d,meshes,atlas,model):
 w,h=1000,455;sheet=Image.new('RGB',(3000,2260),'#19212a');draw=ImageDraw.Draw(sheet)
 def label(x,y,s,size=23):draw.text((x,y),s,fill='#e4ebed',font_size=size)
 label(24,12,'HIGH ALBEDO W143 / FILLED SEMANTIC VOLUMES + CLEAN FACE UV',32)
 photo=Image.open(PHOTO).convert('RGB');photo.thumbnail((1100,580));sheet.paste(photo,(0,60))
 lines=[f'{len(model["elements"])} opaque authored cuboids / 0 triangles / 0 alpha shells',
  'Blue upper receiver, red filled frame and slanted grip, orange brace',
  'Real upper bore + lower nozzle + trigger clearance + carry slot',
  'Original source graphics sampled only on decal-bearing side faces',
  f'Inert source: 2 accepted objects / {d["source_matching"]["triangles"]:,} triangles; W30 difference 0',
  'Canonical dirty-seeded model: 253 cuboids, read only',
  'Same source scale / anchor / axes / exact canonical display',
  'ADS + twohand + generic reload retained; no split reload added',
  'Offline diffuse CPU comparison; native and PBR acceptance pending']
 for i,line in enumerate(lines):label(1135,90+i*48,line)
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/high_albedo.png'))
 ts=[source_triangles(meshes),model_triangles(old,oldtex),model_triangles(model,atlas)]
 points=np.concatenate([m['vertices'] for m in meshes])
 for col,s in enumerate(['ACCEPTED RAW / UNDYED DIFFUSE','DIRTY-SEEDED CANONICAL / 253 CUBOIDS',f'W143 / {len(model["elements"])} SEMANTIC SOLIDS']):label(col*w+18,600,s,22)
 for row,(s,cam) in enumerate([('SIDE',[1,0,0]),('MUZZLE OBLIQUE',[1,.35,-.65]),('REAR OBLIQUE',[-1,.30,.60])]):
  ext=H['frame'](points,cam,w,h)
  for col,tris in enumerate(ts):
   im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);sheet.paste(im,(col*w,640+row*h));label(col*w+15,647+row*h,s,18)
 # Axial render demonstrates geometric air channels, not just black painted circles.
 cam=[0,0,-1];ext=H['frame'](np.array([[6.6,10.6,-3.5],[9.4,14.6,-1]]),cam,620,230)
 im,_=H['render'](ts[2],cam,ext,(620,230));sheet.paste(im,(25,2020));label(20,2005,'AXIAL / TWO RECESSED OPENINGS',18)
 # A close oblique crop uses the same authored model, with no source overlay.
 crop_points=np.array([[6.6,10.5,-3.6],[9.4,14.6,1.3]])
 cam=[.4,.10,-1];ext=H['frame'](crop_points,cam,770,230)
 im,_=H['render'](ts[2],cam,ext,(770,230));sheet.paste(im,(690,2020));label(690,2005,'MUZZLE CLOSE / FACETED WALLS',18)
 thumb=atlas.copy();thumb.thumbnail((300,300));sheet.paste(thumb.convert('RGB'),(1500,1940))
 label(1830,2035,'1024 atlas / independent face rectangles + 2px gutters',22)
 label(1830,2080,'Knurl, panel channels and grip relief are UV detail.',22)
 label(1830,2125,'Actual native views and 10-20 display check: master.',22)
 return png(sheet)

def review_text(d,counts):
 return f"""# High Albedo W143 art review

{sum(counts.values())} assembled opaque authored cuboids, 0 triangle adapters, {sum(counts.values())*6} faces. Group counts: {json.dumps(counts,sort_keys=True)}. The 1,000-element cap is a ceiling; the first blockout was 92 elements and the source-visible stepped barrel collar adds eight justified pieces. No rip-island transfer, voxel shell, alpha silhouette, or invented triangle schema.

Identity: blue upper receiver and sloped carry bridge, red filled lower frame and slanted grip, orange cruciform front brace and cylinder band, black exposed upper barrel in red cage, forward knurled cylinder. Large receiver, frame and grip cores are filled intersecting solids; octagonal tube walls are reserved for actual cylindrical bores. Trigger guard follows the source's open lower end. The upper mouth, lower nozzle, carry slot and cage window are geometric openings. The bore closures are recessed inside the source frame.

Face atlas: 1024 square opaque RGBA; coherent blue/red/orange material blocks, pressed housing channels, grip relief, restrained edge accents, knurl and small hardware in UV. Two-pixel edge gutters per face. Original accepted Decals mesh UVs provide only original side graphics (303 / SD / warning labels); the Main diffuse is not baked across the new body. Source typography follows its stored UV orientation instead of mirroring a new wordmark. Paint is a matte interpretation of the actual W31 defaultphoto, not original PBR recovery.

Source provenance: inert Blender 2.91 SDNA reader adapted from the read-only Long Arm helper, with explicit version support and source-specific acceptance. Exactly two W30 accepted mesh objects, 10,378 Main + 26 Decals = 10,404 triangles. W30 count difference: zero. Stored object matrices and world X,Z,Y mapping, original scale {d['source']['scale']} and anchor [8,8,8], are used directly; no recenter/renormalization. Source bounds are verified before authored geometry. The semantic envelope has small local differences recorded in manifest.json rather than being reported as exact source geometry.

Exact canonical display copied from the dirty-seeded sidearm model. Existing ADS/twohand/inspect models, generic reload, shared routing, gameplay, Java, HUD and audio are untouched. Full-only output; no new moving magazine or split reload.

comparison.png contains the actual defaultphoto, accepted undyed source, dirty-seeded 253-cube canonical model, and new model at identical source-derived side/front/rear camera scales, plus axial muzzle and atlas views. It is a CPU diffuse rendering, not a native screenshot. Worker opened and inspected the generated image; Blockbench UI review and native first/third person, ADS, generic reload and 10-20 simultaneous displays remain with master. Focused practical checks are documented in the worker report; no exhaustive certification is claimed.

Limitations: simplified faceted cylinders and brace profile; shallow grooves/knurl/screws are paint. No native pack-load, DCC, dynamic PBR, performance or gameplay acceptance is asserted.
"""

def generate(include_comparison=True):
 meshes,meta=source_meshes();d=make_design(meta,meshes);atlas,model=compile_model(d)
 counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()))
 out={ART+'design.json':encode(d),TEXTURE:png(atlas),MODEL:encode(model),ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
 if include_comparison:out[ART+'comparison.png']=comparison(d,meshes,atlas,model)
 pts=np.concatenate([vertices(e) for e in model['elements']]);bounds=[pts.min(0).tolist(),pts.max(0).tolist()]
 assert 0<len(model['elements'])<=1000
 manifest=dict(id=ID,revision='W143',method=d['method'],assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),triangle_adapter_elements=0,alpha_body_elements=0,emitted_faces=6*len(model['elements']),max_assembled_elements=1000,groups=counts,texture_size=[EDGE,EDGE],actual_bounds=bounds,source_bounds=meta['model_bounds'],bounds_delta=(np.array(bounds)-meta['model_bounds']).tolist(),source_scale=meta['scale'],source_anchor=meta['anchor'],source_axis=meta['source_axis'],source_matching=d['source_matching'],canonical_seed_elements=len(json.loads((ROOT/BASE).read_bytes())['elements']),canonical_display_exact=True,source_frame_unchanged=True,full_only=True,native_accepted=False,pbr_accepted=False,default_photo_sha256=sha(PHOTO.read_bytes()),generator_sha256=sha((ROOT/SCRIPT).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()),input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],output_sha256={p:sha(data) for p,data in out.items()},limitations=d['limitations'])
 out[ART+'manifest.json']=encode(manifest);return out

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
 for path,data in generate().items():
  target=ROOT/path
  if args.verify:assert target.is_file() and target.read_bytes()==data,path
  else:target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(data)
 print('High Albedo W143', 'verified' if args.verify else 'generated')
if __name__=='__main__':main()
