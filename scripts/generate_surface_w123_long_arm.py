#!/usr/bin/env python3
"""Long Arm W142: authored filled solids and opaque face UV. Offline full-only product.
Inert SDNA decoding, no rip-script/shader/DCC execution. Writes only seven owned artifacts.
"""
import argparse, base64, copy, hashlib, io, json, math, re, runpy, struct, subprocess, uuid
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ID='long_arm'
ART=f'art/weapons/w123/{ID}/'
ASSET='src/main/resources/assets/destiny/'
BASE=ASSET+f'models/weapon/scout_rifle/{ID}.json'
MODEL=ASSET+f'models/weapon_surface_w123/{ID}.json'
TEXTURE=ASSET+f'textures/item/weapon/w123/{ID}.png'
SOURCE=f'art/blockbench/weapons/w30/{ID}.bbmodel'
SCRIPT=f'scripts/generate_surface_w123_{ID}.py'
TEST=f'scripts/qa/test_surface_w123_{ID}.py'
REPORT=f'docs/qa/2026-10-26/w142/{ID}-worker.md'
REFS='art/weapons/w31/references.json'
BATCH='docs/qa/2026-10-26/w142/batch.json'
RAW=Path('/tmp/destiny-weapons-w30/raw/long_arm/extracted/Long Arm')
PHOTO=Path('/tmp/destiny-weapons-w31/references/long_arm.jpg')
HELPER='scripts/generate_surface_w123_beloved.py'
H=runpy.run_path(str(ROOT/HELPER))
FACES=H['FACES']; EDGE=1024
PALETTE=dict(steel=[38,41,40],edge=[66,69,65],wood=[86,59,42],woodlight=[112,80,56],cloth=[175,165,141],gold=[185,155,67],black=[20,24,24])
def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w142:long_arm:'+n))
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
    """Inert SDNA reader adapted from W138; reads Blender 3.1 data only. Never imports bpy or source code."""
    def __init__(self,path):
        data=path.read_bytes()
        if data[:4]==b'\x28\xb5\x2f\xfd':
            data=subprocess.check_output(['rtk','proxy','zstd','-dc',str(path)])
        assert data[:12]==b'BLENDER-v301',data[:12]
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
    """Retained meshes only, stored matrices + SDNA strides, never bpy/shaders."""
    meta=json.loads((ROOT/SOURCE).read_bytes())['destiny_w30']
    path=RAW/"Long Arm.blend"
    assert sha(path.read_bytes())==meta['source_files']['Long Arm/'+path.name]
    b=Blend(path);meshes=[]
    for _,o in b.records('Object'):
        name=b.field(b.field(o,'Object','id'),'ID','name')[2:]
        if name not in meta['source_objects']:continue
        matrix=np.array(b.field(o,'Object','obmat')).reshape(4,4)
        mesh=b.pointed(b.field(o,'Object','data'));n=b.field(mesh,'Mesh','totvert')
        v=np.ndarray((n,3),'<f4',b.pointed(b.field(mesh,'Mesh','mvert')),
            offset=b.fields['MVert']['co'][0],strides=(b.sizes['MVert'],4)).astype(float)
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
        meshes.append(dict(name=name,vertices=native,faces=np.array(faces),uv=np.array(uv),material=material,
            world_bounds=[world.min(0).tolist(),world.max(0).tolist()],object_matrix=matrix.tolist()))
    pts=np.concatenate([m['vertices'] for m in meshes]);world=np.array([m['world_bounds'] for m in meshes])
    assert sorted(m['name'] for m in meshes)==sorted(meta['source_objects'])
    assert sum(len(m['faces']) for m in meshes)==meta['source_triangles']==21812
    np.testing.assert_allclose([world[:,0].min(0),world[:,1].max(0)],meta['source_bounds'],atol=1e-6,rtol=0)
    np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-6,rtol=0)
    ref=next(r for r in json.loads((ROOT/REFS).read_bytes()) if r['id']==ID)
    assert sha(PHOTO.read_bytes())==ref['sha256']
    return meshes,meta


def source_triangles(meshes):
 textures={m:np.asarray(Image.open(RAW/('LA'+m+'_Diffuse.png')).convert('RGBA')) for m in ('Frame','Sight','Bullet')};result=[]
 for m in meshes:
  for p,uv in zip(m['vertices'][m['faces']],m['uv']):
   n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-20)
   result.append((p,uv,textures[m['material']],n))
 return result

def make_design(meta,meshes):
 parts=[]
 def c(name,pos,size,mat,group,motif='plain',turn=None):
  e=dict(name=name,**{'from':[round(a-b/2,7) for a,b in zip(pos,size)],'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
  if turn:e['rotation']=dict(origin=list(pos),axis=turn[0],angle=turn[1])
  parts.append(dict(geometry=e,material=mat,group=group,motif=motif))
 def beam(name,a,b,width,depth,mat,group,motif='plain',x=8):
  z0,y0=a;z1,y1=b;angle=-math.degrees(math.atan2(y1-y0,z1-z0))
  c(name,[x,(y0+y1)/2,(z0+z1)/2],[width,depth,math.hypot(y1-y0,z1-z0)],mat,group,motif,('x',angle))
 def cylinder(name,y,z0,z1,r,mat,group,motif='plain'):
  a=2*r/(1+math.sqrt(2));pos=[8,y,(z0+z1)/2]
  c(name+'_core',pos,[a,2*r,z1-z0],mat,group,motif)
  c(name+'_cross',pos,[2*r,a,z1-z0],mat,group,motif)
  for sx in (-1,1):
   for sy in (-1,1):c(f'{name}_corner_{sx}_{sy}',[8+sx*a/2,y+sy*a/2,pos[2]],[a,a,z1-z0],mat,group,motif,('z',45))
 def tube(name,y,z0,z1,r,thick,mat,group,motif='rim'):
  for i in range(8):
   a=i*45;q=math.radians(a);rr=r-thick/2
   c(name+f'_{i}',[8-rr*math.sin(q),y+rr*math.cos(q),(z0+z1)/2],
     [2*r*math.tan(math.pi/8)+.006,thick,z1-z0],mat,group,motif,('z',a))
 # Six filled overlapping prisms give each long cylinder an octagonal cross-section.
 cylinder('upper_barrel',10.72,-8.56,3.64,.305,'steel','barrel','barrel')
 cylinder('lower_magazine_tube',9.72,-8.65,2.83,.245,'steel','lower_frame','tube')
 # Low actual muzzle is distinct from the raised barrel / bridged front sight.
 tube('muzzle',9.67,-10.52,-9.29,.285,.105,'steel','muzzle','muzzle')
 c('bore_recess_back',[8,9.67,-9.27],[.36,.36,.07],'black','muzzle')
 cylinder('muzzle_root',9.67,-9.30,-8.51,.32,'steel','muzzle','muzzle')
 # Open front crown, with a fine post through an air channel. Never a painted hole.
 for z,tag in [(-10.13,'nose'),(-8.69,'rear')]:
  for sx in (-1,1):c('front_crown_'+tag+str(sx),[8+sx*.245,10.63,z],[.15,.91,.18],'steel','front_sight','goldedge')
  c('front_crown_sill_'+tag,[8,10.14,z],[.65,.18,.26],'steel','front_sight','goldedge')
 c('front_sight_spine',[8,10.66,-9.43],[.095,.105,2.42],'black','front_sight','barrel')
 c('front_bridge_solid',[8,10.12,-9.28],[.75,.41,1.56],'steel','front_sight','receiver')
 # Two load-bearing bands bridge upper/lower rods, leaving long daylight windows.
 for z,tag in [(-5.62,'front'),(1.22,'rear')]:
  c('barrel_band_'+tag,[8,10.53,z],[.88,1.15,.49],'steel','bands','goldedge')
  c('barrel_band_roof_'+tag,[8,11.085,z],[.65,.17,.55],'edge','bands','goldedge')
  for sx in (-1,1):c('barrel_band_shoulder_'+tag+str(sx),[8+sx*.36,10.99,z],[.20,.20,.55],'steel','bands','goldedge',('z',sx*45))
 c('narrow_forward_tie',[8,10.33,-4.82],[.66,.82,.13],'steel','bands','plain')
 c('lower_bed_rail',[8,9.42,-3.35],[.61,.22,10.25],'black','lower_frame','tube')
 cylinder('under_rod',9.14,-6.79,-3.63,.115,'steel','lower_frame','tube')
 # Long forward wood keel has a continuous real section and changes slope only at stations.
 beam('wood_keel_front',[-10.769521,8.46],[-4.00,8.47],.59,.29,'woodlight','forewood','keel')
 beam('wood_keel_rise',[-4.10,8.48],[-2.80,8.68],.66,.38,'woodlight','forewood','keel')
 beam('wood_keel_rear',[-2.9,8.64],[3.78,8.30],.79,.63,'wood','forewood','wood')
 beam('forewood_swell',[-.10,8.80],[3.74,8.34],.91,1.02,'wood','forewood','wood')
 beam('forewood_back_chamfer',[2.95,8.13],[3.70,8.02],.74,.56,'wood','forewood','wood')
 beam('forewood_upper_fill',[-.10,9.02],[3.74,9.02],.86,.53,'wood','forewood','wood')
 # The substantial forward hand contact is continuous walnut; pale wrap is opaque UV.
 c('handguard_solid',[8,9.30,1.67],[.95,.60,4.60],'wood','handguard','wrapwood')
 c('handguard_top_land',[8,9.62,1.67],[.74,.16,4.60],'woodlight','handguard','wrapwood')
 for sx in (-1,1):c('handguard_top_bevel'+str(sx),[8+sx*.40,9.56,1.67],[.20,.20,4.60],'wood','handguard','wrapwood',('z',sx*45))
 for z,tag in [(-.61,'nose'),(3.89,'rear')]:c('handguard_cap_'+tag,[8,9.29,z],[1.0,.66,.14],'steel','handguard','goldedge')
 # Raised wood action cover, visibly separate from the broad lower forward wood.
 c('upper_wood_cover',[8,10.32,5.02],[.88,.52,4.90],'wood','upper_wood','upperwood')
 beam('upper_wood_nose',[2.40,10.25],[3.01,10.41],.81,.35,'wood','upper_wood','upperwood')
 c('upper_wood_roof',[8,10.62,5.42],[.70,.14,4.08],'woodlight','upper_wood','upperwood')
 # Receiver/action is full width; lower contour stops above both true guard openings.
 c('receiver_main',[8,9.40,5.98],[.93,1.00,4.22],'steel','receiver','receiver')
 c('receiver_upper_action',[8,9.95,6.18],[.82,.25,3.72],'edge','receiver','action')
 c('receiver_lower',[8,8.87,6.32],[.79,.25,3.35],'steel','receiver','receiver')
 beam('receiver_tail',[7.37,9.23],[8.19,9.33],.80,.69,'steel','receiver','receiver')
 # Major mechanical side furniture preserves asymmetric depth; fasteners are painted.
 c('bolt_handle',[8.59,9.12,5.61],[.47,.18,.26],'steel','receiver','bolt')
 c('bolt_handle_end',[8.78,9.12,5.59],[.22,.26,.32],'black','receiver','bolt')
 beam('forward_control',[4.24,8.95],[4.39,8.33],.18,.19,'steel','receiver','goldedge',x=8.55)
 # Short hammer and raised rear fork are solid separated mechanical pieces.
 beam('hammer',[7.54,9.88],[8.02,10.12],.22,.16,'steel','receiver','goldedge')
 c('rear_sight_sill',[8,10.10,7.40],[.75,.18,.52],'steel','sight','goldedge')
 for sx in (-1,1):c('rear_sight_fork'+str(sx),[8+sx*.31,10.49,7.53],[.13,.71,.18],'steel','sight','goldedge')
 # Upper golden wrapped cylindrical sight and its actual open rear aperture.
 c('sight_foot',[8,10.83,3.84],[.66,.24,2.47],'black','sight','action')
 cylinder('wrapped_sight',10.99,4.36,5.79,.34,'gold','sight','braid')
 cylinder('sight_front',10.99,3.07,4.36,.265,'black','sight','sight')
 c('sight_aperture_floor',[8,11.13,3.70],[.55,.13,.19],'black','sight')
 for sx in (-1,1):c('sight_aperture_side'+str(sx),[8+sx*.22,11.35,3.70],[.12,.44,.19],'black','sight')
 c('sight_aperture_roof',[8,11.50,3.70],[.55,.10,.19],'black','sight')
 # Filled stock, scooped wrist and comb; the butt is not an outlined hollow shell.
 beam('stock_wrist',[8.03,9.25],[9.63,8.41],.73,.65,'woodlight','stock','stock')
 beam('stock_comb_rise',[9.28,8.54],[11.42,9.49],.72,.70,'wood','stock','stock')
 c('stock_rear_solid',[8,8.42,12.71],[.70,2.10,2.89],'wood','stock','stock',('x',-5))
 beam('stock_comb',[11.10,9.59],[13.93,9.49],.69,.39,'woodlight','stock','stock')
 beam('stock_lower_sweep',[9.26,8.27],[12.89,7.40],.66,.45,'wood','stock','stock')
 beam('butt_pad',[14.15,7.12],[14.00,9.58],.73,.15,'steel','stock','butt')
 beam('stock_haunch_filled',[9.67,8.45],[11.54,8.65],.70,1.47,'wood','stock','stock')
 # Two related but distinct through-holes: trigger space and the long golden lever.
 beam('trigger_guard_front',[5.40,8.82],[5.48,8.31],.42,.19,'steel','guard','goldedge')
 beam('trigger_guard_front_curve',[5.48,8.31],[5.70,8.09],.42,.20,'steel','guard','goldedge')
 beam('trigger_guard_lower',[5.70,8.09],[6.25,7.97],.43,.20,'steel','guard','goldedge')
 beam('trigger_guard_lower_curve',[6.25,7.97],[6.53,8.12],.43,.23,'steel','guard','goldedge')
 beam('trigger_guard_back',[6.53,8.12],[6.95,8.80],.48,.26,'steel','guard','goldedge')
 beam('trigger',[6.33,8.85],[6.16,8.34],.15,.13,'black','trigger')
 beam('lever_upper',[7.18,8.75],[8.27,8.12],.62,.27,'gold','lever','gold')
 beam('lever_rear',[8.27,8.12],[8.81,7.09],.61,.25,'steel','lever','goldedge')
 beam('lever_toe',[8.81,7.09],[8.23,6.15],.61,.26,'gold','lever','gold')
 beam('lever_lower',[8.23,6.15],[6.94,7.16],.56,.25,'steel','lever','goldedge')
 beam('lever_front',[6.94,7.16],[6.37,7.63],.51,.25,'steel','lever','goldedge')
 beam('lever_root',[6.37,7.63],[6.13,8.71],.62,.28,'steel','lever','receiver')
 # No source fragments or downstream aggregate provenance. Immutable source inputs only.
 inputs=[BASE,SOURCE,HELPER,REFS,ASSET+'textures/item/weapon/w30/long_arm.png']+[BASE.replace('.json',suffix+'.json') for suffix in ('_ads','_twohand','_ads_twohand')]
 raws=[RAW/'Long Arm.blend',RAW/'Long Arm.fbx',PHOTO]+[RAW/('LA'+m+'_Diffuse.png') for m in ('Frame','Sight','Bullet')]
 return dict(id=ID,revision='W142',construction='Authored semantic filled cuboids; no adapters, voxels, source islands or alpha silhouette',
  parts=parts,source=meta,palette=PALETTE,full_only=True,muzzle_axis='-Z',hand_frame='Canonical [8,8,8]; no coordinate compensation',
  identity=['long double-level barrel/frame and real daylight windows','walnut stock and pale diagonal wraps','gold trim and braided raised sight','open trigger guard and large lever bow'],
  atlas=dict(size=EDGE,gutter=2,texels_per_unit=25),
  openings=dict(muzzle=[8,9.67,-10.15],front_crown=[8,10.88,-10.13],barrel_daylight=[8,10.18,-2.7],
   trigger_guard=[8,8.40,5.89],lever=[8,7.30,7.65],sight_aperture=[8,11.33,3.70]),
  filled_probes=dict(wrist_haunch=[8,8.50,10.7],stock=[8,8.45,12.5],handguard=[8,9.3,1.0],receiver=[8,9.4,5.1],upper_barrel=[8,10.72,-3]),
  source_matching=dict(method='inert Blender3.1 SDNA, stored object matrices, [world.X,world.Z,world.Y]',objects=len(meshes),triangles=sum(len(m['faces']) for m in meshes)),
  default_photo_sha256=sha(PHOTO.read_bytes()),
  input_sha256={p:sha((ROOT/p).read_bytes()) for p in inputs if p!=SCRIPT},
  raw_input_sha256={str(p):sha(p.read_bytes()) for p in raws},
  limitations=['Offline CPU art evidence; native pack/parser/holding/ADS/reload/10-20 displays pending master.',
   'Curved wood and forged frame simplified to faceted solids; static authored color is not source PBR.',
   'Small fasteners, gold fillets, grain and wraps use opaque UV; muzzle, sight, guard and frame openings are physical.'])


def tile(s,face,w,h):
 u,v=np.meshgrid((np.arange(w)+.5)/w,(np.arange(h)+.5)/h)
 mat=s['material'];motif=s['motif'];pts=vertices(s['geometry'])[list(FACES[face])]
 pos=((1-u)*(1-v))[:,:,None]*pts[0]+(u*(1-v))[:,:,None]*pts[1]+(u*v)[:,:,None]*pts[2]+((1-u)*v)[:,:,None]*pts[3]
 x,y,z=pos[:,:,0],pos[:,:,1],pos[:,:,2]
 rgb=np.broadcast_to(np.array(PALETTE[mat],float),(h,w,3)).copy()
 rgb*=(.96+.065*np.cos(v*math.pi))[:,:,None]
 edge=np.minimum.reduce([u*w,(1-u)*w,v*h,(1-v)*h]);rgb[edge<.7]*=.76;rgb[(edge>=.7)&(edge<1.55)]*=1.15
 side=face in ('east','west')
 if mat.startswith('wood'):
  grain=np.sin(y*35+2*np.sin(z*.48)+.8*np.sin(z*2.0))+ .3*np.sin(y*110+4*np.sin(z*.43))
  rgb*=(1+.075*grain)[:,:,None]
  # Pale diagonal cloth occupies both surfaces and transverse edges, no transparency.
  wrap=np.zeros_like(u,dtype=bool)
  if motif=='stock':
   wrap=(abs(y-(8.55+.63*(z-12.0)))<.38)|(abs(y-(8.65-.62*(z-12.0)))<.38)
   wrap&=z>8.9
  if motif=='wrapwood':wrap=(z+.62*(y-8.8)>-.06)&(z+.62*(y-8.8)<1.85)
  if motif=='wood':wrap=(z+.62*(y-8.8)>-.01)&(z+.62*(y-8.8)<1.92)
  if motif=='upperwood':wrap=(y<10.25)&(z>3.10)&(z<6.64)
  cloth=np.broadcast_to(np.array(PALETTE['cloth'],float),(h,w,3)).copy()
  weave=(np.sin(y*29+z*14)*np.sin(z*31-y*13))
  cloth*=(.96+.045*weave+.020*np.sin(z*23+y*6))[:,:,None]
  rgb[wrap]=cloth[wrap]
  # Wrap seam, world aligned over the bevel and side faces.
  if motif=='wrapwood':
   t=z+.62*(y-8.8);seam=((abs(t-.06)<.033)|(abs(t-.17)<.033)|(abs(t-1.73)<.025))
   rgb[seam]*=.63
  if motif=='keel' and side:
   rr=np.hypot(z+3.05,y-8.67);rgb[rr<.115]=PALETTE['gold'];rgb[(rr>.10)&(rr<.12)]*=.55
  if motif=='upperwood' and side:

   p=((abs(y-10.44)<.028)&(z>3.9)&(z<6.6))|((abs(y-10.52)<.020)&(z>4.5)&(z<6.9))
   rgb[p]=[178,163,134]
 if motif in ('barrel','tube','muzzle'):
  # Single continuous fine gold inlay, no repeated gold geometry strips.
  line=(abs(y-10.74)<.024) if motif=='barrel' else (abs(y-9.77)<.022)
  if side:rgb[line]=PALETTE['gold']
  if motif=='muzzle':rgb[(abs(z+10.18)<.022)|(abs(z+9.42)<.025)]=[122,113,81]
 if motif in ('receiver','goldedge','action'):
  if side:
   line=(edge>2)&(edge<3.3)
   if s['group']=='receiver':
    line=((abs(y-9.02)<.023)&(z>4.12)&(z<6.40))|((abs(y-9.23)<.023)&(z>6.40)&(z<7.73))|((abs(z-6.40)<.024)&(y>9.02)&(y<9.24))
   rgb[line]=PALETTE['gold']
   if motif=='receiver':
    # Photo-supported action ejection slot and a small grounded fastener set.
    port=(z>4.98)&(z<6.43)&(y>9.54)&(y<9.82)
    rgb[port]=[12,17,17]
    rgb[(abs(y-9.84)<.022)&(z>5.0)&(z<6.43)]=[91,94,84]
    rgb[(abs(y-9.50)<.025)&(z>4.16)&(z<4.85)]=[64,69,65]
    for zz,yy in [(4.37,9.18),(5.00,8.99),(6.95,9.19)]:
     rr=np.hypot(z-zz,y-yy);rgb[rr<.057]=[83,84,70];rgb[(rr>.038)&(rr<.050)]*=.40
     rgb[(abs(z-zz)<.012)&(abs(y-yy)<.03)]*=.40
 if motif=='braid':
  # The default reference has a woven gold sight sleeve, no invented insignia.
  phase=np.sin(z*36+y*30+x*12)*np.sin(z*36-y*30-x*12)
  rgb*=(.82+.28*(phase+1)/2)[:,:,None]
  rgb[(np.mod(z*12+y*6,1)<.13)]*=.65
 if motif in ('sight','bolt'):
  rgb[(np.mod(z*16,1)<.10)&(edge>2)]*=.62
 if motif=='butt':rgb[(np.mod(y*11,1)<.20)&(edge>2)]*=.6
 return Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.full((h,w),255,np.uint8)]))


def compile_model(d):
 atlas=Image.new('RGBA',(EDGE,EDGE),(18,23,24,255));requests=[]
 for s in d['parts']:
  for f,ix in FACES.items():
   p=vertices(s['geometry'])[list(ix)];w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*25));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*25))
   requests.append((h,w,s['geometry']['name'],f,s))
 requests.sort(key=lambda a:(-a[0],-a[1],a[2],a[3]));x=y=2;row=0;islands=[];uvmap={}
 for h,w,name,f,s in requests:
  if x+w+2>EDGE:x=2;y+=row+4;row=0
  assert y+h+2<=EDGE,'UV atlas overflow'
  atlas.paste(Image.fromarray(np.pad(np.asarray(tile(s,f,w,h)),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
  rect=[x,y,x+w,y+h];uvmap[name,f]=[a*16/EDGE for a in rect];islands.append(dict(element=name,face=f,rect=rect));x+=w+4;row=max(row,h)
 es=[]
 for s in d['parts']:
  e=copy.deepcopy(s['geometry']);e['faces']={f:dict(uv=uvmap[e['name'],f],texture='#0') for f in FACES};es.append(e)
 d['atlas'].update(used_height=y+row+2,islands=islands,face_islands=len(islands),paint_policy='Opaque independent faceUV, world-continuous walnut grain/wraps and grounded gold inlay')
 return atlas,dict(credit='Long Arm W142 / semantic filled solids and default-photo face UV / full only',
  textures={'0':'destiny:item/weapon/w123/long_arm','particle':'destiny:item/weapon/w123/long_arm'},
  display=copy.deepcopy(json.loads((ROOT/BASE).read_bytes())['display']),elements=es)


def inspection(d,model,atlas):
 es=[];groups={}
 for s,e in zip(d['parts'],model['elements']):
  b=copy.deepcopy(e);r=b.pop('rotation',None);b.update(type='cube',uuid=uid(e['name']),box_uv=False,autouv=0,
   origin=r['origin'] if r else [8,8,8],rotation=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'])
  for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
  es.append(b);groups.setdefault(s['group'],[]).append(b['uuid'])
 return dict(meta=dict(format_version='4.10',model_format='free',box_uv=False),name='Long Arm W142 / editable full solid inspection',
  resolution=dict(width=EDGE,height=EDGE),elements=es,display=copy.deepcopy(model['display']),
  outliner=[dict(name=n,uuid=uid(n),origin=[8,8,8],rotation=[0,0,0],children=cs,export=True) for n,cs in groups.items()],
  textures=[dict(name='long_arm.png',id='0',uuid=uid('atlas'),width=EDGE,height=EDGE,uv_width=EDGE,uv_height=EDGE,
   source='data:image/png;base64,'+base64.b64encode(png(atlas)).decode())],
  destiny_w142=dict(nativeAccepted=False,fullOnly=True,sourceScale=d['source']['scale'],sourceAnchor=d['source']['anchor']))


def comparison(d,ms,atlas,model):
 w,h=1000,360;out=Image.new('RGB',(3000,2040),'#18212a');draw=ImageDraw.Draw(out)
 def label(x,y,s,size=22):draw.text((x,y),s,fill='#e8ebeb',font_size=size)
 label(20,12,'LONG ARM / W142 / SEMANTIC FILLED SOLIDS + OPAQUE FACE UV / OFFLINE ART',30)
 photo=Image.open(PHOTO).convert('RGB').crop((70,390,1740,905));photo.thumbnail((1540,475));out.paste(photo,(20,60))
 for i,s in enumerate([f'{len(model["elements"])} emitted cuboids / full only / no adapters',
  'Default Bungie photo: wood, pale wraps, dark steel, gold',
  'Actual source BLEND: 3 objects / 21,812 triangles',
  'Canonical anchor [8,8,8] / scale 17.675692296761287',
  'Independent face UVs / 1024 atlas / 2px gutters',
  'Physical bore / sights / guard / lever / long daylight',
  'Native pack, holding, ADS, reload and 10-20: pending master']):label(1630,85+i*47,s,23)
 label(20,555,'RAW W30 BLEND / ORIGINAL UV + NEUTRAL DIFFUSE')
 old=json.loads((ROOT/BASE).read_bytes());oldtex=Image.open(ROOT/(ASSET+'textures/item/weapon/w30/long_arm.png'))
 label(w+20,555,f'CANONICAL W30 / {len(old["elements"])} CUBOIDS / READ ONLY')
 label(2*w+20,555,f'W142 / {len(model["elements"])} AUTHOR-PLACED FILLED CUBOIDS')
 ts=[source_triangles(ms),model_triangles(old,oldtex),model_triangles(model,atlas)];points=np.concatenate([m['vertices'] for m in ms])
 for row,(name,cam) in enumerate([('SIDE / EQUAL CAMERA AND SCALE',[-1,0,0]),('FRONT OBLIQUE / EQUAL CAMERA AND SCALE',[-1,.42,-.60]),('REAR OBLIQUE / EQUAL CAMERA AND SCALE',[1,.40,.60])]):
  ext=H['frame'](points,cam,w,h)
  for col,tris in enumerate(ts):
   im,_=H['render'](tris,cam,ext,(w,h),raw=col==0);out.paste(im,(col*w,595+row*h));label(col*w+14,605+row*h,name,18)
 for i,(groups,title,cam) in enumerate([(['muzzle','front_sight'],'BORE + OPEN FRONT CROWN',[.25,.2,-1]),
  (['receiver','guard','trigger','lever','stock'],'GUARD + LEVER + FILLED STOCK',[-1,.20,-.15]),
  (['sight','upper_wood'],'SIGHT APERTURE + BRAID',[.3,.2,-1]),
  (['barrel','bands','lower_frame'],'TRANSVERSE FRAME DEPTH',[-1,.45,-.6])]):
  names={s['geometry']['name'] for s in d['parts'] if s['group'] in groups};es=[e for e in model['elements'] if e['name'] in names];pts=np.concatenate([vertices(e) for e in es])
  im,_=H['render'](model_triangles(dict(elements=es),atlas),cam,H['frame'](pts,cam,750,285),(750,285));out.paste(im,(i*750,1690));label(i*750+13,1700,title,18)
 label(20,2000,'Raw neutral diffuse is not the default shader. CPU views do not establish native parsing, runtime lighting, ADS, reload or performance.',21)
 return png(out)


def review_text(d,counts):
 return f"""# Long Arm W142 — offline product review

{len(d['parts'])} opaque, authored cuboids; {len(d['parts'])*6} explicit face UVs; full-only assembly; zero triangle/contour adapters or alpha silhouette cards. The 1000-element assembled ceiling is a hard cap, not a target. Parts follow semantic barrel/frame, bands, forewood, hand contact, upper wood cover, receiver, sights, stock, guard and lever. Long tubes use filled octagonal sections; an actual recessed muzzle uses opaque tangent walls. Large wood masses are filled across their width. This applies the Ace87/Izanagi79 study without borrowing their motifs.

Reference: actual default Bungie/light.gg item 8293111 photo, inspected via view_image. Default identity is long double-level steel framework, daylight between structural rods, walnut wood and pale cloth wraps, thin gold inlay and braided raised sight, two distinct guard/lever openings, scooped wrist and filled butt. Fine grain, cloth weave/seams, gold lines, panel slots and grounded fasteners use authored faceUV instead of small cubes. Per-face islands keep near/far faces independent; world-space patterns maintain wrap/grain continuity around transverse edges. Paint is opaque with 2px extruded gutters. This is a clean default-color reconstruction, not recovered PBR.

The exact W30 source scale {d['source']['scale']}, anchor {d['source']['anchor']}, thin X / vertical Y / muzzle -Z basis and hand frame are retained. Canonical display values are copied exactly. No shared registration, HUD, ADS, twohand, reload, audio or gameplay files are modified. Full-only output creates no split-reload requirement. Master owns downstream integration and native QA.

Source provenance: read-only compressed Blender3.1 SDNA decoding, stored matrices applied, [world.X, world.Z, world.Y] mapped with original scale/anchor. All three W30 retained objects and 21812 triangles match. Source and native bounds match within floating-point matrix precision. A read-only raw FBX probe found 26377 triangle records across the same three retained object names, versus 21812 in the accepted W30 BLEND. Its bounds also differ slightly laterally/longitudinally. It is hashed as immutable evidence but not fitted or used as the canonical basis; current topology/frame equivalence to FBX is not claimed. No scripts from the rip or shaders are executed. Only the existing trusted CPU renderer is reused read-only. No downstream aggregate manifest hashes are art inputs.

comparison.png has the actual default-photo crop, actual raw BLEND/UV/diffuse, old canonical 256-cube model and new solid model in side and front/rear oblique rows at equal camera/scale, plus muzzle/sight/frame/guard depth closeups. Raw source diffuse is neutral and explicitly labeled; no native screenshot is implied. inspection.bbmodel embeds the exact atlas, editable native cubes and semantic groups; no DCC session was touched.

Checks: emitted schema/budget, source basis/display, filled depth and physically empty ray paths, UV rectangles/opacity/gutters/non-overlap, input/output provenance, inspection parity, exact ten-path ownership, deterministic regeneration. Curved wood/forged contours are faceted; small relief is painted. Offline previews cannot establish resource-pack parsing/loading, live lighting, holding, ADS, generic reload or performance at 10–20 simultaneous displays. Those remain pending master; no server/client/Gradle/DCC run occurred.

Group counts: {json.dumps(counts,sort_keys=True)}.
"""


def generate(include_comparison=True):
 ms,meta=source_meshes();d=make_design(meta,ms);atlas,model=compile_model(d);counts=dict(sorted(Counter(s['group'] for s in d['parts']).items()))
 points=np.concatenate([vertices(e) for e in model['elements']]);outputs={ART+'design.json':encode(d),MODEL:encode(model),TEXTURE:png(atlas),
  ART+'inspection.bbmodel':encode(inspection(d,model,atlas)),ART+'review.md':review_text(d,counts).encode()}
 if include_comparison:outputs[ART+'comparison.png']=comparison(d,ms,atlas,model)
 manifest=dict(id=ID,revision='W142',family='scout_rifle',assembled_elements=len(model['elements']),opaque_cuboids=len(model['elements']),
  emitted_faces=len(model['elements'])*6,triangle_adapter_elements=0,contour_elements=0,alpha_body_elements=0,max_assembled_elements=1000,
  full_only=True,groups=counts,texture_size=[EDGE,EDGE],face_uv_islands=len(d['atlas']['islands']),atlas_used_height=d['atlas']['used_height'],
  actual_bounds=[points.min(0).tolist(),points.max(0).tolist()],source_bounds=meta['model_bounds'],source_scale=meta['scale'],source_anchor=meta['anchor'],
  source_matching=d['source_matching'],default_photo_sha256=d['default_photo_sha256'],canonical_display_exact=True,
  existing_ADS_twohand_reload_audio_gameplay_unchanged=True,native_accepted=False,input_sha256=d['input_sha256'],raw_input_sha256=d['raw_input_sha256'],
  generator_sha256=sha((ROOT/SCRIPT).read_bytes()),test_sha256=sha((ROOT/TEST).read_bytes()),
  output_sha256={p:sha(v) for p,v in sorted(outputs.items())},limitations=d['limitations'])
 outputs[ART+'manifest.json']=encode(manifest)
 owned=next(f['owned_paths'] for f in json.loads((ROOT/BATCH).read_bytes())['features'] if f['name']=='w142-long_arm')
 assert set(outputs)<=set(owned) and len(outputs)==(7 if include_comparison else 6)
 assert len(model['elements'])<=1000
 return outputs


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args();outputs=generate()
 for rel,data in outputs.items():
  path=ROOT/rel
  if args.verify:assert path.is_file() and path.read_bytes()==data,'Regeneration differs: '+rel
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} owned artifacts; {m["assembled_elements"]} filled cuboids / {m["emitted_faces"]} faces; full only; 0 adapters')
 print(f'1024 atlas used height {m["atlas_used_height"]}; payload {sum(len(v) for v in outputs.values())} bytes; native pending master')
if __name__=='__main__':main()
