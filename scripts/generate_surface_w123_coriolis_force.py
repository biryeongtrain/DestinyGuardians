#!/usr/bin/env python3
"""W144 Coriolis Force: inert original BLEND read, authored semantic solids, face UV."""
import argparse, base64, collections, copy, hashlib, io, json, math, re, runpy, struct, subprocess, uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='coriolis_force'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/fusion_rifle/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w123_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w144/{ID}-worker.md'
REFS='art/weapons/w31/references.json'
BATCH='docs/qa/2026-10-26/w144/batch.json'
RAW=Path('/tmp/destiny-weapons-w30/raw/coriolis_force/extracted')
PHOTO=Path('/tmp/destiny-weapons-w31/references/coriolis_force.jpg')
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER))
FACES=H['FACES']; EDGE=1024
PALETTE=dict(red=[201,40,31],redlight=[226,56,40],blue=[43,103,139],steel=[150,162,166],darksteel=[51,59,61],black=[22,27,29],yellow=[214,181,62],white=[203,215,213])
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w144:coriolis_force:'+n))
def vertices(e):return H['vertices'](e)

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
 meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30'];path=RAW/'Coriolis Force.blend'
 assert sha(path.read_bytes())==meta['source_files'][path.name]
 b=Blend(path);meshes=[];audit=[]
 for _,o in b.records('Object'):
  if b.field(o,'Object','type')!=1:continue
  name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
  mesh=b.pointed(b.field(o,'Object','data'));n=b.field(mesh,'Mesh','totvert')
  matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
  v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
  world=(np.c_[v,np.ones(n)]@matrix)[:,:3];native=world[:,[0,2,1]]*meta['scale']+meta['anchor']
  nl=b.field(mesh,'Mesh','totloop');loops=np.ndarray((nl,),'<i4',b.pointed(b.field(mesh,'Mesh','mloop')),strides=(b.sizes['MLoop'],))
  uvs=np.ndarray((nl,2),'<f4',b.pointed(b.field(mesh,'Mesh','mloopuv')),strides=(b.sizes['MLoopUV'],4)).astype(float);uvs[:,1]=1-uvs[:,1]
  polys=b.pointed(b.field(mesh,'Mesh','mpoly'));faces=[];uv=[]
  for i in range(b.field(mesh,'Mesh','totpoly')):
   start,count=struct.unpack_from('<ii',polys,b.sizes['MPoly']*i);assert count==3,(name,count)
   ix=[start,start+1,start+2];faces.append(loops[ix]);uv.append(uvs[ix])
  ptr=struct.unpack_from('<Q',b.pointed(b.field(mesh,'Mesh','mat')))[0]
  material=b.field(b.field(b.pointed(ptr),'Material','id'),'ID','name')[2:]
  retained=name in meta['source_objects'];assert retained or name in meta['excluded_objects'],name
  audit.append(dict(name=name,triangles=len(faces),material=material,retained=retained,reason='retained untextured Fusion plane' if material=='Fusion' else ('retained textured geometry' if retained else 'excluded duplicate Ret alternative')))
  if retained:meshes.append(dict(name=name,vertices=native,faces=np.array(faces),uv=np.array(uv),material=material,world_bounds=[world.min(0).tolist(),world.max(0).tolist()],object_matrix=matrix.tolist()))
 assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
 assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==13801
 assert sum(len(m['faces']) for m in meshes if m['material']!='Fusion')==meta['textured_triangles']==13799
 assert sum(a['triangles'] for a in audit)==13861
 pts=np.concatenate([m['vertices'] for m in meshes]);wb=np.array([m['world_bounds'] for m in meshes])
 np.testing.assert_allclose([wb[:,0].min(0),wb[:,1].max(0)],meta['source_bounds'],atol=1e-7,rtol=0)
 np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-7,rtol=0)
 reference=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID);assert sha(PHOTO.read_bytes())==reference['sha256']
 return meshes,meta,audit

def source_triangles(meshes):
 textures={m:np.asarray(Image.open(RAW/(m+'_Diffuse.dds')).convert('RGBA')) for m in ('Coriolis Force Main','Coriolis Force Scope')};result=[]
 for m in meshes:
  if m['material']=='Fusion':continue # exactly two untextured triangles, explicitly audited
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
   result.append((p,uv,textures[m['material']],n/max(length,1e-20)))
 assert len(result)==13799
 return result

def make_design(meta,audit):
 parts=[]
 def c(name,pos,size,mat,group,motif='plain',turn=None):
  e=dict(name=name,**{'from':[round(a-b/2,7) for a,b in zip(pos,size)],'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
  e['rotation']=dict(origin=list(pos),x=0,y=0,z=0)
  if turn:e['rotation'][turn[0]]=turn[1]
  parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
 def beam(name,a,b,width,depth,mat,group,motif='plain',x=8):
  z0,y0=a;z1,y1=b;angle=-math.degrees(math.atan2(y1-y0,z1-z0))
  c(name,[x,(y0+y1)/2,(z0+z1)/2],[width,depth,math.hypot(y1-y0,z1-z0)],mat,group,motif,('x',angle))
 def cylinder(name,y,z0,z1,r,mat,group,motif='plain',x=8):
  for i in range(4):c(name+f'_octant_{i}',[x,y,(z0+z1)/2],[2*r*math.cos(math.pi/8),2*r*math.sin(math.pi/8),z1-z0],mat,group,motif,('z',i*45))
 def tube(name,y,z0,z1,r,t,mat,group):
  for i in range(8):
   q=math.radians(i*45);rr=r-t/2
   c(name+str(i),[8-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],[2*r*math.tan(math.pi/8)+.008,t,z1-z0],mat,group,'muzzle',('z',i*45))
 # Long silver barrel and open dark muzzle. Four intersecting rectangles fill one octagon.
 cylinder('silver_barrel',13.88,-10.13,-4.18,.405,'steel','barrel','barrel')
 tube('open_muzzle_',13.88,-10.9713429465,-10.22,.43,.12,'darksteel','muzzle')
 c('bore_backstop',[8,13.88,-10.18],[.62,.62,.10],'black','muzzle')
 beam('blue_barrel_bed',[-10.62,13.37],[-4.10,13.37],.94,.32,'blue','barrel','barrel_label')
 beam('blue_nose_scoop',[-10.68,13.4],[-10.23,13.15],.98,.26,'blue','barrel')
 # Paired thin insulated cables rise to the long upper sleeve.
 for x in (7.76,8.24):
  beam('cable_forward'+str(x),[-10.48,14.29],[-5.92,14.32],.075,.075,'darksteel','cables',x=x)
  beam('cable_rise'+str(x),[-5.92,14.32],[-4.52,14.72],.075,.075,'darksteel','cables',x=x)
  beam('cable_rear'+str(x),[-4.52,14.72],[-3.95,14.72],.075,.075,'darksteel','cables',x=x)
 cylinder('insulated_chamber',13.84,-4.32,-1.18,.61,'black','chamber','insulator')
 cylinder('blue_coupling',13.86,-1.25,.10,.72,'blue','coupler','coupler')
 c('coupling_lower_lug',[8,13.26,-.61],[1.02,.65,.39],'blue','coupler')
 c('coupling_side_control',[7.2336445,13.96,-.52],[.28,.24,.45],'darksteel','coupler','control')
 c('coupling_control_end',[7.2036445,13.96,-.78],[.22,.28,.16],'black','coupler')
 # Ribbed red top shroud, two distinct upright sight ears with real sight air.
 c('upper_red_shroud',[8,14.70,-2.62],[1.50,.49,3.76],'red','top_shroud','shroud')
 for z in (-4.18,-3.42,-2.66,-1.90):
  c('shroud_bridge'+str(z),[8,14.98,z],[1.62,.19,.16],'redlight','top_shroud')
  for sx in (-1,1):c('shroud_side_rib'+str(z)+str(sx),[8+sx*.73,14.55,z],[.17,.69,.18],'red','top_shroud')
 c('shroud_rear_transition',[8,14.85,-.92],[1.22,.43,.85],'red','top_shroud','warning')
 for sx in (-1,1):c('sight_ear'+str(sx),[8+sx*.53,15.30,-.35],[.16,.858303398,.30],'red','sight')
 c('rear_sight_sill',[8,14.56,1.24],[1.13,.24,1.05],'red','sight','warning')
 # Front handguard is a load-bearing loop with two true open windows.
 c('handguard_upper',[8,13.01,-6.73],[1.52,.43,6.70],'red','handguard','front_top')
 c('handguard_lower',[8,11.30,-6.57],[1.48,.57,5.88],'red','handguard','front_decals')
 beam('handguard_nose',[-10.10,12.91],[-10.10,11.93],1.45,.41,'red','handguard')
 beam('handguard_nose_curve',[-10.10,11.93],[-9.72,11.42],1.45,.42,'red','handguard')
 beam('handguard_toe',[-9.72,11.42],[-9.28,11.30],1.45,.44,'red','handguard')
 c('handguard_divider',[8,12.15,-7.08],[1.22,1.40,.34],'red','handguard','panel')
 c('handguard_rear_post',[8,12.11,-3.91],[1.39,1.49,.36],'red','handguard')
 # Triangular small front aperture has a diagonal structural sill.
 beam('front_window_diagonal',[-8.77,11.66],[-7.40,12.89],1.15,.23,'red','handguard')
 c('handguard_inner_rest',[8,11.66,-5.47],[.67,.14,1.23],'darksteel','handguard','grip')
 # Continuous action spine and deep solid black cartridge behind the red triangular surround.
 c('receiver_spine',[8,12.39,-.74],[1.58,1.14,5.70],'red','receiver','receiver')
 c('receiver_top_land',[8,13.05,.55],[1.37,.21,3.30],'redlight','receiver')
 c('cartridge_solid',[8,8.42,.02],[.876,5.25,4.42],'black','cartridge','cartridge')
 c('cartridge_upper',[8,10.95,-.52],[.88,.52,4.57],'darksteel','cartridge')
 beam('cartridge_floor',[-3.16,5.72],[2.72,5.72],1.58,.18,'black','cartridge','base')
 beam('cartridge_front_toe',[-3.16,5.72],[-3.42,6.06],1.40,.15,'black','cartridge')
 beam('triangle_front',[-2.06,9.83],[-.70,6.63],1.37,.51,'red','triangle','grip')
 beam('triangle_upper',[-2.61,10.32],[1.70,11.68],1.39,1.05,'red','triangle','panel')
 beam('triangle_rear',[1.70,11.55],[3.98,5.79],1.44,.59,'red','triangle','grip')
 beam('triangle_bottom',[-.70,6.63],[3.98,5.79],1.40,.53,'red','triangle','panel')
 beam('forward_grip_root',[-3.60,11.52],[-2.65,9.30],1.45,.40,'red','triangle','receiver_decals')
 c('coupler_receiver_link',[8,13.72,1.01],[1.26,1.10,2.05],'red','receiver','panel')
 # Main red shoulder cage; all long rails have substantial thickness and true daylight.
 c('rear_receiver',[8,13.92,3.54],[1.64,1.26,3.68],'red','rear_receiver','rear_panel')
 c('rear_lower_action_rail',[8,11.81,4.38],[1.54,.61,5.61],'red','rear_receiver','panel')
 cylinder('rear_action_tube',13.02,1.75,6.55,.35,'darksteel','rear_receiver','tube')
 c('rear_grip_socket',[8,11.56,6.79],[1.38,1.24,1.14],'red','grip','panel')
 c('rear_upper_rail',[8,14.38,9.53],[1.48,.47,7.80],'red','stock','stock_top')
 c('rear_window_sill',[8,12.54,9.67],[1.40,.40,7.43],'red','stock','panel')
 c('rear_window_front',[8,13.47,6.25],[1.37,1.69,.37],'red','stock')
 cylinder('stock_inner_tube',13.36,6.42,13.26,.20,'darksteel','stock','tube')
 c('butt_upper_corner',[8,14.17,13.55],[1.52,.65,.63],'red','stock','butt')
 c('butt_vertical',[8,11.31,13.62],[1.54,5.41,.77],'red','stock','butt')
 beam('butt_lower_curve',[13.62,8.70],[13.25,8.29],1.50,.56,'red','stock','butt')
 beam('lower_stock_rail',[3.98,5.79],[13.25,8.29],1.39,.51,'red','stock','stock_decals')
 beam('butt_pad',[14.00,8.73],[14.00,14.23],1.34,.07,'darksteel','stock','pad')
 # Pistol grip hangs within the large stock opening; curved trigger is separate.
 beam('rear_grip',[7.00,10.82],[8.15,7.18],1.14,.97,'red','grip','grip')
 beam('rear_grip_front',[6.82,10.61],[7.86,7.41],1.16,.27,'black','grip','rubber')
 beam('grip_heel',[7.67,7.15],[8.78,7.47],1.26,.28,'red','grip')
 beam('grip_upper_haunch',[6.35,11.68],[7.00,10.82],1.40,.76,'red','grip','panel')
 beam('trigger_root',[6.75,11.62],[6.61,11.05],.22,.23,'black','trigger')
 beam('trigger_hook',[6.61,11.05],[6.44,10.72],.22,.21,'black','trigger')
 beam('trigger_toe',[6.44,10.72],[6.15,10.67],.22,.19,'black','trigger')
 # Asymmetric raised red U clamp corresponds to the original 1,072-triangle positive-X object.
 beam('u_clamp_front',[2.21,14.39],[2.42,12.38],.49,.38,'red','u_clamp',x=9.12)
 beam('u_clamp_front_elbow',[2.42,12.38],[2.82,12.05],.49,.38,'red','u_clamp',x=9.12)
 beam('u_clamp_floor',[2.82,12.05],[5.97,12.05],.49,.38,'red','u_clamp','clamp',x=9.12)
 beam('u_clamp_rear_elbow',[5.97,12.05],[6.47,12.51],.49,.38,'red','u_clamp',x=9.12)
 beam('u_clamp_rear',[6.47,12.51],[6.49,14.37],.49,.38,'red','u_clamp',x=9.12)
 for z in (2.21,6.49):c('clamp_cross_cleat'+str(z),[8.92,14.33,z],[.966317996,.30,.53],'red','u_clamp')
 # Source photographs place the small control block above the forward grip root.
 c('left_control_housing',[7.13,11.69,-2.95],[.22,.49,1.38],'darksteel','receiver','receiver_decals')
 inputs=[BASE,SOURCE,HELPER,REFS,ASSET+'textures/item/weapon/w30/coriolis_force.png']+[BASE.replace('.json',s+'.json') for s in ('_ads','_twohand','_ads_twohand','_inspect','_inspect_twohand')]
 raws=[RAW/'Coriolis Force.blend',PHOTO]+[RAW/(m+'_Diffuse.dds') for m in ('Coriolis Force Main','Coriolis Force Scope')]
 return dict(id=ID,revision='W144',family='fusion_rifle',parts=parts,palette=PALETTE,source=meta,source_audit=audit,
  construction='Authored long semantic filled cuboids and octagonal solids; no polygon/voxel/island conversion, alpha body plates or custom triangles',
  full_only=True,source_mapping='Blender 2.91 SDNA + stored obmat; native = world[X,Z,Y] * W30 scale + W30 anchor; both bounds independently verified',
  identity=['red open rectangular stock and two foregrip windows','silver barrel and blue coupling/bed','red ribbed top and twin open sight ears','deep black cartridge behind triangular red surround','positive-X raised U clamp and suspended rear grip','original Off World Systems decals sampled from Scope DDS'],
  openings=dict(front_small=[8,12.35,-9.20],front_large=[8,12.25,-5.60],rear_large=[8,9.7,10.5],rear_upper=[8,13.92,10.3],trigger=[8,10.6,5.7]),
  axial_openings=dict(muzzle=[8,13.88,-10.65],sight=[8,15.30,-.35]),
  filled_probes=dict(cartridge=[8,8.7,.4],receiver=[8,12.4,0],barrel=[8,13.88,-7],stock=[8,11.0,13.6],grip=[8,8.7,7.67]),
  source_matching=dict(objects=5,all_objects=7,retained_triangles=13801,textured_triangles=13799,retained_untextured_fusion=2,excluded_reticle_triangles=60,all_triangles=13861),
  atlas=dict(size=EDGE,gutter=2),default_photo_sha256=sha(PHOTO.read_bytes()),input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs},raw_input_sha256={str(p):sha(p.read_bytes()) for p in raws},
  limitations=['Offline CPU evidence only; native parser/held/ADS/twohand/charge/reload/audio/10-20 displays pending master.',
   'Neutral original DDS is material/marking evidence, authored red and blue finish follows default photo; no PBR recovery.',
   'Faceted rounded corners/cylinders; small fasteners and panel grooves are face UV.',
   'Central triangular dark area is backed by the actual solid cartridge, not a through-hole; true front/rear frame apertures remain open.',
   'Two retained Fusion triangles lack a texture and are audited separately; duplicate Ret alternatives excluded as W30.'])

DECALS=[ # scope DDS rect, native side z range, y range; original asymmetry retained
 ((8,394,168,482),(-8.16,-7.47),(11.04,11.54)),
 ((332,374,503,503),(-7.18,-6.66),(11.06,11.51)),
 ((518,24,711,84),(-3.56,-2.44),(11.53,11.88)),
 ((518,412,714,507),(-7.78,-5.20),(13.34,13.60)),
 ((8,394,168,482),(4.55,5.48),(6.02,6.51)),
 ((332,374,503,503),(5.75,6.52),(6.37,6.85)),
 ((516,172,744,403),(13.28,13.95),(10.1,11.75)),
 ((745,177,948,255),(12.05,12.95),(14.16,14.47))]

_DECAL_TEX=None
def decal_texture():
 global _DECAL_TEX
 if _DECAL_TEX is None:_DECAL_TEX=np.asarray(Image.open(RAW/'Coriolis Force Scope_Diffuse.dds').convert('RGB'))
 return _DECAL_TEX

def tile(s,face,w,h):
 u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
 ps=vertices(s['geometry'])[list(FACES[face])];p=ps[0]+u[:,:,None]*(ps[1]-ps[0])+v[:,:,None]*(ps[3]-ps[0]);x,y,z=p[:,:,0],p[:,:,1],p[:,:,2]
 base=np.array(PALETTE[s['material']],float);rgb=np.broadcast_to(base,(h,w,3)).copy();side=face in ('east','west')
 edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);cyl='_octant_' in s['geometry']['name']
 if not(cyl and face in ('north','south')):
  rgb*=(.97+.035*np.cos(v*math.pi))[:,:,None];rgb[edge<.70]*=.76;rgb[(edge>=.70)&(edge<1.45)]*=1.13
 mat=s['material'];motif=s['motif']
 if side and mat.startswith('red'):
  rgb[(edge>2.6)&(edge<3.35)]*=.71
  # Sparse, short authored edge scuffs; no random grain/noise over large paint fields.
  scuff=(edge<1.5)&(((z>-.4)&(z<-.18))|((z>4.92)&(z<5.11))|((z>12.12)&(z<12.29)))
  rgb[scuff]=[146,135,125]
 if motif=='grip' and side:
  rib=(np.mod(y+.32*z,.22)<.025)&(edge>4);rgb[rib]*=.76
 if motif=='rubber' and side:rgb[np.mod(y+.32*z,.20)<.025]*=.62
 if motif in ('insulator','cartridge') and side:
  rgb[np.mod(z+.7*y,.47)<.035]*=.68
 if motif=='barrel' and side:
  rgb[abs(y-14.03)<.022]=[186,195,197]
 if motif=='coupler' and side:
  rgb[(abs(z+.99)<.023)|(abs(z+.28)<.023)]*=.51
  r=np.hypot(z+.57,y-14.10);rgb[r<.065]=[31,49,58]
 if motif in ('rear_panel','receiver') and side:
  rgb[abs(y-12.42)<.027]*=.65
  for yy,zz in ((12.12,1.34),(13.95,3.4),(12.13,-2.0)):
   r=np.hypot(z-zz,y-yy);rgb[(r>.055)&(r<.075)]=[63,57,53];rgb[r<.035]=[36,37,35]
 if motif=='butt' and side:
  rgb[(abs(z-13.52)<.025)&(y>9.0)&(y<13.4)]*=.48
 if motif=='warning' and face=='up':
  mask=(abs(x-8)<.20)&(np.mod(z,.22)<.10);rgb[mask]=PALETTE['yellow']
 # The decal images use real source pixels. Composite only well-supported stickers,
 # never transfer the neutral/noisy surface or pretend it is default dye.
 if face=='west':
  tex=decal_texture()
  for rect,(z0,z1),(y0,y1) in DECALS:
   mask=(z>=z0)&(z<=z1)&(y>=y0)&(y<=y1)
   if not mask.any():continue
   a,b,c,d=rect;tx=np.clip((a+(z-z0)/(z1-z0)*(c-a)).astype(int),a,c-1);ty=np.clip((d-(y-y0)/(y1-y0)*(d-b)).astype(int),b,d-1)
   sample=tex[ty,tx];bg=(np.max(sample,axis=2)-np.min(sample,axis=2)<5)&(sample[:,:,0]>49)&(sample[:,:,0]<78)
   mask&=~bg;rgb[mask]=sample[mask]
 arr=np.empty((h,w,4),np.uint8);arr[:,:,:3]=np.clip(rgb,0,255);arr[:,:,3]=255
 return Image.fromarray(arr)

def face_points(e,face):return vertices(e)[list(FACES[face])]

def compile_model(d):
    atlas=Image.new('RGBA',(EDGE,EDGE),(18,25,31,255));requests=[]
    for spec in d['parts']:
        spec['geometry']['faces']={}
        for face in FACES:
            p=face_points(spec['geometry'],face);density=25
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,spec['geometry']['name'],face,spec))
    requests.sort(key=lambda q:(-q[0],-q[1],q[2],q[3]));x=y=2;row=0;ledger=[]
    for h,w,name,face,spec in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow')
        im=tile(spec,face,w,h)
        atlas.paste(Image.fromarray(np.pad(np.array(im),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        spec['geometry']['faces'][face]=dict(uv=[q*16/EDGE for q in (x,y,x+w,y+h)],texture='#0')
        ledger.append(dict(element=name,face=face,pixels=[x,y,x+w,y+h]));x+=w+4;row=max(row,h)
    d['atlas']=dict(size=EDGE,gutter=2,islands=ledger,used_texels=sum((q['pixels'][2]-q['pixels'][0])*(q['pixels'][3]-q['pixels'][1]) for q in ledger))
    model=dict(credit='W144 Coriolis Force / semantic filled solids and authored per-face UV / offline candidate',
        textures={'0':'destiny:item/weapon/w123/coriolis_force','particle':'destiny:item/weapon/w123/coriolis_force'},
        elements=[copy.deepcopy(s['geometry']) for s in d['parts']],display=json.loads((ROOT/BASE).read_bytes())['display'])
    assert len(model['elements'])<=1000
    return atlas,model

def inspection(d,atlas,model):
    elements=[];groups=collections.defaultdict(list)
    for spec,e in zip(d['parts'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation')
        b.update(type='cube',uuid=uid(e['name']),origin=r['origin'],rotation=[r[a] for a in 'xyz'],box_uv=False,autouv=0)
        for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        elements.append(b);groups[spec['group']].append(b['uuid'])
    return dict(meta={'format_version':'4.10','model_format':'free','box_uv':False},name='Coriolis Force W144 default-photo solids',
        resolution={'width':EDGE,'height':EDGE},elements=elements,
        outliner=[dict(name=g,uuid=uid('group:'+g),origin=[8,8,8],rotation=[0,0,0],children=v,export=True) for g,v in groups.items()],
        textures=[dict(name='coriolis_force.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
            source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],display=model['display'],
        destiny_w144={'nativeAccepted':False,'anchor':d['source']['anchor'],'scale':d['source']['scale'],'fullOnly':True})

def comparison(d,meshes,atlas,model):
 w,h=1000,400;sheet=Image.new('RGB',(3000,2040),'#151e27');dr=ImageDraw.Draw(sheet)
 dr.text((22,13),'CORIOLIS FORCE / W144 / ORIGINAL SOURCE + DEFAULT-DYE SEMANTIC REMODEL',fill='#e7edf0',font_size=30)
 photo=Image.open(PHOTO).convert('RGB').crop((870,245,1790,780));photo.thumbnail((900,415));sheet.paste(photo,(20,56))
 n=len(model['elements'])
 lines=[f'{n} emitted filled cuboids / 0 triangle adapters / {n*6} opaque UV faces',
  'Red structural cage / silver barrel / blue coupler and barrel bed',
  'Five verified source meshes: 13,801 retained triangles',
  '13,799 textured + 2 untextured Fusion; 60 duplicate Ret triangles excluded',
  'Original Blender 2.91 SDNA read only; stored object matrices; no DCC',
  'Source world and native bounds match W30; scale / anchor / display retained',
  'Central triangular recess is backed by solid black cartridge',
  'Offline CPU art inspection; native integration and game QA pending master']
 for i,line in enumerate(lines):dr.text((990,75+i*44),line,fill='#d1dee6',font_size=23)
 for x,label in [(22,'ORIGINAL RIP / neutral undyed DDS'),(1022,'W30 CANONICAL / 241 historical cuboids'),(2022,f'W144 / {n} SEMANTIC SOLIDS / default-photo finish')]:dr.text((x,480),label,fill='#e0eaf0',font_size=22)
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/coriolis_force.png'))
 arrays=[source_triangles(meshes),H['model_triangles']({'old':old},oldtex),H['model_triangles']({'full':model},atlas)]
 points=np.concatenate([m['vertices'] for m in meshes]);d['comparison_views']=[]
 for row,(label,cam) in enumerate([('SIDE / -X',[-1,0,0]),('MUZZLE THREE-QUARTER / -X',[-1,.38,-.65]),('REAR THREE-QUARTER / +X / raised U clamp',[1,.30,.62])]):
  extent=H['frame'](points,cam,w,h);d['comparison_views'].append(dict(name=label,camera=cam,center=extent[0].tolist(),scale=float(extent[1]),viewport=[w,h]))
  for col,tris in enumerate(arrays):
   im,_=H['render'](tris,cam,extent,(w,h),raw=col==0);sheet.paste(im,(col*w,512+row*h));dr.text((col*w+20,523+row*h),label,fill='#e1eaf0',font_size=18)
 for col,(label,groups,cam) in enumerate([
  ('OPEN MUZZLE / deep bore',('muzzle','barrel'),[-.35,.15,-1]),
  ('FRONT WINDOWS / actual air',('handguard',),[-1,.30,-.60]),
  ('RAISED U CLAMP / +X depth',('u_clamp','rear_receiver'),[1,.30,-.4]),
  ('CARTRIDGE / inset black solid',('cartridge','triangle'),[-1,.25,-.30])]):
  names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups};subset={'elements':[e for e in model['elements'] if e['name'] in names]}
  ps=np.concatenate([vertices(e) for e in subset['elements']]);tris=H['model_triangles']({'detail':subset},atlas)
  im,_=H['render'](tris,cam,H['frame'](ps,cam,750,270),(750,270));sheet.paste(im,(col*750,1720));dr.text((col*750+14,1730),label,fill='#e0e9ef',font_size=18)
 dr.text((22,2007),'Same camera and scale per comparison row. Original neutral DDS is not default dye. No game screenshot or native acceptance claimed.',fill='#ccd9e2',font_size=21)
 return png(sheet)

def review_text(d,model):
 n=len(model['elements'])
 return f'''# Coriolis Force W144 — offline product art review

The actual default-dye photo `{PHOTO}` was opened. The original pinned Blender 2.91 file and Main/Scope DDS were read as inert data; no embedded code, shader, DCC or game was executed. Source identity: red structural cage, two front handguard windows, rectangular open rear frame, suspended rear grip, silver forward barrel, blue coupling/bed, ribbed upper shroud, twin sight ears and the asymmetric positive-X U clamp. Supported Off World Systems stickers use cropped original Scope DDS pixels.

The design contains **{n} filled solid cuboids, {n*6} explicit opaque face UVs, zero triangle adapters and zero alpha body plates**, below the 1,000 assembled-element cap. Large rails, receiver and grips remain continuous solids. Long cylinders use four overlapping prisms with a filled octagonal section. The muzzle is an eight-wall physical bore with a recessed backstop. Source islands, voxel shells, screw cubes and random noise are not design units. Surface seams, fasteners and stickers use face UV. One 1024-square atlas has independent face islands with two-pixel extruded gutters.

The source five retained objects total exactly **13,801 triangles**: **13,799 textured** Main/Scope triangles and a **two-triangle untextured Fusion plane**. The two duplicate Ret alternatives (30 triangles each) are explicitly excluded following W30, so raw total is 13,861 across seven objects. Object labels match W30 here; none were silently skipped. SDNA stored matrices plus `[world.X, world.Z, world.Y] * scale + anchor` reproduce both W30 source and native bounds within 1e-7. No FBX axes from another weapon were assumed. The central triangular dark region has actual cartridge surfaces behind it; it is modeled as a recessed solid black cartridge within a red surround, while the handguard and rear frame windows are true openings.

Canonical `fusion_rifle/coriolis_force.json` is the full-only reference. Source scale `{d['source']['scale']}`, anchor `{d['source']['anchor']}`, native frame and exact canonical display are retained. Candidate: `{MODEL}`. Existing handhold/ADS/twohand/inspect/charge/generic reload/timings/sounds remain unchanged; no split resources or shared registries were edited. Master owns integration.

`comparison.png` contains the actual photo, original neutral-DDS source, W30 historical model and the candidate at shared scale/cameras for side and two obliques. Detail views show bore depth, front windows, asymmetric U clamp and cartridge recess. `inspection.bbmodel` embeds the complete final atlas and named editable cubes/groups. Both are deterministic generator outputs.

Caveats: circular surfaces and rounded corners are intentionally faceted. Reverse-side small decals are omitted where evidence is unavailable. The authored finish follows photo colors; it is not recovered PBR/refraction. The two untextured Fusion triangles are counted and audited, not rendered with an invented material. Offline renders establish art evidence only.

Native pending with master: resource parser and pack/registration/texture loading; first/third-person hand contact and twohand; ADS sight visibility; fusion charging/firing/muzzle effects/audio; generic reload ammo/timing/return; representative 10–20 simultaneous displays. No native/Gradle/CU/Vision/live-DCC/game screenshot result is claimed. See worker report for executed tests and export evidence.
'''

def generate(include_comparison=True):
 meshes,meta,audit=source_meshes();d=make_design(meta,audit);atlas,model=compile_model(d)
 points=np.concatenate([m['vertices'] for m in meshes]);d['comparison_views']=[]
 for label,cam in [('SIDE / -X',[-1,0,0]),('MUZZLE THREE-QUARTER / -X',[-1,.38,-.65]),('REAR THREE-QUARTER / +X / raised U clamp',[1,.30,.62])]:
  extent=H['frame'](points,cam,1000,400);d['comparison_views'].append(dict(name=label,camera=cam,center=extent[0].tolist(),scale=float(extent[1]),viewport=[1000,400]))
 bb=inspection(d,atlas,model);comp=comparison(d,meshes,atlas,model) if include_comparison else None
 products={MODEL:encode(model),TEXTURE:png(atlas),ART+'design.json':encode(d),ART+'inspection.bbmodel':encode(bb),ART+'review.md':review_text(d,model).encode()}
 if comp is not None:products[ART+'comparison.png']=comp
 n=len(model['elements']);pts=np.concatenate([vertices(e) for e in model['elements']])
 man=dict(id=ID,revision='W144',family='fusion_rifle',full_only=True,assembled_elements=n,opaque_cuboids=n,triangle_adapter_elements=0,alpha_body_elements=0,emitted_faces=n*6,
  groups=dict(Counter(s['group'] for s in d['parts'])),actual_bounds=[pts.min(0).round(7).tolist(),pts.max(0).round(7).tolist()],source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],canonical_display_exact=True,
  native_accepted=False,native_pending=['resource parser/pack load/registration','first/third person hand contact and twohand','ADS sight visibility','fusion charging/fire/muzzle/audio','generic reload return/ammo timing','10-20 simultaneous displays'],
  source_matching=d['source_matching'],default_photo_sha256=d['default_photo_sha256'],input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],generator_sha256=sha(Path(__file__).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()) if (ROOT/TEST).exists() else None,
  output_sha256={p:sha(b) for p,b in products.items()},limitations=d['limitations'])
 products[ART+'manifest.json']=encode(man);return products

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args();products=generate()
 owned=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w144-coriolis_force');assert set(products)<=set(owned)
 for p,b in products.items():
  q=ROOT/p
  if args.verify:assert q.is_file() and q.read_bytes()==b,'Deterministic mismatch: '+p
  else:q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 print(('Verified' if args.verify else 'Generated')+f' {len(products)} owned artifacts; '+str(json.loads(products[ART+'manifest.json'])['assembled_elements'])+' cubes')

if __name__=='__main__':main()
